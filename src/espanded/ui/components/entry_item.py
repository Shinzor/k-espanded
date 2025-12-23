"""Entry list item widget for displaying entry information."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu, QFrame
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QMouseEvent, QCursor

from espanded.ui.theme import ThemeManager
from espanded.ui.tag_colors import get_tag_color_manager
from espanded.core.models import Entry


class EntryItem(QWidget):
    """Widget displaying a single entry in the sidebar list."""

    # Signals
    clicked = Signal(str)  # Emits entry_id
    double_clicked = Signal(str)  # Emits entry_id
    context_menu_requested = Signal(str, object)  # Emits entry_id, QPoint

    def __init__(self, entry: Entry, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.theme_manager = theme_manager
        self._is_selected = False
        self._is_hovering = False
        self._setup_ui()

    def _setup_ui(self):
        """Build the entry item layout."""
        colors = self.theme_manager.colors

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Top row: Trigger text and favorite star
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        # Trigger text
        trigger_text = self.entry.full_trigger
        self.trigger_label = QLabel(trigger_text)
        self.trigger_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """
        )
        top_row.addWidget(self.trigger_label, stretch=1)

        # Favorite star (if favorited)
        # Note: Entry model doesn't have a 'favorited' field yet,
        # but we'll add placeholder for future implementation
        if hasattr(self.entry, "favorited") and self.entry.favorited:
            star_label = QLabel("\u2605")  # Filled star
            star_label.setStyleSheet(
                f"""
                QLabel {{
                    font-size: 14px;
                    color: {colors.warning};
                    background-color: transparent;
                }}
            """
            )
            top_row.addWidget(star_label)

        layout.addLayout(top_row)

        # Replacement preview (truncated)
        preview = self.entry.replacement[:50].replace("\n", " ")
        if len(self.entry.replacement) > 50:
            preview += "..."

        self.preview_label = QLabel(preview)
        self.preview_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """
        )
        self.preview_label.setWordWrap(False)
        layout.addWidget(self.preview_label)

        # Tag chips (show first 3)
        if self.entry.tags:
            tags_row = QHBoxLayout()
            tags_row.setSpacing(6)

            tag_color_manager = get_tag_color_manager()

            for i, tag in enumerate(self.entry.tags[:3]):
                # Get color for this tag
                tag_colors_dict = tag_color_manager.get_color(tag)

                # Use QFrame container for proper rounded corners (QFrame renders borders better than QWidget)
                tag_container = QFrame()
                tag_container.setFrameShape(QFrame.Shape.NoFrame)
                tag_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Enable styling
                tag_container.setStyleSheet(
                    f"""
                    QFrame {{
                        background-color: {tag_colors_dict['bg']};
                        border-radius: 12px;
                        border: none;
                    }}
                """
                )
                tag_layout = QHBoxLayout(tag_container)
                tag_layout.setContentsMargins(10, 4, 10, 4)
                tag_layout.setSpacing(0)

                tag_chip = QLabel(tag)
                tag_chip.setStyleSheet(
                    f"""
                    QLabel {{
                        font-size: 11px;
                        font-weight: 500;
                        color: {tag_colors_dict['text']};
                        background-color: transparent;
                        border: none;
                        padding: 0px;
                    }}
                """
                )
                tag_layout.addWidget(tag_chip)
                tags_row.addWidget(tag_container)

            # Show "+N more" if there are more tags
            if len(self.entry.tags) > 3:
                more_label = QLabel(f"+{len(self.entry.tags) - 3}")
                more_label.setStyleSheet(
                    f"""
                    QLabel {{
                        font-size: 10px;
                        color: {colors.text_tertiary};
                        background-color: transparent;
                    }}
                """
                )
                tags_row.addWidget(more_label)

            tags_row.addStretch()
            layout.addLayout(tags_row)

        # Set initial styling
        self._update_styling()

    def _update_styling(self):
        """Update widget styling based on state."""
        colors = self.theme_manager.colors

        if self._is_selected:
            bg_color = colors.entry_selected
            border = f"3px solid {colors.primary}"
            # Update trigger color to primary when selected
            self.trigger_label.setStyleSheet(
                f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: 600;
                    color: {colors.primary};
                    background-color: transparent;
                }}
            """
            )
        elif self._is_hovering:
            bg_color = colors.entry_hover
            border = "3px solid transparent"
            # Reset trigger color on hover
            self.trigger_label.setStyleSheet(
                f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: 600;
                    color: {colors.text_primary};
                    background-color: transparent;
                }}
            """
            )
        else:
            bg_color = "transparent"
            border = "3px solid transparent"
            # Reset trigger color
            self.trigger_label.setStyleSheet(
                f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: 600;
                    color: {colors.text_primary};
                    background-color: transparent;
                }}
            """
            )

        self.setStyleSheet(
            f"""
            EntryItem {{
                background-color: {bg_color};
                border-left: {border};
                border-radius: 8px;
            }}
        """
        )

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.entry.id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.entry.id)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """Handle right-click context menu."""
        self.context_menu_requested.emit(self.entry.id, event.globalPos())

    def enterEvent(self, event: QEvent):
        """Handle mouse enter (hover start)."""
        self._is_hovering = True
        self._update_styling()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        """Handle mouse leave (hover end)."""
        self._is_hovering = False
        self._update_styling()
        super().leaveEvent(event)

    def set_selected(self, selected: bool):
        """Set selection state."""
        self._is_selected = selected
        self._update_styling()

    def is_selected(self) -> bool:
        """Get selection state."""
        return self._is_selected

    def get_entry_id(self) -> str:
        """Get the entry ID."""
        return self.entry.id

    def update_entry(self, entry: Entry):
        """Update the displayed entry data."""
        self.entry = entry
        # Rebuild UI with new data
        # Clear layout
        while self.layout().count():
            child = self.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        # Rebuild
        self._setup_ui()
