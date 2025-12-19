"""Qt theme system with dark/light modes and color customization."""

from dataclasses import dataclass, field, asdict

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
import pyqtdarktheme

try:
    import darkdetect
except ImportError:
    darkdetect = None


@dataclass
class ColorPalette:
    """Color palette for theming - all colors customizable by user."""

    # Primary Brand Colors
    primary: str = "#3b82f6"
    primary_hover: str = "#2563eb"
    primary_muted: str = "#1e3a5f"

    # Background Colors
    bg_base: str = "#0f1419"
    bg_surface: str = "#1a1f26"
    bg_elevated: str = "#242b35"
    bg_sidebar: str = "#151a21"

    # Text Colors
    text_primary: str = "#f3f4f6"
    text_secondary: str = "#9ca3af"
    text_tertiary: str = "#6b7280"
    text_inverse: str = "#0f1419"

    # Border Colors
    border_default: str = "#2d3748"
    border_muted: str = "#1f2937"
    border_focus: str = "#3b82f6"

    # Status Colors
    success: str = "#22c55e"
    warning: str = "#f59e0b"
    error: str = "#ef4444"
    info: str = "#3b82f6"

    # Entry List
    entry_hover: str = "#1f2937"
    entry_selected: str = "#1e3a5f"

    # Tags
    tag_bg: str = "#374151"
    tag_text: str = "#e5e7eb"

    def to_dict(self) -> dict[str, str]:
        """Convert palette to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "ColorPalette":
        """Create palette from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Predefined Themes
DARK_THEME = ColorPalette(
    # Primary - Modern blue accent
    primary="#3b82f6",
    primary_hover="#2563eb",
    primary_muted="#1e3a5f",
    # Backgrounds - Rich dark with subtle elevation
    bg_base="#0f1419",
    bg_surface="#1a1f26",
    bg_elevated="#242b35",
    bg_sidebar="#151a21",
    # Text - High contrast for readability
    text_primary="#f3f4f6",
    text_secondary="#9ca3af",
    text_tertiary="#6b7280",
    text_inverse="#0f1419",
    # Borders
    border_default="#2d3748",
    border_muted="#1f2937",
    border_focus="#3b82f6",
    # Status
    success="#22c55e",
    warning="#f59e0b",
    error="#ef4444",
    info="#3b82f6",
    # Entry List
    entry_hover="#1f2937",
    entry_selected="#1e3a5f",
    # Tags
    tag_bg="#374151",
    tag_text="#e5e7eb",
)

LIGHT_THEME = ColorPalette(
    # Primary
    primary="#2563eb",
    primary_hover="#1d4ed8",
    primary_muted="#dbeafe",
    # Backgrounds
    bg_base="#ffffff",
    bg_surface="#f9fafb",
    bg_elevated="#ffffff",
    bg_sidebar="#f3f4f6",
    # Text
    text_primary="#111827",
    text_secondary="#4b5563",
    text_tertiary="#9ca3af",
    text_inverse="#ffffff",
    # Borders
    border_default="#e5e7eb",
    border_muted="#f3f4f6",
    border_focus="#2563eb",
    # Status
    success="#16a34a",
    warning="#d97706",
    error="#dc2626",
    info="#2563eb",
    # Entry List
    entry_hover="#f3f4f6",
    entry_selected="#dbeafe",
    # Tags
    tag_bg="#e5e7eb",
    tag_text="#374151",
)


@dataclass
class ThemeSettings:
    """Settings related to theming."""

    theme: str = "system"  # "light", "dark", "system"
    custom_colors: dict[str, str] = field(default_factory=dict)


def get_default_settings() -> ThemeSettings:
    """Get default theme settings."""
    return ThemeSettings()


