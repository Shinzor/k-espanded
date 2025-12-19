<objective>
Migrate Espanded from Flet to PySide6 - Phase 2: Main Window and Layout Structure

Create the main window with sidebar, content area, title bar, and status bar matching the Flet layout.
</objective>

<context>
This is Phase 2 of the Flet to PySide6 migration. Phase 1 set up dependencies and the theme system.

The main window layout consists of:
- Custom title bar (frameless window with custom controls)
- Left sidebar (280px) with entry list, search, and navigation
- Right content area (expandable) for dashboard/editor/settings
- Bottom status bar with sync status and entry count

Read CLAUDE.md first for project conventions.
</context>

<research>
Before implementing, examine these files to understand current layout:
- @src/espanded/ui/main_window.py - MainWindow class, layout structure
- @src/espanded/ui/sidebar.py - Sidebar with entry list
- @src/espanded/ui/qt_theme.py - Theme manager from Phase 1
- @src/espanded/core/app_state.py - App state management
</research>

<requirements>
1. **Main Window** (`./src/espanded/ui/qt_main_window.py`)
   - Create QMainWindow subclass
   - Frameless window with custom title bar (use setWindowFlags)
   - Minimum size: 900x600
   - Default size: 1200x800
   - Apply theme colors from QtThemeManager
   - Handle window drag from title bar
   - Window controls: minimize, maximize/restore, close

2. **Layout Structure**
   - QHBoxLayout for main content area:
     - Left: Sidebar widget (fixed 280px width)
     - Right: Stacked widget for content panels (Dashboard, Editor, Settings, etc.)
   - QVBoxLayout wrapping everything:
     - Top: Title bar (40px height)
     - Middle: Main content area (expandable)
     - Bottom: Status bar (28px height)

3. **Title Bar** (`./src/espanded/ui/components/qt_title_bar.py`)
   - App icon and title "Espanded"
   - Settings gear icon button
   - Window controls (minimize, maximize, close)
   - Draggable area for window movement
   - Match dark theme styling

4. **Status Bar** (`./src/espanded/ui/components/qt_status_bar.py`)
   - Left: Sync status indicator (icon + text)
   - Right: Entry count display
   - Background: bg_sidebar color
   - Height: 28px

5. **Sidebar Container** (`./src/espanded/ui/qt_sidebar.py`)
   - Fixed width: 280px
   - Background: bg_sidebar color
   - Border: right border with border_muted color
   - Placeholder content for now (will be filled in Phase 3)
   - Sections:
     - Search bar area
     - View tabs (All, Favorites, Tags, Trash)
     - Entry list area (scrollable)
     - Add Entry button at bottom

6. **Content Area**
   - QStackedWidget to switch between views
   - Views to support (as placeholders):
     - Dashboard (index 0, default)
     - Entry Editor (index 1)
     - Settings (index 2)
     - History (index 3)
     - Trash (index 4)
</requirements>

<implementation>
Use this pattern for frameless window:

```python
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt

class QtMainWindow(QMainWindow):
    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager

        # Frameless window
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Enable custom window movement
        self._drag_pos = None

        self._setup_ui()

    def _setup_ui(self):
        colors = self.theme_manager.colors

        # Central widget with main layout
        central = QWidget()
        central.setStyleSheet(f"background-color: {colors.bg_base};")
        self.setCentralWidget(central)

        # Main vertical layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add title bar, content, status bar...
```

For window dragging:
```python
def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        self._drag_pos = event.globalPosition().toPoint()

def mouseMoveEvent(self, event):
    if self._drag_pos:
        self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
        self._drag_pos = event.globalPosition().toPoint()
```

Do NOT:
- Implement actual sidebar content yet (Phase 3)
- Implement actual content panels yet (Phase 3)
- Modify core logic files
</implementation>

<output>
Create these files:
- `./src/espanded/ui/qt_main_window.py` - Main window class
- `./src/espanded/ui/qt_sidebar.py` - Sidebar container (placeholder content)
- `./src/espanded/ui/components/qt_title_bar.py` - Custom title bar
- `./src/espanded/ui/components/qt_status_bar.py` - Status bar

Update:
- `./src/espanded/qt_app.py` - Import and show QtMainWindow
</output>

<verification>
After implementation, verify:
1. Run the app with `python -m espanded` or `python src/espanded/main.py`
2. Window should appear with dark theme
3. Custom title bar should be visible with window controls
4. Minimize, maximize, close buttons should work
5. Window should be draggable from title bar
6. Sidebar area should be visible on left (280px, darker background)
7. Content area should show placeholder
8. Status bar should be visible at bottom
</verification>

<success_criteria>
- Frameless window with custom title bar
- Window controls (min/max/close) functional
- Window draggable from title bar
- Sidebar placeholder visible (280px, dark)
- Content area visible (expandable)
- Status bar visible (28px, bottom)
- All colors match the theme palette
- No visual artifacts or layout issues
</success_criteria>
