---
stepsCompleted: [1, 2, 3, 4, 6, 7, 8, 9, 10]
inputDocuments: [
  "_bmad-output/index.md",
  "_bmad-output/project-overview.md",
  "_bmad-output/architecture.md",
  "_bmad-output/component-inventory.md"
]
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 0
  projectDocs: 4
workflowType: 'prd'
lastStep: 0
project_name: 'FreeTranscriber'
user_name: 'Андрей'
date: 'четверг, 18 декабря 2025 г.'
---

# Product Requirements Document - FreeTranscriber

**Author:** Андрей
**Date:** четверг, 18 декабря 2025 г.

## Executive Summary

FreeTranscriber v3.0 is a major leap forward for the privacy-focused desktop transcription tool. Moving beyond incremental updates, this version focuses on **Visual Intelligence** and **Technical Excellence**, establishing a new platform standard for offline AI interaction. The goal is to transform the minimalist interface into a professional "Smart UI" while optimizing core performance for long-term reliability and low resource consumption.

### What Makes This Special

The "v3.0 Experience" centers on the **Smart Pill** interaction model—a dynamic, adaptive UI that provides real-time feedback (voice waveforms, timers, and status) without cluttering the screen. Combined with **Under-the-Hood Optimization** (Smart Memory Management, streaming audio to disk), it offers a premium, high-performance experience that remains completely offline.

## Project Classification

**Technical Type:** Desktop Application (Python/PyQt6)
**Domain:** Productivity / AI
**Complexity:** Medium
**Project Context:** Brownfield - implementing a major platform upgrade (v3.0)

### Brainstormed Features (v3.0 Roadmap)

1.  **Smart Pill UI**: Transformation from a circle to a status panel during recording.
2.  **Live Visual Feedback**: Animated waveform and recording timer.
3.  **UI Scaling**: Support for high-resolution displays (4K) via adjustable scaling.
4.  **Smart Memory Management**: Dynamic unloading of models and audio buffering.
5.  **Low RAM Mode**: INT8 quantization for entry-level hardware.
6.  **Reliability Improvements**: Low-level Windows API hooks for global hotkeys.

## Success Criteria

### User Success
*   **Zero Anxiety**: Users instantly know recording status via the "Smart Pill" and Waveform animation.
*   **Responsiveness**: The application feels significantly snappier; no UI freezes during model loading or processing.
*   **Adoption**: Existing users upgrade to v3.0 and keep using it without reverting due to performance issues.

### Technical Success
*   **Memory Efficiency**: Reduce Idle RAM usage by ~40% by unloading Whisper models when inactive.
*   **Stability**: Audio recording remains stable indefinitely (no OOM crashes) thanks to disk buffering.
*   **UI Performance**: Animations (Waveform) run at smooth 30-60 FPS without blocking the main thread.

### Measurable Outcomes
*   **Launch Time**: Application cold start under 3 seconds.
*   **Feedback Latency**: Visual feedback on voice input < 100ms.

## Product Scope

### MVP - Minimum Viable Product (v3.0 - The Revolution)
*   **Smart Pill UI**: Dynamic widget expansion (Circle -> Status Panel).
*   **Live Visuals**: Real-time voice waveform visualization.
*   **Optimization**: Dynamic model unloading & chunk-based audio recording.
*   **Basic Feedback**: Timer and Status text ("Listening...", "Thinking...").
*   **System Reliability**: Implementation of low-level Windows API hooks for hotkeys.

### Growth Features (v3.1 - v3.2)
*   **Customization (v3.1)**: UI Scale slider & Theme selector (Dark/Glass).
*   **Performance Mode (v3.2)**: Toggle for INT8 quantization (Low RAM mode).
*   **Settings Overhaul**: Updated settings dialog to support new features.

### Vision (Future)
*   **Voice Activity Detection (VAD)**: Hands-free recording control.
*   **Smart Formatting**: Auto-punctuation and custom vocabulary injection.

## User Journeys

**Journey 1: Alexey (Researcher) - Academic Pressure**
Alexey is transcribing long interviews for his thesis. In v3.0, when he starts recording, the "Smart Pill" expands, showing a live waveform that assures him his cheap laptop mic is picking up clear audio. Thanks to **Smart Memory Management**, the app unloads the Whisper model while he's reviewing notes, keeping his laptop cool and responsive for writing.

**Journey 2: Elena (Manager) - The Long Meeting**
Elena records a 90-minute board meeting. The **Chunk-based Recording** ensures that even if her PC crashes, the audio data is safely buffered to the disk. She relies on the **Recording Timer** in the Smart Pill to keep track of key discussion points.

