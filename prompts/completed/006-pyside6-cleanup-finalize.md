<objective>
Migrate Espanded from Flet to PySide6 - Phase 6: Cleanup and Finalization

Remove all Flet code, consolidate Qt modules, update documentation, and finalize the migration.
</objective>

<context>
This is Phase 6 (cleanup) of the Flet to PySide6 migration. All functionality has been ported to PySide6 in Phases 1-5.

Now we need to:
- Remove old Flet code
- Rename Qt modules to standard names
- Update imports and references
- Update documentation
- Final testing

Read CLAUDE.md first for project conventions.
</context>

<research>
List all files that need cleanup:
- Check for any remaining Flet imports: `grep -r "import flet" src/`
- Check for any remaining Flet references: `grep -r "ft\." src/`
- List all qt_ prefixed files that need renaming
</research>

<requirements>
1. **Remove Flet Files**
   Delete these Flet-based files:
   - `./src/espanded/ui/theme.py` (replaced by qt_theme.py)
   - `./src/espanded/ui/main_window.py` (replaced by qt_main_window.py)
   - `./src/espanded/ui/sidebar.py` (replaced by qt_sidebar.py)
   - `./src/espanded/ui/dashboard.py` (replaced by qt_dashboard.py)
   - `./src/espanded/ui/entry_editor.py` (replaced by qt_entry_editor.py)
   - `./src/espanded/ui/settings_view.py` (replaced by qt_settings_view.py)
   - `./src/espanded/ui/history_view.py` (replaced by qt_history_view.py)
   - `./src/espanded/ui/trash_view.py` (replaced by qt_trash_view.py)
   - `./src/espanded/ui/quick_add.py` (replaced by qt_quick_add.py)
   - `./src/espanded/ui/first_run_wizard.py` (needs Qt version or removal)
   - `./src/espanded/app.py` (replaced by qt_app.py)
   - Any other Flet-specific files

2. **Rename Qt Modules**
   Remove qt_ prefix from filenames (they're the only version now):
   - `qt_theme.py` → `theme.py`
   - `qt_main_window.py` → `main_window.py`
   - `qt_sidebar.py` → `sidebar.py`
   - `qt_dashboard.py` → `dashboard.py`
   - `qt_entry_editor.py` → `entry_editor.py`
   - `qt_settings_view.py` → `settings_view.py`
   - `qt_history_view.py` → `history_view.py`
   - `qt_trash_view.py` → `trash_view.py`
   - `qt_quick_add.py` → `quick_add.py`
   - `qt_system_tray.py` → `system_tray.py`
   - `qt_app.py` → `app.py`

3. **Update Imports**
   After renaming, update all imports throughout the codebase:
   - `from espanded.ui.qt_main_window` → `from espanded.ui.main_window`
   - Similar for all renamed modules

4. **Update __init__.py Files**
   Update all `__init__.py` files to export the correct modules:
   - `./src/espanded/ui/__init__.py`
   - `./src/espanded/ui/components/__init__.py`
   - `./src/espanded/__init__.py`

5. **First Run Wizard**
   Either:
   - Create Qt version of first_run_wizard.py, OR
   - Remove wizard and handle first-run differently

6. **Update Documentation**
   - Update README.md with new dependencies
   - Update CLAUDE.md if needed
   - Update any other docs mentioning Flet
   - Remove any Flet-specific troubleshooting (Windows rendering workarounds)

7. **Update pyproject.toml**
   - Ensure flet is completely removed
   - Ensure PySide6 and pyqtdarktheme are present
   - Update project description if it mentions Flet

8. **Clean Up Unused Code**
   - Remove any unused utility functions
   - Remove Flet-specific workarounds in main.py
   - Remove environment variable hacks for Impeller/GPU
</requirements>

<implementation>
Use bash commands for bulk operations:

```bash
# Find remaining Flet references
grep -rn "import flet" src/
grep -rn "from flet" src/
grep -rn "ft\." src/

# Rename files (example)
mv src/espanded/ui/qt_theme.py src/espanded/ui/theme.py
mv src/espanded/ui/qt_main_window.py src/espanded/ui/main_window.py
# ... etc

# Remove old Flet files
rm src/espanded/app.py.bak  # if backup exists
```

For import updates, use search/replace:
```python
# Old
from espanded.ui.qt_main_window import QtMainWindow
# New
from espanded.ui.main_window import MainWindow
```

Also rename classes to remove Qt prefix if desired:
- `QtMainWindow` → `MainWindow`
- `QtThemeManager` → `ThemeManager`
- etc.
</implementation>

<output>
After cleanup, the file structure should be:
```
src/espanded/
├── __init__.py
├── main.py              # Entry point (Qt)
├── app.py               # App initialization (Qt)
├── core/
│   ├── app_state.py     # Unchanged
│   ├── entry_manager.py # Unchanged
│   ├── models.py        # Unchanged
│   └── ...
├── ui/
│   ├── __init__.py
│   ├── theme.py         # Qt theme manager
│   ├── main_window.py   # Qt main window
│   ├── sidebar.py       # Qt sidebar
│   ├── dashboard.py     # Qt dashboard
│   ├── entry_editor.py  # Qt entry editor
│   ├── settings_view.py # Qt settings
│   ├── history_view.py  # Qt history
│   ├── trash_view.py    # Qt trash
│   ├── quick_add.py     # Qt quick add popup
│   ├── system_tray.py   # Qt system tray
│   └── components/
│       ├── __init__.py
│       ├── title_bar.py
│       ├── status_bar.py
│       ├── entry_item.py
│       ├── search_bar.py
│       ├── view_tabs.py
│       └── hotkey_recorder.py
├── services/
│   └── hotkey_service.py # Updated for Qt
├── sync/
│   └── ...              # Unchanged
├── tray/
│   └── ...              # May be deprecated in favor of ui/system_tray.py
└── hotkeys/
    └── ...              # Unchanged
```
</output>

<verification>
Final verification checklist:
1. `grep -r "flet" src/` returns no results
2. `grep -r "ft\." src/` returns no results
3. App launches: `python -m espanded`
4. All UI panels display correctly
5. Entry CRUD operations work
6. Settings save and load
7. Theme switching works
8. Global hotkey triggers Quick Add
9. System tray works
10. Close-to-tray works
11. GitHub sync works (if configured)
12. App exits cleanly
13. No import errors
14. No console warnings about missing modules
</verification>

<success_criteria>
- Zero Flet references in codebase
- All modules have clean names (no qt_ prefix)
- All imports updated
- App fully functional
- Documentation updated
- Clean file structure
- No dead code
</success_criteria>
