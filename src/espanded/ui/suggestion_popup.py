"""Suggestion popup for inline autocomplete.

This is a non-focus-stealing popup that shows filtered entry suggestions
as the user types. It appears near the text cursor and allows selection
via keyboard navigation.
"""

import logging
from typing import Callable

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QApplication,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QFont, QColor, QKeyEvent

from espanded.core.models import Entry
from espanded.ui.theme import ThemeManager

logger = logging.getLogger(__name__)


class SuggestionItem(QFrame):
    """A single suggestion item in the popup."""

    clicked = Signal(object)  # Emits the Entry

    def __init__(
        self,
        entry: Entry,
        theme_manager: ThemeManager,
        is_selected: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.entry = entry
        self.theme_manager = theme_manager
        self._is_selected = is_selected

        self._setup_ui()
        self.update_selection(is_selected)

    def _setup_ui(self):
        """Build the item UI."""
        colors = self.theme_manager.colors

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Trigger label (e.g., ":hello")
        trigger_label = QLabel(self.entry.full_trigger)
        trigger_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.primary};
                font-size: 13px;
                font-weight: 600;
                font-family: 'Consolas', 'Monaco', monospace;
                background: transparent;
            }}
        """)
        trigger_label.setFixedWidth(120)
        layout.addWidget(trigger_label)

        # Replacement preview (truncated)
        preview = self.entry.replacement
        if len(preview) > 50:
            preview = preview[:47] + "..."
        # Replace newlines with spaces for preview
        preview = preview.replace("\n", " ").replace("\r", "")

        preview_label = QLabel(preview)
        preview_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_secondary};
                font-size: 12px;
                background: transparent;
            }}
        """)
        layout.addWidget(preview_label, stretch=1)

    def update_selection(self, is_selected: bool):
        """Update the selection state."""
        self._is_selected = is_selected
        colors = self.theme_manager.colors

        if is_selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.entry_selected};
                    border-radius: 6px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border-radius: 6px;
                }}
                QFrame:hover {{
                    background-color: {colors.entry_hover};
                }}
            """)

    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.entry)
        super().mousePressEvent(event)


class SuggestionPopup(QWidget):
    """Non-focus-stealing popup for showing autocomplete suggestions.

    This popup appears near the text cursor and shows filtered entry
    suggestions. It handles keyboard navigation via signals from
    the autocomplete service.
    """

    # Signals
    entry_selected = Signal(object)  # Entry - user selected an entry
    dismissed = Signal()  # Popup was dismissed

    def __init__(self, theme_manager: ThemeManager, parent=None):
        # Use None as parent to avoid main window dependency
        super().__init__(None)
        self.theme_manager = theme_manager

        self._entries: list[Entry] = []
        self._items: list[SuggestionItem] = []
        self._selected_index: int = 0
        self._filter_text: str = ""

        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """Configure window properties for non-focus-stealing behavior."""
        # Window flags for non-focus-stealing popup
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )

        # Don't take focus when shown
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # No focus policy
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Size constraints
        self.setMinimumWidth(350)
        self.setMaximumWidth(500)
        self.setMaximumHeight(400)

    def _setup_ui(self):
        """Build the popup UI."""
        colors = self.theme_manager.colors

        # Main container with styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_surface};
                border: 1px solid {colors.border_default};
                border-radius: 8px;
            }}
        """)

        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(2)

        # Header showing what was typed
        self.header_label = QLabel("")
        self.header_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_tertiary};
                font-size: 11px;
                padding: 4px 8px;
                background: transparent;
            }}
        """)
        self.main_layout.addWidget(self.header_label)

        # Items container
        self.items_container = QWidget()
        self.items_container.setStyleSheet("background: transparent;")
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(2)
        self.main_layout.addWidget(self.items_container)

        # Footer with hint
        self.footer_label = QLabel("↑↓ navigate • Enter select • Esc dismiss")
        self.footer_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_tertiary};
                font-size: 10px;
                padding: 6px 8px 4px 8px;
                background: transparent;
            }}
        """)
        self.main_layout.addWidget(self.footer_label)

    def show_suggestions(
        self,
        entries: list[Entry],
        filter_text: str,
        trigger: str,
        position: tuple[int, int],
    ):
        """Show the popup with suggestions at the given position.

        Args:
            entries: List of matching entries to show
            filter_text: Current filter text (for display)
            trigger: The trigger that was typed (e.g., ':')
            position: Screen position (x, y) to show popup at
        """
        if not entries:
            self.hide()
            return

        self._entries = entries
        self._filter_text = filter_text
        self._selected_index = 0

        # Update header
        search_text = f"{trigger}{filter_text}" if filter_text else trigger
        self.header_label.setText(f"Suggestions for \"{search_text}\"")

        # Clear existing items
        self._clear_items()

        # Add new items
        for i, entry in enumerate(entries):
            item = SuggestionItem(
                entry=entry,
                theme_manager=self.theme_manager,
                is_selected=(i == 0),
            )
            item.clicked.connect(self._on_item_clicked)
            self.items_layout.addWidget(item)
            self._items.append(item)

        # Adjust size
        self.adjustSize()

        # Position the popup
        self._position_popup(position)

        # Show
        self.show()
        self.raise_()

    def update_filter(self, entries: list[Entry], filter_text: str, trigger: str):
        """Update the suggestions with new filter results.

        Args:
            entries: Updated list of matching entries
            filter_text: New filter text
            trigger: The trigger character
        """
        if not entries:
            self.hide()
            self.dismissed.emit()
            return

        self._entries = entries
        self._filter_text = filter_text

        # Clamp selected index
        if self._selected_index >= len(entries):
            self._selected_index = len(entries) - 1

        # Update header
        search_text = f"{trigger}{filter_text}" if filter_text else trigger
        self.header_label.setText(f"Suggestions for \"{search_text}\"")

        # Clear and rebuild items
        self._clear_items()

        for i, entry in enumerate(entries):
            item = SuggestionItem(
                entry=entry,
                theme_manager=self.theme_manager,
                is_selected=(i == self._selected_index),
            )
            item.clicked.connect(self._on_item_clicked)
            self.items_layout.addWidget(item)
            self._items.append(item)

        self.adjustSize()

    def move_selection(self, delta: int):
        """Move the selection up or down.

        Args:
            delta: -1 for up, +1 for down
        """
        if not self._items:
            return

        # Update old selection
        if 0 <= self._selected_index < len(self._items):
            self._items[self._selected_index].update_selection(False)

        # Calculate new selection
        self._selected_index = (self._selected_index + delta) % len(self._items)

        # Update new selection
        self._items[self._selected_index].update_selection(True)

    def select_current(self) -> Entry | None:
        """Select the currently highlighted entry.

        Returns:
            The selected Entry, or None if nothing selected
        """
        if not self._entries or self._selected_index >= len(self._entries):
            return None

        entry = self._entries[self._selected_index]
        self.hide()
        self.entry_selected.emit(entry)
        return entry

    def dismiss(self):
        """Dismiss the popup without selecting."""
        self.hide()
        self.dismissed.emit()

    def _position_popup(self, position: tuple[int, int]):
        """Position the popup near the cursor, keeping it on screen.

        Args:
            position: Target screen position (x, y)
        """
        x, y = position

        # Get screen geometry
        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()

            # Offset slightly from cursor
            x += 2
            y += 4

            # Ensure popup stays on screen
            popup_width = self.width()
            popup_height = self.height()

            # Horizontal bounds
            if x + popup_width > screen_rect.right():
                x = screen_rect.right() - popup_width - 10

            if x < screen_rect.left():
                x = screen_rect.left() + 10

            # Vertical bounds - prefer below cursor, but go above if needed
            if y + popup_height > screen_rect.bottom():
                # Show above the cursor instead
                y = position[1] - popup_height - 20

            if y < screen_rect.top():
                y = screen_rect.top() + 10

        self.move(x, y)

    def _clear_items(self):
        """Clear all suggestion items."""
        for item in self._items:
            item.clicked.disconnect()
            self.items_layout.removeWidget(item)
            item.deleteLater()
        self._items.clear()

    def _on_item_clicked(self, entry: Entry):
        """Handle item click."""
        self.hide()
        self.entry_selected.emit(entry)

    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        # Clean up items when hidden
        # self._clear_items()
