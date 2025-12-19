# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Espanded is a Python desktop GUI for managing [Espanso](https://espanso.org/) text expansions. It provides cross-device sync via GitHub, global hotkeys, and a modern PySide6-based UI.

**Tech Stack**: Python 3.11+, PySide6 (Qt6), SQLite, pynput, ruamel.yaml, GitPython, httpx, pyqtdarktheme

## Commands

### Development
```bash
uv pip install -e ".[dev]"           # Install with dev tools
uv run espanded                      # Run app (Qt native desktop mode)
python -m espanded                   # Run from source
python run.py                        # Alternative run from source
```

### Testing
```bash
pytest                               # Run all tests with coverage
pytest tests/unit/                   # Unit tests only
pytest tests/unit/test_entry_manager.py  # Single test file
pytest -k "test_create"              # Run tests matching pattern
```

### Linting
```bash
ruff check .                         # Lint
ruff check . --fix                   # Lint with auto-fix
ruff format .                        # Format code
```

## Architecture

```
src/espanded/
├── core/           # Business logic & data
│   ├── models.py       # Entry, Settings, HistoryEntry dataclasses
│   ├── database.py     # SQLite persistence
│   ├── entry_manager.py # Entry CRUD with change notifications
│   ├── espanso.py      # Espanso path detection
│   └── yaml_handler.py # Espanso YAML format handling
├── sync/           # GitHub synchronization
│   ├── github_sync.py      # GitHub API client
│   ├── conflict_resolver.py # Conflict detection/resolution
│   └── sync_manager.py     # Sync orchestration
├── hotkeys/        # Global keyboard shortcuts (pynput)
├── services/       # Service facades
├── ui/             # PySide6 (Qt6) UI components
│   ├── app.py          # Qt application initialization
│   ├── theme.py        # Theme management with dark/light modes
│   ├── main_window.py  # Main window with frameless design
│   ├── sidebar.py      # Left sidebar navigation
│   ├── dashboard.py    # Entry list view
│   ├── entry_editor.py # Entry create/edit form
│   ├── settings_view.py # Settings panel
│   ├── history_view.py # History panel
│   ├── trash_view.py   # Trash panel
│   ├── quick_add.py    # Quick add popup dialog
│   ├── system_tray.py  # Qt system tray integration
│   └── components/     # Reusable UI components
│       ├── title_bar.py     # Custom window title bar
│       ├── status_bar.py    # Bottom status bar
│       ├── search_bar.py    # Search input
│       ├── view_tabs.py     # Tab navigation
│       ├── entry_item.py    # Entry list item widget
│       └── hotkey_recorder.py # Hotkey input widget
└── tray/           # Legacy system tray (deprecated, use ui/system_tray.py)
```

### Key Patterns

- **AppState Singleton** (`core/app_state.py`): Holds shared services (database, entry manager, settings)
- **Observer Pattern**: `EntryManager` supports change listeners - UI components register for notifications
- **Soft Deletes**: Entries have `deleted_at` timestamp, not hard deleted
- **Change History**: All CRUD operations logged to history table

### Data Flow

1. User action → Qt signal/slot → UI component method
2. UI → AppState service (EntryManager, SyncManager)
3. Service → Database / GitHub API
4. Change notification → Listeners → UI update (via Qt signals)

## Key Files

| Purpose | File |
|---------|------|
| CLI entry point | `src/espanded/main.py` |
| Qt app setup | `src/espanded/app.py` |
| Main window | `src/espanded/ui/main_window.py` |
| Theme system | `src/espanded/ui/theme.py` |
| Data models | `src/espanded/core/models.py` |
| Entry operations | `src/espanded/core/entry_manager.py` |
| GitHub sync | `src/espanded/sync/sync_manager.py` |
| Test fixtures | `tests/conftest.py` |

## Platform Considerations

### Windows
- Qt native desktop mode works out of the box
- Hotkey backtick (`) may have issues - Ctrl+Alt+E is more reliable
- pynput may require Administrator privileges for global hotkeys
- Diagnostic scripts available: `debug_startup.py`, `test_hotkeys.py`

### Linux/macOS
- Qt native desktop mode fully supported
- System tray requires desktop environment support (GNOME, KDE, etc.)
- Global hotkeys work with standard permissions

## Code Style

- Line length: 100 characters
- Linter: ruff (rules: E, F, I, N, W, UP)
- Full type hints throughout
- Dataclasses for data structures
- ruamel.yaml for format-preserving YAML handling
