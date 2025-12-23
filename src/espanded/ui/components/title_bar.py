"""Custom title bar for frameless window."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap

from espanded.ui.theme import ThemeManager


class TitleBar(QWidget):
    """Custom title bar with window controls."""

    # Signals
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()
    settings_clicked = Signal()
    title_clicked = Signal()  # Navigate to dashboard

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFixedHeight(40)
        self._setup_ui()

    def _setup_ui(self):
        """Build the title bar layout."""
        colors = self.theme_manager.colors

        # Set background
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_surface};
                border-bottom: 1px solid {colors.border_muted};
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 6px 8px;
                color: {colors.text_secondary};
            }}
            QPushButton:hover {{
                background-color: {colors.entry_hover};
            }}
            QPushButton#closeButton:hover {{
                background-color: {colors.error};
                color: white;
            }}
        """)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        # App title (clickable to return to dashboard)
        self.title_button = QPushButton("Espanded")
        self.title_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_button.setStyleSheet(f"""
            QPushButton {{
                color: {colors.text_primary};
                font-size: 14px;
                font-weight: 600;
                background-color: transparent;
                border: none;
                padding: 6px 8px;
                text-align: left;
            }}
            QPushButton:hover {{
                color: {colors.primary};
                background-color: {colors.entry_hover};
            }}
        """)
        self.title_button.clicked.connect(self.title_clicked.emit)
        layout.addWidget(self.title_button)

        # Spacer (draggable area)
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addItem(spacer)

        # Settings button
        self.settings_button = QPushButton("\u2699")  # Gear icon
        self.settings_button.setToolTip("Settings")
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_button)

        # Window control buttons
        # Minimize
        self.minimize_button = QPushButton("\u2500")  # Minus
        self.minimize_button.setToolTip("Minimize")
        self.minimize_button.setFixedSize(32, 32)
        self.minimize_button.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.minimize_button)

        # Maximize/Restore
        self.maximize_button = QPushButton("\u25a1")  # Square
        self.maximize_button.setToolTip("Maximize")
        self.maximize_button.setFixedSize(32, 32)
        self.maximize_button.clicked.connect(self.maximize_clicked.emit)
        layout.addWidget(self.maximize_button)

        # Close
        self.close_button = QPushButton("\u2715")  # X
        self.close_button.setObjectName("closeButton")
        self.close_button.setToolTip("Close")
        self.close_button.setFixedSize(32, 32)
        self.close_button.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.close_button)

    def update_maximize_button(self, is_maximized: bool):
        """Update maximize button icon based on window state."""
        if is_maximized:
            self.maximize_button.setText("\u25a2")  # Two squares (restore)
            self.maximize_button.setToolTip("Restore")
        else:
            self.maximize_button.setText("\u25a1")  # Single square (maximize)
            self.maximize_button.setToolTip("Maximize")
