# Diagnostic Tools for Espanded

This directory contains three diagnostic scripts to help troubleshoot issues with Espanded on Windows 11.

## Quick Reference

| Issue | Script to Run | Requires Admin |
|-------|---------------|----------------|
| White screen / App won't start | `uv run python debug_startup.py` | No |
| Hotkeys not working | `uv run python test_hotkeys.py` | Yes (recommended) |
| UI rendering issues | `uv run python test_minimal_ui.py` | No |

---

## 1. debug_startup.py

**Purpose:** Comprehensive system diagnostic for Espanded startup issues.

**When to Use:**
- App shows white screen
- App crashes on startup
- Import errors
- Database errors
- General troubleshooting

**What It Tests:**
1. Python version and platform
2. All dependencies (flet, pynput, ruamel.yaml, Pillow)
3. pynput functionality (imports, hotkey parsing)
4. Flet basic functionality
5. Espanded module imports
6. Database initialization
7. Minimal Flet window rendering

**How to Run:**
```powershell
cd C:\_projects\general-apps\k-espanded
uv run python debug_startup.py
```

**Expected Output:**
```
================================================================================
ESPANDED DIAGNOSTIC SCRIPT
================================================================================

1. Python Version: 3.11.x
   Platform: win32

2. Checking Dependencies...
   ✓ flet: 0.25.0
   ✓ pynput: 1.7.6
   ✓ ruamel.yaml: 0.18.x
   ✓ Pillow: 10.x.x

3. Testing pynput...
   ✓ pynput imports successfully
   ✓ Hotkey parsing works: <ctrl>+<alt>+`

4. Testing Flet...
   ✓ Flet imports successfully
   Flet version: 0.25.0

5. Testing Espanded Imports...
   ✓ espanded.core.app_state
   ✓ espanded.core.database
   [... more modules ...]

6. Testing Database Initialization...
   ✓ Database created at: ~/.espanded/espanded.db
   ✓ Settings loaded: has_imported=False

7. Testing Minimal Flet App...
   Launching test window...
   ✓ Minimal app created successfully
   ✓ Flet rendering test PASSED

================================================================================
SUMMARY
================================================================================
Dependencies: ✓ All OK
Flet Rendering: ✓ OK
```

**Interpreting Results:**

- **All ✓ checkmarks:** System is healthy, issue is elsewhere
- **✗ in Dependencies:** Run `uv sync` to install missing packages
- **✗ in Flet Rendering:** Flet installation issue, try `uv pip install --upgrade flet[all]`
- **✗ in Espanded Imports:** Code error, check stack trace

**Duration:** ~10 seconds (includes 3-second test window)

---

## 2. test_hotkeys.py

**Purpose:** Test global hotkey system and keyboard event detection.

**When to Use:**
- Global hotkey (Ctrl+Alt+`) doesn't work
- In-app hotkey recorder doesn't detect keys
- Want to verify pynput functionality
- Testing different hotkey combinations

**What It Tests:**
1. pynput import and availability
2. Hotkey parsing (4 different formats)
3. GlobalHotKeys listener with `Ctrl+Alt+E`
4. Backtick key specifically with `Ctrl+Alt+\``
5. Keyboard event listener (for in-app recording)

**How to Run:**
```powershell
# IMPORTANT: Run as Administrator for accurate results
# Right-click PowerShell > Run as Administrator

cd C:\_projects\general-apps\k-espanded
uv run python test_hotkeys.py
```

**Expected Output:**
```
================================================================================
HOTKEY SYSTEM TEST
================================================================================

1. Testing pynput import...
✓ pynput imported successfully

2. Testing hotkey parsing...
✓ <ctrl>+<alt>+` - Valid
✓ <ctrl>+<alt>+e - Valid
✓ <ctrl>+<shift>+e - Valid
✓ <ctrl>+<alt>+<space> - Valid

