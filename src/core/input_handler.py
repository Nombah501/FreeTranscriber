import keyboard
import pyperclip
import time

class InputHandler:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.current_hotkey = None
        self.callback = None

    def type_text(self, text):
        """
        Copies text to clipboard and simulates Ctrl+V to paste it.
        This is more reliable than typing character by character for Cyrillic.
        """
        if not text:
            return

        # 1. Put new text into clipboard
        # Note: We rely on user config preference for 'copy_to_clipboard' if we were strict,
        # but for pasting we MUST use clipboard as the transport mechanism.
        try:
            pyperclip.copy(text)
            
            # 2. Simulate Ctrl+V
            time.sleep(0.1) # Small delay to ensure focus
            keyboard.press_and_release('ctrl+v')
        except Exception as e:
            print(f"Error typing text: {e}")

    def register_hotkey(self, hotkey_str, callback):
        """
        Registers a global hotkey, removing the previous one if it exists.
        """
        if self.current_hotkey:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except:
                pass # Ignore if it wasn't there
        
        self.current_hotkey = hotkey_str
        self.callback = callback
        
        try:
            keyboard.add_hotkey(hotkey_str, callback)
            print(f"Hotkey '{hotkey_str}' registered.")
        except Exception as e:
            print(f"Failed to register hotkey: {e}")
            self.current_hotkey = None

    def update_hotkey(self, new_hotkey):
        if self.callback and new_hotkey != self.current_hotkey:
            self.register_hotkey(new_hotkey, self.callback)