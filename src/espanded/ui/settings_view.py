"""Settings view for application preferences."""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QFrame,
    QScrollArea,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from espanded.ui.theme import ThemeManager
from espanded.ui.components.hotkey_recorder import HotkeyRecorder
from espanded.core.app_state import get_app_state
from espanded.core.models import Settings


class SettingsView(QWidget):
    """Settings view for managing application preferences."""

    # Signals
    close_requested = Signal()
    theme_changed = Signal()
    settings_saved = Signal()

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.app_state = get_app_state()

        # Local state for form fields
        self.settings = self.app_state.settings

        self._setup_ui()

    def _setup_ui(self):
        """Build the settings view layout."""
        colors = self.theme_manager.colors

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Action buttons row (fixed at top)
        actions_row = self._create_action_buttons()
        layout.addWidget(actions_row)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors.bg_base};
                border: none;
            }}
        """)

        content = self._create_content()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

    def _create_header(self) -> QWidget:
        """Create settings header."""
        colors = self.theme_manager.colors

        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_base};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 0)

        # Icon and title
        title_row = QWidget()
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)

        icon_label = QLabel("\u2699")  # Gear emoji
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                color: {colors.primary};
                background-color: transparent;
            }}
        """)
        title_layout.addWidget(icon_label)

        title = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        title_layout.addWidget(title)

        header_layout.addWidget(title_row)
        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("\u2715")  # X symbol
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.close_requested.emit)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: none;
                border-radius: 4px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {colors.bg_elevated};
            }}
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(close_btn)

        return header

    def _create_action_buttons(self) -> QWidget:
        """Create action buttons row."""
        colors = self.theme_manager.colors

        actions = QWidget()
        actions.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_base};
                border-bottom: 1px solid {colors.border_muted};
            }}
        """)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(20, 16, 20, 16)

        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._on_reset_defaults)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: none;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                color: {colors.text_primary};
                text-decoration: underline;
            }}
        """)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(reset_btn)
        actions_layout.addStretch()

        # Save button
        save_btn = QPushButton("\u1F4BE Save Settings")
        save_btn.clicked.connect(self._on_save)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
        """)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(save_btn)

        return actions

    def _create_content(self) -> QWidget:
        """Create scrollable settings content."""
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 20)
        content_layout.setSpacing(16)

        # Appearance section
        appearance_section = self._create_appearance_section()
        content_layout.addWidget(appearance_section)

        # Espanso section
        espanso_section = self._create_espanso_section()
        content_layout.addWidget(espanso_section)

        # GitHub Sync section
        sync_section = self._create_sync_section()
        content_layout.addWidget(sync_section)

        # Hotkeys section
        hotkeys_section = self._create_hotkeys_section()
        content_layout.addWidget(hotkeys_section)

        content_layout.addStretch()

        return content

    def _create_section_card(self, title: str, icon: str, content_widget: QWidget) -> QFrame:
        """Create a settings section card."""
        colors = self.theme_manager.colors

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_surface};
                border: 1px solid {colors.border_muted};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                color: {colors.primary};
                background-color: transparent;
            }}
        """)
        header_layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

        # Content
        layout.addWidget(content_widget)

        return card

    def _create_appearance_section(self) -> QFrame:
        """Create appearance settings section."""
        colors = self.theme_manager.colors

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # Theme selection
        theme_label = QLabel("Theme")
        theme_label_font = QFont()
        theme_label_font.setPointSize(10)
        theme_label_font.setBold(True)
        theme_label.setFont(theme_label_font)
        theme_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(theme_label)

        # Radio buttons for theme
        theme_row = QWidget()
        theme_layout = QHBoxLayout(theme_row)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(16)

        self.theme_group = QButtonGroup()

        self.light_radio = QRadioButton("Light")
        self.dark_radio = QRadioButton("Dark")
        self.system_radio = QRadioButton("System")

        self.theme_group.addButton(self.light_radio, 0)
        self.theme_group.addButton(self.dark_radio, 1)
        self.theme_group.addButton(self.system_radio, 2)

        # Set current theme
        if self.settings.theme == "light":
            self.light_radio.setChecked(True)
        elif self.settings.theme == "dark":
            self.dark_radio.setChecked(True)
        else:
            self.system_radio.setChecked(True)

        theme_layout.addWidget(self.light_radio)
        theme_layout.addWidget(self.dark_radio)
        theme_layout.addWidget(self.system_radio)
        theme_layout.addStretch()

        content_layout.addWidget(theme_row)

        # Default prefix
        prefix_label = QLabel("Default Prefix")
        prefix_label.setFont(theme_label_font)
        prefix_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(prefix_label)

        self.default_prefix_dropdown = QComboBox()
        self.default_prefix_dropdown.addItem(": (colon)", ":")
        self.default_prefix_dropdown.addItem("; (semicolon)", ";")
        self.default_prefix_dropdown.addItem("// (double slash)", "//")
        self.default_prefix_dropdown.addItem(":: (double colon)", "::")
        self.default_prefix_dropdown.addItem("(none)", "")

        # Set current value
        for i in range(self.default_prefix_dropdown.count()):
            if self.default_prefix_dropdown.itemData(i) == self.settings.default_prefix:
                self.default_prefix_dropdown.setCurrentIndex(i)
                break

        self.default_prefix_dropdown.setMaximumWidth(200)
        content_layout.addWidget(self.default_prefix_dropdown)

        help_text = QLabel("Default trigger prefix for new entries")
        help_text.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(help_text)

        return self._create_section_card("Appearance", "\u1F3A8", content)

    def _create_espanso_section(self) -> QFrame:
        """Create Espanso configuration section."""
        colors = self.theme_manager.colors

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # Config path
        path_label = QLabel("Config Path")
        path_label_font = QFont()
        path_label_font.setPointSize(10)
        path_label_font.setBold(True)
        path_label.setFont(path_label_font)
        path_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(path_label)

        path_row = QWidget()
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(12)

        self.espanso_path_field = QLineEdit()
        self.espanso_path_field.setText(self.settings.espanso_config_path)
        self.espanso_path_field.setPlaceholderText("Path to Espanso configuration directory")
        path_layout.addWidget(self.espanso_path_field, stretch=1)

        browse_btn = QPushButton("\u1F4C2 Browse")
        browse_btn.clicked.connect(self._on_browse_espanso_path)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {colors.bg_surface};
                border-color: {colors.primary};
            }}
        """)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        path_layout.addWidget(browse_btn)

        content_layout.addWidget(path_row)

        help_text = QLabel("Location of your Espanso configuration files")
        help_text.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(help_text)

        return self._create_section_card("Espanso Configuration", "\u1F4C1", content)

    def _create_sync_section(self) -> QFrame:
        """Create GitHub sync section."""
        colors = self.theme_manager.colors

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # Connection status
        is_connected = bool(self.settings.github_repo and self.settings.github_token)
        status_text = "Connected" if is_connected else "Not connected"
        status_icon = "\u2713" if is_connected else "\u2601"
        status_color = colors.success if is_connected else colors.text_tertiary

        status_row = QWidget()
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)

        status_icon_label = QLabel(status_icon)
        status_icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                color: {status_color};
                background-color: transparent;
            }}
        """)
        status_layout.addWidget(status_icon_label)

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {status_color};
                background-color: transparent;
            }}
        """)
        status_layout.addWidget(status_label)
        status_layout.addStretch()

        content_layout.addWidget(status_row)

        # Repository field
        repo_label = QLabel("Repository")
        repo_label_font = QFont()
        repo_label_font.setPointSize(10)
        repo_label_font.setBold(True)
        repo_label.setFont(repo_label_font)
        repo_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(repo_label)

        self.github_repo_field = QLineEdit()
        self.github_repo_field.setText(self.settings.github_repo or "")
        self.github_repo_field.setPlaceholderText("username/repository")
        content_layout.addWidget(self.github_repo_field)

        # Auto-sync checkbox
        self.auto_sync_checkbox = QCheckBox("Auto-sync on changes")
        self.auto_sync_checkbox.setChecked(self.settings.auto_sync)
        content_layout.addWidget(self.auto_sync_checkbox)

        # Sync interval
        interval_label = QLabel("Sync interval (minutes)")
        interval_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(interval_label)

        self.sync_interval_field = QLineEdit()
        self.sync_interval_field.setText(str(self.settings.sync_interval // 60))
        self.sync_interval_field.setMaximumWidth(100)
        content_layout.addWidget(self.sync_interval_field)

        # Note
        note = QLabel("Note: OAuth integration is not yet implemented")
        note.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {colors.text_tertiary};
                font-style: italic;
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(note)

        return self._create_section_card("GitHub Sync", "\u21BB", content)

    def _create_hotkeys_section(self) -> QFrame:
        """Create hotkeys settings section."""
        colors = self.theme_manager.colors

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # Info box
        info_box = QFrame()
        info_box.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_elevated};
                border: 1px solid {colors.border_muted};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        info_layout = QHBoxLayout(info_box)
        info_layout.setContentsMargins(8, 8, 8, 8)

        info_icon = QLabel("\u2139")
        info_icon.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {colors.primary};
                background-color: transparent;
            }}
        """)
        info_layout.addWidget(info_icon)

        info_text = QLabel("Press the hotkey anywhere to open Quick Add. If text is selected, it will be used as the replacement.")
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        info_layout.addWidget(info_text, stretch=1)

        content_layout.addWidget(info_box)

        # Enable hotkeys
        self.hotkeys_enabled_switch = QCheckBox("Enable global hotkeys")
        self.hotkeys_enabled_switch.setChecked(self.settings.hotkeys_enabled)
        content_layout.addWidget(self.hotkeys_enabled_switch)

        # Quick add hotkey recorder
        self.quick_add_hotkey_recorder = HotkeyRecorder(
            theme_manager=self.theme_manager,
            value=self.settings.quick_add_hotkey,
            label="Quick Add Hotkey",
        )
        self.quick_add_hotkey_recorder.setMaximumWidth(350)
        content_layout.addWidget(self.quick_add_hotkey_recorder)

        # Minimize to tray
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray")
        self.minimize_to_tray_checkbox.setChecked(self.settings.minimize_to_tray)
        content_layout.addWidget(self.minimize_to_tray_checkbox)

        return self._create_section_card("Hotkeys & Behavior", "\u2328", content)

    def _on_browse_espanso_path(self):
        """Handle browse button for Espanso path."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Espanso Config Directory",
            self.espanso_path_field.text() or str(Path.home()),
        )
        if directory:
            self.espanso_path_field.setText(directory)

    def _on_reset_defaults(self):
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Create new default settings
            self.settings = Settings()
            self.app_state.settings = self.settings

            # Rebuild UI to reflect defaults
            self._rebuild_ui()

            # Notify theme change
            self.theme_changed.emit()

            QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults")

    def _rebuild_ui(self):
        """Rebuild UI with current settings values."""
        # Theme
        if self.settings.theme == "light":
            self.light_radio.setChecked(True)
        elif self.settings.theme == "dark":
            self.dark_radio.setChecked(True)
        else:
            self.system_radio.setChecked(True)

        # Default prefix
        for i in range(self.default_prefix_dropdown.count()):
            if self.default_prefix_dropdown.itemData(i) == self.settings.default_prefix:
                self.default_prefix_dropdown.setCurrentIndex(i)
                break

        # Espanso
        self.espanso_path_field.setText(self.settings.espanso_config_path)

        # GitHub
        self.github_repo_field.setText(self.settings.github_repo or "")
        self.auto_sync_checkbox.setChecked(self.settings.auto_sync)
        self.sync_interval_field.setText(str(self.settings.sync_interval // 60))

        # Hotkeys
        self.hotkeys_enabled_switch.setChecked(self.settings.hotkeys_enabled)
        self.quick_add_hotkey_recorder.set_value(self.settings.quick_add_hotkey)
        self.minimize_to_tray_checkbox.setChecked(self.settings.minimize_to_tray)

    def _on_save(self):
        """Save settings."""
        try:
            # Get theme selection
            if self.light_radio.isChecked():
                theme = "light"
            elif self.dark_radio.isChecked():
                theme = "dark"
            else:
                theme = "system"

            # Check if theme changed
            old_theme = self.settings.theme
            theme_changed = old_theme != theme

            # Update settings from form fields
            self.settings.theme = theme
            self.settings.default_prefix = self.default_prefix_dropdown.currentData()
            self.settings.espanso_config_path = self.espanso_path_field.text()
            self.settings.github_repo = self.github_repo_field.text() or None
            self.settings.auto_sync = self.auto_sync_checkbox.isChecked()

            # Parse sync interval
            try:
                interval_minutes = int(self.sync_interval_field.text())
                self.settings.sync_interval = interval_minutes * 60
            except ValueError:
                self.settings.sync_interval = 10800  # Default 3 hours

            # Hotkeys
            self.settings.quick_add_hotkey = self.quick_add_hotkey_recorder.get_value()
            self.settings.hotkeys_enabled = self.hotkeys_enabled_switch.isChecked()
            self.settings.minimize_to_tray = self.minimize_to_tray_checkbox.isChecked()

            # Update hotkey service if settings changed
            from espanded.services.hotkey_service import get_hotkey_service

            hotkey_service = get_hotkey_service()
            if hotkey_service and hotkey_service.is_running:
                hotkey_service.update_hotkey(self.settings.quick_add_hotkey)
                if self.settings.hotkeys_enabled:
                    hotkey_service.enable()
                else:
                    hotkey_service.disable()

            # Save to database
            self.app_state.settings = self.settings

            # Emit signals
            self.settings_saved.emit()
            if theme_changed:
                self.theme_changed.emit()

            QMessageBox.information(self, "Settings Saved", "Settings saved successfully")

        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Error saving settings: {str(ex)}")
