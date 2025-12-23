"""History view showing entry change log."""

from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from espanded.ui.theme import ThemeManager
from espanded.ui.components.message_dialog import (
    show_information,
    show_warning,
)
from espanded.core.app_state import get_app_state
from espanded.core.models import HistoryEntry


class HistoryView(QWidget):
    """History view showing entry change log with filtering."""

    # Signals
    close_requested = Signal()
    entry_restored = Signal(str)  # Emits entry_id

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.app_state = get_app_state()

        # State
        self.filter_action = "all"
        self.search_query = ""

        self._setup_ui()

    def _setup_ui(self):
        """Build the history view layout."""
        colors = self.theme_manager.colors

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Filter and search bar
        filter_bar = self._create_filter_bar()
        layout.addWidget(filter_bar)

        # Scrollable history list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors.bg_base};
                border: none;
            }}
        """)

        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(20, 0, 20, 20)
        self.history_layout.setSpacing(0)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.history_container)
        layout.addWidget(scroll, stretch=1)

    def _create_header(self) -> QWidget:
        """Create history header."""
        colors = self.theme_manager.colors

        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_base};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 16)

        # Icon and title
        title_row = QWidget()
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)

        # Title without icon for cross-platform compatibility

        title = QLabel("History")
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
        close_btn = QPushButton("\u2715")
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

    def _create_filter_bar(self) -> QWidget:
        """Create filter and search bar."""
        colors = self.theme_manager.colors

        filter_bar = QWidget()
        filter_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_base};
                border-bottom: 1px solid {colors.border_muted};
            }}
        """)
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(20, 0, 20, 16)
        filter_layout.setSpacing(12)

        # Filter dropdown
        self.filter_dropdown = QComboBox()
        self.filter_dropdown.addItem("All changes", "all")
        self.filter_dropdown.addItem("Created", "created")
        self.filter_dropdown.addItem("Modified", "modified")
        self.filter_dropdown.addItem("Deleted", "deleted")
        self.filter_dropdown.addItem("Restored", "restored")
        self.filter_dropdown.currentIndexChanged.connect(self._on_filter_change)
        self.filter_dropdown.setFixedWidth(200)
        filter_layout.addWidget(self.filter_dropdown)

        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by trigger name...")
        self.search_field.textChanged.connect(self._on_search_change)
        filter_layout.addWidget(self.search_field, stretch=1)

        return filter_bar

    def _on_filter_change(self):
        """Handle filter dropdown change."""
        self.filter_action = self.filter_dropdown.currentData()
        self._refresh_history()

    def _on_search_change(self, text: str):
        """Handle search field change."""
        self.search_query = text.lower()
        self._refresh_history()

    def _refresh_history(self):
        """Refresh the history list."""
        colors = self.theme_manager.colors

        # Clear existing items
        while self.history_layout.count():
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Get history entries
        all_history = self.app_state.database.get_history(limit=200)

        # Filter by action type
        if self.filter_action != "all":
            all_history = [h for h in all_history if h.action == self.filter_action]

        # Filter by search query
        if self.search_query:
            all_history = [
                h for h in all_history
                if self.search_query in h.trigger_name.lower()
            ]

        # Group by date
        grouped = self._group_by_date(all_history)

        if not grouped:
            # Empty state
            self._show_empty_state()
            return

        # Build list
        for date_label, entries in grouped:
            # Date header
            date_header = QLabel(date_label)
            date_font = QFont()
            date_font.setPointSize(11)
            date_font.setBold(True)
            date_header.setFont(date_font)
            date_header.setStyleSheet(f"""
                QLabel {{
                    color: {colors.text_primary};
                    background-color: transparent;
                    margin-top: 16px;
                    margin-bottom: 8px;
                }}
            """)
            self.history_layout.addWidget(date_header)

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
            self.history_layout.addWidget(divider)

            # History items
            for history_entry in entries:
                item = self._build_history_item(history_entry)
                self.history_layout.addWidget(item)

    def _group_by_date(self, history: list[HistoryEntry]) -> list[tuple[str, list[HistoryEntry]]]:
        """Group history entries by date."""
        now = datetime.now()
        today = now.date()
        yesterday = (now - timedelta(days=1)).date()

        groups: dict[str, list[HistoryEntry]] = {}

        for entry in history:
            entry_date = entry.timestamp.date()

            if entry_date == today:
                label = "Today"
            elif entry_date == yesterday:
                label = "Yesterday"
            else:
                label = entry.timestamp.strftime("%b %d, %Y")

            if label not in groups:
                groups[label] = []
            groups[label].append(entry)

        # Return in order: Today, Yesterday, then chronological
        result = []
        if "Today" in groups:
            result.append(("Today", groups["Today"]))
        if "Yesterday" in groups:
            result.append(("Yesterday", groups["Yesterday"]))

        # Add other dates in reverse chronological order
        other_dates = [
            (label, entries)
            for label, entries in groups.items()
            if label not in ["Today", "Yesterday"]
        ]
        other_dates.sort(key=lambda x: x[1][0].timestamp, reverse=True)
        result.extend(other_dates)

        return result

    def _build_history_item(self, history: HistoryEntry) -> QFrame:
        """Build a single history item."""
        colors = self.theme_manager.colors

        # Get action info
        action_info = self._get_action_info(history.action)
        icon = action_info["icon"]
        icon_color = action_info["color"]
        action_text = action_info["text"]

        # Format timestamp
        time_str = history.timestamp.strftime("%I:%M %p")

        # Build item
        item = QFrame()
        item.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_surface};
                border: 1px solid {colors.border_muted};
                border-radius: 8px;
                margin-bottom: 4px;
                padding: 12px;
            }}
        """)
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(8, 8, 8, 8)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                color: {icon_color};
                background-color: transparent;
            }}
        """)
        item_layout.addWidget(icon_label)

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)

        # First row: time and action
        first_row = QWidget()
        first_layout = QHBoxLayout(first_row)
        first_layout.setContentsMargins(0, 0, 0, 0)

        time_label = QLabel(f"{time_str} - {action_text} ")
        time_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {colors.text_primary};
                font-weight: 500;
                background-color: transparent;
            }}
        """)
        first_layout.addWidget(time_label)

        trigger_label = QLabel(history.trigger_name)
        trigger_font = QFont()
        trigger_font.setBold(True)
        trigger_label.setFont(trigger_font)
        trigger_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {colors.primary};
                background-color: transparent;
            }}
        """)
        first_layout.addWidget(trigger_label)
        first_layout.addStretch()

        content_layout.addWidget(first_row)

        # Action buttons
        if history.action == "deleted":
            button_row = QWidget()
            button_layout = QHBoxLayout(button_row)
            button_layout.setContentsMargins(0, 4, 0, 0)
            button_layout.setSpacing(8)

            restore_btn = QPushButton("\u21BA Restore")
            restore_btn.clicked.connect(lambda: self._restore_entry(history.entry_id))
            restore_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.success};
                    color: {colors.text_inverse};
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
            """)
            restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            button_layout.addWidget(restore_btn)
            button_layout.addStretch()

            content_layout.addWidget(button_row)

        item_layout.addWidget(content, stretch=1)

        return item

    def _get_action_info(self, action: str) -> dict:
        """Get icon, color, and text for an action."""
        colors = self.theme_manager.colors

        action_map = {
            "created": {
                "icon": "\u2795",  # Plus
                "color": colors.success,
                "text": "Created",
            },
            "modified": {
                "icon": "\u270F",  # Pencil
                "color": colors.info,
                "text": "Modified",
            },
            "deleted": {
                "icon": "\u2716",  # X
                "color": colors.error,
                "text": "Deleted",
            },
            "restored": {
                "icon": "\u21BA",  # Counterclockwise arrow
                "color": colors.warning,
                "text": "Restored",
            },
        }

        return action_map.get(action, {
            "icon": "\u25CF",  # Circle
            "color": colors.text_secondary,
            "text": action.capitalize(),
        })

    def _show_empty_state(self):
        """Show empty state message."""
        colors = self.theme_manager.colors

        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(8)

        msg_label = QLabel("No history found")
        msg_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(msg_label)

        desc_label = QLabel("Changes to entries will appear here")
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(desc_label)

        self.history_layout.addWidget(empty)

    def _restore_entry(self, entry_id: str):
        """Restore a deleted entry."""
        success = self.app_state.entry_manager.restore_entry(entry_id)

        if success:
            self.entry_restored.emit(entry_id)
            self._refresh_history()
            show_information(
                self.theme_manager,
                "Entry Restored",
                "Entry has been restored successfully.",
                parent=self,
            )
        else:
            show_warning(
                self.theme_manager,
                "Restore Failed",
                "Failed to restore entry.",
                parent=self,
            )

    def refresh(self):
        """Refresh the history view."""
        self._refresh_history()
