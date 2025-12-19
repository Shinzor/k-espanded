"""Global hotkey listener using pynput GlobalHotKeys."""

import threading
from typing import Callable

# pynput is required
try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    keyboard = None
    Key = None
    KeyCode = None


# Default hotkey
DEFAULT_HOTKEY = "<ctrl>+<alt>+`"


def normalize_hotkey(hotkey_string: str) -> str:
    """Normalize hotkey string to pynput format.

    Converts various formats to pynput's angle bracket format:
    - ctrl+alt+e -> <ctrl>+<alt>+e
    - CTRL+ALT+E -> <ctrl>+<alt>+e
    - <ctrl>+<alt>+e -> <ctrl>+<alt>+e (already correct)

    Args:
        hotkey_string: Hotkey string in any format

    Returns:
        Normalized hotkey string for pynput
    """
    if not hotkey_string:
        return DEFAULT_HOTKEY

    # Convert to lowercase
    hotkey = hotkey_string.lower().strip()

    # Split by +
    parts = hotkey.split("+")
    normalized = []

    # Modifier mapping
    modifiers = {
        "ctrl": "<ctrl>",
        "control": "<ctrl>",
        "<ctrl>": "<ctrl>",
        "alt": "<alt>",
        "<alt>": "<alt>",
        "shift": "<shift>",
        "<shift>": "<shift>",
        "meta": "<cmd>",
        "cmd": "<cmd>",
        "command": "<cmd>",
        "win": "<cmd>",
        "<cmd>": "<cmd>",
        "<meta>": "<cmd>",
    }

    # Special key mapping
    special_keys = {
        "space": "<space>",
        "<space>": "<space>",
        "enter": "<enter>",
        "<enter>": "<enter>",
        "tab": "<tab>",
        "<tab>": "<tab>",
        "escape": "<esc>",
        "esc": "<esc>",
        "<esc>": "<esc>",
        "backspace": "<backspace>",
        "<backspace>": "<backspace>",
        "delete": "<delete>",
        "<delete>": "<delete>",
        "`": "`",
        "backtick": "`",
    }

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if part in modifiers:
            normalized.append(modifiers[part])
        elif part in special_keys:
            normalized.append(special_keys[part])
        elif part.startswith("<") and part.endswith(">"):
            # Already in angle bracket format
            normalized.append(part)
        elif len(part) == 1:
            # Single character key
            normalized.append(part)
        elif part.startswith("f") and part[1:].isdigit():
            # Function key like f1, f2
            normalized.append(f"<{part}>")
        else:
            # Unknown - wrap in angle brackets if it looks like a special key
            normalized.append(part)

    return "+".join(normalized)


def display_hotkey(hotkey_string: str) -> str:
    """Convert pynput hotkey format to display format.

    Converts: <ctrl>+<alt>+` -> Ctrl + Alt + `
    """
    if not hotkey_string:
        return "Not set"

    # Replace angle brackets and format nicely
    display = hotkey_string.replace("<", "").replace(">", "")
    parts = display.split("+")
    formatted = []
    for p in parts:
        p = p.strip()
        if p:
            formatted.append(p.capitalize() if len(p) > 1 else p)
    return " + ".join(formatted)


class HotkeyListener:
    """Global hotkey listener using pynput GlobalHotKeys.

    Uses the recommended GlobalHotKeys class for reliable hotkey detection.

    Usage:
        listener = HotkeyListener()
        listener.register("<ctrl>+<alt>+e", on_quick_add)
        listener.start()
        # ... later ...
        listener.stop()
    """

    def __init__(self):
        if not PYNPUT_AVAILABLE:
            raise ImportError(
                "pynput is required for global hotkeys. "
                "Install with: pip install pynput"
            )

        self._hotkeys: dict[str, Callable] = {}
        self._listener = None
        self._running = False
        self._enabled = True

    def register(self, hotkey_string: str, callback: Callable):
        """Register a hotkey callback.

        Args:
            hotkey_string: Hotkey string in pynput format (e.g., '<ctrl>+<alt>+e')
            callback: Function to call when hotkey is pressed
        """
        normalized = normalize_hotkey(hotkey_string)
        self._hotkeys[normalized] = callback

        # If already running, restart to pick up new hotkey
        if self._running:
            self._restart()

    def unregister(self, hotkey_string: str):
        """Unregister a hotkey."""
        normalized = normalize_hotkey(hotkey_string)
        if normalized in self._hotkeys:
            del self._hotkeys[normalized]
            if self._running:
                self._restart()

    def start(self):
        """Start listening for hotkeys."""
        if self._running or not self._hotkeys:
            return

        self._create_listener()
        self._running = True

    def stop(self):
        """Stop listening for hotkeys."""
        self._running = False
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _restart(self):
        """Restart the listener with updated hotkeys."""
        self.stop()
        if self._hotkeys:
            self.start()

    def _create_listener(self):
        """Create the GlobalHotKeys listener."""
        if not self._hotkeys:
            return

        # Create wrapper callbacks that check enabled state
        def make_callback(cb):
            def wrapper():
                if self._enabled:
                    # Run in separate thread to not block
                    try:
                        threading.Thread(target=cb, daemon=True).start()
                    except Exception as e:
                        print(f"Error in hotkey callback: {e}")
            return wrapper

        hotkey_map = {k: make_callback(v) for k, v in self._hotkeys.items()}

        try:
            self._listener = keyboard.GlobalHotKeys(hotkey_map)
            self._listener.start()
            print(f"GlobalHotKeys listener started successfully with {len(hotkey_map)} hotkey(s)")
        except PermissionError as e:
            print(f"Permission error starting hotkey listener: {e}")
            print("TIP: On Windows, try running as Administrator")
            self._listener = None
        except Exception as e:
            print(f"Error starting hotkey listener: {e}")
            import traceback
            traceback.print_exc()
            print("TIP: Try using a different hotkey (e.g., <ctrl>+<alt>+e instead of backtick)")
            self._listener = None

    def enable(self):
        """Enable hotkey handling."""
        self._enabled = True

    def disable(self):
        """Disable hotkey handling (listener still runs but ignores keys)."""
        self._enabled = False

    def toggle(self) -> bool:
        """Toggle hotkey handling. Returns new enabled state."""
        self._enabled = not self._enabled
        return self._enabled

    @property
    def is_enabled(self) -> bool:
        """Check if hotkeys are enabled."""
        return self._enabled

    @property
    def is_running(self) -> bool:
        """Check if listener is running."""
        return self._running


def test_hotkey(hotkey_string: str) -> tuple[bool, str]:
    """Test if a hotkey can be registered.

    Args:
        hotkey_string: Hotkey to test

    Returns:
        Tuple of (success, message)
    """
    if not PYNPUT_AVAILABLE:
        return False, "pynput not available"

    normalized = normalize_hotkey(hotkey_string)

    try:
        # Try to parse the hotkey
        keyboard.HotKey.parse(normalized)
        return True, f"Hotkey '{display_hotkey(normalized)}' is valid"
    except Exception as e:
        return False, f"Invalid hotkey: {str(e)}"


# Singleton instance
_listener_instance: HotkeyListener | None = None


def get_hotkey_listener() -> HotkeyListener | None:
    """Get the global hotkey listener instance.

    Returns:
        HotkeyListener instance or None if pynput is not available.
    """
    global _listener_instance

    if not PYNPUT_AVAILABLE:
        return None

    if _listener_instance is None:
        _listener_instance = HotkeyListener()

    return _listener_instance
