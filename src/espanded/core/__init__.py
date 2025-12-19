"""Core business logic for Espanded."""

from espanded.core.models import Entry, Settings, HistoryEntry
from espanded.core.database import Database
from espanded.core.yaml_handler import YAMLHandler
from espanded.core.espanso import EspansoManager
from espanded.core.entry_manager import EntryManager
from espanded.core.app_state import AppState, get_app_state

__all__ = [
    "Entry",
    "Settings",
    "HistoryEntry",
    "Database",
    "YAMLHandler",
    "EspansoManager",
    "EntryManager",
    "AppState",
    "get_app_state",
]
