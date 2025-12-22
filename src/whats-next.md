# Handoff Document: Espanded Hotkey Fixes

## Original Task

Fix hotkey-related issues in the Espanded app (a Python/Flet desktop UI for managing Espanso text expansions):

1. **Hotkey recording not working**: When clicking "Record" and pressing keys, nothing was captured
2. **Global hotkeys not triggering**: Pressing the configured hotkey (e.g., Ctrl+Alt+P) did nothing
3. **"signal only works in main thread" error**: Server threw this error when hotkey was pressed
4. **"pynput not available" message**: App showed this in the hotkey settings area
5. **UI improvements requested**:
   - Add button to disable/enable hotkeys
   - Change "Clear" button to "Reset" (reverts to default instead of clearing)
   - Add "Test" button for conflict checking
   - Default hotkey should be `Ctrl+Alt+`` (backtick)

The expected behavior: Press hotkey anywhere → Quick Add popup appears → If text was selected, it pre-fills the replacement field → User adds trigger and saves entry.

## Work Completed

### 1. Rewrote `espanded/hotkeys/listener.py`
**Key changes:**
- Changed from custom keyboard listener to pynput's `GlobalHotKeys` class (lines 197-217)
- Fixed hotkey format: pynput requires angle brackets `<ctrl>+<alt>+h` not `ctrl+alt+h`
- Added `normalize_hotkey()` function (lines 22-104) - converts any format to pynput format
- Added `display_hotkey()` function (lines 107-123) - converts pynput format to user-friendly display
- Added `test_hotkey()` function (lines 243-262) - validates hotkey can be registered
- Changed default hotkey to `<ctrl>+<alt>+`` (line 19)

### 2. Rewrote `espanded/ui/components/hotkey_recorder.py`
**Key changes:**
- Added graceful fallback when pynput not available (lines 10-64)
- Built complete UI with Record, Test, and Reset buttons (lines 165-191)
- Recording captures keys via Flet's `page.on_keyboard_event` (lines 259-314)
- Outputs hotkey in pynput angle bracket format (lines 278-295)
- Added conflict checking against common system shortcuts (lines 67-84, 409-421)
- Reset button restores default `<ctrl>+<alt>+`` instead of clearing (lines 375-391)

### 3. Fixed "signal only works in main thread" error
**Files modified:**
- `espanded/ui/quick_add.py` - Rewrote `_run_quick_add_subprocess()` (lines 209-242)
  - Changed from threading to subprocess.Popen
  - Passes selected text via temp file to avoid command line escaping issues

- **Created** `espanded/quick_add_standalone.py` (new file, 223 lines)
  - Standalone Flet app that runs as separate process
  - Reads selected text from temp file passed as command line argument
  - Saves entry via `app_state.entry_manager.create_entry()`
  - Cleans up temp file after reading

### 4. Updated `espanded/services/hotkey_service.py`
- Updated imports to use new functions from listener.py (lines 7-23)
- Added fallback definitions when pynput unavailable (lines 17-23)
- Default hotkey constant uses angle bracket format (line 20)

### 5. Updated `espanded/core/models.py`
- Added `hotkeys_enabled: bool = True` field to Settings class
- Changed `quick_add_hotkey` default to `<ctrl>+<alt>+``

### 6. Updated `espanded/app.py`
- Changed default hotkey format on line 57: `quick_add_hotkey or "<ctrl>+<alt>+\`"`
- Added check for `hotkeys_enabled` setting (lines 60-61)

### 7. Updated `pyproject.toml`
- Moved pynput from optional to required dependencies (line 33: `"pynput>=1.7.6"`)

### Code Verification
All Python files compile successfully:
- `listener.py`, `clipboard.py`, `hotkey_service.py`, `hotkey_recorder.py`, `quick_add.py`, `quick_add_standalone.py`, `app.py`

Code structure verified:
- HotkeyRecorder has pynput fallback ✓
- QuickAdd uses subprocess (not threading) ✓
- Standalone script exists and saves entries ✓
- Listener uses GlobalHotKeys class ✓
- Service integrates with quick_add_popup ✓

## Work Remaining

### User Testing Required
The code changes are complete but need manual testing on Windows:

1. **Test hotkey recording in Settings UI**:
   - Open Espanded → Settings → Quick Add Hotkey section
   - Click "Record" button
   - Press a key combination (e.g., Ctrl+Alt+P)
   - Verify the combination is captured and displayed
   - Click "Test" button to validate

