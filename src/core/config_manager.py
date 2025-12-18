import json
import os

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "window_x": 100,
            "window_y": 100,
            "model_size": "small",
            "hotkey": "ctrl+shift+space",
            "idle_opacity": 0.4
        }
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            return self.default_config.copy()
        
        try:
            with open(self.config_file, 'r') as f:
                loaded = json.load(f)
                # Merge with defaults to ensure all keys exist
                config = self.default_config.copy()
                config.update(loaded)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key):
        return self.config.get(key, self.default_config.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save_config()
