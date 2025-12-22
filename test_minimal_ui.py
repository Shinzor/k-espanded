"""Minimal UI test to isolate white screen issue."""

import flet as ft
import sys
import traceback

print("=" * 80)
print("MINIMAL UI TEST")
print("=" * 80)

# Test 1: Absolute minimal Flet app
print("\n1. Testing absolute minimal Flet app...")

def test_minimal(page: ft.Page):
    print("  Inside test_minimal()")
    page.title = "Minimal Test"
    page.add(ft.Text("Hello World", size=24))
    page.update()
    print("  ✓ Minimal app created")

try:
    print("  Launching...")
    ft.app(target=test_minimal)
    print("✓ Minimal test completed")
except Exception as e:
    print(f"✗ Minimal test failed: {e}")
    traceback.print_exc()

# Test 2: Test with Container and Column (like Espanded uses)
print("\n2. Testing Container + Column layout...")

def test_container_layout(page: ft.Page):
    print("  Inside test_container_layout()")
    page.title = "Container Test"

    container = ft.Container(
        content=ft.Column([
            ft.Text("Container Test", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("This tests the layout structure", size=14),
            ft.ElevatedButton("Click Me", on_click=lambda e: print("Button clicked!")),
        ]),
        padding=20,
        bgcolor=ft.Colors.BLUE_GREY_900,
        expand=True,
    )

    page.add(container)
    page.update()
    print("  ✓ Container layout created")

try:
    print("  Launching...")
    ft.app(target=test_container_layout)
    print("✓ Container test completed")
except Exception as e:
    print(f"✗ Container test failed: {e}")
    traceback.print_exc()

# Test 3: Test imports from Espanded
print("\n3. Testing Espanded component imports...")

try:
    print("  Importing app_state...")
    from espanded.core.app_state import get_app_state
    print("  ✓ app_state imported")

    print("  Importing theme...")
    from espanded.ui.theme import ThemeManager, ThemeSettings
    print("  ✓ theme imported")

    print("  Importing MainWindow...")
    from espanded.ui.main_window import MainWindow
    print("  ✓ MainWindow imported")

    print("  Importing FirstRunWizard...")
    from espanded.ui.first_run_wizard import FirstRunWizard
    print("  ✓ FirstRunWizard imported")

except Exception as e:
    print(f"✗ Import test failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test creating FirstRunWizard (likely issue)
print("\n4. Testing FirstRunWizard creation...")

def test_wizard(page: ft.Page):
    print("  Inside test_wizard()")
    try:
        print("  Creating app_state...")
        from espanded.core.app_state import get_app_state
        app_state = get_app_state()
        print("  ✓ app_state created")

        print("  Creating theme...")
        from espanded.ui.theme import ThemeManager, ThemeSettings
        settings = app_state.settings
        theme_settings = ThemeSettings(
            theme=settings.theme,
            custom_colors=settings.custom_colors,
        )
        theme_manager = ThemeManager(theme_settings)
        print("  ✓ theme_manager created")

        print("  Creating FirstRunWizard...")
        from espanded.ui.first_run_wizard import FirstRunWizard

        def on_complete():
            print("  Wizard completed!")
            page.window.close()

        wizard = FirstRunWizard(theme=theme_manager, on_complete=on_complete)
        print("  ✓ wizard instance created")

        print("  Adding wizard to page...")
        page.add(wizard)
        print("  ✓ wizard added")

        print("  Updating page...")
        page.update()
        print("  ✓ page updated - UI should be visible now!")

    except Exception as e:
        print(f"  ✗ Error in test_wizard: {e}")
        traceback.print_exc()
        # Show error in UI
        page.add(ft.Text(f"Error: {e}", color=ft.Colors.RED, size=18))
        page.update()

try:
    print("  Launching wizard test...")
    ft.app(target=test_wizard)
    print("✓ Wizard test completed")
except Exception as e:
    print(f"✗ Wizard test failed: {e}")
    traceback.print_exc()

# Test 5: Test creating MainWindow (for non-first-run case)
print("\n5. Testing MainWindow creation...")

def test_main_window(page: ft.Page):
    print("  Inside test_main_window()")
    try:
        print("  Creating app_state...")
        from espanded.core.app_state import get_app_state
        app_state = get_app_state()

        # Force has_imported to True to skip wizard
        app_state.settings.has_imported = True
        print("  ✓ app_state created (has_imported=True)")

        print("  Creating theme...")
        from espanded.ui.theme import ThemeManager, ThemeSettings
        settings = app_state.settings
        theme_settings = ThemeSettings(
            theme=settings.theme,
            custom_colors=settings.custom_colors,
        )
        theme_manager = ThemeManager(theme_settings)
        print("  ✓ theme_manager created")

        print("  Creating MainWindow...")
        from espanded.ui.main_window import MainWindow
        main_window = MainWindow(page, theme_manager)
        print("  ✓ main_window instance created")

        print("  Adding main_window to page...")
        page.add(main_window)
        print("  ✓ main_window added")

        print("  Updating page...")
        page.update()
        print("  ✓ page updated - UI should be visible now!")

    except Exception as e:
        print(f"  ✗ Error in test_main_window: {e}")
        traceback.print_exc()
        # Show error in UI
        page.add(ft.Text(f"Error: {e}", color=ft.Colors.RED, size=18))
        page.update()

try:
    print("  Launching main window test...")
    ft.app(target=test_main_window)
    print("✓ Main window test completed")
except Exception as e:
    print(f"✗ Main window test failed: {e}")
    traceback.print_exc()

print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
print("\nIf you see white screens:")
print("  - Check the console output above for specific errors")
print("  - The error likely occurs during component initialization")
print("  - Most common: missing files, import errors, or theme issues")
print("\nIf windows appear correctly:")
print("  - The issue may be specific to the startup flow in main.py")
print("  - Try running: uv run espanded")
print("=" * 80)
