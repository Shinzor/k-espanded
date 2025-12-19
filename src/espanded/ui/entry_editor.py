"""Entry editor component for creating and editing entries."""

import flet as ft
from typing import Callable
from uuid import uuid4

from espanded.ui.theme import ThemeManager
from espanded.ui.components.autocomplete import VARIABLE_CATEGORIES
from espanded.core.models import Entry


# Available trigger prefixes
TRIGGER_PREFIXES = [
    (":", "Colon (default)"),
    (";", "Semicolon"),
    ("//", "Double slash"),
    ("::", "Double colon"),
    ("", "None (blank)"),
]


class EntryEditor(ft.Container):
    """Editor for creating and modifying entries."""

    def __init__(
        self,
        theme: ThemeManager,
        on_save: Callable[[Entry], None],
        on_delete: Callable[[Entry], None],
        on_clone: Callable[[Entry], None],
        on_close: Callable[[], None],
    ):
        super().__init__()
        self.theme = theme
        self.on_save = on_save
        self.on_delete = on_delete
        self.on_clone = on_clone
        self.on_close = on_close

        self.current_entry: Entry | None = None
        self.is_new: bool = True
        self._mounted = False

        self._build()

    def did_mount(self):
        """Called when control is added to page."""
        self._mounted = True

    def will_unmount(self):
        """Called when control is removed from page."""
        self._mounted = False

    def _build(self):
        """Build the editor layout."""
        colors = self.theme.colors

        # Header
        self.header_text = ft.Text(
            "New Entry",
            size=18,
            weight=ft.FontWeight.W_600,
            color=colors.text_primary,
        )

        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.EDIT_OUTLINED, size=20, color=colors.primary),
                            self.header_text,
                        ],
                        spacing=10,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=colors.text_secondary,
                        tooltip="Close",
                        on_click=lambda e: self.on_close(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            margin=ft.margin.only(bottom=20),
        )

        # Trigger field with prefix dropdown
        self.prefix_dropdown = ft.Dropdown(
            value=":",
            options=[
                ft.dropdown.Option(key=prefix, text=prefix if prefix else "(none)")
                for prefix, _ in TRIGGER_PREFIXES
            ],
            width=80,
            bgcolor=colors.bg_surface,
            border_color=colors.border_muted,
            focused_border_color=colors.primary,
            text_style=ft.TextStyle(color=colors.text_primary),
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )

        self.trigger_field = ft.TextField(
            hint_text="Enter trigger text...",
            border_radius=8,
            bgcolor=colors.bg_surface,
            border_color=colors.border_muted,
            focused_border_color=colors.primary,
            text_style=ft.TextStyle(color=colors.text_primary),
            hint_style=ft.TextStyle(color=colors.text_tertiary),
            expand=True,
        )

        trigger_row = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Trigger", size=13, weight=ft.FontWeight.W_500, color=colors.text_secondary),
                    ft.Row(
                        controls=[
                            self.prefix_dropdown,
                            self.trigger_field,
                        ],
                        spacing=8,
                    ),
                ],
                spacing=6,
            ),
            margin=ft.margin.only(bottom=16),
        )

        # Replacement field with autocomplete
        self.replacement_field = ft.TextField(
            hint_text="Enter replacement text...\n\nType {{ to insert variables and forms",
            multiline=True,
            min_lines=5,
            max_lines=10,
            border_radius=8,
            bgcolor=colors.bg_surface,
            border_color=colors.border_muted,
            focused_border_color=colors.primary,
            text_style=ft.TextStyle(color=colors.text_primary),
            hint_style=ft.TextStyle(color=colors.text_tertiary),
            on_change=self._on_replacement_change,
        )

        # View source button
        view_source_btn = ft.TextButton(
            text="View Source",
            icon=ft.Icons.CODE,
            style=ft.ButtonStyle(color=colors.text_secondary),
            on_click=self._on_view_source,
        )

        # Variable insert popup menu
        insert_var_btn = ft.PopupMenuButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DATA_OBJECT, size=16, color=colors.primary),
                    ft.Text("Insert Variable", size=13, color=colors.primary),
                ],
                spacing=4,
            ),
            items=self._build_variable_menu_items(),
        )

        replacement_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Replacement", size=13, weight=ft.FontWeight.W_500, color=colors.text_secondary),
                            ft.Row(
                                controls=[insert_var_btn, view_source_btn],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.replacement_field,
                ],
                spacing=6,
            ),
            margin=ft.margin.only(bottom=16),
        )

        # Tags section
        self.tags_row = ft.Row(
            controls=[],
            spacing=8,
            wrap=True,
        )

        self.add_tag_field = ft.TextField(
            hint_text="Add tag...",
            width=120,
            height=32,
            border_radius=16,
            bgcolor=colors.bg_surface,
            border_color=colors.border_muted,
            focused_border_color=colors.primary,
            text_style=ft.TextStyle(color=colors.text_primary, size=12),
            hint_style=ft.TextStyle(color=colors.text_tertiary, size=12),
            content_padding=ft.padding.symmetric(horizontal=12, vertical=4),
            on_submit=self._on_add_tag,
        )

        tags_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Tags", size=13, weight=ft.FontWeight.W_500, color=colors.text_secondary),
                    ft.Row(
                        controls=[
                            self.tags_row,
                            self.add_tag_field,
                        ],
                        spacing=8,
                        wrap=True,
                    ),
                ],
                spacing=8,
            ),
            margin=ft.margin.only(bottom=16),
        )

        # Advanced options (collapsed by default)
        self.advanced_expanded = False
        self.advanced_section = self._build_advanced_options()

        # Action buttons
        self.delete_btn = ft.OutlinedButton(
            text="Delete",
            icon=ft.Icons.DELETE_OUTLINE,
            style=ft.ButtonStyle(
                color=colors.error,
                side=ft.BorderSide(1, colors.error),
            ),
            on_click=self._on_delete_click,
        )

        self.clone_btn = ft.OutlinedButton(
            text="Clone",
            icon=ft.Icons.COPY,
            style=ft.ButtonStyle(
                color=colors.text_secondary,
                side=ft.BorderSide(1, colors.border_default),
            ),
            on_click=self._on_clone_click,
        )

        self.save_btn = ft.ElevatedButton(
            text="Save",
            icon=ft.Icons.SAVE,
            bgcolor=colors.primary,
            color=colors.text_inverse,
            on_click=self._on_save_click,
        )

        # Action buttons row - fixed at top
        actions_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[self.delete_btn, self.clone_btn],
                        spacing=8,
                    ),
                    self.save_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(bottom=16),
            border=ft.border.only(bottom=ft.BorderSide(1, colors.border_muted)),
        )

        # Scrollable form content
        form_content = ft.Column(
            controls=[
                trigger_row,
                replacement_section,
                tags_section,
                self.advanced_section,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # Main layout with fixed header/actions and scrollable form
        self.content = ft.Column(
            controls=[
                header,
                actions_row,
                form_content,
            ],
            spacing=0,
            expand=True,
        )

        self.expand = True
        self.padding = 20

    def _build_advanced_options(self) -> ft.Container:
        """Build the advanced options expandable section."""
        colors = self.theme.colors

        # Checkbox options
        self.word_trigger_cb = ft.Checkbox(
            label="Word trigger (expand at word boundaries)",
            value=True,
            fill_color=colors.primary,
        )

        self.propagate_case_cb = ft.Checkbox(
            label="Propagate case (match input casing)",
            value=False,
            fill_color=colors.primary,
        )

        self.case_insensitive_cb = ft.Checkbox(
            label="Case insensitive matching",
            value=False,
            fill_color=colors.primary,
        )

        self.force_clipboard_cb = ft.Checkbox(
            label="Force clipboard paste",
            value=False,
            fill_color=colors.primary,
        )

        self.passive_cb = ft.Checkbox(
            label="Passive mode (manual trigger only)",
            value=False,
            fill_color=colors.primary,
        )

        self.regex_cb = ft.Checkbox(
            label="Regex trigger",
            value=False,
            fill_color=colors.primary,
        )

        # Filter apps field
        self.filter_apps_field = ft.TextField(
            hint_text="chrome, slack, vscode (comma-separated)",
            border_radius=8,
            bgcolor=colors.bg_surface,
            border_color=colors.border_muted,
            focused_border_color=colors.primary,
            text_style=ft.TextStyle(color=colors.text_primary, size=13),
            hint_style=ft.TextStyle(color=colors.text_tertiary, size=13),
        )

        # Expandable content
        self.advanced_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Trigger Settings",
                        size=12,
                        weight=ft.FontWeight.W_500,
                        color=colors.text_tertiary,
                    ),
                    self.word_trigger_cb,
                    self.propagate_case_cb,
                    ft.Container(height=8),
                    ft.Text(
                        "Matching",
                        size=12,
                        weight=ft.FontWeight.W_500,
                        color=colors.text_tertiary,
                    ),
                    self.regex_cb,
                    self.case_insensitive_cb,
                    ft.Container(height=8),
                    ft.Text(
                        "Behavior",
                        size=12,
                        weight=ft.FontWeight.W_500,
                        color=colors.text_tertiary,
                    ),
                    self.force_clipboard_cb,
                    self.passive_cb,
                    ft.Container(height=8),
                    ft.Text(
                        "App Filtering",
                        size=12,
                        weight=ft.FontWeight.W_500,
                        color=colors.text_tertiary,
                    ),
                    self.filter_apps_field,
                ],
                spacing=4,
            ),
            padding=ft.padding.only(left=16, top=8, bottom=8),
            visible=False,
        )

        # Header row with toggle icon stored as class attribute
        self.advanced_toggle_icon = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_RIGHT,
            size=18,
            color=colors.text_secondary,
        )

        header_row = ft.Container(
            content=ft.Row(
                controls=[
                    self.advanced_toggle_icon,
                    ft.Text(
                        "Advanced Options",
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=colors.text_secondary,
                    ),
                ],
                spacing=4,
            ),
            on_click=self._toggle_advanced,
            padding=ft.padding.symmetric(vertical=8),
            ink=True,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    header_row,
                    self.advanced_content,
                ],
                spacing=0,
            ),
            border=ft.border.only(top=ft.BorderSide(1, colors.border_muted)),
            padding=ft.padding.only(top=8),
        )

    def _toggle_advanced(self, e=None):
        """Toggle advanced options visibility."""
        self.advanced_expanded = not self.advanced_expanded
        self.advanced_content.visible = self.advanced_expanded
        self.advanced_toggle_icon.name = ft.Icons.KEYBOARD_ARROW_DOWN if self.advanced_expanded else ft.Icons.KEYBOARD_ARROW_RIGHT
        if self._mounted:
            self.update()

    def _build_tag_chip(self, tag: str) -> ft.Container:
        """Build a tag chip."""
        colors = self.theme.colors

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(tag, size=12, color=colors.tag_text),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=14,
                        icon_color=colors.tag_text,
                        tooltip="Remove tag",
                        on_click=lambda e, t=tag: self._on_remove_tag(t),
                        padding=0,
                        width=20,
                        height=20,
                    ),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor=colors.tag_bg,
            padding=ft.padding.only(left=10, right=4, top=4, bottom=4),
            border_radius=16,
        )

    def set_entry(self, entry: Entry | None):
        """Set the entry to edit."""
        self.current_entry = entry
        self.is_new = entry is None or not entry.id

        if entry:
            self.header_text.value = "Edit Entry"
            self.prefix_dropdown.value = entry.prefix
            self.trigger_field.value = entry.trigger
            self.replacement_field.value = entry.replacement

            # Set tags
            self.tags_row.controls.clear()
            for tag in entry.tags:
                self.tags_row.controls.append(self._build_tag_chip(tag))

            # Set advanced options
            self.word_trigger_cb.value = entry.word
            self.propagate_case_cb.value = entry.propagate_case
            self.regex_cb.value = entry.regex
            self.case_insensitive_cb.value = entry.case_insensitive
            self.force_clipboard_cb.value = entry.force_clipboard
            self.passive_cb.value = entry.passive

            if entry.filter_apps:
                self.filter_apps_field.value = ", ".join(entry.filter_apps)
            else:
                self.filter_apps_field.value = ""

            # Show delete/clone buttons
            self.delete_btn.visible = True
            self.clone_btn.visible = True
        else:
            self.header_text.value = "New Entry"
            self.prefix_dropdown.value = ":"
            self.trigger_field.value = ""
            self.replacement_field.value = ""
            self.tags_row.controls.clear()

            # Reset advanced options
            self.word_trigger_cb.value = True
            self.propagate_case_cb.value = False
            self.regex_cb.value = False
            self.case_insensitive_cb.value = False
            self.force_clipboard_cb.value = False
            self.passive_cb.value = False
            self.filter_apps_field.value = ""

            # Hide delete/clone buttons for new entry
            self.delete_btn.visible = False
            self.clone_btn.visible = False

        # Only update if mounted
        if self._mounted:
            self.update()

    def _get_current_tags(self) -> list[str]:
        """Get current tags from the UI."""
        tags = []
        for control in self.tags_row.controls:
            if isinstance(control, ft.Container):
                row = control.content
                if isinstance(row, ft.Row) and row.controls:
                    text = row.controls[0]
                    if isinstance(text, ft.Text):
                        tags.append(text.value)
        return tags

    def _on_add_tag(self, e):
        """Handle adding a new tag."""
        tag = e.control.value.strip()
        if tag and tag not in self._get_current_tags():
            self.tags_row.controls.append(self._build_tag_chip(tag))
        e.control.value = ""
        if self._mounted:
            self.update()

    def _on_remove_tag(self, tag: str):
        """Handle removing a tag."""
        for control in self.tags_row.controls[:]:
            if isinstance(control, ft.Container):
                row = control.content
                if isinstance(row, ft.Row) and row.controls:
                    text = row.controls[0]
                    if isinstance(text, ft.Text) and text.value == tag:
                        self.tags_row.controls.remove(control)
                        break
        if self._mounted:
            self.update()

    def _build_entry_from_form(self) -> Entry | None:
        """Build an Entry object from form values."""
        trigger = self.trigger_field.value.strip() if self.trigger_field.value else ""
        if not trigger:
            return None

        filter_apps = None
        if self.filter_apps_field.value:
            filter_apps = [a.strip() for a in self.filter_apps_field.value.split(",") if a.strip()]

        return Entry(
            id=self.current_entry.id if self.current_entry and self.current_entry.id else str(uuid4()),
            trigger=trigger,
            prefix=self.prefix_dropdown.value,
            replacement=self.replacement_field.value,
            tags=self._get_current_tags(),
            word=self.word_trigger_cb.value,
            propagate_case=self.propagate_case_cb.value,
            regex=self.regex_cb.value,
            case_insensitive=self.case_insensitive_cb.value,
            force_clipboard=self.force_clipboard_cb.value,
            passive=self.passive_cb.value,
            filter_apps=filter_apps,
        )

    def _on_save_click(self, e):
        """Handle save button click."""
        entry = self._build_entry_from_form()
        if not entry:
            # Show error if trigger is empty
            if self.page:
                colors = self.theme.colors
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Trigger is required", color=colors.text_primary),
                    bgcolor=colors.error,
                    duration=2000,
                )
                self.page.snack_bar.open = True
                self.page.update()
            return
        self.on_save(entry)

    def _on_delete_click(self, e):
        """Handle delete button click."""
        if self.current_entry:
            self.on_delete(self.current_entry)

    def _on_clone_click(self, e):
        """Handle clone button click."""
        if self.current_entry:
            self.on_clone(self.current_entry)

    def _on_view_source(self, e):
        """Handle view source button click - show YAML source dialog."""
        if not self.page:
            return

        colors = self.theme.colors

        # Build entry from current form values
        entry = self._build_entry_from_form()
        if not entry:
            return

        # Convert to YAML
        from espanded.core.yaml_handler import YAMLHandler
        handler = YAMLHandler()
        yaml_source = handler.export_to_yaml(entry)

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def copy_to_clipboard(e):
            self.page.set_clipboard(yaml_source)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Copied to clipboard!", color=colors.text_primary),
                bgcolor=colors.success,
                duration=2000,
            )
            self.page.snack_bar.open = True
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CODE, color=colors.primary),
                    ft.Text("YAML Source", color=colors.text_primary),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                yaml_source,
                                font_family="monospace",
                                size=12,
                                color=colors.text_primary,
                                selectable=True,
                            ),
                            bgcolor=colors.bg_elevated,
                            padding=16,
                            border_radius=8,
                            border=ft.border.all(1, colors.border_muted),
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=500,
                height=300,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
                ft.ElevatedButton(
                    "Copy",
                    icon=ft.Icons.COPY,
                    bgcolor=colors.primary,
                    color=colors.text_inverse,
                    on_click=copy_to_clipboard,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors.bg_surface,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    # Variable insertion methods

    def _build_variable_menu_items(self) -> list[ft.PopupMenuItem]:
        """Build popup menu items for variable insertion."""
        items = []

        for category in VARIABLE_CATEGORIES:
            # Add category header
            items.append(ft.PopupMenuItem(
                text=category["name"],
                disabled=True,
            ))

            # Add items in category
            for item in category["items"]:
                items.append(ft.PopupMenuItem(
                    text=f"{item.label}",
                    on_click=lambda e, v=item.value: self._insert_variable_at_cursor(v),
                ))

            # Add divider between categories
            items.append(ft.PopupMenuItem())

        return items[:-1]  # Remove last divider

    def _insert_variable_at_cursor(self, variable: str):
        """Insert a variable at the current cursor position in the replacement field."""
        current = self.replacement_field.value or ""
        self.replacement_field.value = current + variable
        if self._mounted:
            self.update()

    def _on_replacement_change(self, e):
        """Handle replacement text change."""
        # Just a simple handler, no autocomplete logic needed
        pass
