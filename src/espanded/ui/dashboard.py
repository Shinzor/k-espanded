"""Dashboard panel showing statistics, sync status, and quick tips."""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QGridLayout,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from espanded.ui.theme import ThemeManager
from espanded.core.app_state import get_app_state


class Dashboard(QWidget):
    """Dashboard panel with statistics and quick tips."""

    # Signals
    sync_clicked = Signal()  # Emitted when sync button is clicked
    settings_clicked = Signal()  # Emitted when configure sync button is clicked

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.app_state = get_app_state()
        self._setup_ui()

    def _setup_ui(self):
        """Build the dashboard layout."""
        colors = self.theme_manager.colors

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = self._create_header()
        layout.addWidget(header)

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
        layout.addWidget(scroll)

    def _create_header(self) -> QWidget:
        """Create dashboard header."""
        colors = self.theme_manager.colors

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Icon
        icon_label = QLabel("\u1F4CA")  # Dashboard emoji
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                color: {colors.primary};
                background-color: transparent;
            }}
        """)
        header_layout.addWidget(icon_label)

        # Title
        title = QLabel("Dashboard")
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
        header_layout.addWidget(title)
        header_layout.addStretch()

        return header

    def _create_content(self) -> QWidget:
        """Create scrollable dashboard content."""
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # First row: Statistics and Sync Status
        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(16)

        self.stats_card = self._create_stats_card()
        row1_layout.addWidget(self.stats_card, stretch=1)

        self.sync_card = self._create_sync_card()
        row1_layout.addWidget(self.sync_card, stretch=1)

        content_layout.addWidget(row1)

        # Second row: Quick Tips
        tips_card = self._create_tips_card()
        content_layout.addWidget(tips_card)

        content_layout.addStretch()

        return content

    def _create_card(self, title: str, icon: str, content_widget: QWidget) -> QFrame:
        """Create a card container."""
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header with icon and title
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # Icon
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 18px;
                    color: {colors.primary};
                    background-color: transparent;
                }}
            """)
            header_layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(11)
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

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.border_muted};
                border: none;
                max-height: 1px;
            }}
        """)
        layout.addWidget(divider)

        # Content
        layout.addWidget(content_widget)

        return card

    def _create_stats_card(self) -> QFrame:
        """Create statistics card."""
        colors = self.theme_manager.colors

        # Get real stats
        stats_data = self.app_state.entry_manager.get_stats()

        # Format last modified
        last_modified = stats_data.get("last_modified")
        if last_modified:
            try:
                dt = datetime.fromisoformat(last_modified)
                last_modified_str = dt.strftime("%b %d, %I:%M %p")
            except Exception:
                last_modified_str = "Unknown"
        else:
            last_modified_str = "Never"

        # Format entries today
        entries_today = stats_data.get("created_today", 0)
        modified_today = stats_data.get("modified_today", 0)
        today_str = f"{entries_today} new" if entries_today else "None"
        if modified_today > entries_today:
            today_str += f", {modified_today - entries_today} modified"

        stats = [
            ("\u1F4DD", "Total Entries", str(stats_data.get("total_entries", 0))),
            ("\u1F3F7", "Active Tags", str(stats_data.get("tag_count", 0))),
            ("\u23F0", "Last Modified", last_modified_str),
            ("\u1F4C5", "Entries Today", today_str),
        ]

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        for icon, label, value in stats:
            stat_widget = self._create_stat_item(icon, label, value)
            content_layout.addWidget(stat_widget)

        return self._create_card("Statistics", "\u1F4CA", content)

    def _create_stat_item(self, icon: str, label: str, value: str) -> QWidget:
        """Create a single stat item."""
        colors = self.theme_manager.colors

        item = QWidget()
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(0, 8, 0, 8)
        item_layout.setSpacing(12)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        item_layout.addWidget(icon_label)

        # Label and value
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        text_layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(11)
        value_font.setBold(True)
        value_widget.setFont(value_font)
        value_widget.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        text_layout.addWidget(value_widget)

        item_layout.addWidget(text_widget)
        item_layout.addStretch()

        return item

    def _create_sync_card(self) -> QFrame:
        """Create sync status card."""
        colors = self.theme_manager.colors

        # Get real sync status
        settings = self.app_state.settings
        is_connected = bool(settings.github_repo and settings.github_token)

        last_sync = "Never"
        if settings.last_sync:
            try:
                last_sync = settings.last_sync.strftime("%b %d, %I:%M %p")
            except Exception:
                pass

        repo_name = settings.github_repo or "Not configured"

        status_icon = "\u2713" if is_connected else "\u2601"  # Checkmark or Cloud
        status_text = "Connected" if is_connected else "Not connected"
        status_color = colors.success if is_connected else colors.text_tertiary

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Status row
        status_row = QWidget()
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)

        status_icon_label = QLabel(status_icon)
        status_icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
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

        # Info section
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 8, 0, 0)
        info_layout.setSpacing(4)

        repo_label = QLabel(f"Repository: {repo_name}")
        repo_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        info_layout.addWidget(repo_label)

        sync_label = QLabel(f"Last sync: {last_sync}")
        sync_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        info_layout.addWidget(sync_label)

        content_layout.addWidget(info_widget)

        # Action button
        self.sync_button = QPushButton()
        if is_connected:
            self.sync_button.setText("\u21BB Sync Now")
            self.sync_button.clicked.connect(self.sync_clicked.emit)
        else:
            self.sync_button.setText("\u2699 Configure Sync")
            self.sync_button.clicked.connect(self.settings_clicked.emit)

        self.sync_button.setStyleSheet(f"""
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
        self.sync_button.setCursor(Qt.CursorShape.PointingHandCursor)
        content_layout.addWidget(self.sync_button)

        return self._create_card("Sync Status", "\u21BB", content)

    def _create_tips_card(self) -> QFrame:
        """Create quick tips card."""
        colors = self.theme_manager.colors

        tips = [
            ("Select text + Ctrl+Shift+E", "Quickly create a new entry from selected text"),
            ("Type {{ in replacement", "Insert variables, forms, and scripts"),
            ("Use tags", "Organize and filter your entries efficiently"),
            ("Prefix options", "Use :, ;, //, :: or blank for different trigger styles"),
        ]

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        for shortcut, description in tips:
            tip_widget = self._create_tip_item(shortcut, description)
            content_layout.addWidget(tip_widget)

        return self._create_card("Quick Tips", "\u1F4A1", content)

    def _create_tip_item(self, shortcut: str, description: str) -> QWidget:
        """Create a single tip item."""
        colors = self.theme_manager.colors

        item = QWidget()
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(0, 6, 0, 6)
        item_layout.setSpacing(12)

        # Lightbulb icon
        icon_label = QLabel("\u1F4A1")
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {colors.warning};
                background-color: transparent;
            }}
        """)
        item_layout.addWidget(icon_label)

        # Text
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        shortcut_label = QLabel(shortcut)
        shortcut_font = QFont()
        shortcut_font.setPointSize(10)
        shortcut_font.setBold(True)
        shortcut_label.setFont(shortcut_font)
        shortcut_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        text_layout.addWidget(shortcut_label)

        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)

        item_layout.addWidget(text_widget, stretch=1)

        return item

    def refresh_stats(self):
        """Refresh dashboard statistics."""
        # Rebuild stats and sync cards
        old_stats = self.stats_card
        old_sync = self.sync_card

        # Find parent layout (row1_layout)
        parent = old_stats.parent()
        if parent:
            layout = parent.layout()
            if layout:
                # Remove old widgets
                layout.removeWidget(old_stats)
                layout.removeWidget(old_sync)
                old_stats.deleteLater()
                old_sync.deleteLater()

                # Create new widgets
                self.stats_card = self._create_stats_card()
                layout.insertWidget(0, self.stats_card, stretch=1)

                self.sync_card = self._create_sync_card()
                layout.insertWidget(1, self.sync_card, stretch=1)
