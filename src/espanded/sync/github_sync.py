"""GitHub API operations for syncing Espanso configurations."""

import base64
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    if not TYPE_CHECKING:
        # Create a dummy httpx module for type hints when not available
        class _DummyClient:
            pass
        class httpx:  # noqa: N801
            Client = _DummyClient


class GitHubAPIError(Exception):
    """Exception raised for GitHub API errors."""
    pass


class GitHubSync:
    """Handles GitHub API operations for repository sync."""

    API_BASE = "https://api.github.com"

    def __init__(self, repo: str, token: str):
        """Initialize GitHub sync.

        Args:
            repo: Repository in format "owner/repo"
            token: GitHub Personal Access Token (fine-grained)
        """
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for GitHub sync. Install with: pip install httpx"
            )

        self.repo = repo
        self.token = token
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30.0,
            )
        return self._client

    def close(self):
        """Close HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def test_connection(self) -> bool:
        """Test if connection to GitHub is working.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.client.get(f"{self.API_BASE}/repos/{self.repo}")
            return response.status_code == 200
        except Exception:
            return False

    def get_file_content(self, path: str, ref: str = "main") -> tuple[str, str] | None:
        """Get file content from repository.

        Args:
            path: File path in repository
            ref: Git reference (branch, tag, commit SHA)

        Returns:
            Tuple of (content, sha) or None if file not found
        """
        url = f"{self.API_BASE}/repos/{self.repo}/contents/{path}"
        params = {"ref": ref}

        try:
            response = self.client.get(url, params=params)

            if response.status_code == 404:
                return None

            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to get file {path}: {response.status_code} - {response.text}"
                )

            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content, data["sha"]

        except httpx.HTTPError as e:
            raise GitHubAPIError(f"HTTP error getting file {path}: {e}")

    def create_or_update_file(
        self,
        path: str,
        content: str,
        message: str,
        sha: str | None = None,
        branch: str = "main",
    ) -> dict[str, Any]:
        """Create or update a file in the repository.

        Args:
            path: File path in repository
            content: File content (will be base64 encoded)
            message: Commit message
            sha: File SHA (required for updates, None for creates)
            branch: Branch to commit to

        Returns:
            Response data with commit info
        """
        url = f"{self.API_BASE}/repos/{self.repo}/contents/{path}"

        # Encode content to base64
        content_bytes = content.encode("utf-8")
        encoded_content = base64.b64encode(content_bytes).decode("utf-8")

        data: dict[str, Any] = {
            "message": message,
            "content": encoded_content,
            "branch": branch,
        }

        if sha:
            data["sha"] = sha

        try:
            response = self.client.put(url, json=data)

            if response.status_code not in (200, 201):
                raise GitHubAPIError(
                    f"Failed to update file {path}: {response.status_code} - {response.text}"
                )

            return response.json()

        except httpx.HTTPError as e:
            raise GitHubAPIError(f"HTTP error updating file {path}: {e}")

    def delete_file(
        self,
        path: str,
        message: str,
        sha: str,
        branch: str = "main",
    ) -> dict[str, Any]:
        """Delete a file from the repository.

        Args:
            path: File path in repository
            message: Commit message
            sha: File SHA (required)
            branch: Branch to commit to

        Returns:
            Response data with commit info
        """
        url = f"{self.API_BASE}/repos/{self.repo}/contents/{path}"

        data = {
            "message": message,
            "sha": sha,
            "branch": branch,
        }

        try:
            response = self.client.delete(url, json=data)

            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to delete file {path}: {response.status_code} - {response.text}"
                )

            return response.json()

        except httpx.HTTPError as e:
            raise GitHubAPIError(f"HTTP error deleting file {path}: {e}")

    def get_directory_contents(
        self, path: str = "", ref: str = "main"
    ) -> list[dict[str, Any]]:
        """Get directory contents from repository.

        Args:
            path: Directory path in repository (empty for root)
            ref: Git reference (branch, tag, commit SHA)

        Returns:
            List of file/directory objects
        """
        url = f"{self.API_BASE}/repos/{self.repo}/contents/{path}"
        params = {"ref": ref}

        try:
            response = self.client.get(url, params=params)

            if response.status_code == 404:
                return []

            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to get directory {path}: {response.status_code} - {response.text}"
                )

            return response.json()

        except httpx.HTTPError as e:
            raise GitHubAPIError(f"HTTP error getting directory {path}: {e}")

    def get_latest_commit(self, branch: str = "main") -> dict[str, Any] | None:
        """Get the latest commit on a branch.

        Args:
            branch: Branch name

        Returns:
            Commit data or None if branch not found
        """
        url = f"{self.API_BASE}/repos/{self.repo}/commits/{branch}"

        try:
            response = self.client.get(url)

            if response.status_code == 404:
                return None

            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to get latest commit: {response.status_code} - {response.text}"
                )

            return response.json()

        except httpx.HTTPError as e:
            raise GitHubAPIError(f"HTTP error getting latest commit: {e}")

    def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = True,
    ) -> dict[str, Any]:
        """Create a new repository.

        Args:
            name: Repository name
            description: Repository description
            private: Whether repository should be private

        Returns:
            Repository data
        """
        url = f"{self.API_BASE}/user/repos"

        data = {
            "name": name,
            "description": description or "Espanded configuration sync",
            "private": private,
            "auto_init": True,  # Initialize with README
        }

        try:
            response = self.client.post(url, json=data)

            if response.status_code != 201:
                raise GitHubAPIError(
                    f"Failed to create repository: {response.status_code} - {response.text}"
                )

            return response.json()

        except httpx.HTTPError as e:
            raise GitHubAPIError(f"HTTP error creating repository: {e}")

    def get_repository_info(self) -> dict[str, Any]:
        """Get repository information.

        Returns:
            Repository data
        """
        url = f"{self.API_BASE}/repos/{self.repo}"

        try:
            response = self.client.get(url)

            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to get repository info: {response.status_code} - {response.text}"
                )

            return response.json()

        except httpx.HTTPError as e:
            raise GitHubAPIError(f"HTTP error getting repository info: {e}")

    def get_file_last_modified(self, path: str, branch: str = "main") -> datetime | None:
        """Get the last modified timestamp for a file.

        Args:
            path: File path in repository
            branch: Branch name

        Returns:
            Last modified datetime or None if file not found
        """
        url = f"{self.API_BASE}/repos/{self.repo}/commits"
        params = {"path": path, "sha": branch, "per_page": 1}

        try:
            response = self.client.get(url, params=params)

            if response.status_code != 200:
                return None

            commits = response.json()
            if not commits:
                return None

            commit_date = commits[0]["commit"]["committer"]["date"]
            return datetime.fromisoformat(commit_date.replace("Z", "+00:00"))

        except (httpx.HTTPError, KeyError, ValueError):
            return None
