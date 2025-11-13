import sys
import socket
import argparse
from pathlib import Path

from PyQt6 import QtWidgets

from phologtolabstreaminglayer.ui_qt.main_window import run_app


# Singleton lock (simple socket bind) mirrors previous behavior
PROGRAM_LOCK_PORT = int(
	Path.cwd().joinpath(".port").read_text().strip()  # optional override if file exists
).__int__() if Path.cwd().joinpath(".port").exists() else 13379


def is_instance_running() -> bool:
	try:
		test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		test_socket.bind(("localhost", PROGRAM_LOCK_PORT))
		test_socket.close()
		return False
	except OSError:
		return True


def main(xdf_folder: Path, unsafe: bool = False) -> None:
	if not unsafe and is_instance_running():
		# Minimal QMessageBox to preserve UX
		app = QtWidgets.QApplication(sys.argv)
		QtWidgets.QMessageBox.critical(None, "Instance Already Running",
			"Another instance of LSL Logger is already running.\n"
			"Only one instance can run at a time.\n"
			"To override this safety check, launch with --unsafe.")
		sys.exit(1)

	run_app(xdf_folder=xdf_folder)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="PhoLogToLabStreamingLayer")
	parser.add_argument("--unsafe", action="store_true", help="Override safety checks and allow multiple instances")
	args = parser.parse_args()
	unsafe = args.unsafe

	_default_xdf_folder = Path(r"E:\Dropbox (Personal)\Databases\UnparsedData\PhoLogToLabStreamingLayer_logs").resolve()
	main(xdf_folder=_default_xdf_folder, unsafe=unsafe)


