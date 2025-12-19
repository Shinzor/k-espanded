"""Entry manager - business logic for entry CRUD operations."""

from datetime import datetime
from typing import Callable

from espanded.core.models import Entry, HistoryEntry
from espanded.core.database import Database
from espanded.core.yaml_handler import YAMLHandler
from espanded.core.espanso import EspansoManager


class EntryManager:
    """Manages entry CRUD operations with database and Espanso sync."""

    def __init__(
        self,
        database: Database | None = None,
        espanso: EspansoManager | None = None,
    ):
        """Initialize entry manager.

        Args:
            database: Database instance. If None, creates default.
            espanso: EspansoManager instance. If None, creates default.
        """
        self.db = database or Database()
        self.espanso = espanso or EspansoManager()
        self.yaml_handler = YAMLHandler()

        # Callbacks for UI updates
        self._on_entries_changed: list[Callable[[], None]] = []

    def add_change_listener(self, callback: Callable[[], None]):
        """Add a callback to be called when entries change."""
        self._on_entries_changed.append(callback)

    def remove_change_listener(self, callback: Callable[[], None]):
        """Remove a change listener."""
        if callback in self._on_entries_changed:
            self._on_entries_changed.remove(callback)

    def _notify_change(self):
        """Notify all listeners that entries have changed."""
        for callback in self._on_entries_changed:
            try:
                callback()
            except Exception:
                pass  # Don't let callback errors break the flow

    # CRUD Operations

    def create_entry(self, entry: Entry) -> Entry:
        """Create a new entry.

        Args:
            entry: Entry to create.

        Returns:
            Created entry with generated ID.
        """
        entry.created_at = datetime.now()
        entry.modified_at = datetime.now()

        saved_entry = self.db.save_entry(entry)

        # Log history
        self.db.add_history(HistoryEntry(
            entry_id=saved_entry.id,
            action="created",
            trigger_name=saved_entry.full_trigger,
        ))

        # Sync to Espanso
        self._sync_to_espanso()
        self._notify_change()

        return saved_entry

    def update_entry(self, entry: Entry) -> Entry:
        """Update an existing entry.

        Args:
            entry: Entry with updated values.

        Returns:
            Updated entry.
        """
        # Get old entry for history
        old_entry = self.db.get_entry(entry.id)

        entry.modified_at = datetime.now()
        saved_entry = self.db.save_entry(entry)

        # Log history with changes
        changes = {}
        if old_entry:
            if old_entry.trigger != entry.trigger:
                changes["trigger"] = {"old": old_entry.trigger, "new": entry.trigger}
            if old_entry.replacement != entry.replacement:
                changes["replacement"] = {"old": old_entry.replacement[:50], "new": entry.replacement[:50]}
            if old_entry.tags != entry.tags:
                changes["tags"] = {"old": old_entry.tags, "new": entry.tags}

        self.db.add_history(HistoryEntry(
            entry_id=saved_entry.id,
            action="modified",
            trigger_name=saved_entry.full_trigger,
            changes=changes,
        ))

        # Sync to Espanso
        self._sync_to_espanso()
        self._notify_change()

        return saved_entry

    def save_entry(self, entry: Entry) -> Entry:
        """Save an entry (create or update based on existence).

        Args:
            entry: Entry to save.

        Returns:
            Saved entry.
        """
        existing = self.db.get_entry(entry.id) if entry.id else None
        if existing:
            return self.update_entry(entry)
        return self.create_entry(entry)

    def delete_entry(self, entry_id: str) -> bool:
        """Soft-delete an entry (move to trash).

        Args:
            entry_id: ID of entry to delete.

        Returns:
            True if deleted, False if not found.
        """
        entry = self.db.get_entry(entry_id)
        if not entry:
            return False

        result = self.db.soft_delete_entry(entry_id)

        if result:
            # Log history
            self.db.add_history(HistoryEntry(
                entry_id=entry_id,
                action="deleted",
                trigger_name=entry.full_trigger,
            ))

            # Sync to Espanso
            self._sync_to_espanso()
            self._notify_change()

        return result

    def restore_entry(self, entry_id: str) -> bool:
        """Restore a deleted entry from trash.

        Args:
            entry_id: ID of entry to restore.

        Returns:
            True if restored, False if not found.
        """
        entry = self.db.get_entry(entry_id)
        if not entry:
            return False

        result = self.db.restore_entry(entry_id)

        if result:
            # Log history
            self.db.add_history(HistoryEntry(
                entry_id=entry_id,
                action="restored",
                trigger_name=entry.full_trigger,
            ))

            # Sync to Espanso
            self._sync_to_espanso()
            self._notify_change()

        return result

    def permanent_delete(self, entry_id: str) -> bool:
        """Permanently delete an entry.

        Args:
            entry_id: ID of entry to delete permanently.

        Returns:
            True if deleted, False if not found.
        """
        result = self.db.permanent_delete_entry(entry_id)
        if result:
            self._notify_change()
        return result

    def clone_entry(self, entry_id: str) -> Entry | None:
        """Clone an existing entry.

        Args:
            entry_id: ID of entry to clone.

        Returns:
            New cloned entry, or None if original not found.
        """
        original = self.db.get_entry(entry_id)
        if not original:
            return None

        # Create clone with new ID and modified trigger
        cloned = Entry(
            id="",  # Will be generated
            trigger=f"{original.trigger}_copy",
            prefix=original.prefix,
            replacement=original.replacement,
            tags=original.tags.copy(),
            word=original.word,
            propagate_case=original.propagate_case,
            uppercase_style=original.uppercase_style,
            regex=original.regex,
            case_insensitive=original.case_insensitive,
            force_clipboard=original.force_clipboard,
            passive=original.passive,
            markdown=original.markdown,
            cursor_hint=original.cursor_hint,
            filter_apps=original.filter_apps.copy() if original.filter_apps else None,
            source_file=original.source_file,
        )

        return self.create_entry(cloned)

    # Query Operations

    def get_entry(self, entry_id: str) -> Entry | None:
        """Get an entry by ID."""
        return self.db.get_entry(entry_id)

    def get_all_entries(self) -> list[Entry]:
        """Get all active entries."""
        return self.db.get_all_entries(include_deleted=False)

    def get_deleted_entries(self) -> list[Entry]:
        """Get all deleted entries (trash)."""
        return self.db.get_deleted_entries()

    def search_entries(
        self,
        query: str = "",
        tags: list[str] | None = None,
    ) -> list[Entry]:
        """Search entries by text and/or tags.

        Args:
            query: Search text (searches trigger and replacement).
            tags: List of tags to filter by (any match).

        Returns:
            List of matching entries.
        """
        if query:
            entries = self.db.search_entries(query, tags)
        else:
            entries = self.db.get_all_entries()
            if tags:
                entries = [e for e in entries if any(t in e.tags for t in tags)]

        return entries

    def get_all_tags(self) -> dict[str, int]:
        """Get all unique tags with counts."""
        return self.db.get_all_tags()

    def get_stats(self) -> dict:
        """Get entry statistics."""
        return self.db.get_stats()

    # Espanso Sync

    def _sync_to_espanso(self):
        """Sync all entries to Espanso configuration files."""
        if not self.espanso.exists():
            return

        # Group entries by source file
        entries = self.get_all_entries()
        by_file: dict[str, list[Entry]] = {}

        for entry in entries:
            file_name = entry.source_file or "base.yml"
            if file_name not in by_file:
                by_file[file_name] = []
            by_file[file_name].append(entry)

        # Write each file
        for file_name, file_entries in by_file.items():
            file_path = self.espanso.match_dir / file_name
            self.yaml_handler.write_match_file(file_path, file_entries)

        # Reload Espanso
        self.espanso.reload()

    def import_from_espanso(self) -> int:
        """Import entries from existing Espanso configuration.

        Returns:
            Number of entries imported.
        """
        if not self.espanso.exists():
            return 0

        all_entries = self.yaml_handler.read_all_match_files(self.espanso.config_path)
        count = 0

        for file_name, entries in all_entries.items():
            for entry in entries:
                entry.source_file = file_name
                self.db.save_entry(entry)
                count += 1

        self._notify_change()
        return count

    def export_to_espanso(self):
        """Export all entries to Espanso configuration."""
        self._sync_to_espanso()
