"""Theme system with dark/light modes and color customization."""

from dataclasses import dataclass, field, asdict
from typing import Any

import flet as ft

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
    """Manages theme state and color overrides."""

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

    def apply_to_page(self, page: ft.Page):
        """Apply theme colors to Flet page."""
        colors = self.colors

        # Set theme mode
        page.theme_mode = ft.ThemeMode.DARK if self._is_dark else ft.ThemeMode.LIGHT

        # Create custom theme
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=colors.primary,
                on_primary=colors.text_inverse,
                primary_container=colors.primary_muted,
                secondary=colors.primary,
                surface=colors.bg_surface,
                on_surface=colors.text_primary,
                surface_variant=colors.bg_elevated,
                on_surface_variant=colors.text_secondary,
                background=colors.bg_base,
                on_background=colors.text_primary,
                error=colors.error,
                on_error=colors.text_inverse,
                outline=colors.border_default,
                outline_variant=colors.border_muted,
            ),
        )

        page.dark_theme = page.theme
        page.bgcolor = colors.bg_base
        page.update()

    def get_container_style(self, variant: str = "surface") -> dict[str, Any]:
        """Get styling dict for containers based on variant."""
        colors = self.colors

        styles = {
            "surface": {
                "bgcolor": colors.bg_surface,
                "border": ft.border.all(1, colors.border_muted),
            },
            "elevated": {
                "bgcolor": colors.bg_elevated,
                "border": ft.border.all(1, colors.border_default),
            },
            "sidebar": {
                "bgcolor": colors.bg_sidebar,
                "border": ft.border.only(right=ft.BorderSide(1, colors.border_muted)),
            },
        }
        return styles.get(variant, styles["surface"])
