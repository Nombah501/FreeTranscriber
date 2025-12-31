import sys
import os
import time
import logging
from typing import Optional, Callable

try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except Exception as e:
    KEYBOARD_AVAILABLE = False
    keyboard = None

try:
    from pynput import keyboard as pynput_keyboard
    from pynput.keyboard import Key, HotKey

    PYNPUT_AVAILABLE = True
except Exception as e:
    PYNPUT_AVAILABLE = False
    pynput_keyboard = None

import pyperclip

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_linux_permissions():
    """Check if user has proper permissions for input devices on Linux."""
    if sys.platform != "linux":
        return True, None

    try:
        import grp

        username = os.getlogin()
        groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]

        if "input" not in groups:
            hint = (
                "Missing input group permissions. Run:\n"
                "  sudo usermod -a -G input $USER\n"
                "Then log out and log back in."
            )
            return False, hint

        try:
            test_path = "/dev/input/event0"
            if os.path.exists(test_path):
                if not os.access(test_path, os.R_OK):
                    hint = (
                        "No read access to input devices. Try:\n"
                        "  sudo chmod 660 /dev/input/event*\n"
                        "  sudo chown root:input /dev/input/event*"
                    )
                    return False, hint
        except Exception:
            pass

        return True, None
    except Exception as e:
        logger.warning(f"Could not check permissions: {e}")
        return True, None


