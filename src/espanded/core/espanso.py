"""Espanso integration - path detection, restart, and management."""

import os
import platform
import subprocess
from pathlib import Path


class EspansoManager:
    """Manages Espanso integration - paths, restart, and configuration."""

    def __init__(self, config_path: str | Path | None = None):
        """Initialize Espanso manager.

        Args:
            config_path: Override config path. If None, auto-detects.
        """
        self._config_path = Path(config_path) if config_path else None
        self._system = platform.system()

    @property
    def config_path(self) -> Path:
        """Get Espanso configuration directory path."""
        if self._config_path:
            return self._config_path

        return self._detect_config_path()

    @config_path.setter
    def config_path(self, path: str | Path):
        """Set custom config path."""
        self._config_path = Path(path)

    def _detect_config_path(self) -> Path:
        """Detect Espanso config path based on operating system."""
        if self._system == "Windows":
            # Windows: %APPDATA%\espanso
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                return Path(appdata) / "espanso"
            return Path.home() / "AppData" / "Roaming" / "espanso"

        elif self._system == "Darwin":
            # macOS: ~/Library/Application Support/espanso
            return Path.home() / "Library" / "Application Support" / "espanso"

        else:
            # Linux: ~/.config/espanso
            xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
            if xdg_config:
                return Path(xdg_config) / "espanso"
            return Path.home() / ".config" / "espanso"

    @property
    def match_dir(self) -> Path:
        """Get path to match files directory."""
        return self.config_path / "match"

    @property
    def config_file(self) -> Path:
        """Get path to main config file."""
        return self.config_path / "config" / "default.yml"

    def exists(self) -> bool:
        """Check if Espanso configuration exists."""
        return self.config_path.exists()

    def is_installed(self) -> bool:
        """Check if Espanso is installed and accessible."""
        try:
            result = subprocess.run(
                ["espanso", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def get_version(self) -> str | None:
        """Get installed Espanso version."""
        try:
            result = subprocess.run(
                ["espanso", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None

    def restart(self) -> bool:
        """Restart Espanso to apply configuration changes.

        Returns:
            True if restart was successful, False otherwise.
        """
        try:
            # Stop Espanso
            subprocess.run(
                ["espanso", "stop"],
                capture_output=True,
                timeout=10,
            )

            # Start Espanso
            result = subprocess.run(
                ["espanso", "start"],
                capture_output=True,
                timeout=10,
            )

            return result.returncode == 0

        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def reload(self) -> bool:
        """Reload Espanso configuration without full restart.

        Note: This may not be available in all Espanso versions.

        Returns:
            True if reload was successful, False otherwise.
        """
        try:
            # Try the restart command which is more reliable
            result = subprocess.run(
                ["espanso", "restart"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0

        except (subprocess.SubprocessError, FileNotFoundError):
            # Fall back to stop/start
            return self.restart()

    def get_status(self) -> str:
        """Get Espanso running status.

        Returns:
            Status string: "running", "stopped", or "unknown".
        """
        try:
            result = subprocess.run(
                ["espanso", "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            output = result.stdout.lower()
            if "running" in output:
                return "running"
            elif "not running" in output or "stopped" in output:
                return "stopped"

        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return "unknown"

    def get_match_files(self) -> list[Path]:
        """Get list of all match files in the config directory."""
        if not self.match_dir.exists():
            return []

        files = list(self.match_dir.glob("*.yml"))
        files.extend(self.match_dir.glob("*.yaml"))
        return sorted(files)

    def ensure_directories(self):
        """Ensure required directories exist."""
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.match_dir.mkdir(parents=True, exist_ok=True)
        (self.config_path / "config").mkdir(parents=True, exist_ok=True)

    def backup_config(self, backup_dir: Path | str) -> Path:
        """Create a backup of the current configuration.

        Args:
            backup_dir: Directory to store backup.

        Returns:
            Path to the backup directory.
        """
        import shutil
        from datetime import datetime

        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"espanso_backup_{timestamp}"

        shutil.copytree(self.config_path, backup_path)
        return backup_path

    def get_config_info(self) -> dict:
        """Get information about the current configuration.

        Returns:
            Dictionary with config information.
        """
        info = {
            "path": str(self.config_path),
            "exists": self.exists(),
            "is_installed": self.is_installed(),
            "version": self.get_version(),
            "status": self.get_status(),
            "match_files": [],
            "total_entries": 0,
        }

        if self.exists():
            match_files = self.get_match_files()
            info["match_files"] = [f.name for f in match_files]

            # Count entries (basic count without parsing)
            from espanded.core.yaml_handler import YAMLHandler
            yaml_handler = YAMLHandler()

            total = 0
            for match_file in match_files:
                entries = yaml_handler.read_match_file(match_file)
                total += len(entries)

            info["total_entries"] = total

        return info
