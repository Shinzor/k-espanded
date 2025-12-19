"""Autocomplete component for {{ variable insertion."""

import flet as ft
from typing import Callable
from dataclasses import dataclass

from espanded.ui.theme import ThemeManager


@dataclass
class AutocompleteItem:
    """An autocomplete suggestion item."""
    value: str
    label: str
    description: str
    category: str


# All Espanso variables organized by category
VARIABLE_CATEGORIES = [
    {
        "name": "Date & Time",
        "icon": "calendar_today",
        "items": [
            AutocompleteItem("{{date}}", "{{date}}", "Current date (locale format)", "Date & Time"),
            AutocompleteItem("{{date:%Y-%m-%d}}", "{{date:FORMAT}}", "Custom date format", "Date & Time"),
            AutocompleteItem("{{time}}", "{{time}}", "Current time", "Date & Time"),
            AutocompleteItem("{{time:%H:%M}}", "{{time:FORMAT}}", "Custom time format", "Date & Time"),
        ],
    },
    {
        "name": "Clipboard",
        "icon": "content_paste",
        "items": [
            AutocompleteItem("{{clipboard}}", "{{clipboard}}", "Current clipboard content", "Clipboard"),
        ],
    },
    {
        "name": "Random",
        "icon": "casino",
        "items": [
            AutocompleteItem("{{random:uuid}}", "{{random:uuid}}", "Random UUID", "Random"),
            AutocompleteItem("{{random:chars:5}}", "{{random:chars:N}}", "Random characters", "Random"),
            AutocompleteItem("{{random:alnum:5}}", "{{random:alnum:N}}", "Random alphanumeric", "Random"),
            AutocompleteItem("{{random:num:5}}", "{{random:num:N}}", "Random numbers", "Random"),
        ],
    },
    {
        "name": "Forms",
        "icon": "text_fields",
        "items": [
            AutocompleteItem("{{form:text:Label}}", "{{form:text:LABEL}}", "Single line text input", "Forms"),
            AutocompleteItem("{{form:multiline:Label}}", "{{form:multiline:LABEL}}", "Multi-line text input", "Forms"),
            AutocompleteItem("{{form:choice:Opt1,Opt2}}", "{{form:choice:OPTIONS}}", "Dropdown selection", "Forms"),
            AutocompleteItem("{{form:list:Label}}", "{{form:list:LABEL}}", "List input", "Forms"),
        ],
    },
    {
        "name": "Scripts",
        "icon": "terminal",
        "items": [
            AutocompleteItem("{{output:shell:command}}", "{{output:shell:CMD}}", "Shell command output", "Scripts"),
            AutocompleteItem("{{output:cmd:command}}", "{{output:cmd:CMD}}", "CMD command (Windows)", "Scripts"),
            AutocompleteItem("{{output:powershell:command}}", "{{output:powershell:CMD}}", "PowerShell command", "Scripts"),
        ],
    },
    {
        "name": "Cursor",
        "icon": "text_select_start",
        "items": [
            AutocompleteItem("$|$", "$|$", "Cursor position after expansion", "Cursor"),
        ],
    },
]


def get_all_items() -> list[AutocompleteItem]:
    """Get all autocomplete items as a flat list."""
    items = []
    for category in VARIABLE_CATEGORIES:
        items.extend(category["items"])
    return items


def filter_items(query: str) -> list[AutocompleteItem]:
    """Filter items by query string."""
    if not query:
        return get_all_items()

    query = query.lower().replace("{{", "").replace("}}", "")
    results = []

    for item in get_all_items():
        # Match against value, label, description, or category
        searchable = f"{item.value} {item.label} {item.description} {item.category}".lower()
        if query in searchable:
            results.append(item)

    return results