class InputHandler:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.current_hotkey = None
        self.callback = None
        self.backend = None
        self.pynput_listener = None
        self.pynput_hotkey = None

        self._initialize_backend()
        self._check_permissions()

    def _initialize_backend(self):
        """Initialize keyboard backend with fallback options."""
        logger.info("Initializing keyboard backend...")

        if KEYBOARD_AVAILABLE:
            self.backend = "keyboard"
            logger.info("Using 'keyboard' library backend")
        elif PYNPUT_AVAILABLE:
            self.backend = "pynput"
            logger.info("Using 'pynput' library backend (fallback)")
        else:
            self.backend = None
            logger.error("No keyboard library available!")

    def _check_permissions(self):
        """Check and report permissions issues."""
        if sys.platform == "linux":
            has_perms, hint = check_linux_permissions()
            if not has_perms:
                logger.warning(f"Permission issue detected:\n{hint}")
                print(f"⚠️  Warning: {hint}")
        else:
            logger.info(f"Running on {sys.platform}, no permission check needed")

    def type_text(self, text):
        """
        Copies text to clipboard and simulates Ctrl+V to paste it.
        This is more reliable than typing character by character for Cyrillic.
        """
        if not text:
            return

        try:
            pyperclip.copy(text)
            time.sleep(0.1)

            if self.backend == "keyboard":
                keyboard.press_and_release("ctrl+v")
                logger.debug("Typed text using keyboard backend")
            elif self.backend == "pynput":
                controller = pynput_keyboard.Controller()
                with controller.pressed(Key.ctrl):
                    controller.press(Key.from_char("v"))
                    controller.release(Key.from_char("v"))
                logger.debug("Typed text using pynput backend")
            else:
                logger.error("No keyboard backend available for typing")
                print("⚠️  Error: Cannot type text - no keyboard backend available")

        except Exception as e:
            logger.error(f"Error typing text: {e}")
            print(f"⚠️  Error typing text: {e}")

    def register_hotkey(self, hotkey_str: str, callback: Callable):
        """
        Registers a global hotkey, removing the previous one if it exists.
        Tries multiple backends with fallback.
        """
        if self.current_hotkey:
            self.unregister_hotkey()

        self.current_hotkey = hotkey_str
        self.callback = callback

        logger.info(f"Attempting to register hotkey: {hotkey_str}")

        if self.backend == "keyboard":
            success = self._register_keyboard_hotkey(hotkey_str, callback)
        elif self.backend == "pynput":
            success = self._register_pynput_hotkey(hotkey_str, callback)
        else:
            success = False

        if success:
            logger.info(f"✓ Hotkey '{hotkey_str}' registered successfully")
            print(f"✓ Hotkey '{hotkey_str}' registered")
        else:
            logger.error(f"✗ Failed to register hotkey: {hotkey_str}")
            self._show_hotkey_error(hotkey_str)
            self.current_hotkey = None

    def _register_keyboard_hotkey(self, hotkey_str: str, callback: Callable) -> bool:
        """Register hotkey using keyboard library."""
        try:
            keyboard.add_hotkey(hotkey_str, callback)
            return True
        except Exception as e:
            logger.warning(f"keyboard library failed: {e}")
            return False

    def _register_pynput_hotkey(self, hotkey_str: str, callback: Callable) -> bool:
        """Register hotkey using pynput library."""
        try:
            keys = self._parse_hotkey_for_pynput(hotkey_str)
            if not keys:
                logger.error(f"Could not parse hotkey '{hotkey_str}' for pynput")
                return False

            hotkey_obj = HotKey(keys, callback)

            if self.pynput_listener:
                self.pynput_listener.stop()

            self.pynput_listener = pynput_keyboard.Listener(
                on_press=self._create_pynpress_handler(hotkey_obj)
            )
            self.pynput_listener.start()

            return True
        except Exception as e:
            logger.error(f"pynput hotkey registration failed: {e}")
            return False

    def _parse_hotkey_for_pynput(self, hotkey_str: str):
        """Parse hotkey string like 'ctrl+shift+f1' into pynput keys."""
        try:
            parts = hotkey_str.lower().replace("+", " ").split()
            keys = []

            for part in parts:
                if part == "ctrl":
                    keys.append(Key.ctrl)
                elif part == "alt":
                    keys.append(Key.alt)
                elif part == "shift":
                    keys.append(Key.shift)
                elif part == "cmd" or part == "super" or part == "win":
                    keys.append(Key.cmd)
                elif part.startswith("f") and part[1:].isdigit():
                    keys.append(getattr(Key, part))
                else:
                    if len(part) == 1:
                        keys.append(Key.from_char(part))
                    else:
                        try:
                            keys.append(Key[part])
                        except KeyError:
                            logger.warning(f"Unknown key: {part}")
                            return None

            return keys
        except Exception as e:
            logger.error(f"Failed to parse hotkey: {e}")
            return None

    def _create_pynpress_handler(self, hotkey_obj):
        """Create on_press handler for pynput listener."""

        def on_press(key):
            try:
                hotkey_obj.press(key)
            except AttributeError:
                pass

        return on_press

    def unregister_hotkey(self):
        """Unregister current hotkey."""
        if not self.current_hotkey:
            return

        logger.info(f"Unregistering hotkey: {self.current_hotkey}")

        try:
            if self.backend == "keyboard" and self.current_hotkey:
                try:
                    if keyboard is not None:
                        keyboard.remove_hotkey(self.current_hotkey)
                except:
                    pass
            elif self.backend == "pynput" and self.pynput_listener:
                self.pynput_listener.stop()
                self.pynput_listener = None

            logger.info(f"Hotkey '{self.current_hotkey}' unregistered")
        except Exception as e:
            logger.warning(f"Error unregistering hotkey: {e}")
        finally:
            self.current_hotkey = None

    def update_hotkey(self, new_hotkey: str):
        """Update hotkey to new value."""
        if self.callback and new_hotkey != self.current_hotkey:
            self.register_hotkey(new_hotkey, self.callback)

    def _show_hotkey_error(self, hotkey_str: str):
        """Show helpful error message when hotkey registration fails."""
        print(f"\n✗ Failed to register hotkey: '{hotkey_str}'")
        print("\nPossible solutions:")

        if sys.platform == "linux":
            print("  1. Add your user to the 'input' group:")
            print("     sudo usermod -a -G input $USER")
            print("     (Then log out and log back in)")
            print("\n  2. Fix permissions on /dev/input devices:")
            print("     sudo chmod 660 /dev/input/event*")
            print("     sudo chown root:input /dev/input/event*")
            print("\n  3. Try running with sudo (not recommended)")

        print("\n  4. The application will continue, but hotkeys won't work.")
        print("  5. You can use the floating button to trigger recording instead.\n")

    def __del__(self):
        """Cleanup on destruction."""
        self.unregister_hotkey()
