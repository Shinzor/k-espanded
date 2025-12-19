<objective>
Migrate Espanded from Flet to PySide6 - Phase 1: Setup and Theme System

Replace the Flet framework with PySide6 to fix Windows rendering issues while preserving the dark/light theme system and color palette.
</objective>

<context>
Espanded is a desktop GUI for managing Espanso text expansions. Currently built with Flet (Flutter-based), it suffers from white/black screen rendering issues on Windows due to Flutter's Impeller engine.

PySide6 is the target framework because:
- Native Qt rendering (no Flutter/Impeller issues)
- Battle-tested on Windows
- Rich widget library
- Good dark theme support via pyqtdarktheme or qdarkstyle

Read CLAUDE.md first for project conventions.
</context>

<research>
Before implementing, examine these files to understand current structure:
- @src/espanded/main.py - Entry point and app initialization
- @src/espanded/app.py - App configuration and startup sequence
- @src/espanded/ui/theme.py - ThemeManager, ColorPalette, DARK_THEME, LIGHT_THEME
- @pyproject.toml - Current dependencies
</research>

<requirements>
1. **Update Dependencies**
   - Remove flet from pyproject.toml
   - Add PySide6 (>=6.6.0)
   - Add pyqtdarktheme for modern dark theme support
   - Keep all non-Flet dependencies (pynput, pystray, darkdetect, etc.)

2. **Create New Theme System** (`./src/espanded/ui/qt_theme.py`)
   - Port ColorPalette dataclass with all color definitions
   - Port DARK_THEME and LIGHT_THEME palettes exactly
   - Create QtThemeManager class that:
     - Detects system theme preference (use darkdetect)
     - Applies theme to QApplication
     - Supports custom color overrides from settings
     - Provides color accessors for widgets
   - Generate Qt stylesheets from color palettes

3. **Create New Entry Point** (`./src/espanded/main.py`)
   - Initialize QApplication
   - Set up high-DPI scaling
   - Apply theme before showing window
   - Handle command-line arguments (--web flag can be removed)
   - Proper cleanup on exit

4. **Create Base App Module** (`./src/espanded/qt_app.py`)
   - Replace create_app() function with Qt equivalent
   - Initialize app state (keep existing core/app_state.py)
   - Set up window properties (title, size, min size)
   - Initialize services (hotkey, sync) - just stubs for now

5. **Preserve Color Values**
   Port these exact colors from the Flet theme:
   ```python
   # Dark Theme
   primary = "#3b82f6"
   bg_base = "#0f1419"
   bg_surface = "#1a1f26"
   bg_elevated = "#242b35"
   bg_sidebar = "#151a21"
   text_primary = "#f3f4f6"
   text_secondary = "#9ca3af"
   border_default = "#2d3748"
   # ... all other colors from theme.py
   ```
</requirements>

<implementation>
Use this pattern for the Qt theme manager:

```python
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
import pyqtdarktheme

class QtThemeManager:
    def __init__(self, settings):
        self.settings = settings
        self._palette = self._load_palette()

    def apply_to_app(self, app: QApplication):
        # Use pyqtdarktheme as base, then customize
        if self.is_dark:
            pyqtdarktheme.setup_theme("dark")
        else:
            pyqtdarktheme.setup_theme("light")

        # Apply custom stylesheet for our specific colors
        app.setStyleSheet(self._generate_stylesheet())

    def _generate_stylesheet(self) -> str:
        colors = self._palette
        return f"""
            QMainWindow {{ background-color: {colors.bg_base}; }}
            QWidget {{ color: {colors.text_primary}; }}
            /* ... more styles */
        """
```

Do NOT:
- Modify any core logic files (core/*.py) - they're framework-agnostic
- Remove the web mode entirely yet - just make it optional/deprecated
- Change the settings storage format
</implementation>

<output>
Create/modify these files:
- `./pyproject.toml` - Updated dependencies
- `./src/espanded/main.py` - New Qt entry point
- `./src/espanded/qt_app.py` - New app initialization
- `./src/espanded/ui/qt_theme.py` - New Qt theme system

Keep but don't modify:
- `./src/espanded/ui/theme.py` - Keep for reference until migration complete
</output>

<verification>
After implementation, verify:
1. Run `uv sync` to install new dependencies
2. Run `python -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"`
3. Run `python -c "from espanded.ui.qt_theme import QtThemeManager; print('Theme OK')"`
4. The app should launch and show an empty dark-themed window
</verification>

<success_criteria>
- Flet removed from dependencies
- PySide6 and pyqtdarktheme added
- QtThemeManager matches Flet ThemeManager API
- All color values preserved exactly
- App launches showing empty dark window
- No import errors
</success_criteria>
