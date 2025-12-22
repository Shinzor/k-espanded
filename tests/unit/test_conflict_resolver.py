"""Tests for conflict resolution."""

import pytest
from datetime import datetime, timedelta

from espanded.sync.conflict_resolver import (
    ConflictResolver,
    FileConflict,
    ConflictResolution,
)


class TestFileConflict:
    """Tests for FileConflict dataclass."""

    def test_is_major_conflict_deletion(self):
        """Test major conflict detection for deletions."""
        conflict = FileConflict(
            path="test.yml",
            local_content="content",
            remote_content=None,
            local_modified=datetime.now(),
            remote_modified=None,
            conflict_type="remote_deleted",
        )

        assert conflict.is_major_conflict is True

    def test_is_major_conflict_both_modified_same_time(self):
        """Test major conflict when both modified within 1 minute."""
        now = datetime.now()
        conflict = FileConflict(
            path="test.yml",
            local_content="local",
            remote_content="remote",
            local_modified=now,
            remote_modified=now + timedelta(seconds=30),
            conflict_type="both_modified",
        )

        assert conflict.is_major_conflict is True

    def test_is_not_major_conflict(self):
        """Test non-major conflict when times differ significantly."""
        now = datetime.now()
        conflict = FileConflict(
            path="test.yml",
            local_content="local",
            remote_content="remote",
            local_modified=now,
            remote_modified=now - timedelta(minutes=5),
            conflict_type="both_modified",
        )

        assert conflict.is_major_conflict is False

    def test_get_suggested_resolution_local_newer(self):
        """Test suggested resolution when local is newer."""
        now = datetime.now()
        conflict = FileConflict(
            path="test.yml",
            local_content="local",
            remote_content="remote",
            local_modified=now,
            remote_modified=now - timedelta(hours=1),
            conflict_type="both_modified",
        )

        resolution = conflict.get_suggested_resolution()
        assert resolution == ConflictResolution.KEEP_LOCAL

    def test_get_suggested_resolution_remote_newer(self):
        """Test suggested resolution when remote is newer."""
        now = datetime.now()
        conflict = FileConflict(
            path="test.yml",
            local_content="local",
            remote_content="remote",
            local_modified=now - timedelta(hours=1),
            remote_modified=now,
            conflict_type="both_modified",
        )

        resolution = conflict.get_suggested_resolution()
        assert resolution == ConflictResolution.KEEP_REMOTE

    def test_get_suggested_resolution_major_conflict(self):
        """Test suggested resolution for major conflict."""
        now = datetime.now()
        conflict = FileConflict(
            path="test.yml",
            local_content="local",
            remote_content="remote",
            local_modified=now,
            remote_modified=now + timedelta(seconds=10),
            conflict_type="both_modified",
        )

        resolution = conflict.get_suggested_resolution()
        assert resolution == ConflictResolution.MANUAL

    def test_get_suggested_resolution_local_deleted(self):
        """Test suggested resolution when local is deleted."""
        conflict = FileConflict(
            path="test.yml",
            local_content=None,
            remote_content="remote",
            local_modified=None,
            remote_modified=datetime.now(),
            conflict_type="local_deleted",
        )

        # Deletion conflicts are major conflicts, require manual resolution
        resolution = conflict.get_suggested_resolution()
        assert resolution == ConflictResolution.MANUAL

    def test_get_suggested_resolution_remote_deleted(self):
        """Test suggested resolution when remote is deleted."""
        conflict = FileConflict(
            path="test.yml",
            local_content="local",
            remote_content=None,
            local_modified=datetime.now(),
            remote_modified=None,
            conflict_type="remote_deleted",
        )

        # Deletion conflicts are major conflicts, require manual resolution
        resolution = conflict.get_suggested_resolution()
        assert resolution == ConflictResolution.MANUAL


