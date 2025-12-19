"""Search bar component with clear button."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from espanded.ui.theme import ThemeManager


class SearchBar(QWidget):
    """Search input with icon and clear button."""

    # Signals
    search_changed = Signal(str)  # Emits search text

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self._setup_ui()

    def _setup_ui(self):
        """Build the search bar layout."""
        colors = self.theme_manager.colors

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search entries...")
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {colors.bg_surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border_muted};
                border-radius: 8px;
                padding: 8px 36px 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors.border_focus};
            }}
        """
        )

        # Clear button (overlaid on right side of input)
        self.clear_button = QPushButton("\u2715")  # X symbol
        self.clear_button.setFixedSize(24, 24)
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.clicked.connect(self._on_clear)
        self.clear_button.setVisible(False)
        self.clear_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_tertiary};
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {colors.entry_hover};
                color: {colors.text_secondary};
            }}
        """
        )

        # Position clear button over search input
        layout.addWidget(self.search_input)

        # Use absolute positioning for clear button
        self.clear_button.setParent(self.search_input)
        self.search_input.textChanged.connect(self._update_clear_button_position)

    def _update_clear_button_position(self):
        """Position clear button on the right side of the input."""
        input_height = self.search_input.height()
        button_y = (input_height - self.clear_button.height()) // 2
        button_x = self.search_input.width() - self.clear_button.width() - 8
        self.clear_button.move(button_x, button_y)

    def resizeEvent(self, event):
        """Handle resize to reposition clear button."""
        super().resizeEvent(event)
        self._update_clear_button_position()

    def _on_text_changed(self, text: str):
        """Handle search text change."""
        # Show/hide clear button
        self.clear_button.setVisible(bool(text))
        self._update_clear_button_position()

        # Emit signal
        self.search_changed.emit(text)

    def _on_clear(self):
        """Clear the search input."""
        self.search_input.clear()
        self.search_input.setFocus()

    def get_text(self) -> str:
        """Get current search text."""
        return self.search_input.text()

    def set_text(self, text: str):
        """Set search text."""
        self.search_input.setText(text)

    def clear(self):
        """Clear the search input."""
        self.search_input.clear()
