"""Diagnostic script to identify startup and rendering issues."""

import sys
import traceback
from pathlib import Path

print("=" * 80)
print("ESPANDED DIAGNOSTIC SCRIPT")
print("=" * 80)

# Step 1: Check Python version
print(f"\n1. Python Version: {sys.version}")
print(f"   Platform: {sys.platform}")

# Step 2: Check dependencies
print("\n2. Checking Dependencies...")
dependencies = {
    "flet": None,
    "pynput": None,
    "ruamel.yaml": None,
    "Pillow": None,
}

for dep in dependencies.keys():
    try:
        module = __import__(dep.replace(".", "_") if "." in dep else dep)
        version = getattr(module, "__version__", "unknown")
        dependencies[dep] = version
        print(f"   ✓ {dep}: {version}")
    except ImportError as e:
        dependencies[dep] = None
        print(f"   ✗ {dep}: NOT FOUND - {e}")

# Step 3: Check pynput functionality
print("\n3. Testing pynput...")
try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    print("   ✓ pynput imports successfully")

    # Test GlobalHotKeys
    try:
        test_hotkey = "<ctrl>+<alt>+`"
        keyboard.HotKey.parse(test_hotkey)
        print(f"   ✓ Hotkey parsing works: {test_hotkey}")
    except Exception as e:
        print(f"   ✗ Hotkey parsing failed: {e}")
        traceback.print_exc()
except ImportError as e:
    print(f"   ✗ pynput import failed: {e}")

# Step 4: Test Flet basic functionality
print("\n4. Testing Flet...")
try:
    import flet as ft
    print(f"   ✓ Flet imports successfully")
    print(f"   Flet version: {ft.__version__ if hasattr(ft, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"   ✗ Flet import failed: {e}")

# Step 5: Check espanded imports
print("\n5. Testing Espanded Imports...")
espanded_modules = [
    "espanded.core.app_state",
    "espanded.core.database",
    "espanded.core.entry_manager",
    "espanded.ui.theme",
    "espanded.ui.main_window",
    "espanded.ui.first_run_wizard",
    "espanded.hotkeys.listener",
    "espanded.services.hotkey_service",
]

for mod in espanded_modules:
    try:
        __import__(mod)
        print(f"   ✓ {mod}")
    except Exception as e:
        print(f"   ✗ {mod}: {e}")
        traceback.print_exc()

# Step 6: Check database initialization
print("\n6. Testing Database Initialization...")
try:
    from espanded.core.database import Database
    db = Database()
    print(f"   ✓ Database created at: {db.db_path}")
    settings = db.get_settings()
    print(f"   ✓ Settings loaded: has_imported={settings.has_imported}")
except Exception as e:
    print(f"   ✗ Database initialization failed: {e}")
    traceback.print_exc()

# Step 7: Test minimal Flet app
print("\n7. Testing Minimal Flet App...")
print("   Creating minimal test app (will open window for 3 seconds)...")

test_passed = False

def test_minimal_app(page: ft.Page):
    global test_passed
    try:
        page.title = "Test Window"
        page.window.width = 400
        page.window.height = 300

        # Add simple controls
        page.add(
            ft.Column([
                ft.Text("Test Successful!", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("If you see this, Flet rendering works!"),
                ft.ElevatedButton("Click Me", on_click=lambda e: print("   Button clicked!")),
            ])
        )

        page.update()
        test_passed = True
        print("   ✓ Minimal app created successfully")

        # Auto-close after delay
        import time
        time.sleep(3)
        page.window.close()
    except Exception as e:
        print(f"   ✗ Minimal app failed: {e}")
        traceback.print_exc()

try:
    import flet as ft
    print("   Launching test window...")
    ft.app(target=test_minimal_app)
    if test_passed:
        print("   ✓ Flet rendering test PASSED")
    else:
        print("   ✗ Flet rendering test FAILED")
except Exception as e:
    print(f"   ✗ Could not launch test app: {e}")
    traceback.print_exc()

# Step 8: Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

all_deps_ok = all(v is not None for v in dependencies.values())
print(f"Dependencies: {'✓ All OK' if all_deps_ok else '✗ Some missing'}")
print(f"Flet Rendering: {'✓ OK' if test_passed else '✗ FAILED'}")

print("\nNext Steps:")
if not all_deps_ok:
    print("  1. Install missing dependencies with: uv pip install <package>")
if not test_passed:
    print("  2. Flet rendering issue detected - check Flet version and system compatibility")

print("\nTo run the actual app with verbose logging, use:")
print("  uv run python -c 'import espanded.app; import flet as ft; ft.app(target=espanded.app.create_app)'")
print("=" * 80)
