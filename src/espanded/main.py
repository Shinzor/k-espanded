"""Application entry point for Espanded."""

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from espanded.app import create_app


def main():
    """Main entry point for the Qt application."""
    # Enable high DPI scaling
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Create QApplication instance
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Espanded")
    app.setOrganizationName("Espanded")
    app.setApplicationDisplayName("Espanded - Espanso GUI Manager")

    # Create main window and initialize services
    main_window, services = create_app()

    if main_window is None:
        print("Failed to create main window - exiting")
        return 1

    # Apply theme to application
    from espanded.core.app_state import get_app_state
    app_state = get_app_state()
    if app_state.theme_manager:
        app_state.theme_manager.apply_to_app(app)

    # Show the main window
    main_window.show()

    # Run the application event loop
    exit_code = app.exec()

    # Cleanup on exit
    if services.get('cleanup_func'):
        services['cleanup_func']()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
