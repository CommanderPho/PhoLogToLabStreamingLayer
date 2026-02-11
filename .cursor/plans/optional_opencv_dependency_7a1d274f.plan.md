---
name: Optional opencv dependency
overview: Make opencv-python an optional extra so platforms that cannot or do not need video metadata can use the library without it; use a lazy import and clear error when the video feature is used without the extra.
todos: []
isProject: false
---

# Make opencv-python optional for PhoPyLSLhelper

## Current state

- [pyproject.toml](PhoPyLSLhelper/pyproject.toml): `opencv-python>=4.5.0` is a **required** dependency.
- [video_metadata.py](PhoPyLSLhelper/src/phopylslhelper/file_metadata_caching/video_metadata.py): Top-level `import cv2` (line 6); `cv2` is only used inside `extract_video_metadata()` (and `extract_file_metadata()` which delegates to it).
- Package **[init**.py](PhoPyLSLhelper/src/phopylslhelper/__init__.py) and [file_metadata_caching/**init**.py](PhoPyLSLhelper/src/phopylslhelper/file_metadata_caching/__init__.py) import `VideoMetadataParser` from `video_metadata`. If `cv2` stays a top-level import in `video_metadata.py`, then importing the package would fail when opencv is not installed.

## Approach

1. **Move opencv to an optional extra** in `pyproject.toml` so installs without video support remain valid.
2. **Lazy-import cv2** only inside the code path that needs it (`extract_video_metadata`), and raise a clear, actionable error if `cv2` is not installed when that code runs. No changes to `__init__.py` are required: the package and `VideoMetadataParser` can be imported without opencv; only calling video extraction will require the extra.

## Implementation

### 1. pyproject.toml

- Remove `"opencv-python>=4.5.0"` from the main `dependencies` list.
- Add an optional-dependencies section with a single extra (e.g. `video`) that includes opencv:

```toml
[project.optional-dependencies]
video = ["opencv-python>=4.5.0"]
```

Users who need video metadata install with: `uv add 'phopylslhelper[video]'` or `pip install phopylslhelper[video]`.

### 2. video_metadata.py

- Remove the top-level `import cv2`.
- At the start of `extract_video_metadata()` (the only method that uses cv2), add a lazy import with a clear error on failure:
  - `try: import cv2` then use `cv2` as today.
  - `except ImportError`: raise an error (e.g. `ImportError` or `RuntimeError`) with a message like:  
  `"Video metadata extraction requires opencv-python. Install with: pip install opencv-python or pip install phopylslhelper[video]"`
- No other methods need changes: `extract_file_metadata()` already delegates to `extract_video_metadata()`, so the lazy import and error will occur when that code path is used.

### 3. No changes to **init**.py

- Keeping `VideoMetadataParser` in the public API is correct: the class is always importable; only the code path that calls `extract_video_metadata` (e.g. `parse_video_folder` or direct `extract_video_metadata` / `extract_file_metadata`) will trigger the need for opencv and the new error message.

### 4. Documentation (optional but recommended)

- In README or project docs, mention that video metadata features require the optional dependency, e.g.  
`pip install phopylslhelper[video]` or `uv add 'phopylslhelper[video]'`.

## Result

- **Without the extra**: `import phopylslhelper` and use of non-video features (e.g. `DataFileMetadataParser`, `BaseFileMetadataParser`, LSL helpers) work. Using `VideoMetadataParser.parse_video_folder()` or `extract_video_metadata()` raises a clear error pointing to installing opencv or the `video` extra.
- **With the extra**: Behavior unchanged; video metadata works as today.

## Summary of file changes


| File                                                                                           | Change                                                                                                                            |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| [pyproject.toml](PhoPyLSLhelper/pyproject.toml)                                                | Remove opencv from `dependencies`; add `[project.optional-dependencies]` with `video = ["opencv-python>=4.5.0"]`.                 |
| [video_metadata.py](PhoPyLSLhelper/src/phopylslhelper/file_metadata_caching/video_metadata.py) | Remove top-level `import cv2`; inside `extract_video_metadata()`, lazy-import `cv2` and on `ImportError` raise a helpful message. |


After implementation, run `uv sync --all-extras` in the repo to regenerate the lockfile so the default environment has no opencv and `uv sync --all-extras` (or installing with `[video]`) includes it for local/dev use.