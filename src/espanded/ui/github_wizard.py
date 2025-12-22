"""GitHub connection wizard for setting up sync."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QWidget,
    QCheckBox,
    QMessageBox,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QThread, QUrl, QPoint
from PySide6.QtGui import QDesktopServices, QMouseEvent, QCursor

from espanded.ui.theme import ThemeManager
from espanded.core.app_state import get_app_state

# Check for sync dependencies
try:
    from espanded.sync.github_sync import GitHubSync, HTTPX_AVAILABLE
except ImportError:
    HTTPX_AVAILABLE = False
    GitHubSync = None


class ConnectionTestThread(QThread):
    """Thread for testing GitHub connection."""

    finished = Signal(bool, str)  # success, message

    def __init__(self, token: str, repo: str):
        super().__init__()
        self.token = token
        self.repo = repo

    def run(self):
        try:
            sync = GitHubSync(self.repo, self.token)
            if sync.test_connection():
                self.finished.emit(True, "Connection successful!")
            else:
                self.finished.emit(False, "Could not connect to repository. Check your token and repository name.")
            sync.close()
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class CreateRepoThread(QThread):
    """Thread for creating a new GitHub repository."""

    finished = Signal(bool, str, str)  # success, message, repo_full_name

    def __init__(self, token: str, repo_name: str, private: bool = True):
        super().__init__()
        self.token = token
        self.repo_name = repo_name
        self.private = private

    def run(self):
        try:
            import httpx
            client = httpx.Client(
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30.0,
            )

            response = client.post(
                "https://api.github.com/user/repos",
                json={
                    "name": self.repo_name,
                    "description": "Espanded configuration sync",
                    "private": self.private,
                    "auto_init": True,
                }
            )

            client.close()

            if response.status_code == 201:
                data = response.json()
                self.finished.emit(True, "Repository created successfully!", data["full_name"])
            elif response.status_code == 422:
                self.finished.emit(False, "Repository already exists. Try a different name.", "")
            else:
                self.finished.emit(False, f"Failed to create repository: {response.text}", "")

        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "")


class GitHubWizard(QDialog):
    """Wizard dialog for connecting to GitHub - frameless, draggable."""

    connection_saved = Signal()

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(None)  # No parent to avoid showing main window
        self.theme_manager = theme_manager
        self.app_state = get_app_state()

        self._test_thread = None
        self._create_thread = None
        self._drag_pos: QPoint | None = None

        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """Configure window properties."""
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(520, 620)

        colors = self.theme_manager.colors
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors.bg_surface};
                border: 1px solid {colors.border_default};
                border-radius: 12px;
            }}
        """)

    def _setup_ui(self):
        """Build the wizard UI."""
        colors = self.theme_manager.colors

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (draggable)
        self.header = QWidget()
        self.header.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_surface};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)
        self.header.setCursor(Qt.CursorShape.SizeAllCursor)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 16, 16, 12)
        header_layout.setSpacing(8)

        title = QLabel("Connect to GitHub")
        title.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 16px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: none;
                border-radius: 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {colors.error};
                color: {colors.text_inverse};
            }}
        """)
        close_btn.clicked.connect(self.reject)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(close_btn)

        layout.addWidget(self.header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {colors.border_muted}; border: none;")
        layout.addWidget(sep)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors.bg_surface};
                border: none;
            }}
        """)

        content = self._create_content()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # Bottom buttons
        button_container = QWidget()
        button_container.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.bg_surface};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 12, 20, 16)
        button_layout.setSpacing(12)

        test_btn = QPushButton("Test Connection")
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {colors.primary};
            }}
        """)
        test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(test_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {colors.bg_elevated};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save & Connect")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
            }}
        """)
        save_btn.clicked.connect(self._save_connection)
        button_layout.addWidget(save_btn)

        layout.addWidget(button_container)

    def _create_content(self) -> QWidget:
        """Create the main content area."""
        colors = self.theme_manager.colors

        content = QWidget()
        content.setStyleSheet(f"background-color: {colors.bg_surface};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(16)

        # Subtitle
        subtitle = QLabel("Sync your Espanso entries across devices using a private GitHub repository.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_secondary};
                font-size: 13px;
                background: transparent;
            }}
        """)
        content_layout.addWidget(subtitle)

        # Step 1
        step1_title = QLabel("Step 1: Create a Personal Access Token")
        step1_title.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                margin-top: 8px;
            }}
        """)
        content_layout.addWidget(step1_title)

        # Instructions in a subtle bordered container
        instructions_frame = QFrame()
        instructions_frame.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: 1px solid {colors.border_muted};
                border-radius: 6px;
            }}
        """)
        instr_layout = QVBoxLayout(instructions_frame)
        instr_layout.setContentsMargins(12, 10, 12, 10)
        instr_layout.setSpacing(4)

        instructions = [
            "1. Go to GitHub → Settings → Developer settings → Personal access tokens",
            "2. Select 'Fine-grained tokens' → 'Generate new token'",
            "3. Name it 'Espanded Sync', set expiration",
            "4. Repository access: Select your sync repo (or All)",
            "5. Permissions: Contents (Read/Write), Metadata (Read)",
            "6. Generate and copy the token",
        ]

        for instr in instructions:
            lbl = QLabel(instr)
            lbl.setStyleSheet(f"""
                QLabel {{
                    color: {colors.text_secondary};
                    font-size: 11px;
                    background: transparent;
                }}
            """)
            instr_layout.addWidget(lbl)

        content_layout.addWidget(instructions_frame)

        # Open GitHub button
        github_btn = QPushButton("Open GitHub Token Settings")
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.primary};
                border: 1px solid {colors.primary};
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_muted};
            }}
        """)
        github_btn.clicked.connect(self._open_github_tokens)
        content_layout.addWidget(github_btn)

        # Step 2
        step2_title = QLabel("Step 2: Enter Your Token")
        step2_title.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                margin-top: 12px;
            }}
        """)
        content_layout.addWidget(step2_title)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("github_pat_xxxxxxxxxx...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            QLineEdit:focus {{
                border-color: {colors.primary};
            }}
        """)
        content_layout.addWidget(self.token_input)

        show_token = QCheckBox("Show token")
        show_token.setStyleSheet(f"""
            QCheckBox {{
                color: {colors.text_secondary};
                font-size: 11px;
                background: transparent;
            }}
        """)
        show_token.toggled.connect(
            lambda checked: self.token_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        content_layout.addWidget(show_token)

        # Step 3
        step3_title = QLabel("Step 3: Repository")
        step3_title.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_primary};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                margin-top: 12px;
            }}
        """)
        content_layout.addWidget(step3_title)

        # Repository row
        repo_row = QWidget()
        repo_row.setStyleSheet("background: transparent;")
        repo_layout = QHBoxLayout(repo_row)
        repo_layout.setContentsMargins(0, 0, 0, 0)
        repo_layout.setSpacing(8)

        self.repo_input = QLineEdit()
        self.repo_input.setPlaceholderText("username/espanded-sync")
        self.repo_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors.bg_elevated};
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {colors.primary};
            }}
        """)
        repo_layout.addWidget(self.repo_input, stretch=1)

        create_repo_btn = QPushButton("Create New")
        create_repo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_repo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_primary};
                border: 1px solid {colors.border_default};
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {colors.primary};
            }}
        """)
        create_repo_btn.clicked.connect(self._create_repository)
        repo_layout.addWidget(create_repo_btn)

        content_layout.addWidget(repo_row)

        repo_hint = QLabel("Format: username/repository-name")
        repo_hint.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_tertiary};
                font-size: 11px;
                background: transparent;
            }}
        """)
        content_layout.addWidget(repo_hint)

        # Status message
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text_secondary};
                font-size: 12px;
                padding: 10px 12px;
                background-color: transparent;
                border: 1px solid {colors.border_muted};
                border-radius: 6px;
            }}
        """)
        self.status_label.setVisible(False)
        content_layout.addWidget(self.status_label)

        content_layout.addStretch()

        # Load existing values
        self._load_existing_settings()

        return content

    def _load_existing_settings(self):
        """Load existing GitHub settings if available."""
        settings = self.app_state.settings
        if settings.github_token:
            self.token_input.setText(settings.github_token)
        if settings.github_repo:
            self.repo_input.setText(settings.github_repo)

    def _open_github_tokens(self):
        """Open GitHub token settings in browser."""
        QDesktopServices.openUrl(
            QUrl("https://github.com/settings/tokens?type=beta")
        )

    def _show_status(self, message: str, is_error: bool = False, is_success: bool = False):
        """Show status message."""
        colors = self.theme_manager.colors

        if is_error:
            border_color = colors.error
            text_color = colors.error
        elif is_success:
            border_color = colors.success
            text_color = colors.success
        else:
            border_color = colors.border_muted
            text_color = colors.text_secondary

        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 12px;
                padding: 10px 12px;
                background-color: transparent;
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
        """)
        self.status_label.setText(message)
        self.status_label.setVisible(True)

    def _test_connection(self):
        """Test the GitHub connection."""
        if not HTTPX_AVAILABLE:
            self._show_status("httpx is not installed. Cannot connect to GitHub.", is_error=True)
            return

        token = self.token_input.text().strip()
        repo = self.repo_input.text().strip()

        if not token:
            self._show_status("Please enter your GitHub token.", is_error=True)
            return

        if not repo:
            self._show_status("Please enter the repository name.", is_error=True)
            return

        if "/" not in repo:
            self._show_status("Repository must be in format: username/repo-name", is_error=True)
            return

        self._show_status("Testing connection...")

        self._test_thread = ConnectionTestThread(token, repo)
        self._test_thread.finished.connect(self._on_test_finished)
        self._test_thread.start()

    def _on_test_finished(self, success: bool, message: str):
        """Handle test connection result."""
        self._show_status(message, is_error=not success, is_success=success)

    def _create_repository(self):
        """Create a new GitHub repository."""
        if not HTTPX_AVAILABLE:
            self._show_status("httpx is not installed. Cannot connect to GitHub.", is_error=True)
            return

        token = self.token_input.text().strip()

        if not token:
            self._show_status("Please enter your GitHub token first.", is_error=True)
            return

        from PySide6.QtWidgets import QInputDialog

        repo_name, ok = QInputDialog.getText(
            self,
            "Create Repository",
            "Enter repository name (e.g., espanded-sync):",
            QLineEdit.EchoMode.Normal,
            "espanded-sync"
        )

        if not ok or not repo_name:
            return

        repo_name = repo_name.strip().replace(" ", "-").lower()

        self._show_status(f"Creating repository '{repo_name}'...")

        self._create_thread = CreateRepoThread(token, repo_name, private=True)
        self._create_thread.finished.connect(self._on_create_finished)
        self._create_thread.start()

    def _on_create_finished(self, success: bool, message: str, repo_full_name: str):
        """Handle create repository result."""
        self._show_status(message, is_error=not success, is_success=success)

        if success and repo_full_name:
            self.repo_input.setText(repo_full_name)

    def _save_connection(self):
        """Save the connection settings."""
        token = self.token_input.text().strip()
        repo = self.repo_input.text().strip()

        if not token:
            self._show_status("Please enter your GitHub token.", is_error=True)
            return

        if not repo:
            self._show_status("Please enter the repository name.", is_error=True)
            return

        if "/" not in repo:
            self._show_status("Repository must be in format: username/repo-name", is_error=True)
            return

        self.app_state.settings.github_token = token
        self.app_state.settings.github_repo = repo
        self.app_state.settings.auto_sync = True
        self.app_state.save_settings()

        self.connection_saved.emit()

        QMessageBox.information(
            self,
            "Connected",
            f"Successfully connected to GitHub!\n\nRepository: {repo}\n\nYour entries will now sync automatically."
        )

        self.accept()

    def show_centered(self):
        """Show wizard centered on screen."""
        cursor_pos = QCursor.pos()
        x = cursor_pos.x() - self.width() // 2
        y = cursor_pos.y() - self.height() // 2

        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = max(screen.x(), min(x, screen.x() + screen.width() - self.width()))
        y = max(screen.y(), min(y, screen.y() + screen.height() - self.height()))

        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            header_rect = self.header.geometry()
            if header_rect.contains(event.pos()):
                self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for window dragging."""
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to stop dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
