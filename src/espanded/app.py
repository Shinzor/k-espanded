"""PySide6 application setup and configuration."""

import logging
import sys
import traceback
from pathlib import Path

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

from espanded.core.app_state import get_app_state
from espanded.ui.theme import ThemeManager, ThemeSettings
from espanded.ui.main_window import MainWindow
from espanded.ui.system_tray import SystemTray
from espanded.ui.quick_add import QuickAddPopup
from espanded.services.hotkey_service import get_hotkey_service
from espanded.services.autocomplete_service import init_autocomplete_service, get_autocomplete_service
from espanded.hotkeys.listener import get_keystroke_monitor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Optional sync support
try:
    from espanded.sync import SyncManager
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False
    SyncManager = None

logger = logging.getLogger(__name__)


def create_app() -> tuple[MainWindow | None, dict]:
    """Create and configure the Qt application.

    Returns:
        tuple: (MainWindow instance or None, dict of initialized services)
    """
    print("=" * 80)
    print("ESPANDED STARTUP - BEGIN (Qt)")
    print("=" * 80)

    services = {
        'hotkey_service': None,
        'autocomplete_service': None,
        'keystroke_monitor': None,
        'sync_manager': None,
        'tray': None,
        'cleanup_func': None,
    }

    try:
        # Initialize app state
        print("[1/7] Initializing app state...")
        app_state = get_app_state()
        print("✓ App state initialized")

        # Load settings
        print("[2/7] Loading settings...")
        settings = app_state.settings
        print(f"✓ Settings loaded: theme={settings.theme}, has_imported={settings.has_imported}")

        # Initialize theme manager
        print("[3/7] Initializing theme manager...")
        theme_settings = ThemeSettings(
            theme=settings.theme,
            custom_colors=settings.custom_colors,
        )
        theme_manager = ThemeManager(theme_settings)
        app_state.theme_manager = theme_manager
        print("✓ Theme manager created")

    except Exception as e:
        print(f"✗ ERROR during initialization: {e}")
        traceback.print_exc()
        return None, services

    # Initialize hotkey service
    try:
        print("[4/8] Initializing hotkey service...")
        hotkey_service = get_hotkey_service()
        if hotkey_service.is_available:
            # Use the quick add hotkey from settings
            quick_add_hotkey = settings.quick_add_hotkey or "<ctrl>+<alt>+`"
            print(f"  Starting hotkey listener with: {quick_add_hotkey}")
            hotkey_service.start(quick_add_hotkey)
            # Respect enabled/disabled setting
            if not getattr(settings, 'hotkeys_enabled', True):
                hotkey_service.disable()
            print(f"✓ Hotkey service started: {quick_add_hotkey} (enabled: {hotkey_service.is_enabled})")
        else:
            print("⚠ Hotkey service not available (pynput not installed or failed to import)")
        services['hotkey_service'] = hotkey_service
    except Exception as e:
        print(f"⚠ WARNING: Hotkey service initialization failed: {e}")
        traceback.print_exc()
        # Continue without hotkeys

    # Initialize autocomplete service (inline suggestions)
    try:
        print("[5/8] Initializing autocomplete service...")
        autocomplete_service = None
        keystroke_monitor = None

        if settings.autocomplete_enabled:
            # Initialize the autocomplete service
            autocomplete_service = init_autocomplete_service(app_state, theme_manager)

            # Get and configure the keystroke monitor
            keystroke_monitor = get_keystroke_monitor()
            if keystroke_monitor:
                # Set the callback to route keystrokes to autocomplete service
                keystroke_monitor.set_callback(autocomplete_service.on_key_press)
                keystroke_monitor.start()
                print(f"✓ Autocomplete service started with triggers: {settings.autocomplete_triggers}")
            else:
                print("⚠ Keystroke monitor not available")

            # Start the autocomplete service
            autocomplete_service.start()
        else:
            print("✓ Autocomplete service skipped (disabled in settings)")

        services['autocomplete_service'] = autocomplete_service
        services['keystroke_monitor'] = keystroke_monitor
    except Exception as e:
        print(f"⚠ WARNING: Autocomplete service initialization failed: {e}")
        traceback.print_exc()
        # Continue without autocomplete

    # Initialize sync manager (if available and configured)
    try:
        print("[6/8] Initializing sync manager...")
        sync_manager = None
        if SYNC_AVAILABLE and SyncManager and settings.github_repo and settings.github_token:
            try:
                sync_manager = SyncManager(
                    repo=settings.github_repo,
                    token=settings.github_token,
                    local_path=Path(settings.espanso_config_path) if settings.espanso_config_path else Path.home() / ".config" / "espanso",
                    on_conflict=None,  # TODO: Wire up conflict resolution UI
                )

                # Test connection
                if sync_manager.test_connection():
                    print(f"✓ GitHub sync connected to {settings.github_repo}")

                    # Start auto-sync if enabled
                    if settings.auto_sync:
                        sync_manager.start_auto_sync(settings.sync_interval)
                        print(f"✓ Auto-sync started (interval: {settings.sync_interval}s)")
                else:
                    print("⚠ GitHub sync connection test failed")
                    sync_manager = None

            except Exception as e:
                print(f"⚠ Failed to initialize sync manager: {e}")
                sync_manager = None
        else:
            print("✓ Sync manager skipped (not configured)")

        # Store sync manager in app state for later access
        app_state.sync_manager = sync_manager
        services['sync_manager'] = sync_manager
    except Exception as e:
        print(f"⚠ WARNING: Sync manager initialization failed: {e}")
        traceback.print_exc()
        app_state.sync_manager = None
        # Continue without sync

    # Initialize system tray (Qt-based)
    try:
        print("[7/8] Initializing system tray...")
        tray = None
        # Check if system tray is available
        from PySide6.QtWidgets import QSystemTrayIcon
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("⚠ System tray not available on this platform")
        elif settings.minimize_to_tray:
            tray = SystemTray(theme_manager)
            print("✓ Qt system tray created")
        else:
            print("✓ System tray skipped (minimize_to_tray disabled)")
        services['tray'] = tray
    except Exception as e:
        print(f"⚠ WARNING: System tray initialization failed: {e}")
        traceback.print_exc()
        tray = None
        # Continue without tray

    def cleanup_and_exit():
        """Cleanup resources and exit."""
        # Stop keystroke monitor
        if services['keystroke_monitor']:
            services['keystroke_monitor'].stop()

        # Stop autocomplete service
        if services['autocomplete_service']:
            services['autocomplete_service'].stop()

        # Stop hotkey service
        if services['hotkey_service']:
            services['hotkey_service'].stop()

        # Stop sync manager
        if services['sync_manager']:
            services['sync_manager'].close()

        # Stop tray (Qt tray uses cleanup method)
        if services['tray']:
            services['tray'].cleanup()

        # Save settings
        app_state.save_settings()

    services['cleanup_func'] = cleanup_and_exit

    # Create main window
    try:
        print("[8/8] Creating main window...")
        main_window = MainWindow(
            theme_manager,
            tray=services['tray'],
            hotkey_service=services['hotkey_service'],
        )
        print("✓ Main window created with custom title bar, sidebar, and content area")

        print("=" * 80)
        print("ESPANDED STARTUP - COMPLETE (Qt)")
        print("=" * 80)

        return main_window, services

    except Exception as e:
        print(f"✗ ERROR during window creation: {e}")
        traceback.print_exc()
        return None, services
