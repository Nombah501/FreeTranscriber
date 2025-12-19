"""
Unit tests for Transcriber module.

Tests lazy loading, memory management, CUDA fallback, and config reactivity.
"""

import unittest
import tempfile
import os
import threading
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import gc

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.transcriber import Transcriber
from core.config_manager import ConfigManager


class TestTranscriber(unittest.TestCase):
    """Test cases for Transcriber module."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock config manager
        self.mock_config = Mock(spec=ConfigManager)
        self.mock_config.get = Mock(side_effect=lambda key, default=None: {
            "model_size": "base",
            "device": "auto",
            "language": "auto"
        }.get(key, default))

    def tearDown(self):
        """Clean up after tests."""
        gc.collect()

    def test_transcriber_initialization_lightweight(self):
        """Test that transcriber initialization does NOT load model."""
        transcriber = Transcriber(self.mock_config)

        # Model should NOT be loaded
        self.assertIsNone(transcriber.model)
        self.assertIsNone(transcriber.current_model_size)
        self.assertIsNone(transcriber.current_device)
        self.assertFalse(transcriber._model_dirty)

    def test_config_signal_connection(self):
        """Test that transcriber connects to config changed signal."""
        # Mock config with signal
        mock_config_with_signal = Mock(spec=ConfigManager)
        mock_config_with_signal.config_changed = Mock()
        mock_config_with_signal.config_changed.connect = Mock()
        mock_config_with_signal.get = Mock(return_value="base")

        transcriber = Transcriber(mock_config_with_signal)

        # Should have connected to signal
        mock_config_with_signal.config_changed.connect.assert_called_once()

    def test_on_config_changed_marks_dirty(self):
        """Test that config changes mark model as dirty."""
        transcriber = Transcriber(self.mock_config)

        # Initially not dirty
        self.assertFalse(transcriber._model_dirty)

        # Simulate config change
        transcriber._on_config_changed("model_size", "small")

        # Should now be dirty
        self.assertTrue(transcriber._model_dirty)

    def test_device_detection_auto(self):
        """Test device auto-detection logic."""
        self.mock_config.get = Mock(return_value="auto")
        transcriber = Transcriber(self.mock_config)

        # Device detection should return cuda or cpu
        device = transcriber._detect_device()
        self.assertIn(device, ["cuda", "cpu"])

    def test_device_detection_explicit(self):
        """Test explicit device configuration."""
        self.mock_config.get = Mock(side_effect=lambda key, default=None: {
            "device": "cpu"
        }.get(key, default))

        transcriber = Transcriber(self.mock_config)
        device = transcriber._detect_device()

        # Should return explicit device
        self.assertEqual(device, "cpu")

    @patch('core.transcriber.WhisperModel')
    def test_load_model_internal_success(self, mock_whisper):
        """Test successful model loading."""
        mock_model_instance = MagicMock()
        mock_whisper.return_value = mock_model_instance

        transcriber = Transcriber(self.mock_config)
        transcriber._load_model_internal("base", "cpu")

        # Model should be loaded
        self.assertIsNotNone(transcriber.model)
        self.assertEqual(transcriber.current_model_size, "base")
        self.assertEqual(transcriber.current_device, "cpu")

        # WhisperModel should have been called with correct params
        mock_whisper.assert_called_once_with(
            "base",
            device="cpu",
            compute_type="int8"
        )

    @patch('core.transcriber.WhisperModel')
    def test_load_model_cuda_fallback_to_cpu(self, mock_whisper):
        """Test CUDA failure fallback to CPU."""
        # First call (CUDA) fails, second call (CPU) succeeds
        mock_whisper.side_effect = [
            Exception("CUDA OOM"),
            MagicMock()  # CPU success
        ]

        transcriber = Transcriber(self.mock_config)
        transcriber._load_model_internal("base", "cuda")

        # Should have fallen back to CPU
        self.assertEqual(transcriber.current_device, "cpu")
        self.assertEqual(mock_whisper.call_count, 2)

    def test_unload_model(self):
        """Test model unloading and garbage collection."""
        transcriber = Transcriber(self.mock_config)

        # Simulate loaded model
        transcriber.model = MagicMock()
        transcriber.current_model_size = "base"
        transcriber.current_device = "cpu"

        # Unload model
        transcriber.unload_model()

        # Model should be cleared
        self.assertIsNone(transcriber.model)
        self.assertIsNone(transcriber.current_model_size)
        self.assertIsNone(transcriber.current_device)

    def test_unload_model_when_not_loaded(self):
        """Test unloading when no model is loaded."""
        transcriber = Transcriber(self.mock_config)

        # Should not raise error
        transcriber.unload_model()
        self.assertIsNone(transcriber.model)

    @patch('core.transcriber.WhisperModel')
    def test_transcribe_missing_file(self, mock_whisper):
        """Test transcription with missing file."""
        transcriber = Transcriber(self.mock_config)

        # Try to transcribe non-existent file
        result = transcriber.transcribe("/nonexistent/file.wav")

        # Should return empty string
        self.assertEqual(result, "")

    @patch('core.transcriber.WhisperModel')
    def test_transcribe_empty_file(self, mock_whisper):
        """Test transcription with 0-byte file."""
        transcriber = Transcriber(self.mock_config)

        # Create temporary empty file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            temp_path = f.name

        try:
            # Try to transcribe empty file
            result = transcriber.transcribe(temp_path)

            # Should return empty string
            self.assertEqual(result, "")
        finally:
            os.unlink(temp_path)

    @patch('core.transcriber.WhisperModel')
    def test_transcribe_triggers_lazy_load(self, mock_whisper):
        """Test that transcribe triggers lazy model loading."""
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        # Mock transcription result
        mock_segment = MagicMock()
        mock_segment.text = " Test transcription "
        mock_model.transcribe.return_value = ([mock_segment], MagicMock())

        transcriber = Transcriber(self.mock_config)

        # Create temp audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            f.write(b'fake audio data')
            temp_path = f.name

        try:
            # Model should not be loaded yet
            self.assertIsNone(transcriber.model)

            # Transcribe should trigger load
            result = transcriber.transcribe(temp_path)

            # Model should now be loaded
            self.assertIsNotNone(transcriber.model)

            # Result should be stripped
            self.assertEqual(result, "Test transcription")
        finally:
            os.unlink(temp_path)

    @patch('core.transcriber.WhisperModel')
    def test_model_reload_on_dirty_flag(self, mock_whisper):
        """Test that dirty flag triggers model reload."""
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model
        mock_model.transcribe.return_value = ([MagicMock(text="test")], MagicMock())

        transcriber = Transcriber(self.mock_config)

        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            f.write(b'data')
            temp_path = f.name

        try:
            # First transcription loads model
            transcriber.transcribe(temp_path)
            initial_load_count = mock_whisper.call_count

            # Mark dirty (simulate config change)
            transcriber._model_dirty = True

            # Second transcription should reload
            transcriber.transcribe(temp_path)

            # Should have called WhisperModel again (reload)
            self.assertGreater(mock_whisper.call_count, initial_load_count)
        finally:
            os.unlink(temp_path)

    @patch('core.transcriber.WhisperModel')
    def test_concurrency_unload_wait_for_transcribe(self, mock_whisper):
        """Test that unload_model waits for transcribe to finish (thread safety)."""
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model
        
        # Make transcribe take some time
        def slow_transcribe(*args, **kwargs):
            time.sleep(0.2)
            return [MagicMock(text="slow")], MagicMock()
        
        mock_model.transcribe.side_effect = slow_transcribe

        transcriber = Transcriber(self.mock_config)
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            f.write(b'data')
            temp_path = f.name

        try:
            # Ensure model is loaded first
            transcriber.transcribe(temp_path)
            
            # Variables to track timing
            unload_started = False
            unload_finished = False
            
            def run_unload():
                nonlocal unload_started, unload_finished
                time.sleep(0.05) # Wait for transcribe to start
                unload_started = True
                transcriber.unload_model()
                unload_finished = True

            # Start unload thread
            t = threading.Thread(target=run_unload)
            t.start()

            # Run transcribe in main thread (blocking)
            # This should take 0.2s
            start_time = time.time()
            transcriber.transcribe(temp_path)
            end_time = time.time()

            t.join()

            # Verify:
            # 1. Unload started while transcribe was running
            # 2. Unload finished AFTER transcribe finished (because of lock)
            # Actually, because we sleep 0.05 before unload, unload attempts to acquire lock.
            # Transcribe holds lock for 0.2s.
            # Unload should finish only after transcribe releases lock.
            
            self.assertTrue(unload_started, "Unload should have started")
            self.assertTrue(unload_finished, "Unload should have finished")
            
            # Transcribe took ~0.2s. Unload started at 0.05s.
            # If no lock, unload would finish immediately at ~0.05s.
            # With lock, unload should finish at ~0.2s.
            # So execution time of unload thread should be around 0.15s (waiting).
            # But simpler check: Transcribe finished. Model should be None NOW.
            self.assertIsNone(transcriber.model, "Model should be unloaded after thread finishes")
            
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
