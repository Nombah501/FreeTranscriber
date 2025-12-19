# Story 1.5: Global Hotkey & Input Injection

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want to start recording with a keyboard shortcut and have text appear where I am typing,
so that I can use the tool seamlessly in any application without switching focus.

## Acceptance Criteria

1. [x] **Global Hotkey**: A global hotkey (default: `ctrl+shift+space`) triggers the recording toggle (start/stop) regardless of which application is in focus.
2. [x] **Reliability (Windows API)**: Hotkey registration uses the native `RegisterHotKey` Windows API for maximum reliability and low latency, integrated into the PyQt6 event loop.
3. [x] **Fallback Mechanism**: The system maintains the `keyboard` library as a fallback if native registration fails.
4. [x] **Text Injection**: Transcribed text is automatically injected into the active window's cursor position.
5. [x] **Cyrillic Support**: Text injection works reliably for Russian (Cyrillic) characters, primarily using the "Clipboard + Ctrl+V" simulation pattern.
6. [x] **Configuration**: The hotkey is configurable via `config.json` and updates dynamically without requiring an app restart.

## Tasks / Subtasks

- [x] **Task 1: Robust Hotkey Implementation (AC: 1, 2, 3)**
    - [x] Implement `NativeHotkeyManager` using `ctypes` and `user32.dll`.
    - [x] Map string-based hotkeys (e.g., "ctrl+shift+space") to Windows virtual-key codes and modifiers.
    - [x] Integrate `nativeEvent` handling into `FloatingButton` to catch `WM_HOTKEY` (0x0312).
    - [x] Implement fallback to `keyboard.add_hotkey` if `RegisterHotKey` returns False.
- [x] **Task 2: Enhanced Input Injection (AC: 4, 5)**
    - [x] Refine `InputHandler.type_text` to ensure it handles focus timing correctly (small delay before Ctrl+V).
    - [x] Add a "Direct Typing" fallback for applications that block clipboard-based pasting (optional/future-proof).
- [x] **Task 3: Integration & Event Loop (AC: 6)**
    - [x] Update `AppController` to bridge the native hotkey event to the existing `toggle_recording` logic.
    - [x] Ensure the hotkey is properly unregistered on application exit to prevent system resource leaks.

## Dev Notes

- **Native Event Loop**: Successfully integrated `nativeEvent` in `FloatingButton` class. It emits a Qt signal when a hotkey is detected.
- **Reliability**: Using `win32con` values via `NativeHotkeyManager` for low-level interaction.
- **Indentation fix**: Fixed several indentation errors in `main.py` introduced during implementation.

### Project Structure Notes

- `src/core/input_handler.py`: Added `NativeHotkeyManager` class.
- `src/ui/overlay_window.py`: Added `nativeEvent` and `native_hotkey_received` signal.
- `src/main.py`: Updated `AppController` to manage lifecycle and event bridging.

### References

- [Source: _bmad-output/prd.md#Functional Requirements] - FR1, FR14, FR15
- [Source: _bmad-output/architecture.md#Core Components] - AppController and InputHandler responsibilities

## Dev Agent Record

### Agent Model Used

gemini-2.0-flash-exp

### Debug Log References

- Verified `NativeHotkeyManager` with unit tests in `tests/test_input_handler.py`.
- Fixed startup `IndentationError` in `main.py`.
- Verified application startup and initial component initialization in logs.

### Completion Notes List

- [2025-12-18] Implemented native hotkey support.
- [2025-12-18] Verified Cyrillic text injection via clipboard simulation.
- [2025-12-18] Ensured fallback to `keyboard` library for non-standard environments.
- [2025-12-19] AI Review: Fixed hardcoded hotkey ID, improved key map support, and refactored UI colors.
- [2025-12-19] AI Review: Updated audio recorder sample rate handling (previously uncommitted).

### File List

- `src/core/input_handler.py`
- `src/ui/overlay_window.py`
- `src/main.py`
- `tests/test_input_handler.py`
- `src/core/audio_recorder.py`
- `requirements.txt`