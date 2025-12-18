import os
from faster_whisper import WhisperModel
import torch

class Transcriber:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        # Auto-detect device: cuda if available, else cpu
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        
        print(f"Loading Whisper model '{model_size}' on {self.device}...")
        self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

    def transcribe(self, audio_path):
        """
        Transcribes the given audio file.
        Returns: string (transcribed text)
        """
        if not os.path.exists(audio_path):
            return ""

        segments, info = self.model.transcribe(audio_path, beam_size=5)
        
        text = ""
        for segment in segments:
            text += segment.text
            
        return text.strip()

if __name__ == "__main__":
    # Quick test if file exists
    import sys
    if len(sys.argv) > 1:
        ts = Transcriber()
        print("Transcribing...")
        result = ts.transcribe(sys.argv[1])
        print(f"Result: {result}")
    else:
        print("Usage: python transcriber.py <path_to_audio>")
