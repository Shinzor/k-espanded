"""Autocomplete service - orchestrates inline suggestion functionality.

This service coordinates:
- Keystroke monitoring and trigger detection
- Entry filtering and matching
- Popup display and positioning
- Text insertion after selection
"""

import logging
import threading
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication

from espanded.core.models import Entry
from espanded.hotkeys.keystroke_buffer import KeystrokeBuffer, TriggerMatch
from espanded.hotkeys.cursor_position import get_cursor_position
from espanded.hotkeys.text_inserter import TextInserter

if TYPE_CHECKING:
    from espanded.core.app_state import AppState
    from espanded.ui.theme import ThemeManager

logger = logging.getLogger(__name__)


# Singleton instance
_autocomplete_service: "AutocompleteService | None" = None


def get_autocomplete_service() -> "AutocompleteService | None":
    """Get the autocomplete service singleton."""
    return _autocomplete_service


def init_autocomplete_service(
    app_state: "AppState",
    theme_manager: "ThemeManager",
) -> "AutocompleteService":
    """Initialize the autocomplete service singleton.

    Args:
        app_state: Application state with settings and entry manager
        theme_manager: Theme manager for popup styling

    Returns:
        The initialized AutocompleteService
    """
    global _autocomplete_service
    if _autocomplete_service is not None:
        _autocomplete_service.stop()

    _autocomplete_service = AutocompleteService(app_state, theme_manager)
    return _autocomplete_service