3. Testing GlobalHotKeys listener...
  Creating listener for: <ctrl>+<alt>+e
  Press Ctrl+Alt+E within 10 seconds to test...
✓ Listener started successfully

[When you press Ctrl+Alt+E:]
🎉 HOTKEY DETECTED! Test passed!
Stopping listener...
✓ GlobalHotKeys test PASSED

4. Testing backtick key specifically...
  Creating listener for: <ctrl>+<alt>+`
  Press Ctrl+Alt+` (backtick) within 10 seconds...

[Result varies by keyboard:]
✓ Backtick hotkey works!
  OR
⚠ Backtick hotkey not detected
  RECOMMENDATION: Use alternative hotkey like Ctrl+Alt+E

5. Testing keyboard event listener (for recording)...
  Recording next 5 key presses...
  (Type any keys now)
  Key pressed: h
  Key pressed: e
  Key pressed: l
  Key pressed: l
  Key pressed: o
✓ Recorded 5 keys: 'h', 'e', 'l', 'l', 'o'

================================================================================
SUMMARY
================================================================================
✓ Hotkey system is WORKING
```

**Interpreting Results:**

- **GlobalHotKeys test PASSED:** System works, issue might be app-specific
- **GlobalHotKeys test FAILED:**
  - Not running as Administrator → Run PowerShell as admin
  - Permission denied → Check Windows Privacy settings
  - Other app conflict → Close AutoHotkey, gaming software, etc.
- **Backtick hotkey not detected:** Use `Ctrl+Alt+E` instead
- **No keys recorded:** Keyboard permission issue, check Windows Security settings

**Duration:** ~30 seconds (includes two 10-second wait periods)

**Requirements:** Administrator privileges recommended

---

## 3. test_minimal_ui.py

**Purpose:** Test UI component rendering in isolation.

**When to Use:**
- White screen issue
- Suspect specific component is broken
- Want to verify Flet works
- Testing UI without full app initialization

**What It Tests:**
1. Absolute minimal Flet app (Text widget only)
2. Container + Column layout (Espanded's pattern)
3. Espanded component imports
4. FirstRunWizard creation
5. MainWindow creation

**How to Run:**
```powershell
cd C:\_projects\general-apps\k-espanded
uv run python test_minimal_ui.py
```

**Expected Output:**
```
================================================================================
MINIMAL UI TEST
================================================================================

1. Testing absolute minimal Flet app...
  Inside test_minimal()"
  ✓ Minimal app created
[Window opens showing "Hello World"]
✓ Minimal test completed

2. Testing Container + Column layout...
  Inside test_container_layout()
  ✓ Container layout created
[Window opens showing blue-grey container with text and button]
✓ Container test completed

3. Testing Espanded component imports...
  Importing app_state...
  ✓ app_state imported
  Importing theme...
  ✓ theme imported
  Importing MainWindow...
  ✓ MainWindow imported
  Importing FirstRunWizard...
  ✓ FirstRunWizard imported

4. Testing FirstRunWizard creation...
  Inside test_wizard()
  Creating app_state...
  ✓ app_state created
  Creating theme...
  ✓ theme_manager created
  Creating FirstRunWizard...
  ✓ wizard instance created
  Adding wizard to page...
  ✓ wizard added
  Updating page...
  ✓ page updated - UI should be visible now!
[Window opens showing first-run wizard]
✓ Wizard test completed

5. Testing MainWindow creation...
  Inside test_main_window()
  Creating app_state...
  ✓ app_state created (has_imported=True)
  Creating theme...
  ✓ theme_manager created
  Creating MainWindow...
  ✓ main_window instance created
  Adding main_window to page...
  ✓ main_window added
  Updating page...
  ✓ page updated - UI should be visible now!
[Window opens showing main application interface]
✓ Main window test completed

