# Phase 3: Sidebar Developer Guide

## Quick Reference

### Component Overview

| Component | Lines | Methods | Signals | Purpose |
|-----------|-------|---------|---------|---------|
| QtSidebar | 425 | 25 | 3 | Main sidebar container |
| QtSearchBar | 115 | 8 | 1 | Search input with clear button |
| QtViewTabs | 210 | 10 | 2 | View switching tabs |
| QtEntryItem | 243 | 9 | 3 | Individual entry widget |
| **Total** | **993** | **52** | **9** | **4 components** |

### Component Locations

```
src/espanded/ui/
├── qt_sidebar.py                    # Main sidebar (425 lines)
└── components/
    ├── qt_search_bar.py             # Search component (115 lines)
    ├── qt_view_tabs.py              # Tab buttons (210 lines)
    └── qt_entry_item.py             # Entry display (243 lines)
```

## Using the Sidebar

### Basic Usage

```python
from PySide6.QtWidgets import QApplication
from espanded.ui.qt_theme import QtThemeManager, ThemeSettings
from espanded.ui.qt_sidebar import QtSidebar

app = QApplication([])

# Create theme
theme_settings = ThemeSettings(theme="dark")
theme_manager = QtThemeManager(theme_settings)

# Create sidebar
sidebar = QtSidebar(theme_manager)

# Connect signals
sidebar.entry_selected.connect(lambda entry: print(f"Selected: {entry.trigger}"))
sidebar.entry_double_clicked.connect(lambda entry: print(f"Edit: {entry.trigger}"))
sidebar.add_entry_clicked.connect(lambda: print("Add new entry"))

sidebar.show()
app.exec()
```

### Signals Reference

#### QtSidebar Signals

```python
entry_selected = Signal(object)         # Emits Entry object when clicked
entry_double_clicked = Signal(object)   # Emits Entry object when double-clicked
add_entry_clicked = Signal()            # Emits when + Add Entry button clicked
```

#### QtSearchBar Signals

```python
search_changed = Signal(str)            # Emits search text on every change
```

#### QtViewTabs Signals

```python
view_changed = Signal(str)              # Emits view name: "all", "favorites", "tags", "trash"
tag_selected = Signal(str)              # Emits tag name when specific tag selected
```

#### QtEntryItem Signals

```python
clicked = Signal(str)                   # Emits entry_id on click
double_clicked = Signal(str)            # Emits entry_id on double-click
context_menu_requested = Signal(str, object)  # Emits entry_id and QPoint
```

## Public Methods

### QtSidebar

```python
# Refresh the entry list from database
sidebar.refresh_entries()

# Clear current selection
sidebar.clear_selection()

# Get currently selected entry
entry = sidebar.get_selected_entry()  # Returns Entry | None
```

### QtSearchBar

```python
# Get current search text
text = search_bar.get_text()

# Set search text programmatically
search_bar.set_text("search query")

# Clear search
search_bar.clear()
```

### QtViewTabs

```python
# Get current view
view = view_tabs.get_current_view()  # Returns "all", "favorites", "tags", or "trash"

# Set current view programmatically
view_tabs.set_current_view("trash")

# Update available tags
tags_dict = {"personal": 5, "work": 3}
view_tabs.set_available_tags(tags_dict)
```

### QtEntryItem

```python
# Set selection state
entry_item.set_selected(True)

# Check if selected
is_selected = entry_item.is_selected()

# Get entry ID
entry_id = entry_item.get_entry_id()

# Update entry data
entry_item.update_entry(new_entry)
```

## Customization

### Styling with Theme

All components use the theme manager for colors:

```python
colors = theme_manager.colors

# Available colors:
colors.primary              # Main accent color
colors.primary_hover        # Hover state
colors.bg_sidebar           # Sidebar background
colors.bg_surface           # Input backgrounds
colors.text_primary         # Primary text
colors.text_secondary       # Secondary text
colors.text_tertiary        # Muted text
colors.entry_hover          # Entry hover state
colors.entry_selected       # Entry selected state
colors.border_muted         # Subtle borders
colors.border_focus         # Focus borders
```

