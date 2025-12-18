"""
Unit tests for logger module.

Tests the centralized logging functionality including:
- Logger initialization and singleton behavior
- File and console handler configuration
- Log format and output
"""

import unittest
import logging
from pathlib import Path
import tempfile
import shutil

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logger import get_logger, reset_logger


class TestLogger(unittest.TestCase):
    """Test cases for logger module."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset logger before each test
        reset_logger()

    def tearDown(self):
        """Clean up after tests."""
        reset_logger()

    def test_logger_initialization(self):
        """Test that logger can be initialized."""
        logger = get_logger()
        self.assertIsNotNone(logger)
        self.assertIsInstance(logger, logging.Logger)

    def test_logger_singleton(self):
        """Test that get_logger returns the same instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        # Both should reference the same root logger
        self.assertEqual(logger1.root, logger2.root)

    def test_logger_with_name(self):
        """Test that logger can be created with custom name."""
        logger = get_logger("test_module")
        self.assertEqual(logger.name, "FreeTranscriber.test_module")

    def test_logger_has_handlers(self):
        """Test that logger has both console and file handlers."""
        logger = get_logger()
        # Get root logger to check handlers
        root_logger = logging.getLogger("FreeTranscriber")
        self.assertEqual(len(root_logger.handlers), 2)

        # Check handler types
        handler_types = [type(h).__name__ for h in root_logger.handlers]
        self.assertIn("StreamHandler", handler_types)
        self.assertIn("RotatingFileHandler", handler_types)

    def test_log_file_created(self):
        """Test that log file is created in logs directory."""
        logger = get_logger()
        logger.info("Test message")

        log_file = Path("logs/freetranscriber.log")
        self.assertTrue(log_file.exists())

    def test_log_format(self):
        """Test that log messages have correct format."""
        logger = get_logger("test_format")
        logger.info("Test format message")

        # Read log file
        log_file = Path("logs/freetranscriber.log")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check format contains timestamp, level, module name
        self.assertIn("[INFO", content)
        self.assertIn("[FreeTranscriber.test_format]", content)
        self.assertIn("Test format message", content)

    def test_logger_levels(self):
        """Test that different log levels work."""
        logger = get_logger("test_levels")

        # Test different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Read log file
        log_file = Path("logs/freetranscriber.log")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # All levels should be in file (file handler is DEBUG level)
        self.assertIn("Debug message", content)
        self.assertIn("Info message", content)
        self.assertIn("Warning message", content)
        self.assertIn("Error message", content)

    def test_reset_logger(self):
        """Test that reset_logger clears the logger instance."""
        logger1 = get_logger()
        reset_logger()
        logger2 = get_logger()

        # After reset, should get fresh instance with handlers
        root_logger = logging.getLogger("FreeTranscriber")
        self.assertEqual(len(root_logger.handlers), 2)


if __name__ == "__main__":
    unittest.main()
