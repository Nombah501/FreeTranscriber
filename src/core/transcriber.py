import os
from faster_whisper import WhisperModel
import time

class Transcriber:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self.device = "auto"
        self.compute_type = "default" 
        
        print(f"Loading Whisper model '{model_size}'...")
        try:
            self.model = WhisperModel(
                self.model_size, 
                device=self.device, 
                compute_type=self.compute_type
            )
        except Exception as e:
            print(f"Error loading model: {e}. Falling back to CPU/int8.")
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_path):
        if not os.path.exists(audio_path):
            return ""

        try:
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            
            text = ""
            for segment in segments:
                text += segment.text
            
            return text.strip()
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            raise e