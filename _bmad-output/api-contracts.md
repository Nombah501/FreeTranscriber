# Internal API Contracts

Since FreeTranscriber is a desktop application, "API Contracts" refer to the public methods of the Core classes used by the Controller.

## Core Modules

### `Transcriber`
*Class in `src/core/transcriber.py`*

| Method | Signature | Description |
| :--- | :--- | :--- |
| `__init__` | `(config_manager)` | Initializes with config. Lazy loads model. |
| `transcribe` | `(audio_path: str) -> str` | **Blocking**. Loads model (if needed) and converts audio file to text. Returns empty string on failure. |

### `AudioRecorder`
*Class in `src/core/audio_recorder.py`*

| Method | Signature | Description |
| :--- | :--- | :--- |
| `start_recording` | `()` | Starts async audio stream from selected device. |
| `stop_recording` | `() -> str | None` | Stops stream, writes buffered audio to a temp `.wav` file. Returns file path. |

### `ConfigManager`
*Class in `src/core/config_manager.py`*

| Method | Signature | Description |
| :--- | :--- | :--- |
| `get` | `(key: str) -> Any` | Returns value for key, falling back to default. |
| `set` | `(key: str, value: Any)` | Updates value, saves to disk, and emits `config_changed` signal. |
| `config_changed` | `Signal(str, object)` | **Qt Signal**. Emitted when any setting is updated. |

### `InputHandler`
*Class in `src/core/input_handler.py`*

| Method | Signature | Description |
| :--- | :--- | :--- |
| `register_hotkey` | `(hotkey_str, callback)` | Binds a global hotkey (e.g., "ctrl+space"). |
| `type_text` | `(text: str)` | Simulates keyboard events to type the text into the active window. |
