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
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from espanded.ui.theme import ThemeManager
from espanded.ui.components.hotkey_recorder import HotkeyRecorder
from espanded.ui.components.message_dialog import (
    show_information,
    show_warning,
    show_critical,
    show_question,
)
from espanded.ui.components.tag_color_dialog import TagColorDialog
from espanded.ui.github_wizard import GitHubWizard
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
        save_btn = QPushButton("Save Settings")
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
        colors = self.theme_manager.colors

        content = QWidget()
        content.setStyleSheet(f"background-color: {colors.bg_base};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 20)
        content_layout.setSpacing(16)

        # Hotkeys section (first - most commonly used)
        hotkeys_section = self._create_hotkeys_section()
        content_layout.addWidget(hotkeys_section)

        # Autocomplete section (inline suggestions)
        autocomplete_section = self._create_autocomplete_section()
        content_layout.addWidget(autocomplete_section)

        # Espanso section
        espanso_section = self._create_espanso_section()
        content_layout.addWidget(espanso_section)

        # GitHub Sync section
        sync_section = self._create_sync_section()
        content_layout.addWidget(sync_section)

        # Appearance section (last)
        appearance_section = self._create_appearance_section()
        content_layout.addWidget(appearance_section)

        content_layout.addStretch()

        return content

    def _create_section_card(self, title: str, icon: str, content_widget: QWidget) -> QFrame:
        """Create a settings section card."""
        colors = self.theme_manager.colors

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_surface};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header (title only - icons removed for cross-platform compatibility)
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        layout.addWidget(title_label)

        # Content
        layout.addWidget(content_widget)

        return card

    def _create_appearance_section(self) -> QFrame:
        """Create appearance settings section."""
        colors = self.theme_manager.colors

        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
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
        theme_row.setStyleSheet("background-color: transparent;")
        theme_layout = QHBoxLayout(theme_row)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(16)

        self.theme_group = QButtonGroup()

        radio_style = f"""
            QRadioButton {{
                color: {colors.text_primary};
                spacing: 8px;
                background-color: transparent;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {colors.border_default};
                border-radius: 9px;
                background-color: {colors.bg_elevated};
            }}
            QRadioButton::indicator:checked {{
                background-color: {colors.primary};
                border-color: {colors.primary};
            }}
            QRadioButton::indicator:hover {{
                border-color: {colors.primary};
            }}
        """

        self.light_radio = QRadioButton("Light")
        self.light_radio.setStyleSheet(radio_style)
        self.dark_radio = QRadioButton("Dark")
        self.dark_radio.setStyleSheet(radio_style)
        self.system_radio = QRadioButton("System")
        self.system_radio.setStyleSheet(radio_style)

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
        self.default_prefix_dropdown.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QComboBox:focus {{
                border-color: {colors.primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                selection-background-color: {colors.entry_selected};
            }}
        """)

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

        # Tag Colors
        tag_colors_label = QLabel("Tag Colors")
        tag_colors_label.setFont(theme_label_font)
        tag_colors_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
                margin-top: 8px;
            }}
        """)
        content_layout.addWidget(tag_colors_label)

        tag_colors_btn = QPushButton("Customize Tag Colors")
        tag_colors_btn.setMaximumWidth(200)
        tag_colors_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
        """)
        tag_colors_btn.clicked.connect(self._on_customize_tag_colors)
        tag_colors_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        content_layout.addWidget(tag_colors_btn)

        tag_colors_help = QLabel("Customize colors for your tags")
        tag_colors_help.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(tag_colors_help)

        return self._create_section_card("Appearance", "", content)

    def _create_espanso_section(self) -> QFrame:
        """Create Espanso configuration section."""
        colors = self.theme_manager.colors

        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
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
        path_row.setStyleSheet("background-color: transparent;")
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(12)

        self.espanso_path_field = QLineEdit()
        self.espanso_path_field.setText(self.settings.espanso_config_path)
        self.espanso_path_field.setPlaceholderText("Path to Espanso configuration directory")
        self.espanso_path_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{
                border-color: {colors.primary};
            }}
        """)
        path_layout.addWidget(self.espanso_path_field, stretch=1)

        browse_btn = QPushButton("Browse")
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

        return self._create_section_card("Espanso Configuration", "", content)

    def _create_sync_section(self) -> QFrame:
        """Create GitHub sync section."""
        colors = self.theme_manager.colors

        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # Connection status row with Sync Now button
        is_connected = bool(self.settings.github_repo and self.settings.github_token)
        status_text = "Connected" if is_connected else "Not connected"
        status_icon = "\u2713" if is_connected else "\u2601"
        status_color = colors.success if is_connected else colors.text_tertiary

        status_row = QWidget()
        status_row.setStyleSheet("background-color: transparent;")
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

        # Connect to GitHub button
        self.connect_github_btn = QPushButton("Connect to GitHub" if not is_connected else "Settings")
        self.connect_github_btn.clicked.connect(self._on_connect_github)
        self.connect_github_btn.setStyleSheet(f"""
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
        self.connect_github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        status_layout.addWidget(self.connect_github_btn)

        # Sync Now button
        self.sync_now_btn = QPushButton("Sync Now")
        self.sync_now_btn.clicked.connect(self._on_sync_now)
        self.sync_now_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
            QPushButton:disabled {{
                background-color: {colors.border_muted};
                color: {colors.text_tertiary};
            }}
        """)
        self.sync_now_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sync_now_btn.setVisible(is_connected)  # Only show when connected
        status_layout.addWidget(self.sync_now_btn)

        # Pull from Server button
        self.pull_btn = QPushButton("Pull from Server")
        self.pull_btn.clicked.connect(self._on_pull_from_server)
        self.pull_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.primary};
                border: 1px solid {colors.primary};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
            }}
            QPushButton:disabled {{
                border-color: {colors.border_muted};
                color: {colors.text_tertiary};
            }}
        """)
        self.pull_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pull_btn.setVisible(is_connected)  # Only show when connected
        self.pull_btn.setToolTip("Download all files from server, overwriting local changes")
        status_layout.addWidget(self.pull_btn)

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
        self.github_repo_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{
                border-color: {colors.primary};
            }}
        """)
        content_layout.addWidget(self.github_repo_field)

        # Auto-sync checkbox
        checkbox_style = f"""
            QCheckBox {{
                color: {colors.text_primary};
                spacing: 8px;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {colors.border_default};
                border-radius: 4px;
                background-color: {colors.bg_elevated};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors.primary};
                border-color: {colors.primary};
            }}
            QCheckBox::indicator:hover {{
                border-color: {colors.primary};
            }}
        """

        self.auto_sync_checkbox = QCheckBox("Auto-sync on changes")
        self.auto_sync_checkbox.setChecked(self.settings.auto_sync)
        self.auto_sync_checkbox.setStyleSheet(checkbox_style)
        content_layout.addWidget(self.auto_sync_checkbox)

        # Sync interval row
        interval_row = QWidget()
        interval_row.setStyleSheet("background-color: transparent;")
        interval_layout = QHBoxLayout(interval_row)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.setSpacing(8)

        interval_label = QLabel("Sync interval:")
        interval_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        interval_layout.addWidget(interval_label)

        self.sync_interval_field = QLineEdit()
        self.sync_interval_field.setText(str(self.settings.sync_interval // 60))
        self.sync_interval_field.setFixedWidth(60)
        self.sync_interval_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 6px 10px;
                text-align: center;
            }}
            QLineEdit:focus {{
                border-color: {colors.primary};
            }}
        """)
        interval_layout.addWidget(self.sync_interval_field)

        minutes_label = QLabel("minutes")
        minutes_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        interval_layout.addWidget(minutes_label)
        interval_layout.addStretch()

        content_layout.addWidget(interval_row)

        # Note
        note = QLabel("Note: Configure GitHub token in your Espanso settings for sync to work")
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
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # Info box
        info_box = QFrame()
        info_box.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_base};
                border: 1px solid {colors.border_muted};
                border-radius: 8px;
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
        checkbox_style = f"""
            QCheckBox {{
                color: {colors.text_primary};
                spacing: 8px;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {colors.border_default};
                border-radius: 4px;
                background-color: {colors.bg_elevated};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors.primary};
                border-color: {colors.primary};
            }}
            QCheckBox::indicator:hover {{
                border-color: {colors.primary};
            }}
        """

        self.hotkeys_enabled_switch = QCheckBox("Enable global hotkeys")
        self.hotkeys_enabled_switch.setChecked(self.settings.hotkeys_enabled)
        self.hotkeys_enabled_switch.setStyleSheet(checkbox_style)
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
        self.minimize_to_tray_checkbox.setStyleSheet(checkbox_style)
        content_layout.addWidget(self.minimize_to_tray_checkbox)

        return self._create_section_card("Hotkeys & Behavior", "\u2328", content)

    def _create_autocomplete_section(self) -> QFrame:
        """Create autocomplete settings section."""
        colors = self.theme_manager.colors

        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # Info box
        info_box = QFrame()
        info_box.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_base};
                border: 1px solid {colors.border_muted};
                border-radius: 8px;
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

        info_text = QLabel("When enabled, typing a trigger character (like :) will show matching entries inline as you type.")
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

        # Enable autocomplete
        checkbox_style = f"""
            QCheckBox {{
                color: {colors.text_primary};
                spacing: 8px;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {colors.border_default};
                border-radius: 4px;
                background-color: {colors.bg_elevated};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors.primary};
                border-color: {colors.primary};
            }}
            QCheckBox::indicator:hover {{
                border-color: {colors.primary};
            }}
        """

        self.autocomplete_enabled_checkbox = QCheckBox("Enable inline autocomplete")
        self.autocomplete_enabled_checkbox.setChecked(self.settings.autocomplete_enabled)
        self.autocomplete_enabled_checkbox.setStyleSheet(checkbox_style)
        content_layout.addWidget(self.autocomplete_enabled_checkbox)

        # Trigger characters
        trigger_label = QLabel("Trigger Characters")
        trigger_label_font = QFont()
        trigger_label_font.setPointSize(10)
        trigger_label_font.setBold(True)
        trigger_label.setFont(trigger_label_font)
        trigger_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(trigger_label)

        # Trigger selection (checkboxes for common triggers)
        triggers_row = QWidget()
        triggers_row.setStyleSheet("background: transparent;")
        triggers_layout = QHBoxLayout(triggers_row)
        triggers_layout.setContentsMargins(0, 0, 0, 0)
        triggers_layout.setSpacing(16)

        current_triggers = self.settings.autocomplete_triggers

        self.trigger_colon = QCheckBox(": (colon)")
        self.trigger_colon.setChecked(":" in current_triggers)
        self.trigger_colon.setStyleSheet(checkbox_style)
        triggers_layout.addWidget(self.trigger_colon)

        self.trigger_semicolon = QCheckBox("; (semicolon)")
        self.trigger_semicolon.setChecked(";" in current_triggers)
        self.trigger_semicolon.setStyleSheet(checkbox_style)
        triggers_layout.addWidget(self.trigger_semicolon)

        self.trigger_slash = QCheckBox("// (double slash)")
        self.trigger_slash.setChecked("//" in current_triggers)
        self.trigger_slash.setStyleSheet(checkbox_style)
        triggers_layout.addWidget(self.trigger_slash)

        triggers_layout.addStretch()
        content_layout.addWidget(triggers_row)

        trigger_help = QLabel("Select which prefix characters trigger the autocomplete popup")
        trigger_help.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(trigger_help)

        # Max suggestions
        max_row = QWidget()
        max_row.setStyleSheet("background: transparent;")
        max_layout = QHBoxLayout(max_row)
        max_layout.setContentsMargins(0, 0, 0, 0)
        max_layout.setSpacing(8)

        max_label = QLabel("Max suggestions:")
        max_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        max_layout.addWidget(max_label)

        self.autocomplete_max_field = QLineEdit()
        self.autocomplete_max_field.setText(str(self.settings.autocomplete_max_suggestions))
        self.autocomplete_max_field.setFixedWidth(50)
        self.autocomplete_max_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 6px 10px;
                text-align: center;
            }}
            QLineEdit:focus {{
                border-color: {colors.primary};
            }}
        """)
        max_layout.addWidget(self.autocomplete_max_field)
        max_layout.addStretch()

        content_layout.addWidget(max_row)

        return self._create_section_card("Inline Autocomplete", "", content)

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
        reply = show_question(
            self.theme_manager,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
            buttons=["Yes", "No"],
            default_button="No",
            parent=self,
        )

        if reply == "Yes":
            # Create new default settings
            self.settings = Settings()
            self.app_state.settings = self.settings

            # Rebuild UI to reflect defaults
            self._rebuild_ui()

            # Notify theme change
            self.theme_changed.emit()

            show_information(
                self.theme_manager,
                "Settings Reset",
                "Settings have been reset to defaults.",
                parent=self,
            )

    def _on_customize_tag_colors(self):
        """Open tag color customization dialog."""
        # Get all unique tags from all entries
        all_entries = self.app_state.entry_manager.get_all_entries()
        all_tags = []
        for entry in all_entries:
            all_tags.extend(entry.tags)

        # Open dialog
        dialog = TagColorDialog(self.theme_manager, all_tags, self)
        dialog.colors_changed.connect(self._on_tag_colors_changed)
        dialog.exec()

    def _on_tag_colors_changed(self):
        """Handle tag color changes - refresh UI to show new colors."""
        # Notify main window to refresh sidebar
        if hasattr(self.parent(), 'sidebar'):
            self.parent().sidebar.refresh_entries()

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

        # Autocomplete
        self.autocomplete_enabled_checkbox.setChecked(self.settings.autocomplete_enabled)
        triggers = self.settings.autocomplete_triggers
        self.trigger_colon.setChecked(":" in triggers)
        self.trigger_semicolon.setChecked(";" in triggers)
        self.trigger_slash.setChecked("//" in triggers)
        self.autocomplete_max_field.setText(str(self.settings.autocomplete_max_suggestions))

    def _on_pull_from_server(self):
        """Handle Pull from Server button click."""
        # Confirm with user
        reply = show_question(
            self.theme_manager,
            "Pull from Server",
            "This will download all configuration files from the server and overwrite any local changes.\n\nAre you sure you want to continue?",
            buttons=["Yes", "No"],
            default_button="No",
            parent=self,
        )

        if reply != "Yes":
            return

        # Check if sync is configured
        if not self.app_state.sync_manager:
            show_information(
                self.theme_manager,
                "Sync Not Configured",
                "GitHub sync is not configured. Click 'Connect to GitHub' to set it up.",
                parent=self,
            )
            return

        # Disable buttons during pull
        self.sync_now_btn.setEnabled(False)
        self.pull_btn.setEnabled(False)
        self.pull_btn.setText("Pulling...")

        try:
            # Perform pull
            result = self.app_state.sync_manager.pull(force=True)

            file_count = len(result)

            # Import the pulled files into the database (clear existing entries first)
            imported_count = self.app_state.entry_manager.import_from_espanso(clear_existing=True)

            # Refresh all UI components
            if hasattr(self.parent(), 'sidebar'):
                self.parent().sidebar.refresh_entries()
            if hasattr(self.parent(), 'status_bar'):
                self.parent().status_bar.update_entry_count()
            if hasattr(self.parent(), 'dashboard'):
                self.parent().dashboard.refresh_stats()

            show_information(
                self.theme_manager,
                "Pull Complete",
                f"Successfully downloaded {file_count} file(s) from server and imported {imported_count} entries.",
                parent=self,
            )
        except Exception as ex:
            show_critical(
                self.theme_manager,
                "Pull Error",
                f"Error during pull: {str(ex)}",
                parent=self,
            )
        finally:
            # Re-enable buttons
            self.sync_now_btn.setEnabled(True)
            self.pull_btn.setEnabled(True)
            self.pull_btn.setText("Pull from Server")

    def _on_sync_now(self):
        """Handle Sync Now button click."""
        # Check if sync is configured
        if not self.app_state.sync_manager:
            # Try to initialize if settings are available
            settings = self.app_state.settings
            if settings.github_repo and settings.github_token:
                self._initialize_sync_manager()
                if not self.app_state.sync_manager:
                    return  # Initialization failed, message already shown
            else:
                show_information(
                    self.theme_manager,
                    "Sync Not Configured",
                    "GitHub sync is not configured. Click 'Connect to GitHub' to set it up.",
                    parent=self,
                )
                return

        # Disable button during sync
        self.sync_now_btn.setEnabled(False)
        self.sync_now_btn.setText("Syncing...")

        try:
            # Perform sync
            result = self.app_state.sync_manager.sync()

            if result.get("success"):
                # Import any pulled files into the database
                if result.get('pulled', 0) > 0:
                    imported_count = self.app_state.entry_manager.import_from_espanso()

                    # Refresh all UI components
                    if hasattr(self.parent(), 'sidebar'):
                        self.parent().sidebar.refresh_entries()
                    if hasattr(self.parent(), 'status_bar'):
                        self.parent().status_bar.update_entry_count()
                    if hasattr(self.parent(), 'dashboard'):
                        self.parent().dashboard.refresh_stats()

                show_information(
                    self.theme_manager,
                    "Sync Complete",
                    f"Sync completed successfully.\n\nPulled: {result.get('pulled', 0)} changes\nPushed: {result.get('pushed', 0)} changes",
                    parent=self,
                )
            else:
                show_warning(
                    self.theme_manager,
                    "Sync Failed",
                    f"Sync failed: {result.get('error', 'Unknown error')}",
                    parent=self,
                )
        except Exception as ex:
            show_critical(
                self.theme_manager,
                "Sync Error",
                f"Error during sync: {str(ex)}",
                parent=self,
            )
        finally:
            # Re-enable button
            self.sync_now_btn.setEnabled(True)
            self.sync_now_btn.setText("Sync Now")

    def _on_connect_github(self):
        """Open GitHub connection wizard."""
        self._github_wizard = GitHubWizard(self.theme_manager, self)
        self._github_wizard.connection_saved.connect(self._on_github_connection_saved)
        self._github_wizard.show_centered()

    def _on_github_connection_saved(self):
        """Handle GitHub connection saved."""
        # Reload settings
        self.settings = self.app_state.settings

        # Update the repository field
        self.github_repo_field.setText(self.settings.github_repo or "")

        # Update the auto-sync checkbox
        self.auto_sync_checkbox.setChecked(self.settings.auto_sync)

        # Update UI state to show sync buttons
        self.sync_now_btn.setVisible(True)
        self.pull_btn.setVisible(True)
        self.connect_github_btn.setText("Settings")

        # Initialize sync manager
        self._initialize_sync_manager(show_success_message=True)

    def _initialize_sync_manager(self, show_success_message: bool = False):
        """Initialize or reinitialize the sync manager with current settings.

        Args:
            show_success_message: If True, show a message box on successful connection.
        """
        from pathlib import Path

        try:
            from espanded.sync import SyncManager
        except ImportError:
            show_warning(
                self.theme_manager,
                "Sync Not Available",
                "Sync functionality is not available. Please install httpx.",
                parent=self,
            )
            return

        settings = self.app_state.settings

        if not settings.github_repo or not settings.github_token:
            return

        try:
            # Determine espanso config path
            if settings.espanso_config_path:
                local_path = Path(settings.espanso_config_path)
            else:
                # Default espanso config path
                import platform
                if platform.system() == "Windows":
                    local_path = Path.home() / "AppData" / "Roaming" / "espanso"
                else:
                    local_path = Path.home() / ".config" / "espanso"

            # Create sync manager
            sync_manager = SyncManager(
                repo=settings.github_repo,
                token=settings.github_token,
                local_path=local_path,
                on_conflict=None,
            )

            # Test connection
            if sync_manager.test_connection():
                self.app_state.sync_manager = sync_manager
                if show_success_message:
                    show_information(
                        self.theme_manager,
                        "Connected",
                        f"Successfully connected to GitHub!\n\nRepository: {settings.github_repo}\n\nYou can now use Sync Now.",
                        parent=self,
                    )
            else:
                show_warning(
                    self.theme_manager,
                    "Connection Failed",
                    "Could not connect to GitHub. Please check your token and repository.",
                    parent=self,
                )

        except Exception as e:
            show_critical(
                self.theme_manager,
                "Error",
                f"Failed to initialize sync: {str(e)}",
                parent=self,
            )

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

            # Autocomplete settings
            self.settings.autocomplete_enabled = self.autocomplete_enabled_checkbox.isChecked()

            # Build trigger list from checkboxes
            triggers = []
            if self.trigger_colon.isChecked():
                triggers.append(":")
            if self.trigger_semicolon.isChecked():
                triggers.append(";")
            if self.trigger_slash.isChecked():
                triggers.append("//")
            # Default to colon if nothing selected
            if not triggers:
                triggers = [":"]
            self.settings.autocomplete_triggers = triggers

            # Parse max suggestions
            try:
                max_suggestions = int(self.autocomplete_max_field.text())
                self.settings.autocomplete_max_suggestions = max(1, min(max_suggestions, 20))
            except ValueError:
                self.settings.autocomplete_max_suggestions = 8

            # Update hotkey service if settings changed
            from espanded.services.hotkey_service import get_hotkey_service

            hotkey_service = get_hotkey_service()
            if hotkey_service and hotkey_service.is_running:
                hotkey_service.update_hotkey(self.settings.quick_add_hotkey)
                if self.settings.hotkeys_enabled:
                    hotkey_service.enable()
                else:
                    hotkey_service.disable()

            # Update autocomplete service if settings changed
            from espanded.services.autocomplete_service import get_autocomplete_service

            autocomplete_service = get_autocomplete_service()
            if autocomplete_service:
                autocomplete_service.update_settings()

            # Save to database
            self.app_state.settings = self.settings

            # Emit signals
            self.settings_saved.emit()
            if theme_changed:
                self.theme_changed.emit()

            show_information(
                self.theme_manager,
                "Settings Saved",
                "Settings saved successfully.",
                parent=self,
            )

        except Exception as ex:
            show_critical(
                self.theme_manager,
                "Error",
                f"Error saving settings: {str(ex)}",
                parent=self,
            )
