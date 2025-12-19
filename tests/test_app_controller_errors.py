import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import pyqtSignal, QObject
import sys

# Mock AudioRecorder to simulate signals
class MockAudioRecorder(QObject):
    error_occurred = pyqtSignal(str)
    amplitude_changed = pyqtSignal(float)
    
    def __init__(self, config):
        super().__init__()
        self.recording = False
        self.start_recording = MagicMock()
        self.stop_recording = MagicMock()

@pytest.fixture
def app():
    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def controller(app):
    with patch('core.audio_recorder.AudioRecorder', side_effect=MockAudioRecorder) as mock_recorder_cls:
        from main import AppController
        
        # Mock other dependencies to isolate AppController
        with patch('main.ConfigManager'), \
             patch('main.Transcriber'), \
             patch('main.InputHandler'), \
             patch('main.FloatingButton') as mock_ui_cls:
            
            mock_ui = mock_ui_cls.return_value
            mock_ui.winId.return_value = 12345
            
            ctrl = AppController(app)
            return ctrl

def test_recorder_error_handling(controller):
    """
    Test that AppController handles error_occurred signal from AudioRecorder.
    """
    # Verify flash_error is called on the UI mock
    # The UI mock is already created in the fixture via patch('main.FloatingButton')
    
    # Emit error from recorder
    error_msg = "Microphone disconnected"
    controller.recorder.error_occurred.emit(error_msg)
    
    # Assert UI interaction
    controller.ui.flash_error.assert_called_once()
    controller.ui.set_recording.assert_called_with(False)
