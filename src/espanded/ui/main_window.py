"""Main window layout with sidebar and content pane."""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QLabel,
    QApplication,
)
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QMouseEvent

from espanded.ui.theme import ThemeManager
from espanded.ui.sidebar import Sidebar
from espanded.ui.components.title_bar import TitleBar
from espanded.ui.components.status_bar import StatusBar
from espanded.ui.components.message_dialog import (
    show_information,
    show_critical,
)
from espanded.ui.icon import create_app_icon
from espanded.ui.dashboard import Dashboard
from espanded.ui.entry_editor import EntryEditor
from espanded.ui.settings_view import SettingsView
from espanded.ui.history_view import HistoryView
from espanded.ui.trash_view import TrashView
from espanded.ui.quick_add import QuickAddPopup
from espanded.core.app_state import get_app_state
from espanded.core.models import Entry


class MainWindow(QMainWindow):
    """Main application window with frameless design and two-pane layout."""

    # Signal for cross-thread communication (hotkey triggers from background thread)
    _quick_add_signal = Signal(str)

    def __init__(self, theme_manager: ThemeManager, tray=None, hotkey_service=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.app_state = get_app_state()
        self.tray = tray
        self.hotkey_service = hotkey_service

        # Window drag state
        self._drag_pos: QPoint | None = None
        self._is_maximized = False

        # Window resize state (using integer flags for edges)
        self._resize_edge: int = 0
        self._resize_start_pos: QPoint | None = None
        self._resize_start_geom: tuple | None = None  # (x, y, w, h)
        self._resize_margin = 8  # Pixels from edge to detect resize

        # Edge flags
        self.EDGE_NONE = 0
        self.EDGE_LEFT = 1
        self.EDGE_RIGHT = 2
        self.EDGE_TOP = 4
        self.EDGE_BOTTOM = 8

        # Quick add popup reference (to prevent garbage collection)
        self._quick_add_popup = None

        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._connect_tray_signals()
        self._connect_hotkey_service()

    def _setup_window(self):
        """Configure window properties."""
        # Frameless window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Enable mouse tracking for resize cursor updates
        self.setMouseTracking(True)

        # Set window icon
        self.setWindowIcon(create_app_icon())

        # Window size
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)

        # Apply theme
        colors = self.theme_manager.colors
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors.bg_base};
            }}
        """)

    def _setup_ui(self):
        """Build the main window layout."""
        colors = self.theme_manager.colors

        # Central widget
        central_widget = QWidget()
        central_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_base};
            }}
        """)
        self.setCentralWidget(central_widget)

        # Main vertical layout (title bar + content + status bar)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        self.title_bar = TitleBar(self.theme_manager)
        main_layout.addWidget(self.title_bar)

        # Content area (horizontal layout: sidebar + content)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self.theme_manager)
        content_layout.addWidget(self.sidebar)

        # Content pane (stacked widget for different views)
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {colors.bg_base};
            }}
        """)

        # Create placeholder content panels
        self._create_content_panels()

        content_layout.addWidget(self.content_stack, stretch=1)

        main_layout.addWidget(content_widget, stretch=1)

        # Status bar
        self.status_bar = StatusBar(self.theme_manager)
        main_layout.addWidget(self.status_bar)

        # Initial entry count
        self.status_bar.update_entry_count()

    def _create_content_panels(self):
        """Create content panels."""
        # Dashboard (index 0, default)
        self.dashboard = Dashboard(self.theme_manager)
        self.dashboard.sync_clicked.connect(self._on_sync_now)
        self.dashboard.settings_clicked.connect(self._on_settings)
        self.content_stack.addWidget(self.dashboard)

        # Entry Editor (index 1)
        self.entry_editor = EntryEditor(self.theme_manager)
        self.entry_editor.entry_saved.connect(self._on_entry_saved)
        self.entry_editor.entry_deleted.connect(self._on_entry_deleted)
        self.entry_editor.entry_cloned.connect(self._on_entry_cloned)
        self.entry_editor.close_requested.connect(self.show_dashboard)
        self.content_stack.addWidget(self.entry_editor)

        # Settings (index 2)
        self.settings_view = SettingsView(self.theme_manager)
        self.settings_view.close_requested.connect(self.show_dashboard)
        self.settings_view.theme_changed.connect(self._on_theme_changed)
        self.settings_view.settings_saved.connect(self._on_settings_saved)
        self.content_stack.addWidget(self.settings_view)

        # History (index 3)
        self.history_view = HistoryView(self.theme_manager)
        self.history_view.close_requested.connect(self.show_dashboard)
        self.history_view.entry_restored.connect(self._on_entry_restored)
        self.content_stack.addWidget(self.history_view)

        # Trash (index 4)
        self.trash_view = TrashView(self.theme_manager)
        self.trash_view.close_requested.connect(self.show_dashboard)
        self.trash_view.entry_restored.connect(self._on_entry_restored)
        self.content_stack.addWidget(self.trash_view)

        # Set default view (Dashboard)
        self.content_stack.setCurrentIndex(0)

    def _connect_signals(self):
        """Connect signals and slots."""
        # Title bar signals
        self.title_bar.minimize_clicked.connect(self._on_minimize)
        self.title_bar.maximize_clicked.connect(self._on_maximize)
        self.title_bar.close_clicked.connect(self._on_close)
        self.title_bar.settings_clicked.connect(self._on_settings)
        self.title_bar.title_clicked.connect(self.show_dashboard)

        # Sidebar signals
        self.sidebar.entry_selected.connect(self._on_entry_selected)
        self.sidebar.entry_double_clicked.connect(self._on_entry_double_clicked)
        self.sidebar.add_entry_clicked.connect(self._on_add_entry)

    def _on_minimize(self):
        """Handle minimize button click."""
        self.showMinimized()

    def _on_maximize(self):
        """Handle maximize/restore button click."""
        if self._is_maximized:
            self.showNormal()
            self._is_maximized = False
        else:
            self.showMaximized()
            self._is_maximized = True
        self.title_bar.update_maximize_button(self._is_maximized)

    def _on_close(self):
        """Handle close button click."""
        # Check if we should minimize to tray instead of closing
        if self.tray and self.app_state.settings.minimize_to_tray:
            self.hide()
            if self.tray:
                self.tray.show_notification(
                    "Espanded",
                    "Espanded is still running in the system tray",
                    2000,
                )
        else:
            self.close()

    def _on_settings(self):
        """Handle settings button click."""
        self.content_stack.setCurrentIndex(2)  # Settings view
        self.sidebar.clear_selection()

    def _on_entry_selected(self, entry: Entry):
        """Handle entry selection from sidebar."""
        # Show entry in editor (view mode initially)
        self.entry_editor.set_entry(entry)
        self.content_stack.setCurrentIndex(1)

    def _on_entry_double_clicked(self, entry: Entry):
        """Handle entry double-click from sidebar."""
        # Open entry in editor for editing
        self.entry_editor.set_entry(entry)
        self.content_stack.setCurrentIndex(1)

    def _on_add_entry(self):
        """Handle add entry button click."""
        # Open editor with new entry
        self.entry_editor.set_entry(None)
        self.content_stack.setCurrentIndex(1)

    def _on_entry_saved(self, entry: Entry):
        """Handle entry save from editor."""
        try:
            # Save or update entry
            if self.app_state.entry_manager.get_entry(entry.id):
                # Update existing
                self.app_state.entry_manager.update_entry(entry)
            else:
                # Create new
                self.app_state.entry_manager.create_entry(entry)

            # Refresh views
            self.sidebar.refresh_entries()
            self.status_bar.update_entry_count()
            self.dashboard.refresh_stats()

            # Go back to dashboard
            self.show_dashboard()

        except Exception as ex:
            show_critical(
                self.theme_manager,
                "Save Error",
                f"Failed to save entry: {str(ex)}",
                parent=self,
            )

    def _on_entry_deleted(self, entry: Entry):
        """Handle entry delete from editor."""
        # Delete entry (soft delete)
        self.app_state.entry_manager.delete_entry(entry.id)

        # Refresh views
        self.sidebar.refresh_entries()
        self.status_bar.update_entry_count()
        self.dashboard.refresh_stats()

        # Go back to dashboard
        self.show_dashboard()

    def _on_entry_cloned(self, entry: Entry):
        """Handle entry clone from editor."""
        # Clone entry
        new_entry = self.app_state.entry_manager.clone_entry(entry.id)

        if new_entry:
            # Show new entry in editor
            self.entry_editor.set_entry(new_entry)

    def _on_entry_restored(self, entry_id: str):
        """Handle entry restore from trash/history."""
        # Refresh views
        self.sidebar.refresh_entries()
        self.status_bar.update_entry_count()
        self.dashboard.refresh_stats()
        self.trash_view.refresh()
        self.history_view.refresh()

    def _on_sync_now(self):
        """Handle sync now button from dashboard."""
        # Check if sync is configured
        if not self.app_state.sync_manager:
            show_information(
                self.theme_manager,
                "Sync Not Configured",
                "GitHub sync is not configured. Go to Settings to set it up.",
                parent=self,
            )
            return

        try:
            # Perform sync
            result = self.app_state.sync_manager.sync()

            if result.get("success"):
                # Import any pulled files
                if result.get('pulled', 0) > 0:
                    imported_count = self.app_state.entry_manager.import_from_espanso()

                    # Refresh all UI components
                    self.sidebar.refresh_entries()
                    self.status_bar.update_entry_count()
                    self.dashboard.refresh_stats()

                show_information(
                    self.theme_manager,
                    "Sync Complete",
                    f"Sync completed successfully.\n\nPulled: {result.get('pulled', 0)} changes\nPushed: {result.get('pushed', 0)} changes",
                    parent=self,
                )
            else:
                show_critical(
                    self.theme_manager,
                    "Sync Failed",
                    f"Sync failed: {result.get('error', 'Unknown error')}",
                    parent=self,
                )
        except Exception as ex:
            show_critical(
                self.theme_manager,
                "Sync Error",
                f"Error during sync: {str(ex)}",
                parent=self,
            )

    def _on_theme_changed(self):
        """Handle theme change from settings."""
        # Reload theme
        self.theme_manager.set_theme(self.app_state.settings.theme)
        self.theme_manager.apply_to_app(QApplication.instance())

        # Refresh all views (theme colors updated)
        show_information(
            self.theme_manager,
            "Theme Changed",
            "Theme has been changed. Please restart the application for full effect.",
            parent=self,
        )

    def _on_settings_saved(self):
        """Handle settings save."""
        # Refresh dashboard stats (in case sync settings changed)
        self.dashboard.refresh_stats()

    def show_dashboard(self):
        """Switch to dashboard view."""
        self.content_stack.setCurrentIndex(0)
        self.sidebar.clear_selection()

    def navigate_to_settings(self):
        """Navigate to settings view."""
        self._on_settings()

    def show_editor(self, entry: Entry | None = None):
        """Switch to entry editor view."""
        self.entry_editor.set_entry(entry)
        self.content_stack.setCurrentIndex(1)

    def show_history(self):
        """Switch to history view."""
        self.history_view.refresh()
        self.content_stack.setCurrentIndex(3)
        self.sidebar.clear_selection()

    def show_trash(self):
        """Switch to trash view."""
        self.trash_view.refresh()
        self.content_stack.setCurrentIndex(4)
        self.sidebar.clear_selection()

    def _connect_tray_signals(self):
        """Connect system tray signals."""
        if not self.tray:
            return

        self.tray.show_requested.connect(self._on_tray_show)
        self.tray.quick_add_requested.connect(self.show_quick_add)
        self.tray.hotkeys_toggled.connect(self._on_tray_hotkeys_toggled)
        self.tray.quit_requested.connect(self.quit_application)

        # Show the tray icon
        self.tray.show()

    def _connect_hotkey_service(self):
        """Connect hotkey service callbacks."""
        if not self.hotkey_service:
            return

        # Connect our signal to the show_quick_add slot (Qt handles thread-safety via queued connection)
        self._quick_add_signal.connect(self.show_quick_add)

        # Set up callback for quick add hotkey - emit signal from background thread
        def on_quick_add(selected_text: str):
            # Emit signal - Qt will queue this to the main thread automatically
            print(f"[MainWindow] Emitting _quick_add_signal with text: {selected_text[:30] if selected_text else '(empty)'}...")
            self._quick_add_signal.emit(selected_text)

        self.hotkey_service.set_callbacks(on_quick_add=on_quick_add)

    def _on_tray_show(self):
        """Handle show window from tray."""
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_tray_hotkeys_toggled(self, enabled: bool):
        """Handle hotkey toggle from tray."""
        if self.hotkey_service:
            if enabled:
                self.hotkey_service.enable()
            else:
                self.hotkey_service.disable()
            self.status_bar.update_sync_status(
                f"Hotkeys {'enabled' if enabled else 'disabled'}",
                is_syncing=False,
            )

    def show_quick_add(self, selected_text: str = ""):
        """Show quick add popup.

        Args:
            selected_text: Pre-filled text from selection
        """
        print("[MainWindow] show_quick_add called")
        try:
            # Store popup as instance variable to prevent garbage collection
            self._quick_add_popup = QuickAddPopup(self.theme_manager, selected_text, self)
            self._quick_add_popup.entry_created.connect(self._on_quick_add_entry_created)
            self._quick_add_popup.finished.connect(self._on_quick_add_finished)
            print("[MainWindow] QuickAddPopup created, showing at cursor...")
            self._quick_add_popup.show_at_cursor()
            print("[MainWindow] QuickAddPopup show_at_cursor() completed")
        except Exception as e:
            print(f"[MainWindow] ERROR showing quick add popup: {e}")
            import traceback
            traceback.print_exc()

    def _on_quick_add_finished(self, result: int):
        """Handle quick add popup closed."""
        # Clear reference to allow garbage collection
        self._quick_add_popup = None

    def _on_quick_add_entry_created(self, entry: Entry):
        """Handle entry created from quick add popup."""
        # Refresh views
        self.sidebar.refresh_entries()
        self.status_bar.update_entry_count()
        self.dashboard.refresh_stats()

        # Show notification
        if self.tray:
            self.tray.show_notification(
                "Entry Created",
                f"Created trigger: {entry.trigger}",
                2000,
            )

    def quit_application(self):
        """Quit the application completely (used by tray quit action)."""
        # Close the window (this will trigger cleanup)
        QApplication.instance().quit()

    def closeEvent(self, event):
        """Handle window close event."""
        # If minimize to tray is enabled, hide instead of close
        if self.tray and self.app_state.settings.minimize_to_tray:
            event.ignore()
            self.hide()
            if self.tray:
                self.tray.show_notification(
                    "Espanded",
                    "Espanded is still running in the system tray",
                    2000,
                )
        else:
            # Normal close - accept the event
            event.accept()

    def _get_resize_edge(self, pos: QPoint) -> int:
        """Determine which edge(s) the mouse is near for resizing.

        Returns:
            Combination of edge flags, or 0 if not near any edge
        """
        if self._is_maximized:
            return 0

        edge = 0
        margin = self._resize_margin

        if pos.x() <= margin:
            edge |= self.EDGE_LEFT
        elif pos.x() >= self.width() - margin:
            edge |= self.EDGE_RIGHT

        if pos.y() <= margin:
            edge |= self.EDGE_TOP
        elif pos.y() >= self.height() - margin:
            edge |= self.EDGE_BOTTOM

        return edge

    def _update_cursor_for_resize(self, edge: int):
        """Update cursor shape based on resize edge."""
        if edge == 0:
            self.unsetCursor()
        elif edge == (self.EDGE_TOP | self.EDGE_LEFT) or edge == (self.EDGE_BOTTOM | self.EDGE_RIGHT):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge == (self.EDGE_TOP | self.EDGE_RIGHT) or edge == (self.EDGE_BOTTOM | self.EDGE_LEFT):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edge & (self.EDGE_LEFT | self.EDGE_RIGHT):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge & (self.EDGE_TOP | self.EDGE_BOTTOM):
            self.setCursor(Qt.CursorShape.SizeVerCursor)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for window dragging and resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check for resize edge first
            edge = self._get_resize_edge(event.pos())
            if edge != 0:
                self._resize_edge = edge
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geom = (self.x(), self.y(), self.width(), self.height())
                return

            # Otherwise, check for dragging from title bar
            title_bar_rect = self.title_bar.geometry()
            if title_bar_rect.contains(event.pos()):
                self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for window dragging, resizing, and cursor updates."""
        # If resizing
        if self._resize_edge != 0 and self._resize_start_pos is not None:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            x, y, w, h = self._resize_start_geom

            new_x, new_y = x, y
            new_w, new_h = w, h

            if self._resize_edge & self.EDGE_LEFT:
                new_x = x + delta.x()
                new_w = w - delta.x()
            elif self._resize_edge & self.EDGE_RIGHT:
                new_w = w + delta.x()

            if self._resize_edge & self.EDGE_TOP:
                new_y = y + delta.y()
                new_h = h - delta.y()
            elif self._resize_edge & self.EDGE_BOTTOM:
                new_h = h + delta.y()

            # Enforce minimum size
            min_w = self.minimumWidth()
            min_h = self.minimumHeight()

            if new_w < min_w:
                if self._resize_edge & self.EDGE_LEFT:
                    new_x = x + w - min_w
                new_w = min_w

            if new_h < min_h:
                if self._resize_edge & self.EDGE_TOP:
                    new_y = y + h - min_h
                new_h = min_h

            self.setGeometry(new_x, new_y, new_w, new_h)
            return

        # If dragging
        if self._drag_pos is not None and not self._is_maximized:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            return

        # Update cursor based on edge proximity
        edge = self._get_resize_edge(event.pos())
        self._update_cursor_for_resize(edge)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to stop dragging and resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            self._resize_edge = 0
            self._resize_start_pos = None
            self._resize_start_geom = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click on title bar to maximize/restore."""
        # Check if double-click is within title bar bounds
        title_bar_rect = self.title_bar.geometry()
        if title_bar_rect.contains(event.pos()):
            self._on_maximize()