class AutocompleteService(QObject):
    """Service that orchestrates inline autocomplete functionality.

    This service:
    1. Monitors keystrokes via KeystrokeBuffer
    2. Detects trigger characters and filter text
    3. Queries EntryManager for matching entries
    4. Shows/updates the SuggestionPopup
    5. Handles selection and text insertion
    """

    # Signals for thread-safe UI updates
    _show_popup_signal = Signal(list, str, str, int, int)  # entries, filter, trigger, x, y
    _update_popup_signal = Signal(list, str, str)  # entries, filter, trigger
    _hide_popup_signal = Signal()
    _move_selection_signal = Signal(int)  # delta
    _select_current_signal = Signal()

    def __init__(self, app_state: "AppState", theme_manager: "ThemeManager"):
        """Initialize the autocomplete service.

        Args:
            app_state: Application state
            theme_manager: Theme manager for styling
        """
        super().__init__()

        self.app_state = app_state
        self.theme_manager = theme_manager

        self._enabled = False
        self._popup = None
        self._keystroke_buffer = None
        self._text_inserter = None
        self._current_match: TriggerMatch | None = None

        # Delay timer for showing popup
        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.timeout.connect(self._on_show_timer)
        self._pending_show_data = None

        # Connect signals for thread-safe UI updates
        self._show_popup_signal.connect(self._do_show_popup)
        self._update_popup_signal.connect(self._do_update_popup)
        self._hide_popup_signal.connect(self._do_hide_popup)
        self._move_selection_signal.connect(self._do_move_selection)
        self._select_current_signal.connect(self._do_select_current)

    def start(self):
        """Start the autocomplete service."""
        if self._enabled:
            return

        settings = self.app_state.settings
        if not settings.autocomplete_enabled:
            logger.info("Autocomplete is disabled in settings")
            return

        logger.info("Starting autocomplete service")

        # Create the popup (must be done on main thread)
        self._create_popup()

        # Create text inserter
        self._text_inserter = TextInserter()

        # Create keystroke buffer with callbacks
        self._keystroke_buffer = KeystrokeBuffer(
            triggers=settings.autocomplete_triggers,
            on_trigger_detected=self._on_trigger_detected,
            on_trigger_updated=self._on_trigger_updated,
            on_trigger_cancelled=self._on_trigger_cancelled,
        )

        self._enabled = True
        logger.info("Autocomplete service started")

    def stop(self):
        """Stop the autocomplete service."""
        if not self._enabled:
            return

        logger.info("Stopping autocomplete service")

        self._enabled = False

        if self._keystroke_buffer:
            self._keystroke_buffer.close()
            self._keystroke_buffer = None

        if self._popup:
            self._popup.hide()
            self._popup.deleteLater()
            self._popup = None

        self._show_timer.stop()
        self._current_match = None

    def update_settings(self):
        """Update service with new settings."""
        settings = self.app_state.settings

        if not settings.autocomplete_enabled:
            self.stop()
            return

        if not self._enabled:
            self.start()
            return

        # Update triggers
        if self._keystroke_buffer:
            self._keystroke_buffer.update_triggers(settings.autocomplete_triggers)

    def on_key_press(self, key, char: str | None):
        """Handle a key press event from the global listener.

        Args:
            key: The key object from pynput
            char: The character if it's a printable key, None otherwise
        """
        if not self._enabled or not self._keystroke_buffer:
            return

        try:
            from pynput.keyboard import Key

            # Handle special keys
            if key == Key.backspace:
                self._keystroke_buffer.handle_backspace()
            elif key == Key.space:
                self._keystroke_buffer.handle_word_boundary()
            elif key == Key.enter:
                # If popup is visible, select current item
                if self._popup and self._popup.isVisible():
                    self._select_current_signal.emit()
                    return True  # Consume the key
                else:
                    self._keystroke_buffer.handle_word_boundary()
            elif key == Key.esc:
                if self._popup and self._popup.isVisible():
                    self._keystroke_buffer.handle_cancel()
                    return True  # Consume the key
            elif key == Key.tab:
                self._keystroke_buffer.handle_word_boundary()
            elif key == Key.up:
                if self._popup and self._popup.isVisible():
                    self._move_selection_signal.emit(-1)
                    return True  # Consume the key
            elif key == Key.down:
                if self._popup and self._popup.isVisible():
                    self._move_selection_signal.emit(1)
                    return True  # Consume the key
            elif char:
                # Regular character
                self._keystroke_buffer.add_character(char)

        except Exception as e:
            logger.error(f"Error handling key press: {e}")

        return False  # Don't consume the key

    def _create_popup(self):
        """Create the suggestion popup widget."""
        # Import here to avoid circular imports
        from espanded.ui.suggestion_popup import SuggestionPopup

        self._popup = SuggestionPopup(self.theme_manager)
        self._popup.entry_selected.connect(self._on_entry_selected)
        self._popup.dismissed.connect(self._on_popup_dismissed)

    def _on_trigger_detected(self, match: TriggerMatch):
        """Handle trigger detection.

        Args:
            match: The detected trigger match
        """
        logger.debug(f"Trigger detected: {match.trigger}")
        self._current_match = match

        settings = self.app_state.settings

        # Check minimum characters requirement
        if len(match.filter_text) < settings.autocomplete_min_chars:
            return

        # Get cursor position
        cursor_pos = get_cursor_position()

        # Find matching entries
        entries = self._find_matching_entries(match)

        if not entries:
            return

        # Limit entries
        entries = entries[: settings.autocomplete_max_suggestions]

        # Show popup with delay
        self._pending_show_data = (entries, match.filter_text, match.trigger, cursor_pos.x, cursor_pos.y)
        self._show_timer.start(settings.autocomplete_show_delay_ms)

    def _on_trigger_updated(self, match: TriggerMatch):
        """Handle trigger filter text update.

        Args:
            match: The updated trigger match
        """
        logger.debug(f"Trigger updated: {match.trigger}{match.filter_text}")
        self._current_match = match

        settings = self.app_state.settings

        # Check minimum characters requirement
        if len(match.filter_text) < settings.autocomplete_min_chars:
            if self._popup and self._popup.isVisible():
                self._hide_popup_signal.emit()
            return

        # Find matching entries
        entries = self._find_matching_entries(match)

        if not entries:
            self._hide_popup_signal.emit()
            return

        # Limit entries
        entries = entries[: settings.autocomplete_max_suggestions]

        # Update popup
        if self._popup and self._popup.isVisible():
            self._update_popup_signal.emit(entries, match.filter_text, match.trigger)
        else:
            # Popup not visible yet, show it
            cursor_pos = get_cursor_position()
            self._show_popup_signal.emit(
                entries, match.filter_text, match.trigger, cursor_pos.x, cursor_pos.y
            )

    def _on_trigger_cancelled(self):
        """Handle trigger cancellation."""
        logger.debug("Trigger cancelled")
        self._current_match = None
        self._show_timer.stop()
        self._hide_popup_signal.emit()

    def _on_show_timer(self):
        """Handle show timer timeout - actually show the popup."""
        if self._pending_show_data:
            entries, filter_text, trigger, x, y = self._pending_show_data
            self._pending_show_data = None
            self._show_popup_signal.emit(entries, filter_text, trigger, x, y)

    def _find_matching_entries(self, match: TriggerMatch) -> list[Entry]:
        """Find entries matching the trigger and filter.

        Args:
            match: The current trigger match

        Returns:
            List of matching entries
        """
        try:
            # Get all active entries
            all_entries = self.app_state.entry_manager.get_all_entries()

            # Filter by trigger prefix and filter text
            search_text = match.filter_text.lower()
            matching = []

            for entry in all_entries:
                # Check if entry's prefix matches the trigger
                if entry.prefix != match.trigger:
                    continue

                # Check if trigger text matches
                trigger_lower = entry.trigger.lower()

                if search_text:
                    # Filter by typed text
                    if trigger_lower.startswith(search_text):
                        matching.append((0, entry))  # Prefix match - highest priority
                    elif search_text in trigger_lower:
                        matching.append((1, entry))  # Contains match
                    elif search_text in entry.replacement.lower():
                        matching.append((2, entry))  # Replacement match
                else:
                    # No filter text yet, show all with this prefix
                    matching.append((0, entry))

            # Sort by priority, then by trigger name
            matching.sort(key=lambda x: (x[0], x[1].trigger.lower()))

            return [entry for _, entry in matching]

        except Exception as e:
            logger.error(f"Error finding matching entries: {e}")
            return []

    def _on_entry_selected(self, entry: Entry):
        """Handle entry selection from popup.

        Args:
            entry: The selected entry
        """
        logger.info(f"Entry selected: {entry.full_trigger}")

        if self._current_match and self._text_inserter:
            # Calculate how many chars to delete
            chars_to_delete = self._current_match.total_chars

            # Insert the replacement
            self._text_inserter.insert_replacement(
                chars_to_delete=chars_to_delete,
                replacement=entry.replacement,
            )

        # Clear state
        self._current_match = None
        if self._keystroke_buffer:
            self._keystroke_buffer.clear()

    def _on_popup_dismissed(self):
        """Handle popup dismissal."""
        self._current_match = None

    # Thread-safe UI update methods (called via signals)

    def _do_show_popup(self, entries: list, filter_text: str, trigger: str, x: int, y: int):
        """Actually show the popup (on main thread)."""
        if self._popup:
            self._popup.show_suggestions(entries, filter_text, trigger, (x, y))

    def _do_update_popup(self, entries: list, filter_text: str, trigger: str):
        """Actually update the popup (on main thread)."""
        if self._popup:
            self._popup.update_filter(entries, filter_text, trigger)

    def _do_hide_popup(self):
        """Actually hide the popup (on main thread)."""
        if self._popup:
            self._popup.hide()

    def _do_move_selection(self, delta: int):
        """Actually move selection (on main thread)."""
        if self._popup:
            self._popup.move_selection(delta)

    def _do_select_current(self):
        """Actually select current item (on main thread)."""
        if self._popup and self._popup.isVisible():
            entry = self._popup.select_current()
            if entry:
                self._on_entry_selected(entry)
