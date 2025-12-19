"""Qt hotkey recorder widget for capturing keyboard shortcuts."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent

from espanded.ui.theme import ThemeManager

# Import hotkey utilities
try:
    from espanded.hotkeys.listener import (
        DEFAULT_HOTKEY,
        normalize_hotkey,
        display_hotkey,
        test_hotkey,
        PYNPUT_AVAILABLE,
    )
except ImportError:
    DEFAULT_HOTKEY = "<ctrl>+<alt>+`"
    PYNPUT_AVAILABLE = False

    def normalize_hotkey(x):
        return x

    def display_hotkey(x):
        return x.replace("<", "").replace(">", "")

    def test_hotkey(x):
        return (False, "pynput not available")


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


class HotkeyRecorder(QWidget):
    """Widget for recording keyboard shortcuts.

    Features:
    - Click Record to capture key combinations
    - Test button to validate hotkey
    - Reset button to restore default
    - Visual feedback during recording
    - Conflict warnings
    """

    hotkey_changed = Signal(str)

    def __init__(
        self,
        theme_manager: ThemeManager,
        value: str = "",
        label: str = "Hotkey",
        parent=None,
    ):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self._hotkey_value = normalize_hotkey(value) if value else DEFAULT_HOTKEY
        self.label_text = label
        self.is_recording = False

        self._setup_ui()

    def _setup_ui(self):
        """Build the widget UI."""
        colors = self.theme_manager.colors

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Label
        label = QLabel(self.label_text)
        label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 13px;
                font-weight: 500;
                background: transparent;
            }}
        """
        )
        layout.addWidget(label)

        # Container with border
        container = QFrame()
        container.setStyleSheet(
            f"""
            QFrame {{
                background-color: {colors.bg_elevated};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
            }}
        """
        )
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(10)

        # Display row
        display_row = QHBoxLayout()
        display_row.setSpacing(8)

        self.hotkey_display = QLabel(display_hotkey(self._hotkey_value))
        self.hotkey_display.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }}
        """
        )
        display_row.addWidget(self.hotkey_display, stretch=1)

        # Reset button
        reset_btn = QPushButton("⟲")
        reset_btn.setFixedSize(28, 28)
        reset_btn.setToolTip(f"Reset to default ({display_hotkey(DEFAULT_HOTKEY)})")
        reset_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors.bg_surface};
                color: {colors.text_secondary};
                border: 1px solid {colors.border_muted};
                border-radius: 14px;
                font-size: 16px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {colors.entry_hover};
                border-color: {colors.primary};
                color: {colors.primary};
            }}
        """
        )
        reset_btn.clicked.connect(self._on_reset)
        display_row.addWidget(reset_btn)

        container_layout.addLayout(display_row)

        # Status text
        self.status_label = QLabel()
        self.status_label.setVisible(False)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.text_secondary};
                font-size: 11px;
                background: transparent;
            }}
        """
        )
        container_layout.addWidget(self.status_label)

        # Manual input field (hidden by default)
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Type hotkey (e.g., ctrl+alt+p)")
        self.manual_input.setVisible(False)
        self.manual_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {colors.bg_base};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors.primary};
            }}
        """
        )
        self.manual_input.returnPressed.connect(self._on_manual_submit)
        container_layout.addWidget(self.manual_input)

        # Button row
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        # Record button
        self.record_btn = QPushButton("Record")
        self.record_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
        """
        )
        self.record_btn.clicked.connect(self._on_record)
        button_row.addWidget(self.record_btn)

        # Manual button
        manual_btn = QPushButton("Type")
        manual_btn.setProperty("secondary", True)
        manual_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors.bg_surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.entry_hover};
                border-color: {colors.primary};
            }}
        """
        )
        manual_btn.clicked.connect(self._on_manual)
        button_row.addWidget(manual_btn)

        # Test button
        test_btn = QPushButton("Test")
        test_btn.setProperty("secondary", True)
        test_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors.bg_surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.entry_hover};
                border-color: {colors.primary};
            }}
        """
        )
        test_btn.clicked.connect(self._on_test)
        button_row.addWidget(test_btn)

        container_layout.addLayout(button_row)

        layout.addWidget(container)

        # Check for conflicts on init
        self._check_conflicts()

    def get_value(self) -> str:
        """Get the current hotkey value."""
        return self._hotkey_value

    def set_value(self, value: str):
        """Set the hotkey value."""
        self._hotkey_value = normalize_hotkey(value) if value else DEFAULT_HOTKEY
        self.hotkey_display.setText(display_hotkey(self._hotkey_value))
        self._check_conflicts()

    def _on_record(self):
        """Handle record button click."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start recording keyboard input."""
        self.is_recording = True
        colors = self.theme_manager.colors

        # Update UI
        self.hotkey_display.setText("Press key combination...")
        self.record_btn.setText("Cancel")
        self.record_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors.error};
                color: {colors.text_inverse};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.error};
            }}
        """
        )
        self.status_label.setText("Press your key combination... (Esc to cancel)")
        self.status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.warning};
                font-size: 11px;
                background: transparent;
            }}
        """
        )
        self.status_label.setVisible(True)

        # Grab keyboard focus
        self.setFocus()

    def _stop_recording(self):
        """Stop recording keyboard input."""
        self.is_recording = False
        colors = self.theme_manager.colors

        # Restore UI
        self.hotkey_display.setText(display_hotkey(self._hotkey_value))
        self.record_btn.setText("Record")
        self.record_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
        """
        )
        self.status_label.setVisible(False)

    def _on_manual(self):
        """Toggle manual input field."""
        self.manual_input.setVisible(not self.manual_input.isVisible())
        if self.manual_input.isVisible():
            self.manual_input.setText(self._hotkey_value.replace("<", "").replace(">", ""))
            self.manual_input.setFocus()
            self.manual_input.selectAll()

    def _on_manual_submit(self):
        """Handle manual input submission."""
        raw_input = self.manual_input.text().strip().lower()
        if not raw_input:
            return

        # Normalize the input
        normalized = normalize_hotkey(raw_input)

        # Validate - needs at least a modifier + key
        parts = normalized.split("+")
        has_modifier = any(p in ["<ctrl>", "<alt>", "<shift>", "<cmd>"] for p in parts)
        has_key = any(p not in ["<ctrl>", "<alt>", "<shift>", "<cmd>"] for p in parts)

        colors = self.theme_manager.colors

        if has_modifier and has_key:
            self._hotkey_value = normalized
            self.hotkey_display.setText(display_hotkey(self._hotkey_value))
            self.manual_input.setVisible(False)
            self._show_status(f"✓ Set to: {display_hotkey(normalized)}", colors.success)
            self._check_conflicts()
            self.hotkey_changed.emit(self._hotkey_value)
        else:
            self._show_status("Need modifier + key (e.g., ctrl+alt+p)", colors.warning)

    def _on_test(self):
        """Test the current hotkey."""
        colors = self.theme_manager.colors
        success, message = test_hotkey(self._hotkey_value)

        if success:
            self._show_status(f"✓ {message}", colors.success)
        else:
            self._show_status(f"✗ {message}", colors.error)

    def _on_reset(self):
        """Reset to default hotkey."""
        if self.is_recording:
            self._stop_recording()

        self._hotkey_value = DEFAULT_HOTKEY
        self.hotkey_display.setText(display_hotkey(DEFAULT_HOTKEY))
        colors = self.theme_manager.colors
        self._show_status(f"Reset to default: {display_hotkey(DEFAULT_HOTKEY)}", colors.info)
        self._check_conflicts()
        self.hotkey_changed.emit(self._hotkey_value)

    def _check_conflicts(self):
        """Check for conflicts with system shortcuts."""
        if not self._hotkey_value:
            return

        normalized = normalize_hotkey(self._hotkey_value)
        if normalized in SYSTEM_SHORTCUTS:
            conflict = SYSTEM_SHORTCUTS[normalized]
            colors = self.theme_manager.colors
            self._show_status(f"⚠ May conflict with: {conflict}", colors.warning)

    def _show_status(self, message: str, color: str):
        """Show status message."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                background: transparent;
            }}
        """
        )
        self.status_label.setVisible(True)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events during recording."""
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        # Escape cancels recording
        if event.key() == Qt.Key.Key_Escape:
            self._stop_recording()
            return

        # Build hotkey string
        parts = []
        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("<ctrl>")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("<alt>")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("<shift>")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            parts.append("<cmd>")

        # Get key name
        key = self._normalize_key(event.key(), event.text())
        if key:
            parts.append(key)

        # Need at least modifier + key
        if len(parts) >= 2:
            self._hotkey_value = "+".join(parts)
            self._stop_recording()
            self.hotkey_display.setText(display_hotkey(self._hotkey_value))
            colors = self.theme_manager.colors
            self._show_status(f"✓ Recorded: {display_hotkey(self._hotkey_value)}", colors.success)
            self._check_conflicts()
            self.hotkey_changed.emit(self._hotkey_value)

    def _normalize_key(self, key_code: int, key_text: str) -> str:
        """Normalize Qt key to pynput format."""
        # Special keys
        key_map = {
            Qt.Key.Key_Space: "<space>",
            Qt.Key.Key_Return: "<enter>",
            Qt.Key.Key_Enter: "<enter>",
            Qt.Key.Key_Tab: "<tab>",
            Qt.Key.Key_Backspace: "<backspace>",
            Qt.Key.Key_Delete: "<delete>",
            Qt.Key.Key_Escape: "<esc>",
            Qt.Key.Key_F1: "<f1>",
            Qt.Key.Key_F2: "<f2>",
            Qt.Key.Key_F3: "<f3>",
            Qt.Key.Key_F4: "<f4>",
            Qt.Key.Key_F5: "<f5>",
            Qt.Key.Key_F6: "<f6>",
            Qt.Key.Key_F7: "<f7>",
            Qt.Key.Key_F8: "<f8>",
            Qt.Key.Key_F9: "<f9>",
            Qt.Key.Key_F10: "<f10>",
            Qt.Key.Key_F11: "<f11>",
            Qt.Key.Key_F12: "<f12>",
        }

        if key_code in key_map:
            return key_map[key_code]

        # Regular character
        if key_text and len(key_text) == 1 and key_text.isprintable():
            return key_text.lower()

        return ""
