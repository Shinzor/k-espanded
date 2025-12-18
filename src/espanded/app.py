"""Flet application setup and configuration."""

import flet as ft
import logging
import sys
import traceback
from pathlib import Path

from espanded.core.app_state import get_app_state
from espanded.ui.theme import ThemeManager, ThemeSettings
from espanded.ui.main_window import MainWindow
from espanded.ui.first_run_wizard import FirstRunWizard
from espanded.services.hotkey_service import get_hotkey_service

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Optional tray support
try:
    from espanded.tray import SystemTray, PYSTRAY_AVAILABLE
except ImportError:
    PYSTRAY_AVAILABLE = False
    SystemTray = None

# Optional sync support
try:
    from espanded.sync import SyncManager
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False
    SyncManager = None

logger = logging.getLogger(__name__)


def create_app(page: ft.Page):
    """Create and configure the main Flet application."""
    print("=" * 80)
    print("ESPANDED STARTUP - BEGIN")
    print("=" * 80)

    try:
        # Initialize app state
        print("[1/10] Initializing app state...")
        app_state = get_app_state()
        print("✓ App state initialized")

        # Basic page setup
        print("[2/10] Setting up page properties...")
        page.title = "Espanded"
        page.window.width = 1200
        page.window.height = 800
        page.window.min_width = 900
        page.window.min_height = 600
        print("✓ Page properties set")

        # Initialize theme manager from settings
        print("[3/10] Loading settings...")
        settings = app_state.settings
        print(f"✓ Settings loaded: theme={settings.theme}, has_imported={settings.has_imported}")

        print("[4/10] Initializing theme manager...")
        theme_settings = ThemeSettings(
            theme=settings.theme,
            custom_colors=settings.custom_colors,
        )
        theme_manager = ThemeManager(theme_settings)
        app_state.theme_manager = theme_manager
        print("✓ Theme manager created")

        print("[5/10] Applying theme to page...")
        theme_manager.apply_to_page(page)
        print("✓ Theme applied to page")
    except Exception as e:
        print(f"✗ ERROR during initialization: {e}")
        traceback.print_exc()
        # Show error in window
        page.add(ft.Text(f"Initialization Error: {e}", color=ft.Colors.RED))
        page.update()
        return

    # Initialize hotkey service
    try:
        print("[6/10] Initializing hotkey service...")
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
    except Exception as e:
        print(f"⚠ WARNING: Hotkey service initialization failed: {e}")
        traceback.print_exc()
        # Continue without hotkeys

    # Initialize sync manager (if available and configured)
    try:
        print("[7/10] Initializing sync manager...")
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
    except Exception as e:
        print(f"⚠ WARNING: Sync manager initialization failed: {e}")
        traceback.print_exc()
        app_state.sync_manager = None
        # Continue without sync

    # Initialize system tray (if available)
    try:
        print("[8/10] Initializing system tray...")
        tray = None
        if PYSTRAY_AVAILABLE and SystemTray and settings.minimize_to_tray:
            try:
                tray = SystemTray()

                def show_main_window():
                    page.window.visible = True
                    page.window.focused = True
                    page.update()

                def trigger_quick_add():
                    from espanded.ui.quick_add import show_quick_add_popup
                    show_quick_add_popup("")

                def quit_app():
                    cleanup_and_exit()

                def toggle_hotkeys(enabled: bool):
                    if enabled:
                        hotkey_service.enable()
                    else:
                        hotkey_service.disable()

                tray.set_callbacks(
                    on_show=show_main_window,
                    on_quick_add=trigger_quick_add,
                    on_quit=quit_app,
                    on_toggle_hotkeys=toggle_hotkeys,
                )
                tray.run_detached()
                print("✓ System tray initialized")
            except Exception as e:
                print(f"⚠ Failed to initialize system tray: {e}")
                tray = None
        else:
            print("✓ System tray skipped (not available or disabled)")
    except Exception as e:
        print(f"⚠ WARNING: System tray initialization failed: {e}")
        traceback.print_exc()
        tray = None
        # Continue without tray

    def cleanup_and_exit():
        """Cleanup resources and exit."""
        # Stop hotkey service
        hotkey_service.stop()

        # Stop sync manager
        if sync_manager:
            sync_manager.close()

        # Stop tray
        if tray:
            tray.stop()

        # Save settings
        app_state.save_settings()

        # Close window
        page.window.destroy()

    # Handle window events
    print("[9/10] Setting up window event handlers...")
    def on_window_event(e):
        if e.data == "close":
            if tray and settings.minimize_to_tray:
                # Minimize to tray instead of closing
                page.window.visible = False
                page.update()
            else:
                cleanup_and_exit()

    page.window.on_event = on_window_event
    page.window.prevent_close = True
    print("✓ Window event handlers configured")

    # Check if this is first run
    try:
        print("[10/10] Building UI...")
        if not settings.has_imported:
            # Show first run wizard
            print("  Showing first run wizard...")
            def on_wizard_complete():
                print("  Wizard complete - transitioning to main window...")
                # Clear page and show main window
                page.clean()
                main_window = MainWindow(page, theme_manager)
                page.add(main_window)
                page.update()
                print("✓ Main window displayed after wizard")

            wizard = FirstRunWizard(theme=theme_manager, on_complete=on_wizard_complete)
            page.add(wizard)
            print("✓ First run wizard added to page")
        else:
            # Create and add main window
            print("  Creating main window...")
            main_window = MainWindow(page, theme_manager)
            print("  Adding main window to page...")
            page.add(main_window)
            print("✓ Main window added to page")

        print("  Calling page.update()...")
        page.update()
        print("✓ Page updated successfully")
        print("=" * 80)
        print("ESPANDED STARTUP - COMPLETE")
        print("=" * 80)
    except Exception as e:
        print(f"✗ ERROR during UI creation: {e}")
        traceback.print_exc()
        # Try to show error
        try:
            page.clean()
            page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Text("Startup Error", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                        ft.Text(f"Error: {e}", color=ft.Colors.RED),
                        ft.Text("Check console for details", size=12),
                    ]),
                    padding=20,
                )
            )
            page.update()
        except:
            pass
