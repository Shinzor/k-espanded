"""GitHub sync module for Espanded."""

from espanded.sync.github_sync import GitHubSync
from espanded.sync.sync_manager import SyncManager
from espanded.sync.conflict_resolver import ConflictResolver, ConflictResolution

__all__ = [
    "GitHubSync",
    "SyncManager",
    "ConflictResolver",
    "ConflictResolution",
]
