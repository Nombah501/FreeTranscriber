# Story 1.2: Audio Recording Module

Status: done

<!-- Note: Validation COMPLETED. Quality Competition improvements applied. -->

## Story

**As a** User,
**I want** the application to record my voice when I trigger it,
**so that** my speech can be captured for transcription without freezing my computer or losing data.

## Acceptance Criteria

1.  **Engine**
    *   Class `AudioRecorder` refactored/implemented in `src/core/audio_recorder.py`.
    *   **Strict 16kHz**: Audio MUST be saved as 16kHz, Mono, Float32 (Faster-Whisper native format). If the input device runs at 44.1/48kHz, the recorder must handle resampling on-the-fly or configure the stream to 16kHz.
    *   **Disk Streaming**: Audio data must be written to a temporary `.wav` file in chunks using `soundfile` (not RAM-heavy lists).
    *   **Thread Safety**: Use `queue.Queue` to transfer audio blocks from the high-priority audio callback to a separate file-writer thread/consumer.

2.  **Visual Feedback (Smart Pill Support)**
    *   **Waveform Data**: The recorder must emit a real-time signal (e.g., `amplitude_changed(float)`) with the RMS (Root Mean Square) volume level (0.0 to 1.0) ~30-60 times per second for the UI animation.

3.  **Reliability & Cleanup**
    *   **Temp File Hygiene**: The system must track created temporary files. `FR19`: Files must be auto-deleted when `reset()` is called or on app exit.
    *   **Error Handling**:
        *   Detect `device_lost` or stream errors (e.g., USB mic unplugged).
        *   Emit a specific signal `error_occurred(str)` so the UI can show the "Orange" error state.
        *   Fail gracefully (no crashes) if the device is unavailable.

4.  **Control**
    *   Non-blocking `start()` and `stop()` methods.
    *   `stop()` must cleanly flush the file buffer, close the file handle, and return the absolute path to the saved `.wav`.

## Tasks / Subtasks

- [x] **Dependency Update**
  - [x] Add `soundfile` and `resampy` (if needed for high-quality resampling, otherwise `scipy` or `samplerate`) to `requirements.txt`.
- [x] **Core Implementation (`AudioRecorder`)**
  - [x] Implement `__init__` with `queue.Queue` and threading flags.
  - [x] Create `_audio_callback`:
    - [x] Calculate RMS amplitude for UI visualization.
    - [x] Emit `amplitude_signal`.
    - [x] Put copy of `indata` into Queue.
  - [x] Create `_file_writer_thread`:
    - [x] Continuously pull from Queue.
    - [x] Write to `soundfile.SoundFile`.
    - [x] Handle Stop signal to close file.
  - [x] Implement `start_recording()`:
    - [x] Setup `sounddevice.InputStream` with **16000 Hz** target rate.
    - [x] Start writer thread.
  - [x] Implement `stop_recording()`:
    - [x] Signal threads to stop.
    - [x] Join threads.
    - [x] Return file path.
- [x] **Error & Cleanup Logic**
  - [x] Wrap stream creation in try/except blocks to catch hardware failures.
  - [x] Implement `cleanup_temp_files()` method to remove old recordings.
  - [x] Add `__del__` or `atexit` handler for safety.
- [x] **Review Fixes (AI)**
  - [x] Replaced fake 16kHz test with real mock-based test.
  - [x] Removed blocking logging from audio callback.
  - [x] Fixed race condition in start_recording (zombie thread check).
  - [x] Added missing resampy dependency.
  - [x] Extracted magic numbers to constants.

## Dev Notes

**Context:**
This is the heart of the "Smart Pill" experience. If this module lags, the UI lags. If this module crashes, the user loses trust. The move to **Disk Streaming** is non-negotiable for v3.0 stability.

**Architecture Compliance:**
- **Library**: Use `soundfile` for writing. It is more robust than `scipy.io.wavfile` for streaming.
- **Signals**: Do not depend on PyQt signals inside the audio callback directly if it causes lag. Consider using a thread-safe deque or specific QThread slot mechanism if needed, but standard Signals usually work fine for 60Hz updates.
- **Resampling**: Whisper implies 16kHz. Sending 48kHz wastes CPU during transcription (Whisper will downsample it anyway). Downsample at capture time if possible.

**Anti-Patterns (DO NOT DO):**
- ❌ storing `self.audio_data = []` (RAM accumulation).
- ❌ blocking the `_audio_callback` with complex math or file I/O.
- ❌ using `wave` module directly (verbose/error-prone for float32).

### Reference
- **PRD**: FR1 (Recording), FR3 (Disk Buffering), FR10 (Waveform), FR19 (Cleanup).
- **Tech Stack**: `sounddevice` (PortAudio), `soundfile` (libsndfile).

## Dev Agent Record

### Implementation Plan
- Complete refactor of AudioRecorder from RAM-based to disk streaming architecture
- Implemented queue-based threading for non-blocking audio writes
- Added PyQt signals for real-time amplitude feedback and error handling
- Created comprehensive test suite covering all edge cases

### Completion Notes
- [x] Validated `soundfile` installation and integration
- [x] Confirmed strict 16kHz output format with mono float32
- [x] Implemented RMS amplitude calculation (~30-60 Hz UI updates)
- [x] Created thread-safe queue architecture for audio data transfer
- [x] Implemented file writer thread with graceful shutdown
- [x] Added error handling for device failures with fallback to default
- [x] Implemented cleanup mechanism with atexit registration
- [x] Replaced all print statements with logger
- [x] Created 11 comprehensive unit tests (all passing)
- [x] **Code Review Passed**: Critical issues fixed (tests, threading, performance).

### File List
- src/core/audio_recorder.py - Complete refactor with disk streaming
- tests/test_audio_recorder.py - New comprehensive test suite (11 tests)

### Change Log
- 2025-12-18: Story 1.2 completed - Audio Recording Module with disk streaming
- 2025-12-19: Code Review fixes applied (tests, race conditions, perf)


### Technical Highlights
- **Disk Streaming**: Zero RAM accumulation, direct write to soundfile
- **Threading**: Separate writer thread prevents audio callback blocking
- **Thread Safety**: Queue-based communication between audio and writer threads
- **Error Resilience**: Graceful device failure handling with fallback
- **Cleanup**: Automatic temp file management via atexit
- **Signals**: amplitude_changed(float) and error_occurred(str) for UI integration
