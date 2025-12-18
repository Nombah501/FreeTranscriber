import pytest
from unittest.mock import MagicMock, patch
from core.input_handler import InputHandler

@pytest.fixture
def input_handler():
    config = MagicMock()
    return InputHandler(config)

def test_type_text_empty(input_handler):
    with patch('pyperclip.copy') as mock_copy:
        input_handler.type_text("")
        mock_copy.assert_not_called()

def test_type_text_cyrillic(input_handler):
    test_text = "Привет, мир!"
    with patch('pyperclip.copy') as mock_copy, \
         patch('keyboard.press_and_release') as mock_keyboard, \
         patch('time.sleep'): # Skip sleep in tests
        input_handler.type_text(test_text)
        mock_copy.assert_called_once_with(test_text)
        mock_keyboard.assert_called_once_with('ctrl+v')

def test_register_hotkey_fallback(input_handler):
    callback = MagicMock()
    # Mock NativeHotkeyManager to fail registration to trigger fallback
    with patch.object(input_handler.native_manager, 'register', return_value=False), \
         patch('keyboard.add_hotkey') as mock_add:
        input_handler.register_hotkey("ctrl+shift+space", callback)
        mock_add.assert_called_once_with("ctrl+shift+space", callback)
        assert input_handler.current_hotkey == "ctrl+shift+space"
        assert input_handler.is_native_active is False

def test_register_hotkey_native(input_handler):
    callback = MagicMock()
    hwnd = 12345
    # Mock NativeHotkeyManager to succeed
    with patch.object(input_handler.native_manager, 'register', return_value=True), \
         patch('keyboard.add_hotkey') as mock_add:
        input_handler.register_hotkey("ctrl+shift+space", callback, hwnd=hwnd)
        input_handler.native_manager.register.assert_called_once_with(hwnd, 1, "ctrl+shift+space")
        mock_add.assert_not_called()
        assert input_handler.current_hotkey == "ctrl+shift+space"
        assert input_handler.is_native_active is True
