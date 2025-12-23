"""Custom message dialog - borderless and draggable."""

from enum import Enum
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QWidget,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent

from espanded.ui.theme import ThemeManager


class MessageType(Enum):
    """Message dialog types."""
    INFORMATION = "information"
    WARNING = "warning"
    CRITICAL = "critical"
    QUESTION = "question"


class MessageDialog(QDialog):
    """Custom message dialog with borderless, draggable design."""

    def __init__(
        self,
        theme_manager: ThemeManager,
        title: str,
        message: str,
        message_type: MessageType = MessageType.INFORMATION,
        buttons: list[str] | None = None,
        default_button: str | None = None,
        parent=None,
    ):
        """Initialize message dialog.

        Args:
            theme_manager: Theme manager instance
            title: Dialog title
            message: Message text
            message_type: Type of message (information, warning, critical, question)
            buttons: List of button labels (default: ["OK"] or ["Yes", "No"])
            default_button: Label of the default button
            parent: Parent widget
        """
        super().__init__(parent)
        self.theme_manager = theme_manager
        self._drag_pos: QPoint | None = None
        self.clicked_button: str | None = None

        # Default buttons based on type
        if buttons is None:
            if message_type == MessageType.QUESTION:
                buttons = ["Yes", "No"]
                default_button = default_button or "No"
            else:
                buttons = ["OK"]
                default_button = default_button or "OK"

        self.buttons = buttons
        self.default_button = default_button

        self._setup_window()
        self._setup_ui(title, message, message_type)

    def _setup_window(self):
        """Configure window properties."""
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setModal(True)

        colors = self.theme_manager.colors
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors.bg_surface};
                border: 1px solid {colors.border_default};
                border-radius: 12px;
            }}
        """)

    def _setup_ui(self, title: str, message: str, message_type: MessageType):
        """Build the dialog UI."""
        colors = self.theme_manager.colors

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (draggable)
        self.header = QWidget()
        self.header.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_surface};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)
        self.header.setCursor(Qt.CursorShape.SizeAllCursor)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 16, 16, 12)
        header_layout.setSpacing(8)

        # Icon based on type
        icon_map = {
            MessageType.INFORMATION: "ℹ️",
            MessageType.WARNING: "⚠️",
            MessageType.CRITICAL: "❌",
            MessageType.QUESTION: "❓",
        }
        icon = icon_map.get(message_type, "ℹ️")

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 16px;
                background: transparent;
            }}
        """)
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: none;
                border-radius: 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {colors.error};
                color: {colors.text_inverse};
            }}
        """)
        close_btn.clicked.connect(self.reject)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(close_btn)

        layout.addWidget(self.header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {colors.border_muted}; border: none;")
        layout.addWidget(sep)

        # Content
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(16)

        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 13px;
                line-height: 1.5;
                background: transparent;
            }}
        """)
        content_layout.addWidget(message_label)

        layout.addWidget(content)

        # Buttons
        button_row = QWidget()
        button_row.setStyleSheet("background: transparent;")
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(24, 0, 24, 20)
        button_layout.setSpacing(12)
        button_layout.addStretch()

        for btn_label in self.buttons:
            btn = QPushButton(btn_label)
            is_default = btn_label == self.default_button

            # Style based on whether it's the default button
            if is_default:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors.primary};
                        color: {colors.text_inverse};
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                        font-size: 13px;
                        font-weight: 500;
                        min-width: 80px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.primary_hover};
                    }}
                """)
                btn.setDefault(True)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {colors.text_secondary};
                        border: 1px solid {colors.border_default};
                        border-radius: 6px;
                        padding: 8px 20px;
                        font-size: 13px;
                        font-weight: 500;
                        min-width: 80px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.bg_elevated};
                        border-color: {colors.border_focus};
                        color: {colors.text_primary};
                    }}
                """)

            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, label=btn_label: self._on_button_clicked(label))
            button_layout.addWidget(btn)

        layout.addWidget(button_row)

        # Calculate size based on content
        self.adjustSize()
        min_width = 400
        max_width = 600
        width = max(min_width, min(max_width, self.sizeHint().width()))
        self.setFixedWidth(width)

    def _on_button_clicked(self, label: str):
        """Handle button click."""
        self.clicked_button = label
        if label in ["OK", "Yes"]:
            self.accept()
        else:
            self.reject()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
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

    def show_centered(self):
        """Show dialog centered on screen or parent."""
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)
        else:
            screen = self.screen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        self.show()


# Convenience functions
def show_information(theme_manager: ThemeManager, title: str, message: str, parent=None):
    """Show an information dialog."""
    dialog = MessageDialog(
        theme_manager,
        title,
        message,
        MessageType.INFORMATION,
        parent=parent,
    )
    dialog.show_centered()
    return dialog.exec()


def show_warning(theme_manager: ThemeManager, title: str, message: str, parent=None):
    """Show a warning dialog."""
    dialog = MessageDialog(
        theme_manager,
        title,
        message,
        MessageType.WARNING,
        parent=parent,
    )
    dialog.show_centered()
    return dialog.exec()


def show_critical(theme_manager: ThemeManager, title: str, message: str, parent=None):
    """Show a critical error dialog."""
    dialog = MessageDialog(
        theme_manager,
        title,
        message,
        MessageType.CRITICAL,
        parent=parent,
    )
    dialog.show_centered()
    return dialog.exec()


def show_question(
    theme_manager: ThemeManager,
    title: str,
    message: str,
    buttons: list[str] | None = None,
    default_button: str | None = None,
    parent=None,
) -> str | None:
    """Show a question dialog and return the clicked button label."""
    dialog = MessageDialog(
        theme_manager,
        title,
        message,
        MessageType.QUESTION,
        buttons=buttons,
        default_button=default_button,
        parent=parent,
    )
    dialog.show_centered()
    dialog.exec()
    return dialog.clicked_button