class AutocompleteDropdown(ft.Container):
    """Dropdown component for {{ autocomplete."""

    def __init__(
        self,
        theme: ThemeManager,
        on_select: Callable[[str], None],
        on_dismiss: Callable[[], None],
    ):
        super().__init__()
        self.theme = theme
        self.on_select = on_select
        self.on_dismiss = on_dismiss

        self.items: list[AutocompleteItem] = []
        self.selected_index: int = 0
        self.query: str = ""

        self._build()

    def _build(self):
        """Build the dropdown UI."""
        colors = self.theme.colors

        self.item_list = ft.ListView(
            spacing=2,
            padding=8,
            height=300,
        )

        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CODE, size=14, color=colors.primary),
                                ft.Text(
                                    "Insert Variable",
                                    size=12,
                                    weight=ft.FontWeight.W_500,
                                    color=colors.text_secondary,
                                ),
                            ],
                            spacing=6,
                        ),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border=ft.border.only(bottom=ft.BorderSide(1, colors.border_muted)),
                    ),
                    # Items
                    self.item_list,
                    # Footer hint
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("↑↓ Navigate", size=10, color=colors.text_tertiary),
                                ft.Text("Enter Select", size=10, color=colors.text_tertiary),
                                ft.Text("Esc Close", size=10, color=colors.text_tertiary),
                            ],
                            spacing=12,
                        ),
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border=ft.border.only(top=ft.BorderSide(1, colors.border_muted)),
                    ),
                ],
                spacing=0,
            ),
            bgcolor=colors.bg_elevated,
            border_radius=8,
            border=ft.border.all(1, colors.border_default),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
            width=350,
        )

        self.visible = False

    def _build_item(self, item: AutocompleteItem, index: int) -> ft.Container:
        """Build a single autocomplete item."""
        colors = self.theme.colors
        is_selected = index == self.selected_index

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        item.label,
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=colors.primary if is_selected else colors.text_primary,
                        font_family="monospace",
                    ),
                    ft.Text(
                        item.description,
                        size=11,
                        color=colors.text_secondary,
                    ),
                ],
                spacing=2,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=6,
            bgcolor=colors.entry_selected if is_selected else None,
            on_hover=lambda e, i=index: self._on_item_hover(e, i),
            on_click=lambda e, itm=item: self._on_item_click(itm),
        )

    def show(self, query: str = ""):
        """Show the dropdown with filtered items."""
        self.query = query
        self.items = filter_items(query)
        self.selected_index = 0
        self._refresh_list()
        self.visible = True
        self.update()

    def hide(self):
        """Hide the dropdown."""
        self.visible = False
        self.update()

    def _refresh_list(self):
        """Refresh the item list."""
        self.item_list.controls.clear()

        if not self.items:
            colors = self.theme.colors
            self.item_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No matches found",
                        size=12,
                        color=colors.text_tertiary,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            # Group by category
            current_category = None
            for i, item in enumerate(self.items):
                if item.category != current_category:
                    current_category = item.category
                    colors = self.theme.colors
                    self.item_list.controls.append(
                        ft.Container(
                            content=ft.Text(
                                current_category,
                                size=10,
                                weight=ft.FontWeight.W_600,
                                color=colors.text_tertiary,
                            ),
                            padding=ft.padding.only(left=12, top=8, bottom=4),
                        )
                    )
                self.item_list.controls.append(self._build_item(item, i))

    def update_filter(self, query: str):
        """Update the filter query."""
        self.query = query
        self.items = filter_items(query)
        self.selected_index = 0
        self._refresh_list()
        self.update()

    def move_selection(self, direction: int):
        """Move selection up (-1) or down (+1)."""
        if not self.items:
            return

        self.selected_index = (self.selected_index + direction) % len(self.items)
        self._refresh_list()
        self.update()

    def select_current(self):
        """Select the currently highlighted item."""
        if self.items and 0 <= self.selected_index < len(self.items):
            item = self.items[self.selected_index]
            self.on_select(item.value)
            self.hide()

    def _on_item_hover(self, e, index: int):
        """Handle item hover."""
        if e.data:  # Mouse entered
            self.selected_index = index
            self._refresh_list()
            self.update()

    def _on_item_click(self, item: AutocompleteItem):
        """Handle item click."""
        self.on_select(item.value)
        self.hide()


