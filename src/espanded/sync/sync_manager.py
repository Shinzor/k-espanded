"""Sync manager for orchestrating GitHub sync operations."""

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable

from espanded.sync.github_sync import GitHubSync, GitHubAPIError
from espanded.sync.conflict_resolver import (
    ConflictResolver,
    ConflictResolution,
    FileConflict,
)


logger = logging.getLogger(__name__)


class SyncError(Exception):
    """Exception raised for sync errors."""
    pass


class SyncManager:
    """Manages GitHub sync operations for Espanso configurations."""

    def __init__(
        self,
        repo: str,
        token: str,
        local_path: Path,
        on_conflict: Callable[[list[FileConflict]], dict[str, ConflictResolution]] | None = None,
    ):
        """Initialize sync manager.

        Args:
            repo: GitHub repository in format "owner/repo"
            token: GitHub Personal Access Token
            local_path: Local Espanso config directory path
            on_conflict: Callback for handling conflicts (called with list of conflicts,
                        should return dict mapping file paths to resolutions)
        """
        self.repo = repo
        self.token = token
        self.local_path = Path(local_path)
        self.on_conflict = on_conflict

        self.github = GitHubSync(repo, token)
        self.resolver = ConflictResolver()

        # Sync state
        self.last_sync: datetime | None = None
        self.is_syncing = False
        self.sync_lock = threading.Lock()

        # Auto-sync timer
        self._timer: threading.Timer | None = None
        self._auto_sync_enabled = False
        self._sync_interval = 300  # seconds

    def test_connection(self) -> bool:
        """Test GitHub connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            return self.github.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def push(self, message: str | None = None) -> dict[str, str]:
        """Push local changes to GitHub.

        Args:
            message: Commit message (auto-generated if None)

        Returns:
            Dict of {file_path: status} where status is "created", "updated", or "deleted"

        Raises:
            SyncError: If sync fails
        """
        with self.sync_lock:
            if self.is_syncing:
                raise SyncError("Sync already in progress")

            self.is_syncing = True

        try:
            results = {}
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            default_message = f"Update from Espanded - {timestamp}"

            # Get local files
            local_files = self._get_local_files()

            # Process each file
            for rel_path, (content, _) in local_files.items():
                try:
                    # Get remote file info
                    remote_data = self.github.get_file_content(rel_path)

                    if remote_data:
                        # File exists - update
                        _, sha = remote_data
                        self.github.create_or_update_file(
                            path=rel_path,
                            content=content,
                            message=message or default_message,
                            sha=sha,
                        )
                        results[rel_path] = "updated"
                    else:
                        # File doesn't exist - create
                        self.github.create_or_update_file(
                            path=rel_path,
                            content=content,
                            message=message or default_message,
                        )
                        results[rel_path] = "created"

                except GitHubAPIError as e:
                    logger.error(f"Failed to push {rel_path}: {e}")
                    raise SyncError(f"Failed to push {rel_path}: {e}")

            self.last_sync = datetime.now()
            return results

        finally:
            self.is_syncing = False

    def pull(self) -> dict[str, str]:
        """Pull remote changes from GitHub.

        Returns:
            Dict of {file_path: status} where status is "created", "updated", or "deleted"

        Raises:
            SyncError: If sync fails
        """
        with self.sync_lock:
            if self.is_syncing:
                raise SyncError("Sync already in progress")

            self.is_syncing = True

        try:
            results = {}

            # Get remote files
            remote_files = self._get_remote_files()

            # Process each file
            for rel_path, (content, _) in remote_files.items():
                try:
                    local_file = self.local_path / rel_path
                    local_file.parent.mkdir(parents=True, exist_ok=True)

                    if local_file.exists():
                        # File exists - update
                        local_file.write_text(content, encoding="utf-8")
                        results[rel_path] = "updated"
                    else:
                        # File doesn't exist - create
                        local_file.write_text(content, encoding="utf-8")
                        results[rel_path] = "created"

                except Exception as e:
                    logger.error(f"Failed to pull {rel_path}: {e}")
                    raise SyncError(f"Failed to pull {rel_path}: {e}")

            self.last_sync = datetime.now()
            return results

        finally:
            self.is_syncing = False

    def sync(self) -> dict:
        """Perform bidirectional sync with conflict resolution.

        Returns:
            Dict with keys:
                - success: bool
                - pushed: int (number of files pushed)
                - pulled: int (number of files pulled)
                - files: dict of {file_path: status}
                - error: str (only if success=False)

        Raises:
            SyncError: If sync fails critically
        """
        with self.sync_lock:
            if self.is_syncing:
                raise SyncError("Sync already in progress")

            self.is_syncing = True

        try:
            results = {}
            pushed_count = 0
            pulled_count = 0

            # Get local and remote files
            local_files = self._get_local_files()
            remote_files = self._get_remote_files()

            logger.info(f"Sync: Found {len(local_files)} local files, {len(remote_files)} remote files")

            # Detect conflicts
            conflicts = self.resolver.detect_conflicts(local_files, remote_files)

            if conflicts:
                logger.info(f"Sync: Detected {len(conflicts)} conflicts")
                # Try to auto-resolve
                resolved, unresolved = self.resolver.auto_resolve(conflicts)

                # Handle unresolved conflicts
                if unresolved:
                    if self.on_conflict:
                        # Call user-provided conflict handler
                        resolutions = self.on_conflict(unresolved)

                        # Apply manual resolutions
                        for conflict in unresolved:
                            resolution = resolutions.get(
                                conflict.path, ConflictResolution.MANUAL
                            )
                            resolved.append(conflict)
                    else:
                        # No conflict handler - use default strategy (most recent wins)
                        resolved.extend(unresolved)

                # Apply resolutions
                for conflict in resolved:
                    resolution = conflict.get_suggested_resolution()
                    status = self._apply_resolution(conflict, resolution)
                    results[conflict.path] = status
                    if status in ("kept_local", "pushed"):
                        pushed_count += 1
                    elif status in ("kept_remote", "pulled"):
                        pulled_count += 1

            # Sync files without conflicts
            all_paths = set(local_files.keys()) | set(remote_files.keys())
            conflict_paths = {c.path for c in conflicts}

            for path in all_paths:
                if path in conflict_paths:
                    continue  # Already handled

                local_data = local_files.get(path)
                remote_data = remote_files.get(path)

                if local_data and remote_data:
                    # Both exist and match - no action needed
                    continue
                elif local_data and not remote_data:
                    # Local only - push to remote
                    content, _ = local_data
                    try:
                        self.github.create_or_update_file(
                            path=path,
                            content=content,
                            message=f"Create {path} from local",
                        )
                        results[path] = "pushed"
                        pushed_count += 1
                        logger.info(f"Sync: Pushed {path}")
                    except GitHubAPIError as e:
                        logger.error(f"Sync: Failed to push {path}: {e}")
                        results[path] = f"error: {e}"
                elif remote_data and not local_data:
                    # Remote only - pull to local
                    content, _ = remote_data
                    try:
                        local_file = self.local_path / path
                        local_file.parent.mkdir(parents=True, exist_ok=True)
                        local_file.write_text(content, encoding="utf-8")
                        results[path] = "pulled"
                        pulled_count += 1
                        logger.info(f"Sync: Pulled {path}")
                    except Exception as e:
                        logger.error(f"Sync: Failed to pull {path}: {e}")
                        results[path] = f"error: {e}"

            self.last_sync = datetime.now()
            self.resolver.clear_conflicts()

            logger.info(f"Sync complete: pushed={pushed_count}, pulled={pulled_count}")

            return {
                "success": True,
                "pushed": pushed_count,
                "pulled": pulled_count,
                "files": results,
            }

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "pushed": 0,
                "pulled": 0,
                "files": {},
            }

        finally:
            self.is_syncing = False

    def _apply_resolution(
        self, conflict: FileConflict, resolution: ConflictResolution
    ) -> str:
        """Apply a conflict resolution.

        Args:
            conflict: The conflict to resolve
            resolution: Resolution strategy

        Returns:
            Status string describing the action taken
        """
        # For MANUAL resolution without a handler, default to keeping local
        # This is safer than throwing an error
        if resolution == ConflictResolution.MANUAL:
            logger.warning(
                f"Manual resolution requested for {conflict.path}, defaulting to keep local"
            )
            resolution = ConflictResolution.KEEP_LOCAL

        content = self.resolver.resolve_conflict(conflict, resolution)

        if resolution == ConflictResolution.KEEP_LOCAL:
            # Push local to remote
            if conflict.local_content:
                remote_data = self.github.get_file_content(conflict.path)
                sha = remote_data[1] if remote_data else None
                self.github.create_or_update_file(
                    path=conflict.path,
                    content=conflict.local_content,
                    message=f"Resolve conflict: keep local version of {conflict.path}",
                    sha=sha,
                )
                return "kept_local"
            else:
                # Local deleted - delete remote
                remote_data = self.github.get_file_content(conflict.path)
                if remote_data:
                    _, sha = remote_data
                    self.github.delete_file(
                        path=conflict.path,
                        message=f"Resolve conflict: delete {conflict.path}",
                        sha=sha,
                    )
                return "deleted"

        elif resolution == ConflictResolution.KEEP_REMOTE:
            # Pull remote to local
            if conflict.remote_content:
                local_file = self.local_path / conflict.path
                local_file.parent.mkdir(parents=True, exist_ok=True)
                local_file.write_text(conflict.remote_content, encoding="utf-8")
                return "kept_remote"
            else:
                # Remote deleted - delete local
                local_file = self.local_path / conflict.path
                if local_file.exists():
                    local_file.unlink()
                return "deleted"

        elif resolution == ConflictResolution.KEEP_BOTH:
            # Write merged content to both sides
            if content:
                local_file = self.local_path / conflict.path
                local_file.write_text(content, encoding="utf-8")

                remote_data = self.github.get_file_content(conflict.path)
                sha = remote_data[1] if remote_data else None
                self.github.create_or_update_file(
                    path=conflict.path,
                    content=content,
                    message=f"Resolve conflict: merge both versions of {conflict.path}",
                    sha=sha,
                )
                return "merged"

        return "unresolved"

    def _get_local_files(self) -> dict[str, tuple[str, datetime]]:
        """Get all local Espanso config files.

        Returns:
            Dict of {relative_path: (content, modified_time)}
        """
        files = {}

        # Scan config and match directories
        for dir_name in ["config", "match"]:
            dir_path = self.local_path / dir_name
            if not dir_path.exists():
                continue

            for file_path in dir_path.glob("*.yml"):
                rel_path = f"{dir_name}/{file_path.name}"
                content = file_path.read_text(encoding="utf-8")
                modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                files[rel_path] = (content, modified)

        return files

    def _get_remote_files(self) -> dict[str, tuple[str, datetime]]:
        """Get all remote Espanso config files from GitHub.

        Returns:
            Dict of {relative_path: (content, modified_time)}
        """
        files = {}

        # Scan config and match directories
        for dir_name in ["config", "match"]:
            try:
                dir_contents = self.github.get_directory_contents(dir_name)

                for item in dir_contents:
                    if item["type"] == "file" and item["name"].endswith(".yml"):
                        rel_path = f"{dir_name}/{item['name']}"

                        # Get file content
                        result = self.github.get_file_content(rel_path)
                        if result:
                            content, _ = result

                            # Get last modified time
                            modified = self.github.get_file_last_modified(rel_path)
                            if modified:
                                files[rel_path] = (content, modified)

            except GitHubAPIError:
                # Directory might not exist yet
                continue

        return files

    def start_auto_sync(self, interval: int = 300):
        """Start automatic sync timer.

        Args:
            interval: Sync interval in seconds (default: 300 = 5 minutes)
        """
        self._sync_interval = interval
        self._auto_sync_enabled = True
        self._schedule_next_sync()

    def stop_auto_sync(self):
        """Stop automatic sync timer."""
        self._auto_sync_enabled = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _schedule_next_sync(self):
        """Schedule the next auto-sync."""
        if not self._auto_sync_enabled:
            return

        def auto_sync():
            if self._auto_sync_enabled:
                try:
                    self.sync()
                    logger.info("Auto-sync completed successfully")
                except Exception as e:
                    logger.error(f"Auto-sync failed: {e}")
                finally:
                    self._schedule_next_sync()

        self._timer = threading.Timer(self._sync_interval, auto_sync)
        self._timer.daemon = True
        self._timer.start()

    def close(self):
        """Clean up resources."""
        self.stop_auto_sync()
        self.github.close()
