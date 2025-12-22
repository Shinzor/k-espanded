"""Tests for entry manager."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from espanded.core.models import Entry, HistoryEntry
from espanded.core.entry_manager import EntryManager


class TestEntryManager:
    """Tests for EntryManager class."""

    def test_create_entry(self, entry_manager, sample_entry):
        """Test creating a new entry."""
        created = entry_manager.create_entry(sample_entry)

        assert created.id == sample_entry.id
        assert created.trigger == "test"
        assert created.replacement == "Test replacement text"

        # Verify it was saved to database
        retrieved = entry_manager.get_entry(sample_entry.id)
        assert retrieved is not None
        assert retrieved.trigger == "test"

    def test_update_entry(self, entry_manager, sample_entry):
        """Test updating an existing entry."""
        # Create entry first
        created = entry_manager.create_entry(sample_entry)

        # Update it
        created.replacement = "Updated replacement"
        updated = entry_manager.update_entry(created)

        assert updated.replacement == "Updated replacement"
        assert updated.modified_at > created.created_at

    def test_save_entry_creates_new(self, entry_manager):
        """Test save_entry creates new entry when it doesn't exist."""
        entry = Entry(
            trigger="new_test",
            prefix=":",
            replacement="New content"
        )
        saved = entry_manager.save_entry(entry)

        assert saved.id != ""
        assert saved.trigger == "new_test"

    def test_save_entry_updates_existing(self, entry_manager, sample_entry):
        """Test save_entry updates existing entry."""
        created = entry_manager.create_entry(sample_entry)
        created.replacement = "Modified"

        saved = entry_manager.save_entry(created)

        assert saved.id == created.id
        assert saved.replacement == "Modified"

    def test_delete_entry(self, entry_manager, sample_entry):
        """Test soft-deleting an entry."""
        created = entry_manager.create_entry(sample_entry)

        result = entry_manager.delete_entry(created.id)
        assert result is True

        # Entry should be marked as deleted
        deleted = entry_manager.get_entry(created.id)
        assert deleted.is_deleted is True

        # Should not appear in active entries
        active_entries = entry_manager.get_all_entries()
        assert created.id not in [e.id for e in active_entries]

    def test_delete_nonexistent_entry(self, entry_manager):
        """Test deleting an entry that doesn't exist."""
        result = entry_manager.delete_entry("nonexistent-id")
        assert result is False

    def test_restore_entry(self, entry_manager, sample_entry):
        """Test restoring a deleted entry."""
        created = entry_manager.create_entry(sample_entry)
        entry_manager.delete_entry(created.id)

        result = entry_manager.restore_entry(created.id)
        assert result is True

        # Entry should no longer be deleted
        restored = entry_manager.get_entry(created.id)
        assert restored.is_deleted is False

        # Should appear in active entries
        active_entries = entry_manager.get_all_entries()
        assert created.id in [e.id for e in active_entries]

    def test_permanent_delete(self, entry_manager, sample_entry):
        """Test permanently deleting an entry."""
        created = entry_manager.create_entry(sample_entry)

        result = entry_manager.permanent_delete(created.id)
        assert result is True

        # Entry should be completely gone
        deleted = entry_manager.get_entry(created.id)
        assert deleted is None

    def test_clone_entry(self, entry_manager, sample_entry):
        """Test cloning an entry."""
        created = entry_manager.create_entry(sample_entry)

        cloned = entry_manager.clone_entry(created.id)

        assert cloned is not None
        assert cloned.id != created.id
        assert cloned.trigger == "test_copy"
        assert cloned.replacement == created.replacement
        assert cloned.tags == created.tags

    def test_clone_nonexistent_entry(self, entry_manager):
        """Test cloning an entry that doesn't exist."""
        cloned = entry_manager.clone_entry("nonexistent-id")
        assert cloned is None

    def test_get_all_entries(self, entry_manager, sample_entries):
        """Test getting all active entries."""
        for entry in sample_entries:
            entry_manager.create_entry(entry)

        all_entries = entry_manager.get_all_entries()
        assert len(all_entries) == len(sample_entries)

    def test_get_deleted_entries(self, entry_manager, sample_entries):
        """Test getting deleted entries."""
        # Create and delete some entries
        for entry in sample_entries[:2]:
            created = entry_manager.create_entry(entry)
            entry_manager.delete_entry(created.id)

        # Create one active entry
        entry_manager.create_entry(sample_entries[2])

        deleted = entry_manager.get_deleted_entries()
        assert len(deleted) == 2

    def test_search_entries_by_query(self, entry_manager, sample_entries):
        """Test searching entries by text query."""
        for entry in sample_entries:
            entry_manager.create_entry(entry)

        # Search for "meeting"
        results = entry_manager.search_entries(query="meeting")
        assert len(results) == 1
        assert results[0].trigger == "meeting"

    def test_search_entries_by_tags(self, entry_manager, sample_entries):
        """Test searching entries by tags."""
        for entry in sample_entries:
            entry_manager.create_entry(entry)

        # Search for "work" tag
        results = entry_manager.search_entries(tags=["work"])
        assert len(results) == 1
        assert "work" in results[0].tags

    def test_search_entries_by_query_and_tags(self, entry_manager, sample_entries):
        """Test searching entries by both query and tags."""
        for entry in sample_entries:
            entry_manager.create_entry(entry)

        # Search for query with tag filter
        results = entry_manager.search_entries(query="123", tags=["personal"])
        assert len(results) == 1
        assert results[0].trigger == "addr"

    def test_get_all_tags(self, entry_manager, sample_entries):
        """Test getting all unique tags with counts."""
        for entry in sample_entries:
            entry_manager.create_entry(entry)

        tags = entry_manager.get_all_tags()
        assert "work" in tags
        assert "email" in tags
        assert tags["work"] == 1  # One entry with "work" tag

    def test_get_stats(self, entry_manager, sample_entries):
        """Test getting entry statistics."""
        for entry in sample_entries:
            entry_manager.create_entry(entry)

        # Delete one entry
        entry_manager.delete_entry(sample_entries[0].id)

        stats = entry_manager.get_stats()
        assert stats["total_entries"] == 2  # Active entries only
        assert stats["deleted_entries"] == 1

    def test_change_listener(self, entry_manager, sample_entry):
        """Test change listener notification."""
        callback_called = False

        def callback():
            nonlocal callback_called
            callback_called = True

        entry_manager.add_change_listener(callback)

        # Create entry should trigger callback
        entry_manager.create_entry(sample_entry)
        assert callback_called is True

        # Reset
        callback_called = False

        # Update should trigger callback
        sample_entry.replacement = "Modified"
        entry_manager.update_entry(sample_entry)
        assert callback_called is True

    def test_remove_change_listener(self, entry_manager, sample_entry):
        """Test removing change listener."""
        callback_called = False

        def callback():
            nonlocal callback_called
            callback_called = True

        entry_manager.add_change_listener(callback)
        entry_manager.remove_change_listener(callback)

        # Create entry should NOT trigger callback
        entry_manager.create_entry(sample_entry)
        assert callback_called is False

    def test_history_on_create(self, entry_manager, sample_entry):
        """Test that history is logged on entry creation."""
        created = entry_manager.create_entry(sample_entry)

        # Check history was logged
        history = entry_manager.db.get_entry_history(created.id)
        assert len(history) > 0
        assert history[0].action == "created"
        assert history[0].entry_id == created.id

    def test_history_on_update(self, entry_manager, sample_entry):
        """Test that history is logged on entry update."""
        created = entry_manager.create_entry(sample_entry)
        created.replacement = "Updated text"
        entry_manager.update_entry(created)

        # Check history
        history = entry_manager.db.get_entry_history(created.id)
        actions = [h.action for h in history]
        assert "created" in actions
        assert "modified" in actions

    def test_history_on_delete(self, entry_manager, sample_entry):
        """Test that history is logged on entry deletion."""
        created = entry_manager.create_entry(sample_entry)
        entry_manager.delete_entry(created.id)

        # Check history
        history = entry_manager.db.get_entry_history(created.id)
        actions = [h.action for h in history]
        assert "deleted" in actions

    def test_history_on_restore(self, entry_manager, sample_entry):
        """Test that history is logged on entry restoration."""
        created = entry_manager.create_entry(sample_entry)
        entry_manager.delete_entry(created.id)
        entry_manager.restore_entry(created.id)

        # Check history
        history = entry_manager.db.get_entry_history(created.id)
        actions = [h.action for h in history]
        assert "restored" in actions
