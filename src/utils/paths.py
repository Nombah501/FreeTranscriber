"""
Path management utilities for FreeTranscriber.

This module provides OS-agnostic path handling using pathlib,
especially for temp/ and logs/ directories.

Usage:
    from src.utils.paths import get_temp_dir, get_logs_dir, get_resource_path
    temp_path = get_temp_dir() / "audio.wav"
"""

from pathlib import Path
from typing import Optional
import tempfile
import uuid

from src.core.logger import get_logger


logger = get_logger(__name__)


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to project root (where main.py is located)
    """
    # Assuming this file is at src/utils/paths.py
    return Path(__file__).parent.parent.parent


def get_temp_dir() -> Path:
    """
    Get the temp directory for audio files.

    Creates the directory if it doesn't exist.

    Returns:
        Path to temp/ directory
    """
    temp_dir = get_project_root() / "temp"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir


def get_logs_dir() -> Path:
    """
    Get the logs directory.

    Creates the directory if it doesn't exist.

    Returns:
        Path to logs/ directory
    """
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_temp_audio_file(extension: str = "wav") -> Path:
    """
    Generate a unique temporary audio file path.

    Args:
        extension: File extension (default: wav)

    Returns:
        Path to temporary audio file with unique UUID name
    """
    filename = f"audio_{uuid.uuid4().hex}.{extension}"
    return get_temp_dir() / filename


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to a resource file.

    Works both in development and when bundled with PyInstaller.

    Args:
        relative_path: Relative path to resource from project root

    Returns:
        Absolute path to resource
    """
    # Check if running in PyInstaller bundle
    import sys
    if getattr(sys, 'frozen', False):
        # Running in bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in normal Python environment
        base_path = get_project_root()

    return base_path / relative_path


def cleanup_temp_files(older_than_seconds: Optional[int] = None) -> int:
    """
    Clean up old temporary files.

    Args:
        older_than_seconds: Only delete files older than this many seconds.
                           If None, delete all files in temp directory.

    Returns:
        Number of files deleted
    """
    import time

    temp_dir = get_temp_dir()
    deleted_count = 0

    for file_path in temp_dir.glob("*"):
        if not file_path.is_file():
            continue

        should_delete = False
        if older_than_seconds is None:
            should_delete = True
        else:
            file_age = time.time() - file_path.stat().st_mtime
            should_delete = file_age > older_than_seconds

        if should_delete:
            try:
                file_path.unlink()
                deleted_count += 1
                logger.debug(f"Deleted temp file: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path.name}: {e}")

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} temporary files")

    return deleted_count
