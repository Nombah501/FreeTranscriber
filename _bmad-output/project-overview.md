# Project Overview

**FreeTranscriber** is a productivity tool designed to bring "Voice-to-Text" capability to any Windows application. Unlike cloud-based solutions (like Siri or Google Docs typing), FreeTranscriber runs entirely **offline** using OpenAI's Whisper models.

## Key Features
- **Global Hotkey**: Toggle recording from anywhere (Default: `Ctrl+Shift+Space`).
- **Floating UI**: Minimalist overlay that shows recording status.
- **Privacy First**: All processing happens locally on your GPU/CPU. No audio leaves your machine.
- **Smart Output**: Automatically types the transcribed text into the active window and copies it to the clipboard.
- **Customizable**: Choose model size (Tiny -> Large) to balance speed vs. accuracy.

## Technology Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core logic and coordination |
| **GUI Framework** | PyQt6 | User Interface and Event Loop |
| **AI Engine** | faster-whisper | Efficient implementation of OpenAI's Whisper |
| **Audio Capture** | sounddevice | Low-latency microphone recording |
| **Input Control** | keyboard | Global hotkey detection and text typing |
| **Packaging** | PyInstaller | Compiling to standalone `.exe` |

## Repository Structure
The project follows a **Monolithic** structure where UI and Logic reside in the same codebase but are cleanly separated.

- **`src/core/`**: Backend logic (Audio, AI, Config).
- **`src/ui/`**: Frontend logic (Widgets, Dialogs).
- **`docs/`**: Project documentation.
