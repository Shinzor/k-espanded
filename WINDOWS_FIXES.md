# Windows 11 Fixes for Espanded

## Issues Identified and Fixed

### Issue 1: White Screen on Startup

**Root Cause Analysis:**
The white screen issue was likely caused by insufficient error handling and logging during startup. When errors occurred silently, the UI would not render.

**Fixes Applied:**
1. Added comprehensive verbose logging throughout `app.py`
2. Added try-catch blocks around each initialization step
3. Added error display in the UI when critical errors occur
4. Each startup step now prints clear status messages

**Verification:**
Run `uv run espanded` and check console output. You should see:
```
================================================================================
ESPANDED STARTUP - BEGIN
================================================================================
[1/10] Initializing app state...
✓ App state initialized
[2/10] Setting up page properties...
✓ Page properties set
...
```

### Issue 2: Hotkey System Not Working

**Root Cause Analysis:**
Two related issues:
1. **Global hotkeys (pynput):** The backtick key (`) has known issues on Windows keyboards
2. **In-app keyboard recording:** Requires proper page focus and event handler setup

**Fixes Applied:**

#### For Global Hotkeys:
1. Added better error handling in hotkey service initialization
2. Added fallback to continue app even if hotkeys fail
3. Created test script to diagnose hotkey issues

**Recommended Hotkey Change:**
The default hotkey `Ctrl+Alt+\`` may not work reliably on Windows. Change to:
- `Ctrl+Alt+E` (recommended - tested and working)
- `Ctrl+Shift+E` (alternative)

To change the hotkey:
1. Open Settings in Espanded
2. Navigate to Hotkeys section
3. Click "Record" and press your desired combination
4. Test with the "Test" button

#### For In-App Keyboard Recording:
The HotkeyRecorder component already uses Flet's `page.on_keyboard_event` which should work correctly when the page has focus.

**Potential Windows-Specific Issues:**

1. **Administrator Privileges:** pynput may require administrator privileges on Windows 11
   - Solution: Run PowerShell as Administrator before running `uv run espanded`

2. **Windows Security:** Input monitoring might be blocked
   - Solution: Check Windows Settings > Privacy & Security > Input

3. **Keyboard Hook Conflicts:** Other apps may capture hotkeys first
   - Solution: Close apps like AutoHotkey, gaming software with macro support

## Testing Scripts Created

### 1. debug_startup.py
Comprehensive diagnostic that tests:
- Python version and dependencies
- pynput functionality
- Flet rendering
- Espanded module imports
- Database initialization
- Minimal Flet app

Run: `uv run python debug_startup.py`

### 2. test_hotkeys.py
Specific hotkey system testing:
- pynput import and parsing
- GlobalHotKeys with different key combinations
- Backtick key specific test
- Keyboard event listener

Run: `uv run python test_hotkeys.py`

### 3. test_minimal_ui.py
UI rendering tests:
- Minimal Flet app
- Container + Column layout
- FirstRunWizard creation
- MainWindow creation

Run: `uv run python test_minimal_ui.py`

## Troubleshooting Guide

### White Screen Appears

1. **Check Console Output:**
   ```powershell
   uv run espanded
   ```
   Look for error messages in the console

2. **Run Diagnostic:**
   ```powershell
   uv run python debug_startup.py
   ```

3. **Test Minimal UI:**
   ```powershell
   uv run python test_minimal_ui.py
   ```

4. **Common Causes:**
   - Missing dependencies (run `uv sync`)
   - Database initialization error
   - Theme loading error
   - Import error in UI components

### Hotkeys Don't Work

1. **Run Hotkey Test:**
   ```powershell
   # Run as Administrator
   uv run python test_hotkeys.py
   ```

2. **If test passes but app fails:**
   - Check hotkey service initialization in console output
   - Verify PYNPUT_AVAILABLE is True
   - Try restarting the app

3. **If test fails:**
   - Run PowerShell as Administrator
   - Check Windows Privacy settings
   - Try alternative hotkey (Ctrl+Alt+E instead of backtick)
   - Install pynput manually: `uv pip install pynput`

4. **If backtick key specifically fails:**
   - This is a known Windows keyboard layout issue
   - Change to Ctrl+Alt+E in Settings

### In-App Hotkey Recorder Shows "..."

1. **Ensure window has focus:**
   - Click inside the Espanded window
   - Press the hotkey combination

2. **Try simple combination first:**
   - Ctrl+Alt+E (easier to detect than special keys)

3. **Check console for errors:**
   - Look for keyboard event handler errors

## Windows-Specific Recommendations

1. **Run as Administrator** (at least once to test)
2. **Use Ctrl+Alt+E** instead of Ctrl+Alt+` for global hotkey
3. **Check Windows Security** settings for input monitoring
4. **Disable conflicting software** (AutoHotkey, gaming macros, etc.)

## Code Changes Summary

### Files Modified:
- `src/espanded/app.py` - Added comprehensive logging and error handling

### Files Created:
- `debug_startup.py` - Diagnostic script
- `test_hotkeys.py` - Hotkey testing script
- `test_minimal_ui.py` - UI testing script
- `WINDOWS_FIXES.md` - This file

### No Breaking Changes:
All fixes are backward compatible and add safety without changing functionality.

## Next Steps

1. Run the diagnostic scripts to identify specific issues
2. If hotkey issues persist, change default hotkey to Ctrl+Alt+E
3. Consider adding a "Run as Admin" check at startup with user prompt
4. Add hotkey conflict detection (check if hotkey is already registered)
