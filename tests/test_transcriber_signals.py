import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QObject

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.transcriber import Transcriber

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.get.return_value = "base" # Default model size
    return config

def test_transcriber_loading_signals(mock_config):
    """
    Test that Transcriber emits loading signals when loading model.
    """
    with patch('core.transcriber.WhisperModel') as MockModel:
        transcriber = Transcriber(mock_config)
        
        # Create mocks for signals (since they are pyqtBoundSignal, we can't spy easily without connection)
        # We will connect them to MagicMocks
        start_mock = MagicMock()
        finish_mock = MagicMock()
        
        transcriber.model_loading_started.connect(start_mock)
        transcriber.model_loading_finished.connect(finish_mock)
        
        # Trigger load
        transcriber.load_model()
        
        # Verify signals
        start_mock.assert_called_once()
        finish_mock.assert_called_once()
        
        # Verify order? (start called before finish)
        # We can check parent mock calls if we want, but simple existence is enough for now.

def test_transcriber_loading_error_signals(mock_config):
    """
    Test that Transcriber emits finished signal even if loading fails.
    """
    with patch('core.transcriber.WhisperModel', side_effect=Exception("Load failed")):
        transcriber = Transcriber(mock_config)
        
        start_mock = MagicMock()
        finish_mock = MagicMock()
        
        transcriber.model_loading_started.connect(start_mock)
        transcriber.model_loading_finished.connect(finish_mock)
        
        # Trigger load - expect exception
        with pytest.raises(Exception):
            transcriber.load_model()
        
        # Verify signals
        start_mock.assert_called_once()
        finish_mock.assert_called_once() # Should be called despite error