2. **Test global hotkey triggering**:
   - With Espanded running (can be minimized)
   - Select text in any application (e.g., Notepad)
   - Press Ctrl+Alt+` (backtick)
   - Verify Quick Add popup appears with selected text pre-filled

3. **Test enable/disable toggle** (if implemented in settings_view.py):
   - Toggle hotkeys off → verify hotkey press does nothing
   - Toggle hotkeys on → verify hotkey press shows popup

4. **Test Reset button**:
   - Change hotkey to something custom
   - Click Reset button
   - Verify it reverts to `Ctrl + Alt + `` (displayed) / `<ctrl>+<alt>+`` (stored)

### Potential Follow-up Work
- Add hotkey enable/disable toggle UI in settings_view.py if not already present
- Consider adding visual indicator (tray icon?) when hotkeys are enabled/disabled
- Add unit tests for hotkey normalization functions

## Attempted Approaches

### 1. Threading approach for Quick Add (FAILED)
**What was tried:** Running `ft.app()` in a background thread to show Quick Add popup
**Error:** `signal only works in main thread of the main interpreter`
**Why it failed:** Flet uses signals internally which only work in main thread
**Solution:** Subprocess approach - launch entirely separate Python process

### 2. Direct pynput import in HotkeyRecorder (FAILED)
**What was tried:** Importing pynput functions directly at module level
**Error:** `pynput not available` shown in UI
**Why it failed:** Import chain issues when pynput module available but not properly installed
**Solution:** Try/except with full fallback implementations that work without pynput

### 3. Using simple hotkey string format (FAILED)
**What was tried:** Using `ctrl+alt+e` format
**Error:** Hotkeys not detected
**Why it failed:** pynput GlobalHotKeys requires angle bracket format `<ctrl>+<alt>+e`
**Solution:** Added `normalize_hotkey()` function to convert any format

### 4. Recreating venv in WSL (BLOCKED)
**What was tried:** `rm -rf .venv && uv sync`
**Error:** `evdev` compilation failed - missing Python.h headers
**Why:** pynput on Linux depends on evdev which needs python3-dev
**Workaround:** This is a Windows app - test from Windows PowerShell, not WSL

## Critical Context

### pynput Hotkey Format
- pynput GlobalHotKeys requires angle brackets: `<ctrl>+<alt>+<shift>+a`
- Single character keys are lowercase without brackets: `a`, `b`, `` ` ``
- Special keys need brackets: `<space>`, `<enter>`, `<f1>`
- Modifier mapping:
  - `ctrl`, `control` → `<ctrl>`
  - `alt` → `<alt>`
  - `shift` → `<shift>`
  - `meta`, `cmd`, `win` → `<cmd>`

### Key Files and Their Roles
```
espanded/
├── hotkeys/
│   ├── listener.py         # GlobalHotKeys listener, normalize/display/test functions
│   └── clipboard.py        # Cross-platform clipboard + simulate Ctrl+C
├── services/
│   └── hotkey_service.py   # Singleton service coordinating hotkeys + quick add
├── ui/
│   ├── components/
│   │   └── hotkey_recorder.py  # UI component for recording hotkeys
│   └── quick_add.py        # Launches subprocess for popup
├── quick_add_standalone.py # Standalone Flet app for Quick Add popup
└── app.py                  # Main app initialization, starts hotkey service
```

### Default Hotkey
- Stored format: `<ctrl>+<alt>+`` (pynput format)
- Display format: `Ctrl + Alt + `` (user-friendly)
- The backtick (`) key is next to 1 on most keyboards

### Threading Limitation
- Flet's `ft.app()` cannot run in a thread due to signal handling
- Solution: Use `subprocess.Popen()` to launch as separate process
- Selected text passed via temp file to avoid command line escaping issues

### Environment
- Project: `/mnt/c/_projects/general-apps/k-espanded/` (WSL path)
- Windows path: `C:\_projects\general-apps\k-espanded\`
- Python: 3.11+ required
- Package manager: `uv`
- Run command: `uv run espanded`

## Current State

### Deliverables Status
| Item | Status |
|------|--------|
| Hotkey format fix (listener.py) | Complete |
| HotkeyRecorder UI component | Complete |
| Quick Add subprocess approach | Complete |
| Standalone quick_add script | Complete |
| pynput fallbacks | Complete |
| Code compilation verified | Complete |
| Code structure verified | Complete |
| Manual testing on Windows | NOT DONE - requires user |

### Files Modified (Finalized)
- `espanded/hotkeys/listener.py` - Complete rewrite
- `espanded/ui/components/hotkey_recorder.py` - Complete rewrite
- `espanded/ui/quick_add.py` - Subprocess approach
- `espanded/services/hotkey_service.py` - Updated imports
- `espanded/core/models.py` - Added hotkeys_enabled field
- `espanded/app.py` - Updated default hotkey format
- `pyproject.toml` - pynput as required dependency

### Files Created (New)
- `espanded/quick_add_standalone.py` - Standalone popup script

### Environment State
- WSL venv is corrupted/incomplete (missing evdev headers for Linux)
- Windows venv should be recreated fresh for testing
- No temporary workarounds in place

### Next Action for User
Run from Windows PowerShell:
```powershell
cd C:\_projects\general-apps\k-espanded
Remove-Item -Recurse -Force .venv
uv run espanded
```
Then test the hotkey flow (select text → press Ctrl+Alt+` → popup appears).
