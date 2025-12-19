"""UI components for Espanded."""

from espanded.ui.theme import ThemeManager, ColorPalette, ThemeSettings
from espanded.ui.main_window import MainWindow
from espanded.ui.sidebar import Sidebar
from espanded.ui.dashboard import Dashboard
from espanded.ui.entry_editor import EntryEditor
from espanded.ui.settings_view import SettingsView
from espanded.ui.history_view import HistoryView
from espanded.ui.trash_view import TrashView
from espanded.ui.quick_add import QuickAddPopup
from espanded.ui.system_tray import SystemTray

__all__ = [
    "ThemeManager",
    "ColorPalette",
    "ThemeSettings",
    "MainWindow",
    "Sidebar",
    "Dashboard",
    "EntryEditor",
    "SettingsView",
    "HistoryView",
    "TrashView",
    "QuickAddPopup",
    "SystemTray",
]