### Custom Styling

Override styles using Qt stylesheets:

```python
sidebar.setStyleSheet("""
    QWidget {
        background-color: #custom;
    }
""")
```

## Integration Patterns

### Observer Pattern (Auto-refresh)

The sidebar automatically refreshes when entries change:

```python
# The sidebar registers itself as a change listener
self.app_state.entry_manager.add_change_listener(self._on_entries_changed)

# Any CRUD operation triggers refresh
entry_manager.create_entry(entry)  # Sidebar auto-refreshes
entry_manager.update_entry(entry)  # Sidebar auto-refreshes
entry_manager.delete_entry(id)     # Sidebar auto-refreshes
```

### Signal/Slot Pattern

Connect sidebar signals to your handlers:

```python
def on_entry_selected(entry):
    print(f"Selected: {entry.trigger}")
    editor.load_entry(entry)

def on_entry_double_clicked(entry):
    editor.show()
    editor.edit_entry(entry)

sidebar.entry_selected.connect(on_entry_selected)
sidebar.entry_double_clicked.connect(on_entry_double_clicked)
```

## Data Flow

### Entry Loading

```
User Action (view change/search)
    ↓
QtSidebar._on_view_changed() / _on_search_changed()
    ↓
QtSidebar._load_entries()
    ├── Get entries from EntryManager based on view
    ├── Apply search filter
    ├── Update tag dropdown
    └── Call _refresh_entry_list(entries)
        ↓
        QtSidebar._refresh_entry_list()
        ├── Clear existing widgets
        ├── Create QtEntryItem for each entry
        ├── Connect signals
        └── Add to layout
```

### Entry Selection

```
User clicks entry
    ↓
QtEntryItem.mousePressEvent()
    ↓
QtEntryItem.clicked signal (entry_id)
    ↓
QtSidebar._on_entry_clicked(entry_id)
    ├── Update selection state
    ├── Update widget styles
    └── Emit entry_selected signal (Entry object)
        ↓
        MainWindow._on_entry_selected(entry)
        └── Switch to editor view
```

### Context Menu

```
User right-clicks entry
    ↓
QtEntryItem.contextMenuEvent()
    ↓
QtEntryItem.context_menu_requested signal
    ↓
QtSidebar._on_entry_context_menu()
    ├── Create QMenu
    ├── Add actions based on view
    └── Connect actions to handlers
        ↓
        Action triggered
        ↓
        QtSidebar handler (_delete_entry, _duplicate_entry, etc.)
        ↓
        EntryManager operation
        ↓
        Change notification
        ↓
        Auto-refresh sidebar
```

## Common Tasks

### Adding a New View Tab

1. Add button in `QtViewTabs._setup_ui()`:
```python
self.custom_button = self._create_tab_button(
    "\u1234 Custom",
    "custom",
    "Show custom entries"
)
layout.addWidget(self.custom_button)
```

2. Handle in `QtSidebar._load_entries()`:
```python
elif self._current_view == "custom":
    entries = self._get_custom_entries()
```

3. Update empty state in `QtSidebar._show_empty_state()`:
```python
elif self._current_view == "custom":
    message = "No custom entries"
    icon = "\u1234"
```

### Adding a Context Menu Action

In `QtSidebar._on_entry_context_menu()`:

```python
custom_action = menu.addAction("\u1234 Custom Action")
custom_action.triggered.connect(lambda: self._custom_action(entry_id))
```

Then implement the handler:

```python
def _custom_action(self, entry_id: str):
    """Handle custom action."""
    entry = self.app_state.entry_manager.get_entry(entry_id)
    # Do something with entry
```

### Adding Entry Metadata Display

In `QtEntryItem._setup_ui()`, add to layout:

