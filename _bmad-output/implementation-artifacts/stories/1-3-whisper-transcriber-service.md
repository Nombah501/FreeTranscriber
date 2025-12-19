# Story 1.3: Whisper Transcriber Service

Status: done

<!-- Note: Validation COMPLETED. Quality Competition improvements applied. -->

## Story

**As a** User,
**I want** my recorded audio to be transcribed locally using a high-performance AI model,
**so that** I get accurate text results without internet access or data privacy risks.

## Acceptance Criteria

1.  **Engine & Performance**
    *   **Faster-Whisper**: Must use `faster-whisper` (CTranslate2 backend) for inference, NOT `openai-whisper` or API calls.
    *   **Hardware Acceleration**: Auto-detects `device="cuda"` (NVIDIA GPU). Falls back to `device="cpu"` (INT8) if CUDA is unavailable or fails.
    *   **Optimization**: Explicitly uses `compute_type="float16"` for CUDA and `compute_type="int8"` for CPU to maximize performance/compatibility.

2.  **Smart Memory Management (FR5)**
    *   **Dynamic Loading**: The model must NOT load in `__init__`. It should load on demand (first transcription) or via explicit pre-load signal.
    *   **Unloading Mechanism**: Implement `unload_model()` method that:
        1.  Deletes the `WhisperModel` instance.
        2.  Runs `gc.collect()` to force memory release.
        3.  Resets internal state to indicate "unloaded".

3.  **Config & Threading**
    *   **Config Reactive**: Subscribes to `config_manager` signals. If `model_size` changes (e.g., 'base' -> 'small'), the *next* transcription triggers a reload.
    *   **Thread Safety**: The `transcribe()` method must be blocking and thread-safe, designed to be called from a `QThread` worker (in `main.py`), NOT the main UI thread.

4.  **Error Handling**
    *   **Graceful Fallback**: If `cuda` fails to load (OOM or driver issue), automatically attempt to fall back to `cpu` (INT8) and log the warning.
    *   **Corrupt Audio**: Handle 0-byte or corrupt wav files without crashing. Return empty string or specific error code.

## Tasks / Subtasks

- [x] **Core Class Upgrade (`src/core/transcriber.py`)**
  - [x] Refactor `__init__` to be lightweight (do NOT load model).
  - [x] Implement `_load_model_internal(size, device)` with try/except for fallback logic.
  - [x] Implement `unload_model()` with `gc.collect()`.
  - [x] Update `transcribe(audio_path)`:
    - [x] Check if model is loaded; load if needed.
    - [x] Use `beam_size=5` (default) but allow config override if present.
    - [x] Return text string.
- [x] **Signal Integration**
  - [x] Connect `config_manager.signal_config_changed` (if available) or implement a `on_config_changed` slot to set a `_dirty` flag, forcing reload on next usage.
- [x] **Unit/Integration Testing**
  - [x] Verify `cuda` detection works (or mocks correctly on CPU dev env).
  - [x] Verify `unload_model` actually releases RAM (monitor process memory if possible, or trust `gc`).

## Dev Notes

**Architecture Compliance:**
- **File**: `src/core/transcriber.py`.
- **Input**: Expects **16kHz, Mono, Float32** WAV files (from Story 1.2).
- **Output**: Clean text string.
- **Dependency**: `faster-whisper`, `torch` (optional, only if needed for cuda checks, but `ctranslate2` usually handles it), `gc`.

**Previous Story Intelligence (1.2 Audio Recorder):**
- The recorder produces standard wav files. Ensure `transcribe` checks `os.path.getsize(path) > 0` before passing to Whisper to avoid C++ errors on empty files.
- **Avoid Reinventing**: The `Transcriber` class already exists in a basic form. **Refactor** it, do not delete and rewrite from scratch unless necessary. Preserve the `ConfigManager` injection pattern.

**Smart Memory Logic:**
- **Why?** User wants to leave app running 24/7. 2GB VRAM usage while idle is unacceptable.
- **Strategy**: The Controller (Story 1.6) will handle the *timer* to call `unload_model()`. The `Transcriber` class just needs to provide the *capability* to unload and auto-reload.

**Technical Specifics (Web Research):**
- `del self.model` is required.
- `gc.collect()` is highly recommended for CTranslate2 bindings.
- `device="auto"` in `faster-whisper` is good, but explicit "cuda"/"cpu" logic allows for better error handling (e.g. fallback).

**Anti-Patterns (DO NOT DO):**
- ❌ Loading the model in the global scope or module level.
- ❌ Swallowing exceptions in `transcribe` without returning an error signal/string.
- ❌ Hardcoding `model_size="base"`. Use `self.config.get("model_size", "base")`.

### Reference
- **PRD**: FR5 (Unload), FR6 (Hardware Detect), FR7 (Model Size).
- **Library**: `faster-whisper` documentation regarding memory freeing.

## Dev Agent Record

### Implementation Plan
- Refactor Transcriber for lazy loading and smart memory management
- Implement CUDA auto-detection with CPU fallback
- Add config signal integration for dynamic model reloading
- Create comprehensive test suite with mocking

### Completion Notes
- [x] Confirmed `unload_model` capability with gc.collect()
- [x] Verified fallback logic (CUDA -> CPU with INT8)
- [x] Implemented lazy loading (model NOT loaded in __init__)
- [x] Added config signal subscription for model reload detection
- [x] Implemented _model_dirty flag for efficient reloading
- [x] Added comprehensive error handling (missing/empty files)
- [x] Replaced all print statements with logger
- [x] Created 13 comprehensive unit tests (all passing in 85s)

### File List
- src/core/transcriber.py - Complete refactor with lazy loading and memory management
- tests/test_transcriber.py - New comprehensive test suite (13 tests)

### Change Log
- 2025-12-18: Story 1.3 completed - Whisper Transcriber Service with smart memory management
- 2025-12-19: Senior Developer Review - Fixed critical thread safety issue (QMutex) and added concurrency tests. Story approved.

## Senior Developer Review (AI)
- **Status**: Approved
- **Findings**:
  - **Critical**: Missing thread safety for `transcribe` vs `unload_model`. Fixed by adding `QMutex`.
  - **Medium**: Missing concurrency tests. Fixed by adding `test_concurrency_unload_wait_for_transcribe`.
  - **Low**: Missing type hints. Noted.
- **Outcome**: All critical/high issues resolved. ACs met.
- **Lazy Loading**: Model loads on first transcribe(), not at init
- **Memory Management**: unload_model() with explicit gc.collect() for 24/7 apps
- **CUDA Auto-Detection**: Checks torch.cuda and CTranslate2 availability
- **CPU Fallback**: Automatic fallback from CUDA to CPU (INT8) on failure
- **Config Reactivity**: Subscribes to config_changed signal, marks dirty on model_size/device changes
- **Error Resilience**: Handles missing files, 0-byte files, model load failures
- **Thread-Safe**: Designed for QThread worker execution (blocking transcribe)