================================================================================
TESTING COMPLETE
================================================================================
```

**Interpreting Results:**

- **Test 1 fails:** Flet installation broken, reinstall: `uv pip install --upgrade flet[all]`
- **Test 2 fails:** Flet layout issue, check Flet version compatibility
- **Test 3 fails:** Code/import error, check stack trace for missing module
- **Test 4 fails:** FirstRunWizard has issue, check error message
- **Test 5 fails:** MainWindow has issue, check error message
- **All tests pass but main app fails:** Issue is in app.py startup flow

**Duration:** ~15 seconds (5 windows open briefly)

---

## Troubleshooting Workflow

### Problem: White Screen

1. **Run debug_startup.py**
   ```powershell
   uv run python debug_startup.py
   ```
   - If dependencies fail: `uv sync`
   - If Flet fails: `uv pip install --upgrade flet[all]`

2. **Run test_minimal_ui.py**
   ```powershell
   uv run python test_minimal_ui.py
   ```
   - Note which test fails
   - Check error message and stack trace

3. **Run actual app with verbose output**
   ```powershell
   uv run espanded
   ```
   - Look for which step fails (1-10)
   - Check error details in console

### Problem: Hotkeys Don't Work

1. **Run test_hotkeys.py AS ADMINISTRATOR**
   ```powershell
   # Right-click PowerShell > Run as Administrator
   uv run python test_hotkeys.py
   ```
   - Press `Ctrl+Alt+E` when prompted
   - Note if it works

2. **If test fails:**
   - Check Windows Settings > Privacy & Security > Input
   - Close conflicting apps (AutoHotkey, gaming software)
   - Try different hotkey

3. **If test passes but app fails:**
   - Run app as Administrator
   - Check console output for hotkey service errors
   - Verify pynput is installed: `uv pip list | grep pynput`

### Problem: In-App Recorder Shows "..."

1. **Ensure window has focus**
   - Click inside Espanded window
   - Try again

2. **Verify keyboard events work**
   - Run test_hotkeys.py test 5 (keyboard event listener)
   - Type 5 keys
   - Check if they're detected

3. **If test passes but recorder fails:**
   - This indicates white screen issue (window doesn't have proper focus)
   - Go to "White Screen" troubleshooting above

---

## Saving Diagnostic Output

To save diagnostic output for sharing:

```powershell
# Save all diagnostics
uv run python debug_startup.py > diagnostic.txt 2>&1
uv run python test_hotkeys.py > hotkeys.txt 2>&1
uv run python test_minimal_ui.py > ui_test.txt 2>&1

# View saved output
type diagnostic.txt
```

---

## Common Issues and Solutions

### "pynput not installed"
```powershell
uv pip install pynput
```

### "Permission denied" when testing hotkeys
```powershell
# Run PowerShell as Administrator
# Right-click Start > Windows PowerShell (Admin)
```

### "Flet version incompatible"
```powershell
uv pip install --upgrade flet[all]
```

### Database errors
```powershell
# Reset database
Remove-Item ~\.espanded\espanded.db -Force
uv run espanded
```

### "Module not found" errors
```powershell
# Reinstall all dependencies
uv sync --reinstall
```

---

## Additional Resources

- **QUICK_START_WINDOWS.md** - User-friendly quick reference
- **WINDOWS_FIXES.md** - Technical details on fixes applied
- **INVESTIGATION_REPORT.md** - Comprehensive analysis of issues

---

## Getting Help

If all diagnostics pass but you still have issues:

1. Collect all diagnostic outputs
2. Note error messages from app console
3. Record which diagnostic tests passed/failed
4. Include Windows version
5. List any security software or other hotkey apps running

---

## Script Maintenance

These scripts are standalone and can be run independently of the main app. They use minimal dependencies:

- `debug_startup.py` - Uses: sys, pathlib, flet, pynput, espanded modules
- `test_hotkeys.py` - Uses: sys, time, pynput only
- `test_minimal_ui.py` - Uses: sys, flet, espanded modules

Update these scripts if:
- New dependencies are added
- Core components change significantly
- New Windows-specific issues discovered
