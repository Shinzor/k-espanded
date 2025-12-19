"""YAML handler for reading and writing Espanso configuration files."""

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from espanded.core.models import Entry


class YAMLHandler:
    """Handles reading and writing Espanso YAML configuration files."""

    def __init__(self):
        """Initialize YAML handler with ruamel.yaml for format preservation."""
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False
        self.yaml.indent(mapping=2, sequence=4, offset=2)

    def read_match_file(self, file_path: Path | str) -> list[Entry]:
        """Read entries from an Espanso match file.

        Args:
            file_path: Path to the YAML match file.

        Returns:
            List of Entry objects parsed from the file.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            data = self.yaml.load(f)

        if not data:
            return []

        entries = []
        matches = data.get("matches", [])

        for match in matches:
            if "trigger" in match and "replace" in match:
                entry = Entry.from_espanso_dict(
                    match,
                    source_file=file_path.name,
                )
                entries.append(entry)

        return entries

    def write_match_file(self, file_path: Path | str, entries: list[Entry]):
        """Write entries to an Espanso match file.

        Args:
            file_path: Path to the YAML match file.
            entries: List of Entry objects to write.
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert entries to YAML format
        matches = [entry.to_espanso_dict() for entry in entries if not entry.is_deleted]

        data = {"matches": matches}

        with open(file_path, "w", encoding="utf-8") as f:
            self.yaml.dump(data, f)

    def read_config_file(self, file_path: Path | str) -> dict[str, Any]:
        """Read Espanso config file (default.yml).

        Args:
            file_path: Path to the config file.

        Returns:
            Dictionary of configuration values.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return {}

        with open(file_path, "r", encoding="utf-8") as f:
            data = self.yaml.load(f)

        return data or {}

    def write_config_file(self, file_path: Path | str, config: dict[str, Any]):
        """Write Espanso config file.

        Args:
            file_path: Path to the config file.
            config: Configuration dictionary to write.
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            self.yaml.dump(config, f)

    def read_all_match_files(self, config_dir: Path | str) -> dict[str, list[Entry]]:
        """Read all match files from an Espanso config directory.

        Args:
            config_dir: Path to Espanso config directory.

        Returns:
            Dictionary mapping file names to lists of entries.
        """
        config_dir = Path(config_dir)
        match_dir = config_dir / "match"

        if not match_dir.exists():
            return {}

        result = {}
        for yaml_file in match_dir.glob("*.yml"):
            entries = self.read_match_file(yaml_file)
            if entries:
                result[yaml_file.name] = entries

        # Also check for .yaml extension
        for yaml_file in match_dir.glob("*.yaml"):
            entries = self.read_match_file(yaml_file)
            if entries:
                result[yaml_file.name] = entries

        return result

    def export_to_yaml(self, entry: Entry) -> str:
        """Export a single entry to YAML string.

        Args:
            entry: Entry to export.

        Returns:
            YAML formatted string.
        """
        from io import StringIO

        data = {"matches": [entry.to_espanso_dict()]}
        stream = StringIO()
        self.yaml.dump(data, stream)
        return stream.getvalue()

    def import_from_yaml(self, yaml_content: str, source_file: str = "imported.yml") -> list[Entry]:
        """Import entries from YAML string.

        Args:
            yaml_content: YAML formatted string.
            source_file: Name to use for source_file attribute.

        Returns:
            List of Entry objects.
        """
        from io import StringIO

        data = self.yaml.load(StringIO(yaml_content))

        if not data:
            return []

        entries = []
        matches = data.get("matches", [])

        for match in matches:
            if "trigger" in match and "replace" in match:
                entry = Entry.from_espanso_dict(match, source_file=source_file)
                entries.append(entry)

        return entries

    def validate_yaml(self, yaml_content: str) -> tuple[bool, str]:
        """Validate YAML content.

        Args:
            yaml_content: YAML string to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        from io import StringIO

        try:
            data = self.yaml.load(StringIO(yaml_content))

            if data is None:
                return True, ""

            # Check for required structure
            if "matches" in data:
                matches = data["matches"]
                if not isinstance(matches, list):
                    return False, "'matches' must be a list"

                for i, match in enumerate(matches):
                    if not isinstance(match, dict):
                        return False, f"Match {i+1} must be a dictionary"
                    if "trigger" not in match:
                        return False, f"Match {i+1} is missing 'trigger'"
                    if "replace" not in match:
                        return False, f"Match {i+1} is missing 'replace'"

            return True, ""

        except Exception as e:
            return False, str(e)
