---
name: File-Based PID Locking for SingletonInstanceMixin
overview: Replace socket-based singleton lock with file-based PID tracking that works cross-platform, handles permission errors gracefully, and automatically detects stale locks from crashed processes.
todos: []
---

# File-Based PID Locking for SingletonInstanceMixin

## Overview

Replace the socket-based singleton lock mechanism with a file-based approach using PID tracking. This eliminates TIME_WAIT issues, automatically detects stale locks from crashed processes, and works reliably across Windows, Linux, and macOS without requiring elevated permissions.

## Current Implementation

- Uses socket binding to `localhost:port` for locking
- `is_instance_running()` checks if port is available
- `acquire_singleton_lock()` binds to port
- `release_singleton_lock()` closes socket
- Issues: TIME_WAIT delays, no stale lock detection

## New Implementation Strategy

### 1. Lock File Location (Cross-Platform)

**File**: [`src/phopylslhelper/mixins/app_helpers.py`](src/phopylslhelper/mixins/app_helpers.py)

- Use platform-appropriate temp directory:
- Windows: `%TEMP%` or `%LOCALAPPDATA%` (fallback to user home)
- Linux/macOS: `$TMPDIR` or `/tmp` (fallback to user home)
- Lock file name: `.phologtolabstreaminglayer_lock_{port}.pid` (or similar)
- Use `tempfile.gettempdir()` with fallback to `Path.home()`
- Store full path in instance variable for cleanup

### 2. Replace `is_instance_running()` Classmethod

**File**: [`src/phopylslhelper/mixins/app_helpers.py`](src/phopylslhelper/mixins/app_helpers.py)

- Get lock file path using helper method
- Check if lock file exists
- If exists:
- Read PID from file (handle read errors gracefully)
- Check if process is alive using `os.kill(pid, 0)` (signal 0 = check only)
- If process is dead or PID invalid: remove stale lock file and return `False`
- If process is alive: return `True`
- If not exists: return `False`
- Handle all exceptions (permission errors, file errors) gracefully:
- Log warning but return `False` (conservative: assume no instance running)
- Don't fail startup

### 3. Replace `acquire_singleton_lock()` Method

**File**: [`src/phopylslhelper/mixins/app_helpers.py`](src/phopylslhelper/mixins/app_helpers.py)

- Get lock file path
- Check if lock file exists and validate:
- If exists, read PID and check if process is alive
- If process is dead: remove stale lock file
- If process is alive: return `False` (another instance running)
- Create lock file atomically:
- Write current PID to file
- Handle write errors (permissions, disk full) gracefully:
    - Log warning but return `True` (allow startup to continue)
    - Store lock file path in `self._lock_file` for cleanup
- Call `mark_instance_running()`
- Return `True` on success

### 4. Replace `release_singleton_lock()` Method

**File**: [`src/phopylslhelper/mixins/app_helpers.py`](src/phopylslhelper/mixins/app_helpers.py)

- Check if `self._lock_file` exists and is set
- Verify we own the lock (read PID and compare with `os.getpid()`)
- Delete lock file (handle errors gracefully, just log)
- Clear `self._lock_file`
- Call `mark_instance_stopped()`

### 5. Update `init_SingletonInstanceMixin()` Method

**File**: [`src/phopylslhelper/mixins/app_helpers.py`](src/phopylslhelper/mixins/app_helpers.py)

- Remove `self._lock_socket = None`
- Add `self._lock_file = None` instead
- Keep port-based identification (still use port number in lock file name)

### 6. Add Helper Methods

**File**: [`src/phopylslhelper/mixins/app_helpers.py`](src/phopylslhelper/mixins/app_helpers.py)

- `_get_lock_file_path()`: Returns Path object for lock file
- Uses `tempfile.gettempdir()` with fallback to `Path.home() / ".cache"` or `Path.home()`
- Handles permission errors gracefully
- Creates directory if needed (with permission error handling)
- `_is_process_alive(pid)`: Check if PID is running
- Uses `os.kill(pid, 0)` (cross-platform, signal 0 = check only)
- Handles `ProcessLookupError` (process doesn't exist)
- Handles `PermissionError` (can't check, assume alive for safety)
- Returns `True` if alive, `False` if dead, `None` if uncertain (permission error)
- `_read_lock_file_pid(lock_file_path)`: Read PID from lock file
- Returns `(pid, success)` tuple
- Handles file read errors, invalid PID format
- Returns `(None, False)` on any error
- `_remove_stale_lock(lock_file_path)`: Remove stale lock file
- Handles permission errors gracefully (just log warning)
- Returns success status

## Implementation Details

### Cross-Platform PID Checking

```python
def _is_process_alive(self, pid: int) -> Optional[bool]:
    """Check if process with given PID is alive. Returns True/False/None (uncertain)."""
    try:
        os.kill(pid, 0)  # Signal 0 = check only, doesn't kill
        return True
    except ProcessLookupError:
        return False  # Process doesn't exist
    except PermissionError:
        # Can't check (might be different user), assume alive for safety
        return None  # Uncertain
    except OSError:
        return None  # Other OS error, uncertain
```

### Lock File Path Strategy

- Primary: `tempfile.gettempdir()` (OS-provided temp directory)
- Fallback: `Path.home() / ".cache"` (Linux/macOS) or `Path.home()` (Windows)
- Lock file: `{temp_dir}/.phologtolabstreaminglayer_lock_{port}.pid`
- Handle permission errors: if can't write to temp, try home directory

### Error Handling Philosophy

- **Permission errors**: Log warning, continue (don't block startup)
- **File I/O errors**: Log warning, assume no lock exists (conservative)
- **Invalid PID in file**: Treat as stale, remove and continue
- **Race conditions**: Use atomic file operations where possible

## Testing Considerations

- Test on Windows, Linux, macOS
- Test with permission restrictions (read-only temp dir)
- Test with stale lock files (valid PID but dead process)
- Test with invalid lock files (corrupted, wrong format)
- Test concurrent startup attempts
- Verify lock is released on normal shutdown
- Verify lock is detected as stale after crash

## Backward Compatibility

- Maintains same API: `is_instance_running()`, `acquire_singleton_lock()`, `release_singleton_lock()`
- Still uses port number for lock file identification (backward compatible with existing environment variables)
- No changes needed in `logger_app.py` or other consumers

## Risk Assessment

- **Low risk**: Changes are isolated to `SingletonInstanceMixin` class
- **Graceful degradation**: Permission errors result in warnings, not failures