class TestConflictResolver:
    """Tests for ConflictResolver class."""

    def test_detect_conflicts_both_modified(self):
        """Test detecting conflicts when both versions are modified."""
        resolver = ConflictResolver()

        now = datetime.now()
        local_files = {
            "test.yml": ("local content", now),
        }
        remote_files = {
            "test.yml": ("remote content", now - timedelta(hours=1)),
        }

        conflicts = resolver.detect_conflicts(local_files, remote_files)

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "both_modified"
        assert conflicts[0].path == "test.yml"

    def test_detect_conflicts_no_conflict_same_content(self):
        """Test no conflict when content is the same."""
        resolver = ConflictResolver()

        now = datetime.now()
        local_files = {
            "test.yml": ("same content", now),
        }
        remote_files = {
            "test.yml": ("same content", now),
        }

        conflicts = resolver.detect_conflicts(local_files, remote_files)

        assert len(conflicts) == 0

    def test_detect_conflicts_local_deleted(self):
        """Test detecting conflicts when local file is deleted."""
        resolver = ConflictResolver()

        now = datetime.now()
        local_files = {}
        remote_files = {
            "test.yml": ("remote content", now),
        }

        conflicts = resolver.detect_conflicts(local_files, remote_files)

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "local_deleted"

    def test_detect_conflicts_remote_deleted(self):
        """Test detecting conflicts when remote file is deleted."""
        resolver = ConflictResolver()

        now = datetime.now()
        local_files = {
            "test.yml": ("local content", now),
        }
        remote_files = {}

        conflicts = resolver.detect_conflicts(local_files, remote_files)

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "remote_deleted"

    def test_detect_conflicts_multiple_files(self):
        """Test detecting conflicts across multiple files."""
        resolver = ConflictResolver()

        now = datetime.now()
        local_files = {
            "file1.yml": ("local1", now),
            "file2.yml": ("local2", now),
            "file3.yml": ("same", now),
        }
        remote_files = {
            "file1.yml": ("remote1", now - timedelta(hours=1)),
            "file3.yml": ("same", now),
            "file4.yml": ("remote4", now),
        }

        conflicts = resolver.detect_conflicts(local_files, remote_files)

        # file1: both_modified
        # file2: remote_deleted
        # file3: no conflict (same content)
        # file4: local_deleted
        assert len(conflicts) == 3

    def test_auto_resolve(self):
        """Test automatic resolution of conflicts."""
        resolver = ConflictResolver()

        now = datetime.now()
        conflicts = [
            # Can auto-resolve - local newer
            FileConflict(
                path="auto1.yml",
                local_content="local",
                remote_content="remote",
                local_modified=now,
                remote_modified=now - timedelta(hours=1),
                conflict_type="both_modified",
            ),
            # Cannot auto-resolve - major conflict
            FileConflict(
                path="manual.yml",
                local_content="local",
                remote_content="remote",
                local_modified=now,
                remote_modified=now + timedelta(seconds=10),
                conflict_type="both_modified",
            ),
        ]

        resolved, unresolved = resolver.auto_resolve(conflicts)

        assert len(resolved) == 1
        assert len(unresolved) == 1
        assert resolved[0].path == "auto1.yml"
        assert unresolved[0].path == "manual.yml"

    def test_resolve_conflict_keep_local(self):
        """Test resolving conflict by keeping local version."""
        resolver = ConflictResolver()

        conflict = FileConflict(
            path="test.yml",
            local_content="local content",
            remote_content="remote content",
            local_modified=datetime.now(),
            remote_modified=datetime.now(),
            conflict_type="both_modified",
        )

        result = resolver.resolve_conflict(conflict, ConflictResolution.KEEP_LOCAL)

        assert result == "local content"

    def test_resolve_conflict_keep_remote(self):
        """Test resolving conflict by keeping remote version."""
        resolver = ConflictResolver()

        conflict = FileConflict(
            path="test.yml",
            local_content="local content",
            remote_content="remote content",
            local_modified=datetime.now(),
            remote_modified=datetime.now(),
            conflict_type="both_modified",
        )

        result = resolver.resolve_conflict(conflict, ConflictResolution.KEEP_REMOTE)

        assert result == "remote content"

    def test_resolve_conflict_keep_both(self):
        """Test resolving conflict by keeping both versions."""
        resolver = ConflictResolver()

        conflict = FileConflict(
            path="test.yml",
            local_content="local content",
            remote_content="remote content",
            local_modified=datetime.now(),
            remote_modified=datetime.now(),
            conflict_type="both_modified",
        )

        result = resolver.resolve_conflict(conflict, ConflictResolution.KEEP_BOTH)

        assert result is not None
        assert "LOCAL VERSION" in result
        assert "REMOTE VERSION" in result
        assert "local content" in result
        assert "remote content" in result

    def test_resolve_conflict_keep_both_one_none(self):
        """Test keeping both when one version is None."""
        resolver = ConflictResolver()

        conflict = FileConflict(
            path="test.yml",
            local_content="local content",
            remote_content=None,
            local_modified=datetime.now(),
            remote_modified=None,
            conflict_type="remote_deleted",
        )

        result = resolver.resolve_conflict(conflict, ConflictResolution.KEEP_BOTH)

        assert result == "local content"

    def test_resolve_conflict_manual_raises_error(self):
        """Test that manual resolution raises error."""
        resolver = ConflictResolver()

        conflict = FileConflict(
            path="test.yml",
            local_content="local",
            remote_content="remote",
            local_modified=datetime.now(),
            remote_modified=datetime.now(),
            conflict_type="both_modified",
        )

        with pytest.raises(ValueError):
            resolver.resolve_conflict(conflict, ConflictResolution.MANUAL)

    def test_get_major_conflicts(self):
        """Test getting major conflicts."""
        resolver = ConflictResolver()

        now = datetime.now()
        resolver.conflicts = [
            FileConflict(
                path="major.yml",
                local_content="local",
                remote_content=None,
                local_modified=now,
                remote_modified=None,
                conflict_type="remote_deleted",
            ),
            FileConflict(
                path="minor.yml",
                local_content="local",
                remote_content="remote",
                local_modified=now,
                remote_modified=now - timedelta(hours=1),
                conflict_type="both_modified",
            ),
        ]

        major = resolver.get_major_conflicts()

        assert len(major) == 1
        assert major[0].path == "major.yml"

    def test_get_minor_conflicts(self):
        """Test getting minor conflicts."""
        resolver = ConflictResolver()

        now = datetime.now()
        resolver.conflicts = [
            FileConflict(
                path="major.yml",
                local_content="local",
                remote_content=None,
                local_modified=now,
                remote_modified=None,
                conflict_type="remote_deleted",
            ),
            FileConflict(
                path="minor.yml",
                local_content="local",
                remote_content="remote",
                local_modified=now,
                remote_modified=now - timedelta(hours=1),
                conflict_type="both_modified",
            ),
        ]

        minor = resolver.get_minor_conflicts()

        assert len(minor) == 1
        assert minor[0].path == "minor.yml"

    def test_clear_conflicts(self):
        """Test clearing conflicts."""
        resolver = ConflictResolver()

        resolver.conflicts = [
            FileConflict(
                path="test.yml",
                local_content="local",
                remote_content="remote",
                local_modified=datetime.now(),
                remote_modified=datetime.now(),
                conflict_type="both_modified",
            ),
        ]

        resolver.clear_conflicts()

        assert len(resolver.conflicts) == 0

    def test_has_conflicts(self):
        """Test checking if conflicts exist."""
        resolver = ConflictResolver()

        assert resolver.has_conflicts() is False

        resolver.conflicts = [
            FileConflict(
                path="test.yml",
                local_content="local",
                remote_content="remote",
                local_modified=datetime.now(),
                remote_modified=datetime.now(),
                conflict_type="both_modified",
            ),
        ]

        assert resolver.has_conflicts() is True

    def test_has_major_conflicts(self):
        """Test checking if major conflicts exist."""
        resolver = ConflictResolver()

        now = datetime.now()
        resolver.conflicts = [
            FileConflict(
                path="minor.yml",
                local_content="local",
                remote_content="remote",
                local_modified=now,
                remote_modified=now - timedelta(hours=1),
                conflict_type="both_modified",
            ),
        ]

        assert resolver.has_major_conflicts() is False

        resolver.conflicts.append(
            FileConflict(
                path="major.yml",
                local_content="local",
                remote_content=None,
                local_modified=now,
                remote_modified=None,
                conflict_type="remote_deleted",
            )
        )

        assert resolver.has_major_conflicts() is True
