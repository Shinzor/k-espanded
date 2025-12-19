<objective>
Migrate Espanded from Flet to PySide6 - Phase 4: Content Panels

Implement all content panels: Dashboard, Entry Editor, Settings View, History View, and Trash View.
</objective>

<context>
This is Phase 4 of the Flet to PySide6 migration. Phase 3 implemented the sidebar with entry list.

Content panels appear in the right area of the main window. The QStackedWidget switches between them based on sidebar selection and navigation.

Read CLAUDE.md first for project conventions.
</context>

<research>
Before implementing, examine these files to understand each panel:
- @src/espanded/ui/dashboard.py - Dashboard with stats and tips
- @src/espanded/ui/entry_editor.py - Entry editing form
- @src/espanded/ui/settings_view.py - Settings configuration
- @src/espanded/ui/history_view.py - Usage history (if exists)
- @src/espanded/ui/trash_view.py - Deleted entries (if exists)
</research>

<requirements>
1. **Dashboard Panel** (`./src/espanded/ui/qt_dashboard.py`)
   - Header: "Dashboard" with icon
   - Statistics Card:
     - Total Entries count
     - Active Tags count
     - Last Modified date
     - Entries Today count
   - Sync Status Card:
     - Connection status (Connected/Not connected)
     - Repository name
     - Last sync time
     - "Configure Sync" or "Sync Now" button
   - Quick Tips Card:
     - List of helpful tips with lightbulb icons
   - Layout: Cards in responsive grid/flow layout

2. **Entry Editor Panel** (`./src/espanded/ui/qt_entry_editor.py`)
   - Header: "Edit Entry" / "New Entry"
   - Form fields:
     - Trigger input (with prefix selector: :, ;, //, ::, none)
     - Replacement text area (multi-line, monospace font)
     - Tags input (with autocomplete from existing tags)
     - Favorite toggle checkbox
     - Word boundary option checkbox
     - Case sensitivity option
   - Preview section showing final trigger
   - Action buttons: Save, Cancel, Delete (if editing)
   - Validation: trigger required, unique trigger check
   - Espanso variable insertion helper ({{ button)

3. **Settings Panel** (`./src/espanded/ui/qt_settings_view.py`)
   - Tabs or sections:
     - **General**:
       - Theme selector (Light/Dark/System)
       - Start minimized checkbox
       - Minimize to tray checkbox
     - **Espanso**:
       - Config path input with browse button
       - Backend selector
       - Reload config button
     - **GitHub Sync**:
       - Repository URL input
       - Token input (password field)
       - Token scope info text
       - Test connection button
       - Auto-sync toggle
       - Sync interval selector
     - **Hotkeys**:
       - Quick Add hotkey recorder
       - Enable/disable hotkeys toggle
   - Save and Cancel buttons

4. **History Panel** (`./src/espanded/ui/qt_history_view.py`)
   - Header: "Usage History"
   - List of recently used entries with timestamps
   - Filter by date range
   - Clear history button
   - Click to view entry

5. **Trash Panel** (`./src/espanded/ui/qt_trash_view.py`)
   - Header: "Trash"
   - List of deleted entries
   - Each item shows: trigger, deletion date
   - Restore button per item
   - Empty Trash button
   - Permanent delete option

6. **Integration**
   - QStackedWidget in main window manages panel switching
   - Sidebar signals connect to panel switching
   - Entry selection loads entry in editor
   - Settings changes save to app_state
</requirements>

<implementation>
Use this pattern for panels:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea

class QtDashboard(QWidget):
    def __init__(self, theme_manager, app_state):
        super().__init__()
        self.theme_manager = theme_manager
        self.app_state = app_state
        self._setup_ui()

    def _setup_ui(self):
        colors = self.theme_manager.colors
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = self._create_content()
        scroll.setWidget(content)
        layout.addWidget(scroll)
```

For cards:
```python
def _create_card(self, title: str, content: QWidget) -> QFrame:
    colors = self.theme_manager.colors
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {colors.bg_surface};
            border: 1px solid {colors.border_muted};
            border-radius: 12px;
        }}
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 20, 20, 20)
    # Add title and content...
    return card
```

Do NOT:
- Modify core logic (entry_manager, app_state, models)
- Change settings storage format
- Implement actual sync logic (just UI)
</implementation>

<output>
Create these files:
- `./src/espanded/ui/qt_dashboard.py` - Dashboard panel
- `./src/espanded/ui/qt_entry_editor.py` - Entry editor panel
- `./src/espanded/ui/qt_settings_view.py` - Settings panel
- `./src/espanded/ui/qt_history_view.py` - History panel
- `./src/espanded/ui/qt_trash_view.py` - Trash panel

Update:
- `./src/espanded/ui/qt_main_window.py` - Add panels to stacked widget, connect signals
</output>

<verification>
After implementation, verify:
1. Dashboard shows with correct stats from app_state
2. Dashboard cards styled correctly
3. Entry editor loads when entry selected
4. Entry editor saves/updates entries correctly
5. Settings panel shows all sections
6. Settings changes persist
7. Theme change applies immediately
8. History panel lists recent usage
9. Trash panel shows deleted entries
10. Restore from trash works
11. Panel switching is smooth (no flicker)
</verification>

<success_criteria>
- All 5 panels implemented and functional
- Dashboard shows real statistics
- Entry editor can create/edit/delete entries
- Settings persist correctly
- Theme switching works
- Panel transitions smooth
- Layout matches original Flet design
- All form validation works
</success_criteria>
