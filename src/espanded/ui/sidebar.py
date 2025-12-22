"""Sidebar with search, view tabs, and scrollable entry list."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QFrame,
    QPushButton,
    QLabel,
    QMenu,
)
from PySide6.QtCore import Qt, Signal

from espanded.ui.theme import ThemeManager
from espanded.ui.components.search_bar import SearchBar
from espanded.ui.components.view_tabs import ViewTabs
from espanded.ui.components.entry_item import EntryItem
from espanded.core.app_state import get_app_state
from espanded.core.models import Entry


class Sidebar(QWidget):
    """Sidebar with search, tabs, and entry list."""

    # Signals
    entry_selected = Signal(object)  # Emits Entry object
    entry_double_clicked = Signal(object)  # Emits Entry object
    add_entry_clicked = Signal()

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.app_state = get_app_state()

        # State
        self._current_view = "all"
        self._search_query = ""
        self._selected_tag: str | None = None
        self._selected_entry_id: str | None = None
        self._entry_widgets: dict[str, EntryItem] = {}

        # Set fixed width
        self.setFixedWidth(280)

        self._setup_ui()
        self._load_entries()

        # Register for entry changes
        self.app_state.entry_manager.add_change_listener(self._on_entries_changed)

    def _setup_ui(self):
        """Build the sidebar layout."""
        colors = self.theme_manager.colors

        # Set background
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_sidebar};
            }}
        """)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Search bar
        self.search_bar = SearchBar(self.theme_manager)
        self.search_bar.search_changed.connect(self._on_search_changed)
        layout.addWidget(self.search_bar)

        # View tabs
        self.view_tabs = ViewTabs(self.theme_manager)
        self.view_tabs.view_changed.connect(self._on_view_changed)
        self.view_tabs.tag_selected.connect(self._on_tag_selected)
        layout.addWidget(self.view_tabs)

        # Scrollable entry list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Entry list container
        self.entry_list_widget = QWidget()
        self.entry_list_widget.setStyleSheet(f"background-color: {colors.bg_sidebar};")
        self.entry_list_layout = QVBoxLayout(self.entry_list_widget)
        self.entry_list_layout.setContentsMargins(0, 8, 0, 8)
        self.entry_list_layout.setSpacing(4)
        self.entry_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.entry_list_widget)
        layout.addWidget(scroll_area, stretch=1)

        # Add Entry button
        self.add_button = QPushButton("+ Add Entry")
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.clicked.connect(self.add_entry_clicked.emit)
        self.add_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
        """)
        layout.addWidget(self.add_button)

    def _load_entries(self):
        """Load entries from entry manager based on current filters."""
        # Get entries based on current view
        if self._current_view == "all":
            entries = self.app_state.entry_manager.get_all_entries()
        elif self._current_view == "favorites":
            entries = [
                e
                for e in self.app_state.entry_manager.get_all_entries()
                if hasattr(e, "favorited") and e.favorited
            ]
        elif self._current_view == "tags":
            if self._selected_tag:
                entries = self.app_state.entry_manager.search_entries(
                    query="", tags=[self._selected_tag]
                )
            else:
                entries = [e for e in self.app_state.entry_manager.get_all_entries() if e.tags]
        elif self._current_view == "trash":
            entries = self.app_state.entry_manager.get_deleted_entries()
        else:
            entries = []

        # Apply search filter
        if self._search_query:
            entries = [
                e
                for e in entries
                if self._search_query.lower() in e.trigger.lower()
                or self._search_query.lower() in e.replacement.lower()
            ]

        # Update tag dropdown with available tags
        all_tags = self.app_state.entry_manager.get_all_tags()
        self.view_tabs.set_available_tags(all_tags)

        # Refresh the list display
        self._refresh_entry_list(entries)

    def _refresh_entry_list(self, entries: list[Entry]):
        """Refresh the entry list display with given entries."""
        # Clear existing widgets
        for widget in self._entry_widgets.values():
            widget.deleteLater()
        self._entry_widgets.clear()

        # Clear layout
        while self.entry_list_layout.count():
            child = self.entry_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Show empty state if no entries
        if not entries:
            self._show_empty_state()
            return

        # Create entry widgets
        for entry in entries:
            entry_widget = EntryItem(entry, self.theme_manager)
            entry_widget.clicked.connect(self._on_entry_clicked)
            entry_widget.double_clicked.connect(self._on_entry_double_clicked)
            entry_widget.context_menu_requested.connect(self._on_entry_context_menu)

            # Set selection state
            if entry.id == self._selected_entry_id:
                entry_widget.set_selected(True)

            self.entry_list_layout.addWidget(entry_widget)
            self._entry_widgets[entry.id] = entry_widget

    def _show_empty_state(self):
        """Show empty state message."""
        colors = self.theme_manager.colors

        # Determine message based on view
        if self._search_query or self._selected_tag:
            message = "No entries found"
        elif self._current_view == "trash":
            message = "Trash is empty"
        elif self._current_view == "favorites":
            message = "No favorites yet"
        elif self._current_view == "tags":
            message = "No tagged entries"
        else:
            message = "No entries yet\nClick + Add Entry to create one"

        # Message label
        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"""
            font-size: 13px;
            color: {colors.text_tertiary};
            padding: 40px 20px;
        """)
        self.entry_list_layout.addWidget(msg_label)

    def _on_search_changed(self, text: str):
        """Handle search query change."""
        self._search_query = text
        self._load_entries()

    def _on_view_changed(self, view: str):
        """Handle view tab change."""
        self._current_view = view
        self._selected_tag = None
        self._load_entries()

    def _on_tag_selected(self, tag: str):
        """Handle specific tag selection."""
        self._selected_tag = tag
        self._current_view = "tags"
        self._load_entries()

    def _on_entry_clicked(self, entry_id: str):
        """Handle entry click."""
        # Update selection
        old_selected = self._selected_entry_id
        self._selected_entry_id = entry_id

        # Update widget states
        if old_selected and old_selected in self._entry_widgets:
            self._entry_widgets[old_selected].set_selected(False)

        if entry_id in self._entry_widgets:
            self._entry_widgets[entry_id].set_selected(True)

        # Emit signal with full entry object
        entry = self.app_state.entry_manager.get_entry(entry_id)
        if entry:
            self.entry_selected.emit(entry)

    def _on_entry_double_clicked(self, entry_id: str):
        """Handle entry double-click."""
        entry = self.app_state.entry_manager.get_entry(entry_id)
        if entry:
            self.entry_double_clicked.emit(entry)

    def _on_entry_context_menu(self, entry_id: str, pos):
        """Handle entry right-click context menu."""
        entry = self.app_state.entry_manager.get_entry(entry_id)
        if not entry:
            return

        colors = self.theme_manager.colors

        # Create context menu
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

        # Menu actions
        if self._current_view == "trash":
            restore_action = menu.addAction("Restore")
            restore_action.triggered.connect(lambda: self._restore_entry(entry_id))

            delete_action = menu.addAction("Delete Permanently")
            delete_action.triggered.connect(lambda: self._permanent_delete_entry(entry_id))
        else:
            edit_action = menu.addAction("Edit")
            edit_action.triggered.connect(lambda: self._edit_entry(entry_id))

            duplicate_action = menu.addAction("Duplicate")
            duplicate_action.triggered.connect(lambda: self._duplicate_entry(entry_id))

            menu.addSeparator()

            favorite_action = menu.addAction("Toggle Favorite")
            favorite_action.triggered.connect(lambda: self._toggle_favorite(entry_id))

            menu.addSeparator()

            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(lambda: self._delete_entry(entry_id))

        # Show menu
        menu.exec(pos)

    def _edit_entry(self, entry_id: str):
        """Edit entry."""
        entry = self.app_state.entry_manager.get_entry(entry_id)
        if entry:
            self.entry_double_clicked.emit(entry)

    def _duplicate_entry(self, entry_id: str):
        """Duplicate entry."""
        self.app_state.entry_manager.clone_entry(entry_id)

    def _toggle_favorite(self, entry_id: str):
        """Toggle entry favorite status."""
        pass  # TODO: Implement when Entry model supports favorited field

    def _delete_entry(self, entry_id: str):
        """Delete entry (move to trash)."""
        self.app_state.entry_manager.delete_entry(entry_id)

    def _restore_entry(self, entry_id: str):
        """Restore entry from trash."""
        self.app_state.entry_manager.restore_entry(entry_id)

    def _permanent_delete_entry(self, entry_id: str):
        """Permanently delete entry."""
        self.app_state.entry_manager.permanent_delete(entry_id)

    def _on_entries_changed(self):
        """Handle entry manager change notification."""
        self._load_entries()

    def refresh_entries(self):
        """Refresh entry list."""
        self._load_entries()

    def clear_selection(self):
        """Clear the current entry selection."""
        if self._selected_entry_id and self._selected_entry_id in self._entry_widgets:
            self._entry_widgets[self._selected_entry_id].set_selected(False)
        self._selected_entry_id = None

    def get_selected_entry(self) -> Entry | None:
        """Get the currently selected entry."""
        if self._selected_entry_id:
            return self.app_state.entry_manager.get_entry(self._selected_entry_id)
        return None
