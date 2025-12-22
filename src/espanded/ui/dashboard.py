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
    sync_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.app_state = get_app_state()
        self._setup_ui()

    def _setup_ui(self):
        """Build the dashboard layout."""
        colors = self.theme_manager.colors

        # Set background
        self.setStyleSheet(f"background-color: {colors.bg_base};")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = self._create_content()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

    def _create_header(self) -> QWidget:
        """Create dashboard header."""
        colors = self.theme_manager.colors

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # Title
        title = QLabel("Dashboard")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 600;
            color: {colors.text_primary};
            background: transparent;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        return header

    def _create_content(self) -> QWidget:
        """Create scrollable dashboard content."""
        colors = self.theme_manager.colors

        content = QWidget()
        content.setStyleSheet(f"background-color: {colors.bg_base};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(24)

        # Stats cards row
        stats_row = QWidget()
        stats_layout = QHBoxLayout(stats_row)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(16)

        # Get stats
        stats_data = self.app_state.entry_manager.get_stats()

        # Create stat cards
        self.stat_cards = []
        stat_items = [
            ("Total Entries", str(stats_data.get("total_entries", 0)), colors.primary),
            ("Active Tags", str(stats_data.get("tag_count", 0)), colors.success),
            ("Created Today", str(stats_data.get("created_today", 0)), colors.warning),
            ("Modified Today", str(stats_data.get("modified_today", 0)), colors.info),
        ]

        for label, value, accent_color in stat_items:
            card = self._create_stat_card(label, value, accent_color)
            stats_layout.addWidget(card, stretch=1)
            self.stat_cards.append(card)

        content_layout.addWidget(stats_row)

        # Second row: Sync Status and Tips
        row2 = QWidget()
        row2_layout = QHBoxLayout(row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(16)

        self.sync_card = self._create_sync_card()
        row2_layout.addWidget(self.sync_card, stretch=1)

        tips_card = self._create_tips_card()
        row2_layout.addWidget(tips_card, stretch=1)

        content_layout.addWidget(row2)

        content_layout.addStretch()
        return content

    def _create_stat_card(self, label: str, value: str, accent_color: str) -> QFrame:
        """Create a single stat card."""
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
        layout.setSpacing(8)

        # Value (big number)
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {accent_color};
            background: transparent;
        """)
        layout.addWidget(value_label)

        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: 13px;
            color: {colors.text_secondary};
            background: transparent;
        """)
        layout.addWidget(label_widget)

        return card

    def _create_sync_card(self) -> QFrame:
        """Create sync status card."""
        colors = self.theme_manager.colors

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_surface};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("GitHub Sync")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {colors.text_primary};
            background: transparent;
        """)
        layout.addWidget(title)

        # Get sync status
        settings = self.app_state.settings
        is_connected = bool(settings.github_repo and settings.github_token)

        # Status indicator
        status_row = QWidget()
        status_row.setStyleSheet("background: transparent;")
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)

        status_dot = QLabel("●")
        status_color = colors.success if is_connected else colors.text_tertiary
        status_dot.setStyleSheet(f"font-size: 12px; color: {status_color}; background: transparent;")
        status_layout.addWidget(status_dot)

        status_text = QLabel("Connected" if is_connected else "Not configured")
        status_text.setStyleSheet(f"font-size: 13px; color: {status_color}; background: transparent;")
        status_layout.addWidget(status_text)
        status_layout.addStretch()

        layout.addWidget(status_row)

        # Repository info
        repo_name = settings.github_repo or "No repository set"
        repo_label = QLabel(repo_name)
        repo_label.setStyleSheet(f"""
            font-size: 12px;
            color: {colors.text_secondary};
            background: transparent;
        """)
        layout.addWidget(repo_label)

        # Last sync
        last_sync = "Never"
        if settings.last_sync:
            try:
                last_sync = settings.last_sync.strftime("%b %d, %I:%M %p")
            except Exception:
                pass
        sync_label = QLabel(f"Last sync: {last_sync}")
        sync_label.setStyleSheet(f"""
            font-size: 12px;
            color: {colors.text_tertiary};
            background: transparent;
        """)
        layout.addWidget(sync_label)

        # Action button
        layout.addStretch()
        self.sync_button = QPushButton()
        if is_connected:
            self.sync_button.setText("Sync Now")
            self.sync_button.clicked.connect(self.sync_clicked.emit)
        else:
            self.sync_button.setText("Configure Sync")
            self.sync_button.clicked.connect(self.settings_clicked.emit)
        self.sync_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.sync_button)

        return card

    def _create_tips_card(self) -> QFrame:
        """Create quick tips card."""
        colors = self.theme_manager.colors

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_surface};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Quick Tips")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {colors.text_primary};
            background: transparent;
        """)
        layout.addWidget(title)

        tips = [
            ("Ctrl+Shift+E", "Quick add from selected text"),
            ("Use {{ in text", "Insert variables and forms"),
            ("Add tags", "Organize entries for easy filtering"),
            ("Prefix options", "Use :, ;, //, :: or blank"),
        ]

        for shortcut, description in tips:
            tip = self._create_tip_item(shortcut, description)
            layout.addWidget(tip)

        layout.addStretch()
        return card

    def _create_tip_item(self, shortcut: str, description: str) -> QWidget:
        """Create a single tip item."""
        colors = self.theme_manager.colors

        item = QWidget()
        item.setStyleSheet("background: transparent;")
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(0, 4, 0, 4)
        item_layout.setSpacing(12)

        # Shortcut badge - use border instead of background
        shortcut_label = QLabel(shortcut)
        shortcut_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {colors.primary};
            background-color: transparent;
            border: 1px solid {colors.primary};
            border-radius: 4px;
            padding: 4px 8px;
        """)
        item_layout.addWidget(shortcut_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"""
            font-size: 13px;
            color: {colors.text_secondary};
            background: transparent;
        """)
        item_layout.addWidget(desc_label, stretch=1)

        return item

    def refresh_stats(self):
        """Refresh dashboard statistics."""
        # Get fresh stats
        stats_data = self.app_state.entry_manager.get_stats()
        colors = self.theme_manager.colors

        stat_values = [
            str(stats_data.get("total_entries", 0)),
            str(stats_data.get("tag_count", 0)),
            str(stats_data.get("created_today", 0)),
            str(stats_data.get("modified_today", 0)),
        ]

        # Update stat card values
        for i, card in enumerate(self.stat_cards):
            if i < len(stat_values):
                # Find the value label (first QLabel in the card)
                for child in card.findChildren(QLabel):
                    if child.styleSheet() and "font-size: 32px" in child.styleSheet():
                        child.setText(stat_values[i])
                        break
