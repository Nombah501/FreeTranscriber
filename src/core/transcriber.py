import os
from faster_whisper import WhisperModel

class Transcriber:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        
        # 'auto' will prefer CUDA if available, then CPU.
        # This avoids needing to import 'torch' explicitly.
        self.device = "auto"
        # For CPU 'int8' is best, for CUDA 'float16' is preferred. 
        # WhisperModel handles compute_type="default" or we can be specific.
        self.compute_type = "default" 
        
        print(f"Loading Whisper model '{model_size}' (device={self.device})...")
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
        """
        Transcribes the given audio file.
        Returns: string (transcribed text)
        """
        if not os.path.exists(audio_path):
            return ""

        # beam_size 5 is a good balance between speed and accuracy
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        
        text = ""
        for segment in segments:
            text += segment.text
            
        return text.strip()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ts = Transcriber()
        print("Transcribing...")
        result = ts.transcribe(sys.argv[1])
        print(f"Result: {result}")
    else:
        print("Usage: python transcriber.py <path_to_audio>")