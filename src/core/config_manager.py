import json
import os
from PyQt6.QtCore import QObject, pyqtSignal
from core.logger import get_logger

logger = get_logger(__name__)

class ConfigManager(QObject):
    # Сигнал, который испускается при изменении любой настройки
    # Передает ключ и новое значение
    config_changed = pyqtSignal(str, object)

    def __init__(self, config_file="config.json"):
        super().__init__()
        self.config_file = config_file
        self.default_config = {
            # Window settings
            "window_x": 100,
            "window_y": 100,
            "idle_opacity": 0.6,
            "active_opacity": 1.0,
            "always_on_top": True,
            
            # AI & Transcription settings
            "model_size": "base",  # tiny, base, small, medium, large
            "device": "auto",      # auto, cpu, cuda
            "language": "ru",      # ru, en, auto
            
            # Audio settings
            "input_device_id": None, # None = default system device
            "sample_rate": 16000,
            
            # UX/Control settings
            "hotkey": "ctrl+shift+space",
            "use_sounds": True,
            "copy_to_clipboard": True,
            "type_text": True,
            
            # History
            "save_history": True,
            "history_limit": 50
        }
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            return self.default_config.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge with defaults to ensure all keys exist
                config = self.default_config.copy()
                config.update(loaded)
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.default_config.copy()

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default if default is not None else self.default_config.get(key))

    def set(self, key, value):
        # Only save and signal if value actually changed
        if self.config.get(key) != value:
            self.config[key] = value
            self.save_config()
            self.config_changed.emit(key, value)