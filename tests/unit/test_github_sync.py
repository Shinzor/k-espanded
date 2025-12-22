"""Tests for GitHub sync functionality."""

import base64
import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

from espanded.sync.github_sync import GitHubSync, GitHubAPIError


@pytest.fixture
def github_sync():
    """Create a GitHubSync instance with mocked httpx."""
    with patch("espanded.sync.github_sync.HTTPX_AVAILABLE", True):
        sync = GitHubSync(repo="user/test-repo", token="test_token")
        yield sync
        sync.close()


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"status": "ok"}
    response.text = "OK"
    return response


class TestGitHubSync:
    """Tests for GitHubSync class."""

    def test_initialization(self):
        """Test GitHubSync initialization."""
        with patch("espanded.sync.github_sync.HTTPX_AVAILABLE", True):
            sync = GitHubSync(repo="user/repo", token="token123")
            assert sync.repo == "user/repo"
            assert sync.token == "token123"
            sync.close()

    def test_initialization_without_httpx(self):
        """Test GitHubSync raises error when httpx not available."""
        with patch("espanded.sync.github_sync.HTTPX_AVAILABLE", False):
            with pytest.raises(ImportError):
                GitHubSync(repo="user/repo", token="token123")

    def test_client_property(self, github_sync):
        """Test client property creates httpx client."""
        with patch("espanded.sync.github_sync.httpx.Client") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            client = github_sync.client

            MockClient.assert_called_once()
            assert github_sync._client == mock_client

    def test_close(self, github_sync):
        """Test closing the HTTP client."""
        mock_client = MagicMock()
        github_sync._client = mock_client

        github_sync.close()

        mock_client.close.assert_called_once()
        assert github_sync._client is None

    def test_context_manager(self):
        """Test GitHubSync as context manager."""
        with patch("espanded.sync.github_sync.HTTPX_AVAILABLE", True):
            with patch("espanded.sync.github_sync.httpx.Client"):
                with GitHubSync(repo="user/repo", token="token") as sync:
                    assert sync is not None

    def test_test_connection_success(self, github_sync, mock_response):
        """Test successful connection test."""
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.test_connection()

        assert result is True
        mock_client.get.assert_called_once()

    def test_test_connection_failure(self, github_sync):
        """Test failed connection test."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.test_connection()

        assert result is False

    def test_test_connection_exception(self, github_sync):
        """Test connection test with exception."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Network error")
        github_sync._client = mock_client

        result = github_sync.test_connection()

        assert result is False

    def test_get_file_content_success(self, github_sync):
        """Test getting file content successfully."""
        content = "Hello, World!"
        encoded_content = base64.b64encode(content.encode()).decode()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "sha": "abc123",
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.get_file_content("test.txt")

        assert result is not None
        content_result, sha = result
        assert content_result == "Hello, World!"
        assert sha == "abc123"

    def test_get_file_content_not_found(self, github_sync):
        """Test getting file content when file doesn't exist."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.get_file_content("nonexistent.txt")

        assert result is None

    def test_get_file_content_error(self, github_sync):
        """Test getting file content with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        with pytest.raises(GitHubAPIError):
            github_sync.get_file_content("test.txt")

    def test_create_or_update_file_create(self, github_sync):
        """Test creating a new file."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"commit": {"sha": "new123"}}

        mock_client = MagicMock()
        mock_client.put.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.create_or_update_file(
            path="new.txt",
            content="New content",
            message="Create new file",
            sha=None,
        )

        assert result["commit"]["sha"] == "new123"
        mock_client.put.assert_called_once()

    def test_create_or_update_file_update(self, github_sync):
        """Test updating an existing file."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"commit": {"sha": "updated123"}}

        mock_client = MagicMock()
        mock_client.put.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.create_or_update_file(
            path="existing.txt",
            content="Updated content",
            message="Update file",
            sha="old123",
        )

        assert result["commit"]["sha"] == "updated123"

    def test_create_or_update_file_error(self, github_sync):
        """Test error when creating/updating file."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"

        mock_client = MagicMock()
        mock_client.put.return_value = mock_response
        github_sync._client = mock_client

        with pytest.raises(GitHubAPIError):
            github_sync.create_or_update_file(
                path="test.txt",
                content="Content",
                message="Message",
            )

    def test_delete_file_success(self, github_sync):
        """Test deleting a file successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"commit": {"sha": "delete123"}}

        mock_client = MagicMock()
        mock_client.delete.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.delete_file(
            path="test.txt",
            message="Delete file",
            sha="file123",
        )

        assert result["commit"]["sha"] == "delete123"

    def test_delete_file_error(self, github_sync):
        """Test error when deleting file."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        mock_client = MagicMock()
        mock_client.delete.return_value = mock_response
        github_sync._client = mock_client

        with pytest.raises(GitHubAPIError):
            github_sync.delete_file(
                path="test.txt",
                message="Delete",
                sha="file123",
            )

    def test_get_directory_contents(self, github_sync):
        """Test getting directory contents."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "file1.txt", "type": "file"},
            {"name": "file2.txt", "type": "file"},
            {"name": "subdir", "type": "dir"},
        ]

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.get_directory_contents("match")

        assert len(result) == 3
        assert result[0]["name"] == "file1.txt"

    def test_get_directory_contents_not_found(self, github_sync):
        """Test getting contents of non-existent directory."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.get_directory_contents("nonexistent")

        assert result == []

    def test_get_latest_commit(self, github_sync):
        """Test getting latest commit."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sha": "commit123",
            "commit": {"message": "Latest commit"},
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.get_latest_commit()

        assert result is not None
        assert result["sha"] == "commit123"

    def test_get_latest_commit_not_found(self, github_sync):
        """Test getting latest commit when branch doesn't exist."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.get_latest_commit("nonexistent-branch")

        assert result is None

    def test_create_repository(self, github_sync):
        """Test creating a new repository."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "name": "new-repo",
            "full_name": "user/new-repo",
            "private": True,
        }

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.create_repository(
            name="new-repo",
            description="Test repo",
            private=True,
        )

        assert result["name"] == "new-repo"
        assert result["private"] is True

    def test_get_repository_info(self, github_sync):
        """Test getting repository information."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-repo",
            "full_name": "user/test-repo",
            "description": "Test repository",
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.get_repository_info()

        assert result["name"] == "test-repo"

    def test_get_file_last_modified(self, github_sync):
        """Test getting file last modified timestamp."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "commit": {
                    "committer": {
                        "date": "2024-01-15T12:00:00Z"
                    }
                }
            }
        ]

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.get_file_last_modified("test.txt")

        assert result is not None
        assert isinstance(result, datetime)

    def test_get_file_last_modified_not_found(self, github_sync):
        """Test getting last modified for non-existent file."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        github_sync._client = mock_client

        result = github_sync.get_file_last_modified("nonexistent.txt")

        assert result is None
