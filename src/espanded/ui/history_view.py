"""History view component showing change log."""

import flet as ft
from datetime import datetime, timedelta
from typing import Callable

from espanded.core.app_state import get_app_state
from espanded.core.models import HistoryEntry
from espanded.ui.theme import ThemeManager


class HistoryView(ft.Container):
    """History view showing entry change log with filtering."""

    def __init__(self, theme: ThemeManager, on_close: Callable[[], None]):
        super().__init__()
        self.theme = theme
        self.on_close = on_close
        self.app_state = get_app_state()

        # State
        self.filter_action = "all"  # all, created, modified, deleted, restored
        self.search_query = ""
        self._mounted = False

        self._build()

    def _build(self):
        """Build the history view layout."""
        colors = self.theme.colors

        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.HISTORY, size=24, color=colors.primary),
                            ft.Text(
                                "History",
                                size=20,
                                weight=ft.FontWeight.W_600,
                                color=colors.text_primary,
                            ),
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

        # Filter and search bar
        self.filter_dropdown = ft.Dropdown(
            label="Filter",
            value="all",
            options=[
                ft.dropdown.Option("all", "All changes"),
                ft.dropdown.Option("created", "Created"),
                ft.dropdown.Option("modified", "Modified"),
                ft.dropdown.Option("deleted", "Deleted"),
                ft.dropdown.Option("restored", "Restored"),
            ],
            width=200,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            on_change=self._on_filter_change,
        )

        self.search_field = ft.TextField(
            label="Search",
            hint_text="Search by trigger name...",
            expand=True,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            on_change=self._on_search_change,
        )

        filter_bar = ft.Container(
            content=ft.Row(
                controls=[
                    self.filter_dropdown,
                    self.search_field,
                ],
                spacing=12,
            ),
            margin=ft.margin.only(bottom=16),
        )

        # History list
        self.history_list = ft.Column(
            controls=[],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # Layout
        self.content = ft.Column(
            controls=[
                header,
                filter_bar,
                ft.Container(
                    content=self.history_list,
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
        self._refresh_history()

    def will_unmount(self):
        """Called when control is removed from page."""
        self._mounted = False

    def _on_filter_change(self, e):
        """Handle filter dropdown change."""
        self.filter_action = e.control.value
        self._refresh_history()

    def _on_search_change(self, e):
        """Handle search field change."""
        self.search_query = e.control.value.lower()
        self._refresh_history()

    def _refresh_history(self):
        """Refresh the history list."""
        colors = self.theme.colors

        # Get history entries
        all_history = self.app_state.database.get_history(limit=200)

        # Filter by action type
        if self.filter_action != "all":
            all_history = [h for h in all_history if h.action == self.filter_action]

        # Filter by search query
        if self.search_query:
            all_history = [
                h for h in all_history
                if self.search_query in h.trigger_name.lower()
            ]

        # Group by date
        grouped = self._group_by_date(all_history)

        # Build list
        self.history_list.controls.clear()

        if not grouped:
            # Empty state
            self.history_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.HISTORY_OUTLINED,
                                size=64,
                                color=colors.text_tertiary,
                            ),
                            ft.Text(
                                "No history found",
                                size=16,
                                color=colors.text_secondary,
                            ),
                            ft.Text(
                                "Changes to entries will appear here",
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
            for date_label, entries in grouped:
                # Date header
                self.history_list.controls.append(
                    ft.Container(
                        content=ft.Text(
                            date_label,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=colors.text_primary,
                        ),
                        margin=ft.margin.only(top=16, bottom=8),
                    )
                )

                self.history_list.controls.append(
                    ft.Divider(height=1, color=colors.border_muted)
                )

                # History items
                for history_entry in entries:
                    self.history_list.controls.append(
                        self._build_history_item(history_entry)
                    )

        # Only update if mounted
        if self._mounted:
            self.update()

    def _group_by_date(self, history: list[HistoryEntry]) -> list[tuple[str, list[HistoryEntry]]]:
        """Group history entries by date."""
        now = datetime.now()
        today = now.date()
        yesterday = (now - timedelta(days=1)).date()

        groups: dict[str, list[HistoryEntry]] = {}

        for entry in history:
            entry_date = entry.timestamp.date()

            if entry_date == today:
                label = "Today"
            elif entry_date == yesterday:
                label = "Yesterday"
            else:
                # Format as "Dec 15, 2024"
                label = entry.timestamp.strftime("%b %d, %Y")

            if label not in groups:
                groups[label] = []
            groups[label].append(entry)

        # Return in order: Today, Yesterday, then chronological
        result = []
        if "Today" in groups:
            result.append(("Today", groups["Today"]))
        if "Yesterday" in groups:
            result.append(("Yesterday", groups["Yesterday"]))

        # Add other dates in reverse chronological order
        other_dates = [
            (label, entries)
            for label, entries in groups.items()
            if label not in ["Today", "Yesterday"]
        ]
        other_dates.sort(key=lambda x: x[1][0].timestamp, reverse=True)
        result.extend(other_dates)

        return result

    def _build_history_item(self, history: HistoryEntry) -> ft.Container:
        """Build a single history item."""
        colors = self.theme.colors

        # Get action icon and color
        action_info = self._get_action_info(history.action)
        icon = action_info["icon"]
        icon_color = action_info["color"]
        action_text = action_info["text"]

        # Format timestamp
        time_str = history.timestamp.strftime("%I:%M %p")

        # Build change details
        change_details = []
        if history.changes:
            for key, value in history.changes.items():
                if isinstance(value, dict) and "old" in value and "new" in value:
                    old_val = value["old"]
                    new_val = value["new"]

                    # Truncate long values
                    if isinstance(old_val, str) and len(old_val) > 40:
                        old_val = old_val[:40] + "..."
                    if isinstance(new_val, str) and len(new_val) > 40:
                        new_val = new_val[:40] + "..."

                    change_details.append(
                        ft.Text(
                            f"{key.capitalize()}: {old_val} → {new_val}",
                            size=11,
                            color=colors.text_tertiary,
                            italic=True,
                        )
                    )

        # Build details button if there are changes
        details_controls = []
        if change_details:
            details_controls.append(
                ft.TextButton(
                    text="View Details",
                    icon=ft.Icons.INFO_OUTLINE,
                    style=ft.ButtonStyle(
                        color=colors.text_secondary,
                        padding=ft.padding.all(4),
                    ),
                    on_click=lambda e, h=history: self._show_details(h),
                )
            )

        # Add restore button for deleted entries
        if history.action == "deleted":
            details_controls.append(
                ft.TextButton(
                    text="Restore",
                    icon=ft.Icons.RESTORE,
                    style=ft.ButtonStyle(
                        color=colors.success,
                        padding=ft.padding.all(4),
                    ),
                    on_click=lambda e, h=history: self._restore_entry(h),
                )
            )

        return ft.Container(
            content=ft.Row(
                controls=[
                    # Icon
                    ft.Container(
                        content=ft.Icon(icon, size=18, color=icon_color),
                        width=32,
                    ),
                    # Content
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        f"{time_str} - {action_text} ",
                                        size=13,
                                        color=colors.text_primary,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        history.trigger_name,
                                        size=13,
                                        color=colors.primary,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                ],
                                spacing=4,
                            ),
                            *change_details,
                            ft.Row(
                                controls=details_controls,
                                spacing=8,
                            ) if details_controls else ft.Container(),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.symmetric(vertical=12, horizontal=8),
            border_radius=8,
            bgcolor=colors.bg_surface,
            margin=ft.margin.only(bottom=4),
        )

    def _get_action_info(self, action: str) -> dict:
        """Get icon, color, and text for an action."""
        colors = self.theme.colors

        action_map = {
            "created": {
                "icon": ft.Icons.ADD_CIRCLE_OUTLINE,
                "color": colors.success,
                "text": "Created",
            },
            "modified": {
                "icon": ft.Icons.EDIT_OUTLINED,
                "color": colors.info,
                "text": "Modified",
            },
            "deleted": {
                "icon": ft.Icons.DELETE_OUTLINE,
                "color": colors.error,
                "text": "Deleted",
            },
            "restored": {
                "icon": ft.Icons.RESTORE,
                "color": colors.warning,
                "text": "Restored",
            },
        }

        return action_map.get(action, {
            "icon": ft.Icons.CHANGE_CIRCLE_OUTLINED,
            "color": colors.text_secondary,
            "text": action.capitalize(),
        })

    def _show_details(self, history: HistoryEntry):
        """Show details dialog for a history entry."""
        if not self.page:
            return

        colors = self.theme.colors

        # Build details content
        details = []
        if history.changes:
            for key, value in history.changes.items():
                if isinstance(value, dict) and "old" in value and "new" in value:
                    details.append(
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        key.capitalize(),
                                        size=12,
                                        weight=ft.FontWeight.W_600,
                                        color=colors.text_secondary,
                                    ),
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                ft.Text("Old:", size=11, color=colors.text_tertiary),
                                                ft.Container(
                                                    content=ft.Text(
                                                        str(value["old"]),
                                                        size=12,
                                                        color=colors.text_primary,
                                                    ),
                                                    bgcolor=colors.bg_elevated,
                                                    padding=8,
                                                    border_radius=4,
                                                ),
                                                ft.Text("New:", size=11, color=colors.text_tertiary),
                                                ft.Container(
                                                    content=ft.Text(
                                                        str(value["new"]),
                                                        size=12,
                                                        color=colors.text_primary,
                                                    ),
                                                    bgcolor=colors.bg_elevated,
                                                    padding=8,
                                                    border_radius=4,
                                                ),
                                            ],
                                            spacing=4,
                                        ),
                                        margin=ft.margin.only(top=4),
                                    ),
                                ],
                                spacing=4,
                            ),
                            margin=ft.margin.only(bottom=16),
                        )
                    )

        # Create dialog
        def close_dialog(e):
            dialog.open = False
            self.page.update()

        # Build controls list
        controls_list = [
            ft.Text(
                f"Entry: {history.trigger_name}",
                size=13,
                weight=ft.FontWeight.W_500,
                color=colors.text_primary,
            ),
            ft.Text(
                f"Action: {history.action.capitalize()}",
                size=12,
                color=colors.text_secondary,
            ),
            ft.Text(
                f"Time: {history.timestamp.strftime('%b %d, %Y at %I:%M %p')}",
                size=12,
                color=colors.text_secondary,
            ),
            ft.Divider(height=16, color=colors.border_muted),
        ]

        if details:
            controls_list.extend(details)
        else:
            controls_list.append(
                ft.Text(
                    "No detailed changes recorded",
                    size=12,
                    color=colors.text_tertiary,
                    italic=True,
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=colors.primary),
                    ft.Text("Change Details", color=colors.text_primary),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=controls_list,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
            ],
            bgcolor=colors.bg_surface,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _restore_entry(self, history: HistoryEntry):
        """Restore a deleted entry."""
        success = self.app_state.entry_manager.restore_entry(history.entry_id)

        if success:
            self._show_snackbar(f"Restored {history.trigger_name}")
            self._refresh_history()
        else:
            self._show_snackbar("Failed to restore entry", error=True)

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
        """Refresh the history view."""
        self._refresh_history()
