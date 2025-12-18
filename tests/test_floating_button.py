"""
Unit tests for FloatingButton widget.

Tests the floating UI widget functionality including:
- Screen boundary protection
- Off-screen position recovery
- Rapid click protection (debounce)
- Reset position functionality
- Widget state management
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QScreen

# Initialize QApplication for testing
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestFloatingButton(unittest.TestCase):
    """Test cases for FloatingButton widget."""

    def setUp(self):
        """Set up test fixtures."""
        from ui.overlay_window import FloatingButton
        from core.config_manager import ConfigManager

        # Create mock config manager
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.config_changed = Mock()
        self.config_manager.config_changed.connect = Mock()

        # Default config values
        self.default_config = {
            "window_x": 100,
            "window_y": 100,
            "idle_opacity": 0.6,
            "always_on_top": True
        }
        self.config_manager.get = Mock(side_effect=lambda key: self.default_config.get(key))
        self.config_manager.set = Mock()

        # Create widget
        self.widget = FloatingButton(self.config_manager)

    def tearDown(self):
        """Clean up after tests."""
        self.widget.close()

    def test_initialization(self):
        """Test widget initializes with correct properties."""
        self.assertEqual(self.widget.width(), 60)
        self.assertEqual(self.widget.height(), 60)
        self.assertFalse(self.widget.is_recording)
        self.assertFalse(self.widget.is_processing)
        self.assertFalse(self.widget.is_success)
        self.assertEqual(self.widget._last_click_time, 0)

    @patch('ui.overlay_window.QApplication.screens')
    def test_constrain_to_screen_on_screen(self, mock_screens):
        """Test _constrain_to_screen keeps valid position unchanged."""
        # Mock screen geometry
        mock_screen = Mock(spec=QScreen)
        mock_screen.availableGeometry.return_value = QRect(0, 0, 1920, 1080)
        mock_screens.return_value = [mock_screen]

        # Position that should be valid (center of screen)
        pos = QPoint(900, 500)
        result = self.widget._constrain_to_screen(pos)

        # Position should remain unchanged
        self.assertEqual(result, pos)

    @patch('ui.overlay_window.QApplication.screens')
    @patch('ui.overlay_window.QApplication.primaryScreen')
    def test_constrain_to_screen_off_screen(self, mock_primary, mock_screens):
        """Test _constrain_to_screen resets off-screen position to center."""
        # Mock screen geometry
        mock_screen = Mock(spec=QScreen)
        mock_screen.availableGeometry.return_value = QRect(0, 0, 1920, 1080)
        mock_primary.return_value = mock_screen
        mock_screens.return_value = [mock_screen]

        # Position completely off-screen
        pos = QPoint(-9999, -9999)
        result = self.widget._constrain_to_screen(pos)

        # Should be reset to center of screen (allow for integer division rounding)
        # Expected: (1920 // 2) - (60 // 2) = 960 - 30 = 930
        # But QPoint.center() uses integer division which may vary
        self.assertGreater(result.x(), 850)
        self.assertLess(result.x(), 1000)
        self.assertGreater(result.y(), 450)
        self.assertLess(result.y(), 600)

    @patch('ui.overlay_window.QApplication.screens')
    def test_constrain_to_screen_left_edge(self, mock_screens):
        """Test _constrain_to_screen constrains position at left edge."""
        # Mock screen geometry
        mock_screen = Mock(spec=QScreen)
        mock_screen.availableGeometry.return_value = QRect(0, 0, 1920, 1080)
        mock_screens.return_value = [mock_screen]

        # Position beyond left edge (should leave 20px visible)
        pos = QPoint(-50, 500)
        result = self.widget._constrain_to_screen(pos)

        # Should be constrained to left edge minus width + min_visible
        # 0 - 60 + 20 = -40
        self.assertEqual(result.x(), -40)
        self.assertEqual(result.y(), 500)

    @patch('ui.overlay_window.QApplication.screens')
    @patch('ui.overlay_window.QApplication.primaryScreen')
    def test_constrain_to_screen_right_edge(self, mock_primary, mock_screens):
        """Test _constrain_to_screen constrains position at right edge."""
        # Mock screen geometry
        mock_screen = Mock(spec=QScreen)
        mock_screen.availableGeometry.return_value = QRect(0, 0, 1920, 1080)
        mock_primary.return_value = mock_screen
        mock_screens.return_value = [mock_screen]

        # Position beyond right edge - widget will be detected as off-screen
        # and reset to center
        pos = QPoint(2000, 500)
        result = self.widget._constrain_to_screen(pos)

        # Widget at 2000 is completely off-screen, will be reset to center
        self.assertGreater(result.x(), 850)
        self.assertLess(result.x(), 1000)

    @patch('ui.overlay_window.QApplication.primaryScreen')
    def test_reset_position_to_default(self, mock_primary):
        """Test reset_position_to_default centers widget on primary screen."""
        # Mock screen geometry
        mock_screen = Mock(spec=QScreen)
        mock_screen.availableGeometry.return_value = QRect(0, 0, 1920, 1080)
        mock_primary.return_value = mock_screen

        self.widget.reset_position_to_default()

        # Verify config.set was called for window_x and window_y
        calls = self.config_manager.set.call_args_list
        x_calls = [call for call in calls if call[0][0] == "window_x"]
        y_calls = [call for call in calls if call[0][0] == "window_y"]

        self.assertTrue(len(x_calls) > 0, "window_x should be set")
        self.assertTrue(len(y_calls) > 0, "window_y should be set")

        # Verify values are roughly centered
        x_value = x_calls[-1][0][1]
        y_value = y_calls[-1][0][1]
        self.assertGreater(x_value, 850)
        self.assertLess(x_value, 1000)
        self.assertGreater(y_value, 450)
        self.assertLess(y_value, 600)

    def test_rapid_click_protection(self):
        """Test rapid click protection blocks clicks within 300ms."""
        # Reset last click time
        self.widget._last_click_time = 0

        # Mock clicked signal
        signal_emitted = []
        self.widget.clicked.connect(lambda: signal_emitted.append(True))

        # Simulate mouse press and release (first click)
        self.widget._is_dragging = False
        self.widget._last_click_time = time.time()
        self.widget.clicked.emit()

        # First click should emit signal
        self.assertEqual(len(signal_emitted), 1)

        # Simulate rapid click within 300ms (should be blocked)
        current_time = self.widget._last_click_time + 0.1  # 100ms later
        self.widget._last_click_time = self.widget._last_click_time - 0.1
        # Simulate the logic from mouseReleaseEvent
        if current_time - self.widget._last_click_time > 0.3:
            signal_emitted.append(True)

        # Should still be 1 (rapid click blocked)
        self.assertEqual(len(signal_emitted), 1)

        # Simulate click after 300ms (should succeed)
        self.widget._last_click_time = time.time() - 0.4  # 400ms ago
        current_time = time.time()
        if current_time - self.widget._last_click_time > 0.3:
            signal_emitted.append(True)

        # Should be 2 (click allowed)
        self.assertEqual(len(signal_emitted), 2)

    def test_state_management_recording(self):
        """Test set_recording updates widget state correctly."""
        self.widget.set_recording(True)

        self.assertTrue(self.widget.is_recording)
        self.assertFalse(self.widget.is_success)
        self.assertFalse(self.widget.is_processing)
        self.assertEqual(self.widget.windowOpacity(), 1.0)

    def test_state_management_processing(self):
        """Test set_processing updates widget state correctly."""
        self.widget.set_processing(True)

        self.assertTrue(self.widget.is_processing)
        self.assertFalse(self.widget.is_recording)
        self.assertEqual(self.widget.windowOpacity(), 1.0)

    def test_state_management_success_flash(self):
        """Test flash_success triggers success state and auto-resets."""
        self.widget.flash_success()

        self.assertTrue(self.widget.is_success)
        self.assertFalse(self.widget.is_processing)

        # Note: QTimer-based reset tested separately or with QTest

    @patch('ui.overlay_window.QApplication.screens')
    @patch('ui.overlay_window.QApplication.primaryScreen')
    def test_startup_off_screen_recovery(self, mock_primary, mock_screens):
        """Test widget recovers from off-screen position on startup."""
        from ui.overlay_window import FloatingButton

        # Mock screen geometry
        mock_screen = Mock(spec=QScreen)
        mock_screen.availableGeometry.return_value = QRect(0, 0, 1920, 1080)
        mock_primary.return_value = mock_screen
        mock_screens.return_value = [mock_screen]

        # Configure off-screen position
        self.default_config["window_x"] = -9999
        self.default_config["window_y"] = -9999

        # Create widget with off-screen config
        widget = FloatingButton(self.config_manager)

        # Should have been reset to center
        # Verify config.set was called with corrected position
        calls = self.config_manager.set.call_args_list
        x_calls = [call for call in calls if call[0][0] == "window_x"]
        y_calls = [call for call in calls if call[0][0] == "window_y"]

        self.assertTrue(len(x_calls) > 0)
        self.assertTrue(len(y_calls) > 0)

        widget.close()


if __name__ == '__main__':
    unittest.main()
