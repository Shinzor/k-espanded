"""Hotkey recorder component for capturing keyboard shortcuts."""

import flet as ft
from typing import Callable

# Default hotkey
DEFAULT_HOTKEY = "<ctrl>+<alt>+`"
PYNPUT_AVAILABLE = False

# Try to import hotkey utilities
try:
    from espanded.hotkeys.listener import (
        DEFAULT_HOTKEY as _DEFAULT_HOTKEY,
        normalize_hotkey as _normalize_hotkey,
        display_hotkey as _display_hotkey,
        test_hotkey as _test_hotkey,
        PYNPUT_AVAILABLE as _PYNPUT_AVAILABLE,
    )
    DEFAULT_HOTKEY = _DEFAULT_HOTKEY
    PYNPUT_AVAILABLE = _PYNPUT_AVAILABLE

    def normalize_hotkey(x):
        return _normalize_hotkey(x)

    def display_hotkey(x):
        return _display_hotkey(x)

    def test_hotkey(x):
        return _test_hotkey(x)
except ImportError:
    # Fallback implementations when pynput is not available
    def normalize_hotkey(hotkey_string: str) -> str:
        """Normalize hotkey string to pynput format."""
        if not hotkey_string:
            return DEFAULT_HOTKEY
        hotkey = hotkey_string.lower().strip()
        parts = hotkey.split("+")
        normalized = []
        modifiers = {"ctrl": "<ctrl>", "control": "<ctrl>", "alt": "<alt>",
                     "shift": "<shift>", "meta": "<cmd>", "cmd": "<cmd>", "win": "<cmd>"}
        for part in parts:
            part = part.strip()
            if part in modifiers:
                normalized.append(modifiers[part])
            elif part.startswith("<") and part.endswith(">"):
                normalized.append(part)
            elif len(part) == 1:
                normalized.append(part)
            else:
                normalized.append(part)
        return "+".join(normalized)

    def display_hotkey(hotkey_string: str) -> str:
        """Convert pynput hotkey format to display format."""
        if not hotkey_string:
            return "Not set"
        display = hotkey_string.replace("<", "").replace(">", "")
        parts = display.split("+")
        formatted = [p.capitalize() if len(p) > 1 else p for p in parts if p]
        return " + ".join(formatted)

    def test_hotkey(hotkey_string: str) -> tuple:
        """Test if a hotkey is valid."""
        return (False, "pynput not installed - hotkeys will work after restart")


# Common system shortcuts that might conflict
SYSTEM_SHORTCUTS = {
    "<ctrl>+c": "Copy",
    "<ctrl>+v": "Paste",
    "<ctrl>+x": "Cut",
    "<ctrl>+z": "Undo",
    "<ctrl>+y": "Redo",
    "<ctrl>+a": "Select All",
    "<ctrl>+s": "Save",
    "<ctrl>+p": "Print",
    "<ctrl>+f": "Find",
    "<ctrl>+n": "New",
    "<ctrl>+o": "Open",
    "<ctrl>+w": "Close Tab",
    "<ctrl>+t": "New Tab",
    "<alt>+<tab>": "Switch Window",
    "<alt>+<f4>": "Close Window",
}

# Keys that are only modifiers (not valid as primary keys)
MODIFIER_ONLY_KEYS = {
    "Control Left", "Control Right", "Shift Left", "Shift Right",
    "Alt Left", "Alt Right", "Meta Left", "Meta Right",
    "Control", "Shift", "Alt", "Meta",
}


