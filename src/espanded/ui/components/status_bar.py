"""Status bar component showing sync status and entry count."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt

from espanded.ui.theme import ThemeManager
from espanded.core.app_state import get_app_state


class StatusBar(QWidget):
    """Bottom status bar with sync status and entry count."""

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.app_state = get_app_state()
        self.setFixedHeight(28)
        self._setup_ui()

    def _setup_ui(self):
        """Build the status bar layout."""
        colors = self.theme_manager.colors

        # Set background
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_sidebar};
                border-top: 1px solid {colors.border_muted};
            }}
            QLabel {{
                color: {colors.text_secondary};
                font-size: 12px;
                background-color: transparent;
                padding: 0px 4px;
            }}
        """)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        # Left side: Sync status
        self.sync_status_label = QLabel("\u2713 Synced")  # Checkmark
        self.sync_status_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.success};
            }}
        """)
        layout.addWidget(self.sync_status_label)

        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addItem(spacer)

        # Right side: Entry count
        self.entry_count_label = QLabel("0 entries")
        layout.addWidget(self.entry_count_label)

    def update_sync_status(self, status: str, is_syncing: bool = False):
        """Update sync status display.

        Args:
            status: Status message to display
            is_syncing: Whether sync is currently in progress
        """
        colors = self.theme_manager.colors

        if is_syncing:
            self.sync_status_label.setText(f"\u21bb {status}")  # Circular arrow
            self.sync_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors.info};
                }}
            """)
        elif "error" in status.lower() or "failed" in status.lower():
            self.sync_status_label.setText(f"\u2715 {status}")  # X mark
            self.sync_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors.error};
                }}
            """)
        else:
            self.sync_status_label.setText(f"\u2713 {status}")  # Checkmark
            self.sync_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors.success};
                }}
            """)

    def update_entry_count(self, count: int | None = None):
        """Update entry count display.

        Args:
            count: Number of entries, or None to fetch from entry manager
        """
        if count is None:
            try:
                count = len(self.app_state.entry_manager.get_all_entries())
            except Exception:
                count = 0

        plural = "entries" if count != 1 else "entry"
        self.entry_count_label.setText(f"{count} {plural}")
