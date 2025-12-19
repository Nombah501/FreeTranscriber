"""
Whisper Transcriber Service with Smart Memory Management.

This module provides local speech-to-text transcription using:
- Faster-Whisper (CTranslate2 backend) for performance
- Lazy loading (model loads on first use, not at init)
- Dynamic unloading for memory management
- CUDA auto-detection with CPU fallback
- Config reactivity for model changes
"""

import os
import gc
from typing import Optional
from faster_whisper import WhisperModel
from PyQt6.QtCore import QObject, pyqtSignal

from core.logger import get_logger

logger = get_logger(__name__)


class Transcriber(QObject):
    """
    Local AI transcriber using Faster-Whisper.

    Signals:
        model_loading_started: Emitted when model load begins
        model_loading_finished: Emitted when model load completes
    """
    
    model_loading_started = pyqtSignal()
    model_loading_finished = pyqtSignal()

    def __init__(self, config_manager):
        """
        Initialize transcriber (lightweight, no model loading).

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__()
        self.config = config_manager
        self.model: Optional[WhisperModel] = None
        self.current_model_size: Optional[str] = None
        self.current_device: Optional[str] = None
        self._model_dirty = False  # Flag to force reload on next transcribe

        # Connect to config changes for model reload detection
        if hasattr(self.config, 'config_changed'):
            self.config.config_changed.connect(self._on_config_changed)

        logger.info("Transcriber initialized (model will load on demand)")

    def _on_config_changed(self, key: str, value):
        """
        Handle config changes to trigger model reload when needed.

        Args:
            key: Configuration key that changed
            value: New value
        """
        if key in ('model_size', 'device'):
            logger.info(f"Config changed: {key}={value}, marking model for reload")
            self._model_dirty = True

    def _detect_device(self) -> str:
        """
        Auto-detect best available device (CUDA or CPU).

        Returns:
            'cuda' if NVIDIA GPU available, 'cpu' otherwise
        """
        device_config = self.config.get("device", "auto")

        if device_config == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    logger.info("CUDA GPU detected, will use device='cuda'")
                    return "cuda"
            except ImportError:
                logger.debug("torch not available for CUDA detection")

            # Check CTranslate2's own detection
            try:
                # Try to create a dummy model on CUDA
                test_model = WhisperModel("tiny", device="cuda", compute_type="float16")
                del test_model
                logger.info("CTranslate2 CUDA available")
                return "cuda"
            except Exception as e:
                logger.debug(f"CUDA not available: {e}")

            logger.info("No CUDA available, will use device='cpu'")
            return "cpu"
        else:
            return device_config

    def _load_model_internal(self, model_size: str, device: str):
        """
        Internal method to load Whisper model with fallback logic.

        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: Device to use ('cuda' or 'cpu')

        Raises:
            Exception: If both CUDA and CPU loading fail
        """
        compute_type = "float16" if device == "cuda" else "int8"

        logger.info(f"Loading Whisper model '{model_size}' on {device} ({compute_type})...")
        self.model_loading_started.emit()

        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )
            self.current_model_size = model_size
            self.current_device = device
            logger.info(f"Model '{model_size}' loaded successfully on {device}")

        except Exception as e:
            logger.error(f"Failed to load model on {device}: {e}")

            # Fallback to CPU if CUDA failed
            if device == "cuda":
                logger.warning("Attempting fallback to CPU with INT8...")
                try:
                    self.model = WhisperModel(
                        model_size,
                        device="cpu",
                        compute_type="int8"
                    )
                    self.current_model_size = model_size
                    self.current_device = "cpu"
                    logger.info(f"Model '{model_size}' loaded successfully on CPU (fallback)")
                except Exception as e2:
                    logger.error(f"CRITICAL: CPU fallback also failed: {e2}")
                    self.model_loading_finished.emit() # Ensure we finish even on error
                    raise
            else:
                # Already on CPU, can't fallback further
                logger.error("CRITICAL: Failed to load model on CPU")
                self.model_loading_finished.emit() # Ensure we finish even on error
                raise
        
        self.model_loading_finished.emit()

    def load_model(self):
        """
        Load model on demand or reload if config changed.

        This is called automatically by transcribe() but can be called
        explicitly to pre-load the model.
        """
        model_size = self.config.get("model_size", "base")
        device = self._detect_device()

        # Check if reload needed
        needs_reload = (
            self.model is None or
            self._model_dirty or
            self.current_model_size != model_size or
            self.current_device != device
        )

        if not needs_reload:
            logger.debug("Model already loaded with current config, skipping reload")
            return

        # Unload old model first
        if self.model is not None:
            logger.info("Unloading old model before reload...")
            self.unload_model()

        # Load new model
        self._load_model_internal(model_size, device)
        self._model_dirty = False

    def unload_model(self):
        """
        Unload model to free memory (VRAM/RAM).

        This explicitly deletes the model instance and runs garbage collection
        to force memory release. Useful for 24/7 running apps.
        """
        if self.model is not None:
            logger.info("Unloading Whisper model...")
            del self.model
            self.model = None
            self.current_model_size = None
            self.current_device = None

            # Force garbage collection to free CTranslate2 memory
            gc.collect()
            logger.info("Model unloaded, memory freed")
        else:
            logger.debug("No model loaded, nothing to unload")

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Absolute path to WAV file (16kHz mono float32)

        Returns:
            Transcribed text string, or empty string on error
        """
        # Validate file exists
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return ""

        # Validate file size (avoid 0-byte files)
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            logger.error(f"Audio file is empty (0 bytes): {audio_path}")
            return ""

        # Ensure model is loaded
        if self.model is None or self._model_dirty:
            logger.debug("Model not loaded or dirty, loading now...")
            try:
                self.load_model()
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                return ""

        if self.model is None:
            error_msg = "Model failed to load, cannot transcribe"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Perform transcription
        try:
            # Get language from config
            language = self.config.get("language", "auto")
            if language == "auto":
                language = None

            logger.debug(f"Transcribing {file_size} bytes from {audio_path}")

            segments, info = self.model.transcribe(
                audio_path,
                beam_size=5,
                language=language
            )

            # Concatenate all segments
            text = "".join(segment.text for segment in segments)
            result = text.strip()

            logger.info(f"Transcription complete: {len(result)} characters")
            return result

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise
