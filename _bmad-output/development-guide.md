# Development Guide

## Prerequisites

- **OS**: Windows 10/11 (Primary target), Linux/macOS (Supported but requires adjustments)
- **Python**: Version 3.10+ recommended
- **Microphone**: A working input device

## Setup Environment

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd FreeTranscriber
    ```

2.  **Create a Virtual Environment** (Recommended):
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `faster-whisper` and `PyQt6` are the heavy dependencies.*

## Running Locally

To start the application in development mode:

```bash
python src/main.py
```

- A floating button should appear on your screen.
- A system tray icon will also be created.

## Code Style & Conventions

- **Framework**: PyQt6 for UI. Use Signals/Slots for communication between components.
- **Async Logic**: Never block the main thread. Use `QThread` (as seen in `TranscribeWorker`) for long-running tasks like model loading and transcription.
- **Config**: Do not hardcode values. Use `self.config.get("key")` from `ConfigManager`.

## Common Tasks

### Adding a New Setting
1.  Add the default key/value to `ConfigManager.default_config` in `src/core/config_manager.py`.
2.  Add a UI control (Checkbox, Slider, etc.) in `src/ui/settings_dialog.py`.
3.  Connect the control's signal to `self.config.set("key", value)`.
4.  Handle the `config_changed` signal in the relevant component (e.g., `AppController` or `Transcriber`) if the change needs immediate effect.

### Debugging
- `print()` statements in `src/main.py` output to the console.
- If running the compiled `.exe` (windowed mode), stdout is suppressed. Run from a terminal or modify the spec to see logs.
