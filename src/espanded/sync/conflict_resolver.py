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
    conflict_type: str  # "both_modified", "local_deleted", "remote_deleted"

    @property
    def is_major_conflict(self) -> bool:
        """Check if this is a major conflict requiring user intervention.

        Major conflicts occur when:
        - Both versions modified within 1 minute of each other
        - File deleted on one side but modified on other
        """
        # Deletion conflicts are always major
        if self.conflict_type in ("local_deleted", "remote_deleted"):
            return True

        # Both modified - check if within 1 minute threshold
        if (
            self.local_modified
            and self.remote_modified
            and abs(self.local_modified - self.remote_modified) < timedelta(minutes=1)
        ):
            return True

        return False

    def get_suggested_resolution(self) -> ConflictResolution:
        """Get suggested resolution based on timestamps.

        Returns:
            ConflictResolution.KEEP_LOCAL if local is newer
            ConflictResolution.KEEP_REMOTE if remote is newer
            ConflictResolution.MANUAL if timestamps are equal or conflict is major
        """
        # Major conflicts require manual resolution
        if self.is_major_conflict:
            return ConflictResolution.MANUAL

        # Deletion conflicts
        if self.conflict_type == "local_deleted":
            # Local deleted, remote modified - keep remote (restore file)
            return ConflictResolution.KEEP_REMOTE
        if self.conflict_type == "remote_deleted":
            # Remote deleted, local modified - keep local (push deletion)
            return ConflictResolution.KEEP_LOCAL

        # Compare timestamps for "both_modified"
        if self.local_modified and self.remote_modified:
            if self.local_modified > self.remote_modified:
                return ConflictResolution.KEEP_LOCAL
            elif self.remote_modified > self.local_modified:
                return ConflictResolution.KEEP_REMOTE
            else:
                # Equal timestamps - require manual resolution
                return ConflictResolution.MANUAL

        # Fallback to manual
        return ConflictResolution.MANUAL


class ConflictResolver:
    """Handles conflict detection and resolution for sync operations."""

    def __init__(self):
        """Initialize conflict resolver."""
        self.conflicts: list[FileConflict] = []

    def detect_conflicts(
        self,
        local_files: dict[str, tuple[str, datetime]],
        remote_files: dict[str, tuple[str, datetime]],
    ) -> list[FileConflict]:
        """Detect conflicts between local and remote files.

        Args:
            local_files: Dict of {path: (content, modified_time)}
            remote_files: Dict of {path: (content, modified_time)}

        Returns:
            List of detected conflicts
        """
        conflicts = []
        all_paths = set(local_files.keys()) | set(remote_files.keys())

        for path in all_paths:
            local_data = local_files.get(path)
            remote_data = remote_files.get(path)

            # Both exist - check if modified
            if local_data and remote_data:
                local_content, local_time = local_data
                remote_content, remote_time = remote_data

                # Content differs - conflict
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

            # Only local exists - remote deleted
            elif local_data and not remote_data:
                local_content, local_time = local_data
                conflicts.append(
                    FileConflict(
                        path=path,
                        local_content=local_content,
                        remote_content=None,
                        local_modified=local_time,
                        remote_modified=None,
                        conflict_type="remote_deleted",
                    )
                )

            # Only remote exists - local deleted
            elif remote_data and not local_data:
                remote_content, remote_time = remote_data
                conflicts.append(
                    FileConflict(
                        path=path,
                        local_content=None,
                        remote_content=remote_content,
                        local_modified=None,
                        remote_modified=remote_time,
                        conflict_type="local_deleted",
                    )
                )

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
            # Manual resolution should be handled by caller
            raise ValueError("Manual resolution must be handled by user")

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
