"""Quick Add popup dialog for rapid entry creation."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QComboBox,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QKeyEvent, QCursor

from espanded.ui.theme import ThemeManager
from espanded.core.app_state import get_app_state
from espanded.core.models import Entry


class QuickAddPopup(QDialog):
    """Quick Add popup for creating entries from selected text.

    This frameless, always-on-top popup appears when the global hotkey is pressed.
    The selected text becomes the replacement, user just adds a trigger.
    """

    entry_created = Signal(Entry)

    def __init__(self, theme_manager: ThemeManager, selected_text: str = "", parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.selected_text = selected_text
        self.app_state = get_app_state()

        self._setup_window()
        self._setup_ui()
        self._connect_signals()

    def _setup_window(self):
        """Configure window properties."""
        # Frameless, always on top
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Fixed size
        self.setFixedSize(400, 320)

        # Apply theme
        colors = self.theme_manager.colors
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {colors.bg_surface};
                border: 2px solid {colors.primary};
                border-radius: 8px;
            }}
        """
        )

    def _setup_ui(self):
        """Build the popup UI."""
        colors = self.theme_manager.colors

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        title_label = QLabel("⚡ Quick Add Entry")
        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 16px;
                font-weight: 600;
                background: transparent;
            }}
        """
        )
        header.addWidget(title_label)
        header.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: none;
                border-radius: 12px;
                font-size: 16px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {colors.error};
                color: {colors.text_inverse};
            }}
        """
        )
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {colors.border_muted}; border: none;")
        layout.addWidget(separator)

        # Trigger row
        trigger_row = QHBoxLayout()
        trigger_row.setSpacing(8)

        # Prefix dropdown
        self.prefix_combo = QComboBox()
        self.prefix_combo.addItems([":", ";", "/", "//", "::", "none"])
        self.prefix_combo.setCurrentText(":")
        self.prefix_combo.setFixedWidth(80)
        self.prefix_combo.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
            }}
            QComboBox:focus {{
                border: 1px solid {colors.primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                selection-background-color: {colors.entry_selected};
            }}
        """
        )
        trigger_row.addWidget(self.prefix_combo)

        # Trigger input
        self.trigger_input = QLineEdit()
        self.trigger_input.setPlaceholderText("e.g., email, addr, sig")
        self.trigger_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors.primary};
            }}
        """
        )
        trigger_row.addWidget(self.trigger_input, stretch=1)

        layout.addLayout(trigger_row)

        # Trigger label
        trigger_label = QLabel("Trigger")
        trigger_label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.text_secondary};
                font-size: 11px;
                background: transparent;
            }}
        """
        )
        layout.addWidget(trigger_label)

        # Replacement text area
        self.replacement_text = QTextEdit()
        self.replacement_text.setPlaceholderText("Replacement text...")
        self.replacement_text.setPlainText(self.selected_text)
        self.replacement_text.setMinimumHeight(100)
        self.replacement_text.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            QTextEdit:focus {{
                border: 1px solid {colors.primary};
            }}
        """
        )
        layout.addWidget(self.replacement_text)

        # Replacement label
        replacement_label = QLabel("Replacement" + (" (from selection)" if self.selected_text else ""))
        replacement_label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.text_secondary};
                font-size: 11px;
                background: transparent;
            }}
        """
        )
        layout.addWidget(replacement_label)

        # Error message
        self.error_label = QLabel()
        self.error_label.setVisible(False)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.error};
                font-size: 11px;
                background: transparent;
            }}
        """
        )
        layout.addWidget(self.error_label)

        # Buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.bg_surface};
                border-color: {colors.primary};
            }}
        """
        )
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
        """
        )
        save_btn.clicked.connect(self._on_save)
        button_row.addWidget(save_btn)

        layout.addLayout(button_row)

    def _connect_signals(self):
        """Connect signals."""
        # Enter key in trigger field should focus replacement
        self.trigger_input.returnPressed.connect(self.replacement_text.setFocus)

    def _on_save(self):
        """Handle save button click."""
        # Get values
        trigger = self.trigger_input.text().strip()
        prefix = self.prefix_combo.currentText()
        replacement = self.replacement_text.toPlainText().strip()

        # Validation
        if not trigger:
            self._show_error("Please enter a trigger")
            return

        if not replacement:
            self._show_error("Please enter replacement text")
            return

        # Build full trigger
        if prefix == "none":
            full_trigger = trigger
        else:
            full_trigger = f"{prefix}{trigger}"

        # Create entry
        try:
            entry = Entry(
                id="",  # Will be generated by entry manager
                trigger=full_trigger,
                replacement=replacement,
                description="",
                tags=[],
                category="",
                is_regex=False,
                case_sensitive=False,
                word=True,
                propagate_case=False,
                uppercase_style=None,
            )

            # Save via entry manager
            created_entry = self.app_state.entry_manager.create_entry(entry)

            # Emit signal
            self.entry_created.emit(created_entry)

            # Close popup
            self.accept()

        except Exception as e:
            self._show_error(f"Failed to create entry: {str(e)}")

    def _show_error(self, message: str):
        """Show error message."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def show_at_cursor(self):
        """Show popup near cursor position."""
        # Get cursor position
        cursor_pos = QCursor.pos()

        # Calculate popup position (centered on cursor)
        x = cursor_pos.x() - self.width() // 2
        y = cursor_pos.y() - self.height() // 2

        # Ensure popup stays on screen
        from PySide6.QtWidgets import QApplication

        screen = QApplication.primaryScreen().geometry()
        x = max(screen.x(), min(x, screen.x() + screen.width() - self.width()))
        y = max(screen.y(), min(y, screen.y() + screen.height() - self.height()))

        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

        # Focus trigger input
        self.trigger_input.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        # Escape closes the popup
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
