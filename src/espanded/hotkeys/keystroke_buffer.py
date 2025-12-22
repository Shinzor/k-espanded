"""Keystroke buffer for tracking typed characters and detecting triggers."""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class TriggerMatch:
    """Represents a detected trigger match."""

    trigger: str  # The trigger character(s) that were typed
    filter_text: str  # Text typed after the trigger
    total_chars: int  # Total characters to delete (trigger + filter)

    @property
    def search_text(self) -> str:
        """Get the full text to search for (trigger + filter)."""
        return f"{self.trigger}{self.filter_text}"


class KeystrokeBuffer:
    """Tracks typed characters and detects trigger patterns.

    This buffer monitors keystrokes to detect when a user types a trigger
    character (like ':') followed by filter text. It handles:
    - Character accumulation
    - Backspace/delete handling
    - Word boundary detection (space, enter clears buffer)
    - Timeout-based clearing
    """

    def __init__(
        self,
        triggers: list[str] | None = None,
        on_trigger_detected: Callable[[TriggerMatch], None] | None = None,
        on_trigger_updated: Callable[[TriggerMatch], None] | None = None,
        on_trigger_cancelled: Callable[[], None] | None = None,
        buffer_timeout: float = 5.0,  # seconds before buffer auto-clears
    ):
        """Initialize the keystroke buffer.

        Args:
            triggers: List of trigger characters/strings (e.g., [':', ';', '//'])
            on_trigger_detected: Called when a trigger is first detected
            on_trigger_updated: Called when filter text changes after trigger
            on_trigger_cancelled: Called when trigger is cancelled (space, escape, etc.)
            buffer_timeout: Seconds of inactivity before buffer clears
        """
        self.triggers = triggers or [":"]
        self.on_trigger_detected = on_trigger_detected
        self.on_trigger_updated = on_trigger_updated
        self.on_trigger_cancelled = on_trigger_cancelled
        self.buffer_timeout = buffer_timeout

        self._buffer: list[str] = []
        self._active_trigger: str | None = None
        self._filter_start_idx: int = 0
        self._last_keystroke_time: float = 0
        self._lock = threading.Lock()

        # Timer for timeout-based clearing
        self._timeout_timer: threading.Timer | None = None

    @property
    def is_active(self) -> bool:
        """Check if a trigger is currently active."""
        return self._active_trigger is not None

    @property
    def current_match(self) -> TriggerMatch | None:
        """Get the current trigger match, if active."""
        if not self._active_trigger:
            return None

        with self._lock:
            filter_text = "".join(self._buffer[self._filter_start_idx:])
            return TriggerMatch(
                trigger=self._active_trigger,
                filter_text=filter_text,
                total_chars=len(self._buffer),
            )

    def add_character(self, char: str):
        """Add a typed character to the buffer.

        Args:
            char: The character that was typed
        """
        with self._lock:
            self._last_keystroke_time = time.time()
            self._reset_timeout_timer()

            # Add to buffer
            self._buffer.append(char)
            buffer_str = "".join(self._buffer)

            # Check if we just completed a trigger
            if not self._active_trigger:
                for trigger in sorted(self.triggers, key=len, reverse=True):
                    if buffer_str.endswith(trigger):
                        self._active_trigger = trigger
                        self._filter_start_idx = len(self._buffer)
                        logger.debug(f"Trigger detected: {trigger}")

                        if self.on_trigger_detected:
                            match = TriggerMatch(
                                trigger=trigger,
                                filter_text="",
                                total_chars=len(self._buffer),
                            )
                            self._schedule_callback(self.on_trigger_detected, match)
                        return
            else:
                # Trigger is active, update filter text
                if self.on_trigger_updated:
                    match = self.current_match
                    if match:
                        self._schedule_callback(self.on_trigger_updated, match)

    def handle_backspace(self):
        """Handle backspace key - remove last character."""
        with self._lock:
            if not self._buffer:
                return

            self._buffer.pop()
            self._last_keystroke_time = time.time()
            self._reset_timeout_timer()

            # Check if we deleted back past the trigger
            if self._active_trigger:
                if len(self._buffer) < len(self._active_trigger):
                    # Deleted the trigger itself
                    self._cancel_trigger()
                elif len(self._buffer) < self._filter_start_idx:
                    # Shouldn't happen, but handle it
                    self._filter_start_idx = len(self._buffer)
                else:
                    # Still have filter text, update
                    if self.on_trigger_updated:
                        match = self.current_match
                        if match:
                            self._schedule_callback(self.on_trigger_updated, match)

    def handle_cancel(self):
        """Handle cancel keys (Escape, etc.) - cancel any active trigger."""
        with self._lock:
            if self._active_trigger:
                self._cancel_trigger()
            self._clear_buffer()

    def handle_word_boundary(self):
        """Handle word boundary (space, enter, tab) - clear buffer."""
        with self._lock:
            if self._active_trigger:
                self._cancel_trigger()
            self._clear_buffer()

    def handle_selection(self) -> TriggerMatch | None:
        """Handle selection (Enter while trigger active) - return match and clear.

        Returns:
            The current match if a trigger was active, None otherwise
        """
        with self._lock:
            if not self._active_trigger:
                return None

            match = self.current_match
            self._active_trigger = None
            self._filter_start_idx = 0
            self._clear_buffer()
            return match

    def clear(self):
        """Clear the buffer and cancel any active trigger."""
        with self._lock:
            if self._active_trigger:
                self._cancel_trigger()
            self._clear_buffer()

    def update_triggers(self, triggers: list[str]):
        """Update the list of trigger characters.

        Args:
            triggers: New list of triggers
        """
        with self._lock:
            self.triggers = triggers
            # If current trigger is no longer valid, cancel it
            if self._active_trigger and self._active_trigger not in triggers:
                self._cancel_trigger()
                self._clear_buffer()

    def _clear_buffer(self):
        """Clear the internal buffer (must hold lock)."""
        self._buffer.clear()
        self._filter_start_idx = 0
        self._cancel_timeout_timer()

    def _cancel_trigger(self):
        """Cancel the active trigger (must hold lock)."""
        logger.debug(f"Trigger cancelled: {self._active_trigger}")
        self._active_trigger = None
        self._filter_start_idx = 0

        if self.on_trigger_cancelled:
            self._schedule_callback(self.on_trigger_cancelled)

    def _reset_timeout_timer(self):
        """Reset the timeout timer (must hold lock)."""
        self._cancel_timeout_timer()

        def on_timeout():
            with self._lock:
                if time.time() - self._last_keystroke_time >= self.buffer_timeout:
                    logger.debug("Buffer timeout - clearing")
                    if self._active_trigger:
                        self._cancel_trigger()
                    self._clear_buffer()

        self._timeout_timer = threading.Timer(self.buffer_timeout, on_timeout)
        self._timeout_timer.daemon = True
        self._timeout_timer.start()

    def _cancel_timeout_timer(self):
        """Cancel the timeout timer (must hold lock)."""
        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_timer = None

    def _schedule_callback(self, callback: Callable, *args):
        """Schedule a callback to run outside the lock.

        This prevents deadlocks if callbacks try to access the buffer.
        """
        # Run callback in a separate thread to avoid blocking
        def run_callback():
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"Error in keystroke buffer callback: {e}")

        thread = threading.Thread(target=run_callback, daemon=True)
        thread.start()

    def close(self):
        """Clean up resources."""
        with self._lock:
            self._cancel_timeout_timer()
            self._clear_buffer()
            self._active_trigger = None
