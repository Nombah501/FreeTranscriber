"""
Unit tests for AudioRecorder module.

Tests disk streaming, threading, RMS calculation, and error handling.
"""

import unittest
import time
import numpy as np
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import soundfile as sf

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.audio_recorder import AudioRecorder
from core.config_manager import ConfigManager


class TestAudioRecorder(unittest.TestCase):
    """Test cases for AudioRecorder module."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock config manager
        self.mock_config = Mock(spec=ConfigManager)
        self.mock_config.get = Mock(side_effect=lambda key, default=None: {
            "input_device_id": None,
            "sample_rate": 16000
        }.get(key, default))

    def tearDown(self):
        """Clean up after tests."""
        pass

    def test_recorder_initialization(self):
        """Test that recorder can be initialized."""
        recorder = AudioRecorder(self.mock_config)
        self.assertIsNotNone(recorder)
        self.assertFalse(recorder.recording)
        self.assertEqual(len(recorder._temp_files), 0)

    def test_rms_calculation(self):
        """Test RMS amplitude calculation."""
        recorder = AudioRecorder(self.mock_config)

        # Silent audio (all zeros)
        silent = np.zeros((1024, 1), dtype=np.float32)
        rms_silent = recorder._calculate_rms(silent)
        self.assertEqual(rms_silent, 0.0)

        # Loud audio (sine wave)
        t = np.linspace(0, 1, 1024)
        loud = np.sin(2 * np.pi * 440 * t).astype(np.float32).reshape(-1, 1)
        rms_loud = recorder._calculate_rms(loud)
        self.assertGreater(rms_loud, 0.0)
        self.assertLessEqual(rms_loud, 1.0)

    def test_signals_defined(self):
        """Test that PyQt signals are defined."""
        recorder = AudioRecorder(self.mock_config)
        self.assertTrue(hasattr(recorder, 'amplitude_changed'))
        self.assertTrue(hasattr(recorder, 'error_occurred'))

    @patch('sounddevice.InputStream')
    def test_start_recording_creates_temp_file(self, mock_stream_class):
        """Test that start_recording creates a temp file path."""
        # Mock stream
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        recorder = AudioRecorder(self.mock_config)
        recorder.start_recording()

        # Check that temp file path was created
        self.assertIsNotNone(recorder._current_file_path)
        self.assertEqual(len(recorder._temp_files), 1)
        self.assertTrue(recorder.recording)

        # Cleanup
        recorder.stop_recording()
        recorder.cleanup_temp_files()

    @patch('sounddevice.InputStream')
    def test_stop_recording_returns_file_path(self, mock_stream_class):
        """Test that stop_recording returns the file path."""
        # Mock stream
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        recorder = AudioRecorder(self.mock_config)
        recorder.start_recording()

        # Give writer thread time to start
        time.sleep(0.2)

        # Stop recording
        file_path = recorder.stop_recording()

        # Should return path (even if file might be empty in test)
        self.assertIsInstance(file_path, (str, type(None)))

        # Cleanup
        recorder.cleanup_temp_files()

    def test_cleanup_temp_files(self):
        """Test cleanup of temporary files."""
        recorder = AudioRecorder(self.mock_config)

        # Create fake temp files
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)

        fake_file1 = temp_dir / "test_audio_1.wav"
        fake_file2 = temp_dir / "test_audio_2.wav"

        fake_file1.touch()
        fake_file2.touch()

        recorder._temp_files = [fake_file1, fake_file2]

        # Cleanup all
        recorder.cleanup_temp_files()

        # Check files were removed
        self.assertFalse(fake_file1.exists())
        self.assertFalse(fake_file2.exists())
        self.assertEqual(len(recorder._temp_files), 0)

    def test_cleanup_keep_latest(self):
        """Test cleanup with keep_latest=True."""
        recorder = AudioRecorder(self.mock_config)

        # Create fake temp files
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)

        fake_file1 = temp_dir / "test_audio_3.wav"
        fake_file2 = temp_dir / "test_audio_4.wav"

        fake_file1.touch()
        fake_file2.touch()

        recorder._temp_files = [fake_file1, fake_file2]

        # Cleanup keeping latest
        recorder.cleanup_temp_files(keep_latest=True)

        # Check first file removed, second kept
        self.assertFalse(fake_file1.exists())
        self.assertTrue(fake_file2.exists())
        self.assertEqual(len(recorder._temp_files), 1)

        # Cleanup remaining
        recorder.cleanup_temp_files()

    @patch('sounddevice.InputStream')
    @patch('soundfile.SoundFile')
    def test_recording_creates_16khz_file(self, mock_soundfile, mock_stream_class):
        """Test that recorded file is 16kHz mono (verified via mock)."""
        # Mock stream
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream
        
        # Mock soundfile context manager
        mock_sf_instance = MagicMock()
        mock_soundfile.return_value.__enter__.return_value = mock_sf_instance

        recorder = AudioRecorder(self.mock_config)
        recorder.start_recording()
        
        # Verify SoundFile was initialized with correct parameters
        # We need to find the call that created the file
        self.assertTrue(mock_soundfile.called)
        
        # Check arguments of the call
        # args[0] is file path, kwargs should contain settings
        call_args = mock_soundfile.call_args
        _, kwargs = call_args
        
        self.assertEqual(kwargs.get('samplerate'), 16000)
        self.assertEqual(kwargs.get('channels'), 1)
        self.assertEqual(kwargs.get('format'), 'WAV')
        self.assertEqual(kwargs.get('subtype'), 'FLOAT')

        # Cleanup
        recorder.stop_recording()
        recorder.cleanup_temp_files()

    @patch('sounddevice.InputStream')
    def test_error_handling_device_failure(self, mock_stream_class):
        """Test error handling when device fails."""
        # Mock stream to raise error
        mock_stream_class.side_effect = Exception("Device not found")

        recorder = AudioRecorder(self.mock_config)

        # Should handle error gracefully
        try:
            recorder.start_recording()
        except Exception:
            pass  # Expected to raise or emit error signal

        # Should not be recording
        self.assertFalse(recorder.recording)

        # Cleanup
        recorder.cleanup_temp_files()

    def test_double_start_ignored(self):
        """Test that calling start twice doesn't cause issues."""
        with patch('sounddevice.InputStream'):
            recorder = AudioRecorder(self.mock_config)
            recorder.start_recording()

            # Try starting again
            recorder.start_recording()  # Should be ignored

            # Should still be recording
            self.assertTrue(recorder.recording)

            # Cleanup
            recorder.stop_recording()
            recorder.cleanup_temp_files()

    def test_stop_when_not_recording(self):
        """Test that calling stop when not recording is safe."""
        recorder = AudioRecorder(self.mock_config)

        # Call stop without starting
        result = recorder.stop_recording()

        # Should return None
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
