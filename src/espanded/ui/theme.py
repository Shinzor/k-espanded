"""Qt theme system with dark/light modes and color customization."""

from dataclasses import dataclass, field, asdict

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

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
        # Apply our comprehensive stylesheet
        app.setStyleSheet(self._generate_stylesheet())

    def _generate_stylesheet(self) -> str:
        """Generate Qt stylesheet from color palette."""
        c = self._current_palette

        return f"""
            /* ========================================
               GLOBAL RESETS & BASE STYLES
               ======================================== */

            * {{
                font-family: "Segoe UI", "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
            }}

            QWidget {{
                background-color: transparent;
                color: {c.text_primary};
                border: none;
            }}

            QMainWindow {{
                background-color: {c.bg_base};
            }}

            /* ========================================
               SCROLL AREAS
               ======================================== */

            QScrollArea {{
                background-color: transparent;
                border: none;
            }}

            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                margin: 0;
            }}

            QScrollBar::handle:vertical {{
                background-color: {c.border_default};
                border-radius: 4px;
                min-height: 30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {c.text_tertiary};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
                height: 0;
                border: none;
            }}

            QScrollBar:horizontal {{
                background-color: transparent;
                height: 8px;
                margin: 0;
            }}

            QScrollBar::handle:horizontal {{
                background-color: {c.border_default};
                border-radius: 4px;
                min-width: 30px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: {c.text_tertiary};
            }}

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: transparent;
                width: 0;
                border: none;
            }}

            /* ========================================
               TEXT INPUTS
               ======================================== */

            QLineEdit {{
                background-color: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 6px;
                padding: 8px 12px;
                selection-background-color: {c.primary};
                selection-color: {c.text_inverse};
            }}

            QLineEdit:focus {{
                border-color: {c.primary};
            }}

            QLineEdit:disabled {{
                background-color: {c.bg_surface};
                color: {c.text_tertiary};
            }}

            QTextEdit, QPlainTextEdit {{
                background-color: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 6px;
                padding: 8px;
                selection-background-color: {c.primary};
                selection-color: {c.text_inverse};
            }}

            QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {c.primary};
            }}

            /* ========================================
               BUTTONS
               ======================================== */

            QPushButton {{
                background-color: {c.primary};
                color: {c.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }}

            QPushButton:hover {{
                background-color: {c.primary_hover};
            }}

            QPushButton:pressed {{
                background-color: {c.primary_muted};
            }}

            QPushButton:disabled {{
                background-color: {c.border_muted};
                color: {c.text_tertiary};
            }}

            /* Secondary/Ghost buttons */
            QPushButton[flat="true"],
            QPushButton[secondary="true"] {{
                background-color: transparent;
                color: {c.text_primary};
                border: 1px solid {c.border_default};
            }}

            QPushButton[flat="true"]:hover,
            QPushButton[secondary="true"]:hover {{
                background-color: {c.bg_elevated};
                border-color: {c.primary};
            }}

            /* Danger button */
            QPushButton[danger="true"] {{
                background-color: {c.error};
            }}

            QPushButton[danger="true"]:hover {{
                background-color: #dc2626;
            }}

            /* ========================================
               LABELS
               ======================================== */

            QLabel {{
                background-color: transparent;
                color: {c.text_primary};
                border: none;
            }}

            /* ========================================
               FRAMES & CARDS
               ======================================== */

            QFrame {{
                background-color: transparent;
                border: none;
            }}

            /* Card style - use object names or properties */
            QFrame[card="true"] {{
                background-color: {c.bg_surface};
                border: 1px solid {c.border_muted};
                border-radius: 12px;
            }}

            /* ========================================
               COMBO BOX
               ======================================== */

            QComboBox {{
                background-color: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 6px;
                padding: 6px 28px 6px 12px;
                min-height: 20px;
            }}

            QComboBox:focus {{
                border-color: {c.primary};
            }}

            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border: none;
                background: transparent;
            }}

            QComboBox QAbstractItemView {{
                background-color: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                selection-background-color: {c.entry_selected};
                outline: none;
            }}

            QComboBox QAbstractItemView::item {{
                padding: 6px 12px;
                min-height: 24px;
            }}

            QComboBox QAbstractItemView::item:hover {{
                background-color: {c.entry_hover};
            }}

            /* ========================================
               CHECKBOXES & RADIO BUTTONS
               ======================================== */

            QCheckBox, QRadioButton {{
                color: {c.text_primary};
                spacing: 8px;
                background-color: transparent;
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {c.border_default};
                border-radius: 4px;
                background-color: {c.bg_elevated};
            }}

            QCheckBox::indicator:checked {{
                background-color: {c.primary};
                border-color: {c.primary};
            }}

            QCheckBox::indicator:hover {{
                border-color: {c.primary};
            }}

            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {c.border_default};
                border-radius: 9px;
                background-color: {c.bg_elevated};
            }}

            QRadioButton::indicator:checked {{
                background-color: {c.primary};
                border-color: {c.primary};
            }}

            QRadioButton::indicator:hover {{
                border-color: {c.primary};
            }}

            /* ========================================
               MENUS
               ======================================== */

            QMenu {{
                background-color: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 8px;
                padding: 4px;
            }}

            QMenu::item {{
                padding: 8px 24px 8px 12px;
                border-radius: 4px;
            }}

            QMenu::item:selected {{
                background-color: {c.entry_selected};
            }}

            QMenu::separator {{
                height: 1px;
                background-color: {c.border_muted};
                margin: 4px 8px;
            }}

            /* ========================================
               TAB WIDGET
               ======================================== */

            QTabWidget::pane {{
                background-color: {c.bg_surface};
                border: 1px solid {c.border_muted};
                border-radius: 8px;
                padding: 8px;
            }}

            QTabBar::tab {{
                background-color: transparent;
                color: {c.text_secondary};
                padding: 10px 20px;
                margin-right: 4px;
                border: none;
                border-bottom: 2px solid transparent;
            }}

            QTabBar::tab:selected {{
                color: {c.primary};
                border-bottom-color: {c.primary};
            }}

            QTabBar::tab:hover:!selected {{
                color: {c.text_primary};
            }}

            /* ========================================
               TOOLTIPS
               ======================================== */

            QToolTip {{
                background-color: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 4px;
                padding: 6px 10px;
            }}

            /* ========================================
               MESSAGE BOX
               ======================================== */

            QMessageBox {{
                background-color: {c.bg_surface};
            }}

            QMessageBox QLabel {{
                color: {c.text_primary};
            }}

            /* ========================================
               STACKED WIDGET
               ======================================== */

            QStackedWidget {{
                background-color: {c.bg_base};
            }}

            /* ========================================
               SPLITTER
               ======================================== */

            QSplitter::handle {{
                background-color: {c.border_muted};
            }}

            QSplitter::handle:hover {{
                background-color: {c.border_default};
            }}

            /* ========================================
               SPIN BOX
               ======================================== */

            QSpinBox {{
                background-color: {c.bg_elevated};
                color: {c.text_primary};
                border: 1px solid {c.border_default};
                border-radius: 6px;
                padding: 6px 8px;
            }}

            QSpinBox:focus {{
                border-color: {c.primary};
            }}

            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: transparent;
                border: none;
                width: 16px;
            }}
        """

    def get_color(self, color_name: str) -> QColor:
        """Get QColor object for a named color from the palette."""
        color_value = getattr(self._current_palette, color_name, "#000000")
        return QColor(color_value)
