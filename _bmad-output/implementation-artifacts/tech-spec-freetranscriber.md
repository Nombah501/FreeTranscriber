# Tech-Spec: FreeTranscriber (Local AI Voice Typer)

**Created:** 2025-12-18
**Status:** Ready for Development

## Overview

### Problem Statement
The user needs a quick, free, and private way to transcribe voice to text on a Windows PC to speed up interaction with CLI/AI tools. Existing tools are either paid, cloud-based (slow/non-private), or lack seamless integration (typing directly into the target app).

### Solution
A lightweight, modern Python desktop application that runs in the background. It provides a floating, semi-transparent widget ("Always on Top").
- **Core Function:** Records audio -> Transcribes via local Whisper model -> Inserts text directly into the active window (and clipboard).
- **UX:** Minimalist. Single click or Hotkey to start/stop.
- **Privacy:** 100% offline using `faster-whisper`.

### Scope (In/Out)
**In Scope:**
- Modern GUI (PyQt6) with transparency and "Always on Top" behavior.
- **Async Architecture:** Transcription runs in a separate thread to prevent UI freezing.
- **UX Enhancements:** Pulsing animation during recording.
- Global Hotkey support (e.g., `Ctrl+Shift+Space`).
- Audio recording with `sounddevice`.
- Local transcription using `faster-whisper` (optimized for CPU/GPU).
- **Hardware Handling:** Auto-detect GPU (CUDA) vs CPU.
- Text output modes: Clipboard Copy + Keyboard Emulation (Typewriter style).
- Settings: Select model size (tiny/base), hotkey configuration, **select input device**.

**Out of Scope:**
- Multi-speaker diarization (identifying who is speaking).
- Translation to languages other than English/Russian (Whisper supports it, but UI won't focus on it initially).
- Mobile version.

## Context for Development

### Technical Stack
- **Language:** Python 3.10+
- **GUI Framework:** `PyQt6` (robust window management for overlay capabilities).
- **AI Model:** `faster-whisper` (CTranslate2 backend, efficient for local execution).
- **Audio:** `sounddevice`, `numpy`, `scipy` (wav file generation).
- **System IO:** `keyboard` (global hotkeys & typing), `pyperclip` (clipboard).

### Architecture
- **`main.py`**: Entry point, initializes the Qt Application.
- **`ui/overlay_window.py`**: The floating widget logic (transparency, drag-and-drop, animations).
- **`core/audio_recorder.py`**: Handles microphone stream and saving `.wav` files. Selectable device ID.
- **`core/transcriber.py`**: Wraps the `faster-whisper` model loading and inference. Runs in QThread/background worker.
- **`core/input_handler.py`**: Manages global hotkeys and text injection.

### Technical Decisions
- **Why `faster-whisper`?** Much faster than standard OpenAI whisper on CPUs, essential for a seamless "voice typing" feel on average hardware.
- **Why PyQt6?** Provides the most control over window flags (Frameless, WindowStaysOnTopHint, Tool) required for the floating widget.
- **Async Logic:** Using `QThread` for heavy lifting (Model Load, Transcribe) to keep the `QTimer` based animations smooth.

## Implementation Plan

### Tasks

- [ ] **Task 1: Project Skeleton & Dependencies**
    - Set up `requirements.txt` (`PyQt6`, `faster-whisper`, `sounddevice`, `keyboard`, `pyperclip`, `scipy`, `numpy`).
    - Create folder structure.

- [ ] **Task 2: Audio Recording Module**
    - Implement `AudioRecorder` class.
    - Support Start/Stop recording.
    - Support device selection.
    - Save audio to a temporary `.wav` file.

- [ ] **Task 3: Whisper Transcriber Service**
    - Implement `Transcriber` class.
    - Implement Async Worker (QThread) for non-blocking transcription.
    - Load `faster-whisper` model (default to 'base' or 'small' for speed).
    - Auto-detect 'cuda' or 'cpu'.

- [ ] **Task 4: Floating UI (PyQt6)**
    - Create a frameless, circular widget.
    - Implement "Always on Top" and semi-transparency (opacity 0.6 idle, 1.0 active).
    - Add click handler to toggle recording.
    - Add pulsing animation (stylesheet or paintEvent updates).

- [ ] **Task 5: Global Hotkey & Input Injection**
    - Integrate `keyboard` library to listen for hotkey in background thread.
    - Implement `type_text(text)` function using `keyboard.write()` and `pyperclip.copy()`.

- [ ] **Task 6: Integration & Polish**
    - Connect UI -> Recorder -> Transcriber -> Input Handler.
    - Add error handling (e.g., no microphone, no ffmpeg).
    - Create a simple settings file (config.json) for model selection.

### Acceptance Criteria

- [ ] **AC 1: Overlay Widget**
    - App launches as a small icon floating over other windows.
    - Can be dragged to move positions.
    - Becomes opaque when hovered or recording.

- [ ] **AC 2: Recording Flow**
    - Pressing Hotkey OR Clicking Icon starts recording immediately.
    - Visual indicator changes (Red/Pulse).
    - Pressing again stops recording.

- [ ] **AC 3: Transcription & Output**
    - Within 2-5 seconds (depending on PC), text appears in the active text field.
    - UI remains responsive during transcription.
    - Text is also available in clipboard (Ctrl+V works).

## Additional Context

### Dependencies
- Requires `FFmpeg` installed on the user's system (standard for audio processing). *We must provide instructions or a script to check/install this.*

### Testing Strategy
- Manual testing of the overlay behavior on Windows 10/11.
- Verification of hotkey functioning while other apps are focused (Browser, Terminal).