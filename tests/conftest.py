"""Pytest configuration and common fixtures."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from espanded.core.models import Entry, Settings, HistoryEntry
from espanded.core.database import Database
from espanded.core.entry_manager import EntryManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_entry():
    """Create a sample entry for testing."""
    return Entry(
        id="test-id-1",
        trigger="test",
        prefix=":",
        replacement="Test replacement text",
        tags=["work", "template"],
        word=True,
        propagate_case=False,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        modified_at=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def sample_entries():
    """Create multiple sample entries for testing."""
    return [
        Entry(
            id="entry-1",
            trigger="sig",
            prefix=":",
            replacement="Best regards,\nZeel",
            tags=["email", "signature"],
        ),
        Entry(
            id="entry-2",
            trigger="addr",
            prefix=":",
            replacement="123 Main St, City, State 12345",
            tags=["personal", "address"],
        ),
        Entry(
            id="entry-3",
            trigger="meeting",
            prefix="::",
            replacement="Meeting scheduled for...",
            tags=["work", "template"],
        ),
    ]


@pytest.fixture
def sample_settings():
    """Create sample settings for testing."""
    return Settings(
        github_repo="user/espanso-config",
        github_token="test_token_123",
        auto_sync=True,
        sync_interval=300,
        default_prefix=":",
        theme="dark",
        quick_add_hotkey="ctrl+shift+e",
        espanso_config_path="/home/user/.config/espanso",
        has_imported=True,
    )


@pytest.fixture
def test_database(temp_dir):
    """Create a test database instance."""
    db_path = temp_dir / "test.db"
    db = Database(str(db_path))
    yield db
    db.close()


@pytest.fixture
def entry_manager(test_database):
    """Create a test entry manager with mocked Espanso."""
    # Mock EspansoManager to avoid file system operations
    mock_espanso = MagicMock()
    mock_espanso.exists.return_value = False

    manager = EntryManager(database=test_database, espanso=mock_espanso)
    return manager


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub HTTP client."""
    mock_client = MagicMock()

    # Mock successful responses
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "test-repo",
        "full_name": "user/test-repo",
        "private": True,
    }

    mock_client.get.return_value = mock_response
    mock_client.put.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.delete.return_value = mock_response

    return mock_client


@pytest.fixture
def sample_history_entry():
    """Create a sample history entry for testing."""
    return HistoryEntry(
        id="history-1",
        entry_id="entry-1",
        action="created",
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        trigger_name=":test",
        changes={},
    )


@pytest.fixture
def espanso_yaml_data():
    """Sample Espanso YAML data for testing."""
    return {
        "matches": [
            {
                "trigger": ":sig",
                "replace": "Best regards,\nZeel",
            },
            {
                "trigger": "::meeting",
                "replace": "Meeting scheduled for...",
                "word": False,
            },
            {
                "trigger": ":addr",
                "replace": "123 Main St",
                "propagate_case": True,
            },
        ]
    }


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client for GitHub API testing."""
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    return mock
