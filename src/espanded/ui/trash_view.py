"""Trash view showing deleted entries with restore functionality."""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QScrollArea,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from espanded.ui.theme import ThemeManager
from espanded.core.app_state import get_app_state
from espanded.core.models import Entry


class TrashView(QWidget):
    """Trash view showing deleted entries with restore and permanent delete."""

    # Signals
    close_requested = Signal()
    entry_restored = Signal(str)  # Emits entry_id

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.app_state = get_app_state()

        # State
        self.search_query = ""

        self._setup_ui()

    def _setup_ui(self):
        """Build the trash view layout."""
        colors = self.theme_manager.colors

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Toolbar (search and empty trash button)
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Scrollable trash list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors.bg_base};
                border: none;
            }}
        """)

        self.trash_container = QWidget()
        self.trash_layout = QVBoxLayout(self.trash_container)
        self.trash_layout.setContentsMargins(20, 16, 20, 20)
        self.trash_layout.setSpacing(8)
        self.trash_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.trash_container)
        layout.addWidget(scroll, stretch=1)

    def _create_header(self) -> QWidget:
        """Create trash header."""
        colors = self.theme_manager.colors

        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_base};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 16)

        # Icon, title, and count
        title_row = QWidget()
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)

        # Title without icon for cross-platform compatibility

        title = QLabel("Trash")
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

        self.trash_count = QLabel("")
        self.trash_count.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        title_layout.addWidget(self.trash_count)

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

    def _create_toolbar(self) -> QWidget:
        """Create search and empty trash toolbar."""
        colors = self.theme_manager.colors

        toolbar = QWidget()
        toolbar.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_base};
                border-bottom: 1px solid {colors.border_muted};
            }}
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 0, 20, 16)
        toolbar_layout.setSpacing(12)

        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search deleted entries...")
        self.search_field.textChanged.connect(self._on_search_change)
        toolbar_layout.addWidget(self.search_field, stretch=1)

        # Empty trash button
        self.empty_trash_button = QPushButton("Empty Trash")
        self.empty_trash_button.clicked.connect(self._on_empty_trash)
        self.empty_trash_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.error};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: {colors.border_muted};
                color: {colors.text_tertiary};
            }}
        """)
        self.empty_trash_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toolbar_layout.addWidget(self.empty_trash_button)

        return toolbar

    def _on_search_change(self, text: str):
        """Handle search field change."""
        self.search_query = text.lower()
        self._refresh_trash()

    def _refresh_trash(self):
        """Refresh the trash list."""
        colors = self.theme_manager.colors

        # Clear existing items
        while self.trash_layout.count():
            child = self.trash_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Get deleted entries
        all_deleted = self.app_state.entry_manager.get_deleted_entries()

        # Filter by search query
        if self.search_query:
            all_deleted = [
                e for e in all_deleted
                if self.search_query in e.trigger.lower()
                or self.search_query in e.replacement.lower()
            ]

        # Update count
        count = len(all_deleted)
        self.trash_count.setText(f"({count} item{'s' if count != 1 else ''})")

        # Update empty trash button state
        self.empty_trash_button.setEnabled(count > 0)

        if not all_deleted:
            # Empty state
            self._show_empty_state()
            return

        # Build list
        for entry in all_deleted:
            item = self._build_trash_item(entry)
            self.trash_layout.addWidget(item)

    def _build_trash_item(self, entry: Entry) -> QFrame:
        """Build a single trash item."""
        colors = self.theme_manager.colors

        # Format deleted date
        if entry.deleted_at:
            deleted_str = entry.deleted_at.strftime("%b %d, %Y at %I:%M %p")
        else:
            deleted_str = "Unknown"

        # Truncate replacement preview
        preview = entry.replacement
        if len(preview) > 80:
            preview = preview[:80] + "..."

        # Build item
        item = QFrame()
        item.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_surface};
                border: 1px solid {colors.border_muted};
                border-radius: 12px;
            }}
        """)
        item_layout = QVBoxLayout(item)
        item_layout.setContentsMargins(20, 20, 20, 20)
        item_layout.setSpacing(0)

        # Header row: trigger and deleted date
        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)

        trigger_label = QLabel(entry.full_trigger)
        trigger_font = QFont()
        trigger_font.setPointSize(12)
        trigger_font.setBold(True)
        trigger_label.setFont(trigger_font)
        trigger_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        header_layout.addWidget(trigger_label)
        header_layout.addStretch()

        deleted_label = QLabel(f"Deleted: {deleted_str}")
        deleted_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        header_layout.addWidget(deleted_label)

        item_layout.addWidget(header_row)

        # Replacement preview
        if preview:
            preview_label = QLabel(preview)
            preview_label.setWordWrap(True)
            preview_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 13px;
                    color: {colors.text_secondary};
                    background-color: transparent;
                    margin-top: 4px;
                    margin-bottom: 12px;
                }}
            """)
            item_layout.addWidget(preview_label)

        # Tags (if any)
        if entry.tags:
            tags_row = QWidget()
            tags_layout = QHBoxLayout(tags_row)
            tags_layout.setContentsMargins(0, 0, 0, 12)
            tags_layout.setSpacing(4)

            for tag in entry.tags:
                tag_chip = QLabel(tag)
                tag_chip.setStyleSheet(f"""
                    QLabel {{
                        background-color: {colors.tag_bg};
                        color: {colors.tag_text};
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 11px;
                    }}
                """)
                tags_layout.addWidget(tag_chip)

            tags_layout.addStretch()
            item_layout.addWidget(tags_row)

        # Action buttons
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        restore_btn = QPushButton("\u21BA Restore")
        restore_btn.clicked.connect(lambda: self._restore_entry(entry.id))
        restore_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.success};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(restore_btn)

        delete_btn = QPushButton("\u2716 Delete Forever")
        delete_btn.clicked.connect(lambda: self._confirm_permanent_delete(entry.id, entry.full_trigger))
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.error};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(delete_btn)

        item_layout.addWidget(button_row)

        return item

    def _show_empty_state(self):
        """Show empty state message."""
        colors = self.theme_manager.colors

        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(8)

        msg_label = QLabel("Trash is empty")
        msg_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(msg_label)

        desc_label = QLabel("Deleted entries will appear here")
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(desc_label)

        self.trash_layout.addWidget(empty)

    def _restore_entry(self, entry_id: str):
        """Restore a deleted entry."""
        entry = self.app_state.entry_manager.get_entry(entry_id)
        if not entry:
            QMessageBox.warning(self, "Entry Not Found", "Entry not found")
            return

        success = self.app_state.entry_manager.restore_entry(entry_id)

        if success:
            self.entry_restored.emit(entry_id)
            self._refresh_trash()
            QMessageBox.information(self, "Entry Restored", f"Restored {entry.full_trigger}")
        else:
            QMessageBox.warning(self, "Restore Failed", "Failed to restore entry")

    def _confirm_permanent_delete(self, entry_id: str, trigger: str):
        """Show confirmation dialog before permanent deletion."""
        reply = QMessageBox.question(
            self,
            "Confirm Permanent Deletion",
            f"Are you sure you want to permanently delete '{trigger}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._permanent_delete_entry(entry_id, trigger)

    def _permanent_delete_entry(self, entry_id: str, trigger: str):
        """Permanently delete an entry."""
        success = self.app_state.entry_manager.permanent_delete(entry_id)

        if success:
            self._refresh_trash()
            QMessageBox.information(self, "Entry Deleted", f"Permanently deleted {trigger}")
        else:
            QMessageBox.warning(self, "Delete Failed", "Failed to delete entry")

    def _on_empty_trash(self):
        """Show confirmation dialog before emptying trash."""
        deleted_entries = self.app_state.entry_manager.get_deleted_entries()
        count = len(deleted_entries)

        if count == 0:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Empty Trash",
            f"Are you sure you want to permanently delete all {count} items in the trash?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._empty_trash()

    def _empty_trash(self):
        """Empty the trash (permanently delete all deleted entries)."""
        deleted_entries = self.app_state.entry_manager.get_deleted_entries()
        count = 0

        for entry in deleted_entries:
            if self.app_state.entry_manager.permanent_delete(entry.id):
                count += 1

        self._refresh_trash()
        QMessageBox.information(
            self,
            "Trash Emptied",
            f"Permanently deleted {count} item{'s' if count != 1 else ''}",
        )

    def refresh(self):
        """Refresh the trash view."""
        self._refresh_trash()
