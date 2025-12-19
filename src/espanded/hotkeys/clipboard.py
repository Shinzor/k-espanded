"""Clipboard operations for getting selected text."""

import platform
import subprocess
import time
from typing import Callable


class ClipboardManager:
    """Cross-platform clipboard operations."""

    def __init__(self):
        self._system = platform.system()

    def get_clipboard(self) -> str:
        """Get current clipboard content."""
        try:
            if self._system == "Windows":
                return self._get_clipboard_windows()
            elif self._system == "Darwin":
                return self._get_clipboard_macos()
            else:
                return self._get_clipboard_linux()
        except Exception:
            return ""

    def set_clipboard(self, text: str):
        """Set clipboard content."""
        try:
            if self._system == "Windows":
                self._set_clipboard_windows(text)
            elif self._system == "Darwin":
                self._set_clipboard_macos(text)
            else:
                self._set_clipboard_linux(text)
        except Exception:
            pass

    def _get_clipboard_windows(self) -> str:
        """Get clipboard on Windows using PowerShell."""
        result = subprocess.run(
            ["powershell.exe", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    def _set_clipboard_windows(self, text: str):
        """Set clipboard on Windows using PowerShell."""
        # Escape special characters for PowerShell
        escaped = text.replace("'", "''")
        subprocess.run(
            ["powershell.exe", "-Command", f"Set-Clipboard -Value '{escaped}'"],
            capture_output=True,
            timeout=5,
        )

    def _get_clipboard_macos(self) -> str:
        """Get clipboard on macOS using pbpaste."""
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout if result.returncode == 0 else ""

    def _set_clipboard_macos(self, text: str):
        """Set clipboard on macOS using pbcopy."""
        subprocess.run(
            ["pbcopy"],
            input=text,
            text=True,
            timeout=5,
        )

    def _get_clipboard_linux(self) -> str:
        """Get clipboard on Linux using xclip or xsel."""
        # Try xclip first
        try:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout
        except FileNotFoundError:
            pass

        # Fall back to xsel
        try:
            result = subprocess.run(
                ["xsel", "--clipboard", "--output"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout
        except FileNotFoundError:
            pass

        return ""

    def _set_clipboard_linux(self, text: str):
        """Set clipboard on Linux using xclip or xsel."""
        # Try xclip first
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text,
                text=True,
                timeout=5,
            )
            return
        except FileNotFoundError:
            pass

        # Fall back to xsel
        try:
            subprocess.run(
                ["xsel", "--clipboard", "--input"],
                input=text,
                text=True,
                timeout=5,
            )
        except FileNotFoundError:
            pass


def get_selected_text() -> str:
    """Get currently selected text by simulating Ctrl+C.

    This temporarily modifies the clipboard, copies the selection,
    reads the clipboard, and restores the original content.
    """
    clipboard = ClipboardManager()
    system = platform.system()

    # Save current clipboard
    original = clipboard.get_clipboard()

    # Clear clipboard
    clipboard.set_clipboard("")

    # Simulate Ctrl+C to copy selection
    try:
        if system == "Windows":
            _simulate_copy_windows()
        elif system == "Darwin":
            _simulate_copy_macos()
        else:
            _simulate_copy_linux()
    except Exception:
        # Restore and return empty
        clipboard.set_clipboard(original)
        return ""

    # Small delay for clipboard to update
    time.sleep(0.1)

    # Get the copied text
    selected = clipboard.get_clipboard()

    # Restore original clipboard
    clipboard.set_clipboard(original)

    return selected


def _simulate_copy_windows():
    """Simulate Ctrl+C on Windows."""
    try:
        # Try using pynput if available
        from pynput.keyboard import Controller, Key
        keyboard = Controller()
        keyboard.press(Key.ctrl)
        keyboard.press('c')
        keyboard.release('c')
        keyboard.release(Key.ctrl)
    except ImportError:
        # Fall back to PowerShell
        subprocess.run(
            ["powershell.exe", "-Command",
             "[System.Windows.Forms.SendKeys]::SendWait('^c')"],
            capture_output=True,
            timeout=5,
        )


def _simulate_copy_macos():
    """Simulate Cmd+C on macOS."""
    try:
        from pynput.keyboard import Controller, Key
        keyboard = Controller()
        keyboard.press(Key.cmd)
        keyboard.press('c')
        keyboard.release('c')
        keyboard.release(Key.cmd)
    except ImportError:
        subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to keystroke "c" using command down'],
            capture_output=True,
            timeout=5,
        )


def _simulate_copy_linux():
    """Simulate Ctrl+C on Linux."""
    try:
        from pynput.keyboard import Controller, Key
        keyboard = Controller()
        keyboard.press(Key.ctrl)
        keyboard.press('c')
        keyboard.release('c')
        keyboard.release(Key.ctrl)
    except ImportError:
        # Try xdotool
        subprocess.run(
            ["xdotool", "key", "ctrl+c"],
            capture_output=True,
            timeout=5,
        )
