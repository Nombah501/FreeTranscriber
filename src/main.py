import sys
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from ui.overlay_window import FloatingButton
from core.audio_recorder import AudioRecorder
from core.transcriber import Transcriber
from core.input_handler import InputHandler
from core.config_manager import ConfigManager

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
        
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(model_size=self.config.get("model_size"))
        self.input_handler = InputHandler()
        
        self.ui = FloatingButton(self.config)
        self.ui.clicked.connect(self.toggle_recording)
        
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
        quit_action = QAction("Exit", self.app)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Hotkey
        self.input_handler.setup_hotkey(self.config.get("hotkey"), self.toggle_recording)
        
        self.processing = False
        self.current_audio_path = None
        
        # Thread management
        self.thread = None
        self.worker = None

    def quit_app(self):
        self.ui.close()
        self.app.quit()

    def toggle_recording(self):
        if self.processing:
            return 

        if not self.recorder.recording:
            print("Start recording...")
            self.recorder.start_recording()
            self.ui.set_recording(True)
        else:
            print("Stop recording...")
            self.current_audio_path = self.recorder.stop_recording()
            if self.current_audio_path:
                self.start_transcription(self.current_audio_path)
            else:
                self.ui.set_recording(False)

    def start_transcription(self, audio_path):
        print(f"Starting transcription of {audio_path}...")
        self.processing = True
        self.ui.set_processing(True)
        
        # Ensure previous thread is cleaned up
        if self.thread is not None:
            if self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
            self.thread.deleteLater()
            self.worker.deleteLater()
        
        self.thread = QThread()
        self.worker = TranscribeWorker(self.transcriber, audio_path)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_transcription_finished)
        self.worker.finished.connect(self.thread.quit)
        
        self.thread.start()

    def on_transcription_finished(self, text):
        print(f"Transcribed: {text}")
        
        if text:
            clipboard = self.app.clipboard()
            clipboard.setText(text)
            self.input_handler.type_text(text)
            self.ui.flash_success()
        else:
            self.ui.set_recording(False)
            
        self.processing = False
        
        # Cleanup file
        if self.current_audio_path and os.path.exists(self.current_audio_path):
            try:
                os.remove(self.current_audio_path)
            except Exception as e:
                print(f"Failed to delete temp file: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    controller = AppController(app)
    controller.ui.show()
    
    sys.exit(app.exec())