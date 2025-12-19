# Component Inventory

This document lists the User Interface components implemented in PyQt6.

## Main Interface
### `FloatingButton`
*Source: `src/ui/overlay_window.py`*

A minimalist, always-on-top widget that acts as the primary status indicator and control.

- **Visual States**:
    - **Idle**: Dark grey circle (`#323232`), partially transparent.
    - **Recording**: Red circle with square stop icon. High opacity.
    - **Processing**: Orange circle with 3 dots.
    - **Success**: Green circle with checkmark. Flashes briefly.
- **Interactions**:
    - **Left Click**: Toggle recording.
    - **Right Click**: Open Context Menu (Settings, Exit).
    - **Drag**: Move the button around the screen (saves position).

## Dialogs
### `SettingsDialog`
*Source: `src/ui/settings_dialog.py`*

A modal dialog for application configuration.

- **Tab: General**:
    - `opacity_slider`: Controls window transparency when idle.
    - `top_check`: Toggle "Always on Top".
    - `sounds_check`: Toggle UI sound effects.
- **Tab: Audio**:
    - `device_combo`: Dropdown to select input microphone. Uses `sounddevice.query_devices()`.
- **Tab: AI Model**:
    - `model_combo`: Select Whisper model size (`tiny`, `base`, `small`, `medium`, `large`).
    - `lang_combo`: Select source language (`ru`, `en`, `auto`).

## System Integration
### System Tray
*Source: `src/main.py` (AppController)*

- **Icon**: Generated programmatically (Simple drawn circle).
- **Menu**:
    - **Exit**: Quits the application completely.
