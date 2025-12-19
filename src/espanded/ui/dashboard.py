"""Dashboard component shown when no entry is selected."""

import flet as ft
from datetime import datetime

from espanded.core.app_state import get_app_state
from espanded.ui.theme import ThemeManager


class Dashboard(ft.Container):
    """Dashboard with statistics and quick tips."""

    def __init__(self, theme: ThemeManager):
        super().__init__()
        self.theme = theme
        self.app_state = get_app_state()
        self._mounted = False
        self._build()

    def did_mount(self):
        """Called when control is added to page."""
        self._mounted = True

    def will_unmount(self):
        """Called when control is removed from page."""
        self._mounted = False

    def _build(self):
        """Build the dashboard layout."""
        colors = self.theme.colors

        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DASHBOARD_OUTLINED, size=24, color=colors.primary),
                    ft.Text(
                        "Dashboard",
                        size=20,
                        weight=ft.FontWeight.W_600,
                        color=colors.text_primary,
                    ),
                ],
                spacing=12,
            ),
            margin=ft.margin.only(bottom=24),
        )

        # Statistics card
        self.stats_card = self._build_stats_card()

        # Sync status card
        self.sync_card = self._build_sync_card()

        # Quick tips card
        tips_card = self._build_tips_card()

        # Layout
        self.content = ft.Column(
            controls=[
                header,
                ft.Row(
                    controls=[
                        ft.Container(content=self.stats_card, expand=1),
                        ft.Container(content=self.sync_card, expand=1),
                    ],
                    spacing=16,
                ),
                ft.Container(content=tips_card, margin=ft.margin.only(top=16)),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        self.expand = True

    def _build_stats_card(self) -> ft.Container:
        """Build the statistics card."""
        colors = self.theme.colors

        # Get real stats
        stats_data = self.app_state.entry_manager.get_stats()

        last_modified = stats_data.get("last_modified")
        if last_modified:
            try:
                dt = datetime.fromisoformat(last_modified)
                last_modified_str = dt.strftime("%b %d, %I:%M %p")
            except Exception:
                last_modified_str = "Unknown"
        else:
            last_modified_str = "Never"

        entries_today = stats_data.get("created_today", 0)
        modified_today = stats_data.get("modified_today", 0)
        today_str = f"{entries_today} new" if entries_today else "None"
        if modified_today > entries_today:
            today_str += f", {modified_today - entries_today} modified"

        stats = [
            ("Total Entries", str(stats_data.get("total_entries", 0)), ft.Icons.TEXT_SNIPPET_OUTLINED),
            ("Active Tags", str(stats_data.get("tag_count", 0)), ft.Icons.LABEL_OUTLINED),
            ("Last Modified", last_modified_str, ft.Icons.ACCESS_TIME),
            ("Entries Today", today_str, ft.Icons.TODAY),
        ]

        stat_items = []
        for label, value, icon in stats:
            stat_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(icon, size=18, color=colors.text_tertiary),
                            ft.Column(
                                controls=[
                                    ft.Text(label, size=12, color=colors.text_secondary),
                                    ft.Text(
                                        value,
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                        color=colors.text_primary,
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=12,
                    ),
                    padding=ft.padding.symmetric(vertical=8),
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Statistics",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=colors.text_primary,
                    ),
                    ft.Divider(height=16, color=colors.border_muted),
                    *stat_items,
                ],
                spacing=0,
            ),
            padding=20,
            border_radius=12,
            bgcolor=colors.bg_surface,
            border=ft.border.all(1, colors.border_muted),
        )

    def _build_sync_card(self) -> ft.Container:
        """Build the sync status card."""
        colors = self.theme.colors

        # Get real sync status
        settings = self.app_state.settings
        is_connected = bool(settings.github_repo and settings.github_token)

        last_sync = "Never"
        if settings.last_sync:
            try:
                last_sync = settings.last_sync.strftime("%b %d, %I:%M %p")
            except Exception:
                pass

        repo_name = settings.github_repo or "Not configured"

        status_color = colors.success if is_connected else colors.text_tertiary
        status_text = "Connected" if is_connected else "Not connected"
        status_icon = ft.Icons.CHECK_CIRCLE if is_connected else ft.Icons.CLOUD_OFF

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SYNC, size=18, color=colors.primary),
                            ft.Text(
                                "Sync Status",
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=colors.text_primary,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=16, color=colors.border_muted),
                    ft.Row(
                        controls=[
                            ft.Icon(status_icon, size=16, color=status_color),
                            ft.Text(status_text, size=13, color=status_color),
                        ],
                        spacing=8,
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    f"Repository: {repo_name}",
                                    size=12,
                                    color=colors.text_secondary,
                                ),
                                ft.Text(
                                    f"Last sync: {last_sync}",
                                    size=12,
                                    color=colors.text_secondary,
                                ),
                            ],
                            spacing=4,
                        ),
                        margin=ft.margin.only(top=8),
                    ),
                    ft.Container(
                        content=ft.ElevatedButton(
                            text="Configure Sync" if not is_connected else "Sync Now",
                            icon=ft.Icons.SETTINGS if not is_connected else ft.Icons.SYNC,
                            bgcolor=colors.primary,
                            color=colors.text_inverse,
                            on_click=self._on_sync_click,
                        ),
                        margin=ft.margin.only(top=12),
                    ),
                ],
                spacing=0,
            ),
            padding=20,
            border_radius=12,
            bgcolor=colors.bg_surface,
            border=ft.border.all(1, colors.border_muted),
        )

    def _build_tips_card(self) -> ft.Container:
        """Build the quick tips card."""
        colors = self.theme.colors

        tips = [
            ("Select text + Ctrl+Shift+E", "Quickly create a new entry from selected text"),
            ("Type {{ in replacement", "Insert variables, forms, and scripts"),
            ("Use tags", "Organize and filter your entries efficiently"),
            ("Prefix options", "Use :, ;, //, :: or blank for different trigger styles"),
        ]

        tip_items = []
        for shortcut, description in tips:
            tip_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=16, color=colors.warning),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        shortcut,
                                        size=13,
                                        weight=ft.FontWeight.W_500,
                                        color=colors.text_primary,
                                    ),
                                    ft.Text(
                                        description,
                                        size=12,
                                        color=colors.text_secondary,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    padding=ft.padding.symmetric(vertical=6),
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TIPS_AND_UPDATES, size=18, color=colors.warning),
                            ft.Text(
                                "Quick Tips",
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=colors.text_primary,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=16, color=colors.border_muted),
                    *tip_items,
                ],
                spacing=0,
            ),
            padding=20,
            border_radius=12,
            bgcolor=colors.bg_surface,
            border=ft.border.all(1, colors.border_muted),
        )

    def _on_sync_click(self, e):
        """Handle sync button click."""
        # TODO: Open sync settings or trigger sync
        pass

    def refresh_stats(self):
        """Refresh dashboard statistics."""
        # Rebuild the stats and sync cards
        colors = self.theme.colors

        # Find and replace stats card
        if self.content and self.content.controls:
            row = self.content.controls[1]  # The Row containing stats and sync cards
            if isinstance(row, ft.Row) and len(row.controls) >= 2:
                row.controls[0].content = self._build_stats_card()
                row.controls[1].content = self._build_sync_card()

        # Only update if mounted
        if self._mounted:
            self.update()
