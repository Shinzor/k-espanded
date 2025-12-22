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
    QWidget,
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QKeyEvent, QCursor, QMouseEvent

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
        # Pass None as parent to prevent main window from showing
        super().__init__(None)
        self.theme_manager = theme_manager
        self.selected_text = selected_text
        self.app_state = get_app_state()

        # Drag state
        self._drag_pos: QPoint | None = None

        # Tags list
        self._tags: list[str] = []

        self._setup_window()
        self._setup_ui()
        self._connect_signals()

    def _setup_window(self):
        """Configure window properties."""
        # Frameless, always on top, tool window (doesn't show in taskbar)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)

        # Fixed size (increased for tags)
        self.setFixedSize(420, 400)

        # Apply theme
        colors = self.theme_manager.colors
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {colors.bg_surface};
                border: 2px solid {colors.primary};
                border-radius: 12px;
            }}
        """
        )

    def _setup_ui(self):
        """Build the popup UI."""
        colors = self.theme_manager.colors

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(10)

        # Header (draggable area)
        self.header = QWidget()
        self.header.setStyleSheet("background: transparent;")
        self.header.setCursor(Qt.CursorShape.SizeAllCursor)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        title_label = QLabel("Quick Add Entry")
        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 15px;
                font-weight: 600;
                background: transparent;
            }}
        """
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("X")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: none;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {colors.error};
                color: {colors.text_inverse};
            }}
        """
        )
        close_btn.clicked.connect(self.reject)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(close_btn)

        layout.addWidget(self.header)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {colors.border_muted}; border: none;")
        layout.addWidget(separator)

        # Trigger section
        trigger_label = QLabel("Trigger")
        trigger_label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.text_secondary};
                font-size: 11px;
                font-weight: 500;
                background: transparent;
            }}
        """
        )
        layout.addWidget(trigger_label)

        # Trigger row
        trigger_row = QHBoxLayout()
        trigger_row.setSpacing(8)

        # Prefix dropdown with proper arrow
        self.prefix_combo = QComboBox()
        self.prefix_combo.addItems([":", ";", "//", "::", "(none)"])
        self.prefix_combo.setCurrentIndex(0)
        self.prefix_combo.setFixedWidth(75)
        self.prefix_combo.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 14px;
                font-weight: 500;
            }}
            QComboBox:focus {{
                border: 1px solid {colors.primary};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                selection-background-color: {colors.entry_selected};
                outline: none;
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
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors.primary};
            }}
        """
        )
        trigger_row.addWidget(self.trigger_input, stretch=1)

        layout.addLayout(trigger_row)

        # Replacement section
        replacement_label = QLabel("Replacement" + (" (from selection)" if self.selected_text else ""))
        replacement_label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.text_secondary};
                font-size: 11px;
                font-weight: 500;
                background: transparent;
                margin-top: 4px;
            }}
        """
        )
        layout.addWidget(replacement_label)

        # Replacement text area
        self.replacement_text = QTextEdit()
        self.replacement_text.setPlaceholderText("Replacement text...")
        self.replacement_text.setPlainText(self.selected_text)
        self.replacement_text.setMinimumHeight(80)
        self.replacement_text.setMaximumHeight(120)
        self.replacement_text.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
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

        # Tags section
        tags_label = QLabel("Tags (optional)")
        tags_label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.text_secondary};
                font-size: 11px;
                font-weight: 500;
                background: transparent;
                margin-top: 4px;
            }}
        """
        )
        layout.addWidget(tags_label)

        # Tags row
        tags_row = QWidget()
        tags_row.setStyleSheet("background: transparent;")
        tags_layout = QHBoxLayout(tags_row)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(6)

        # Tags container
        self.tags_container = QWidget()
        self.tags_container.setStyleSheet("background: transparent;")
        self.tags_flow = QHBoxLayout(self.tags_container)
        self.tags_flow.setContentsMargins(0, 0, 0, 0)
        self.tags_flow.setSpacing(4)
        self.tags_flow.addStretch()
        tags_layout.addWidget(self.tags_container, stretch=1)

        # Add tag input
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Add tag...")
        self.tag_input.setFixedWidth(100)
        self.tag_input.returnPressed.connect(self._add_tag)
        self.tag_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors.primary};
            }}
        """
        )
        tags_layout.addWidget(self.tag_input)

        layout.addWidget(tags_row)

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
        cancel_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
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
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Entry")
        save_btn.setDefault(True)
        save_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
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
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_row.addWidget(save_btn)

        layout.addLayout(button_row)

    def _connect_signals(self):
        """Connect signals."""
        pass

    def _add_tag(self):
        """Add a tag from the input field."""
        tag = self.tag_input.text().strip()
        if tag and tag not in self._tags:
            self._tags.append(tag)
            self._add_tag_chip(tag)
            self.tag_input.clear()

    def _add_tag_chip(self, tag: str):
        """Add a tag chip to the container."""
        colors = self.theme_manager.colors

        chip = QWidget()
        chip.setProperty("tag", tag)
        chip.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.tag_bg};
                border-radius: 10px;
            }}
        """)
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(8, 3, 4, 3)
        chip_layout.setSpacing(4)

        tag_label = QLabel(tag)
        tag_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {colors.tag_text};
                background: transparent;
            }}
        """)
        chip_layout.addWidget(tag_label)

        remove_btn = QPushButton("x")
        remove_btn.setFixedSize(14, 14)
        remove_btn.clicked.connect(lambda: self._remove_tag(chip, tag))
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {colors.tag_text};
                border: none;
                font-size: 10px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                color: {colors.text_primary};
            }}
        """)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        chip_layout.addWidget(remove_btn)

        # Insert before the stretch
        self.tags_flow.insertWidget(self.tags_flow.count() - 1, chip)

    def _remove_tag(self, chip: QWidget, tag: str):
        """Remove a tag chip."""
        if tag in self._tags:
            self._tags.remove(tag)
        self.tags_flow.removeWidget(chip)
        chip.deleteLater()

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

        # Handle prefix
        if prefix == "(none)":
            prefix = ""

        # Create entry
        try:
            entry = Entry(
                id="",  # Will be generated
                trigger=trigger,
                prefix=prefix,
                replacement=replacement,
                tags=self._tags.copy(),
                word=True,
                propagate_case=False,
                regex=False,
                case_insensitive=False,
                force_clipboard=False,
                passive=False,
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

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is within header bounds
            header_rect = self.header.geometry()
            if header_rect.contains(event.pos()):
                self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for window dragging."""
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to stop dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        # Escape closes the popup
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
