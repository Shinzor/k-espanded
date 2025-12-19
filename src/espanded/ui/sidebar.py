"""Sidebar component with entry list and tag filtering."""

import flet as ft
from typing import Callable

from espanded.core.app_state import get_app_state
from espanded.ui.theme import ThemeManager
from espanded.core.models import Entry


class Sidebar(ft.Container):
    """Sidebar with search, tag filter, and entry list."""

    def __init__(
        self,
        theme: ThemeManager,
        on_entry_selected: Callable[[Entry], None],
        on_add_entry: Callable[[], None],
    ):
        super().__init__()
        self.theme = theme
        self.on_entry_selected = on_entry_selected
        self.on_add_entry = on_add_entry
        self.app_state = get_app_state()

        self.selected_entry_id: str | None = None
        self.entries: list[Entry] = []
        self.filtered_entries: list[Entry] = []
        self.selected_tags: set[str] = set()
        self.search_query: str = ""
        self.all_tags: dict[str, int] = {}
        self._mounted = False

        self._build()

    def _build(self):
        """Build the sidebar layout."""
        colors = self.theme.colors

        # Search field
        self.search_field = ft.TextField(
            hint_text="Search entries...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=8,
            bgcolor=colors.bg_surface,
            border_color=colors.border_muted,
            focused_border_color=colors.primary,
            text_style=ft.TextStyle(color=colors.text_primary),
            hint_style=ft.TextStyle(color=colors.text_tertiary),
            on_change=self._on_search_change,
            height=42,
        )

        # Tag filter label
        self.tag_label = ft.Text("Tags: All", color=colors.text_secondary, size=13)

        # Tag filter dropdown
        self.tag_dropdown = ft.PopupMenuButton(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.LABEL_OUTLINED, size=16, color=colors.text_secondary),
                        self.tag_label,
                        ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=16, color=colors.text_secondary),
                    ],
                    spacing=4,
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border_radius=8,
                bgcolor=colors.bg_surface,
                border=ft.border.all(1, colors.border_muted),
            ),
            items=[],
        )

        # Entry list
        self.entry_list = ft.ListView(
            spacing=2,
            padding=ft.padding.only(top=8),
            expand=True,
        )

        # Build content
        self.content = ft.Column(
            controls=[
                # Search bar
                ft.Container(
                    content=self.search_field,
                    padding=ft.padding.only(left=12, right=12, top=12, bottom=8),
                ),
                # Tag filter
                ft.Container(
                    content=self.tag_dropdown,
                    padding=ft.padding.only(left=12, right=12, bottom=8),
                ),
                # Divider
                ft.Divider(height=1, color=colors.border_muted),
                # Entry list (includes Add Entry button at top)
                ft.Container(
                    content=self.entry_list,
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=8),
                ),
            ],
            spacing=0,
            expand=True,
        )

        self.expand = True

    def did_mount(self):
        """Called when control is added to page - safe to load data."""
        self._mounted = True
        self._load_entries()

    def will_unmount(self):
        """Called when control is removed from page."""
        self._mounted = False

    def _load_entries(self):
        """Load entries from database."""
        self.entries = self.app_state.entry_manager.get_all_entries()
        self.all_tags = self.app_state.entry_manager.get_all_tags()
        self._update_tag_menu()
        self._apply_filters()

    def _update_tag_menu(self):
        """Update the tag filter menu items."""
        items = [
            ft.PopupMenuItem(
                text="All",
                on_click=lambda e: self._on_clear_tags(),
            ),
        ]

        if self.all_tags:
            items.append(ft.PopupMenuItem())  # Divider

            for tag, count in sorted(self.all_tags.items()):
                items.append(
                    ft.PopupMenuItem(
                        text=f"{tag} ({count})",
                        checked=tag in self.selected_tags,
                        on_click=lambda e, t=tag: self._on_tag_toggle(t),
                    )
                )

        self.tag_dropdown.items = items

    def _build_entry_item(self, entry: Entry) -> ft.Container:
        """Build a single entry list item."""
        colors = self.theme.colors
        is_selected = entry.id == self.selected_entry_id

        trigger_text = f"{entry.prefix}{entry.trigger}" if entry.prefix else entry.trigger
        preview = entry.replacement[:50].replace("\n", " ")
        if len(entry.replacement) > 50:
            preview += "..."

        # Tag chips (show first 2)
        tag_chips = []
        for tag in entry.tags[:2]:
            tag_chips.append(
                ft.Container(
                    content=ft.Text(tag, size=10, color=colors.tag_text),
                    bgcolor=colors.tag_bg,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=10,
                )
            )
        if len(entry.tags) > 2:
            tag_chips.append(
                ft.Text(f"+{len(entry.tags) - 2}", size=10, color=colors.text_tertiary)
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                trigger_text,
                                weight=ft.FontWeight.W_500,
                                color=colors.primary if is_selected else colors.text_primary,
                                size=14,
                                expand=True,
                            ),
                            *tag_chips,
                        ],
                        spacing=4,
                    ),
                    ft.Text(
                        preview,
                        color=colors.text_secondary,
                        size=12,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border_radius=8,
            bgcolor=colors.entry_selected if is_selected else None,
            on_hover=lambda e: self._on_entry_hover(e, entry),
            on_click=lambda e: self._on_entry_click(entry),
            data=entry.id,
        )

    def _apply_filters(self):
        """Apply search and tag filters to entries."""
        # Use entry manager's search if we have a query
        if self.search_query or self.selected_tags:
            self.filtered_entries = self.app_state.entry_manager.search_entries(
                query=self.search_query,
                tags=list(self.selected_tags) if self.selected_tags else None,
            )
        else:
            self.filtered_entries = self.entries.copy()

        self._refresh_list()

    def _build_add_entry_button(self) -> ft.Container:
        """Build the Add Entry button for the entry list."""
        colors = self.theme.colors

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ADD, size=18, color=colors.text_inverse),
                    ft.Text("Add Entry", size=14, color=colors.text_inverse, weight=ft.FontWeight.W_500),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=colors.primary,
            padding=ft.padding.symmetric(vertical=10),
            border_radius=8,
            on_click=lambda e: self.on_add_entry(),
            ink=True,
            margin=ft.margin.only(bottom=8),
        )

    def _refresh_list(self):
        """Refresh the entry list display."""
        self.entry_list.controls.clear()

        # Always add the Add Entry button at the top
        self.entry_list.controls.append(self._build_add_entry_button())

        if not self.filtered_entries:
            colors = self.theme.colors
            self.entry_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=colors.text_tertiary),
                            ft.Text(
                                "No entries found" if self.search_query or self.selected_tags else "No entries yet",
                                color=colors.text_tertiary,
                                size=14,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for entry in self.filtered_entries:
                self.entry_list.controls.append(self._build_entry_item(entry))

        # Only update if mounted
        if self._mounted:
            self.update()

    def _on_search_change(self, e):
        """Handle search text change."""
        self.search_query = e.control.value
        self._apply_filters()

    def _on_clear_tags(self):
        """Clear all tag filters."""
        self.selected_tags.clear()
        self.tag_label.value = "Tags: All"
        self._update_tag_menu()
        self._apply_filters()

    def _on_tag_toggle(self, tag: str):
        """Toggle a tag in the filter."""
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)
        else:
            self.selected_tags.add(tag)

        # Update label
        if not self.selected_tags:
            self.tag_label.value = "Tags: All"
        elif len(self.selected_tags) == 1:
            self.tag_label.value = f"Tag: {list(self.selected_tags)[0]}"
        else:
            self.tag_label.value = f"Tags: {len(self.selected_tags)} selected"

        self._update_tag_menu()
        self._apply_filters()

    def _on_entry_hover(self, e, entry: Entry):
        """Handle entry hover effect."""
        colors = self.theme.colors
        if entry.id != self.selected_entry_id:
            # e.data is "true" when mouse enters, "false" when it leaves
            is_hovering = e.data == "true"
            e.control.bgcolor = colors.entry_hover if is_hovering else None
            e.control.update()

    def _on_entry_click(self, entry: Entry):
        """Handle entry click."""
        self.selected_entry_id = entry.id
        self._refresh_list()
        self.on_entry_selected(entry)

    def clear_selection(self):
        """Clear the current selection."""
        self.selected_entry_id = None
        self._refresh_list()

    def refresh_entries(self):
        """Refresh entries from data source."""
        self._load_entries()
