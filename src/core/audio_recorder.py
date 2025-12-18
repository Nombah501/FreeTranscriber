import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import threading

class AudioRecorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_data = []
        self._stream = None
        self.device_id = None # Default device

    def get_devices(self):
        """Returns list of available audio input devices."""
        return sd.query_devices()

    def set_device(self, device_id):
        self.device_id = device_id

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"Error in audio stream: {status}")
        if self.recording:
            self.audio_data.append(indata.copy())

    def start_recording(self):
        self.recording = True
        self.audio_data = []
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=self._callback,
            device=self.device_id
        )
        self._stream.start()

    def stop_recording(self, output_path="temp_recording.wav"):
        self.recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
        
        if not self.audio_data:
            return None

        # Concatenate all recorded chunks
        full_audio = np.concatenate(self.audio_data, axis=0)
        
        # Save to wav file
        wav.write(output_path, self.sample_rate, full_audio)
        return output_path

if __name__ == "__main__":
    # Quick test
    recorder = AudioRecorder()
    print("Recording for 3 seconds...")
    recorder.start_recording()
    import time
    time.sleep(3)
    path = recorder.stop_recording("test.wav")
    print(f"Saved to {path}")
