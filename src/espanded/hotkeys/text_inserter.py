"""Text insertion for autocomplete - replaces trigger text with expansion.

This module handles the mechanics of:
1. Deleting the typed trigger + filter text
2. Inserting the replacement text

It uses a combination of simulated keypresses and clipboard operations.
"""

import logging
import platform
import time
import threading
from typing import Callable

logger = logging.getLogger(__name__)


class TextInserter:
    """Handles text insertion after autocomplete selection.

    Uses keyboard simulation to delete typed text and insert replacement.
    Falls back to clipboard-based insertion for longer text.
    """

    # Threshold for using clipboard vs typing (characters)
    CLIPBOARD_THRESHOLD = 50

    def __init__(self):
        """Initialize the text inserter."""
        self._keyboard = None
        self._controller = None
        self._init_keyboard()

    def _init_keyboard(self):
        """Initialize the keyboard controller."""
        try:
            from pynput.keyboard import Controller, Key

            self._controller = Controller()
            self._Key = Key
            logger.debug("pynput keyboard controller initialized")
        except ImportError:
            logger.warning("pynput not available - text insertion will be limited")

    def insert_replacement(
        self,
        chars_to_delete: int,
        replacement: str,
        on_complete: Callable[[], None] | None = None,
    ):
        """Replace typed text with the expansion replacement.

        Args:
            chars_to_delete: Number of characters to delete (trigger + filter)
            replacement: The replacement text to insert
            on_complete: Optional callback when insertion is complete
        """
        if not self._controller:
            logger.error("Keyboard controller not available")
            return

        # Run insertion in a separate thread to avoid blocking
        def do_insert():
            try:
                # Small delay to ensure popup is hidden and focus is back
                time.sleep(0.05)

                # Delete the typed characters
                self._delete_chars(chars_to_delete)

                # Small delay between delete and insert
                time.sleep(0.02)

                # Insert the replacement
                if len(replacement) > self.CLIPBOARD_THRESHOLD:
                    self._insert_via_clipboard(replacement)
                else:
                    self._insert_via_typing(replacement)

                if on_complete:
                    on_complete()

            except Exception as e:
                logger.error(f"Error inserting text: {e}")

        thread = threading.Thread(target=do_insert, daemon=True)
        thread.start()

    def _delete_chars(self, count: int):
        """Delete characters using backspace.

        Args:
            count: Number of characters to delete
        """
        if not self._controller:
            return

        logger.debug(f"Deleting {count} characters")

        for _ in range(count):
            self._controller.press(self._Key.backspace)
            self._controller.release(self._Key.backspace)
            time.sleep(0.005)  # Small delay between keypresses

    def _insert_via_typing(self, text: str):
        """Insert text by simulating keypresses.

        Args:
            text: Text to insert
        """
        if not self._controller:
            return

        logger.debug(f"Typing {len(text)} characters")

        # Handle special characters and newlines
        for char in text:
            if char == "\n":
                self._controller.press(self._Key.enter)
                self._controller.release(self._Key.enter)
            elif char == "\t":
                self._controller.press(self._Key.tab)
                self._controller.release(self._Key.tab)
            else:
                self._controller.type(char)

            time.sleep(0.002)  # Small delay for reliability

    def _insert_via_clipboard(self, text: str):
        """Insert text via clipboard paste.

        This is faster for longer text and handles special characters better.

        Args:
            text: Text to insert
        """
        logger.debug(f"Pasting {len(text)} characters via clipboard")

        try:
            # Save current clipboard content
            old_clipboard = self._get_clipboard()

            # Set new clipboard content
            self._set_clipboard(text)

            # Small delay for clipboard to update
            time.sleep(0.02)

            # Simulate Ctrl+V / Cmd+V
            self._paste()

            # Small delay before restoring clipboard
            time.sleep(0.05)

            # Restore old clipboard content
            if old_clipboard:
                self._set_clipboard(old_clipboard)

        except Exception as e:
            logger.error(f"Clipboard paste failed: {e}")
            # Fall back to typing
            self._insert_via_typing(text)

    def _paste(self):
        """Simulate paste keystroke (Ctrl+V or Cmd+V)."""
        if not self._controller:
            return

        system = platform.system()

        if system == "Darwin":
            # macOS: Cmd+V
            self._controller.press(self._Key.cmd)
            self._controller.press("v")
            self._controller.release("v")
            self._controller.release(self._Key.cmd)
        else:
            # Windows/Linux: Ctrl+V
            self._controller.press(self._Key.ctrl)
            self._controller.press("v")
            self._controller.release("v")
            self._controller.release(self._Key.ctrl)

    def _get_clipboard(self) -> str | None:
        """Get current clipboard content.

        Returns:
            Clipboard text content, or None if unavailable
        """
        try:
            # Try Qt first (most reliable in our context)
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QMimeData

            clipboard = QApplication.clipboard()
            if clipboard:
                return clipboard.text()
        except Exception:
            pass

        # Platform-specific fallbacks
        system = platform.system()

        if system == "Windows":
            try:
                import ctypes

                CF_UNICODETEXT = 13

                ctypes.windll.user32.OpenClipboard(0)
                try:
                    if ctypes.windll.user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
                        handle = ctypes.windll.user32.GetClipboardData(CF_UNICODETEXT)
                        if handle:
                            ctypes.windll.kernel32.GlobalLock.restype = ctypes.c_wchar_p
                            data = ctypes.windll.kernel32.GlobalLock(handle)
                            if data:
                                text = str(data)
                                ctypes.windll.kernel32.GlobalUnlock(handle)
                                return text
                finally:
                    ctypes.windll.user32.CloseClipboard()
            except Exception as e:
                logger.debug(f"Win32 clipboard read failed: {e}")

        return None

    def _set_clipboard(self, text: str):
        """Set clipboard content.

        Args:
            text: Text to put on clipboard
        """
        try:
            # Try Qt first (most reliable in our context)
            from PySide6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text)
                return
        except Exception:
            pass

        # Platform-specific fallbacks
        system = platform.system()

        if system == "Windows":
            try:
                import ctypes
                from ctypes import wintypes

                CF_UNICODETEXT = 13
                GMEM_MOVEABLE = 0x0002

                # Open clipboard
                ctypes.windll.user32.OpenClipboard(0)
                try:
                    ctypes.windll.user32.EmptyClipboard()

                    # Allocate global memory
                    text_bytes = (text + "\0").encode("utf-16-le")
                    handle = ctypes.windll.kernel32.GlobalAlloc(
                        GMEM_MOVEABLE, len(text_bytes)
                    )
                    if handle:
                        locked = ctypes.windll.kernel32.GlobalLock(handle)
                        if locked:
                            ctypes.memmove(locked, text_bytes, len(text_bytes))
                            ctypes.windll.kernel32.GlobalUnlock(handle)
                            ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, handle)
                finally:
                    ctypes.windll.user32.CloseClipboard()
            except Exception as e:
                logger.debug(f"Win32 clipboard write failed: {e}")

        elif system == "Darwin":
            try:
                import subprocess

                process = subprocess.Popen(
                    ["pbcopy"], stdin=subprocess.PIPE, text=True
                )
                process.communicate(text)
            except Exception as e:
                logger.debug(f"macOS clipboard write failed: {e}")

        elif system == "Linux":
            try:
                import subprocess

                # Try xclip first, then xsel
                for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                    try:
                        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
                        process.communicate(text)
                        return
                    except FileNotFoundError:
                        continue
            except Exception as e:
                logger.debug(f"Linux clipboard write failed: {e}")
