"""Tag color customization dialog."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QFrame,
    QComboBox,
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor, QCursor, QMouseEvent

from espanded.ui.theme import ThemeManager
from espanded.ui.tag_colors import get_tag_color_manager, TAG_COLORS
from espanded.ui.icon import create_app_icon


class TagColorDialog(QDialog):
    """Frameless, draggable dialog for customizing tag colors."""

    colors_changed = Signal()

    def __init__(self, theme_manager: ThemeManager, all_tags: list[str], parent=None):
        super().__init__(None)  # No parent to prevent issues
        self.theme_manager = theme_manager
        self.all_tags = sorted(set(all_tags))  # Unique, sorted tags
        self.tag_color_manager = get_tag_color_manager()
        self.color_combos = {}  # Map tag to QComboBox

        # Drag state
        self._drag_pos: QPoint | None = None

        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """Configure window properties."""
        # Frameless, always on top, tool window
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Set window icon
        self.setWindowIcon(create_app_icon())

        # Fixed size
        self.setFixedSize(520, 650)

        # Apply theme with border
        colors = self.theme_manager.colors
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors.bg_surface};
                border: 2px solid {colors.primary};
                border-radius: 12px;
            }}
        """)

    def _setup_ui(self):
        """Build the dialog UI."""
        colors = self.theme_manager.colors

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

        title_label = QLabel("Customize Tag Colors")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 15px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("X")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
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
        """)
        close_btn.clicked.connect(self.accept)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(close_btn)

        layout.addWidget(self.header)

        # Description
        desc_label = QLabel("Choose a color for each tag. Changes apply immediately.")
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {colors.text_secondary};
                background: transparent;
            }}
        """)
        layout.addWidget(desc_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {colors.border_muted}; border: none;")
        layout.addWidget(separator)

        # Scroll area for tags
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {colors.bg_elevated};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors.primary};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors.primary_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        if not self.all_tags:
            no_tags_label = QLabel("No tags found. Create entries with tags first.")
            no_tags_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 13px;
                    color: {colors.text_secondary};
                    padding: 20px;
                }}
            """)
            scroll_layout.addWidget(no_tags_label)
        else:
            # Create a row for each tag
            for tag in self.all_tags:
                tag_row = self._create_tag_row(tag)
                scroll_layout.addWidget(tag_row)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.addStretch()

        reset_btn = QPushButton("Reset All")
        reset_btn.setStyleSheet(f"""
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
        """)
        reset_btn.clicked.connect(self._reset_all)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_row.addWidget(reset_btn)

        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.setStyleSheet(f"""
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
        """)
        close_btn.clicked.connect(self.accept)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_row.addWidget(close_btn)

        layout.addLayout(button_row)

    def _create_tag_row(self, tag: str) -> QFrame:
        """Create a row for a single tag."""
        colors = self.theme_manager.colors
        current_color_key = self.tag_color_manager.get_tag_color_key(tag)

        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_elevated};
                border-radius: 8px;
                padding: 8px;
            }}
        """)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 8, 12, 8)
        row_layout.setSpacing(12)

        # Tag preview
        tag_colors_dict = self.tag_color_manager.get_color(tag)
        tag_preview = QWidget()
        tag_preview.setStyleSheet(f"""
            QWidget {{
                background-color: {tag_colors_dict['bg']};
                border-radius: 12px;
            }}
        """)
        preview_layout = QHBoxLayout(tag_preview)
        preview_layout.setContentsMargins(10, 4, 10, 4)
        preview_layout.setSpacing(0)

        tag_label = QLabel(tag)
        tag_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: 500;
                color: {tag_colors_dict['text']};
                background-color: transparent;
            }}
        """)
        preview_layout.addWidget(tag_label)
        row_layout.addWidget(tag_preview)

        row_layout.addStretch()

        # Color selector
        color_combo = QComboBox()
        color_combo.setFixedWidth(120)

        # Add color options
        for color_name in TAG_COLORS.keys():
            color_combo.addItem(color_name.capitalize(), color_name)

        # Set current color
        for i in range(color_combo.count()):
            if color_combo.itemData(i) == current_color_key:
                color_combo.setCurrentIndex(i)
                break

        color_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors.bg_base};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
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
        """)

        # Connect change handler
        color_combo.currentIndexChanged.connect(
            lambda: self._on_color_changed(tag, color_combo, tag_preview, tag_label)
        )

        self.color_combos[tag] = color_combo
        row_layout.addWidget(color_combo)

        return row

    def _on_color_changed(self, tag: str, combo: QComboBox, preview: QWidget, label: QLabel):
        """Handle color selection change."""
        color_key = combo.currentData()

        # Update the tag color manager
        self.tag_color_manager.set_color(tag, color_key)

        # Update preview
        tag_colors_dict = self.tag_color_manager.get_color(tag)
        preview.setStyleSheet(f"""
            QWidget {{
                background-color: {tag_colors_dict['bg']};
                border-radius: 12px;
            }}
        """)
        label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: 500;
                color: {tag_colors_dict['text']};
                background-color: transparent;
            }}
        """)

        # Emit signal
        self.colors_changed.emit()

    def _reset_all(self):
        """Reset all tags to default color."""
        for tag in self.all_tags:
            self.tag_color_manager.remove_color(tag)

            # Update combo box to default (blue)
            if tag in self.color_combos:
                combo = self.color_combos[tag]
                for i in range(combo.count()):
                    if combo.itemData(i) == "blue":
                        combo.setCurrentIndex(i)
                        break

        self.colors_changed.emit()

    def show_centered(self):
        """Show dialog centered on screen."""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

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
