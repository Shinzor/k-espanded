"""Hotkey service coordinating global hotkeys and quick add."""

from typing import Callable

# Check for hotkey dependencies
try:
    from espanded.hotkeys.listener import (
        HotkeyListener,
        PYNPUT_AVAILABLE,
        DEFAULT_HOTKEY,
        normalize_hotkey,
        display_hotkey,
        test_hotkey,
    )
    from espanded.hotkeys.clipboard import get_selected_text
except ImportError:
    PYNPUT_AVAILABLE = False
    HotkeyListener = None
    get_selected_text = None
    DEFAULT_HOTKEY = "<ctrl>+<alt>+`"
    normalize_hotkey = lambda x: x
    display_hotkey = lambda x: x
    test_hotkey = lambda x: (False, "pynput not available")


class HotkeyService:
    """Service coordinating global hotkeys and quick add popup.

    This service manages:
    - Global hotkey registration (Ctrl+Alt+` for quick add by default)
    - Getting selected text from clipboard
    - Triggering the quick add popup

    Usage:
        service = HotkeyService()
        service.start()
        # ... later ...
        service.stop()
    """

    # Default hotkey for quick add
    DEFAULT_QUICK_ADD_HOTKEY = DEFAULT_HOTKEY

    def __init__(self):
        self._listener: "HotkeyListener | None" = None
        self._running = False
        self._enabled = True

        # Callbacks
        self._on_quick_add: Callable[[str], None] | None = None
        self._on_show_main: Callable[[], None] | None = None

    @property
    def is_available(self) -> bool:
        """Check if hotkey functionality is available."""
        return PYNPUT_AVAILABLE

    @property
    def is_running(self) -> bool:
        """Check if the hotkey service is running."""
        return self._running

    @property
    def is_enabled(self) -> bool:
        """Check if hotkeys are enabled."""
        return self._enabled

    def set_callbacks(
        self,
        on_quick_add: Callable[[str], None] | None = None,
        on_show_main: Callable[[], None] | None = None,
    ):
        """Set callback functions.

        Args:
            on_quick_add: Called when quick add hotkey is pressed.
                          Receives the selected text as argument.
            on_show_main: Called when show main window hotkey is pressed.
        """
        self._on_quick_add = on_quick_add
        self._on_show_main = on_show_main

    def start(self, quick_add_hotkey: str | None = None):
        """Start listening for hotkeys.

        Args:
            quick_add_hotkey: Custom hotkey string (default: ctrl+shift+e)
        """
        if not PYNPUT_AVAILABLE:
            print("Hotkeys not available: pynput not installed")
            return

        if self._running:
            return

        hotkey = quick_add_hotkey or self.DEFAULT_QUICK_ADD_HOTKEY

        self._listener = HotkeyListener()
        self._listener.register(hotkey, self._handle_quick_add)
        self._listener.start()
        self._running = True

        print(f"Hotkey service started: {hotkey} for quick add")

    def stop(self):
        """Stop listening for hotkeys."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._running = False

    def update_hotkey(self, new_hotkey: str):
        """Update the hotkey by restarting the service.

        Args:
            new_hotkey: New hotkey string (e.g., '<ctrl>+<alt>+e')
        """
        was_running = self._running
        was_enabled = self._enabled

        # Stop current listener
        self.stop()

        # Start with new hotkey
        if was_running:
            self.start(new_hotkey)

        # Restore enabled state
        if not was_enabled:
            self.disable()

        print(f"Hotkey updated to: {new_hotkey}")

    def enable(self):
        """Enable hotkey handling."""
        self._enabled = True
        if not self._running:
            self.start()

    def disable(self):
        """Disable hotkey handling (listener still runs but ignores keys)."""
        self._enabled = False

    def toggle(self) -> bool:
        """Toggle hotkey handling. Returns new enabled state."""
        if self._enabled:
            self.disable()
        else:
            self.enable()
        return self._enabled

    def _handle_quick_add(self):
        """Handle the quick add hotkey press."""
        if not self._enabled:
            return

        # Get selected text
        selected_text = ""
        if get_selected_text:
            try:
                selected_text = get_selected_text()
            except Exception as e:
                print(f"Error getting selected text: {e}")

        # Trigger callback
        if self._on_quick_add:
            self._on_quick_add(selected_text)
        else:
            # Default behavior: show quick add popup
            self._show_quick_add_popup(selected_text)

    def _show_quick_add_popup(self, selected_text: str):
        """Show the quick add popup with the selected text.

        This method should not be called directly - the UI framework
        should set a callback via set_callbacks().
        """
        print(f"Quick add triggered with selected text: {selected_text[:50]}...")
        print("Note: Quick add popup requires a callback to be set via set_callbacks()")


# Singleton instance
_service_instance: HotkeyService | None = None


def get_hotkey_service() -> HotkeyService:
    """Get the global hotkey service instance."""
    global _service_instance

    if _service_instance is None:
        _service_instance = HotkeyService()

    return _service_instance
