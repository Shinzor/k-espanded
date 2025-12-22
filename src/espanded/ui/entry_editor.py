"""Entry editor panel for creating and editing entries."""

from uuid import uuid4

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QFrame,
    QScrollArea,
    QMessageBox,
    QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor

from espanded.ui.theme import ThemeManager
from espanded.core.app_state import get_app_state
from espanded.core.models import Entry


# Trigger prefix options - just the characters
TRIGGER_PREFIXES = [
    (":", ":"),
    (";", ";"),
    ("//", "//"),
    ("::", "::"),
    ("", "(none)"),
]

# Variable categories for insertion
VARIABLE_ITEMS = [
    ("Date & Time", [
        ("{{date}}", "Current date"),
        ("{{date:%Y-%m-%d}}", "Custom date format"),
        ("{{time}}", "Current time"),
        ("{{time:%H:%M}}", "Custom time format"),
    ]),
    ("Clipboard", [
        ("{{clipboard}}", "Clipboard content"),
    ]),
    ("Random", [
        ("{{random:uuid}}", "Random UUID"),
        ("{{random:chars:5}}", "Random characters"),
        ("{{random:alnum:5}}", "Random alphanumeric"),
        ("{{random:num:5}}", "Random numbers"),
    ]),
    ("Forms", [
        ("{{form1}}", "Simple form field"),
        ("{{form1:default=value}}", "Form with default"),
    ]),
    ("Cursor", [
        ("$|$", "Cursor position"),
    ]),
]


