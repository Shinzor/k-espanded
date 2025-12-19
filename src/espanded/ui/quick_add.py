"""Quick Add popup window for rapid entry creation."""

import flet as ft
import subprocess
import sys
import json
import tempfile
import os
from pathlib import Path
from typing import Callable

from espanded.core.app_state import get_app_state
from espanded.ui.theme import ThemeManager, ThemeSettings, DARK_THEME


class QuickAddPopup(ft.Column):
    """Quick add popup for creating entries from selected text.

    This popup appears when the global hotkey is pressed.
    The selected text becomes the replacement, user just adds a trigger.
    """

    def __init__(
        self,
        selected_text: str = "",
        on_save: Callable[[str, str], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ):
        super().__init__()
        self.selected_text = selected_text
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel

        # Get theme from app state or create default
        app_state = get_app_state()
        self.theme = app_state.theme_manager if app_state.theme_manager else ThemeManager()

        # Form fields
        self.trigger_field: ft.TextField | None = None
        self.prefix_dropdown: ft.Dropdown | None = None
        self.replacement_field: ft.TextField | None = None
        self.error_text: ft.Text | None = None
        self._mounted = False

    def did_mount(self):
        """Called when control is added to page."""
        self._mounted = True

    def will_unmount(self):
        """Called when control is removed from page."""
        self._mounted = False

    def build(self):
        colors = self.theme.colors

        # Trigger prefix dropdown
        self.prefix_dropdown = ft.Dropdown(
            value=":",
            options=[
                ft.dropdown.Option("", "None"),
                ft.dropdown.Option(":", ": (colon)"),
                ft.dropdown.Option(";", "; (semicolon)"),
                ft.dropdown.Option("/", "/ (slash)"),
                ft.dropdown.Option("\\", "\\ (backslash)"),
            ],
            width=100,
            height=40,
            text_size=14,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.primary,
        )

        # Trigger input
        self.trigger_field = ft.TextField(
            label="Trigger",
            hint_text="e.g., email, addr, sig",
            autofocus=True,
            width=200,
            height=50,
            text_size=14,
            bgcolor=colors.bg_surface,
            border_color=colors.border_default,
            focused_border_color=colors.primary,
            on_submit=self._on_save,
        )

        # Replacement preview (read-only, shows selected text)
        self.replacement_field = ft.TextField(
            label="Replacement (from selection)",
            value=self.selected_text,
            multiline=True,
            min_lines=2,
            max_lines=5,
            read_only=True,
            width=320,
            text_size=14,
            bgcolor=colors.bg_elevated,
            border_color=colors.border_default,
        )

        # Error text
        self.error_text = ft.Text(
            "",
            color=colors.error,
            size=12,
            visible=False,
        )

        # Build layout
        self.controls = [
            # Header
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.FLASH_ON, color=colors.primary, size=24),
                        ft.Text(
                            "Quick Add Entry",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=colors.text_primary,
                        ),
                    ],
                    spacing=8,
                ),
                margin=ft.margin.only(bottom=16),
            ),

            # Trigger row
            ft.Row(
                [
                    self.prefix_dropdown,
                    self.trigger_field,
                ],
                spacing=8,
            ),

            # Replacement preview
            ft.Container(
                content=self.replacement_field,
                margin=ft.margin.only(top=8),
            ),

            # Error text
            self.error_text,

            # Buttons
            ft.Container(
                content=ft.Row(
                    [
                        ft.TextButton(
                            "Cancel",
                            on_click=self._on_cancel,
                        ),
                        ft.ElevatedButton(
                            "Save",
                            icon=ft.Icons.SAVE,
                            bgcolor=colors.primary,
                            color=colors.text_inverse,
                            on_click=self._on_save,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=8,
                ),
                margin=ft.margin.only(top=16),
            ),
        ]

        self.spacing = 4
        self.width = 360

        return self

    def _on_save(self, e=None):
        """Handle save button click."""
        trigger = self.trigger_field.value.strip() if self.trigger_field else ""
        prefix = self.prefix_dropdown.value if self.prefix_dropdown else ":"

        # Validation
        if not trigger:
            self._show_error("Please enter a trigger")
            return

        if not self.selected_text:
            self._show_error("No text selected")
            return

        # Build full trigger with prefix
        full_trigger = f"{prefix}{trigger}"

        if self.on_save_callback:
            self.on_save_callback(full_trigger, self.selected_text)

    def _on_cancel(self, e=None):
        """Handle cancel button click."""
        if self.on_cancel_callback:
            self.on_cancel_callback()

    def _show_error(self, message: str):
        """Show error message."""
        if self.error_text:
            self.error_text.value = message
            self.error_text.visible = True
            if self._mounted:
                self.update()


def _run_quick_add_subprocess(selected_text: str = ""):
    """Run the quick add window as a subprocess.

    This avoids the 'signal only works in main thread' error
    by running the Flet app in a completely separate process.
    """
    # Get the path to the quick_add_standalone script
    script_dir = Path(__file__).parent.parent
    standalone_script = script_dir / "quick_add_standalone.py"

    # Write selected text to a temp file to pass to subprocess
    # (avoids issues with special characters in command line args)
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(selected_text)
            temp_file = f.name

        # Get the Python executable from the current environment
        python_exe = sys.executable

        # Run the subprocess
        subprocess.Popen(
            [python_exe, str(standalone_script), temp_file],
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        )
    except Exception as e:
        print(f"Error launching quick add subprocess: {e}")
        # Clean up temp file if subprocess failed to launch
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass


def show_quick_add_popup(selected_text: str = ""):
    """Show the quick add popup window.

    This launches the quick add form in a separate process
    to avoid threading issues with Flet.
    """
    _run_quick_add_subprocess(selected_text)
