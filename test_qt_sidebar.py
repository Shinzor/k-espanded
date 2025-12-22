"""Test script for Qt sidebar implementation - Phase 3."""

import sys
from PySide6.QtWidgets import QApplication

from espanded.ui.qt_theme import QtThemeManager, ThemeSettings
from espanded.ui.qt_main_window import QtMainWindow
from espanded.core.app_state import get_app_state
from espanded.core.models import Entry


def create_test_entries():
    """Create some test entries for demonstration."""
    app_state = get_app_state()
    entry_manager = app_state.entry_manager

    # Check if we already have entries
    existing = entry_manager.get_all_entries()
    if existing:
        print(f"Found {len(existing)} existing entries")
        return

    print("Creating test entries...")

    # Create test entries with different characteristics
    test_entries = [
        Entry(
            trigger="email",
            prefix=":",
            replacement="john.doe@example.com",
            tags=["contact", "personal"],
        ),
        Entry(
            trigger="addr",
            prefix=":",
            replacement="123 Main St, Springfield, IL 62701",
            tags=["personal"],
        ),
        Entry(
            trigger="phone",
            prefix=":",
            replacement="+1 (555) 123-4567",
            tags=["contact"],
        ),
        Entry(
            trigger="signature",
            prefix=":",
            replacement="Best regards,\nJohn Doe\nSoftware Engineer",
            tags=["email", "professional"],
        ),
        Entry(
            trigger="meeting",
            prefix=":",
            replacement="Thanks for scheduling a meeting. I'm available on:\n- Monday at 2pm\n- Wednesday at 10am\n- Friday at 3pm",
            tags=["email", "professional", "meetings"],
        ),
        Entry(
            trigger="lorem",
            prefix=":",
            replacement="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
            tags=["text", "placeholder"],
        ),
        Entry(
            trigger="date",
            prefix=":",
            replacement="{{mydate}}",
            tags=["variables", "time"],
        ),
        Entry(
            trigger="name",
            prefix=":",
            replacement="John Doe",
            tags=["personal"],
        ),
        Entry(
            trigger="website",
            prefix=":",
            replacement="https://example.com",
            tags=["links"],
        ),
        Entry(
            trigger="code",
            prefix=":",
            replacement='def hello_world():\n    print("Hello, World!")',
            tags=["code", "python"],
        ),
    ]

    for entry in test_entries:
        entry_manager.create_entry(entry)

    print(f"Created {len(test_entries)} test entries")


def main():
    """Run the Qt sidebar test."""
    print("Starting Qt Sidebar Test (Phase 3)...")
    print("=" * 60)

    # Create Qt application
    app = QApplication(sys.argv)

    # Create test entries
    create_test_entries()

    # Create theme manager
    theme_settings = ThemeSettings(theme="dark")
    theme_manager = QtThemeManager(theme_settings)
    theme_manager.apply_to_app(app)

    # Create main window
    window = QtMainWindow(theme_manager)
    window.show()

    print("\nTest Instructions:")
    print("-" * 60)
    print("1. Search Bar:")
    print("   - Type in the search box to filter entries")
    print("   - Click X button to clear search")
    print()
    print("2. View Tabs:")
    print("   - Click 'All' to see all entries")
    print("   - Click 'Favorites' (empty for now)")
    print("   - Click 'Tags' to see tag dropdown menu")
    print("   - Click 'Trash' to see deleted entries")
    print()
    print("3. Entry List:")
    print("   - Click entry to select (visual feedback)")
    print("   - Double-click entry to edit (opens editor view)")
    print("   - Right-click entry for context menu:")
    print("     * Edit, Duplicate, Toggle Favorite, Delete")
    print("   - Scroll to see all entries")
    print()
    print("4. Add Entry Button:")
    print("   - Click '+ Add Entry' button at bottom")
    print("   - Check console for 'Add new entry clicked' message")
    print()
    print("5. Context Menu Actions:")
    print("   - Duplicate: Creates a copy of the entry")
    print("   - Delete: Moves entry to trash")
    print("   - In Trash view: Restore or Delete Permanently")
    print()
    print("Press Ctrl+C to exit")
    print("=" * 60)

    # Run app
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
