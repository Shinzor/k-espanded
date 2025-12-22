"""Conflict detection and resolution for GitHub sync."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class ConflictResolution(Enum):
    """Conflict resolution strategy."""

    KEEP_LOCAL = "local"
    KEEP_REMOTE = "remote"
    KEEP_BOTH = "both"
    MANUAL = "manual"


@dataclass
class FileConflict:
    """Represents a file sync conflict."""

    path: str
    local_content: str | None
    remote_content: str | None
    local_modified: datetime | None
    remote_modified: datetime | None
    conflict_type: str  # "both_modified" - only type now (single-side files are not conflicts)

    @property
    def is_major_conflict(self) -> bool:
        """Check if this is a major conflict requiring user intervention.

        Major conflicts occur when both versions were modified within
        1 minute of each other (making timestamp-based resolution unreliable).
        """
        # Both modified within 1 minute - timestamps too close to auto-resolve
        if (
            self.local_modified
            and self.remote_modified
            and abs(self.local_modified - self.remote_modified) < timedelta(minutes=1)
        ):
            return True

        return False

    def get_suggested_resolution(self) -> ConflictResolution:
        """Get suggested resolution based on timestamps.

        For "both_modified" conflicts, the newer version wins.
        If timestamps are within 1 minute, it's a major conflict requiring manual resolution.

        Returns:
            ConflictResolution.KEEP_LOCAL if local is newer
            ConflictResolution.KEEP_REMOTE if remote is newer
            ConflictResolution.MANUAL if timestamps are too close to auto-resolve
        """
        # Compare timestamps - newer wins
        if self.local_modified and self.remote_modified:
            # If timestamps are within 1 minute, require manual resolution
            if abs(self.local_modified - self.remote_modified) < timedelta(minutes=1):
                return ConflictResolution.MANUAL

            if self.local_modified > self.remote_modified:
                return ConflictResolution.KEEP_LOCAL
            else:
                return ConflictResolution.KEEP_REMOTE

        # If we can't compare timestamps, keep local (safer default)
        if self.local_modified:
            return ConflictResolution.KEEP_LOCAL
        if self.remote_modified:
            return ConflictResolution.KEEP_REMOTE

        # Fallback - keep local
        return ConflictResolution.KEEP_LOCAL


class ConflictResolver:
    """Handles conflict detection and resolution for sync operations."""

    def __init__(self):
        """Initialize conflict resolver."""
        self.conflicts: list[FileConflict] = []

    def detect_conflicts(
        self,
        local_files: dict[str, tuple[str, datetime]],
        remote_files: dict[str, tuple[str, datetime]],
        last_sync: datetime | None = None,
    ) -> list[FileConflict]:
        """Detect conflicts between local and remote files.

        Only files that exist on BOTH sides with different content are conflicts.
        Files that only exist on one side are NOT conflicts - they are simply
        new files to be synced and are handled separately by the sync manager.

        Args:
            local_files: Dict of {path: (content, modified_time)}
            remote_files: Dict of {path: (content, modified_time)}
            last_sync: Last sync timestamp (used to detect deletion conflicts)

        Returns:
            List of detected conflicts
        """
        conflicts = []

        # Only check files that exist on BOTH sides
        common_paths = set(local_files.keys()) & set(remote_files.keys())

        for path in common_paths:
            local_data = local_files.get(path)
            remote_data = remote_files.get(path)

            if local_data and remote_data:
                local_content, local_time = local_data
                remote_content, remote_time = remote_data

                # Content differs - this is a real conflict
                if local_content != remote_content:
                    conflicts.append(
                        FileConflict(
                            path=path,
                            local_content=local_content,
                            remote_content=remote_content,
                            local_modified=local_time,
                            remote_modified=remote_time,
                            conflict_type="both_modified",
                        )
                    )

        # Note: Files that only exist on one side are NOT conflicts.
        # - Local-only files: new files to push to remote
        # - Remote-only files: new files to pull to local
        # These are handled by sync_manager.sync() in the "Sync files without conflicts" section.

        self.conflicts = conflicts
        return conflicts

    def auto_resolve(
        self, conflicts: list[FileConflict]
    ) -> tuple[list[FileConflict], list[FileConflict]]:
        """Automatically resolve conflicts where possible.

        Args:
            conflicts: List of conflicts to resolve

        Returns:
            Tuple of (resolved_conflicts, unresolved_conflicts)
        """
        resolved = []
        unresolved = []

        for conflict in conflicts:
            resolution = conflict.get_suggested_resolution()

            if resolution == ConflictResolution.MANUAL:
                # Cannot auto-resolve - needs user input
                unresolved.append(conflict)
            else:
                # Can auto-resolve based on timestamps
                resolved.append(conflict)

        return resolved, unresolved

    def resolve_conflict(
        self, conflict: FileConflict, resolution: ConflictResolution
    ) -> str | None:
        """Resolve a conflict with the given strategy.

        Args:
            conflict: The conflict to resolve
            resolution: Resolution strategy to apply

        Returns:
            Content to use (None means delete the file)
        """
        if resolution == ConflictResolution.KEEP_LOCAL:
            return conflict.local_content

        elif resolution == ConflictResolution.KEEP_REMOTE:
            return conflict.remote_content

        elif resolution == ConflictResolution.KEEP_BOTH:
            # For "keep both", we need to merge or create a variant
            # For now, we'll append a timestamp to create a backup
            if conflict.local_content and conflict.remote_content:
                # Create a merged version with both contents marked
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                merged = f"""# Conflict Resolution - {timestamp}
# This file had conflicting changes. Both versions are preserved below.

# ========== LOCAL VERSION ==========
{conflict.local_content}

# ========== REMOTE VERSION ==========
{conflict.remote_content}
"""
                return merged
            # If one is None, fall back to the existing one
            return conflict.local_content or conflict.remote_content

        elif resolution == ConflictResolution.MANUAL:
            # Manual resolution - caller should have converted this to a concrete resolution
            # If we get here, default to keeping local version (safer)
            return conflict.local_content

        return None

    def get_major_conflicts(self) -> list[FileConflict]:
        """Get all major conflicts that require user intervention.

        Returns:
            List of major conflicts
        """
        return [c for c in self.conflicts if c.is_major_conflict]

    def get_minor_conflicts(self) -> list[FileConflict]:
        """Get all minor conflicts that can be auto-resolved.

        Returns:
            List of minor conflicts
        """
        return [c for c in self.conflicts if not c.is_major_conflict]

    def clear_conflicts(self):
        """Clear all stored conflicts."""
        self.conflicts = []

    def has_conflicts(self) -> bool:
        """Check if there are any conflicts.

        Returns:
            True if conflicts exist, False otherwise
        """
        return len(self.conflicts) > 0

    def has_major_conflicts(self) -> bool:
        """Check if there are any major conflicts.

        Returns:
            True if major conflicts exist, False otherwise
        """
        return any(c.is_major_conflict for c in self.conflicts)
