import keyboard
import pyperclip
import time
import ctypes
import ctypes.wintypes
from core.logger import get_logger

logger = get_logger(__name__)

class NativeHotkeyManager:
    """
    Handles global hotkey registration using Windows API (RegisterHotKey).
    This provides better reliability than the standard 'keyboard' library on Windows.
    """
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    WM_HOTKEY = 0x0312

    # Virtual Key Codes
    VK_SPACE = 0x20
    
    KEY_MAP = {
        'space': 0x20,
        'enter': 0x0D,
        'tab': 0x09,
        'escape': 0x1B,
        'esc': 0x1B,
        'backspace': 0x08,
        'insert': 0x2D,
        'delete': 0x2E,
        'home': 0x24,
        'end': 0x23,
        'pageup': 0x21,
        'pagedown': 0x22,
        'up': 0x26,
        'down': 0x28,
        'left': 0x25,
        'right': 0x27,
        'f1': 0x70,
        'f2': 0x71,
        'f3': 0x72,
        'f4': 0x73,
        'f5': 0x74,
        'f6': 0x75,
        'f7': 0x76,
        'f8': 0x77,
        'f9': 0x78,
        'f10': 0x79,
        'f11': 0x7A,
        'f12': 0x7B,
    }

    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.registered_hotkeys = {}

    def parse_hotkey(self, hotkey_str):
        """
        Parses a string like 'ctrl+shift+space' into modifiers and virtual key code.
        """
        parts = hotkey_str.lower().replace(" ", "").split('+')
        modifiers = 0
        vk = 0

        for part in parts:
            if part == 'ctrl' or part == 'control':
                modifiers |= self.MOD_CONTROL
            elif part == 'shift':
                modifiers |= self.MOD_SHIFT
            elif part == 'alt':
                modifiers |= self.MOD_ALT
            elif part == 'win' or part == 'windows':
                modifiers |= self.MOD_WIN
            else:
                # Try to get VK code from map or use ord() for single characters
                if part in self.KEY_MAP:
                    vk = self.KEY_MAP[part]
                elif len(part) == 1:
                    vk = self.user32.VkKeyScanW(ord(part)) & 0xFF
                else:
                    logger.warning(f"Unknown key in hotkey: {part}")

        return modifiers, vk

    def register(self, hwnd, hotkey_id, hotkey_str):
        """
        Registers a global hotkey for a specific window handle.
        """
        modifiers, vk = self.parse_hotkey(hotkey_str)
        if not vk:
            logger.error(f"Failed to parse hotkey: {hotkey_str}")
            return False

        # Unregister if ID already exists
        self.unregister(hwnd, hotkey_id)

        if self.user32.RegisterHotKey(hwnd, hotkey_id, modifiers, vk):
            self.registered_hotkeys[hotkey_id] = hotkey_str
            logger.info(f"Native hotkey '{hotkey_str}' registered with ID {hotkey_id}")
            return True
        else:
            logger.error(f"Failed to register native hotkey '{hotkey_str}'")
            return False

    def unregister(self, hwnd, hotkey_id):
        if hotkey_id in self.registered_hotkeys:
            self.user32.UnregisterHotKey(hwnd, hotkey_id)
            del self.registered_hotkeys[hotkey_id]
            return True
        return False

class InputHandler:
    PASTE_DELAY = 0.15
    HOTKEY_ID = 1

    def __init__(self, config_manager=None):
        self.config = config_manager
        self.current_hotkey = None
        self.callback = None
        self.native_manager = NativeHotkeyManager()
        self.is_native_active = False

    def type_text(self, text):
        """
        Copies text to clipboard and simulates Ctrl+V to paste it.
        This is more reliable than typing character by character for Cyrillic.
        """
        if not text:
            return

        try:
            # 1. Store current clipboard to restore it later? 
            # (Optional improvement, but for now just copy)
            pyperclip.copy(text)

            # 2. Simulate Ctrl+V with a small safety delay
            time.sleep(self.PASTE_DELAY) 
            keyboard.press_and_release('ctrl+v')
            logger.info("Text injected via clipboard")
        except Exception as e:
            logger.error(f"Error typing text: {e}")

    def register_hotkey(self, hotkey_str, callback, hwnd=None):
        """
        Registers a global hotkey. Tries native Windows API first, 
        falls back to 'keyboard' library.
        """
        self.callback = callback
        
        # Try native registration if HWND is provided (PyQt window)
        if hwnd:
            if self.native_manager.register(hwnd, self.HOTKEY_ID, hotkey_str):
                self.current_hotkey = hotkey_str
                self.is_native_active = True
                return True

        # Fallback to keyboard library
        self.is_native_active = False
        if self.current_hotkey and not self.is_native_active:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except:
                pass

        self.current_hotkey = hotkey_str
        try:
            keyboard.add_hotkey(hotkey_str, callback)
            logger.info(f"Fallback hotkey '{hotkey_str}' registered.")
            return True
        except Exception as e:
            logger.error(f"Failed to register fallback hotkey: {e}")
            self.current_hotkey = None
            return False

    def update_hotkey(self, new_hotkey, hwnd=None):
        if self.callback and new_hotkey != self.current_hotkey:
            return self.register_hotkey(new_hotkey, self.callback, hwnd)
        return False

    def unregister_all(self, hwnd=None):
        if hwnd and self.is_native_active:
            self.native_manager.unregister(hwnd, self.HOTKEY_ID)
        
        if self.current_hotkey and not self.is_native_active:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except:
                pass