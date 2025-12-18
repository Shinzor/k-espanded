"""Settings view component for application preferences."""

import flet as ft
from pathlib import Path
from typing import Callable

from espanded.core.app_state import get_app_state
from espanded.core.espanso_config import (
    EspansoConfig,
    EspansoConfigHandler,
    TOGGLE_KEY_OPTIONS,
    BACKEND_OPTIONS,
)
from espanded.ui.theme import ThemeManager
from espanded.ui.components.hotkey_recorder import HotkeyRecorder


class SettingsView(ft.Container):
    """Settings view for managing application preferences."""

    def __init__(self, theme: ThemeManager, on_close: Callable[[], None], on_theme_change: Callable[[], None] | None = None):
        super().__init__()
        self.theme = theme
        self.on_close = on_close
        self.on_theme_change = on_theme_change
        self.app_state = get_app_state()

        # Local state for form fields
        self.settings = self.app_state.settings
        self._mounted = False

        # Espanso config
        self.espanso_config: EspansoConfig | None = None
        self._load_espanso_config()

        # File picker for browse functionality
        self.folder_picker = ft.FilePicker(on_result=self._on_folder_picked)

        self._build()

    def _load_espanso_config(self):
        """Load Espanso configuration from default.yml."""
        if self.settings.espanso_config_path:
            try:
                handler = EspansoConfigHandler(self.settings.espanso_config_path)
                if handler.exists():
                    self.espanso_config = handler.load()
                else:
                    self.espanso_config = EspansoConfig()
            except Exception:
                self.espanso_config = EspansoConfig()
        else:
            self.espanso_config = EspansoConfig()

    def did_mount(self):
        """Called when control is added to page."""
        self._mounted = True
        if self.page and self.folder_picker not in self.page.overlay:
            self.page.overlay.append(self.folder_picker)
            self.page.update()

    def will_unmount(self):
        """Called when control is removed from page."""
        self._mounted = False

    def _on_browse_espanso_path(self, e):
        """Handle browse button for Espanso path."""
        if not self.page:
            return
        # Ensure folder picker is in overlay
        if self.folder_picker not in self.page.overlay:
            self.page.overlay.append(self.folder_picker)
            self.page.update()
        self.folder_picker.get_directory_path(dialog_title="Select Espanso Config Directory")

    def _build(self):
        """Build the settings view layout."""
        colors = self.theme.colors

        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SETTINGS, size=24, color=colors.primary),
                            ft.Text(
                                "Settings",
                                size=20,
                                weight=ft.FontWeight.W_600,
                                color=colors.text_primary,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=colors.text_secondary,
                        on_click=lambda e: self.on_close(),
                        tooltip="Close",
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            margin=ft.margin.only(bottom=16),
        )

        # Action buttons row - fixed at top (like Entry Editor)
        actions_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.TextButton(
                        text="Reset to Defaults",
                        on_click=self._on_reset_defaults,
                    ),
                    ft.ElevatedButton(
                        text="Save Settings",
                        icon=ft.Icons.SAVE,
                        bgcolor=colors.primary,
                        color=colors.text_inverse,
                        on_click=self._on_save,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(bottom=16),
            border=ft.border.only(bottom=ft.BorderSide(1, colors.border_muted)),
        )

        # Settings sections
        espanso_section = self._build_espanso_section()
        espanso_options_section = self._build_espanso_options_section()
        sync_section = self._build_sync_section()
        hotkeys_section = self._build_hotkeys_section()
        appearance_section = self._build_appearance_section()

        # Scrollable content
        scrollable_content = ft.Column(
            controls=[
                ft.Container(height=16),  # Top spacing after actions
                espanso_section,
                ft.Container(height=16),
                espanso_options_section,
                ft.Container(height=16),
                sync_section,
                ft.Container(height=16),
                hotkeys_section,
                ft.Container(height=16),
                appearance_section,
                ft.Container(height=16),  # Bottom padding
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # Main layout with fixed header/actions and scrollable content
        self.content = ft.Column(
            controls=[
                header,
                actions_row,
                scrollable_content,
            ],
            spacing=0,
            expand=True,
        )
        self.expand = True
        self.padding = 20

    def _build_section_header(self, icon, title):
        """Build a section header."""
        colors = self.theme.colors

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=20, color=colors.primary),
                    ft.Text(
                        title,
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=colors.text_primary,
                    ),
                ],
                spacing=8,
            ),
            margin=ft.margin.only(bottom=12),
        )

    def _build_subsection_title(self, title: str) -> ft.Container:
        """Build a subsection title with proper spacing."""
        colors = self.theme.colors
        return ft.Container(
            content=ft.Text(
                title,
                size=12,
                weight=ft.FontWeight.W_500,
                color=colors.text_tertiary,
            ),
            margin=ft.margin.only(top=12, bottom=4),
        )

    def _build_espanso_section(self):
        """Build Espanso configuration section."""
        colors = self.theme.colors

        self.espanso_path_field = ft.TextField(
            label="Config Path",
            value=self.settings.espanso_config_path,
            expand=True,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            hint_text="Path to Espanso configuration directory",
        )

        browse_button = ft.ElevatedButton(
            text="Browse",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._on_browse_espanso_path,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_section_header(ft.Icons.FOLDER_OUTLINED, "Espanso Configuration"),
                    ft.Row(
                        controls=[
                            self.espanso_path_field,
                            browse_button,
                        ],
                        spacing=12,
                    ),
                    ft.Text(
                        "Location of your Espanso configuration files",
                        size=11,
                        color=colors.text_tertiary,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=colors.bg_surface,
            padding=16,
            border_radius=12,
            border=ft.border.all(1, colors.border_muted),
        )

    def _build_espanso_options_section(self):
        """Build Espanso options section for default.yml settings."""
        colors = self.theme.colors
        config = self.espanso_config or EspansoConfig()

        # === UI & Notifications ===
        self.esp_show_icon = ft.Switch(
            label="Show tray icon",
            value=config.show_icon,
        )

        self.esp_show_notifications = ft.Switch(
            label="Show notifications",
            value=config.show_notifications,
        )

        # === Behavior ===
        self.esp_auto_restart = ft.Switch(
            label="Auto-restart on config change",
            value=config.auto_restart,
        )

        self.esp_preserve_clipboard = ft.Switch(
            label="Preserve clipboard after expansion",
            value=config.preserve_clipboard,
        )

        self.esp_undo_backspace = ft.Switch(
            label="Undo expansion with backspace",
            value=config.undo_backspace,
        )

        self.esp_enable = ft.Switch(
            label="Enable Espanso",
            value=config.enable,
        )

        self.esp_apply_patch = ft.Switch(
            label="Apply app-specific patches",
            value=config.apply_patch,
        )

        # === Toggle Key ===
        self.esp_toggle_key = ft.Dropdown(
            label="Toggle key",
            value=config.toggle_key,
            options=[ft.dropdown.Option(key, label) for key, label in TOGGLE_KEY_OPTIONS],
            width=200,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
        )

        # === Search ===
        self.esp_search_shortcut = HotkeyRecorder(
            value=config.search_shortcut,
            label="Search shortcut",
            width=280,
            colors=colors,
        )

        self.esp_search_trigger = ft.TextField(
            label="Search trigger word",
            value=config.search_trigger,
            width=200,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            hint_text="off (disabled)",
        )

        # === Backend ===
        self.esp_backend = ft.Dropdown(
            label="Injection backend",
            value=config.backend,
            options=[ft.dropdown.Option(key, label) for key, label in BACKEND_OPTIONS],
            width=200,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
        )

        self.esp_paste_shortcut = HotkeyRecorder(
            value=config.paste_shortcut,
            label="Paste shortcut",
            width=280,
            colors=colors,
        )

        # === Timing (Advanced) ===
        self.esp_inject_delay = ft.TextField(
            label="Inject delay (ms)",
            value=str(config.inject_delay),
            width=120,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.esp_key_delay = ft.TextField(
            label="Key delay (ms)",
            value=str(config.key_delay),
            width=120,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.esp_clipboard_threshold = ft.TextField(
            label="Clipboard threshold",
            value=str(config.clipboard_threshold),
            width=120,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.esp_backspace_limit = ft.TextField(
            label="Backspace limit",
            value=str(config.backspace_limit),
            width=120,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.esp_pre_paste_delay = ft.TextField(
            label="Pre-paste delay (ms)",
            value=str(config.pre_paste_delay),
            width=120,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.esp_restore_clipboard_delay = ft.TextField(
            label="Restore clipboard delay (ms)",
            value=str(config.restore_clipboard_delay),
            width=120,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # === Form Settings ===
        self.esp_max_form_width = ft.TextField(
            label="Max form width (px)",
            value=str(config.max_form_width),
            width=120,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.esp_max_form_height = ft.TextField(
            label="Max form height (px)",
            value=str(config.max_form_height),
            width=120,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Expandable advanced section
        self.esp_advanced_expanded = False
        self.esp_advanced_content = ft.Container(
            content=ft.Column(
                controls=[
                    self._build_subsection_title("Timing"),
                    ft.Row(
                        controls=[
                            self.esp_inject_delay,
                            self.esp_key_delay,
                            self.esp_clipboard_threshold,
                        ],
                        spacing=12,
                        wrap=True,
                    ),
                    ft.Row(
                        controls=[
                            self.esp_backspace_limit,
                            self.esp_pre_paste_delay,
                            self.esp_restore_clipboard_delay,
                        ],
                        spacing=12,
                        wrap=True,
                    ),
                    self._build_subsection_title("Form Dimensions"),
                    ft.Row(
                        controls=[
                            self.esp_max_form_width,
                            self.esp_max_form_height,
                        ],
                        spacing=12,
                    ),
                ],
                spacing=6,
            ),
            padding=ft.padding.only(top=8),
            visible=False,
        )

        self.esp_advanced_toggle_icon = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_RIGHT,
            size=18,
            color=colors.text_secondary,
        )

        advanced_toggle = ft.Container(
            content=ft.Row(
                controls=[
                    self.esp_advanced_toggle_icon,
                    ft.Text("Advanced Options", size=13, color=colors.text_secondary),
                ],
                spacing=4,
            ),
            on_click=self._toggle_esp_advanced,
            padding=ft.padding.symmetric(vertical=8),
            ink=True,
        )

        # Note about Espanso restart
        restart_note = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=colors.primary),
                    ft.Text(
                        "Changes apply when Espanso restarts. Enable 'Auto-restart on config change' for immediate effect.",
                        size=11,
                        color=colors.text_secondary,
                        expand=True,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=colors.bg_elevated,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=6,
            margin=ft.margin.only(top=4, bottom=4),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_section_header(ft.Icons.TUNE, "Espanso Options"),
                    ft.Text(
                        "Configure Espanso's default.yml settings",
                        size=11,
                        color=colors.text_tertiary,
                    ),
                    restart_note,
                    # UI & Notifications
                    self._build_subsection_title("Interface"),
                    ft.Row(controls=[self.esp_show_icon, self.esp_show_notifications], spacing=24, wrap=True),
                    # Behavior
                    self._build_subsection_title("Behavior"),
                    ft.Row(controls=[self.esp_enable, self.esp_auto_restart], spacing=24, wrap=True),
                    ft.Row(controls=[self.esp_preserve_clipboard, self.esp_undo_backspace], spacing=24, wrap=True),
                    self.esp_apply_patch,
                    # Toggle & Search
                    self._build_subsection_title("Toggle & Search"),
                    ft.Row(
                        controls=[self.esp_toggle_key, self.esp_search_shortcut, self.esp_search_trigger],
                        spacing=12,
                        wrap=True,
                    ),
                    # Backend
                    self._build_subsection_title("Backend"),
                    ft.Row(
                        controls=[self.esp_backend, self.esp_paste_shortcut],
                        spacing=12,
                    ),
                    # Advanced section
                    ft.Container(height=8),
                    ft.Divider(height=1, color=colors.border_muted),
                    advanced_toggle,
                    self.esp_advanced_content,
                ],
                spacing=6,
            ),
            bgcolor=colors.bg_surface,
            padding=16,
            border_radius=12,
            border=ft.border.all(1, colors.border_muted),
        )

    def _toggle_esp_advanced(self, e=None):
        """Toggle Espanso advanced options visibility."""
        self.esp_advanced_expanded = not self.esp_advanced_expanded
        self.esp_advanced_content.visible = self.esp_advanced_expanded
        self.esp_advanced_toggle_icon.name = (
            ft.Icons.KEYBOARD_ARROW_DOWN if self.esp_advanced_expanded else ft.Icons.KEYBOARD_ARROW_RIGHT
        )
        if self._mounted:
            self.update()

    def _build_sync_section(self):
        """Build GitHub sync section."""
        colors = self.theme.colors

        self.github_repo_field = ft.TextField(
            label="Repository",
            value=self.settings.github_repo or "",
            expand=True,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            hint_text="username/repository",
        )

        self.auto_sync_checkbox = ft.Checkbox(
            label="Auto-sync on changes",
            value=self.settings.auto_sync,
        )

        self.sync_interval_field = ft.TextField(
            label="Sync interval (minutes)",
            value=str(self.settings.sync_interval // 60),
            width=200,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Connection status
        is_connected = bool(self.settings.github_repo and self.settings.github_token)
        status_text = "Connected" if is_connected else "Not connected"
        status_color = colors.success if is_connected else colors.text_tertiary
        status_icon = ft.Icons.CHECK_CIRCLE if is_connected else ft.Icons.CLOUD_OFF

        connection_button = ft.ElevatedButton(
            text="Disconnect" if is_connected else "Connect with GitHub",
            icon=ft.Icons.LINK_OFF if is_connected else ft.Icons.LINK,
            bgcolor=colors.error if is_connected else colors.primary,
            color=colors.text_inverse,
            on_click=self._on_toggle_github_connection,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_section_header(ft.Icons.CLOUD_SYNC, "GitHub Sync"),
                    ft.Row(
                        controls=[
                            ft.Icon(status_icon, color=status_color, size=18),
                            ft.Text(status_text, size=13, color=status_color),
                        ],
                        spacing=8,
                    ),
                    ft.Container(height=8),
                    self.github_repo_field,
                    connection_button,
                    ft.Container(height=12),
                    self.auto_sync_checkbox,
                    self.sync_interval_field,
                    ft.Text(
                        "Note: OAuth integration is not yet implemented",
                        size=11,
                        color=colors.text_tertiary,
                        italic=True,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=colors.bg_surface,
            padding=16,
            border_radius=12,
            border=ft.border.all(1, colors.border_muted),
        )

    def _build_hotkeys_section(self):
        """Build hotkeys section."""
        colors = self.theme.colors

        # Enable/Disable hotkeys toggle
        self.hotkeys_enabled_switch = ft.Switch(
            label="Enable global hotkeys",
            value=self.settings.hotkeys_enabled if hasattr(self.settings, 'hotkeys_enabled') else True,
        )

        self.quick_add_hotkey_recorder = HotkeyRecorder(
            value=self.settings.quick_add_hotkey,
            label="Quick Add Hotkey",
            width=320,
            colors=colors,
        )

        self.minimize_to_tray_checkbox = ft.Checkbox(
            label="Minimize to system tray",
            value=self.settings.minimize_to_tray,
        )

        # Info note about how hotkeys work
        hotkey_info = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=colors.primary),
                    ft.Text(
                        "Press the hotkey anywhere to open Quick Add. If text is selected, it will be used as the replacement.",
                        size=11,
                        color=colors.text_secondary,
                        expand=True,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=colors.bg_elevated,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=6,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_section_header(ft.Icons.KEYBOARD, "Hotkeys & Behavior"),
                    hotkey_info,
                    ft.Container(height=8),
                    self.hotkeys_enabled_switch,
                    ft.Container(height=8),
                    self.quick_add_hotkey_recorder,
                    ft.Container(height=12),
                    self.minimize_to_tray_checkbox,
                ],
                spacing=8,
            ),
            bgcolor=colors.bg_surface,
            padding=16,
            border_radius=12,
            border=ft.border.all(1, colors.border_muted),
        )

    def _build_appearance_section(self):
        """Build appearance section."""
        colors = self.theme.colors

        self.theme_radio_group = ft.RadioGroup(
            content=ft.Row(
                controls=[
                    ft.Radio(value="light", label="Light"),
                    ft.Radio(value="dark", label="Dark"),
                    ft.Radio(value="system", label="System"),
                ],
                spacing=16,
            ),
            value=self.settings.theme,
        )

        self.default_prefix_dropdown = ft.Dropdown(
            label="Default Prefix",
            value=self.settings.default_prefix,
            options=[
                ft.dropdown.Option(":", ": (colon)"),
                ft.dropdown.Option(";", "; (semicolon)"),
                ft.dropdown.Option("//", "// (double slash)"),
                ft.dropdown.Option("::", ":: (double colon)"),
                ft.dropdown.Option("", "(none)"),
            ],
            width=200,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_section_header(ft.Icons.PALETTE, "Appearance"),
                    ft.Text(
                        "Theme",
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=colors.text_primary,
                    ),
                    self.theme_radio_group,
                    ft.Container(height=8),
                    self.default_prefix_dropdown,
                    ft.Text(
                        "Default trigger prefix for new entries",
                        size=11,
                        color=colors.text_tertiary,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=colors.bg_surface,
            padding=16,
            border_radius=12,
            border=ft.border.all(1, colors.border_muted),
        )

    def _on_folder_picked(self, e: ft.FilePickerResultEvent):
        """Handle folder picker result."""
        if e.path:
            self.espanso_path_field.value = e.path
            if self._mounted:
                self.update()

    def _on_toggle_github_connection(self, e):
        """Handle GitHub connection toggle."""
        is_connected = bool(self.settings.github_repo and self.settings.github_token)

        if is_connected:
            # Disconnect
            self._confirm_disconnect()
        else:
            # Connect - would open OAuth flow in real implementation
            self._show_snackbar("GitHub OAuth integration coming soon")

    def _confirm_disconnect(self):
        """Confirm GitHub disconnection."""
        colors = self.theme.colors

        def disconnect_confirmed(e):
            dialog.open = False
            self.page.update()

            # Clear GitHub settings
            self.settings.github_repo = None
            self.settings.github_token = None
            self.app_state.save_settings()

            self._show_snackbar("Disconnected from GitHub")
            # Rebuild to update UI
            self._build()
            if self._mounted:
                self.update()

        def cancel_disconnect(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER, color=colors.warning),
                    ft.Text("Confirm Disconnect", color=colors.text_primary),
                ],
                spacing=8,
            ),
            content=ft.Text(
                "Are you sure you want to disconnect from GitHub? Your local entries will not be affected.",
                size=14,
                color=colors.text_primary,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_disconnect),
                ft.ElevatedButton(
                    "Disconnect",
                    bgcolor=colors.error,
                    color=colors.text_inverse,
                    on_click=disconnect_confirmed,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors.bg_surface,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _on_reset_defaults(self, e):
        """Reset settings to defaults."""
        colors = self.theme.colors

        def reset_confirmed(e):
            dialog.open = False
            self.page.update()

            # Create new settings with defaults
            from espanded.core.models import Settings
            self.settings = Settings()
            self.app_state.settings = self.settings

            self._show_snackbar("Settings reset to defaults")
            # Rebuild to update UI
            self._build()
            if self._mounted:
                self.update()

            # Notify theme change
            if self.on_theme_change:
                self.on_theme_change()

        def cancel_reset(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER, color=colors.warning),
                    ft.Text("Reset to Defaults", color=colors.text_primary),
                ],
                spacing=8,
            ),
            content=ft.Text(
                "Are you sure you want to reset all settings to their default values?",
                size=14,
                color=colors.text_primary,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_reset),
                ft.ElevatedButton(
                    "Reset",
                    bgcolor=colors.warning,
                    color=colors.text_inverse,
                    on_click=reset_confirmed,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors.bg_surface,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _on_save(self, e):
        """Save settings."""
        try:
            # Update settings from form fields
            self.settings.espanso_config_path = self.espanso_path_field.value
            self.settings.github_repo = self.github_repo_field.value or None
            self.settings.auto_sync = self.auto_sync_checkbox.value

            # Parse sync interval
            try:
                interval_minutes = int(self.sync_interval_field.value)
                self.settings.sync_interval = interval_minutes * 60
            except ValueError:
                self.settings.sync_interval = 300  # Default 5 minutes

            # Check if hotkey changed
            old_hotkey = self.settings.quick_add_hotkey
            new_hotkey = self.quick_add_hotkey_recorder.value

            self.settings.quick_add_hotkey = new_hotkey
            self.settings.hotkeys_enabled = self.hotkeys_enabled_switch.value
            self.settings.minimize_to_tray = self.minimize_to_tray_checkbox.value

            # Theme settings
            old_theme = self.settings.theme
            self.settings.theme = self.theme_radio_group.value
            self.settings.default_prefix = self.default_prefix_dropdown.value

            # Save to database
            self.app_state.settings = self.settings

            # Save Espanso options to default.yml
            self._save_espanso_config()

            # Update hotkey service if hotkey changed
            if old_hotkey != new_hotkey:
                try:
                    from espanded.services.hotkey_service import get_hotkey_service
                    hotkey_service = get_hotkey_service()
                    if hotkey_service.is_available:
                        hotkey_service.update_hotkey(new_hotkey)
                        self._show_snackbar(f"Hotkey updated to: {new_hotkey}")
                    else:
                        self._show_snackbar("Settings saved (hotkey requires restart)")
                except Exception as ex:
                    print(f"Error updating hotkey service: {ex}")
                    self._show_snackbar("Settings saved (hotkey requires restart)")
            else:
                self._show_snackbar("Settings saved successfully")

            # If theme changed, notify parent
            if old_theme != self.settings.theme and self.on_theme_change:
                self.on_theme_change()

        except Exception as ex:
            self._show_snackbar(f"Error saving settings: {str(ex)}", error=True)

    def _save_espanso_config(self):
        """Save Espanso options to default.yml."""
        if not self.settings.espanso_config_path:
            return

        # Build config from form fields
        config = EspansoConfig(
            # UI & Notifications
            show_icon=self.esp_show_icon.value,
            show_notifications=self.esp_show_notifications.value,
            # Behavior
            auto_restart=self.esp_auto_restart.value,
            preserve_clipboard=self.esp_preserve_clipboard.value,
            undo_backspace=self.esp_undo_backspace.value,
            enable=self.esp_enable.value,
            apply_patch=self.esp_apply_patch.value,
            # Toggle & Search
            toggle_key=self.esp_toggle_key.value or "OFF",
            search_shortcut=self.esp_search_shortcut.value or "ALT+SPACE",
            search_trigger=self.esp_search_trigger.value or "off",
            # Backend
            backend=self.esp_backend.value or "Auto",
            paste_shortcut=self.esp_paste_shortcut.value or "CTRL+V",
            # Timing (parse integers safely)
            inject_delay=self._parse_int(self.esp_inject_delay.value, 0),
            key_delay=self._parse_int(self.esp_key_delay.value, 0),
            clipboard_threshold=self._parse_int(self.esp_clipboard_threshold.value, 100),
            backspace_limit=self._parse_int(self.esp_backspace_limit.value, 5),
            pre_paste_delay=self._parse_int(self.esp_pre_paste_delay.value, 300),
            restore_clipboard_delay=self._parse_int(self.esp_restore_clipboard_delay.value, 300),
            # Form dimensions
            max_form_width=self._parse_int(self.esp_max_form_width.value, 700),
            max_form_height=self._parse_int(self.esp_max_form_height.value, 500),
        )

        # Save to file
        handler = EspansoConfigHandler(self.settings.espanso_config_path)
        handler.save(config)

        # Update local state
        self.espanso_config = config

    def _parse_int(self, value: str, default: int) -> int:
        """Safely parse an integer from string."""
        try:
            return int(value) if value else default
        except ValueError:
            return default

    def _show_snackbar(self, message: str, error: bool = False):
        """Show a snackbar notification."""
        colors = self.theme.colors
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=colors.text_primary),
            bgcolor=colors.error if error else colors.success,
            duration=2000,
        )
        self.page.snack_bar.open = True
        self.page.update()
