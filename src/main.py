import sys
import os
from PyQt6.QtWidgets import QApplication
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
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(model_size="base")
        self.input_handler = InputHandler()
        
        self.ui = FloatingButton()
        self.ui.clicked.connect(self.toggle_recording)
        
        # Setup global hotkey
        self.input_handler.setup_hotkey('ctrl+shift+space', self.toggle_recording)
        
        self.temp_audio = "temp_recording.wav"
        self.processing = False

    def toggle_recording(self):
        if self.processing:
            return # Busy transcribing

        if not self.recorder.recording:
            print("Start recording...")
            self.recorder.start_recording()
            self.ui.set_recording(True)
        else:
            print("Stop recording...")
            self.recorder.stop_recording(self.temp_audio)
            self.ui.set_recording(False)
            self.start_transcription()

    def start_transcription(self):
        print("Starting transcription...")
        self.processing = True
        self.ui.setWindowOpacity(0.5) # Visual feedback for processing
        
        self.thread = QThread()
        self.worker = TranscribeWorker(self.transcriber, self.temp_audio)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_transcription_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()

    def on_transcription_finished(self, text):
        print(f"Transcribed: {text}")
        self.input_handler.type_text(text)
        self.processing = False
        self.ui.setWindowOpacity(1.0 if self.ui.underMouse() else 0.7)
        
        # Cleanup temp file
        if os.path.exists(self.temp_audio):
            try:
                os.remove(self.temp_audio)
            except:
                pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = AppController()
    controller.ui.show()
    sys.exit(app.exec())
