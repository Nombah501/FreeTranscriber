import os
from faster_whisper import WhisperModel
import time

class Transcriber:
    def __init__(self, config_manager):
        self.config = config_manager
        self.model = None
        self.current_model_size = None
        
        # Load initial model
        self.load_model()

    def load_model(self):
        model_size = self.config.get("model_size")
        device = self.config.get("device")
        
        if self.model and self.current_model_size == model_size:
            return # No change needed

        print(f"Loading Whisper model '{model_size}' on {device}...")
        try:
            # Cleanup old model if exists to free memory
            if self.model:
                del self.model
                self.model = None
            
            compute_type = "float16" if device == "cuda" else "int8"
            
            self.model = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type
            )
            self.current_model_size = model_size
            print(f"Model '{model_size}' loaded successfully.")
            
        except Exception as e:
            print(f"Error loading model: {e}. Falling back to CPU/int8.")
            try:
                self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
                self.current_model_size = model_size
            except Exception as e2:
                print(f"CRITICAL: Failed to load fallback model: {e2}")

    def transcribe(self, audio_path):
        if not self.model:
            print("Model not loaded, attempting to load...")
            self.load_model()
            if not self.model:
                return "Error: Model failed to load."

        if not os.path.exists(audio_path):
            return ""

        try:
            # Get language from config
            language = self.config.get("language")
            if language == "auto":
                language = None
                
            segments, info = self.model.transcribe(
                audio_path, 
                beam_size=5, 
                language=language
            )
            
            text = ""
            for segment in segments:
                text += segment.text
            
            return text.strip()
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            # If error might be due to model (e.g. CUDA OOM), maybe reload?
            # For now just re-raise or return error
            return f"[Error: {e}]"