**Journey 3: Dmitry (Gamer) - High-Stakes Communication**
Dmitry uses FreeTranscriber to type callouts in a game. He uses **UI Scaling** to make the Smart Pill tiny so it doesn't block his HUD. The **Low-level Windows Hooks** ensure his hotkey works perfectly even while the GPU is under 99% load.

**Journey 4: Marina (New User) - The First Impression (Onboarding)**
Marina downloads the app and sees the initial floating circle. Instead of guessing, the Smart Pill displays a gentle pulsing effect and a hint: *"Press Ctrl+Shift+Space to start"*. A 3-step mini-tutorial guides her through selecting her microphone, ensuring she feels successful within the first 30 seconds.

**Journey 5: Ivan (Engineer) - Error Resilience**
While recording an onsite inspection report, Ivan's USB microphone gets unplugged. Instead of a silent failure, the Smart Pill turns bright orange with a clear alert: *"Microphone Disconnected"*. Ivan reconnects it, and the app allows him to resume the recording seamlessly, saving his work.

### Journey Requirements Summary
*   **Interactive UI**: Dynamic Smart Pill, Waveform, Timers, and Status text.
*   **Onboarding System**: First-launch hints and guided setup.
*   **Error Management**: Real-time hardware status monitoring and visual alerts.
*   **Performance Scaling**: Resource management for both low-end and high-end systems.

## Innovation & Novel Patterns

### Detected Innovation Areas
*   **The Smart Pill Interaction Model**: Unlike static overlays, the Smart Pill is a context-aware widget that transforms its shape and information density based on the application state (Idle vs. Recording vs. Processing). It provides "High-Context, Low-Friction" feedback.
*   **Local AI Accessibility (Edge Optimization)**: By implementing dynamic model unloading and INT8 quantization, we are bringing high-tier AI capabilities to "non-AI" hardware. This democratizes professional-grade transcription.
*   **Universal Input Simulation**: Using low-level system hooks to act as a virtual keyboard makes FreeTranscriber a universal "Voice-to-Anywhere" bridge, requiring zero integration from other software vendors.

### Market Context & Competitive Landscape
While cloud services (Siri, Google Dictation) offer speed, they sacrifice privacy. Existing offline tools are often bulky "pro" software. FreeTranscriber v3.0 occupies the unique niche of **"Professional Power in a Consumer-Grade Package"**, focusing on extreme privacy and system-wide utility.

### Validation Approach
*   **Performance Benchmarking**: Measuring RAM and CPU delta between v1.0 and v3.0 on entry-level hardware.
*   **UX Latency Testing**: Ensuring the "Smart Pill" transitions feel instantaneous (<100ms) to maintain the illusion of a native OS feature.

### Risk Mitigation
*   **Innovation Risk**: Complexity of low-level Windows hooks. 
*   **Fallback**: The system will support a "Legacy Input Mode" using the standard `keyboard` library if native hooks fail on specific OS builds.

## Desktop Application Specific Requirements

### Project-Type Overview
FreeTranscriber is a native Windows desktop application. Its primary technical mandate is **100% Offline Operation** and **Zero Data Egress**, ensuring total user privacy. It operates as a portable utility rather than a deeply integrated system service.

### Technical Architecture Considerations
*   **Platform Support**: Primary focus on Windows 10/11. The architecture (Python/PyQt6) remains portable for future macOS/Linux versions, but no specific native integrations for those platforms are required now.
*   **Offline First**: All AI inference (Faster-Whisper) and business logic must function without an internet connection. No telemetry, statistics, or crash reports are to be sent to external servers.
*   **Update Strategy**: Manual updates only. Users are responsible for checking the GitHub repository for new releases. This keeps the application simple and avoids background "updater" processes that consume resources.

### System Integration
*   **Notification System**: Support for native Windows Toast Notifications to inform users of successful transcriptions or errors. This must be a **toggleable setting** (Opt-in/Opt-out) to respect user focus.
*   **Startup & Resources**: No automatic startup (autostart) or background persistent services. The application only consumes resources when explicitly launched by the user.
*   **Input Simulation**: Continued use of global hotkeys and virtual keyboard injection as the primary method of system interaction.

### Implementation Specifics
*   **Portability**: The application should remain portable (single EXE) to allow users to run it from any folder or USB drive without formal installation.
*   **Hardware Detection**: On startup, the app should detect available compute providers (CUDA vs. CPU) to automatically set the most efficient defaults for the user's hardware.

## Project Scoping & Phased Development

### Release Strategy: The v3.0 Revolution
Instead of an incremental update, this release represents a major architectural and UX overhaul, designated as **FreeTranscriber v3.0**. The philosophy is **"Platform MVP"**—establishing a robust, visually stunning, and highly optimized foundation that will support the product for years to come.

