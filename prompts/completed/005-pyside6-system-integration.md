<objective>
Migrate Espanded from Flet to PySide6 - Phase 5: System Integration

Integrate global hotkeys, system tray, and GitHub sync with the new PySide6 UI.
</objective>

<context>
This is Phase 5 (final) of the Flet to PySide6 migration. The UI is complete from Phases 1-4.

Now we need to connect the existing services (hotkeys, tray, sync) to the new Qt-based UI and ensure everything works together.

These services are mostly framework-agnostic, but some Flet-specific code needs updating.

Read CLAUDE.md first for project conventions.
</context>

<research>
Before implementing, examine these files:
- @src/espanded/services/hotkey_service.py - Global hotkey handling
- @src/espanded/hotkeys/listener.py - Pynput listener
- @src/espanded/tray/tray.py - System tray implementation
- @src/espanded/sync/sync_manager.py - GitHub sync
- @src/espanded/ui/quick_add.py - Quick add popup (Flet-based)
</research>

<requirements>
1. **Hotkey Service Integration**
   - Keep existing pynput-based listener (it's framework-agnostic)
   - Update hotkey_service.py to work without Flet
   - Connect Quick Add hotkey to new Qt popup
   - Settings panel hotkey recorder should use Qt key events
   - Hotkey enable/disable from settings

2. **Quick Add Popup** (`./src/espanded/ui/qt_quick_add.py`)
   - Frameless popup window (QDialog)
   - Always on top
   - Shows near cursor or center screen
   - Simple form:
     - Trigger input
     - Replacement text area
     - Quick tags (optional)
     - Save button
   - Keyboard shortcuts: Enter to save, Escape to cancel
   - Auto-focuses trigger field
   - Closes after save

3. **System Tray Integration**
   - Keep existing pystray implementation if possible
   - OR migrate to Qt's QSystemTrayIcon for better integration:
     ```python
     from PySide6.QtWidgets import QSystemTrayIcon, QMenu
     from PySide6.QtGui import QIcon
     ```
   - Tray menu items:
     - Show/Hide main window
     - Quick Add
     - Toggle Hotkeys
     - Separator
     - Quit
   - Left-click: show main window
   - Tray icon: app icon

4. **GitHub Sync Service**
   - Keep existing sync_manager.py (framework-agnostic)
   - Connect sync status to Qt status bar
   - Connect sync triggers to Settings panel buttons
   - Background sync updates should use Qt signals
   - Error dialogs should use QMessageBox

5. **Window Management**
   - Close to tray (if enabled in settings)
   - Minimize to tray option
   - Restore from tray click
   - Single instance enforcement (prevent multiple windows)

6. **Cleanup on Exit**
   - Stop hotkey listener
   - Stop sync manager
   - Hide/remove tray icon
   - Save settings
   - Proper Qt cleanup

7. **Error Handling**
   - Service initialization errors shown in status bar
   - Non-blocking error notifications
   - Graceful degradation (app works without hotkeys/tray)
</requirements>

<implementation>
Qt System Tray pattern:

```python
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction

class QtSystemTray:
    def __init__(self, main_window, theme_manager):
        self.main_window = main_window
        self.tray_icon = QSystemTrayIcon()

        # Set icon
        self.tray_icon.setIcon(QIcon("assets/icon.png"))
        self.tray_icon.setToolTip("Espanded")

        # Create menu
        menu = QMenu()
        show_action = QAction("Show Espanded", menu)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)

        # ... more actions

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_activated)
        self.tray_icon.show()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_window()
```

For Quick Add popup:
```python
class QtQuickAddPopup(QDialog):
    entry_created = Signal(dict)

    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self._setup_ui()

    def show_at_cursor(self):
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() - self.width() // 2,
                  cursor_pos.y() - self.height() // 2)
        self.show()
        self.trigger_input.setFocus()
```

For connecting hotkey to Qt:
```python
# In hotkey_service.py or a new Qt adapter
def on_quick_add_hotkey():
    # Use Qt's thread-safe signal mechanism
    QMetaObject.invokeMethod(
        main_window,
        "show_quick_add",
        Qt.QueuedConnection
    )
```

Do NOT:
- Rewrite core sync logic
- Change the pynput listener fundamentals
- Remove pystray support entirely (keep as fallback)
</implementation>

<output>
Create these files:
- `./src/espanded/ui/qt_quick_add.py` - Quick Add popup dialog
- `./src/espanded/ui/qt_system_tray.py` - Qt-based system tray
- `./src/espanded/ui/components/qt_hotkey_recorder.py` - Hotkey input widget

Update these files:
- `./src/espanded/services/hotkey_service.py` - Remove Flet dependencies
- `./src/espanded/qt_app.py` - Initialize tray, connect services
- `./src/espanded/ui/qt_main_window.py` - Handle close-to-tray, connect signals
</output>

<verification>
After implementation, verify:
1. Global hotkey triggers Quick Add popup
2. Quick Add popup appears near cursor
3. Quick Add creates entry and closes
4. System tray icon visible
5. Tray menu shows all options
6. Left-click tray shows main window
7. Close button minimizes to tray (if enabled)
8. Sync status shows in status bar
9. App exits cleanly (no orphan processes)
10. Single instance works (second launch focuses existing)
</verification>

<success_criteria>
- Global hotkeys work (Quick Add)
- System tray fully functional
- Quick Add popup works correctly
- Close-to-tray option works
- Sync status visible in UI
- Clean exit with no orphan processes
- All services degrade gracefully if unavailable
</success_criteria>
