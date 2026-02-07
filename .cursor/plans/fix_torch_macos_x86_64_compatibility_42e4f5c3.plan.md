---
name: Fix torch macOS x86_64 compatibility
overview: PyTorch 2.7.1+ doesn't provide pre-built wheels for macOS x86_64 (Intel Macs). The resolver is selecting torch 2.10.0 which only supports macOS ARM64. We need to add platform-specific version constraints to use a compatible torch version for macOS x86_64 while keeping newer versions for other platforms.
todos:
  - id: research_torch_versions
    content: Research the last PyTorch version that provided macOS x86_64 wheels and verify compatibility with project requirements
    status: completed
  - id: update_main_project
    content: Update PhoLogToLabStreamingLayer/pyproject.toml with platform-specific torch constraint for macOS x86_64
    status: completed
    dependencies:
      - research_torch_versions
  - id: update_whisper_project
    content: Update whisper-timestamped/pyproject.toml with platform-specific torch constraint for macOS x86_64
    status: completed
    dependencies:
      - research_torch_versions
  - id: verify_compatibility
    content: Verify torchaudio and torchvision versions are compatible with the constrained torch version
    status: completed
    dependencies:
      - update_main_project
      - update_whisper_project
---

# Fix torch macOS x86_64 Compatibility

## Problem

- PyTorch 2.7.1+ doesn't provide pre-built wheels for macOS x86_64 (Intel)
- Current constraints require `torch>=2.7.1` which resolves to 2.10.0
- torch 2.10.0 only has wheels for: Linux (x86_64/aarch64), Windows, macOS ARM64
- User is on `macosx_12_0_x86_64` (macOS 12 Intel)

## Solution

Add platform-specific torch version constraints:

- For macOS x86_64: Use the last torch version that supported Intel Macs (likely 2.0.x or 2.1.x)
- For other platforms: Keep `torch>=2.7.1`

## Implementation

### Files to modify:

1. **[PhoLogToLabStreamingLayer/pyproject.toml](PhoLogToLabStreamingLayer/pyproject.toml)**

- Update line 28: Change `"torch>=2.7.1; platform_system == 'Darwin' and platform_machine == 'x86_64'"` to use a version constraint that supports macOS x86_64 (e.g., `"torch>=2.0.0,<2.1.0; platform_system == 'Darwin' and platform_machine == 'x86_64'"` or the last known compatible version)

2. **[whisper-timestamped/pyproject.toml](whisper-timestamped/pyproject.toml)**

- Update line 37: Add platform-specific constraint for macOS x86_64
- Change `"torch>=2.7.1"` to include macOS x86_64 exception: `"torch>=2.7.1; platform_system != 'Darwin' or platform_machine != 'x86_64'"`
- Add separate line: `"torch>=2.0.0,<2.1.0; platform_system == 'Darwin' and platform_machine == 'x86_64'"` (or appropriate version range)

### Research needed:

- Verify the last torch version that provided macOS x86_64 wheels
- Check if torch 2.0.x or 2.1.x is compatible with the project's requirements
- Ensure torchaudio and torchvision versions are compatible with the constrained torch version

### Alternative considerations:

- If no recent torch version supports macOS x86_64, may need to make torch optional for this platform
- Consider if whisper-timestamped functionality can work without torch on macOS x86_64