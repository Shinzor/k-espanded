#!/usr/bin/env python3
"""Standalone Quick Add window for Espanded.

This script is launched as a separate process to avoid threading issues with Flet.
It receives the selected text via a temporary file path as command line argument.
"""

import sys
import os
import flet as ft
from pathlib import Path

# Add the parent directory to sys.path for imports
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def create_quick_add_app(selected_text: str = ""):
    """Create the quick add Flet application."""

    def main(page: ft.Page):
        page.title = "Espanded - Quick Add"
        page.window.width = 420
        page.window.height = 320
        page.window.resizable = False
        page.window.center()
        page.window.always_on_top = True
        page.padding = 20
        page.bgcolor = "#1e1e2e"  # Dark theme

        # Colors
        primary = "#7c3aed"
        bg_surface = "#2d2d3d"
        bg_elevated = "#3d3d4d"
        text_primary = "#ffffff"
        text_secondary = "#a0a0b0"
        border_default = "#4d4d5d"
        error_color = "#ef4444"

        # Form state
        error_text = ft.Text("", color=error_color, size=12, visible=False)

        # Prefix dropdown
        prefix_dropdown = ft.Dropdown(
            value=":",
            options=[
                ft.dropdown.Option("", "None"),
                ft.dropdown.Option(":", ": (colon)"),
                ft.dropdown.Option(";", "; (semicolon)"),
                ft.dropdown.Option("/", "/ (slash)"),
            ],
            width=100,
            bgcolor=bg_surface,
            border_color=border_default,
            focused_border_color=primary,
            color=text_primary,
        )

        # Trigger input
        trigger_field = ft.TextField(
            label="Trigger",
            hint_text="e.g., email, addr, sig",
            autofocus=True,
            expand=True,
            height=50,
            bgcolor=bg_surface,
            border_color=border_default,
            focused_border_color=primary,
            color=text_primary,
            label_style=ft.TextStyle(color=text_secondary),
        )

        # Replacement preview
        replacement_field = ft.TextField(
            label="Replacement (from selection)",
            value=selected_text if selected_text else "(no text selected)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            read_only=True,
            expand=True,
            bgcolor=bg_elevated,
            border_color=border_default,
            color=text_primary if selected_text else text_secondary,
            label_style=ft.TextStyle(color=text_secondary),
        )

        def on_save(e=None):
            """Save the entry."""
            trigger = trigger_field.value.strip() if trigger_field.value else ""
            prefix = prefix_dropdown.value if prefix_dropdown.value else ""

            if not trigger:
                error_text.value = "Please enter a trigger"
                error_text.visible = True
                page.update()
                return

            if not selected_text:
                error_text.value = "No text was selected"
                error_text.visible = True
                page.update()
                return

            full_trigger = f"{prefix}{trigger}"

            try:
                # Import here to avoid startup overhead
                from espanded.core.app_state import get_app_state
                app_state = get_app_state()
                app_state.entry_manager.create_entry(
                    trigger=full_trigger,
                    replacement=selected_text,
                    tags=["quick-add"],
                )
                page.window.close()
            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_text.visible = True
                page.update()

        def on_cancel(e=None):
            """Close without saving."""
            page.window.close()

        def on_keyboard(e: ft.KeyboardEvent):
            """Handle keyboard events."""
            if e.key == "Escape":
                on_cancel()
            elif e.key == "Enter" and e.ctrl:
                on_save()

        page.on_keyboard_event = on_keyboard

        # Build the UI
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        # Header
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.FLASH_ON, color=primary, size=24),
                                ft.Text(
                                    "Quick Add Entry",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=text_primary,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Container(height=12),
                        # Trigger row
                        ft.Row(
                            [prefix_dropdown, trigger_field],
                            spacing=8,
                        ),
                        ft.Container(height=8),
                        # Replacement
                        replacement_field,
                        # Error
                        error_text,
                        ft.Container(height=8),
                        # Buttons
                        ft.Row(
                            [
                                ft.TextButton("Cancel", on_click=on_cancel),
                                ft.ElevatedButton(
                                    "Save",
                                    icon=ft.Icons.SAVE,
                                    bgcolor=primary,
                                    color="#ffffff",
                                    on_click=on_save,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            spacing=8,
                        ),
                        ft.Text(
                            "Ctrl+Enter to save, Esc to cancel",
                            size=11,
                            color=text_secondary,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=0,
                ),
                bgcolor=bg_surface,
                border_radius=12,
                padding=20,
                border=ft.border.all(1, border_default),
            )
        )

    return main


def main():
    """Main entry point."""
    selected_text = ""

    # Get selected text from temp file (passed as command line argument)
    if len(sys.argv) > 1:
        temp_file_path = sys.argv[1]
        try:
            if os.path.exists(temp_file_path):
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    selected_text = f.read()
                # Clean up temp file
                os.unlink(temp_file_path)
        except Exception as e:
            print(f"Error reading temp file: {e}")

    # Run the Flet app
    # On Windows, use web browser mode due to Flet desktop rendering issues
    if sys.platform == "win32":
        ft.app(
            target=create_quick_add_app(selected_text),
            view=ft.AppView.WEB_BROWSER,
            port=0,  # Auto-select available port
        )
    else:
        ft.app(target=create_quick_add_app(selected_text))


if __name__ == "__main__":
    main()