class ThemeManager:
    """Manages Qt theme state and color overrides."""

    def __init__(self, settings: ThemeSettings | None = None):
        self.settings = settings or ThemeSettings()
        self._current_palette: ColorPalette = DARK_THEME
        self._is_dark: bool = True
        self._load_theme()

    def _load_theme(self):
        """Load theme based on settings."""
        if self.settings.theme == "light":
            base = LIGHT_THEME
            self._is_dark = False
        elif self.settings.theme == "dark":
            base = DARK_THEME
            self._is_dark = True
        else:  # system
            base, self._is_dark = self._detect_system_theme()

        # Apply user color overrides
        if self.settings.custom_colors:
            base = self._apply_overrides(base, self.settings.custom_colors)

        self._current_palette = base

    def _detect_system_theme(self) -> tuple[ColorPalette, bool]:
        """Detect OS theme preference, default to dark."""
        if darkdetect is not None:
            try:
                system_theme = darkdetect.theme()
                if system_theme and system_theme.lower() == "light":
                    return LIGHT_THEME, False
            except Exception:
                pass
        # Default to dark theme
        return DARK_THEME, True

    def _apply_overrides(
        self, base: ColorPalette, overrides: dict[str, str]
    ) -> ColorPalette:
        """Apply user color overrides to base palette."""
        palette_dict = base.to_dict()
        for key, value in overrides.items():
            if key in palette_dict:
                palette_dict[key] = value
        return ColorPalette.from_dict(palette_dict)

    @property
    def colors(self) -> ColorPalette:
        """Get current color palette."""
        return self._current_palette

    @property
    def is_dark(self) -> bool:
        """Check if current theme is dark."""
        return self._is_dark

    def set_theme(self, theme: str):
        """Set theme and reload palette."""
        self.settings.theme = theme
        self._load_theme()

    def set_custom_color(self, key: str, value: str):
        """Set a custom color override."""
        self.settings.custom_colors[key] = value
        self._load_theme()

    def reset_custom_colors(self):
        """Reset all custom color overrides."""
        self.settings.custom_colors.clear()
        self._load_theme()

    def apply_to_app(self, app: QApplication):
        """Apply theme colors to Qt application."""
        # Use pyqtdarktheme as base, then customize with our colors
        if self._is_dark:
            pyqtdarktheme.setup_theme("dark")
        else:
            pyqtdarktheme.setup_theme("light")

        # Apply custom stylesheet for our specific colors
        app.setStyleSheet(self._generate_stylesheet())

    def _generate_stylesheet(self) -> str:
        """Generate Qt stylesheet from color palette."""
        colors = self._current_palette

        return f"""
            /* Main Window and Base Colors */
            QMainWindow {{
                background-color: {colors.bg_base};
                color: {colors.text_primary};
            }}

            QWidget {{
                background-color: {colors.bg_base};
                color: {colors.text_primary};
            }}

            /* Containers and Panels */
            QFrame {{
                background-color: {colors.bg_surface};
                border: 1px solid {colors.border_muted};
                border-radius: 4px;
            }}

            /* Text Input */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 6px;
                selection-background-color: {colors.primary};
                selection-color: {colors.text_inverse};
            }}

            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid {colors.border_focus};
            }}

            /* Buttons */
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}

            QPushButton:pressed {{
                background-color: {colors.primary_muted};
            }}

            QPushButton:disabled {{
                background-color: {colors.border_muted};
                color: {colors.text_tertiary};
            }}

            /* Secondary Buttons */
            QPushButton[secondary="true"] {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
            }}

            QPushButton[secondary="true"]:hover {{
                background-color: {colors.bg_surface};
                border-color: {colors.primary};
            }}

            /* List Widgets */
            QListWidget, QTreeWidget, QTableWidget {{
                background-color: {colors.bg_surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                outline: none;
            }}

            QListWidget::item, QTreeWidget::item, QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {colors.border_muted};
            }}

            QListWidget::item:hover, QTreeWidget::item:hover, QTableWidget::item:hover {{
                background-color: {colors.entry_hover};
            }}

            QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {{
                background-color: {colors.entry_selected};
                color: {colors.text_primary};
            }}

            /* ComboBox */
            QComboBox {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 6px;
            }}

            QComboBox:focus {{
                border: 1px solid {colors.border_focus};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                selection-background-color: {colors.entry_selected};
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors.bg_surface};
                width: 12px;
                border: none;
            }}

            QScrollBar::handle:vertical {{
                background-color: {colors.border_default};
                border-radius: 6px;
                min-height: 20px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {colors.text_tertiary};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar:horizontal {{
                background-color: {colors.bg_surface};
                height: 12px;
                border: none;
            }}

            QScrollBar::handle:horizontal {{
                background-color: {colors.border_default};
                border-radius: 6px;
                min-width: 20px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: {colors.text_tertiary};
            }}

            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}

            /* Labels */
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}

            QLabel[secondary="true"] {{
                color: {colors.text_secondary};
            }}

            QLabel[tertiary="true"] {{
                color: {colors.text_tertiary};
            }}

            /* Checkboxes and Radio Buttons */
            QCheckBox, QRadioButton {{
                color: {colors.text_primary};
                spacing: 8px;
            }}

            QCheckBox::indicator, QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {colors.border_default};
                border-radius: 3px;
                background-color: {colors.bg_elevated};
            }}

            QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
                background-color: {colors.primary};
                border-color: {colors.primary};
            }}

            /* Menu Bar */
            QMenuBar {{
                background-color: {colors.bg_surface};
                color: {colors.text_primary};
                border-bottom: 1px solid {colors.border_muted};
            }}

            QMenuBar::item:selected {{
                background-color: {colors.entry_hover};
            }}

            QMenu {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
            }}

            QMenu::item:selected {{
                background-color: {colors.entry_selected};
            }}

            /* Status Bar */
            QStatusBar {{
                background-color: {colors.bg_surface};
                color: {colors.text_secondary};
                border-top: 1px solid {colors.border_muted};
            }}

            /* Tab Widget */
            QTabWidget::pane {{
                background-color: {colors.bg_surface};
                border: 1px solid {colors.border_default};
            }}

            QTabBar::tab {{
                background-color: {colors.bg_elevated};
                color: {colors.text_secondary};
                padding: 8px 16px;
                border: 1px solid {colors.border_muted};
                border-bottom: none;
            }}

            QTabBar::tab:selected {{
                background-color: {colors.bg_surface};
                color: {colors.text_primary};
                border-bottom: 2px solid {colors.primary};
            }}

            QTabBar::tab:hover {{
                background-color: {colors.entry_hover};
            }}

            /* Tooltips */
            QToolTip {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                padding: 4px;
            }}

            /* Splitter */
            QSplitter::handle {{
                background-color: {colors.border_muted};
            }}

            QSplitter::handle:hover {{
                background-color: {colors.border_default};
            }}
        """

    def get_color(self, color_name: str) -> QColor:
        """Get QColor object for a named color from the palette."""
        color_value = getattr(self._current_palette, color_name, "#000000")
        return QColor(color_value)
