"""Global hotkey and clipboard functionality."""

from espanded.hotkeys.clipboard import ClipboardManager, get_selected_text
from espanded.hotkeys.listener import (
    HotkeyListener,
    KeystrokeMonitor,
    get_hotkey_listener,
    get_keystroke_monitor,
    normalize_hotkey,
    display_hotkey,
)
from espanded.hotkeys.keystroke_buffer import KeystrokeBuffer, TriggerMatch
from espanded.hotkeys.cursor_position import get_cursor_position, CursorPosition
from espanded.hotkeys.text_inserter import TextInserter

__all__ = [
    "ClipboardManager",
    "get_selected_text",
    "HotkeyListener",
    "KeystrokeMonitor",
    "get_hotkey_listener",
    "get_keystroke_monitor",
    "normalize_hotkey",
    "display_hotkey",
    "KeystrokeBuffer",
    "TriggerMatch",
    "get_cursor_position",
    "CursorPosition",
    "TextInserter",
]
