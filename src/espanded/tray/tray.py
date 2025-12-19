"""System tray integration using pystray."""

import threading
from pathlib import Path
from typing import Callable

# pystray is optional
try:
    import pystray
    from PIL import Image
    PYSTRAY_AVAILABLE = True
except ImportError:
    pystray = None
    Image = None
    PYSTRAY_AVAILABLE = False


def create_default_icon() -> "Image.Image | None":
    """Create a simple default icon for the tray.

    Returns a 64x64 icon with the letter 'E' for Espanded.
    """
    if not PYSTRAY_AVAILABLE or Image is None:
        return None

    # Create a simple icon
    from PIL import ImageDraw, ImageFont

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw background circle
    padding = 4
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=(74, 144, 226, 255),  # Blue color
    )

    # Draw letter 'E'
    try:
        # Try to use a nice font
        font = ImageFont.truetype("arial.ttf", 36)
    except (OSError, IOError):
        # Fall back to default font
        font = ImageFont.load_default()

    # Center the text
    text = "E"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 4

    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    return img


class SystemTray:
    """System tray icon and menu for Espanded.

    Usage:
        tray = SystemTray()
        tray.set_callbacks(
            on_show=show_main_window,
            on_quick_add=show_quick_add,
            on_quit=quit_app,
        )
        tray.run()  # Blocking, runs in main thread
        # OR
        tray.run_detached()  # Non-blocking, runs in background
    """

    def __init__(self, icon_path: str | Path | None = None):
        if not PYSTRAY_AVAILABLE:
            raise ImportError(
                "pystray is required for system tray. "
                "Install with: pip install pystray pillow"
            )

        self._icon_path = icon_path
        self._icon: pystray.Icon | None = None
        self._running = False

        # Callbacks
        self._on_show: Callable[[], None] | None = None
        self._on_quick_add: Callable[[], None] | None = None
        self._on_quit: Callable[[], None] | None = None
        self._on_toggle_hotkeys: Callable[[bool], None] | None = None

        # State
        self._hotkeys_enabled = True

    def set_callbacks(
        self,
        on_show: Callable[[], None] | None = None,
        on_quick_add: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
        on_toggle_hotkeys: Callable[[bool], None] | None = None,
    ):
        """Set callback functions for menu actions.

        Args:
            on_show: Called when "Show Espanded" is clicked
            on_quick_add: Called when "Quick Add" is clicked
            on_quit: Called when "Quit" is clicked
            on_toggle_hotkeys: Called when hotkeys are toggled (receives enabled state)
        """
        self._on_show = on_show
        self._on_quick_add = on_quick_add
        self._on_quit = on_quit
        self._on_toggle_hotkeys = on_toggle_hotkeys

    def _load_icon(self) -> "Image.Image":
        """Load the tray icon image."""
        if self._icon_path and Path(self._icon_path).exists():
            return Image.open(self._icon_path)
        return create_default_icon()

    def _create_menu(self) -> "pystray.Menu":
        """Create the tray context menu."""
        return pystray.Menu(
            pystray.MenuItem(
                "Show Espanded",
                self._handle_show,
                default=True,  # Double-click action
            ),
            pystray.MenuItem(
                "Quick Add (Ctrl+Shift+E)",
                self._handle_quick_add,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Enable Hotkeys",
                self._handle_toggle_hotkeys,
                checked=lambda item: self._hotkeys_enabled,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Quit",
                self._handle_quit,
            ),
        )

    def _handle_show(self, icon=None, item=None):
        """Handle Show menu item."""
        if self._on_show:
            self._on_show()

    def _handle_quick_add(self, icon=None, item=None):
        """Handle Quick Add menu item."""
        if self._on_quick_add:
            self._on_quick_add()

    def _handle_toggle_hotkeys(self, icon=None, item=None):
        """Handle Enable Hotkeys toggle."""
        self._hotkeys_enabled = not self._hotkeys_enabled
        if self._on_toggle_hotkeys:
            self._on_toggle_hotkeys(self._hotkeys_enabled)

    def _handle_quit(self, icon=None, item=None):
        """Handle Quit menu item."""
        self.stop()
        if self._on_quit:
            self._on_quit()

    def run(self):
        """Run the system tray icon (blocking).

        This will block the current thread. Use run_detached() for non-blocking.
        """
        if self._running:
            return

        self._running = True
        icon_image = self._load_icon()

        self._icon = pystray.Icon(
            name="espanded",
            icon=icon_image,
            title="Espanded - Text Expander",
            menu=self._create_menu(),
        )

        self._icon.run()

    def run_detached(self):
        """Run the system tray icon in a background thread (non-blocking)."""
        if self._running:
            return

        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()

    def stop(self):
        """Stop the system tray icon."""
        self._running = False
        if self._icon:
            self._icon.stop()
            self._icon = None

    def update_tooltip(self, text: str):
        """Update the tray icon tooltip."""
        if self._icon:
            self._icon.title = text

    def show_notification(self, title: str, message: str):
        """Show a system notification from the tray icon.

        Note: Not all platforms support notifications.
        """
        if self._icon:
            try:
                self._icon.notify(message, title)
            except Exception:
                pass  # Notifications not supported


# Singleton instance
_tray_instance: SystemTray | None = None


def get_system_tray() -> SystemTray | None:
    """Get the global system tray instance.

    Returns:
        SystemTray instance or None if pystray is not available.
    """
    global _tray_instance

    if not PYSTRAY_AVAILABLE:
        return None

    if _tray_instance is None:
        _tray_instance = SystemTray()

    return _tray_instance
