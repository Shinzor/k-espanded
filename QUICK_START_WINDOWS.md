# Quick Start Guide - Windows 11

## Initial Setup

1. **Open PowerShell** (Right-click Start > Windows PowerShell or Terminal)

2. **Navigate to project directory:**
   ```powershell
   cd C:\_projects\general-apps\k-espanded
   ```

3. **Install dependencies:**
   ```powershell
   uv sync
   ```

## Running Espanded

### Standard Launch
```powershell
uv run espanded
```

### With Administrator Privileges (Recommended for Hotkeys)
1. Right-click PowerShell
2. Select "Run as Administrator"
3. Navigate to project and run:
   ```powershell
   cd C:\_projects\general-apps\k-espanded
   uv run espanded
   ```

## Troubleshooting

### Problem: White/Blank Screen

**Solution 1: Check Console Output**
```powershell
uv run espanded
```
Look for error messages like:
- `✗ ERROR during initialization`
- `✗ ERROR during UI creation`

**Solution 2: Run Diagnostic**
```powershell
uv run python debug_startup.py
```
This will test:
- Dependencies
- Flet rendering
- Component imports
- Database creation

**Solution 3: Run UI Tests**
```powershell
uv run python test_minimal_ui.py
```
This will test each UI component individually.

### Problem: Hotkeys Not Working

**Solution 1: Test Hotkey System**
```powershell
# Run as Administrator!
uv run python test_hotkeys.py
```

**Solution 2: Change Hotkey**
The default backtick key (`) may not work on Windows keyboards.

1. Launch Espanded
2. Click "Settings" at bottom
3. Find "Quick Add Hotkey" section
4. Click "Record"
5. Press: `Ctrl + Alt + E`
6. Click "Test" to verify
7. Click "Save"

**Solution 3: Check Windows Settings**
1. Open Windows Settings
2. Go to Privacy & Security > Input
3. Ensure input monitoring is allowed

**Solution 4: Close Conflicting Apps**
- AutoHotkey
- Gaming software with macro support
- Other hotkey utilities

### Problem: In-App Hotkey Recorder Stuck on "..."

**Solution:**
1. Make sure Espanded window has focus (click inside it)
2. Try simple combination first: `Ctrl + Alt + E`
3. Avoid special keys like backtick, function keys on first try

## Diagnostic Scripts

### 1. Full System Diagnostic
```powershell
uv run python debug_startup.py
```
Tests everything: dependencies, Flet, pynput, database, UI components.

### 2. Hotkey System Test
```powershell
uv run python test_hotkeys.py
```
Tests global hotkeys, backtick key, keyboard recording.

### 3. UI Component Test
```powershell
uv run python test_minimal_ui.py
```
Tests UI rendering in isolation.

## Console Output Guide

### Successful Startup
You should see:
```
================================================================================
ESPANDED STARTUP - BEGIN
================================================================================
[1/10] Initializing app state...
✓ App state initialized
[2/10] Setting up page properties...
✓ Page properties set
[3/10] Loading settings...
✓ Settings loaded: theme=dark, has_imported=False
[4/10] Initializing theme manager...
✓ Theme manager created
[5/10] Applying theme to page...
✓ Theme applied to page
[6/10] Initializing hotkey service...
  Starting hotkey listener with: <ctrl>+<alt>+`
✓ Hotkey service started: <ctrl>+<alt>+` (enabled: True)
[7/10] Initializing sync manager...
✓ Sync manager skipped (not configured)
[8/10] Initializing system tray...
✓ System tray skipped (not available or disabled)
[9/10] Setting up window event handlers...
✓ Window event handlers configured
[10/10] Building UI...
  Showing first run wizard...
✓ First run wizard added to page
  Calling page.update()...
✓ Page updated successfully
================================================================================
ESPANDED STARTUP - COMPLETE
================================================================================
```

### Hotkey Service Issues
If you see:
```
⚠ Hotkey service not available (pynput not installed or failed to import)
```
or
```
Permission error starting hotkey listener
TIP: On Windows, try running as Administrator
```

**Fix:** Run PowerShell as Administrator

### UI Creation Issues
If startup stops before "COMPLETE", note which step failed and check:
- Console error message
- Stack trace (if shown)
- Run diagnostic: `uv run python debug_startup.py`

## Common Error Messages

### "pynput not installed"
```powershell
uv pip install pynput
```

### "Permission denied" or "Access denied"
Run PowerShell as Administrator

### "Flet version incompatible"
```powershell
uv pip install --upgrade flet
```

### Database errors
Delete the database file and restart:
```powershell
Remove-Item ~\.espanded\espanded.db
uv run espanded
```

## Performance Tips

1. **First Run:** May take longer due to:
   - Database creation
   - First-run wizard
   - Dependency loading

2. **Subsequent Runs:** Should be much faster

3. **If Slow:**
   - Check antivirus isn't scanning
   - Ensure Python allowed through Windows Firewall
   - Try running from SSD if available

## Getting Help

If issues persist after troubleshooting:

1. **Collect diagnostic output:**
   ```powershell
   uv run python debug_startup.py > diagnostic.txt
   uv run python test_hotkeys.py > hotkeys.txt
   ```

2. **Check console output** when running `uv run espanded`

3. **Note:**
   - Windows version
   - Error messages
   - Which diagnostic test failed
   - Console output

## Recommended Configuration for Windows

1. **Hotkey:** `Ctrl+Alt+E` (instead of default backtick)
2. **Run Mode:** Administrator (for reliable hotkey support)
3. **Espanso Path:** `%APPDATA%\espanso`

## Quick Commands Reference

```powershell
# Run app
uv run espanded

# Run diagnostics
uv run python debug_startup.py

# Test hotkeys
uv run python test_hotkeys.py

# Test UI
uv run python test_minimal_ui.py

# Update dependencies
uv sync

# Reset database
Remove-Item ~\.espanded\espanded.db
```
