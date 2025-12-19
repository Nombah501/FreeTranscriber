# Source Tree Analysis

## Project Structure Overview

FreeTranscriber is a monolithic desktop application built with Python and PyQt6. The source code is organized into a single `src` directory with clear separation between core logic and user interface.

```
FreeTranscriber/
├── src/
│   ├── main.py              # Application Entry Point & Controller
│   ├── core/                # Core Business Logic
│   │   ├── audio_recorder.py  # Audio capture via SoundDevice
│   │   ├── config_manager.py  # JSON-based configuration management
│   │   ├── input_handler.py   # Global hotkey and keyboard output
│   │   └── transcriber.py     # AI Wrapper (Faster-Whisper)
│   └── ui/                  # User Interface (PyQt6)
│       ├── overlay_window.py  # Main floating widget
│       └── settings_dialog.py # Configuration dialog
├── docs/                    # Documentation
├── build_exe.bat            # Build script (PyInstaller)
├── config.json              # Persistent user settings
└── requirements.txt         # Python dependencies
```

## Critical Directories & Files

### `src/` - Application Root
Contains the entire source code.
- **Entry Point**: `main.py` initializes the `QApplication`, sets up the `AppController`, and starts the event loop.

### `src/core/` - Business Logic
Handles the "heavy lifting" separate from the UI.
- **`audio_recorder.py`**: Manages the microphone stream using `sounddevice`. Handles start/stop recording logic and saving raw WAV files.
- **`transcriber.py`**: Wraps the `faster-whisper` library. Manages model loading (with caching) and the transcription process.
- **`config_manager.py`**: Centralizes configuration. Loads/saves `config.json` and emits `config_changed` signals to update other components dynamically.
- **`input_handler.py`**: Manages global hotkeys (via `keyboard` library) and text injection (typing transcribed text).

### `src/ui/` - User Interface
PyQt6 widgets and dialogs.
- **`overlay_window.py`**: The primary interface. A small, floating, always-on-top button that shows recording state (color changes) and provides a context menu.
- **`settings_dialog.py`**: A standard tabbed dialog for configuring audio devices, AI models, and application behavior.

### Root Files
- **`config.json`**: Stores user preferences (model size, hotkeys, input device, etc.).
- **`build_exe.bat`**: Script to compile the Python scripts into a standalone Windows executable.
