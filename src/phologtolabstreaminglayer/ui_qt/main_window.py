from __future__ import annotations
from typing import Dict, List, Optional, Callable
from pathlib import Path
import threading
import socket
import logging
from datetime import datetime, timedelta

from PyQt6 import QtCore, QtGui, QtWidgets
import pylsl


class QtLogHandler(logging.Handler):
	"""
	Thread-safe logging handler that appends log messages into a QPlainTextEdit.
	"""
	appendRequested = QtCore.pyqtSignal(str)  # type: ignore[attr-defined]

	def __init__(self, target_text_edit: QtWidgets.QPlainTextEdit) -> None:
		super().__init__()
		self._target = target_text_edit
		# Bridge from any thread → main thread
		self.appendRequested.connect(self._on_append_requested)  # type: ignore[attr-defined]

	@QtCore.pyqtSlot(str)  # type: ignore[attr-defined]
	def _on_append_requested(self, text: str) -> None:
		self._target.appendPlainText(text)

	def emit(self, record: logging.LogRecord) -> None:
		try:
			msg = self.format(record)
		except Exception:
			msg = record.getMessage()
		self.appendRequested.emit(msg)


class MainWindow(QtWidgets.QMainWindow):
	"""
	PyQt6 port of the LSL Logger UI. This window mirrors the original Tkinter UI:
	- Tabs: Recording, Live Audio, EventBoard, Manual Log, Settings
	- Stream monitor with selectable streams
	- Manual log input and history
	- EventBoard grid with optional toggle behavior and per-button offset
	- Status/info area
	"""

	# Signals for cross-thread UI updates
	streamsDiscovered = QtCore.pyqtSignal(dict)  # mapping key -> pylsl.StreamInfo  # type: ignore[attr-defined]
	logMessage = QtCore.pyqtSignal(str)  # type: ignore[attr-defined]

	def __init__(self, xdf_folder: Path, parent: Optional[QtWidgets.QWidget] = None) -> None:
		super().__init__(parent)
		self.setWindowTitle("LSL Logger with XDF Recording")
		self.resize(900, 720)

		self._shutting_down: bool = False
		self.xdf_folder: Path = xdf_folder

		# State
		self.stream_names: List[str] = ["TextLogger", "EventBoard", "WhisperLiveLogger"]
		self.recording: bool = False
		self.discovered_streams: Dict[str, pylsl.StreamInfo] = {}
		self.selected_streams: set[str] = set()
		self.stream_monitor_thread: Optional[threading.Thread] = None
		self.stream_discovery_active: bool = False

		self.outlets: Dict[str, Optional[pylsl.StreamOutlet]] = {}
		self.inlets: Dict[str, pylsl.StreamInlet] = {}

		self.eventboard_config: Optional[dict] = None
		self.eventboard_buttons: Dict[str, QtWidgets.QPushButton] = {}
		self.eventboard_toggle_states: Dict[str, bool] = {}
		self.eventboard_original_colors: Dict[str, str] = {}
		self.eventboard_time_offsets: Dict[str, QtWidgets.QLineEdit] = {}

		self._build_ui()
		self._wire_menu_and_tray()
		self._connect_signals()

		# Load configuration and setup LSL
		self._load_eventboard_config()
		self._setup_lsl_outlets()

		# Timers replacing tkinter .after()
		QtCore.QTimer.singleShot(200, self._auto_start_live_transcription)
		QtCore.QTimer.singleShot(2000, self.start_stream_discovery)

	def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
		self._shutting_down = True
		self._stop_stream_discovery()
		super().closeEvent(event)

	def _build_ui(self) -> None:
		central = QtWidgets.QWidget(self)
		self.setCentralWidget(central)
		root_layout = QtWidgets.QVBoxLayout(central)
		root_layout.setContentsMargins(0, 0, 0, 0)

		self.tabs = QtWidgets.QTabWidget(self)
		root_layout.addWidget(self.tabs)

		# Recording tab
		self.tab_recording = QtWidgets.QWidget()
		self.tabs.addTab(self.tab_recording, "Recording")
		self._build_tab_recording(self.tab_recording)

		# Live Audio tab (placeholder; can be extended)
		self.tab_live_audio = QtWidgets.QWidget()
		self.tabs.addTab(self.tab_live_audio, "Live Audio")
		self._build_tab_live_audio(self.tab_live_audio)

		# EventBoard tab
		self.tab_eventboard = QtWidgets.QWidget()
		self.tabs.addTab(self.tab_eventboard, "EventBoard")
		self._build_tab_eventboard(self.tab_eventboard)

		# Manual Log tab
		self.tab_manual = QtWidgets.QWidget()
		self.tabs.addTab(self.tab_manual, "Manual Log")
		self._build_tab_manual(self.tab_manual)

		# Settings tab
		self.tab_settings = QtWidgets.QWidget()
		self.tabs.addTab(self.tab_settings, "Settings")
		self._build_tab_settings(self.tab_settings)

		self.statusBar().showMessage("Ready")

	def _build_tab_recording(self, parent: QtWidgets.QWidget) -> None:
		layout = QtWidgets.QVBoxLayout(parent)
		# LSL status
		self.lsl_status_label = QtWidgets.QLabel("LSL Status: Initializing…", parent)
		palette = self.lsl_status_label.palette()
		palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("orange"))
		self.lsl_status_label.setPalette(palette)
		layout.addWidget(self.lsl_status_label)

		# Controls group
		ctrl_group = QtWidgets.QGroupBox("XDF Recording", parent)
		layout.addWidget(ctrl_group)
		grid = QtWidgets.QGridLayout(ctrl_group)

		self.recording_status_label = QtWidgets.QLabel("Not Recording", ctrl_group)
		red_palette = self.recording_status_label.palette()
		red_palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("red"))
		self.recording_status_label.setPalette(red_palette)
		grid.addWidget(self.recording_status_label, 0, 0)

		self.btn_start_recording = QtWidgets.QPushButton("Start Recording", ctrl_group)
		self.btn_stop_recording = QtWidgets.QPushButton("Stop Recording", ctrl_group)
		self.btn_split_recording = QtWidgets.QPushButton("Split Recording", ctrl_group)
		self.btn_minimize_to_tray = QtWidgets.QPushButton("Minimize to Tray", ctrl_group)
		self.btn_stop_recording.setEnabled(False)
		self.btn_split_recording.setEnabled(False)

		grid.addWidget(self.btn_start_recording, 0, 1)
		grid.addWidget(self.btn_stop_recording, 0, 2)
		grid.addWidget(self.btn_split_recording, 0, 3)
		grid.addWidget(self.btn_minimize_to_tray, 0, 4)

		# Stream monitor
		self._build_stream_monitor(layout)

		# Wire buttons
		self.btn_start_recording.clicked.connect(self.start_recording)
		self.btn_stop_recording.clicked.connect(self.stop_recording)
		self.btn_split_recording.clicked.connect(self.split_recording)
		self.btn_minimize_to_tray.clicked.connect(self._minimize_to_tray)

	def _build_stream_monitor(self, parent_layout: QtWidgets.QVBoxLayout) -> None:
		group = QtWidgets.QGroupBox("LSL Stream Monitor", self)
		parent_layout.addWidget(group)
		vbox = QtWidgets.QVBoxLayout(group)

		self.stream_tree = QtWidgets.QTreeWidget(group)
		self.stream_tree.setHeaderLabels(["Select", "Name", "Type", "Channels", "Rate", "Status"])
		self.stream_tree.setRootIsDecorated(False)
		self.stream_tree.setAlternatingRowColors(True)
		self.stream_tree.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
		vbox.addWidget(self.stream_tree)

		btn_row = QtWidgets.QHBoxLayout()
		vbox.addLayout(btn_row)
		self.btn_refresh_streams = QtWidgets.QPushButton("Refresh Streams", group)
		self.btn_select_all = QtWidgets.QPushButton("Select All", group)
		self.btn_select_none = QtWidgets.QPushButton("Select None", group)
		self.btn_auto_select_own = QtWidgets.QPushButton("Auto-Select Own", group)
		btn_row.addWidget(self.btn_refresh_streams)
		btn_row.addWidget(self.btn_select_all)
		btn_row.addWidget(self.btn_select_none)
		btn_row.addWidget(self.btn_auto_select_own)
		btn_row.addStretch(1)

		self.btn_refresh_streams.clicked.connect(self.refresh_streams)
		self.btn_select_all.clicked.connect(self.select_all_streams)
		self.btn_select_none.clicked.connect(self.select_no_streams)
		self.btn_auto_select_own.clicked.connect(self.auto_select_own_streams)

		self.stream_tree.itemChanged.connect(self._on_stream_item_changed)

	def _build_tab_live_audio(self, parent: QtWidgets.QWidget) -> None:
		layout = QtWidgets.QVBoxLayout(parent)
		lbl = QtWidgets.QLabel("Live Audio controls appear here.", parent)
		layout.addWidget(lbl)
		layout.addStretch(1)

	def _build_tab_eventboard(self, parent: QtWidgets.QWidget) -> None:
		layout = QtWidgets.QGridLayout(parent)
		parent.setLayout(layout)
		self._rebuild_eventboard_grid(layout)

	def _build_tab_manual(self, parent: QtWidgets.QWidget) -> None:
		layout = QtWidgets.QGridLayout(parent)
		parent.setLayout(layout)

		lbl_msg = QtWidgets.QLabel("Message:", parent)
		self.edit_message = QtWidgets.QLineEdit(parent)
		self.btn_log = QtWidgets.QPushButton("Log", parent)
		self.edit_message.returnPressed.connect(self._on_log_clicked)
		self.btn_log.clicked.connect(self._on_log_clicked)

		layout.addWidget(lbl_msg, 0, 0)
		layout.addWidget(self.edit_message, 0, 1)
		layout.addWidget(self.btn_log, 0, 2)

		lbl_history = QtWidgets.QLabel("Log History:", parent)
		layout.addWidget(lbl_history, 1, 0, 1, 3)

		self.log_display = QtWidgets.QPlainTextEdit(parent)
		self.log_display.setReadOnly(True)
		layout.addWidget(self.log_display, 2, 0, 1, 3)

		btn_row = QtWidgets.QHBoxLayout()
		parent.setLayout(layout)
		layout.addLayout(btn_row, 3, 0, 1, 3)
		self.btn_clear_log = QtWidgets.QPushButton("Clear Log Display", parent)
		btn_row.addWidget(self.btn_clear_log)
		btn_row.addStretch(1)

		self.lbl_status_info = QtWidgets.QLabel("Ready", parent)
		btn_row.addWidget(self.lbl_status_info)

		self.btn_clear_log.clicked.connect(lambda: self.log_display.clear())

		# Install log handler
		handler = QtLogHandler(self.log_display)
		handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
		logging.getLogger().addHandler(handler)
		logging.getLogger().setLevel(logging.INFO)

	def _build_tab_settings(self, parent: QtWidgets.QWidget) -> None:
		layout = QtWidgets.QVBoxLayout(parent)
		layout.addWidget(QtWidgets.QLabel("Settings will appear here.", parent))
		layout.addStretch(1)

	def _wire_menu_and_tray(self) -> None:
		# Menu with basic actions and shortcuts
		menu = self.menuBar().addMenu("&File")
		act_quit = QtGui.QAction("&Quit", self)
		act_quit.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
		act_quit.triggered.connect(self.close)
		menu.addAction(act_quit)

		# Keyboard shortcuts for tab switching (Ctrl+1..5)
		for idx in range(5):
			shortcut = QtGui.QShortcut(QtGui.QKeySequence(f"Ctrl+{idx+1}"), self)
			shortcut.activated.connect(lambda i=idx: self.tabs.setCurrentIndex(i))

		# System tray icon
		self.tray = QtWidgets.QSystemTrayIcon(self)
		icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
		self.tray.setIcon(icon)
		tray_menu = QtWidgets.QMenu(self)
		act_show = tray_menu.addAction("Show")
		act_hide = tray_menu.addAction("Hide")
		act_quit_tray = tray_menu.addAction("Quit")
		act_show.triggered.connect(self.showNormal)
		act_hide.triggered.connect(self.hide)
		act_quit_tray.triggered.connect(self.close)
		self.tray.setContextMenu(tray_menu)

	def _connect_signals(self) -> None:
		self.streamsDiscovered.connect(self._on_streams_discovered)
		self.logMessage.connect(self._append_log)

	@QtCore.pyqtSlot(dict)  # type: ignore[attr-defined]
	def _on_streams_discovered(self, mapping: dict) -> None:
		self._populate_stream_tree(mapping)

	@QtCore.pyqtSlot(str)  # type: ignore[attr-defined]
	def _append_log(self, text: str) -> None:
		self.log_display.appendPlainText(text)

	# -------------------------- Recording / LSL --------------------------
	def _setup_lsl_outlets(self) -> None:
		self._setup_textlogger_outlet()
		self._setup_eventboard_outlet()
		self.lsl_status_label.setText("LSL Status: Connected")
		palette = self.lsl_status_label.palette()
		palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("green"))
		self.lsl_status_label.setPalette(palette)

	def _setup_textlogger_outlet(self) -> None:
		try:
			info = pylsl.StreamInfo(
				name="TextLogger",
				type="Markers",
				channel_count=1,
				nominal_srate=pylsl.IRREGULAR_RATE,
				channel_format=pylsl.cf_string,
				source_id="textlogger_001",
			)
			self.outlets["TextLogger"] = pylsl.StreamOutlet(info)
		except Exception as e:
			logging.exception("Error creating TextLogger outlet: %s", e)
			self.outlets["TextLogger"] = None

	def _setup_eventboard_outlet(self) -> None:
		try:
			info = pylsl.StreamInfo(
				name="EventBoard",
				type="Markers",
				channel_count=1,
				nominal_srate=pylsl.IRREGULAR_RATE,
				channel_format=pylsl.cf_string,
				source_id="eventboard_001",
			)
			self.outlets["EventBoard"] = pylsl.StreamOutlet(info)
		except Exception as e:
			logging.exception("Error creating EventBoard outlet: %s", e)
			self.outlets["EventBoard"] = None

	def _auto_start_live_transcription(self) -> None:
		# Placeholder to mirror original timing behavior; hook real logic here
		pass

	def start_recording(self) -> None:
		if self.recording:
			return
		if not self.inlets:
			self._setup_recording_inlets()
		if not self.inlets:
			QtWidgets.QMessageBox.critical(self, "Error", "No LSL inlet available for recording")
			return
		self.recording = True
		self.recording_status_label.setText("Recording")
		self.btn_start_recording.setEnabled(False)
		self.btn_stop_recording.setEnabled(True)
		self.btn_split_recording.setEnabled(True)
		self._append_log(f"{datetime.now():%Y-%m-%d %H:%M:%S} | INFO | Recording started")

	def stop_recording(self) -> None:
		if not self.recording:
			return
		self.recording = False
		self.recording_status_label.setText("Not Recording")
		self.btn_start_recording.setEnabled(True)
		self.btn_stop_recording.setEnabled(False)
		self.btn_split_recording.setEnabled(False)
		self._append_log(f"{datetime.now():%Y-%m-%d %H:%M:%S} | INFO | Recording stopped")

	def split_recording(self) -> None:
		if not self.recording:
			return
		self._append_log(f"{datetime.now():%Y-%m-%d %H:%M:%S} | INFO | Recording split")

	def _setup_recording_inlets(self) -> None:
		self.inlets.clear()
		for name in self.stream_names:
			try:
				found = pylsl.resolve_byprop("name", name, timeout=1.0)
				if found:
					self.inlets[name] = pylsl.StreamInlet(found[0])
			except Exception:
				continue
		if self.inlets:
			QtCore.QTimer.singleShot(500, self._auto_start_recording)

	def _auto_start_recording(self) -> None:
		# Hook auto-start behavior if required
		pass

	# -------------------------- Streams discovery --------------------------
	def start_stream_discovery(self) -> None:
		if self.stream_discovery_active:
			return
		self.stream_discovery_active = True
		self.stream_monitor_thread = threading.Thread(target=self._run_stream_discovery, daemon=True)
		self.stream_monitor_thread.start()

	def _stop_stream_discovery(self) -> None:
		self.stream_discovery_active = False

	def _run_stream_discovery(self) -> None:
		while self.stream_discovery_active:
			try:
				all_streams = pylsl.resolve_streams(wait_time=1.0)
				mapping: Dict[str, pylsl.StreamInfo] = {}
				for info in all_streams:
					key = f"{info.name()}::{info.type()}::{info.source_id()}"
					mapping[key] = info
				self.streamsDiscovered.emit(mapping)  # type: ignore[attr-defined]
			except Exception:
				pass
			QtCore.QThread.msleep(1000)  # Throttle

	def _populate_stream_tree(self, mapping: Dict[str, pylsl.StreamInfo]) -> None:
		self.discovered_streams = mapping
		self.stream_tree.blockSignals(True)
		self.stream_tree.clear()
		for key, info in mapping.items():
			item = QtWidgets.QTreeWidgetItem(self.stream_tree)
			item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
			item.setCheckState(0, QtCore.Qt.CheckState.Checked if key in self.selected_streams else QtCore.Qt.CheckState.Unchecked)
			item.setText(1, info.name())
			item.setText(2, info.type())
			item.setText(3, str(info.channel_count()))
			item.setText(4, f"{info.nominal_srate():.0f}")
			item.setText(5, "Available")
			item.setData(0, QtCore.Qt.ItemDataRole.UserRole, key)
		self.stream_tree.blockSignals(False)
		self._update_stream_info_label()

	def _on_stream_item_changed(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
		key = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
		if not isinstance(key, str):
			return
		checked = item.checkState(0) == QtCore.Qt.CheckState.Checked
		if checked:
			self.selected_streams.add(key)
		else:
			self.selected_streams.discard(key)
		self._update_stream_info_label()

	def _update_stream_info_label(self) -> None:
		selected_names = []
		for key in self.selected_streams:
			info = self.discovered_streams.get(key)
			if info is not None:
				selected_names.append(info.name())
		text = "No streams discovered yet" if not self.discovered_streams else f"Selected: {', '.join(selected_names) or 'None'}"
		self.statusBar().showMessage(text)

	def refresh_streams(self) -> None:
		# On-demand refresh
		try:
			all_streams = pylsl.resolve_streams(wait_time=1.0)
			mapping: Dict[str, pylsl.StreamInfo] = {}
			for info in all_streams:
				key = f"{info.name()}::{info.type()}::{info.source_id()}"
				mapping[key] = info
			self._populate_stream_tree(mapping)
		except Exception:
			pass

	def select_all_streams(self) -> None:
		self.selected_streams = set(self.discovered_streams.keys())
		self._populate_stream_tree(self.discovered_streams)

	def select_no_streams(self) -> None:
		self.selected_streams.clear()
		self._populate_stream_tree(self.discovered_streams)

	def auto_select_own_streams(self) -> None:
		own = {k for k, v in self.discovered_streams.items() if v.name() in set(self.stream_names)}
		self.selected_streams = own
		self._populate_stream_tree(self.discovered_streams)

	# -------------------------- Manual log --------------------------
	def _on_log_clicked(self) -> None:
		text = self.edit_message.text().strip()
		if not text:
			return
		self._send_textlogger_message(text, datetime.now())
		self._append_log(f"{datetime.now():%Y-%m-%d %H:%M:%S} | INFO | {text}")
		self.edit_message.clear()

	def _send_textlogger_message(self, message: str, timestamp: datetime) -> None:
		outlet = self.outlets.get("TextLogger")
		if outlet is None:
			return
		payload = f"{message}|{timestamp.isoformat()}"
		try:
			outlet.push_sample([payload])
		except Exception:
			pass

	# -------------------------- EventBoard --------------------------
	def _load_eventboard_config(self) -> None:
		cfg_path = Path("eventboard_config.json")
		if not cfg_path.exists():
			self.eventboard_config = {
				"title": "Event Board",
				"buttons": [
					{"id": f"button_{i}_{j}", "row": i, "col": j, "text": f"Button {i}-{j}",
					 "event_name": f"EVENT_{i}_{j}", "color": "#2196F3", "type": "instantaneous"}
					for i in range(1, 4) for j in range(1, 6)
				],
			}
			return
		try:
			import json
			with cfg_path.open("r", encoding="utf-8") as f:
				data = json.load(f)
			self.eventboard_config = data.get("eventboard_config", {})
		except Exception:
			self.eventboard_config = None

	def _rebuild_eventboard_grid(self, grid: QtWidgets.QGridLayout) -> None:
		# Clear existing
		while grid.count():
			child = grid.takeAt(0)
			w = child.widget()
			if w:
				w.deleteLater()
		cfg = self.eventboard_config or {}
		buttons = cfg.get("buttons", [])
		for conf in buttons:
			row = max(0, conf.get("row", 1) - 1)
			col = max(0, conf.get("col", 1) - 1)
			text = conf.get("text", "Button")
			event_name = conf.get("event_name", "UNKNOWN_EVENT")
			color = conf.get("color", "#2196F3")
			btn_type = conf.get("type", "instantaneous")
			button_id = conf.get("id", f"button_{row}_{col}")

			container = QtWidgets.QWidget(self)
			container_layout = QtWidgets.QHBoxLayout(container)
			container_layout.setContentsMargins(2, 2, 2, 2)
			container.setStyleSheet(f"background-color: {color}; border: 2px ridge {color};")

			btn = QtWidgets.QPushButton(text, container)
			btn.setStyleSheet("color: white; font-weight: bold;")
			btn.clicked.connect(lambda _=None, e=event_name, t=text, bt=btn_type, bid=button_id: self._on_eventboard_button(e, t, bt, bid))
			container_layout.addWidget(btn, 4)

			offset = QtWidgets.QLineEdit("0s", container)
			offset.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
			offset.setStyleSheet("color: lightgray;")
			offset.installEventFilter(self)
			container_layout.addWidget(offset, 1)

			self.eventboard_buttons[button_id] = btn
			self.eventboard_time_offsets[button_id] = offset
			if btn_type == "toggleable":
				self.eventboard_toggle_states[button_id] = False
				self.eventboard_original_colors[button_id] = color
			grid.addWidget(container, row, col)

	def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:  # noqa: N802
		if isinstance(obj, QtWidgets.QLineEdit):
			if event.type() == QtCore.QEvent.Type.FocusIn:
				if obj.text() == "0s":
					obj.clear()
					obj.setStyleSheet("color: white;")
			elif event.type() == QtCore.QEvent.Type.FocusOut:
				if not obj.text().strip():
					obj.setText("0s")
					obj.setStyleSheet("color: lightgray;")
		return super().eventFilter(obj, event)

	def _parse_time_offset(self, s: str) -> float:
		try:
			s = (s or "").strip().lower()
			if not s:
				return 0.0
			import re
			m = re.match(r"^(\d+(?:\.\d+)?)\s*([smh]?)$", s)
			if not m:
				return 0.0
			val = float(m.group(1))
			unit = m.group(2) or "s"
			if unit == "s":
				return val
			if unit == "m":
				return val * 60.0
			if unit == "h":
				return val * 3600.0
			return 0.0
		except Exception:
			return 0.0

	def _on_eventboard_button(self, event_name: str, button_text: str, btn_type: str, button_id: str) -> None:
		try:
			offset_edit = self.eventboard_time_offsets.get(button_id)
			offset_str = offset_edit.text() if offset_edit else "0s"
			seconds = self._parse_time_offset(offset_str)
			actual_ts = datetime.now() - timedelta(seconds=seconds)

			if btn_type == "toggleable":
				current = self.eventboard_toggle_states.get(button_id, False)
				new_state = not current
				self.eventboard_toggle_states[button_id] = new_state
				orig_color = self.eventboard_original_colors.get(button_id, "#2196F3")
				btn = self.eventboard_buttons[button_id]
				if new_state:
					btn.setText(f"🔴 {button_text}")
					btn.setStyleSheet("color: white; font-weight: bold; border: 2px solid #FF4444;")
				else:
					btn.setText(f"🔘 {button_text}")
					btn.setStyleSheet("color: white; font-weight: bold;")
				suffix = "_START" if new_state else "_END"
				self._send_eventboard_message(f"{event_name}{suffix}", button_text, actual_ts, new_state)
				log_text = f"EventBoard: {button_text} {'ON' if new_state else 'OFF'} ({event_name}{suffix})"
				if seconds > 0:
					log_text += f" [offset: -{offset_str}]"
				self._append_log(f"{datetime.now():%Y-%m-%d %H:%M:%S} | INFO | {log_text}")
			else:
				self._send_eventboard_message(event_name, button_text, actual_ts, None)
				log_text = f"EventBoard: {button_text} ({event_name})"
				if seconds > 0:
					log_text += f" [offset: -{offset_str}]"
				self._append_log(f"{datetime.now():%Y-%m-%d %H:%M:%S} | INFO | {log_text}")
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, "EventBoard Error", f"Failed to send event: {e}")

	def _send_eventboard_message(self, event_name: str, button_text: str, timestamp: datetime, toggle_state: Optional[bool]) -> None:
		outlet = self.outlets.get("EventBoard")
		if outlet is None:
			return
		msg = f"{event_name}|{button_text}|{timestamp.isoformat()}"
		if toggle_state is not None:
			msg += f"|TOGGLE:{toggle_state}"
		try:
			outlet.push_sample([msg])
		except Exception:
			pass

	# -------------------------- Tray --------------------------
	def _minimize_to_tray(self) -> None:
		self.hide()
		self.tray.show()
		self.tray.showMessage("PhoLogToLabStreamingLayer", "Application minimized to tray.", QtWidgets.QSystemTrayIcon.MessageIcon.Information, 3000)


def run_app(xdf_folder: Path) -> None:
	"""
	Entry point for launching the PyQt6 application.
	"""
	import sys
	app = QtWidgets.QApplication(sys.argv)
	window = MainWindow(xdf_folder=xdf_folder)
	window.show()
	sys.exit(app.exec())