class AutocompleteTextField(ft.Container):
    """Text field with {{ autocomplete support."""

    def __init__(
        self,
        theme: ThemeManager,
        hint_text: str = "",
        value: str = "",
        multiline: bool = False,
        min_lines: int = 1,
        max_lines: int = 10,
        on_change: Callable[[str], None] | None = None,
    ):
        super().__init__()
        self.theme = theme
        self._value = value
        self._on_change = on_change

        # Create the text field
        colors = theme.colors
        self.text_field = ft.TextField(
            value=value,
            hint_text=hint_text,
            multiline=multiline,
            min_lines=min_lines,
            max_lines=max_lines,
            border_radius=8,
            bgcolor=colors.bg_surface,
            border_color=colors.border_muted,
            focused_border_color=colors.primary,
            text_style=ft.TextStyle(color=colors.text_primary),
            hint_style=ft.TextStyle(color=colors.text_tertiary),
            on_change=self._handle_change,
            on_focus=self._handle_focus,
            on_blur=self._handle_blur,
        )

        # Create the autocomplete dropdown
        self.dropdown = AutocompleteDropdown(
            theme=theme,
            on_select=self._insert_variable,
            on_dismiss=self._hide_dropdown,
        )

        # Track cursor position for {{ detection
        self._last_text = value
        self._autocomplete_start = -1

        self._build()

    def _build(self):
        """Build the component."""
        self.content = ft.Stack(
            controls=[
                self.text_field,
                ft.Container(
                    content=self.dropdown,
                    left=0,
                    top=0,  # Will be positioned dynamically
                ),
            ],
        )

    @property
    def value(self) -> str:
        """Get the text field value."""
        return self.text_field.value or ""

    @value.setter
    def value(self, val: str):
        """Set the text field value."""
        self.text_field.value = val
        self._last_text = val

    def _handle_change(self, e):
        """Handle text change - detect {{ for autocomplete."""
        new_text = e.control.value or ""

        # Check if user just typed {{
        if len(new_text) > len(self._last_text):
            # Find what was added
            added = new_text[len(self._last_text):]

            # Check for {{ trigger
            if "{{" in new_text and self._autocomplete_start == -1:
                # Find the last {{
                start = new_text.rfind("{{")
                if start >= 0:
                    self._autocomplete_start = start
                    query = new_text[start + 2:]  # Text after {{
                    self.dropdown.show(query)

        # If autocomplete is active, update the filter
        if self._autocomplete_start >= 0:
            if "}}" in new_text[self._autocomplete_start:]:
                # User completed the variable, hide dropdown
                self._hide_dropdown()
            else:
                # Update filter with text after {{
                query = new_text[self._autocomplete_start + 2:]
                self.dropdown.update_filter(query)

        self._last_text = new_text

        if self._on_change:
            self._on_change(new_text)

    def _handle_focus(self, e):
        """Handle text field focus."""
        pass

    def _handle_blur(self, e):
        """Handle text field blur."""
        # Delay hiding to allow click on dropdown
        import threading
        def delayed_hide():
            import time
            time.sleep(0.2)
            if self.dropdown.visible:
                self._hide_dropdown()

        threading.Thread(target=delayed_hide, daemon=True).start()

    def _insert_variable(self, variable: str):
        """Insert selected variable into text field."""
        if self._autocomplete_start >= 0:
            # Replace from {{ to current position with the variable
            current = self.text_field.value or ""
            before = current[:self._autocomplete_start]
            after = ""  # For now, just append

            # Find where the partial variable ends
            partial_end = len(current)
            for i in range(self._autocomplete_start + 2, len(current)):
                if current[i] in " \n\t}":
                    partial_end = i
                    break

            after = current[partial_end:]
            self.text_field.value = before + variable + after
            self._last_text = self.text_field.value

        self._hide_dropdown()
        self.update()

        if self._on_change:
            self._on_change(self.text_field.value)

    def _hide_dropdown(self):
        """Hide the autocomplete dropdown."""
        self._autocomplete_start = -1
        self.dropdown.hide()

    def handle_key(self, key: str) -> bool:
        """Handle keyboard events. Returns True if handled.

        Should be called from parent component's keyboard handler.
        """
        if not self.dropdown.visible:
            return False

        if key == "ArrowDown":
            self.dropdown.move_selection(1)
            return True
        elif key == "ArrowUp":
            self.dropdown.move_selection(-1)
            return True
        elif key == "Enter":
            self.dropdown.select_current()
            return True
        elif key == "Escape":
            self._hide_dropdown()
            return True

        return False
