"""Application entry point for Espanded."""

import argparse
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    # Workarounds for Flet desktop white screen issue on Windows
    # Try multiple rendering fixes:

    # 1. Disable GPU acceleration (may help with some drivers)
    os.environ.setdefault("FLET_DESKTOP_WINDOW_DISABLE_GPU", "true")

    # 2. Force software rendering via ANGLE/SwiftShader
    os.environ.setdefault("ANGLE_DEFAULT_PLATFORM", "swiftshader")

    # 3. Disable Flutter's Impeller rendering engine (new in Flutter 3.22+)
    # This is the most likely fix for white screen on Windows 10/11
    os.environ.setdefault("FLUTTER_ENGINE_SWITCHES", "1")
    os.environ.setdefault("FLUTTER_ENGINE_SWITCH_0", "--no-enable-impeller")

import flet as ft

from espanded.app import create_app


def get_assets_dir() -> str | None:
    """Get absolute path to assets directory, or None if not found."""
    # Try multiple locations for assets
    candidates = [
        # Relative to current working directory
        Path.cwd() / "assets",
        # Relative to this file's package
        Path(__file__).parent.parent.parent / "assets",
        # Relative to project root (if running from src/)
        Path(__file__).parent.parent.parent.parent / "assets",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            # Only return if directory has content, otherwise None
            if any(candidate.iterdir()):
                return str(candidate.resolve())

    # Return None if no assets found (Flet handles this gracefully)
    return None


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Espanded - Espanso GUI Manager")
    parser.add_argument(
        "--web", "-w",
        action="store_true",
        help="Run in web browser mode instead of desktop window"
    )
    parser.add_argument(
        "--desktop", "-d",
        action="store_true",
        help="Force desktop mode (native window)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8550,
        help="Port for web mode (default: 8550)"
    )
    args = parser.parse_args()

    # Get assets directory (None if empty/missing)
    assets_dir = get_assets_dir()

    # Determine view mode
    # On Windows, default to web browser mode due to Flet desktop rendering issues
    # unless --desktop is explicitly requested
    is_windows = sys.platform == "win32"

    if args.desktop:
        # Explicit desktop mode requested
        use_web = False
    elif args.web:
        # Explicit web mode requested
        use_web = True
    elif is_windows:
        # Default to web on Windows due to known Flet desktop white screen issue
        print("Note: Running in web browser mode (Windows default).")
        print("      Use --desktop flag to force native window mode.")
        use_web = True
    else:
        # Default to desktop on Linux/macOS
        use_web = False

    if use_web:
        ft.app(
            target=create_app,
            assets_dir=assets_dir,
            view=ft.AppView.WEB_BROWSER,
            port=args.port
        )
    else:
        ft.app(
            target=create_app,
            assets_dir=assets_dir
        )


if __name__ == "__main__":
    main()