class HotkeyRecorder(ft.Container):
    """A component for recording keyboard shortcuts.

    Features:
    - Click Record to capture key combinations
    - Test button to validate hotkey
    - Reset button to restore default
    - Visual feedback during recording
    - Conflict warnings
    """

    def __init__(
        self,
        value: str = "",
        label: str = "Hotkey",
        width: int = 300,
        on_change: Callable[[str], None] | None = None,
        colors=None,
    ):
        super().__init__()
        # Normalize and store value
        self._hotkey_value = normalize_hotkey(value) if value else DEFAULT_HOTKEY
        self.label_text = label
        self.width_value = width
        self.on_change_callback = on_change
        self.colors = colors
        self.is_recording = False
        self._mounted = False
        self._original_keyboard_handler = None

        self._build()

    def did_mount(self):
        """Called when control is added to page."""
        self._mounted = True

    def will_unmount(self):
        """Called when control is removed from page."""
        self._mounted = False
        if self.is_recording:
            self._stop_recording()

    @property
    def value(self) -> str:
        """Get the current hotkey value in pynput format."""
        return self._hotkey_value

    @value.setter
    def value(self, new_value: str):
        """Set the hotkey value."""
        self._hotkey_value = normalize_hotkey(new_value) if new_value else DEFAULT_HOTKEY
        self._update_display()
        if self._mounted:
            self.update()

    def _build(self):
        """Build the component layout."""
        # Display showing current hotkey
        self.hotkey_display = ft.Text(
            display_hotkey(self._hotkey_value),
            size=16,
            weight=ft.FontWeight.W_600,
        )

        # Status text (recording, test results)
        self.status_text = ft.Text(
            "",
            size=12,
            visible=False,
        )

        # Record button
        self.record_btn = ft.ElevatedButton(
            text="Record",
            icon=ft.Icons.FIBER_MANUAL_RECORD,
            on_click=self._on_record_click,
            height=36,
            style=ft.ButtonStyle(
                bgcolor={"": ft.Colors.BLUE_700},
                color={"": ft.Colors.WHITE},
            ),
        )

        # Test button
        self.test_btn = ft.OutlinedButton(
            text="Test",
            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
            on_click=self._on_test_click,
            height=36,
        )

        # Reset to default button
        self.reset_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=f"Reset to default ({display_hotkey(DEFAULT_HOTKEY)})",
            on_click=self._reset_to_default,
            icon_size=20,
        )

        # Main layout
        self.content = ft.Column(
            controls=[
                ft.Text(self.label_text, size=13, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    self.hotkey_display,
                                    self.reset_btn,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            self.status_text,
                            ft.Row(
                                controls=[
                                    self.record_btn,
                                    self.test_btn,
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=14,
                    border_radius=8,
                    border=ft.border.all(1, "#cccccc"),
                ),
            ],
            spacing=6,
        )
        self.width = self.width_value

    def _update_display(self):
        """Update the display text."""
        self.hotkey_display.value = display_hotkey(self._hotkey_value)
        self._check_conflicts()

    def _on_record_click(self, e=None):
        """Handle record button click."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start recording keyboard input."""
        if not self.page:
            return

        self.is_recording = True
        self.status_text.value = "⏺ Press your key combination... (Esc to cancel)"
        self.status_text.color = ft.Colors.RED_700
        self.status_text.visible = True
        self.record_btn.text = "Cancel"
        self.record_btn.icon = ft.Icons.CANCEL
        self.record_btn.style = ft.ButtonStyle(
            bgcolor={"": ft.Colors.ORANGE_700},
            color={"": ft.Colors.WHITE},
        )
        self.hotkey_display.value = "..."

        # Store original handler
        self._original_keyboard_handler = self.page.on_keyboard_event

        def on_keyboard(e: ft.KeyboardEvent):
            if not self.is_recording:
                return

            # Debug: print the key event
            print(f"[HotkeyRecorder] Key event: key={e.key}, ctrl={e.ctrl}, alt={e.alt}, shift={e.shift}")

            # Escape cancels recording
            if e.key == "Escape":
                self._stop_recording()
                self._update_display()
                self.status_text.value = "Recording cancelled"
                self.status_text.color = ft.Colors.GREY_700
                if self._mounted:
                    self.update()
                return

            # Skip if only modifier keys pressed
            if e.key in MODIFIER_ONLY_KEYS:
                return

            # Build hotkey string in pynput format
            parts = []
            if e.ctrl:
                parts.append("<ctrl>")
            if e.alt:
                parts.append("<alt>")
            if e.shift:
                parts.append("<shift>")
            if e.meta:
                parts.append("<cmd>")

            # Add the main key
            key = self._normalize_key(e.key)
            if key:
                parts.append(key)

            # Need at least one modifier + one key
            if len(parts) >= 2:
                self._hotkey_value = "+".join(parts)
                self._stop_recording()
                self._update_display()

                # Show success message
                self.status_text.value = f"✓ Recorded: {display_hotkey(self._hotkey_value)}"
                self.status_text.color = ft.Colors.GREEN_700
                self.status_text.visible = True

                if self.on_change_callback:
                    self.on_change_callback(self._hotkey_value)

                if self._mounted:
                    self.update()
            else:
                # Show hint if only one key pressed
                self.status_text.value = "Need modifier + key (e.g., Ctrl+Alt+P)"
                self.status_text.color = ft.Colors.ORANGE_700
                if self._mounted:
                    self.update()

        self.page.on_keyboard_event = on_keyboard

        if self._mounted:
            self.update()

    def _stop_recording(self):
        """Stop recording keyboard input."""
        self.is_recording = False
        self.record_btn.text = "Record"
        self.record_btn.icon = ft.Icons.FIBER_MANUAL_RECORD
        self.record_btn.style = ft.ButtonStyle(
            bgcolor={"": ft.Colors.BLUE_700},
            color={"": ft.Colors.WHITE},
        )

        # Restore original handler
        if self.page and self._original_keyboard_handler is not None:
            self.page.on_keyboard_event = self._original_keyboard_handler
        elif self.page:
            self.page.on_keyboard_event = None
        self._original_keyboard_handler = None

        if self._mounted:
            self.update()

    def _normalize_key(self, key: str) -> str:
        """Normalize key name to pynput format."""
        # Map Flet key names to pynput format
        key_map = {
            " ": "<space>",
            "Escape": "<esc>",
            "Enter": "<enter>",
            "Tab": "<tab>",
            "Backspace": "<backspace>",
            "Delete": "<delete>",
            "Insert": "<insert>",
            "Home": "<home>",
            "End": "<end>",
            "Page Up": "<page_up>",
            "Page Down": "<page_down>",
            "Arrow Up": "<up>",
            "Arrow Down": "<down>",
            "Arrow Left": "<left>",
            "Arrow Right": "<right>",
            "F1": "<f1>", "F2": "<f2>", "F3": "<f3>", "F4": "<f4>",
            "F5": "<f5>", "F6": "<f6>", "F7": "<f7>", "F8": "<f8>",
            "F9": "<f9>", "F10": "<f10>", "F11": "<f11>", "F12": "<f12>",
        }

        if key in key_map:
            return key_map[key]

        # Single character key - lowercase
        if len(key) == 1:
            return key.lower()

        # Other keys - lowercase, no spaces
        return key.lower().replace(" ", "")

    def _reset_to_default(self, e=None):
        """Reset to the default hotkey."""
        if self.is_recording:
            self._stop_recording()

        self._hotkey_value = DEFAULT_HOTKEY
        self._update_display()

        self.status_text.value = f"Reset to default: {display_hotkey(DEFAULT_HOTKEY)}"
        self.status_text.color = ft.Colors.BLUE_700
        self.status_text.visible = True

        if self.on_change_callback:
            self.on_change_callback(self._hotkey_value)

        if self._mounted:
            self.update()

    def _on_test_click(self, e=None):
        """Test if the current hotkey is valid."""
        success, message = test_hotkey(self._hotkey_value)

        if success:
            self.status_text.value = f"✓ {message}"
            self.status_text.color = ft.Colors.GREEN_700
        else:
            self.status_text.value = f"✗ {message}"
            self.status_text.color = ft.Colors.RED_700

        self.status_text.visible = True

        if self._mounted:
            self.update()

    def _check_conflicts(self):
        """Check for conflicts with system shortcuts."""
        if not self._hotkey_value:
            return

        # Check against known system shortcuts
        normalized = normalize_hotkey(self._hotkey_value)
        if normalized in SYSTEM_SHORTCUTS:
            conflict = SYSTEM_SHORTCUTS[normalized]
            self.status_text.value = f"⚠ May conflict with: {conflict}"
            self.status_text.color = ft.Colors.ORANGE_700
            self.status_text.visible = True
        # Don't hide - let other operations control visibility
