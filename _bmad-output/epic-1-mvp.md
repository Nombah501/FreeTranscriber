# Epic 1: MVP - FreeTranscriber Core

## Overview
Build the core functionality of FreeTranscriber: a lightweight, always-on-top voice typing tool for Windows.
This epic covers the complete vertical slice from UI to Audio Recording to Transcription and Text Injection.

## User Stories

### Story 1.1: Project Skeleton & Dependencies
**As a** Developer
**I want to** set up the project structure and install necessary libraries
**So that** I can start building the application components.

**Acceptance Criteria:**
- `requirements.txt` includes `PyQt6`, `faster-whisper`, `sounddevice`, `keyboard`, `pyperclip`, `scipy`, `numpy`.
- Project folder structure created (`src/core`, `src/ui`, etc.).
- `main.py` entry point created.
- Build system/scripts verified.

---

### Story 1.2: Audio Recording Module
**As a** User
**I want** the application to record my voice when I trigger it
**So that** my speech can be captured for transcription.

**Acceptance Criteria:**
- `AudioRecorder` class implemented.
- Supports Start/Stop recording actions.
- Saves audio to a temporary `.wav` file.
- Handles default input device correctly.

---

### Story 1.3: Whisper Transcriber Service
**As a** User
**I want** my recorded audio to be transcribed locally
**So that** my voice is converted to text without sending data to the cloud.

**Acceptance Criteria:**
- `Transcriber` class implemented using `faster-whisper`.
- Runs in a separate thread (QThread) to avoid freezing UI.
- Auto-detects GPU (CUDA) or CPU.
- Loads 'base' or 'small' model by default.

---

### Story 1.4: Floating UI (PyQt6)
**As a** User
**I want** a small, unobtrusive floating widget
**So that** I can control the app without it taking up screen space.

**Acceptance Criteria:**
- Frameless, circular widget that stays "Always on Top".
- Semi-transparent (0.6 opacity) when idle, Opaque (1.0) when active/hovered.
- Click handler toggles recording state.
- Visual feedback (pulsing or color change) during recording.

---

### Story 1.5: Global Hotkey & Input Injection
**As a** User
**I want** to start recording with a keyboard shortcut and have text appear where I am typing
**So that** I can use the tool seamlessly in any application.

**Acceptance Criteria:**
- Global hotkey (e.g., `Ctrl+Shift+Space`) triggers recording.
- `type_text` function injects text using `keyboard` or clipboard paste.
- Works even when the app is not in focus.

---

### Story 1.6: Integration & Polish
**As a** User
**I want** all components to work together reliably
**So that** I have a smooth experience.

**Acceptance Criteria:**
- UI triggers Recorder -> Recorder sends file to Transcriber -> Transcriber sends text to Input Handler.
- Error handling for missing microphone or model load failures.
- Basic configuration file for settings.
