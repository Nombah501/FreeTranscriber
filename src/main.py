import sys
import os
import time
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PyQt6.QtCore import QThread, pyqtSignal, QObject, Qt

from ui.overlay_window import FloatingButton
from core.audio_recorder import AudioRecorder
from core.transcriber import Transcriber
from core.input_handler import InputHandler
from core.config_manager import ConfigManager
from core.logger import get_logger

logger = get_logger(__name__)

# Bridge to safely handle hotkeys from non-Qt threads
class HotkeyBridge(QObject):
    hotkey_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()

class TranscribeWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, transcriber, audio_path):
        super().__init__()
        self.transcriber = transcriber
        self.audio_path = audio_path

    def run(self):
        try:
            if os.path.exists(self.audio_path):
                # Small delay to ensure file is written and flushed
                time.sleep(0.2)
                text = self.transcriber.transcribe(self.audio_path)
                self.finished.emit(text)
            else:
                self.error.emit("Audio file not found")
        except Exception as e:
            self.error.emit(str(e))

class AppController:
    def __init__(self, app):
        self.app = app
        self.config = ConfigManager()
        self.recorder = AudioRecorder(self.config)
        self.recorder.error_occurred.connect(self.on_error)
        
        # Transcriber gets config to manage model loading dynamically
        self.transcriber = Transcriber(self.config)
        self.transcriber.model_loading_started.connect(self.on_model_loading_started)
        self.transcriber.model_loading_finished.connect(self.on_model_loading_finished)
        
        self.input_handler = InputHandler(self.config)
        
        # Connect config signals for non-UI updates
        self.config.config_changed.connect(self.on_config_changed)
        
        # UI Setup
        self.ui = FloatingButton(self.config)

        # Hotkey Bridge (CRITICAL for thread safety)
        self.bridge = HotkeyBridge()
        self.bridge.hotkey_pressed.connect(self.toggle_recording, Qt.ConnectionType.QueuedConnection)

        # Connect UI signals
        self.ui.clicked.connect(self.toggle_recording)
        self.ui.native_hotkey_received.connect(lambda: self.bridge.hotkey_pressed.emit())

        # Tray Icon
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(50, 50, 50))
        painter.setPen(QColor(255, 255, 255))
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        
        self.tray_icon = QSystemTrayIcon(QIcon(pixmap), self.app)
        self.tray_icon.setToolTip("FreeTranscriber")
        tray_menu = QMenu()
        
        settings_action = QAction("Settings", self.app)
        settings_action.triggered.connect(self.ui.open_settings)
        tray_menu.addAction(settings_action)
        
        quit_action = QAction("Exit", self.app)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Setup Initial Hotkey
        self.input_handler.register_hotkey(
            self.config.get("hotkey"),
            lambda: self.bridge.hotkey_pressed.emit(),
            self.ui.winId().__int__()
        )
        
        self.processing = False
        self.current_audio_path = None
        self.thread = None
        self.worker = None

    def on_config_changed(self, key, value):
        if key == "hotkey":
            self.input_handler.update_hotkey(value, self.ui.winId().__int__())
        # model_size/device changes are handled by Transcriber internally on next run
        # input_device_id changes are handled by Recorder internally on next run

    def quit_app(self):
        self.input_handler.unregister_all(self.ui.winId().__int__())
        self.ui.close()
        self.app.quit()

    def toggle_recording(self):
        # This now always runs in the Main GUI Thread thanks to the bridge
        if self.processing:
            return 

        if not self.recorder.recording:
            logger.info("Starting recording")
            self.recorder.start_recording()
            self.ui.set_recording(True)
        else:
            logger.info("Stopping recording")
            audio_path = self.recorder.stop_recording()
            if audio_path:
                self.start_transcription(audio_path)
            else:
                self.ui.set_recording(False)

    def start_transcription(self, audio_path):
        self.processing = True
        self.ui.set_processing(True)
        self.current_audio_path = audio_path
        
        # Cleanup previous thread if exists
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()

        self.thread = QThread()
        self.worker = TranscribeWorker(self.transcriber, audio_path)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_transcription_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.on_error)
        self.worker.error.connect(self.thread.quit)
        
        self.thread.start()

    def on_error(self, message):
        logger.error(f"Error during transcription: {message}")
        self.processing = False
        self.ui.set_recording(False)
        self.ui.flash_error()

    def on_model_loading_started(self):
        self.ui.set_loading(True)

    def on_model_loading_finished(self):
        self.ui.set_loading(False)
        # Restore processing state if still processing
        if self.processing:
            self.ui.set_processing(True)

    def on_transcription_finished(self, text):
        logger.info(f"Transcription completed: {text}")
        
        if text:
            # Use Qt clipboard for thread safety and reliability
            if self.config.get("copy_to_clipboard"):
                clipboard = self.app.clipboard()
                clipboard.setText(text)
            
            # Type text into active window
            if self.config.get("type_text"):
                self.input_handler.type_text(text)
            
            # Visual feedback
            self.ui.flash_success()
        else:
            self.ui.set_recording(False)
            
        self.processing = False
        
        # Cleanup temp file
        if self.current_audio_path and os.path.exists(self.current_audio_path):
            try:
                os.remove(self.current_audio_path)
            except:
                pass

if __name__ == "__main__":
    logger.info("Application Started")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    controller = AppController(app)
    controller.ui.show()
    sys.exit(app.exec())
