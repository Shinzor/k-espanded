"""Trash view component showing deleted entries with restore functionality."""

import flet as ft
from datetime import datetime
from typing import Callable

from espanded.core.app_state import get_app_state
from espanded.core.models import Entry
from espanded.ui.theme import ThemeManager


class TrashView(ft.Container):
    """Trash view showing deleted entries with restore and permanent delete."""

    def __init__(self, theme: ThemeManager, on_close: Callable[[], None]):
        super().__init__()
        self.theme = theme
        self.on_close = on_close
        self.app_state = get_app_state()

        # State
        self.search_query = ""
        self._mounted = False

        self._build()

    def _build(self):
        """Build the trash view layout."""
        colors = self.theme.colors

        # Header
        self.trash_count = ft.Text(
            "",
            size=14,
            color=colors.text_secondary,
        )

        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DELETE_OUTLINE, size=24, color=colors.primary),
                            ft.Text(
                                "Trash",
                                size=20,
                                weight=ft.FontWeight.W_600,
                                color=colors.text_primary,
                            ),
                            self.trash_count,
                        ],
                        spacing=12,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=colors.text_secondary,
                        on_click=lambda e: self.on_close(),
                        tooltip="Close",
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            margin=ft.margin.only(bottom=16),
        )

        # Search bar and empty trash button
        self.search_field = ft.TextField(
            label="Search",
            hint_text="Search deleted entries...",
            expand=True,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            on_change=self._on_search_change,
        )

        self.empty_trash_button = ft.ElevatedButton(
            text="Empty Trash",
            icon=ft.Icons.DELETE_FOREVER,
            bgcolor=colors.error,
            color=colors.text_inverse,
            on_click=self._on_empty_trash,
        )

        toolbar = ft.Container(
            content=ft.Row(
                controls=[
                    self.search_field,
                    self.empty_trash_button,
                ],
                spacing=12,
            ),
            margin=ft.margin.only(bottom=16),
        )

        # Trash list
        self.trash_list = ft.Column(
            controls=[],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # Layout
        self.content = ft.Column(
            controls=[
                header,
                toolbar,
                ft.Container(
                    content=self.trash_list,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

        self.expand = True
        self.padding = 20

    def did_mount(self):
        """Called when control is added to page - safe to load data."""
        self._mounted = True
        self._refresh_trash()

    def will_unmount(self):
        """Called when control is removed from page."""
        self._mounted = False

    def _on_search_change(self, e):
        """Handle search field change."""
        self.search_query = e.control.value.lower()
        self._refresh_trash()

    def _refresh_trash(self):
        """Refresh the trash list."""
        colors = self.theme.colors

        # Get deleted entries
        all_deleted = self.app_state.entry_manager.get_deleted_entries()

        # Filter by search query
        if self.search_query:
            all_deleted = [
                e for e in all_deleted
                if self.search_query in e.trigger.lower()
                or self.search_query in e.replacement.lower()
            ]

        # Update count
        count = len(all_deleted)
        self.trash_count.value = f"({count} item{'s' if count != 1 else ''})"

        # Update empty trash button visibility
        self.empty_trash_button.disabled = count == 0

        # Build list
        self.trash_list.controls.clear()

        if not all_deleted:
            # Empty state
            self.trash_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.DELETE_OUTLINE,
                                size=64,
                                color=colors.text_tertiary,
                            ),
                            ft.Text(
                                "Trash is empty",
                                size=16,
                                color=colors.text_secondary,
                            ),
                            ft.Text(
                                "Deleted entries will appear here",
                                size=12,
                                color=colors.text_tertiary,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                )
            )
        else:
            for entry in all_deleted:
                self.trash_list.controls.append(
                    self._build_trash_item(entry)
                )

        # Only update if mounted
        if self._mounted:
            self.update()

    def _build_trash_item(self, entry: Entry) -> ft.Container:
        """Build a single trash item."""
        colors = self.theme.colors

        # Format deleted date
        if entry.deleted_at:
            deleted_str = entry.deleted_at.strftime("%b %d, %Y at %I:%M %p")
        else:
            deleted_str = "Unknown"

        # Truncate replacement preview
        preview = entry.replacement
        if len(preview) > 80:
            preview = preview[:80] + "..."

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header with trigger and deleted date
                    ft.Row(
                        controls=[
                            ft.Text(
                                entry.full_trigger,
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color=colors.text_primary,
                            ),
                            ft.Text(
                                f"Deleted: {deleted_str}",
                                size=12,
                                color=colors.text_tertiary,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # Replacement preview
                    ft.Container(
                        content=ft.Text(
                            preview,
                            size=13,
                            color=colors.text_secondary,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        margin=ft.margin.only(top=4, bottom=12),
                    ),
                    # Tags (if any)
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    tag,
                                    size=11,
                                    color=colors.tag_text,
                                ),
                                bgcolor=colors.tag_bg,
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            )
                            for tag in entry.tags
                        ],
                        spacing=4,
                        wrap=True,
                    ) if entry.tags else ft.Container(),
                    # Action buttons
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                text="Restore",
                                icon=ft.Icons.RESTORE,
                                bgcolor=colors.success,
                                color=colors.text_inverse,
                                on_click=lambda e, entry_id=entry.id: self._restore_entry(entry_id),
                            ),
                            ft.ElevatedButton(
                                text="Delete Forever",
                                icon=ft.Icons.DELETE_FOREVER,
                                bgcolor=colors.error,
                                color=colors.text_inverse,
                                on_click=lambda e, entry_id=entry.id, trigger=entry.full_trigger: self._confirm_permanent_delete(entry_id, trigger),
                            ),
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=0,
            ),
            padding=20,
            border_radius=12,
            bgcolor=colors.bg_surface,
            border=ft.border.all(1, colors.border_muted),
        )

    def _restore_entry(self, entry_id: str):
        """Restore a deleted entry."""
        entry = self.app_state.entry_manager.get_entry(entry_id)
        if not entry:
            self._show_snackbar("Entry not found", error=True)
            return

        success = self.app_state.entry_manager.restore_entry(entry_id)

        if success:
            self._show_snackbar(f"Restored {entry.full_trigger}")
            self._refresh_trash()
        else:
            self._show_snackbar("Failed to restore entry", error=True)

    def _confirm_permanent_delete(self, entry_id: str, trigger: str):
        """Show confirmation dialog before permanent deletion."""
        colors = self.theme.colors

        def delete_confirmed(e):
            dialog.open = False
            self.page.update()
            self._permanent_delete_entry(entry_id, trigger)

        def cancel_delete(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER, color=colors.error),
                    ft.Text("Confirm Permanent Deletion", color=colors.text_primary),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"Are you sure you want to permanently delete this entry?",
                            size=14,
                            color=colors.text_primary,
                        ),
                        ft.Container(
                            content=ft.Text(
                                trigger,
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=colors.error,
                            ),
                            bgcolor=colors.bg_elevated,
                            padding=12,
                            border_radius=8,
                            margin=ft.margin.only(top=8),
                        ),
                        ft.Text(
                            "This action cannot be undone.",
                            size=12,
                            color=colors.warning,
                            weight=ft.FontWeight.W_500,
                            italic=True,
                        ),
                    ],
                    spacing=8,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=cancel_delete,
                ),
                ft.ElevatedButton(
                    "Delete Forever",
                    icon=ft.Icons.DELETE_FOREVER,
                    bgcolor=colors.error,
                    color=colors.text_inverse,
                    on_click=delete_confirmed,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors.bg_surface,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _permanent_delete_entry(self, entry_id: str, trigger: str):
        """Permanently delete an entry."""
        success = self.app_state.entry_manager.permanent_delete(entry_id)

        if success:
            self._show_snackbar(f"Permanently deleted {trigger}")
            self._refresh_trash()
        else:
            self._show_snackbar("Failed to delete entry", error=True)

    def _on_empty_trash(self, e):
        """Show confirmation dialog before emptying trash."""
        colors = self.theme.colors

        deleted_entries = self.app_state.entry_manager.get_deleted_entries()
        count = len(deleted_entries)

        if count == 0:
            return

        def empty_confirmed(e):
            dialog.open = False
            self.page.update()
            self._empty_trash()

        def cancel_empty(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER, color=colors.error),
                    ft.Text("Confirm Empty Trash", color=colors.text_primary),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"Are you sure you want to permanently delete all {count} items in the trash?",
                            size=14,
                            color=colors.text_primary,
                        ),
                        ft.Text(
                            "This action cannot be undone.",
                            size=12,
                            color=colors.warning,
                            weight=ft.FontWeight.W_500,
                            italic=True,
                        ),
                    ],
                    spacing=8,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=cancel_empty,
                ),
                ft.ElevatedButton(
                    "Empty Trash",
                    icon=ft.Icons.DELETE_FOREVER,
                    bgcolor=colors.error,
                    color=colors.text_inverse,
                    on_click=empty_confirmed,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors.bg_surface,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _empty_trash(self):
        """Empty the trash (permanently delete all deleted entries)."""
        deleted_entries = self.app_state.entry_manager.get_deleted_entries()
        count = 0

        for entry in deleted_entries:
            if self.app_state.entry_manager.permanent_delete(entry.id):
                count += 1

        self._show_snackbar(f"Permanently deleted {count} item{'s' if count != 1 else ''}")
        self._refresh_trash()

    def _show_snackbar(self, message: str, error: bool = False):
        """Show a snackbar notification."""
        colors = self.theme.colors
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=colors.text_primary),
            bgcolor=colors.error if error else colors.success,
            duration=2000,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def refresh(self):
        """Refresh the trash view."""
        self._refresh_trash()
