"""Application state - singleton for shared services."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from espanded.core.database import Database
    from espanded.core.entry_manager import EntryManager
    from espanded.core.espanso import EspansoManager
    from espanded.core.models import Settings
    from espanded.ui.theme import ThemeManager
    from espanded.sync.sync_manager import SyncManager


class AppState:
    """Singleton application state holding shared services."""

    _instance: "AppState | None" = None

    def __init__(self):
        """Initialize app state - use get_instance() instead."""
        self._database: "Database | None" = None
        self._entry_manager: "EntryManager | None" = None
        self._espanso: "EspansoManager | None" = None
        self._settings: "Settings | None" = None
        self._theme_manager: "ThemeManager | None" = None
        self._sync_manager: "SyncManager | None" = None

    @classmethod
    def get_instance(cls) -> "AppState":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = AppState()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the singleton (for testing)."""
        cls._instance = None

    @property
    def database(self) -> "Database":
        """Get the database instance."""
        if self._database is None:
            from espanded.core.database import Database
            self._database = Database()
        return self._database

    @database.setter
    def database(self, db: "Database"):
        """Set the database instance."""
        self._database = db

    @property
    def entry_manager(self) -> "EntryManager":
        """Get the entry manager instance."""
        if self._entry_manager is None:
            from espanded.core.entry_manager import EntryManager
            self._entry_manager = EntryManager(
                database=self.database,
                espanso=self.espanso,
            )
        return self._entry_manager

    @entry_manager.setter
    def entry_manager(self, manager: "EntryManager"):
        """Set the entry manager instance."""
        self._entry_manager = manager

    @property
    def espanso(self) -> "EspansoManager":
        """Get the Espanso manager instance."""
        if self._espanso is None:
            from espanded.core.espanso import EspansoManager
            self._espanso = EspansoManager()
        return self._espanso

    @espanso.setter
    def espanso(self, manager: "EspansoManager"):
        """Set the Espanso manager instance."""
        self._espanso = manager

    @property
    def settings(self) -> "Settings":
        """Get the settings instance."""
        if self._settings is None:
            self._settings = self.database.get_settings()
        return self._settings

    @settings.setter
    def settings(self, settings: "Settings"):
        """Set and persist settings."""
        self._settings = settings
        self.database.save_settings(settings)

    @property
    def theme_manager(self) -> "ThemeManager":
        """Get the theme manager instance."""
        if self._theme_manager is None:
            from espanded.ui.theme import ThemeManager, ThemeSettings
            theme_settings = ThemeSettings(
                theme=self.settings.theme,
                custom_colors=self.settings.custom_colors,
            )
            self._theme_manager = ThemeManager(theme_settings)
        return self._theme_manager

    @theme_manager.setter
    def theme_manager(self, manager: "ThemeManager"):
        """Set the theme manager instance."""
        self._theme_manager = manager

    @property
    def sync_manager(self) -> "SyncManager | None":
        """Get the sync manager instance."""
        return self._sync_manager

    @sync_manager.setter
    def sync_manager(self, manager: "SyncManager | None"):
        """Set the sync manager instance."""
        self._sync_manager = manager

    def save_settings(self):
        """Persist current settings to database."""
        if self._settings:
            self.database.save_settings(self._settings)


# Convenience function
def get_app_state() -> AppState:
    """Get the application state singleton."""
    return AppState.get_instance()
