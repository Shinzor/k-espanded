"""Test script for hotkey functionality on Windows."""

import sys
import time
import traceback

print("=" * 80)
print("HOTKEY SYSTEM TEST")
print("=" * 80)

# Test 1: pynput availability
print("\n1. Testing pynput import...")
try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    print("✓ pynput imported successfully")
except ImportError as e:
    print(f"✗ pynput import failed: {e}")
    print("  Install with: uv pip install pynput")
    sys.exit(1)

# Test 2: Parse different hotkey formats
print("\n2. Testing hotkey parsing...")
test_hotkeys = [
    "<ctrl>+<alt>+`",      # Default - backtick
    "<ctrl>+<alt>+e",      # Alternative - letter e
    "<ctrl>+<shift>+e",    # Alternative - shift + e
    "<ctrl>+<alt>+<space>",  # Space key
]

for hotkey in test_hotkeys:
    try:
        keyboard.HotKey.parse(hotkey)
        print(f"✓ {hotkey} - Valid")
    except Exception as e:
        print(f"✗ {hotkey} - Invalid: {e}")

# Test 3: Create GlobalHotKeys listener
print("\n3. Testing GlobalHotKeys listener...")

test_passed = False

def on_hotkey_pressed():
    global test_passed
    test_passed = True
    print("\n🎉 HOTKEY DETECTED! Test passed!")
    print("Stopping listener...")

try:
    # Test with the letter 'e' first (more reliable than backtick on Windows)
    test_hotkey = "<ctrl>+<alt>+e"
    print(f"  Creating listener for: {test_hotkey}")
    print("  Press Ctrl+Alt+E within 10 seconds to test...")

    listener = keyboard.GlobalHotKeys({
        test_hotkey: on_hotkey_pressed
    })

    listener.start()
    print("✓ Listener started successfully")

    # Wait for hotkey press
    start_time = time.time()
    while time.time() - start_time < 10 and not test_passed:
        time.sleep(0.1)

    listener.stop()

    if test_passed:
        print("✓ GlobalHotKeys test PASSED")
    else:
        print("⚠ No hotkey detected within 10 seconds")
        print("  This may indicate:")
        print("    - Windows permissions issue (try running as administrator)")
        print("    - Another application capturing the hotkey")
        print("    - Keyboard driver compatibility issue")

except Exception as e:
    print(f"✗ GlobalHotKeys test failed: {e}")
    traceback.print_exc()

# Test 4: Test specific backtick key issue
print("\n4. Testing backtick key specifically...")

backtick_test_passed = False

def on_backtick():
    global backtick_test_passed
    backtick_test_passed = True
    print("\n🎉 BACKTICK HOTKEY DETECTED!")

try:
    backtick_hotkey = "<ctrl>+<alt>+`"
    print(f"  Creating listener for: {backtick_hotkey}")
    print("  Press Ctrl+Alt+` (backtick) within 10 seconds...")

    listener = keyboard.GlobalHotKeys({
        backtick_hotkey: on_backtick
    })

    listener.start()

    start_time = time.time()
    while time.time() - start_time < 10 and not backtick_test_passed:
        time.sleep(0.1)

    listener.stop()

    if backtick_test_passed:
        print("✓ Backtick hotkey works!")
    else:
        print("⚠ Backtick hotkey not detected")
        print("  RECOMMENDATION: Use alternative hotkey like Ctrl+Alt+E")
        print("  The backtick key (`) has known issues on some Windows keyboards")

except Exception as e:
    print(f"✗ Backtick test failed: {e}")
    traceback.print_exc()

# Test 5: Test keyboard event listener (for in-app recording)
print("\n5. Testing keyboard event listener (for recording)...")

recorded_keys = []

def on_press(key):
    try:
        # Regular key
        if hasattr(key, 'char') and key.char:
            recorded_keys.append(f"'{key.char}'")
            print(f"  Key pressed: {key.char}")
    except AttributeError:
        # Special key
        recorded_keys.append(f"{key}")
        print(f"  Key pressed: {key}")

    # Stop after 5 keys
    if len(recorded_keys) >= 5:
        return False

try:
    print("  Recording next 5 key presses...")
    print("  (Type any keys now)")

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    if recorded_keys:
        print(f"✓ Recorded {len(recorded_keys)} keys: {', '.join(recorded_keys)}")
    else:
        print("⚠ No keys recorded")
        print("  This may indicate keyboard permission issues")

except Exception as e:
    print(f"✗ Keyboard listener test failed: {e}")
    traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if test_passed or backtick_test_passed:
    print("✓ Hotkey system is WORKING")
    if not backtick_test_passed and test_passed:
        print("⚠ However, backtick key has issues - recommend using Ctrl+Alt+E")
else:
    print("✗ Hotkey system has ISSUES")
    print("\nTroubleshooting steps:")
    print("  1. Run PowerShell as Administrator")
    print("  2. Check Windows Settings > Privacy > Input")
    print("  3. Try closing other apps that might capture hotkeys")
    print("  4. Consider using a different hotkey combination")

print("=" * 80)
