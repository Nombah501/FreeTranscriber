# Architecture Documentation

## Executive Summary
FreeTranscriber is a local, privacy-focused audio transcription tool. It uses a **client-side AI model** (Faster-Whisper) to convert speech to text without sending data to the cloud. The application is architected as a **Desktop Monolith** using Python and PyQt6.

## Architectural Patterns
- **Model-View-Controller (MVC)**:
    - **Model**: `ConfigManager` (Settings), `Transcriber` (AI Logic), `AudioRecorder` (Audio Data).
    - **View**: `FloatingButton`, `SettingsDialog` (PyQt6 Widgets).
    - **Controller**: `AppController` (in `main.py`) coordinates interactions.
- **Event-Driven**: Heavily relies on **Qt Signals & Slots** for decoupled communication between components.
- **Threaded Processing**: Heavy AI tasks run in background `QThread`s to keep the UI responsive.

## High-Level Diagram

```mermaid
graph TD
    User[User] -->|Click/Hotkey| UI[Floating UI]
    UI -->|Signal| Controller[AppController]
    
    subgraph Core Logic
        Controller -->|Control| Recorder[AudioRecorder]
        Controller -->|Start Job| Worker[TranscribeWorker (Thread)]
        Worker -->|Use| Transcriber[Transcriber (Faster-Whisper)]
        Controller -->|Read/Write| Config[ConfigManager]
    end
    
    subgraph I/O
        Recorder -->|Audio Stream| Mic[Microphone]
        Transcriber -->|Text| Clipboard
        Transcriber -->|Text| Keyboard[Keyboard Simulation]
    end

    Config -->|Signal: Config Changed| UI
    Config -->|Signal: Config Changed| Transcriber
```

## Core Components

### 1. AppController (`main.py`)
The central hub. It initializes the app, manages the system tray, and bridges the gap between the UI and core logic.
- **Responsibilities**: 
    - Handling global hotkeys (via `HotkeyBridge` for thread safety).
    - Managing the recording state machine.
    - Spawning `TranscribeWorker` threads.
    - Handling success/error feedback loops.

### 2. Configuration Management (`config_manager.py`)
A reactive configuration store.
- **Features**:
    - Persists settings to `config.json`.
    - Emits `config_changed(key, value)` signal.
    - Components subscribe to this signal to update instantly (e.g., changing opacity, switching models) without restart.

### 3. Audio Recorder (`audio_recorder.py`)
Handles raw audio capture.
- **Technology**: `sounddevice` (PortAudio wrapper).
- **Flow**: Captures `float32` samples -> Stores in RAM list -> Writes to temporary `.wav` file on stop.

### 4. Transcriber (`transcriber.py`)
The AI engine wrapper.
- **Technology**: `faster-whisper` (CTranslate2 backend).
- **Optimization**: Caches the loaded model in memory. Only reloads if the user changes the `model_size` or `device` setting.
- **Fallback**: Attempts to fall back to CPU/int8 if CUDA/float16 fails.

## Data Flow

1.  **Recording**: User triggers Hotkey -> `AppController` calls `Recorder.start()`.
2.  **Stop & Save**: User triggers Hotkey -> `Recorder` saves WAV -> returns `file_path`.
3.  **Transcription**: `AppController` starts `TranscribeWorker` with `file_path`.
4.  **Processing**: `Transcriber` loads model (if needed) -> processes WAV -> returns Text.
5.  **Output**: `AppController` puts Text in Clipboard AND simulates keystrokes to type it into the active window.

## Threading Model
- **Main Thread**: Runs the Qt Event Loop (UI, Input handling).
- **Worker Thread**: One-off `QThread` created for *each* transcription task. This prevents the UI from freezing during the 2-10 second transcription process.
