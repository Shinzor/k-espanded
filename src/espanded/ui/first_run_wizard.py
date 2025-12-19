"""First run wizard for initial setup."""

import flet as ft
from pathlib import Path
from typing import Callable

from espanded.core.app_state import get_app_state
from espanded.core.espanso import EspansoManager
from espanded.ui.theme import ThemeManager


class FirstRunWizard(ft.Container):
    """First run wizard for setting up Espanded."""

    def __init__(self, theme: ThemeManager, on_complete: Callable[[], None]):
        super().__init__()
        self.theme = theme
        self.on_complete = on_complete
        self.app_state = get_app_state()
        self.espanso = EspansoManager()

        # State
        self.current_step = 0
        self.espanso_path = ""
        self.found_entries = 0
        self.found_files = []
        self.should_import = True
        self.should_setup_sync = True

        # File picker for browse functionality
        self.folder_picker = ft.FilePicker(on_result=self._on_folder_picked)

        self._build()

    def _build(self):
        """Build the wizard layout."""
        colors = self.theme.colors

        # Container for step content
        self.step_content = ft.Container(
            content=ft.Container(),
            expand=True,
        )

        # Navigation buttons
        self.back_button = ft.TextButton(
            text="Back",
            visible=False,
            on_click=self._on_back,
        )

        self.next_button = ft.ElevatedButton(
            text="Continue",
            icon=ft.Icons.ARROW_FORWARD,
            bgcolor=colors.primary,
            color=colors.text_inverse,
            on_click=self._on_next,
        )

        self.skip_button = ft.TextButton(
            text="Skip Setup",
            on_click=self._on_skip,
        )

        # Layout
        self.content = ft.Column(
            controls=[
                self.step_content,
                ft.Divider(height=1, color=colors.border_muted),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self.skip_button,
                            ft.Row(
                                controls=[
                                    self.back_button,
                                    self.next_button,
                                ],
                                spacing=8,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=16,
                ),
            ],
            spacing=0,
            expand=True,
        )

        self.expand = True
        self.bgcolor = self.theme.colors.bg_base

        # Show initial step content (without calling update)
        self._show_step(0, initial=True)

    def did_mount(self):
        """Called when control is added to page - safe to call update()."""
        # Add file picker to page overlay
        if self.page:
            self.page.overlay.append(self.folder_picker)
        self.update()

    def _show_step(self, step: int, initial: bool = False):
        """Show a specific step."""
        self.current_step = step

        if step == 0:
            self._show_welcome_step()
        elif step == 1:
            self._show_espanso_path_step()
        elif step == 2:
            self._show_import_step()
        elif step == 3:
            self._show_sync_step()
        elif step == 4:
            self._show_complete_step()

        # Update button visibility
        self.back_button.visible = step > 0
        self.skip_button.visible = step < 4

        # Only call update if not initial build (control is mounted)
        if not initial:
            self.update()

    def _show_welcome_step(self):
        """Show welcome step."""
        colors = self.theme.colors

        self.step_content.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.CELEBRATION,
                            size=80,
                            color=colors.primary,
                        ),
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=24),
                    ),
                    ft.Text(
                        "Welcome to Espanded!",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=colors.text_primary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Let's get you set up in just a few steps.",
                            size=16,
                            color=colors.text_secondary,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        margin=ft.margin.only(top=8, bottom=32),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._build_feature_item(
                                    ft.Icons.EDIT_NOTE,
                                    "Visual Editor",
                                    "No more manual YAML editing"
                                ),
                                self._build_feature_item(
                                    ft.Icons.FLASH_ON,
                                    "Quick Add",
                                    "Create entries with Ctrl+Shift+E"
                                ),
                                self._build_feature_item(
                                    ft.Icons.SYNC,
                                    "GitHub Sync",
                                    "Sync your snippets across devices"
                                ),
                                self._build_feature_item(
                                    ft.Icons.HISTORY,
                                    "Change History",
                                    "Track all your modifications"
                                ),
                            ],
                            spacing=16,
                        ),
                        margin=ft.margin.only(bottom=24),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=40,
            alignment=ft.alignment.center,
        )

    def _build_feature_item(self, icon, title, description):
        """Build a feature list item."""
        colors = self.theme.colors

        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(icon, size=24, color=colors.primary),
                    width=40,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            title,
                            size=14,
                            weight=ft.FontWeight.W_600,
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
        )

    def _show_espanso_path_step(self):
        """Show Espanso path configuration step."""
        colors = self.theme.colors

        # Try to auto-detect Espanso path
        detected_path = self.espanso.config_path
        self.espanso_path = str(detected_path) if detected_path else ""

        # Count entries if path exists
        if detected_path and detected_path.exists():
            self._scan_espanso_config(detected_path)

        path_field = ft.TextField(
            label="Espanso Config Path",
            value=self.espanso_path,
            expand=True,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.border_focus,
            on_change=self._on_path_change,
        )

        browse_button = ft.ElevatedButton(
            text="Browse",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._on_browse_path,
        )

        status_text = ft.Text(
            "",
            size=12,
            color=colors.text_secondary,
        )

        if self.found_entries > 0:
            status_text.value = f"Found {self.found_entries} entries in {len(self.found_files)} file(s)"
            status_text.color = colors.success
        elif self.espanso_path:
            status_text.value = "No entries found at this path"
            status_text.color = colors.warning

        self.step_content.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OUTLINED, size=64, color=colors.primary),
                    ft.Text(
                        "Espanso Configuration",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=colors.text_primary,
                    ),
                    ft.Text(
                        "Where is your Espanso configuration located?",
                        size=14,
                        color=colors.text_secondary,
                    ),
                    ft.Container(height=24),
                    ft.Row(
                        controls=[path_field, browse_button],
                        spacing=12,
                    ),
                    status_text,
                    ft.Container(height=16),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "Default locations:",
                                    size=12,
                                    weight=ft.FontWeight.W_500,
                                    color=colors.text_secondary,
                                ),
                                ft.Text(
                                    "• Windows: %APPDATA%\\espanso",
                                    size=11,
                                    color=colors.text_tertiary,
                                ),
                                ft.Text(
                                    "• macOS: ~/Library/Application Support/espanso",
                                    size=11,
                                    color=colors.text_tertiary,
                                ),
                                ft.Text(
                                    "• Linux: ~/.config/espanso",
                                    size=11,
                                    color=colors.text_tertiary,
                                ),
                            ],
                            spacing=4,
                        ),
                        bgcolor=colors.bg_surface,
                        padding=12,
                        border_radius=8,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=40,
            alignment=ft.alignment.center,
        )

    def _on_path_change(self, e):
        """Handle path field change."""
        self.espanso_path = e.control.value
        if self.espanso_path:
            self._scan_espanso_config(Path(self.espanso_path))
            self._show_espanso_path_step()  # Refresh to update status

    def _on_browse_path(self, e):
        """Handle browse button click."""
        self.folder_picker.get_directory_path(dialog_title="Select Espanso Config Directory")

    def _on_folder_picked(self, e: ft.FilePickerResultEvent):
        """Handle folder picker result."""
        if e.path:
            self.espanso_path = e.path
            self._scan_espanso_config(Path(e.path))
            self._show_espanso_path_step()  # Refresh to update UI
            self.update()

    def _scan_espanso_config(self, path: Path):
        """Scan Espanso config directory for entries."""
        self.found_entries = 0
        self.found_files = []

        try:
            match_dir = path / "match"
            if match_dir.exists() and match_dir.is_dir():
                # Find all yml and yaml files
                yml_files = list(match_dir.glob("*.yml")) + list(match_dir.glob("*.yaml"))

                for yml_file in yml_files:
                    self.found_files.append(yml_file.name)
                    # Count actual entries by parsing the YAML
                    try:
                        from espanded.core.yaml_handler import YAMLHandler
                        handler = YAMLHandler()
                        entries = handler.read_match_file(yml_file)
                        self.found_entries += len(entries)
                    except Exception:
                        # Fallback: estimate based on file size
                        try:
                            size = yml_file.stat().st_size
                            self.found_entries += max(1, size // 200)  # Rough estimate
                        except Exception:
                            self.found_entries += 1
        except Exception:
            pass

    def _show_import_step(self):
        """Show import confirmation step."""
        colors = self.theme.colors

        # Save the path to settings
        if self.espanso_path:
            self.app_state.settings.espanso_config_path = self.espanso_path
            self.app_state.save_settings()

        import_checkbox = ft.Checkbox(
            label="Import all existing entries",
            value=True,
            on_change=lambda e: setattr(self, 'should_import', e.control.value),
        )

        files_list = ft.Column(
            controls=[
                ft.Text(f"• {file}", size=12, color=colors.text_secondary)
                for file in self.found_files[:10]  # Show max 10 files
            ] + ([
                ft.Text(
                    f"... and {len(self.found_files) - 10} more",
                    size=12,
                    color=colors.text_tertiary,
                    italic=True,
                )
            ] if len(self.found_files) > 10 else []),
            spacing=4,
        ) if self.found_files else ft.Text(
            "No files found",
            size=12,
            color=colors.text_tertiary,
            italic=True,
        )

        self.step_content.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.DOWNLOAD_OUTLINED, size=64, color=colors.primary),
                    ft.Text(
                        "Import Existing Entries",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=colors.text_primary,
                    ),
                    ft.Text(
                        f"We found approximately {self.found_entries} entries",
                        size=14,
                        color=colors.text_secondary,
                    ),
                    ft.Container(height=24),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "Files to import:",
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                    color=colors.text_primary,
                                ),
                                ft.Container(height=8),
                                files_list,
                            ],
                            spacing=4,
                        ),
                        bgcolor=colors.bg_surface,
                        padding=16,
                        border_radius=8,
                        width=500,
                    ),
                    ft.Container(height=16),
                    import_checkbox,
                    ft.Container(height=8),
                    ft.Text(
                        "Note: This will not modify your existing Espanso files",
                        size=11,
                        color=colors.text_tertiary,
                        italic=True,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=40,
            alignment=ft.alignment.center,
        )

    def _show_sync_step(self):
        """Show GitHub sync setup step."""
        colors = self.theme.colors

        sync_checkbox = ft.Checkbox(
            label="Set up GitHub sync (recommended)",
            value=True,
            on_change=lambda e: setattr(self, 'should_setup_sync', e.control.value),
        )

        self.step_content.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.CLOUD_SYNC, size=64, color=colors.primary),
                    ft.Text(
                        "GitHub Sync",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=colors.text_primary,
                    ),
                    ft.Text(
                        "Keep your snippets synchronized across all your devices",
                        size=14,
                        color=colors.text_secondary,
                    ),
                    ft.Container(height=24),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._build_feature_item(
                                    ft.Icons.DEVICES,
                                    "Multi-Device Sync",
                                    "Access your snippets on all your computers"
                                ),
                                self._build_feature_item(
                                    ft.Icons.BACKUP,
                                    "Automatic Backup",
                                    "Never lose your configurations"
                                ),
                                self._build_feature_item(
                                    ft.Icons.HISTORY,
                                    "Version Control",
                                    "Track changes with Git history"
                                ),
                            ],
                            spacing=16,
                        ),
                        width=500,
                    ),
                    ft.Container(height=24),
                    sync_checkbox,
                    ft.Container(height=8),
                    ft.Text(
                        "You can configure this later in Settings",
                        size=11,
                        color=colors.text_tertiary,
                        italic=True,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=40,
            alignment=ft.alignment.center,
        )

    def _show_complete_step(self):
        """Show completion step."""
        colors = self.theme.colors

        # Perform import if requested
        imported_count = 0
        if self.should_import and self.espanso_path:
            try:
                imported_count = self.app_state.entry_manager.import_from_espanso()
            except Exception as e:
                print(f"Import error: {e}")

        # Mark as imported
        self.app_state.settings.has_imported = True
        self.app_state.save_settings()

        # Update next button to finish
        self.next_button.text = "Get Started"
        self.next_button.icon = ft.Icons.CHECK

        status_items = []

        if imported_count > 0:
            status_items.append(
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=colors.success, size=20),
                        ft.Text(
                            f"Imported {imported_count} entries",
                            size=14,
                            color=colors.text_primary,
                        ),
                    ],
                    spacing=8,
                )
            )

        if self.should_setup_sync:
            status_items.append(
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=colors.info, size=20),
                        ft.Text(
                            "GitHub sync can be configured in Settings",
                            size=14,
                            color=colors.text_primary,
                        ),
                    ],
                    spacing=8,
                )
            )

        self.step_content.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=80, color=colors.success),
                    ft.Text(
                        "All Set!",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=colors.text_primary,
                    ),
                    ft.Text(
                        "Espanded is ready to use",
                        size=16,
                        color=colors.text_secondary,
                    ),
                    ft.Container(height=32),
                    ft.Container(
                        content=ft.Column(
                            controls=status_items,
                            spacing=12,
                        ),
                        bgcolor=colors.bg_surface,
                        padding=20,
                        border_radius=8,
                        width=500,
                    ) if status_items else ft.Container(),
                    ft.Container(height=24),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "Quick Start:",
                                    size=14,
                                    weight=ft.FontWeight.W_600,
                                    color=colors.text_primary,
                                ),
                                ft.Container(height=8),
                                ft.Text(
                                    "• Click 'Add Entry' to create your first snippet",
                                    size=12,
                                    color=colors.text_secondary,
                                ),
                                ft.Text(
                                    "• Press Ctrl+Shift+E to quickly add from selected text",
                                    size=12,
                                    color=colors.text_secondary,
                                ),
                                ft.Text(
                                    "• Use tags to organize your entries",
                                    size=12,
                                    color=colors.text_secondary,
                                ),
                            ],
                            spacing=4,
                        ),
                        bgcolor=colors.bg_surface,
                        padding=16,
                        border_radius=8,
                        width=500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=40,
            alignment=ft.alignment.center,
        )

    def _on_next(self, e):
        """Handle next button click."""
        if self.current_step == 4:
            # Finish wizard
            self.on_complete()
        else:
            self._show_step(self.current_step + 1)

    def _on_back(self, e):
        """Handle back button click."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _on_skip(self, e):
        """Handle skip button click."""
        # Mark as imported so wizard doesn't show again
        self.app_state.settings.has_imported = True
        self.app_state.save_settings()
        self.on_complete()

    def _show_snackbar(self, message: str):
        """Show a snackbar notification."""
        colors = self.theme.colors
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=colors.text_primary),
            duration=2000,
        )
        self.page.snack_bar.open = True
        self.page.update()
