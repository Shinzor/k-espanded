"""Tag management dialog for creating, renaming, deleting, and customizing tag colors."""

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
    QLineEdit,
    QColorDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor, QCursor, QMouseEvent

from espanded.ui.theme import ThemeManager
from espanded.ui.tag_colors import get_tag_color_manager, TAG_COLORS
from espanded.ui.icon import create_app_icon


class TagColorDialog(QDialog):
    """Frameless, draggable dialog for comprehensive tag management."""

    colors_changed = Signal()
    tags_modified = Signal()  # Emitted when tags are created, renamed, or deleted

    def __init__(self, theme_manager: ThemeManager, all_tags: list[str], parent=None):
        super().__init__(None)  # No parent to prevent issues
        self.theme_manager = theme_manager
        self.all_tags = sorted(set(all_tags))  # Unique, sorted tags
        self.tag_color_manager = get_tag_color_manager()
        self.color_combos = {}  # Map tag to QComboBox
        self.tag_rows = {}  # Map tag to row widget for easy access

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

        # Fixed size (increased for new features)
        self.setFixedSize(600, 700)

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

        title_label = QLabel("Tag Management")
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
        close_btn = QPushButton("×")  # Using × symbol
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
        desc_label = QLabel("Create, rename, delete, and customize tag colors. Changes apply immediately.")
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

        # Create New Tag Section
        create_section = QFrame()
        create_section.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_elevated};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        create_layout = QHBoxLayout(create_section)
        create_layout.setContentsMargins(12, 10, 12, 10)
        create_layout.setSpacing(8)

        create_label = QLabel("New Tag:")
        create_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: 500;
                color: {colors.text_primary};
                background: transparent;
            }}
        """)
        create_layout.addWidget(create_label)

        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("Enter tag name...")
        self.new_tag_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_base};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors.primary};
            }}
        """)
        create_layout.addWidget(self.new_tag_input, stretch=1)

        create_btn = QPushButton("Create")
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
            QPushButton:disabled {{
                background-color: {colors.bg_surface};
                color: {colors.text_tertiary};
            }}
        """)
        create_btn.clicked.connect(self._create_new_tag)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_layout.addWidget(create_btn)

        layout.addWidget(create_section)

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
        self.scroll_layout = QVBoxLayout(scroll_content)  # Store as instance variable
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(12)

        if not self.all_tags:
            no_tags_label = QLabel("No tags found. Create a new tag using the section above.")
            no_tags_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 13px;
                    color: {colors.text_secondary};
                    padding: 20px;
                }}
            """)
            self.scroll_layout.addWidget(no_tags_label)
        else:
            # Create a row for each tag
            for tag in self.all_tags:
                tag_row = self._create_tag_row(tag)
                self.tag_rows[tag] = tag_row
                self.scroll_layout.addWidget(tag_row)

        self.scroll_layout.addStretch()
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
        """Create an enhanced row for a single tag with rename, delete, and color options."""
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

        row_layout = QVBoxLayout(row)  # Changed to vertical layout for better organization
        row_layout.setContentsMargins(12, 10, 12, 10)
        row_layout.setSpacing(8)

        # Top row: Tag name (editable) and delete button
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Tag preview with editable name
        tag_colors_dict = self.tag_color_manager.get_color(tag)
        tag_preview = QFrame()
        tag_preview.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        tag_preview.setStyleSheet(f"""
            QFrame {{
                background-color: {tag_colors_dict['bg']};
                border-radius: 12px;
                border: none;
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
        top_row.addWidget(tag_preview)

        # Rename button
        rename_btn = QPushButton("Rename")
        rename_btn.setFixedHeight(26)
        rename_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.bg_base};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.bg_surface};
                border-color: {colors.primary};
            }}
        """)
        rename_btn.clicked.connect(lambda: self._rename_tag(tag))
        rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        top_row.addWidget(rename_btn)

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedHeight(26)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.bg_base};
                color: {colors.error};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.error};
                color: {colors.text_inverse};
                border-color: {colors.error};
            }}
        """)
        delete_btn.clicked.connect(lambda: self._delete_tag(tag))
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        top_row.addWidget(delete_btn)

        row_layout.addLayout(top_row)

        # Bottom row: Color options
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        color_label = QLabel("Color:")
        color_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {colors.text_secondary};
                background: transparent;
            }}
        """)
        bottom_row.addWidget(color_label)

        # Preset color selector
        color_combo = QComboBox()
        color_combo.setFixedWidth(100)

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
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QComboBox:focus {{
                border: 1px solid {colors.primary};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
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
            lambda: self._on_preset_color_changed(tag, color_combo, tag_preview, tag_label)
        )

        self.color_combos[tag] = color_combo
        bottom_row.addWidget(color_combo)

        # Custom hex color input
        hex_input = QLineEdit()
        hex_input.setPlaceholderText("#RRGGBB")
        hex_input.setFixedWidth(80)
        hex_input.setMaxLength(7)
        hex_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_base};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 11px;
                font-family: monospace;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors.primary};
            }}
        """)
        hex_input.returnPressed.connect(lambda: self._on_custom_color_entered(tag, hex_input, tag_preview, tag_label))
        bottom_row.addWidget(hex_input)

        # Color picker button
        picker_btn = QPushButton("🎨")
        picker_btn.setFixedSize(28, 26)
        picker_btn.setToolTip("Choose custom color")
        picker_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.bg_base};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                font-size: 14px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {colors.bg_surface};
                border-color: {colors.primary};
            }}
        """)
        picker_btn.clicked.connect(lambda: self._open_color_picker(tag, tag_preview, tag_label, hex_input))
        picker_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom_row.addWidget(picker_btn)

        bottom_row.addStretch()

        row_layout.addLayout(bottom_row)

        return row

    def _create_new_tag(self):
        """Create a new tag."""
        tag_name = self.new_tag_input.text().strip()

        if not tag_name:
            QMessageBox.warning(self, "Invalid Tag Name", "Please enter a tag name.")
            return

        if tag_name in self.all_tags:
            QMessageBox.warning(self, "Tag Already Exists", f"The tag '{tag_name}' already exists.")
            return

        # Add to tag list
        self.all_tags.append(tag_name)
        self.all_tags.sort()

        # Create and add new tag row before the stretch
        tag_row = self._create_tag_row(tag_name)
        self.tag_rows[tag_name] = tag_row

        # Insert before stretch (last item)
        insert_index = self.scroll_layout.count() - 1
        self.scroll_layout.insertWidget(insert_index, tag_row)

        # Clear input
        self.new_tag_input.clear()

        # Emit signal
        self.tags_modified.emit()
        self.colors_changed.emit()

    def _rename_tag(self, old_tag: str):
        """Rename a tag."""
        from PySide6.QtWidgets import QInputDialog

        new_tag, ok = QInputDialog.getText(
            self,
            "Rename Tag",
            "Enter new tag name:",
            text=old_tag
        )

        if not ok or not new_tag.strip():
            return

        new_tag = new_tag.strip()

        if new_tag == old_tag:
            return

        if new_tag in self.all_tags:
            QMessageBox.warning(self, "Tag Already Exists", f"The tag '{new_tag}' already exists.")
            return

        # Update tag list
        self.all_tags.remove(old_tag)
        self.all_tags.append(new_tag)
        self.all_tags.sort()

        # Transfer color assignment
        if old_tag in self.tag_color_manager._tag_colors:
            color_key = self.tag_color_manager.get_tag_color_key(old_tag)
            self.tag_color_manager.remove_color(old_tag)
            self.tag_color_manager.set_color(new_tag, color_key)

        # Remove old row
        if old_tag in self.tag_rows:
            old_row = self.tag_rows[old_tag]
            self.scroll_layout.removeWidget(old_row)
            old_row.deleteLater()
            del self.tag_rows[old_tag]
            if old_tag in self.color_combos:
                del self.color_combos[old_tag]

        # Create and add new row
        tag_row = self._create_tag_row(new_tag)
        self.tag_rows[new_tag] = tag_row

        # Insert at correct sorted position
        insert_index = 0
        for i in range(self.scroll_layout.count() - 1):  # -1 for stretch
            widget = self.scroll_layout.itemAt(i).widget()
            if widget and widget in self.tag_rows.values():
                # Find which tag this widget belongs to
                widget_tag = [k for k, v in self.tag_rows.items() if v == widget][0]
                if new_tag < widget_tag:
                    break
                insert_index = i + 1

        self.scroll_layout.insertWidget(insert_index, tag_row)

        # Emit signals
        self.tags_modified.emit()
        self.colors_changed.emit()

    def _delete_tag(self, tag: str):
        """Delete a tag."""
        reply = QMessageBox.question(
            self,
            "Delete Tag",
            f"Are you sure you want to delete the tag '{tag}'?\n\nNote: This will only remove the tag from color management. Entries with this tag will not be affected.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from tag list
            self.all_tags.remove(tag)

            # Remove color assignment
            self.tag_color_manager.remove_color(tag)

            # Remove row
            if tag in self.tag_rows:
                row = self.tag_rows[tag]
                self.scroll_layout.removeWidget(row)
                row.deleteLater()
                del self.tag_rows[tag]
                if tag in self.color_combos:
                    del self.color_combos[tag]

            # Emit signals
            self.tags_modified.emit()
            self.colors_changed.emit()

    def _on_preset_color_changed(self, tag: str, combo: QComboBox, preview: QFrame, label: QLabel):
        """Handle preset color selection change."""
        color_key = combo.currentData()

        # Update the tag color manager
        self.tag_color_manager.set_color(tag, color_key)

        # Update preview
        tag_colors_dict = self.tag_color_manager.get_color(tag)
        preview.setStyleSheet(f"""
            QFrame {{
                background-color: {tag_colors_dict['bg']};
                border-radius: 12px;
                border: none;
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

    def _on_custom_color_entered(self, tag: str, hex_input: QLineEdit, preview: QFrame, label: QLabel):
        """Handle custom hex color entry."""
        hex_color = hex_input.text().strip()

        # Validate hex color
        if not hex_color.startswith('#'):
            hex_color = '#' + hex_color

        try:
            # Validate hex format
            if len(hex_color) != 7:
                raise ValueError("Invalid hex color format")

            int(hex_color[1:], 16)  # Check if valid hex

            # Create custom color entry (stored as "custom")
            # We'll need to extend TAG_COLORS or store custom colors separately
            bg_color = hex_color
            # Determine text color based on brightness
            text_color = self._get_contrasting_text_color(hex_color)

            # For now, we'll set this as a custom color in the manager
            # We need to add custom color support to the tag color manager
            self._set_custom_color(tag, bg_color, text_color)

            # Update preview
            preview.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border-radius: 12px;
                    border: none;
                }}
            """)
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    font-weight: 500;
                    color: {text_color};
                    background-color: transparent;
                }}
            """)

            # Clear input
            hex_input.clear()

            # Emit signal
            self.colors_changed.emit()

        except (ValueError, IndexError):
            QMessageBox.warning(self, "Invalid Color", "Please enter a valid hex color (e.g., #FF5733)")

    def _open_color_picker(self, tag: str, preview: QFrame, label: QLabel, hex_input: QLineEdit):
        """Open Qt color picker dialog."""
        current_colors = self.tag_color_manager.get_color(tag)
        initial_color = QColor(current_colors['bg'])

        color = QColorDialog.getColor(initial_color, self, "Choose Tag Color")

        if color.isValid():
            hex_color = color.name()

            # Determine text color based on brightness
            text_color = self._get_contrasting_text_color(hex_color)

            # Set custom color
            self._set_custom_color(tag, hex_color, text_color)

            # Update preview
            preview.setStyleSheet(f"""
                QFrame {{
                    background-color: {hex_color};
                    border-radius: 12px;
                    border: none;
                }}
            """)
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    font-weight: 500;
                    color: {text_color};
                    background-color: transparent;
                }}
            """)

            # Show hex in input
            hex_input.setText(hex_color)

            # Emit signal
            self.colors_changed.emit()

    def _get_contrasting_text_color(self, hex_color: str) -> str:
        """Determine whether to use white or black text based on background brightness."""
        # Remove # if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Calculate relative luminance
        # https://www.w3.org/TR/WCAG20/#relativeluminancedef
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

        # Return white for dark backgrounds, black for light backgrounds
        return "#ffffff" if luminance < 0.5 else "#000000"

    def _set_custom_color(self, tag: str, bg_color: str, text_color: str):
        """Set a custom color for a tag."""
        # We need to extend the tag color manager to support custom colors
        # For now, we'll add a special "custom" entry to TAG_COLORS dynamically
        custom_key = f"custom_{tag}"

        # Import TAG_COLORS to modify it
        from espanded.ui import tag_colors as tag_colors_module

        # Add custom color to the global TAG_COLORS
        tag_colors_module.TAG_COLORS[custom_key] = {
            "bg": bg_color,
            "text": text_color
        }

        # Set this custom color key for the tag
        self.tag_color_manager.set_color(tag, custom_key)

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
