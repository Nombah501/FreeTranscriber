import sys
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from ui.overlay_window import FloatingButton
from core.audio_recorder import AudioRecorder
from core.transcriber import Transcriber
from core.input_handler import InputHandler

class TranscribeWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, transcriber, audio_path):
        super().__init__()
        self.transcriber = transcriber
        self.audio_path = audio_path

    def run(self):
        try:
            text = self.transcriber.transcribe(self.audio_path)
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))

class AppController:
    def __init__(self, app):
        self.app = app
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(model_size="base")
        self.input_handler = InputHandler()
        
        self.ui = FloatingButton()
        self.ui.clicked.connect(self.toggle_recording)
        
        # Setup Tray Icon
        self.tray_icon = QSystemTrayIcon(QIcon("icon.png"), self.app) # Needs an icon, will use default fallback if missing
        self.tray_icon.setToolTip("FreeTranscriber")
        
        tray_menu = QMenu()
        quit_action = QAction("Exit", self.app)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Setup global hotkey
        self.input_handler.setup_hotkey('ctrl+shift+space', self.toggle_recording)
        
        self.processing = False

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
            audio_path = self.recorder.stop_recording()
            if audio_path:
                self.start_transcription(audio_path)
            else:
                self.ui.set_recording(False) # Cancelled or empty

    def start_transcription(self, audio_path):
        print(f"Starting transcription of {audio_path}...")
        self.processing = True
        self.ui.set_processing(True)
        
        self.thread = QThread()
        self.worker = TranscribeWorker(self.transcriber, audio_path)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_transcription_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()

    def on_transcription_finished(self, text):
        print(f"Transcribed: {text}")
        
        if text:
            # Copy to clipboard using Qt (Thread-safe way)
            clipboard = self.app.clipboard()
            clipboard.setText(text)
            
            # Type text
            self.input_handler.type_text(text)
            
            # Show success visual
            self.ui.flash_success()
        else:
            # Empty result
            self.ui.set_recording(False)
            
        self.processing = False
        
        # Cleanup temp file handled by OS temp dir mostly, but good to be explicit if we knew the path here easily.
        # AudioRecorder saves to specific temp file, overwriting it each time, so no massive bloat.

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Important for tray app
    
    controller = AppController(app)
    controller.ui.show()
    
    sys.exit(app.exec())