```python
# Custom metadata
if hasattr(self.entry, 'custom_field'):
    custom_label = QLabel(str(self.entry.custom_field))
    custom_label.setStyleSheet(f"color: {colors.text_tertiary};")
    layout.addWidget(custom_label)
```

## Performance Considerations

### Widget Reuse

The sidebar creates new widgets on each refresh. For very large lists (1000+ entries), consider:

```python
# Instead of creating new widgets each time,
# reuse existing widgets and just update their data
if entry_id in self._entry_widgets:
    self._entry_widgets[entry_id].update_entry(entry)
else:
    widget = QtEntryItem(entry, self.theme_manager)
    self._entry_widgets[entry_id] = widget
```

### Lazy Loading

For thousands of entries, implement lazy loading:

```python
# Only load visible entries
visible_entries = entries[:50]  # First 50
self._refresh_entry_list(visible_entries)

# Load more on scroll
scroll_area.verticalScrollBar().valueChanged.connect(
    self._on_scroll
)
```

### Search Optimization

The current implementation filters in Python. For large datasets, use database filtering:

```python
# Instead of:
entries = [e for e in entries if query in e.trigger]

# Use:
entries = self.entry_manager.search_entries(query=query)
```

## Debugging

### Enable Debug Output

Add to sidebar constructor:

```python
self._debug = True

def _on_entry_clicked(self, entry_id: str):
    if self._debug:
        print(f"Entry clicked: {entry_id}")
    # ... rest of method
```

### Inspect Widget Tree

```python
def print_widget_tree(widget, indent=0):
    print("  " * indent + widget.__class__.__name__)
    for child in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
        print_widget_tree(child, indent + 1)

print_widget_tree(sidebar)
```

### Signal Debugging

```python
sidebar.entry_selected.connect(
    lambda e: print(f"Signal: entry_selected({e.trigger})")
)
```

## Testing

### Unit Testing Example

```python
from PySide6.QtWidgets import QApplication
from espanded.ui.qt_sidebar import QtSidebar

def test_sidebar_selection():
    app = QApplication([])
    sidebar = QtSidebar(theme_manager)

    # Simulate entry click
    entry_id = "test-id"
    sidebar._on_entry_clicked(entry_id)

    # Verify selection
    assert sidebar._selected_entry_id == entry_id
    assert sidebar.get_selected_entry() is not None
```

### Integration Testing Example

```python
def test_search_functionality():
    app = QApplication([])
    sidebar = QtSidebar(theme_manager)

    # Initial entry count
    initial_count = len(sidebar._entry_widgets)

    # Search
    sidebar.search_bar.set_text("test")

    # Verify filtering
    filtered_count = len(sidebar._entry_widgets)
    assert filtered_count <= initial_count
```

## Troubleshooting

### Entries Not Showing

1. Check if EntryManager has entries:
```python
entries = app_state.entry_manager.get_all_entries()
print(f"Entry count: {len(entries)}")
```

2. Check if view filter is correct:
```python
print(f"Current view: {sidebar._current_view}")
print(f"Search query: {sidebar._search_query}")
```

3. Verify layout:
```python
print(f"Widget count: {sidebar.entry_list_layout.count()}")
```

### Signals Not Firing

1. Verify connection:
```python
# Print all connections
for signal in [sidebar.entry_selected, sidebar.add_entry_clicked]:
    print(f"{signal}: {signal.receivers(signal)}")
```

2. Test signal directly:
```python
sidebar.entry_selected.emit(test_entry)
```

### Styling Not Applied

1. Check theme manager:
```python
print(f"Current theme: {theme_manager.colors.to_dict()}")
```

2. Verify stylesheet:
```python
print(sidebar.styleSheet())
```

3. Force style update:
```python
sidebar.setStyleSheet(sidebar.styleSheet())
sidebar.update()
```

## Next Steps

After Phase 3 is complete, Phase 4 will implement:
- Entry editor panel
- Form validation
- Save/Cancel functionality
- Integration with sidebar selection

See `PHASE_3_COMPLETION.md` for full implementation details.
