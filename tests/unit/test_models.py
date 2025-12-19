"""Tests for data models."""

import pytest
from datetime import datetime

from espanded.core.models import Entry, Settings, HistoryEntry


class TestEntry:
    """Tests for Entry model."""

    def test_entry_creation_with_defaults(self):
        """Test creating an entry with default values."""
        entry = Entry(trigger="test", replacement="Test replacement")

        assert entry.trigger == "test"
        assert entry.replacement == "Test replacement"
        assert entry.prefix == ":"
        assert entry.word is True
        assert entry.id != ""  # Auto-generated

    def test_full_trigger(self):
        """Test full_trigger property."""
        entry = Entry(trigger="sig", prefix=":", replacement="Signature")
        assert entry.full_trigger == ":sig"

        entry2 = Entry(trigger="test", prefix="", replacement="Test")
        assert entry2.full_trigger == "test"

    def test_to_espanso_dict(self):
        """Test conversion to Espanso YAML format."""
        entry = Entry(
            trigger="sig",
            prefix=":",
            replacement="Best regards,\nZeel",
            word=True,
            propagate_case=True,
        )

        result = entry.to_espanso_dict()

        assert result["trigger"] == ":sig"
        assert result["replace"] == "Best regards,\nZeel"
        assert result["propagate_case"] is True
        assert "word" not in result  # word=True is default, not included

    def test_from_espanso_dict(self):
        """Test creation from Espanso YAML data."""
        data = {
            "trigger": ":sig",
            "replace": "Best regards",
            "word": False,
            "propagate_case": True,
        }

        entry = Entry.from_espanso_dict(data)

        assert entry.trigger == "sig"
        assert entry.prefix == ":"
        assert entry.replacement == "Best regards"
        assert entry.word is False
        assert entry.propagate_case is True

    def test_soft_delete(self):
        """Test soft delete functionality."""
        entry = Entry(trigger="test", replacement="Test")
        assert entry.is_deleted is False

        entry.deleted_at = datetime.now()
        assert entry.is_deleted is True


class TestSettings:
    """Tests for Settings model."""

    def test_settings_defaults(self):
        """Test settings with default values."""
        settings = Settings()

        assert settings.theme == "system"
        assert settings.default_prefix == ":"
        assert settings.auto_sync is True
        assert settings.github_repo is None

    def test_settings_to_dict(self):
        """Test conversion to dictionary."""
        settings = Settings(theme="dark", default_prefix=";")
        result = settings.to_dict()

        assert result["theme"] == "dark"
        assert result["default_prefix"] == ";"

    def test_settings_from_dict(self):
        """Test creation from dictionary."""
        data = {"theme": "light", "github_repo": "user/repo"}
        settings = Settings.from_dict(data)

        assert settings.theme == "light"
        assert settings.github_repo == "user/repo"


class TestHistoryEntry:
    """Tests for HistoryEntry model."""

    def test_history_entry_creation(self):
        """Test creating a history entry."""
        history = HistoryEntry(
            entry_id="123",
            action="created",
            trigger_name=":test",
        )

        assert history.entry_id == "123"
        assert history.action == "created"
        assert history.trigger_name == ":test"
        assert history.id != ""  # Auto-generated
