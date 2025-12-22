"""Data models for Espanded."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class Entry:
    """Represents a single Espanso text expansion entry."""

    id: str = ""
    trigger: str = ""
    prefix: str = ":"
    replacement: str = ""
    tags: list[str] = field(default_factory=list)

    # Trigger Options
    word: bool = True
    propagate_case: bool = False
    uppercase_style: str = "capitalize"  # capitalize, uppercase, none

    # Matching Options
    regex: bool = False
    case_insensitive: bool = False

    # Behavior Options
    force_clipboard: bool = False
    passive: bool = False
    markdown: bool = False
    cursor_hint: str | None = None

    # App Filtering
    filter_apps: list[str] | None = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    deleted_at: datetime | None = None
    source_file: str = "base.yml"

    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            self.id = str(uuid4())

    @property
    def full_trigger(self) -> str:
        """Get the full trigger including prefix."""
        return f"{self.prefix}{self.trigger}"

    @property
    def is_deleted(self) -> bool:
        """Check if entry is soft-deleted."""
        return self.deleted_at is not None

    def to_espanso_dict(self) -> dict[str, Any]:
        """Convert to Espanso YAML format."""
        entry: dict[str, Any] = {
            "trigger": self.full_trigger,
            "replace": self.replacement,
        }

        # Add optional fields only if they differ from defaults
        if not self.word:
            entry["word"] = False

        if self.propagate_case:
            entry["propagate_case"] = True

        if self.uppercase_style != "capitalize":
            entry["uppercase_style"] = self.uppercase_style

        if self.regex:
            entry["regex"] = True

        if self.case_insensitive:
            entry["case_insensitive"] = True

        if self.force_clipboard:
            entry["force_clipboard"] = True

        if self.passive:
            entry["passive_only"] = True

        if self.markdown:
            entry["markdown"] = True

        if self.cursor_hint:
            entry["cursor_hint"] = self.cursor_hint

        if self.filter_apps:
            entry["filter_apps"] = self.filter_apps

        return entry

    @classmethod
    def from_espanso_dict(
        cls,
        data: dict[str, Any],
        source_file: str = "base.yml",
        entry_id: str | None = None,
    ) -> "Entry":
        """Create Entry from Espanso YAML data."""
        trigger = data.get("trigger", "")
        prefix = ""
        trigger_text = trigger

        # Extract prefix from trigger
        for p in ["//", "::", ":", ";"]:
            if trigger.startswith(p):
                prefix = p
                trigger_text = trigger[len(p):]
                break

        return cls(
            id=entry_id or str(uuid4()),
            trigger=trigger_text,
            prefix=prefix,
            replacement=data.get("replace", ""),
            tags=[],  # Tags are stored separately in our metadata
            word=data.get("word", True),
            propagate_case=data.get("propagate_case", False),
            uppercase_style=data.get("uppercase_style", "capitalize"),
            regex=data.get("regex", False),
            case_insensitive=data.get("case_insensitive", False),
            force_clipboard=data.get("force_clipboard", False),
            passive=data.get("passive_only", False),
            markdown=data.get("markdown", False),
            cursor_hint=data.get("cursor_hint"),
            filter_apps=data.get("filter_apps"),
            source_file=source_file,
        )


@dataclass
class Settings:
    """Application settings."""

    # GitHub Sync
    github_repo: str | None = None
    github_token: str | None = None
    auto_sync: bool = True
    sync_interval: int = 10800  # seconds (3 hours)

    # UI Preferences
    default_prefix: str = ":"
    theme: str = "system"  # light, dark, system
    custom_colors: dict[str, str] = field(default_factory=dict)

    # Hotkeys (using 'e' - backtick has issues on Windows with pynput)
    quick_add_hotkey: str = "<ctrl>+<alt>+e"
    hotkeys_enabled: bool = True
    minimize_to_tray: bool = True

    # Autocomplete (inline suggestions while typing)
    autocomplete_enabled: bool = True
    autocomplete_triggers: list[str] = field(default_factory=lambda: [":"])
    autocomplete_min_chars: int = 0  # chars after trigger before showing popup
    autocomplete_max_suggestions: int = 8
    autocomplete_show_delay_ms: int = 100  # delay before showing popup

    # Espanso Integration
    espanso_config_path: str = ""

    # First Run
    has_imported: bool = False
    last_sync: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary for storage."""
        return {
            "github_repo": self.github_repo,
            "github_token": self.github_token,
            "auto_sync": self.auto_sync,
            "sync_interval": self.sync_interval,
            "default_prefix": self.default_prefix,
            "theme": self.theme,
            "custom_colors": self.custom_colors,
            "quick_add_hotkey": self.quick_add_hotkey,
            "hotkeys_enabled": self.hotkeys_enabled,
            "minimize_to_tray": self.minimize_to_tray,
            "autocomplete_enabled": self.autocomplete_enabled,
            "autocomplete_triggers": self.autocomplete_triggers,
            "autocomplete_min_chars": self.autocomplete_min_chars,
            "autocomplete_max_suggestions": self.autocomplete_max_suggestions,
            "autocomplete_show_delay_ms": self.autocomplete_show_delay_ms,
            "espanso_config_path": self.espanso_config_path,
            "has_imported": self.has_imported,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Settings":
        """Create Settings from dictionary."""
        last_sync = data.get("last_sync")
        if last_sync and isinstance(last_sync, str):
            last_sync = datetime.fromisoformat(last_sync)

        return cls(
            github_repo=data.get("github_repo"),
            github_token=data.get("github_token"),
            auto_sync=data.get("auto_sync", True),
            sync_interval=data.get("sync_interval", 10800),
            default_prefix=data.get("default_prefix", ":"),
            theme=data.get("theme", "system"),
            custom_colors=data.get("custom_colors", {}),
            quick_add_hotkey=data.get("quick_add_hotkey", "<ctrl>+<alt>+e"),
            hotkeys_enabled=data.get("hotkeys_enabled", True),
            minimize_to_tray=data.get("minimize_to_tray", True),
            autocomplete_enabled=data.get("autocomplete_enabled", True),
            autocomplete_triggers=data.get("autocomplete_triggers", [":"]),
            autocomplete_min_chars=data.get("autocomplete_min_chars", 0),
            autocomplete_max_suggestions=data.get("autocomplete_max_suggestions", 8),
            autocomplete_show_delay_ms=data.get("autocomplete_show_delay_ms", 100),
            espanso_config_path=data.get("espanso_config_path", ""),
            has_imported=data.get("has_imported", False),
            last_sync=last_sync,
        )


@dataclass
class HistoryEntry:
    """Represents a change history entry."""

    id: str = ""
    entry_id: str = ""
    action: str = ""  # "created", "modified", "deleted", "restored"
    timestamp: datetime = field(default_factory=datetime.now)
    changes: dict[str, Any] = field(default_factory=dict)  # old_value, new_value pairs
    trigger_name: str = ""  # For display purposes

    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            self.id = str(uuid4())
