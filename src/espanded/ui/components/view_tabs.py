"""View tabs component for filtering entries by category."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMenu
from PySide6.QtCore import Qt, Signal

from espanded.ui.theme import ThemeManager


class ViewTabs(QWidget):
    """Tab bar for switching between different entry views."""

    # Signals
    view_changed = Signal(str)  # Emits view name: "all", "favorites", "tags", "trash"
    tag_selected = Signal(str)  # Emits tag name when specific tag is selected

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self._current_view = "all"
        self._available_tags: dict[str, int] = {}
        self._setup_ui()

    def _setup_ui(self):
        """Build the view tabs layout."""
        colors = self.theme_manager.colors

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Create tab buttons (using simple text for cross-platform compatibility)
        self.all_button = self._create_tab_button(
            "All",
            "all",
            "Show all entries",
        )
        layout.addWidget(self.all_button)

        self.favorites_button = self._create_tab_button(
            "Favorites",
            "favorites",
            "Show favorited entries",
        )
        layout.addWidget(self.favorites_button)

        self.tags_button = self._create_tab_button(
            "Tags",
            "tags",
            "Filter by tags",
        )
        layout.addWidget(self.tags_button)

        self.trash_button = self._create_tab_button(
            "Trash",
            "trash",
            "Show deleted entries",
        )
        layout.addWidget(self.trash_button)

        # Add stretch to push buttons to the left
        layout.addStretch()

        # Set initial selection
        self._update_button_styles()

    def _create_tab_button(self, text: str, view_id: str, tooltip: str) -> QPushButton:
        """Create a tab button with consistent styling."""
        colors = self.theme_manager.colors

        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setProperty("view_id", view_id)

        # Connect click handler
        if view_id == "tags":
            button.clicked.connect(self._on_tags_clicked)
        else:
            button.clicked.connect(lambda: self._on_view_clicked(view_id))

        return button

    def _update_button_styles(self):
        """Update button styles based on selected view."""
        colors = self.theme_manager.colors

        for button in [
            self.all_button,
            self.favorites_button,
            self.tags_button,
            self.trash_button,
        ]:
            view_id = button.property("view_id")
            is_selected = view_id == self._current_view

            if is_selected:
                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: {colors.primary};
                        color: {colors.text_inverse};
                        border: none;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-size: 12px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.primary_hover};
                    }}
                """
                )
            else:
                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {colors.text_secondary};
                        border: none;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-size: 12px;
                        font-weight: 500;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.entry_hover};
                        color: {colors.text_primary};
                    }}
                """
                )

    def _on_view_clicked(self, view_id: str):
        """Handle view tab click."""
        if self._current_view != view_id:
            self._current_view = view_id
            self._update_button_styles()
            self.view_changed.emit(view_id)

    def _on_tags_clicked(self):
        """Handle tags button click - show tag dropdown menu."""
        if not self._available_tags:
            # If no tags, just switch to tags view (will show empty state)
            self._on_view_clicked("tags")
            return

        # Create tag menu
        menu = QMenu(self)
        colors = self.theme_manager.colors

        # Style the menu
        menu.setStyleSheet(
            f"""
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
                margin: 4px 0px;
            }}
        """
        )

        # Add "All Tags" option
        all_tags_action = menu.addAction("All Tags")
        all_tags_action.triggered.connect(lambda: self._on_view_clicked("tags"))

        if self._available_tags:
            menu.addSeparator()

            # Add individual tags
            for tag, count in sorted(self._available_tags.items()):
                tag_action = menu.addAction(f"{tag} ({count})")
                tag_action.triggered.connect(lambda checked=False, t=tag: self._on_tag_selected(t))

        # Show menu below the tags button
        button_pos = self.tags_button.mapToGlobal(self.tags_button.rect().bottomLeft())
        menu.exec(button_pos)

    def _on_tag_selected(self, tag: str):
        """Handle specific tag selection."""
        self._current_view = "tags"
        self._update_button_styles()
        self.tag_selected.emit(tag)

    def set_available_tags(self, tags: dict[str, int]):
        """Set the available tags with their counts."""
        self._available_tags = tags

    def get_current_view(self) -> str:
        """Get the currently selected view."""
        return self._current_view

    def set_current_view(self, view: str):
        """Set the current view programmatically."""
        if view in ["all", "favorites", "tags", "trash"]:
            self._current_view = view
            self._update_button_styles()