### Phase 1: v3.0 (The Revolution) - Core Release
**Focus:** Delivering the "Smart Pill" experience and rock-solid stability.
*   **Must-Have Capabilities:**
    *   **Smart Pill UI**: Complete replacement of the static overlay with an adaptive panel.
    *   **Live Visual Feedback**: Real-time audio visualization (Waveform) and Recording Timer.
    *   **Smart Memory Management**: Automatic unloading of models from RAM/VRAM when idle for >10 mins.
    *   **Disk Audio Buffering**: Chunk-based recording to avoid memory exhaustion during long sessions.
    *   **Low-Level Hooks**: Reliable global hotkeys via direct Windows API interaction.
    *   **Onboarding & Errors**: First-launch tutorial and hardware failure alerts.

### Phase 2: v3.1 (The Style Update)
**Focus:** Visual customization and delight.
*   **Planned Features:**
    *   **Theme Engine**: Support for Dark/Light and Glassmorphism themes.
    *   **Custom Animations**: User-selectable transition effects for the Smart Pill.

### Phase 3: v3.2 (The Accessibility Update)
**Focus:** Hardware adaptability and inclusivity.
*   **Planned Features:**
    *   **UI Scaling**: Slider for 4K/High-DPI monitor support.
    *   **Low RAM Mode**: Toggle for INT8 quantization settings.

### Risk Mitigation Strategy
*   **Technical Risks (Hooks)**: Implementing low-level Windows hooks is complex. *Mitigation:* Keep the `keyboard` library as a hidden fallback option.
*   **Market Risks (Change Aversion)**: Users might dislike the new UI. *Mitigation:* Include a "Classic Mode" toggle in v3.0 that mimics the old static circle behavior.

## Functional Requirements

### 1. Audio Capture Management
- **FR1**: User can start and stop audio recording using a global hotkey.
- **FR2**: System detects audio device disconnection during recording and notifies the user.
- **FR3**: System automatically buffers audio data to disk during recording to prevent data loss.
- **FR4**: User can select the input audio device from a list of available system devices.
- **FR19**: System automatically deletes temporary audio buffer files after successful transcription or upon application exit.

### 2. AI Model Management
- **FR5**: System automatically unloads the Whisper model from memory (RAM/VRAM) after a period of inactivity.
- **FR6**: System detects available hardware accelerators (CUDA) and uses them for transcription.
- **FR7**: User can select the model size (Tiny, Base, Small, etc.) based on their needs.
- **FR8**: User can select the transcription language or set it to auto-detect.
- **FR21**: System automatically falls back to CPU processing if GPU initialization fails, with a notification to the user.

### 3. Adaptive Interface (Smart UI)
- **FR9**: System displays a dynamic overlay ("Smart Pill") that changes shape and content based on the mode (Idle, Recording, Processing).
- **FR10**: User can see a real-time visualization of their voice volume (Waveform) during recording.
- **FR11**: User can see a timer of the current recording.
- **FR12**: User can change the position of the overlay on the screen by dragging.
- **FR13**: User can configure the transparency of the overlay.
- **FR20**: System prevents moving the overlay outside visible screen boundaries and provides a "Reset Position" option in settings.

### 4. Output & Integration
- **FR14**: System can automatically simulate text input into the active window after transcription is complete.
- **FR15**: System can automatically copy the transcription result to the clipboard.
- **FR16**: System can send Windows native notifications for process completion or errors.

### 5. Onboarding & Support
- **FR17**: System displays interactive hints for new users on the first launch.
- **FR18**: System provides a brief onboarding tour of key features.

## Non-Functional Requirements

### Performance
- **Responsiveness**: UI interactions (e.g., button clicks, mode transitions) must respond within 50ms to ensure a "native" feel.
- **Memory Footprint**: In Idle mode (after model unload), the application should consume less than 200MB RAM.
- **Processing Speed**: Transcription speed should achieve at least a 1:5 realtime factor (1 minute of audio processed in <12 seconds) on standard hardware with CPU inference (Base model).

### Reliability
- **Data Safety**: In the event of a crash or power loss, the current recording buffer on disk must remain intact and be recoverable.
- **Stability**: The application must handle hardware exceptions (e.g., microphone unplugged, GPU driver crash) without terminating, providing a graceful error state instead.

### Security & Privacy
- **Zero Egress**: The application must not initiate any outbound network connections during standard operation.
- **Local Storage**: All temporary files and logs must be stored within the user's local profile directories and cleaned up automatically.

### Usability & Accessibility
- **High DPI Support**: The interface must render crisply on 4K monitors without blurring or scaling artifacts.
- **Visual Clarity**: Text and icons in the "Smart Pill" must maintain a minimum contrast ratio of 4.5:1 against the background for readability in varied lighting conditions.
