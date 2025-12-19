"""Espanso default.yml configuration management."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


# Toggle key options
TOGGLE_KEY_OPTIONS = [
    ("OFF", "Off (disabled)"),
    ("CTRL", "Ctrl"),
    ("ALT", "Alt"),
    ("SHIFT", "Shift"),
    ("META", "Meta/Win/Cmd"),
    ("LEFT_CTRL", "Left Ctrl"),
    ("RIGHT_CTRL", "Right Ctrl"),
    ("LEFT_ALT", "Left Alt"),
    ("RIGHT_ALT", "Right Alt"),
    ("LEFT_SHIFT", "Left Shift"),
    ("RIGHT_SHIFT", "Right Shift"),
    ("LEFT_META", "Left Meta"),
    ("RIGHT_META", "Right Meta"),
]

# Backend options
BACKEND_OPTIONS = [
    ("Auto", "Auto (recommended)"),
    ("Clipboard", "Clipboard"),
    ("Inject", "Inject"),
]


@dataclass
class EspansoConfig:
    """Espanso default.yml configuration options."""

    # === Global Options (default.yml only) ===

    # Auto-restart worker on config change
    auto_restart: bool = True

    # Backspace tracking limit for corrections
    backspace_limit: int = 5

    # Preserve clipboard content after expansion
    preserve_clipboard: bool = True

    # Search UI hotkey
    search_shortcut: str = "ALT+SPACE"

    # Search trigger keyword (off = disabled)
    search_trigger: str = "off"

    # Show icon in system tray
    show_icon: bool = True

    # Show expansion notifications
    show_notifications: bool = True

    # Toggle key for enable/disable
    toggle_key: str = "OFF"

    # Undo expansion with backspace
    undo_backspace: bool = True

    # Windows: exclude orphan keyboard events
    win32_exclude_orphan_events: bool = True

    # Windows: keyboard layout cache interval (ms)
    win32_keyboard_layout_cache_interval: int = 2000

    # === App-Specific Options (can be in default.yml) ===

    # Injection backend
    backend: str = "Auto"

    # Character threshold for clipboard backend
    clipboard_threshold: int = 100

    # Enable espanso
    enable: bool = True

    # Delay between injection events (ms)
    inject_delay: int = 0

    # Delay between key events (ms)
    key_delay: int = 0

    # Paste keyboard shortcut
    paste_shortcut: str = "CTRL+V"

    # Delay before paste (ms)
    pre_paste_delay: int = 300

    # Delay before restoring clipboard (ms)
    restore_clipboard_delay: int = 300

    # Delay after forms close (ms)
    post_form_delay: int = 200

    # Delay after search closes (ms)
    post_search_delay: int = 200

    # Delay between paste keystrokes (ms)
    paste_shortcut_event_delay: int = 10

    # Maximum form dimensions
    max_form_width: int = 700
    max_form_height: int = 500

    # Apply built-in patches
    apply_patch: bool = True

    # Word separators (stored as list)
    word_separators: list[str] = field(default_factory=lambda: [
        " ", ",", ".", "?", "!", "@", "#", "$", "%", "^", "&", "*",
        "(", ")", "[", "]", "{", "}", "<", ">", "/", "\\", "|", "-",
        "_", "+", "=", ";", ":", "'", '"', "`", "~", "\n", "\t", "\r"
    ])


class EspansoConfigHandler:
    """Handler for reading and writing Espanso default.yml configuration."""

    def __init__(self, espanso_config_path: str | Path):
        """Initialize with path to Espanso config directory."""
        self.config_dir = Path(espanso_config_path) / "config"
        self.default_yml_path = self.config_dir / "default.yml"
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)

    def load(self) -> EspansoConfig:
        """Load configuration from default.yml."""
        config = EspansoConfig()

        if not self.default_yml_path.exists():
            return config

        try:
            with open(self.default_yml_path, "r", encoding="utf-8") as f:
                data = self.yaml.load(f) or {}

            # Map YAML keys to config attributes
            mapping = {
                "auto_restart": "auto_restart",
                "backspace_limit": "backspace_limit",
                "preserve_clipboard": "preserve_clipboard",
                "search_shortcut": "search_shortcut",
                "search_trigger": "search_trigger",
                "show_icon": "show_icon",
                "show_notifications": "show_notifications",
                "toggle_key": "toggle_key",
                "undo_backspace": "undo_backspace",
                "win32_exclude_orphan_events": "win32_exclude_orphan_events",
                "win32_keyboard_layout_cache_interval": "win32_keyboard_layout_cache_interval",
                "backend": "backend",
                "clipboard_threshold": "clipboard_threshold",
                "enable": "enable",
                "inject_delay": "inject_delay",
                "key_delay": "key_delay",
                "paste_shortcut": "paste_shortcut",
                "pre_paste_delay": "pre_paste_delay",
                "restore_clipboard_delay": "restore_clipboard_delay",
                "post_form_delay": "post_form_delay",
                "post_search_delay": "post_search_delay",
                "paste_shortcut_event_delay": "paste_shortcut_event_delay",
                "max_form_width": "max_form_width",
                "max_form_height": "max_form_height",
                "apply_patch": "apply_patch",
                "word_separators": "word_separators",
            }

            for yaml_key, attr_name in mapping.items():
                if yaml_key in data:
                    value = data[yaml_key]
                    # Handle backend capitalization
                    if attr_name == "backend" and isinstance(value, str):
                        value = value.capitalize()
                    setattr(config, attr_name, value)

        except Exception as e:
            print(f"Error loading Espanso config: {e}")

        return config

    def save(self, config: EspansoConfig) -> bool:
        """Save configuration to default.yml."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Load existing data to preserve unknown keys
            existing_data: dict[str, Any] = {}
            if self.default_yml_path.exists():
                with open(self.default_yml_path, "r", encoding="utf-8") as f:
                    existing_data = self.yaml.load(f) or {}

            # Update with our config values
            data = existing_data.copy()

            # Only write non-default values to keep file clean
            defaults = EspansoConfig()

            def set_if_changed(key: str, value: Any, default: Any):
                if value != default:
                    data[key] = value
                elif key in data:
                    # Remove if set back to default
                    del data[key]

            # Global options
            set_if_changed("auto_restart", config.auto_restart, defaults.auto_restart)
            set_if_changed("backspace_limit", config.backspace_limit, defaults.backspace_limit)
            set_if_changed("preserve_clipboard", config.preserve_clipboard, defaults.preserve_clipboard)
            set_if_changed("search_shortcut", config.search_shortcut, defaults.search_shortcut)
            set_if_changed("search_trigger", config.search_trigger, defaults.search_trigger)
            set_if_changed("show_icon", config.show_icon, defaults.show_icon)
            set_if_changed("show_notifications", config.show_notifications, defaults.show_notifications)
            set_if_changed("toggle_key", config.toggle_key, defaults.toggle_key)
            set_if_changed("undo_backspace", config.undo_backspace, defaults.undo_backspace)
            set_if_changed("win32_exclude_orphan_events", config.win32_exclude_orphan_events, defaults.win32_exclude_orphan_events)
            set_if_changed("win32_keyboard_layout_cache_interval", config.win32_keyboard_layout_cache_interval, defaults.win32_keyboard_layout_cache_interval)

            # App-specific options
            backend_value = config.backend.lower() if config.backend else "auto"
            set_if_changed("backend", backend_value, "auto")
            set_if_changed("clipboard_threshold", config.clipboard_threshold, defaults.clipboard_threshold)
            set_if_changed("enable", config.enable, defaults.enable)
            set_if_changed("inject_delay", config.inject_delay, defaults.inject_delay)
            set_if_changed("key_delay", config.key_delay, defaults.key_delay)
            set_if_changed("paste_shortcut", config.paste_shortcut, defaults.paste_shortcut)
            set_if_changed("pre_paste_delay", config.pre_paste_delay, defaults.pre_paste_delay)
            set_if_changed("restore_clipboard_delay", config.restore_clipboard_delay, defaults.restore_clipboard_delay)
            set_if_changed("post_form_delay", config.post_form_delay, defaults.post_form_delay)
            set_if_changed("post_search_delay", config.post_search_delay, defaults.post_search_delay)
            set_if_changed("paste_shortcut_event_delay", config.paste_shortcut_event_delay, defaults.paste_shortcut_event_delay)
            set_if_changed("max_form_width", config.max_form_width, defaults.max_form_width)
            set_if_changed("max_form_height", config.max_form_height, defaults.max_form_height)
            set_if_changed("apply_patch", config.apply_patch, defaults.apply_patch)

            # Write to file
            with open(self.default_yml_path, "w", encoding="utf-8") as f:
                if data:
                    self.yaml.dump(data, f)
                else:
                    f.write("# Espanso default configuration\n")

            return True

        except Exception as e:
            print(f"Error saving Espanso config: {e}")
            return False

    def exists(self) -> bool:
        """Check if the config directory exists."""
        return self.config_dir.exists()

    def get_default_yml_path(self) -> Path:
        """Get the path to default.yml."""
        return self.default_yml_path
