<objective>
Migrate Espanded from Flet to PySide6 - Phase 3: Sidebar with Entry List

Implement the full sidebar with search, navigation tabs, scrollable entry list, and add entry button.
</objective>

<context>
This is Phase 3 of the Flet to PySide6 migration. Phase 2 created the main window layout with placeholder sidebar.

The sidebar is the primary navigation and displays all text expansion entries. It needs:
- Search functionality with real-time filtering
- View tabs to switch between All/Favorites/Tags/Trash
- Scrollable list of entries with trigger and replacement preview
- Selection highlighting
- Right-click context menu
- Add Entry button at bottom

Read CLAUDE.md first for project conventions.
</context>

<research>
Before implementing, examine these files:
- @src/espanded/ui/sidebar.py - Flet sidebar implementation
- @src/espanded/ui/qt_sidebar.py - Phase 2 placeholder
- @src/espanded/core/entry_manager.py - Entry data management
- @src/espanded/core/models.py - Entry data model
</research>

<requirements>
1. **Search Bar**
   - QLineEdit with search icon
   - Placeholder text: "Search entries..."
   - Real-time filtering as user types
   - Clear button when text present
   - Styling: bg_elevated background, rounded corners

2. **View Tabs**
   - Horizontal row of tab buttons:
     - All (icon: list)
     - Favorites (icon: star)
     - Tags (icon: label) - shows tag dropdown on click
     - Trash (icon: delete)
   - Selected tab highlighted with primary color
   - Click switches the entry list filter

3. **Entry List**
   - QListWidget or custom QScrollArea with entry widgets
   - Each entry shows:
     - Trigger text (bold, primary text color)
     - Replacement preview (truncated, secondary text color)
     - Favorite star icon (if favorited)
     - Tag indicators (small colored dots)
   - Hover: bg_elevated background
   - Selected: entry_selected background with primary border
   - Double-click: opens entry in editor
   - Right-click: context menu (Edit, Duplicate, Delete, Toggle Favorite)

4. **Entry List Item Widget** (`./src/espanded/ui/components/qt_entry_item.py`)
   - Custom QWidget for each entry
   - Layout:
     ```
     ┌─────────────────────────────────┐
     │ ★ :trigger                      │
     │   Replacement preview text...   │
     │   [tag1] [tag2]                 │
     └─────────────────────────────────┘
     ```
   - Signals: clicked, doubleClicked, contextMenuRequested

5. **Add Entry Button**
   - Fixed at bottom of sidebar
   - Full width button
   - Primary color background
   - Icon: add/plus
   - Text: "Add Entry"
   - Click: emits signal to create new entry

6. **Tag Dropdown** (when Tags tab clicked)
   - QMenu or custom popup
   - Lists all unique tags from entries
   - Click tag: filters to that tag
   - "All Tags" option to clear filter

7. **Integration with Entry Manager**
   - Load entries from app_state.entry_manager
   - Refresh list when entries change
   - Support for entry CRUD operations
   - Emit signals when selection changes
</requirements>

<implementation>
Use this pattern for the entry list:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame
from PySide6.QtCore import Signal

class QtSidebar(QWidget):
    entry_selected = Signal(str)  # entry_id
    entry_double_clicked = Signal(str)
    add_entry_clicked = Signal()

    def __init__(self, theme_manager, entry_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.entry_manager = entry_manager
        self._current_filter = "all"
        self._search_text = ""
        self._selected_entry_id = None
        self._setup_ui()
        self._load_entries()

    def _load_entries(self):
        entries = self.entry_manager.get_entries(
            filter_type=self._current_filter,
            search=self._search_text
        )
        self._populate_list(entries)
```

For custom styling:
```python
def _get_entry_item_style(self, selected=False, hover=False):
    colors = self.theme_manager.colors
    if selected:
        return f"""
            background-color: {colors.entry_selected};
            border-left: 3px solid {colors.primary};
        """
    elif hover:
        return f"background-color: {colors.entry_hover};"
    return "background-color: transparent;"
```

Do NOT:
- Implement the entry editor (Phase 4)
- Modify entry_manager core logic
- Change the Entry model
</implementation>

<output>
Create/update these files:
- `./src/espanded/ui/qt_sidebar.py` - Full sidebar implementation
- `./src/espanded/ui/components/qt_entry_item.py` - Entry list item widget
- `./src/espanded/ui/components/qt_search_bar.py` - Search input component
- `./src/espanded/ui/components/qt_view_tabs.py` - View tab buttons

Update:
- `./src/espanded/ui/qt_main_window.py` - Connect sidebar signals
</output>

<verification>
After implementation, verify:
1. Search bar filters entries in real-time
2. View tabs switch between All/Favorites/Tags/Trash
3. Entry list populates with real entries from database
4. Entries show trigger, preview, and tags
5. Click selects entry (visual feedback)
6. Double-click emits signal (check console log)
7. Right-click shows context menu
8. Add Entry button visible and clickable
9. Scrolling works when many entries
10. Empty state shows appropriate message
</verification>

<success_criteria>
- Search filters entries as user types
- View tabs switch list content
- Entries display with correct information
- Selection highlighting works
- Context menu appears on right-click
- Add Entry button functional
- Smooth scrolling performance
- Matches original Flet sidebar layout
</success_criteria>
