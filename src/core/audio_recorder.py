import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import tempfile
import uuid

class AudioRecorder:
    def __init__(self, config_manager):
        self.config = config_manager
        self.recording = False
        self.audio_data = []
        self._stream = None

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"Error in audio stream: {status}")
        if self.recording:
            self.audio_data.append(indata.copy())

    def start_recording(self):
        self.recording = True
        self.audio_data = []
        
        # Get settings from config
        device = self.config.get("input_device_id")
        sample_rate = self.config.get("sample_rate")
        
        try:
            self._stream = sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype='float32',
                callback=self._callback,
                device=device
            )
            self._stream.start()
        except Exception as e:
            print(f"Failed to start stream: {e}")
            self.recording = False
            # Fallback to default device if specific one failed
            if device is not None:
                print("Retrying with default device...")
                try:
                    self._stream = sd.InputStream(
                        samplerate=sample_rate,
                        channels=1,
                        dtype='float32',
                        callback=self._callback
                    )
                    self._stream.start()
                    self.recording = True
                except Exception as ex:
                     print(f"Fallback failed: {ex}")

    def stop_recording(self):
        self.recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        if not self.audio_data:
            return None

        full_audio = np.concatenate(self.audio_data, axis=0)
        
        # Generate unique temp filename to avoid locks
        unique_name = f"rec_{uuid.uuid4().hex[:8]}.wav"
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, unique_name)
        
        wav.write(output_path, self.config.get("sample_rate"), full_audio)
        return output_path