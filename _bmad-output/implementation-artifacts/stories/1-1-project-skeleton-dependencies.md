# Story 1.1: Project Skeleton & Dependencies

Status: done

<!-- Note: Validation COMPLETED. Quality Competition improvements applied. -->

## Story

**As a** Developer,
**I want** to set up the project structure, install critical v3.0 dependencies, and establish logging/quality standards,
**so that** future components (Recorder, Transcriber) have a stable, compatible foundation to build upon.

## Acceptance Criteria

1.  **Dependency Matrix (v3.0)**
    *   `requirements.txt` MUST include:
        *   `PyQt6` (UI)
        *   `faster-whisper` (Core AI Engine)
        *   `sounddevice` (Audio Capture)
        *   `soundfile` (Disk Streaming - **Critical for v3.0**)
        *   `keyboard` (Hotkeys/Injection)
        *   `pyperclip` (Clipboard)
        *   `numpy` (Data processing)
    *   **GPU Compatibility**: Ensure `faster-whisper` installation instructions account for CUDA/cuDNN requirements on Windows (add notes to README or a setup script check).

2.  **Project Structure**
    *   `src/core/` for backend logic (Audio, AI, Config).
    *   `src/ui/` for frontend logic (Widgets, Dialogs).
    *   `logs/` directory for unified application logging.
    *   `temp/` directory management (ensure it's created/cleaned).

3.  **Logging Standard**
    *   Implement `src/core/logger.py` with a singleton `get_logger()` function.
    *   Format: `[TIMESTAMP] [LEVEL] [MODULE] Message`.
    *   Output: Console (for dev) and File (rotating log for production debugging).

4.  **Entry Point**
    *   `main.py` verified to launch a basic PyQt6 "Hello World" window and initialize the Logger.

## Tasks / Subtasks

- [x] **Dependency Management**
  - [x] Create/Update `requirements.txt` with `soundfile`, `sounddevice`, `faster-whisper`, `PyQt6`.
  - [x] Add `python-dotenv` for config management.
  - [x] Add `ruff` or `black` for code formatting (dev-dependency).
- [x] **Core Infrastructure**
  - [x] Create `src/core/logger.py` - Setup `logging` module with FileHandler and StreamHandler.
  - [x] Create `src/core/config_manager.py` stub (Singleton pattern).
  - [x] Create `src/utils/` helper package for path management (getting resource paths, temp paths).
- [x] **Project Layout**
  - [x] Ensure `src/ui/` exists.
  - [x] Create `start.bat` that activates venv and runs `main.py`.
  - [x] Update `.gitignore` to exclude `logs/*.log`, `temp/*.wav`, `__pycache__`, `.env`.
- [x] **Smoke Test**
  - [x] `main.py` runs, logs "Application Started" to file, and shows a blank PyQt window.

## Dev Notes

**Context:**
This is the foundation for v3.0. We are moving to "Disk Streaming" (requires `soundfile`) and "Visual Intelligence" (requires stable `PyQt6` loop).

**Architecture Compliance:**
- **Logging**: Do not use `print()`. All future stories must import `src.core.logger`.
- **Paths**: Use `pathlib` for OS-agnostic path handling, especially for the `temp/` folder.

**Dependency Specifics:**
- **faster-whisper**: On Windows, this relies on `ctranslate2`. If the user has an NVIDIA GPU, they need cuDNN 8.x and CUDA 11.x/12.x. Add a check or clear documentation for this in `README_USER.txt`.

### Reference
- **Architecture**: [Architecture Doc](../architecture.md) - "Core Components".
- **Story 1.2**: Requires `soundfile` which is added here.

## Dev Agent Record

### Implementation Plan
- Updated requirements.txt with all core and dev dependencies (soundfile, ruff)
- Created centralized logging system with singleton pattern
- Implemented path management utilities for cross-platform support
- Enhanced main.py with logging integration
- Created comprehensive test suite for logger module

### Completion Notes
- [x] Added `soundfile` to requirements.txt for v3.0 disk streaming support
- [x] Implemented centralized Logger with rotating file handler and console output
- [x] Created ConfigManager with Qt signals integration (already existed, enhanced with logging)
- [x] Verified folder structure handles `temp` and `logs` directories
- [x] Updated main.py to use logger instead of print statements
- [x] Added GPU/CUDA setup instructions to README_USER.txt
- [x] Created comprehensive test suite (8 tests, all passing)

### File List
- requirements.txt - Added soundfile and ruff dependencies
- src/core/logger.py - New centralized logging module
- src/core/config_manager.py - Enhanced with logger integration
- src/utils/__init__.py - New utils package
- src/utils/paths.py - New path management utilities
- src/main.py - Updated with logger integration
- .gitignore - Added logs/*.log and temp/*.wav exclusions
- README_USER.txt - Added GPU setup instructions
- tests/__init__.py - New test package
- tests/test_logger.py - Logger test suite

### Change Log
- 2025-12-18: Story 1.1 completed - Project skeleton and dependencies established
