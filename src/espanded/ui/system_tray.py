"""Qt-based system tray integration."""

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QObject, Signal

from espanded.ui.theme import ThemeManager
from espanded.ui.icon import create_app_icon


def create_default_icon(size: int = 64) -> QPixmap:
    """Create a simple default icon for the tray.

    Returns a pixmap with the letter 'E' for Espanded.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw background circle
    padding = 4
    painter.setBrush(QColor(74, 144, 226))  # Blue color
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(padding, padding, size - 2 * padding, size - 2 * padding)

    # Draw letter 'E'
    painter.setPen(QColor(255, 255, 255))
    font = painter.font()
    font.setPixelSize(int(size * 0.6))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "E")

    painter.end()
    return pixmap


class SystemTray(QObject):
    """Qt-based system tray icon and menu for Espanded.

    Provides system tray integration with menu items for:
    - Show/Hide main window
    - Quick Add
    - Toggle Hotkeys
    - Quit

    Usage:
        tray = SystemTray(theme_manager)
        tray.set_callbacks(
            on_show=show_main_window,
            on_quick_add=show_quick_add,
            on_quit=quit_app,
        )
        tray.show()
    """

    # Signals
    show_requested = Signal()
    quick_add_requested = Signal()
    hotkeys_toggled = Signal(bool)
    quit_requested = Signal()

    def __init__(self, theme_manager: ThemeManager, icon_path: str | Path | None = None):
        super().__init__()
        self.theme_manager = theme_manager
        self._icon_path = icon_path

        # State
        self._hotkeys_enabled = True

        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setToolTip("Espanded - Text Expander")

        # Set icon
        self._load_icon()

        # Create menu
        self._create_menu()

        # Connect signals
        self.tray_icon.activated.connect(self._on_activated)

    def _load_icon(self):
        """Load the tray icon image."""
        if self._icon_path and Path(self._icon_path).exists():
            icon = QIcon(str(self._icon_path))
        else:
            # Use app icon
            icon = create_app_icon()

        self.tray_icon.setIcon(icon)

    def _create_menu(self):
        """Create the tray context menu."""
        menu = QMenu()

        # Show Espanded (default action)
        self.show_action = QAction("Show Espanded", menu)
        self.show_action.triggered.connect(self._on_show)
        menu.addAction(self.show_action)

        # Quick Add
        self.quick_add_action = QAction("Quick Add (Ctrl+Alt+`)", menu)
        self.quick_add_action.triggered.connect(self._on_quick_add)
        menu.addAction(self.quick_add_action)

        menu.addSeparator()

        # Toggle Hotkeys (checkable)
        self.hotkeys_action = QAction("Enable Hotkeys", menu)
        self.hotkeys_action.setCheckable(True)
        self.hotkeys_action.setChecked(self._hotkeys_enabled)
        self.hotkeys_action.triggered.connect(self._on_toggle_hotkeys)
        menu.addAction(self.hotkeys_action)

        menu.addSeparator()

        # Quit
        self.quit_action = QAction("Quit", menu)
        self.quit_action.triggered.connect(self._on_quit)
        menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(menu)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Handle tray icon activation (click)."""
        # Left-click or double-click shows main window
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._on_show()

    def _on_show(self):
        """Handle Show menu item."""
        self.show_requested.emit()

    def _on_quick_add(self):
        """Handle Quick Add menu item."""
        self.quick_add_requested.emit()

    def _on_toggle_hotkeys(self):
        """Handle Toggle Hotkeys menu item."""
        self._hotkeys_enabled = self.hotkeys_action.isChecked()
        self.hotkeys_toggled.emit(self._hotkeys_enabled)

    def _on_quit(self):
        """Handle Quit menu item."""
        self.quit_requested.emit()

    def show(self):
        """Show the system tray icon."""
        self.tray_icon.show()

    def hide(self):
        """Hide the system tray icon."""
        self.tray_icon.hide()

    def set_hotkeys_enabled(self, enabled: bool):
        """Update the hotkeys enabled state in the menu."""
        self._hotkeys_enabled = enabled
        self.hotkeys_action.setChecked(enabled)

    def update_tooltip(self, text: str):
        """Update the tray icon tooltip."""
        self.tray_icon.setToolTip(text)

    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Show a system notification from the tray icon.

        Args:
            title: Notification title
            message: Notification message
            duration: Duration in milliseconds (default: 3000)
        """
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, duration)

    def is_visible(self) -> bool:
        """Check if tray icon is visible."""
        return self.tray_icon.isVisible()

    def cleanup(self):
        """Clean up tray icon."""
        self.tray_icon.hide()
