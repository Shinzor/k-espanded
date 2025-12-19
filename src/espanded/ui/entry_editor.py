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


# Trigger prefix options
TRIGGER_PREFIXES = [
    (":", "Colon (default)"),
    (";", "Semicolon"),
    ("//", "Double slash"),
    ("::", "Double colon"),
    ("", "None (blank)"),
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
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_base};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 0)

        # Icon and title
        title_row = QWidget()
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        icon_label = QLabel("\u270F")  # Pencil emoji
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                color: {colors.primary};
                background-color: transparent;
            }}
        """)
        title_layout.addWidget(icon_label)

        self.header_text = QLabel("New Entry")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.header_text.setFont(title_font)
        self.header_text.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                background-color: transparent;
            }}
        """)
        title_layout.addWidget(self.header_text)

        header_layout.addWidget(title_row)
        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("\u2715")  # X symbol
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

    def _create_action_buttons(self) -> QWidget:
        """Create action buttons row."""
        colors = self.theme_manager.colors

        actions = QWidget()
        actions.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_base};
                border-bottom: 1px solid {colors.border_muted};
            }}
        """)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(20, 16, 20, 16)

        # Left side buttons (Delete, Clone)
        left_buttons = QWidget()
        left_layout = QHBoxLayout(left_buttons)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.delete_btn = QPushButton("\u1F5D1 Delete")
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

        self.clone_btn = QPushButton("\u2398 Clone")
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
            }}
        """)
        self.clone_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(self.clone_btn)

        actions_layout.addWidget(left_buttons)
        actions_layout.addStretch()

        # Save button
        self.save_btn = QPushButton("\u1F4BE Save")
        self.save_btn.clicked.connect(self._on_save_click)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
        """)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(self.save_btn)

        return actions

    def _create_form(self) -> QWidget:
        """Create the entry form."""
        colors = self.theme_manager.colors

        form = QWidget()
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(20, 16, 20, 20)
        form_layout.setSpacing(16)

        # Trigger section
        trigger_section = self._create_trigger_section()
        form_layout.addWidget(trigger_section)

        # Replacement section
        replacement_section = self._create_replacement_section()
        form_layout.addWidget(replacement_section)

        # Tags section
        tags_section = self._create_tags_section()
        form_layout.addWidget(tags_section)

        # Advanced options (collapsible)
        self.advanced_section = self._create_advanced_section()
        form_layout.addWidget(self.advanced_section)

        form_layout.addStretch()

        return form

    def _create_trigger_section(self) -> QWidget:
        """Create trigger input section."""
        colors = self.theme_manager.colors

        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(6)

        # Label
        label = QLabel("Trigger")
        label_font = QFont()
        label_font.setPointSize(10)
        label_font.setBold(True)
        label.setFont(label_font)
        label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        section_layout.addWidget(label)

        # Prefix dropdown and trigger input
        input_row = QWidget()
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        self.prefix_dropdown = QComboBox()
        for prefix, display in TRIGGER_PREFIXES:
            self.prefix_dropdown.addItem(display if prefix else "(none)", prefix)
        self.prefix_dropdown.setCurrentIndex(0)  # Default to ":"
        self.prefix_dropdown.setFixedWidth(140)
        input_layout.addWidget(self.prefix_dropdown)

        self.trigger_field = QLineEdit()
        self.trigger_field.setPlaceholderText("Enter trigger text...")
        input_layout.addWidget(self.trigger_field, stretch=1)

        section_layout.addWidget(input_row)

        return section

    def _create_replacement_section(self) -> QWidget:
        """Create replacement text section."""
        colors = self.theme_manager.colors

        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(6)

        # Header with label and buttons
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Replacement")
        label_font = QFont()
        label_font.setPointSize(10)
        label_font.setBold(True)
        label.setFont(label_font)
        label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        header_layout.addWidget(label)
        header_layout.addStretch()

        # Insert variable button
        insert_var_btn = QPushButton("\u007B\u007B Insert Variable")
        insert_var_btn.clicked.connect(self._show_variable_menu)
        insert_var_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.primary};
                border: none;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        insert_var_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(insert_var_btn)

        section_layout.addWidget(header)

        # Text editor
        self.replacement_field = QTextEdit()
        self.replacement_field.setPlaceholderText("Enter replacement text...\n\nType {{ to insert variables and forms")
        self.replacement_field.setMinimumHeight(120)
        self.replacement_field.setMaximumHeight(200)
        font = QFont("Consolas, Monaco, monospace")
        font.setPointSize(10)
        self.replacement_field.setFont(font)
        section_layout.addWidget(self.replacement_field)

        return section

    def _create_tags_section(self) -> QWidget:
        """Create tags input section."""
        colors = self.theme_manager.colors

        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(8)

        # Label
        label = QLabel("Tags")
        label_font = QFont()
        label_font.setPointSize(10)
        label_font.setBold(True)
        label.setFont(label_font)
        label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_secondary};
                background-color: transparent;
            }}
        """)
        section_layout.addWidget(label)

        # Tags display and input
        tags_row = QWidget()
        tags_layout = QHBoxLayout(tags_row)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(8)

        # Tags container (will hold tag chips)
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(4)
        self.tags_layout.addStretch()
        tags_layout.addWidget(self.tags_container, stretch=1)

        # Add tag input
        self.add_tag_field = QLineEdit()
        self.add_tag_field.setPlaceholderText("Add tag...")
        self.add_tag_field.setFixedWidth(120)
        self.add_tag_field.returnPressed.connect(self._on_add_tag)
        tags_layout.addWidget(self.add_tag_field)

        section_layout.addWidget(tags_row)

        return section

    def _create_advanced_section(self) -> QWidget:
        """Create advanced options section (collapsible)."""
        colors = self.theme_manager.colors

        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                border-top: 1px solid {colors.border_muted};
                padding-top: 8px;
            }}
        """)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 8, 0, 0)
        section_layout.setSpacing(0)

        # Toggle header
        self.advanced_toggle = QPushButton("\u25B6 Advanced Options")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.clicked.connect(self._toggle_advanced)
        self.advanced_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: none;
                text-align: left;
                padding: 8px 0px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                color: {colors.text_primary};
            }}
        """)
        self.advanced_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        section_layout.addWidget(self.advanced_toggle)

        # Advanced content (hidden by default)
        self.advanced_content = QWidget()
        self.advanced_content.setVisible(False)
        content_layout = QVBoxLayout(self.advanced_content)
        content_layout.setContentsMargins(16, 8, 0, 0)
        content_layout.setSpacing(6)

        # Trigger Settings
        trigger_label = QLabel("Trigger Settings")
        trigger_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {colors.text_tertiary};
                background-color: transparent;
            }}
        """)
        content_layout.addWidget(trigger_label)

        self.word_trigger_cb = QCheckBox("Word trigger (expand at word boundaries)")
        self.word_trigger_cb.setChecked(True)
        content_layout.addWidget(self.word_trigger_cb)

        self.propagate_case_cb = QCheckBox("Propagate case (match input casing)")
        content_layout.addWidget(self.propagate_case_cb)

        # Matching
        matching_label = QLabel("Matching")
        matching_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {colors.text_tertiary};
                background-color: transparent;
                margin-top: 8px;
            }}
        """)
        content_layout.addWidget(matching_label)

        self.regex_cb = QCheckBox("Regex trigger")
        content_layout.addWidget(self.regex_cb)

        self.case_insensitive_cb = QCheckBox("Case insensitive matching")
        content_layout.addWidget(self.case_insensitive_cb)

        # Behavior
        behavior_label = QLabel("Behavior")
        behavior_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {colors.text_tertiary};
                background-color: transparent;
                margin-top: 8px;
            }}
        """)
        content_layout.addWidget(behavior_label)

        self.force_clipboard_cb = QCheckBox("Force clipboard paste")
        content_layout.addWidget(self.force_clipboard_cb)

        self.passive_cb = QCheckBox("Passive mode (manual trigger only)")
        content_layout.addWidget(self.passive_cb)

        # App Filtering
        filtering_label = QLabel("App Filtering")
        filtering_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {colors.text_tertiary};
                background-color: transparent;
                margin-top: 8px;
            }}
        """)
        content_layout.addWidget(filtering_label)

        self.filter_apps_field = QLineEdit()
        self.filter_apps_field.setPlaceholderText("chrome, slack, vscode (comma-separated)")
        content_layout.addWidget(self.filter_apps_field)

        section_layout.addWidget(self.advanced_content)

        return section

    def _toggle_advanced(self):
        """Toggle advanced options visibility."""
        is_visible = self.advanced_content.isVisible()
        self.advanced_content.setVisible(not is_visible)
        icon = "\u25BC" if not is_visible else "\u25B6"
        self.advanced_toggle.setText(f"{icon} Advanced Options")

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
                padding: 4px 8px;
            }}
        """)
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(8, 4, 4, 4)
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

        remove_btn = QPushButton("\u2715")
        remove_btn.setFixedSize(16, 16)
        remove_btn.clicked.connect(lambda: self._remove_tag_chip(chip))
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.tag_text};
                border: none;
                font-size: 10px;
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