class EntryEditor(QWidget):
    """Entry editor panel for creating and editing entries."""

    # Signals
    entry_saved = Signal(object)  # Emits Entry object
    entry_deleted = Signal(object)  # Emits Entry object
    entry_cloned = Signal(object)  # Emits Entry object
    close_requested = Signal()

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.app_state = get_app_state()

        self.current_entry: Entry | None = None
        self.is_new: bool = True

        self._setup_ui()

    def _setup_ui(self):
        """Build the entry editor layout."""
        colors = self.theme_manager.colors

        # Set background for entire widget
        self.setStyleSheet(f"background-color: {colors.bg_base};")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Action buttons row (fixed at top)
        actions_row = self._create_action_buttons()
        layout.addWidget(actions_row)

        # Scrollable form content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors.bg_base};
                border: none;
            }}
        """)

        form_content = self._create_form()
        scroll.setWidget(form_content)
        layout.addWidget(scroll, stretch=1)

    def _create_header(self) -> QWidget:
        """Create editor header with title and close button."""
        colors = self.theme_manager.colors

        header = QWidget()
        header.setStyleSheet(f"background-color: {colors.bg_base};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 24, 24, 0)

        # Title
        self.header_text = QLabel("New Entry")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.header_text.setFont(title_font)
        self.header_text.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        header_layout.addWidget(self.header_text)
        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("X")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.close_requested.emit)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
            }}
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(close_btn)

        return header

    def _create_action_buttons(self) -> QWidget:
        """Create action buttons row."""
        colors = self.theme_manager.colors

        actions = QWidget()
        actions.setStyleSheet(f"background-color: {colors.bg_base};")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(24, 16, 24, 16)

        # Left side buttons (Delete, Clone)
        left_buttons = QWidget()
        left_buttons.setStyleSheet("background-color: transparent;")
        left_layout = QHBoxLayout(left_buttons)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete_click)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.error};
                border: 1px solid {colors.error};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {colors.error};
                color: {colors.text_inverse};
            }}
        """)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(self.delete_btn)

        self.clone_btn = QPushButton("Clone")
        self.clone_btn.clicked.connect(self._on_clone_click)
        self.clone_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {colors.bg_elevated};
                border-color: {colors.primary};
                color: {colors.text_primary};
            }}
        """)
        self.clone_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(self.clone_btn)

        actions_layout.addWidget(left_buttons)
        actions_layout.addStretch()

        # Save button
        self.save_btn = QPushButton("Save Entry")
        self.save_btn.clicked.connect(self._on_save_click)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 10px 28px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
        """)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(self.save_btn)

        return actions

    def _create_form(self) -> QWidget:
        """Create the entry form with card sections."""
        colors = self.theme_manager.colors

        form = QWidget()
        form.setStyleSheet(f"background-color: {colors.bg_base};")
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(24, 8, 24, 24)
        form_layout.setSpacing(16)

        # Trigger Card
        trigger_card = self._create_card("Trigger", self._create_trigger_content())
        form_layout.addWidget(trigger_card)

        # Replacement Card
        replacement_card = self._create_card("Replacement", self._create_replacement_content())
        form_layout.addWidget(replacement_card)

        # Tags Card
        tags_card = self._create_card("Tags", self._create_tags_content())
        form_layout.addWidget(tags_card)

        # Advanced Options Card (collapsible)
        self.advanced_card = self._create_advanced_card()
        form_layout.addWidget(self.advanced_card)

        form_layout.addStretch()

        return form

    def _create_card(self, title: str, content: QWidget) -> QFrame:
        """Create a card with title and content."""
        colors = self.theme_manager.colors

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_surface};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        layout.addWidget(title_label)

        # Content
        content.setStyleSheet(f"background-color: transparent;")
        layout.addWidget(content)

        return card

    def _create_trigger_content(self) -> QWidget:
        """Create trigger input content."""
        colors = self.theme_manager.colors

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Description
        desc = QLabel("The text that triggers the expansion")
        desc.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(desc)

        # Trigger input row: "Trigger:" label + prefix dropdown + text input
        input_row = QWidget()
        input_row.setStyleSheet("background-color: transparent;")
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        # Trigger label
        trigger_label = QLabel("Trigger:")
        trigger_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        input_layout.addWidget(trigger_label)

        # Prefix dropdown (compact, just shows the character)
        self.prefix_dropdown = QComboBox()
        for prefix, display in TRIGGER_PREFIXES:
            self.prefix_dropdown.addItem(display, prefix)
        self.prefix_dropdown.setCurrentIndex(0)
        self.prefix_dropdown.setFixedWidth(70)
        self.prefix_dropdown.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 500;
            }}
            QComboBox:focus {{
                border-color: {colors.primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                selection-background-color: {colors.entry_selected};
            }}
        """)
        input_layout.addWidget(self.prefix_dropdown)

        # Trigger text field
        self.trigger_field = QLineEdit()
        self.trigger_field.setPlaceholderText("e.g., addr, sig, hello")
        self.trigger_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {colors.primary};
            }}
        """)
        input_layout.addWidget(self.trigger_field, stretch=1)

        content_layout.addWidget(input_row)

        return content

    def _create_replacement_content(self) -> QWidget:
        """Create replacement text content."""
        colors = self.theme_manager.colors

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Header with description and insert button
        header = QWidget()
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        desc = QLabel("The text that will replace the trigger")
        desc.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        header_layout.addWidget(desc)
        header_layout.addStretch()

        # Insert variable button
        insert_var_btn = QPushButton("+ Insert Variable")
        insert_var_btn.clicked.connect(self._show_variable_menu)
        insert_var_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.primary_muted};
                color: {colors.primary};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.entry_selected};
            }}
        """)
        insert_var_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(insert_var_btn)

        content_layout.addWidget(header)

        # Text editor
        self.replacement_field = QTextEdit()
        self.replacement_field.setPlaceholderText("Enter replacement text...\n\nTip: Use {{ to insert variables and forms")
        self.replacement_field.setMinimumHeight(140)
        self.replacement_field.setMaximumHeight(200)
        font = QFont("Consolas, Monaco, monospace")
        font.setPointSize(11)
        self.replacement_field.setFont(font)
        self.replacement_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 8px;
                padding: 12px;
            }}
            QTextEdit:focus {{
                border-color: {colors.primary};
            }}
        """)
        content_layout.addWidget(self.replacement_field)

        return content

    def _create_tags_content(self) -> QWidget:
        """Create tags input content."""
        colors = self.theme_manager.colors

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Description
        desc = QLabel("Organize entries with tags for easy filtering")
        desc.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(desc)

        # Tags display and input row
        tags_row = QWidget()
        tags_row.setStyleSheet("background-color: transparent;")
        tags_layout = QHBoxLayout(tags_row)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(8)

        # Tags container (will hold tag chips)
        self.tags_container = QWidget()
        self.tags_container.setStyleSheet("background-color: transparent;")
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(6)
        self.tags_layout.addStretch()
        tags_layout.addWidget(self.tags_container, stretch=1)

        # Add tag input
        self.add_tag_field = QLineEdit()
        self.add_tag_field.setPlaceholderText("Add tag...")
        self.add_tag_field.setFixedWidth(140)
        self.add_tag_field.returnPressed.connect(self._on_add_tag)
        self.add_tag_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {colors.primary};
            }}
        """)
        tags_layout.addWidget(self.add_tag_field)

        content_layout.addWidget(tags_row)

        return content

    def _create_advanced_card(self) -> QFrame:
        """Create advanced options card (collapsible)."""
        colors = self.theme_manager.colors

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_surface};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        # Toggle header
        self.advanced_toggle = QPushButton("Advanced Options")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.clicked.connect(self._toggle_advanced)
        self.advanced_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: none;
                text-align: left;
                padding: 4px 0px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: {colors.text_primary};
            }}
        """)
        self.advanced_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.advanced_toggle)

        # Advanced content (hidden by default)
        self.advanced_content = QWidget()
        self.advanced_content.setVisible(False)
        self.advanced_content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(self.advanced_content)
        content_layout.setContentsMargins(0, 16, 0, 0)
        content_layout.setSpacing(16)

        # Trigger Settings Group
        trigger_group = self._create_options_group("Trigger Settings", [
            ("word_trigger_cb", "Word trigger (expand at word boundaries)", True),
            ("propagate_case_cb", "Propagate case (match input casing)", False),
        ])
        content_layout.addWidget(trigger_group)

        # Matching Group
        matching_group = self._create_options_group("Matching", [
            ("regex_cb", "Regex trigger", False),
            ("case_insensitive_cb", "Case insensitive matching", False),
        ])
        content_layout.addWidget(matching_group)

        # Behavior Group
        behavior_group = self._create_options_group("Behavior", [
            ("force_clipboard_cb", "Force clipboard paste", False),
            ("passive_cb", "Passive mode (manual trigger only)", False),
        ])
        content_layout.addWidget(behavior_group)

        # App Filtering
        filter_section = QWidget()
        filter_section.setStyleSheet("background-color: transparent;")
        filter_layout = QVBoxLayout(filter_section)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(6)

        filter_label = QLabel("App Filtering")
        filter_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 600;
                color: {colors.text_tertiary};
                text-transform: uppercase;
                letter-spacing: 0.5px;
                background-color: transparent;
            }}
        """)
        filter_layout.addWidget(filter_label)

        self.filter_apps_field = QLineEdit()
        self.filter_apps_field.setPlaceholderText("chrome, slack, vscode (comma-separated)")
        self.filter_apps_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {colors.primary};
            }}
        """)
        filter_layout.addWidget(self.filter_apps_field)

        content_layout.addWidget(filter_section)

        layout.addWidget(self.advanced_content)

        return card

    def _create_options_group(self, title: str, options: list) -> QWidget:
        """Create a group of checkbox options."""
        colors = self.theme_manager.colors

        group = QWidget()
        group.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Group title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 600;
                color: {colors.text_tertiary};
                text-transform: uppercase;
                letter-spacing: 0.5px;
                background-color: transparent;
            }}
        """)
        layout.addWidget(title_label)

        # Checkboxes
        for attr_name, label, default in options:
            cb = QCheckBox(label)
            cb.setChecked(default)
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {colors.text_primary};
                    spacing: 8px;
                    background-color: transparent;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid {colors.border_default};
                    border-radius: 4px;
                    background-color: {colors.bg_elevated};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {colors.primary};
                    border-color: {colors.primary};
                }}
                QCheckBox::indicator:hover {{
                    border-color: {colors.primary};
                }}
            """)
            setattr(self, attr_name, cb)
            layout.addWidget(cb)

        return group

    def _toggle_advanced(self):
        """Toggle advanced options visibility."""
        is_visible = self.advanced_content.isVisible()
        self.advanced_content.setVisible(not is_visible)
        arrow = "v" if not is_visible else ">"
        self.advanced_toggle.setText(f"{arrow} Advanced Options")

    def _show_variable_menu(self):
        """Show variable insertion menu."""
        colors = self.theme_manager.colors

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {colors.entry_selected};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {colors.border_muted};
                margin: 4px 8px;
            }}
        """)

        for category_name, items in VARIABLE_ITEMS:
            # Category header (disabled)
            header = menu.addAction(category_name)
            header.setEnabled(False)

            # Category items
            for value, label in items:
                action = menu.addAction(f"  {label}")
                action.triggered.connect(lambda checked=False, v=value: self._insert_variable(v))

            menu.addSeparator()

        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))

    def _insert_variable(self, variable: str):
        """Insert variable at cursor position."""
        cursor = self.replacement_field.textCursor()
        cursor.insertText(variable)
        self.replacement_field.setFocus()

    def _on_add_tag(self):
        """Add a tag chip."""
        tag = self.add_tag_field.text().strip()
        if tag and tag not in self._get_current_tags():
            self._add_tag_chip(tag)
            self.add_tag_field.clear()

    def _add_tag_chip(self, tag: str):
        """Add a tag chip to the container."""
        colors = self.theme_manager.colors

        chip = QWidget()
        chip.setProperty("tag", tag)
        chip.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.tag_bg};
                border-radius: 12px;
            }}
        """)
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(10, 4, 6, 4)
        chip_layout.setSpacing(4)

        tag_label = QLabel(tag)
        tag_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors.tag_text};
                background-color: transparent;
            }}
        """)
        chip_layout.addWidget(tag_label)

        remove_btn = QPushButton("x")
        remove_btn.setFixedSize(16, 16)
        remove_btn.clicked.connect(lambda: self._remove_tag_chip(chip))
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.tag_text};
                border: none;
                font-size: 10px;
                font-weight: 600;
                padding: 0px;
            }}
            QPushButton:hover {{
                color: {colors.text_primary};
            }}
        """)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        chip_layout.addWidget(remove_btn)

        # Insert before stretch
        self.tags_layout.insertWidget(self.tags_layout.count() - 1, chip)

    def _remove_tag_chip(self, chip: QWidget):
        """Remove a tag chip."""
        self.tags_layout.removeWidget(chip)
        chip.deleteLater()

    def _get_current_tags(self) -> list[str]:
        """Get current tags from chips."""
        tags = []
        for i in range(self.tags_layout.count()):
            widget = self.tags_layout.itemAt(i).widget()
            if widget and widget.property("tag"):
                tags.append(widget.property("tag"))
        return tags

    def set_entry(self, entry: Entry | None):
        """Set the entry to edit."""
        self.current_entry = entry
        self.is_new = entry is None or not entry.id

        if entry:
            # Edit mode
            self.header_text.setText("Edit Entry")

            # Set prefix
            for i in range(self.prefix_dropdown.count()):
                if self.prefix_dropdown.itemData(i) == entry.prefix:
                    self.prefix_dropdown.setCurrentIndex(i)
                    break

            # Set fields
            self.trigger_field.setText(entry.trigger)
            self.replacement_field.setPlainText(entry.replacement)

            # Clear and set tags
            while self.tags_layout.count() > 1:  # Keep stretch
                item = self.tags_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            for tag in entry.tags:
                self._add_tag_chip(tag)

            # Set advanced options
            self.word_trigger_cb.setChecked(entry.word)
            self.propagate_case_cb.setChecked(entry.propagate_case)
            self.regex_cb.setChecked(entry.regex)
            self.case_insensitive_cb.setChecked(entry.case_insensitive)
            self.force_clipboard_cb.setChecked(entry.force_clipboard)
            self.passive_cb.setChecked(entry.passive)

            if entry.filter_apps:
                self.filter_apps_field.setText(", ".join(entry.filter_apps))
            else:
                self.filter_apps_field.clear()

            # Show delete/clone buttons
            self.delete_btn.setVisible(True)
            self.clone_btn.setVisible(True)
        else:
            # New entry mode
            self.header_text.setText("New Entry")
            self.prefix_dropdown.setCurrentIndex(0)
            self.trigger_field.clear()
            self.replacement_field.clear()

            # Clear tags
            while self.tags_layout.count() > 1:
                item = self.tags_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Reset advanced options
            self.word_trigger_cb.setChecked(True)
            self.propagate_case_cb.setChecked(False)
            self.regex_cb.setChecked(False)
            self.case_insensitive_cb.setChecked(False)
            self.force_clipboard_cb.setChecked(False)
            self.passive_cb.setChecked(False)
            self.filter_apps_field.clear()

            # Hide delete/clone buttons
            self.delete_btn.setVisible(False)
            self.clone_btn.setVisible(False)

    def _build_entry_from_form(self) -> Entry | None:
        """Build Entry object from form values."""
        trigger = self.trigger_field.text().strip()
        if not trigger:
            return None

        prefix = self.prefix_dropdown.currentData()
        replacement = self.replacement_field.toPlainText()
        tags = self._get_current_tags()

        filter_apps = None
        filter_apps_text = self.filter_apps_field.text().strip()
        if filter_apps_text:
            filter_apps = [a.strip() for a in filter_apps_text.split(",") if a.strip()]

        entry_id = self.current_entry.id if self.current_entry and self.current_entry.id else str(uuid4())

        return Entry(
            id=entry_id,
            trigger=trigger,
            prefix=prefix,
            replacement=replacement,
            tags=tags,
            word=self.word_trigger_cb.isChecked(),
            propagate_case=self.propagate_case_cb.isChecked(),
            regex=self.regex_cb.isChecked(),
            case_insensitive=self.case_insensitive_cb.isChecked(),
            force_clipboard=self.force_clipboard_cb.isChecked(),
            passive=self.passive_cb.isChecked(),
            filter_apps=filter_apps,
        )

    def _on_save_click(self):
        """Handle save button click."""
        entry = self._build_entry_from_form()
        if not entry:
            QMessageBox.warning(self, "Validation Error", "Trigger is required")
            return

        self.entry_saved.emit(entry)

    def _on_delete_click(self):
        """Handle delete button click."""
        if self.current_entry:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete '{self.current_entry.full_trigger}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.entry_deleted.emit(self.current_entry)

    def _on_clone_click(self):
        """Handle clone button click."""
        if self.current_entry:
            self.entry_cloned.emit(self.current_entry)
