"""Integration tests for full entry lifecycle workflow."""

import pytest
from datetime import datetime

from espanded.core.models import Entry
from espanded.core.entry_manager import EntryManager


class TestFullWorkflow:
    """Integration tests for complete entry lifecycle."""

    def test_entry_lifecycle(self, entry_manager):
        """Test complete entry lifecycle: create, update, delete, restore."""
        # Create entry
        entry = Entry(
            trigger="test",
            prefix=":",
            replacement="Test content",
            tags=["test", "demo"],
        )

        created = entry_manager.create_entry(entry)
        assert created.id != ""
        assert created.trigger == "test"

        # Verify it appears in all entries
        all_entries = entry_manager.get_all_entries()
        assert created.id in [e.id for e in all_entries]

        # Update entry
        created.replacement = "Updated content"
        created.tags.append("updated")

        updated = entry_manager.update_entry(created)
        assert updated.replacement == "Updated content"
        assert "updated" in updated.tags
        assert updated.modified_at > created.created_at

        # Delete entry (soft delete)
        deleted = entry_manager.delete_entry(created.id)
        assert deleted is True

        # Verify it doesn't appear in active entries
        all_entries = entry_manager.get_all_entries()
        assert created.id not in [e.id for e in all_entries]

        # Verify it appears in deleted entries
        deleted_entries = entry_manager.get_deleted_entries()
        assert created.id in [e.id for e in deleted_entries]

        # Restore entry
        restored = entry_manager.restore_entry(created.id)
        assert restored is True

        # Verify it's back in active entries
        all_entries = entry_manager.get_all_entries()
        assert created.id in [e.id for e in all_entries]

        # Permanent delete
        permanent = entry_manager.permanent_delete(created.id)
        assert permanent is True

        # Verify it's completely gone
        entry_result = entry_manager.get_entry(created.id)
        assert entry_result is None

    def test_multiple_entries_with_search(self, entry_manager):
        """Test creating multiple entries and searching."""
        # Create multiple entries
        entries = [
            Entry(trigger="email", prefix=":", replacement="test@example.com", tags=["contact"]),
            Entry(trigger="phone", prefix=":", replacement="555-1234", tags=["contact"]),
            Entry(trigger="addr", prefix=":", replacement="123 Main St", tags=["personal"]),
            Entry(trigger="meeting", prefix="::", replacement="Meeting at...", tags=["work"]),
        ]

        for entry in entries:
            entry_manager.create_entry(entry)

        # Test get all
        all_entries = entry_manager.get_all_entries()
        assert len(all_entries) == 4

        # Test search by query
        results = entry_manager.search_entries(query="555")
        assert len(results) == 1
        assert results[0].trigger == "phone"

        # Test search by tags
        results = entry_manager.search_entries(tags=["contact"])
        assert len(results) == 2

        # Test combined search
        results = entry_manager.search_entries(query="example", tags=["contact"])
        assert len(results) == 1
        assert results[0].trigger == "email"

    def test_entry_cloning(self, entry_manager):
        """Test cloning entries."""
        # Create original entry
        original = Entry(
            trigger="original",
            prefix=":",
            replacement="Original content",
            tags=["original", "test"],
            propagate_case=True,
        )

        created = entry_manager.create_entry(original)

        # Clone it
        cloned = entry_manager.clone_entry(created.id)

        assert cloned is not None
        assert cloned.id != created.id
        assert cloned.trigger == "original_copy"
        assert cloned.replacement == created.replacement
        assert cloned.tags == created.tags
        assert cloned.propagate_case == created.propagate_case

        # Verify both exist
        all_entries = entry_manager.get_all_entries()
        assert len(all_entries) == 2

    def test_history_tracking(self, entry_manager):
        """Test that history is properly tracked."""
        # Create entry
        entry = Entry(trigger="hist", prefix=":", replacement="Initial")
        created = entry_manager.create_entry(entry)

        # Update multiple times
        created.replacement = "Update 1"
        entry_manager.update_entry(created)

        created.replacement = "Update 2"
        entry_manager.update_entry(created)

        # Delete
        entry_manager.delete_entry(created.id)

        # Restore
        entry_manager.restore_entry(created.id)

        # Check history
        history = entry_manager.db.get_entry_history(created.id)

        actions = [h.action for h in history]
        assert "created" in actions
        assert "modified" in actions
        assert "deleted" in actions
        assert "restored" in actions

        # Should have at least 5 entries (create + 2 updates + delete + restore)
        assert len(history) >= 5

    def test_tag_management(self, entry_manager):
        """Test tag collection and counting."""
        # Create entries with various tags
        entries = [
            Entry(trigger="e1", prefix=":", replacement="Content", tags=["work", "email"]),
            Entry(trigger="e2", prefix=":", replacement="Content", tags=["work", "template"]),
            Entry(trigger="e3", prefix=":", replacement="Content", tags=["personal"]),
            Entry(trigger="e4", prefix=":", replacement="Content", tags=["work"]),
        ]

        for entry in entries:
            entry_manager.create_entry(entry)

        # Get all tags
        tags = entry_manager.get_all_tags()

        assert "work" in tags
        assert tags["work"] == 3
        assert "email" in tags
        assert tags["email"] == 1
        assert "personal" in tags
        assert tags["personal"] == 1

    def test_statistics(self, entry_manager):
        """Test entry statistics."""
        # Create entries
        entries = [
            Entry(trigger="e1", prefix=":", replacement="Content"),
            Entry(trigger="e2", prefix=":", replacement="Content"),
            Entry(trigger="e3", prefix=":", replacement="Content"),
        ]

        created_ids = []
        for entry in entries:
            created = entry_manager.create_entry(entry)
            created_ids.append(created.id)

        # Delete one
        entry_manager.delete_entry(created_ids[0])

        # Get stats
        stats = entry_manager.get_stats()

        assert stats["total_entries"] == 2  # Active entries only
        assert stats["deleted_entries"] == 1

    def test_change_notifications(self, entry_manager):
        """Test change listener notifications."""
        notifications = []

        def listener():
            notifications.append(datetime.now())

        entry_manager.add_change_listener(listener)

        # Create entry
        entry = Entry(trigger="test", prefix=":", replacement="Content")
        created = entry_manager.create_entry(entry)
        assert len(notifications) == 1

        # Update entry
        created.replacement = "Updated"
        entry_manager.update_entry(created)
        assert len(notifications) == 2

        # Delete entry
        entry_manager.delete_entry(created.id)
        assert len(notifications) == 3

        # Restore entry
        entry_manager.restore_entry(created.id)
        assert len(notifications) == 4

        # Remove listener
        entry_manager.remove_change_listener(listener)

        # Create another entry - should not notify
        entry2 = Entry(trigger="test2", prefix=":", replacement="Content")
        entry_manager.create_entry(entry2)
        assert len(notifications) == 4  # Still 4, no new notification

    def test_concurrent_operations(self, entry_manager):
        """Test multiple operations in sequence."""
        # Create multiple entries quickly
        entries = []
        for i in range(10):
            entry = Entry(
                trigger=f"test{i}",
                prefix=":",
                replacement=f"Content {i}",
                tags=[f"tag{i % 3}"],
            )
            created = entry_manager.create_entry(entry)
            entries.append(created)

        # Verify all were created
        all_entries = entry_manager.get_all_entries()
        assert len(all_entries) == 10

        # Delete half
        for i in range(5):
            entry_manager.delete_entry(entries[i].id)

        # Verify counts
        all_entries = entry_manager.get_all_entries()
        deleted_entries = entry_manager.get_deleted_entries()
        assert len(all_entries) == 5
        assert len(deleted_entries) == 5

        # Restore some
        for i in range(2):
            entry_manager.restore_entry(entries[i].id)

        # Verify final counts
        all_entries = entry_manager.get_all_entries()
        deleted_entries = entry_manager.get_deleted_entries()
        assert len(all_entries) == 7
        assert len(deleted_entries) == 3
