---
name: Stream Discovery and Shutdown Reliability Fixes
overview: Add thread-safe guards and proper shutdown sequencing to prevent race conditions and crashes during stream discovery and application shutdown.
todos: []
---

# Stream Discovery and Shutdown Reliability Fixes

## Overview

This plan addresses race conditions in stream discovery and ensures robust shutdown sequencing to prevent crashes when threads access shared resources during cleanup.

## Issues Identified

### Stream Discovery Reliability

1. **Race condition**: `stream_discovery_worker` (background thread) and GUI methods (main thread) both modify `self.discovered_streams` and `self.selected_streams` without synchronization
2. **KeyError risk**: `get_selected_streams()` iterates `selected_streams` then accesses `discovered_streams[stream_key]` - stream may be removed between iteration and access
3. **GUI updates after shutdown**: `update_stream_display()` and `update_stream_tree_display()` don't check `_shutting_down` before accessing shared state
4. **Concurrent modification**: `refresh_streams()` (main thread) directly modifies `discovered_streams` while `stream_discovery_worker` (background thread) may be modifying it

### Shutdown Robustness

1. **Resource cleanup order**: `on_closing()` deletes `self.inlets` before ensuring `legacy_recording_worker` has fully stopped
2. **Missing shutdown checks**: `legacy_recording_worker` doesn't check `_shutting_down` or if `self.inlets` is `None` before accessing
3. **Mid-iteration shutdown**: `stream_discovery_worker` checks `_shutting_down` in while condition but may access shared state after shutdown starts
4. **Join timeout risk**: If threads don't stop within 2.0s timeout, resources are cleaned up anyway, causing potential crashes

## Implementation Plan

### 1. Add Thread Lock for Stream Discovery State

**File**: [`src/phologtolabstreaminglayer/logger_app.py`](src/phologtolabstreaminglayer/logger_app.py)

- Add `self._stream_discovery_lock = threading.Lock()` in `__init__` (around line 109)
- Use this lock to protect all access to `self.discovered_streams` and `self.selected_streams`

### 2. Protect Stream Discovery Worker

**File**: [`src/phologtolabstreaminglayer/logger_app.py`](src/phologtolabstreaminglayer/logger_app.py)

- In `stream_discovery_worker()` (line 1853):
- Wrap dictionary updates (lines 1877-1891) with lock: `with self._stream_discovery_lock:`
- Add `_shutting_down` check before accessing `self.discovered_streams.keys()` (line 1879)
- Add `_shutting_down` check before scheduling GUI updates (line 1894)

### 3. Protect GUI Methods Accessing Stream State

**File**: [`src/phologtolabstreaminglayer/logger_app.py`](src/phologtolabstreaminglayer/logger_app.py)

- In `get_selected_streams()` (line 1953):
- Wrap with lock and add try/except for KeyError: `with self._stream_discovery_lock: ... try: ... except KeyError: continue`
- In `select_stream()` (line 1944):
- Wrap with lock: `with self._stream_discovery_lock:`
- In `auto_select_own_streams()` (line 1962):
- Wrap with lock: `with self._stream_discovery_lock:`
- In `update_stream_display()` (line 1926):
- Add `if self._shutting_down: return` at start
- Wrap `self.discovered_streams` access with lock
- In `update_stream_tree_display()` (line 2039):
- Add `if self._shutting_down: return` at start
- Wrap `self.discovered_streams` access with lock
- In `refresh_streams()` (line 1989):
- Wrap `self.discovered_streams` assignment (line 2009) with lock: `with self._stream_discovery_lock:`
- In `select_all_streams()` (line 2026):
- Wrap with lock: `with self._stream_discovery_lock:`
- In `select_no_streams()` (line 2033):
- Wrap with lock: `with self._stream_discovery_lock:`

### 4. Protect Legacy Recording Worker

**File**: [`src/phologtolabstreaminglayer/logger_app.py`](src/phologtolabstreaminglayer/logger_app.py)

- In `legacy_recording_worker()` (line 1389):
- Add shutdown check in while condition: `while self.recording and self.has_any_inlets and not self._shutting_down:`
- Add guard before accessing `self.inlets.items()`: `if self._shutting_down or self.inlets is None: break`
- Add guard at start of loop iteration (after line 1393)

### 5. Improve Shutdown Sequencing

**File**: [`src/phologtolabstreaminglayer/logger_app.py`](src/phologtolabstreaminglayer/logger_app.py)

- In `on_closing()` (line 2074):
- Ensure `_shutting_down = True` is set first (already done)
- After `stop_recording()` and `stop_stream_discovery()`, add explicit wait:
- Check if threads are still alive after join timeout
- Log warning if threads didn't stop cleanly
- Only delete `self.inlets` and `self.outlets` after confirming threads have stopped
- Add guard: `if self.inlets is not None:` before deletion loop

### 6. Add Safety Check in has_any_inlets Property

**File**: [`src/phologtolabstreaminglayer/logger_app.py`](src/phologtolabstreaminglayer/logger_app.py)

- In `has_any_inlets` property (line 156):
- Add `_shutting_down` check: `if self._shutting_down: return False`
- This prevents property access during shutdown

## Testing Considerations

- Verify no crashes when closing app during active recording
- Verify no crashes when closing app during active stream discovery
- Verify stream discovery continues working normally with lock overhead
- Verify GUI updates don't cause issues during shutdown

## Risk Assessment

- **Low risk**: Adding locks and shutdown checks is defensive and shouldn't break existing functionality