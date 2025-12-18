"""
Audio Recording Module with Disk Streaming.

This module provides real-time audio recording with:
- Disk streaming (no RAM accumulation)
- Thread-safe queue-based architecture
- RMS amplitude calculation for UI visualization
- Automatic cleanup of temporary files
- Error handling for device failures
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import queue
import threading
import atexit
from pathlib import Path
from typing import Optional, List
from PyQt6.QtCore import QObject, pyqtSignal

from src.core.logger import get_logger
from src.utils.paths import get_temp_audio_file

logger = get_logger(__name__)


class AudioRecorder(QObject):
    """
    Audio recorder with disk streaming and real-time amplitude feedback.

    Signals:
        amplitude_changed(float): Emitted ~30-60 times/sec with RMS amplitude (0.0-1.0)
        error_occurred(str): Emitted when recording error occurs
    """

    amplitude_changed = pyqtSignal(float)
    error_occurred = pyqtSignal(str)

    def __init__(self, config_manager):
        """
        Initialize audio recorder.

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__()
        self.config = config_manager
        self.recording = False
        self._stream = None
        self._audio_queue = queue.Queue()
        self._writer_thread = None
        self._stop_writer = threading.Event()
        self._current_file_path: Optional[Path] = None
        self._temp_files: List[Path] = []

        # Register cleanup on exit
        atexit.register(self.cleanup_temp_files)

        logger.info("AudioRecorder initialized")

    def _calculate_rms(self, audio_data: np.ndarray) -> float:
        """
        Calculate RMS (Root Mean Square) amplitude for visualization.

        Args:
            audio_data: Audio samples as numpy array

        Returns:
            RMS amplitude normalized to 0.0-1.0 range
        """
        rms = np.sqrt(np.mean(audio_data ** 2))
        # Normalize to reasonable range (most speech is < 0.3 RMS)
        normalized = min(rms * 3.0, 1.0)
        return float(normalized)

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Audio input callback (runs in high-priority audio thread).

        Args:
            indata: Input audio data
            frames: Number of frames
            time_info: Time information
            status: Stream status
        """
        if status:
            logger.warning(f"Audio stream status: {status}")
            if status.input_overflow:
                logger.error("Audio buffer overflow detected")

        if self.recording:
            # Calculate and emit RMS for UI
            rms = self._calculate_rms(indata)
            self.amplitude_changed.emit(rms)

            # Put audio data in queue for writer thread
            # Make a copy to avoid issues with buffer reuse
            self._audio_queue.put(indata.copy())

    def _file_writer_thread_func(self):
        """
        File writer thread function.

        Continuously pulls audio data from queue and writes to disk using soundfile.
        """
        try:
            logger.debug(f"Starting file writer thread: {self._current_file_path}")

            # Open soundfile for writing (16kHz, mono, float32)
            with sf.SoundFile(
                self._current_file_path,
                mode='w',
                samplerate=16000,
                channels=1,
                format='WAV',
                subtype='FLOAT'
            ) as sound_file:

                while not self._stop_writer.is_set():
                    try:
                        # Get audio data from queue (with timeout to check stop flag)
                        audio_chunk = self._audio_queue.get(timeout=0.1)
                        sound_file.write(audio_chunk)
                    except queue.Empty:
                        continue

                # Flush remaining data in queue after stop signal
                while not self._audio_queue.empty():
                    try:
                        audio_chunk = self._audio_queue.get_nowait()
                        sound_file.write(audio_chunk)
                    except queue.Empty:
                        break

            logger.debug("File writer thread finished successfully")

        except Exception as e:
            logger.error(f"Error in file writer thread: {e}")
            self.error_occurred.emit(f"File write error: {str(e)}")

    def start_recording(self):
        """
        Start audio recording.

        Creates temp file, starts writer thread, and begins audio stream.
        """
        if self.recording:
            logger.warning("Already recording, ignoring start request")
            return

        try:
            # Generate unique temp file path
            self._current_file_path = get_temp_audio_file()
            self._temp_files.append(self._current_file_path)

            # Clear queue and reset stop flag
            while not self._audio_queue.empty():
                try:
                    self._audio_queue.get_nowait()
                except queue.Empty:
                    break
            self._stop_writer.clear()

            # Start file writer thread
            self._writer_thread = threading.Thread(
                target=self._file_writer_thread_func,
                daemon=True
            )
            self._writer_thread.start()

            # Get settings from config
            device = self.config.get("input_device_id")

            # Start audio stream (targeting 16kHz)
            try:
                self._stream = sd.InputStream(
                    samplerate=16000,  # Strict 16kHz for Whisper
                    channels=1,
                    dtype='float32',
                    callback=self._audio_callback,
                    device=device
                )
                self._stream.start()
                self.recording = True
                logger.info(f"Recording started: {self._current_file_path}")

            except sd.PortAudioError as e:
                logger.error(f"Failed to start stream with device {device}: {e}")

                # Fallback to default device
                if device is not None:
                    logger.info("Retrying with default audio device...")
                    try:
                        self._stream = sd.InputStream(
                            samplerate=16000,
                            channels=1,
                            dtype='float32',
                            callback=self._audio_callback
                        )
                        self._stream.start()
                        self.recording = True
                        logger.info("Recording started with default device")
                    except Exception as fallback_error:
                        logger.error(f"Fallback to default device failed: {fallback_error}")
                        self._stop_writer.set()
                        self.error_occurred.emit(f"Audio device error: {str(fallback_error)}")
                        raise
                else:
                    self._stop_writer.set()
                    self.error_occurred.emit(f"Audio device error: {str(e)}")
                    raise

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.recording = False
            self._stop_writer.set()
            if self._writer_thread and self._writer_thread.is_alive():
                self._writer_thread.join(timeout=1.0)
            self.error_occurred.emit(f"Recording start failed: {str(e)}")

    def stop_recording(self) -> Optional[str]:
        """
        Stop audio recording and return file path.

        Returns:
            Absolute path to recorded WAV file, or None if recording failed
        """
        if not self.recording:
            logger.warning("Not recording, ignoring stop request")
            return None

        try:
            self.recording = False

            # Stop audio stream
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            # Signal writer thread to stop
            self._stop_writer.set()

            # Wait for writer thread to finish
            if self._writer_thread and self._writer_thread.is_alive():
                self._writer_thread.join(timeout=2.0)
                if self._writer_thread.is_alive():
                    logger.warning("Writer thread did not finish in time")

            # Return file path if it exists
            if self._current_file_path and self._current_file_path.exists():
                file_size = self._current_file_path.stat().st_size
                logger.info(f"Recording stopped: {self._current_file_path} ({file_size} bytes)")
                return str(self._current_file_path)
            else:
                logger.error("Recording file not found after stop")
                return None

        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            self.error_occurred.emit(f"Stop error: {str(e)}")
            return None

    def cleanup_temp_files(self, keep_latest: bool = False):
        """
        Clean up temporary audio files.

        Args:
            keep_latest: If True, keeps the most recent file (for transcription)
        """
        files_to_remove = self._temp_files[:-1] if keep_latest else self._temp_files

        removed_count = 0
        for file_path in files_to_remove:
            try:
                if file_path.exists():
                    file_path.unlink()
                    removed_count += 1
                    logger.debug(f"Removed temp file: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to remove temp file {file_path}: {e}")

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} temporary audio files")

        # Update list to only keep latest if requested
        if keep_latest and self._temp_files:
            self._temp_files = [self._temp_files[-1]]
        else:
            self._temp_files.clear()

    def __del__(self):
        """Destructor: cleanup on object deletion."""
        try:
            if self.recording:
                self.stop_recording()
            self.cleanup_temp_files()
        except:
            pass  # Avoid errors during cleanup
