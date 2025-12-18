import keyboard
import pyperclip
import time

class InputHandler:
    def __init__(self):
        pass

    def type_text(self, text):
        """
        Copies text to clipboard and simulates Ctrl+V to paste it.
        This is more reliable than typing character by character for Cyrillic.
        """
        if not text:
            return

        # 1. Save current clipboard content
        old_clipboard = pyperclip.paste()

        # 2. Put new text into clipboard
        pyperclip.copy(text)

        # 3. Simulate Ctrl+V (or Cmd+V for Mac, but we are on Win)
        time.sleep(0.1) # Small delay to ensure focus
        keyboard.press_and_release('ctrl+v')
        
        # 4. (Optional) Restore old clipboard after a short delay
        # For now, we leave the transcribed text in clipboard as it's useful.

    def setup_hotkey(self, hotkey_str, callback):
        """
        Sets up a global hotkey.
        Example: 'ctrl+shift+space'
        """
        try:
            keyboard.add_hotkey(hotkey_str, callback)
            print(f"Hotkey '{hotkey_str}' registered.")
        except Exception as e:
            print(f"Failed to register hotkey: {e}")

if __name__ == "__main__":
    handler = InputHandler()
    print("Testing hotkey 'alt+s' in 2 seconds...")
    handler.setup_hotkey('alt+s', lambda: print("Hotkey pressed!"))
    keyboard.wait('esc')
