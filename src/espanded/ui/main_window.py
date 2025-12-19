"""Main window layout with sidebar and content pane."""

import flet as ft

from espanded.core.app_state import get_app_state
from espanded.ui.theme import ThemeManager
from espanded.ui.sidebar import Sidebar
from espanded.ui.dashboard import Dashboard
from espanded.ui.entry_editor import EntryEditor
from espanded.ui.history_view import HistoryView
from espanded.ui.trash_view import TrashView
from espanded.ui.settings_view import SettingsView
from espanded.core.models import Entry


class MainWindow(ft.Container):
    """Main application window with two-pane layout."""

    def __init__(self, page: ft.Page, theme_manager: ThemeManager):
        super().__init__()
        self.page = page
        self.theme = theme_manager
        self.app_state = get_app_state()
        self.selected_entry: Entry | None = None

        # Initialize components
        self.sidebar = Sidebar(
            theme=self.theme,
            on_entry_selected=self._on_entry_selected,
            on_add_entry=self._on_add_entry,
        )

        self.dashboard = Dashboard(theme=self.theme)
        self.entry_editor = EntryEditor(
            theme=self.theme,
            on_save=self._on_save_entry,
            on_delete=self._on_delete_entry,
            on_clone=self._on_clone_entry,
            on_close=self._on_close_editor,
        )
        self.history_view = HistoryView(
            theme=self.theme,
            on_close=self._show_dashboard,
        )
        self.trash_view = TrashView(
            theme=self.theme,
            on_close=self._show_dashboard,
        )
        self.settings_view = SettingsView(
            theme=self.theme,
            on_close=self._show_dashboard,
            on_theme_change=self._on_theme_change,
        )

        # Register for entry changes
        self.app_state.entry_manager.add_change_listener(self._on_entries_changed)

        # Build layout
        self._build()

    def _build(self):
        """Build the main window layout."""
        colors = self.theme.colors

        # Right pane container (switches between dashboard and editor)
        self.right_pane = ft.Container(
            content=self.dashboard,
            expand=True,
            bgcolor=colors.bg_base,
            padding=20,
        )

        # Bottom status bar
        self.status_bar = self._build_status_bar()

        # Main layout
        self.content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=self.sidebar,
                                width=320,
                                bgcolor=colors.bg_sidebar,
                                border=ft.border.only(
                                    right=ft.BorderSide(1, colors.border_muted)
                                ),
                            ),
                            self.right_pane,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=True,
                ),
                self.status_bar,
            ],
            spacing=0,
            expand=True,
        )

        self.expand = True

    def _build_status_bar(self) -> ft.Container:
        """Build the bottom status bar."""
        colors = self.theme.colors

        return ft.Container(
            content=ft.Row(
                controls=[
                    # Left side: navigation buttons
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                text="Settings",
                                icon=ft.Icons.SETTINGS_OUTLINED,
                                style=ft.ButtonStyle(
                                    color=colors.text_secondary,
                                ),
                                on_click=self._on_settings_click,
                            ),
                            ft.TextButton(
                                text="History",
                                icon=ft.Icons.HISTORY,
                                style=ft.ButtonStyle(
                                    color=colors.text_secondary,
                                ),
                                on_click=self._on_history_click,
                            ),
                            ft.TextButton(
                                text="Trash",
                                icon=ft.Icons.DELETE_OUTLINE,
                                style=ft.ButtonStyle(
                                    color=colors.text_secondary,
                                ),
                                on_click=self._on_trash_click,
                            ),
                        ],
                        spacing=0,
                    ),
                    # Right side: entry count
                    ft.Text(
                        f"{len(self.app_state.entry_manager.get_all_entries())} entries",
                        color=colors.text_tertiary,
                        size=12,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            bgcolor=colors.bg_surface,
            border=ft.border.only(top=ft.BorderSide(1, colors.border_muted)),
        )

    def _show_dashboard(self):
        """Switch right pane to dashboard."""
        self.selected_entry = None
        self.right_pane.content = self.dashboard
        self.sidebar.clear_selection()
        self.page.update()
        # Refresh stats after dashboard is mounted
        self.dashboard.refresh_stats()

    def _show_editor(self, entry: Entry | None = None):
        """Switch right pane to entry editor."""
        # First add to page tree, then update to mount it
        self.right_pane.content = self.entry_editor
        self.page.update()
        # Now the editor is mounted, safe to call set_entry
        self.entry_editor.set_entry(entry)

    def _on_entry_selected(self, entry: Entry):
        """Handle entry selection from sidebar."""
        self.selected_entry = entry
        self._show_editor(entry)

    def _on_add_entry(self, e=None):
        """Handle add new entry action."""
        self._show_editor(None)  # None means new entry

    def _on_save_entry(self, entry: Entry):
        """Handle entry save."""
        self.app_state.entry_manager.save_entry(entry)
        self._show_snackbar("Entry saved successfully")

    def _on_delete_entry(self, entry: Entry):
        """Handle entry delete."""
        self.app_state.entry_manager.delete_entry(entry.id)
        self._show_dashboard()
        self._show_snackbar("Entry moved to trash")

    def _on_clone_entry(self, entry: Entry):
        """Handle entry clone."""
        cloned = self.app_state.entry_manager.clone_entry(entry.id)
        if cloned:
            self._show_editor(cloned)
            self._show_snackbar("Entry cloned")

    def _on_close_editor(self):
        """Handle editor close."""
        self._show_dashboard()

    def _on_entries_changed(self):
        """Handle entry data changes."""
        self.sidebar.refresh_entries()
        self.dashboard.refresh_stats()

    def _show_snackbar(self, message: str):
        """Show a snackbar notification."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            duration=2000,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _on_settings_click(self, e):
        """Open settings view."""
        self.selected_entry = None
        self.right_pane.content = self.settings_view
        self.sidebar.clear_selection()
        self.page.update()

    def _on_history_click(self, e):
        """Open history view."""
        self.selected_entry = None
        self.history_view.refresh()
        self.right_pane.content = self.history_view
        self.sidebar.clear_selection()
        self.page.update()

    def _on_trash_click(self, e):
        """Open trash view."""
        self.selected_entry = None
        self.trash_view.refresh()
        self.right_pane.content = self.trash_view
        self.sidebar.clear_selection()
        self.page.update()

    def _on_theme_change(self):
        """Handle theme changes from settings."""
        # Reload theme manager with new settings
        from espanded.ui.theme import ThemeSettings
        theme_settings = ThemeSettings(
            theme=self.app_state.settings.theme,
            custom_colors=self.app_state.settings.custom_colors,
        )
        self.app_state.theme_manager.settings = theme_settings
        self.app_state.theme_manager._load_theme()
        self.app_state.theme_manager.apply_to_page(self.page)
        self._show_snackbar("Theme updated - restart may be required for full effect")
