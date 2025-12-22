"""Cursor position detection for showing autocomplete popups.

This module attempts to get the text caret (insertion point) position
in the currently focused application. Since this is notoriously difficult
to do reliably across all applications, it uses multiple strategies:

1. Windows: GetGUIThreadInfo API to get caret position
2. Fallback: Use mouse cursor position (less accurate but always works)
"""

import logging
import platform
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CursorPosition:
    """Screen position for the cursor/caret."""

    x: int
    y: int
    is_caret: bool = False  # True if this is actual caret position, False if fallback

    def offset(self, dx: int = 0, dy: int = 0) -> "CursorPosition":
        """Return a new position offset from this one."""
        return CursorPosition(self.x + dx, self.y + dy, self.is_caret)


def get_cursor_position() -> CursorPosition:
    """Get the current cursor/caret position.

    Attempts to get the text caret position first, falls back to mouse position.

    Returns:
        CursorPosition with screen coordinates
    """
    system = platform.system()

    if system == "Windows":
        pos = _get_windows_caret_position()
        if pos:
            return pos

    # Fallback to mouse position
    return _get_mouse_position()


def _get_windows_caret_position() -> CursorPosition | None:
    """Get caret position on Windows using Win32 API.

    Returns:
        CursorPosition if successful, None otherwise
    """
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        # Define GUITHREADINFO structure
        class GUITHREADINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("hwndActive", wintypes.HWND),
                ("hwndFocus", wintypes.HWND),
                ("hwndCapture", wintypes.HWND),
                ("hwndMenuOwner", wintypes.HWND),
                ("hwndMoveSize", wintypes.HWND),
                ("hwndCaret", wintypes.HWND),
                ("rcCaret", wintypes.RECT),
            ]

        # Get GUI thread info for foreground thread (0 = current foreground)
        gui_info = GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)

        if not user32.GetGUIThreadInfo(0, ctypes.byref(gui_info)):
            logger.debug("GetGUIThreadInfo failed")
            return None

        # Check if we have a caret window
        if not gui_info.hwndCaret:
            logger.debug("No caret window found")
            return None

        # Get caret position (bottom-left of caret for popup positioning)
        point = wintypes.POINT()
        point.x = gui_info.rcCaret.left
        point.y = gui_info.rcCaret.bottom

        # Convert client coordinates to screen coordinates
        if not user32.ClientToScreen(gui_info.hwndCaret, ctypes.byref(point)):
            logger.debug("ClientToScreen failed")
            return None

        logger.debug(f"Got caret position: ({point.x}, {point.y})")
        return CursorPosition(point.x, point.y, is_caret=True)

    except Exception as e:
        logger.debug(f"Windows caret detection failed: {e}")
        return None


def _get_mouse_position() -> CursorPosition:
    """Get mouse cursor position as fallback.

    Returns:
        CursorPosition with mouse coordinates
    """
    try:
        # Try using Qt if available (more reliable cross-platform)
        from PySide6.QtGui import QCursor

        pos = QCursor.pos()
        logger.debug(f"Using mouse position (Qt): ({pos.x()}, {pos.y()})")
        return CursorPosition(pos.x(), pos.y(), is_caret=False)
    except ImportError:
        pass

    # Fallback to platform-specific methods
    system = platform.system()

    if system == "Windows":
        try:
            import ctypes
            from ctypes import wintypes

            class POINT(ctypes.Structure):
                _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

            point = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            logger.debug(f"Using mouse position (Win32): ({point.x}, {point.y})")
            return CursorPosition(point.x, point.y, is_caret=False)
        except Exception as e:
            logger.debug(f"Win32 mouse position failed: {e}")

    elif system == "Darwin":
        try:
            from Quartz import CGEventGetLocation, CGEventCreate

            event = CGEventCreate(None)
            pos = CGEventGetLocation(event)
            logger.debug(f"Using mouse position (macOS): ({pos.x}, {pos.y})")
            return CursorPosition(int(pos.x), int(pos.y), is_caret=False)
        except Exception as e:
            logger.debug(f"macOS mouse position failed: {e}")

    elif system == "Linux":
        try:
            from Xlib import display

            d = display.Display()
            data = d.screen().root.query_pointer()._data
            logger.debug(f"Using mouse position (X11): ({data['root_x']}, {data['root_y']})")
            return CursorPosition(data["root_x"], data["root_y"], is_caret=False)
        except Exception as e:
            logger.debug(f"X11 mouse position failed: {e}")

    # Ultimate fallback - center of screen
    logger.warning("Could not get cursor position, using screen center")
    return CursorPosition(500, 500, is_caret=False)


def get_active_window_info() -> dict | None:
    """Get information about the currently active window.

    Returns:
        Dict with 'title', 'process', etc. or None if unavailable
    """
    system = platform.system()

    if system == "Windows":
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32

            # Get foreground window
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            # Get window title
            length = user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)

            return {
                "hwnd": hwnd,
                "title": buffer.value,
            }
        except Exception as e:
            logger.debug(f"Could not get window info: {e}")
            return None

    return None
