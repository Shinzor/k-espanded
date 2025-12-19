# Espanded

A modern, beautiful desktop UI for managing [Espanso](https://espanso.org/) text expansions with GitHub-based synchronization.

## Features

- **Intuitive UI**: Clean, modern interface built with PySide6 (Qt6) for managing your text expansions
- **Espanso Integration**: Direct import/export from your existing Espanso configuration
- **GitHub Sync**: Sync your configurations across devices using GitHub repositories
- **Quick Add**: Global hotkey for adding expansions on the fly
- **Advanced Search**: Find expansions by trigger, content, or tags
- **History Tracking**: Complete change history for all your expansions
- **Conflict Resolution**: Intelligent conflict detection and resolution for syncs
- **System Tray**: Minimize to system tray for quick access
- **Dark/Light Theme**: Automatic theme switching based on system preferences

## Screenshots

> Add screenshots here after building the UI

## Installation

### Requirements

- Python 3.11 or higher
- [Espanso](https://espanso.org/) installed and configured
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/Shinzor/k-espanded
cd k-espanded
uv venv

# Install with uv
uv pip install -e .

# For development
uv pip install -e ".[dev]"
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/Shinzor/k-espanded
cd espanded

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"
```

## Quick Start

### First Run

1. Launch Espanded:
   ```bash
   espanded
   ```

2. On first run, the wizard will guide you through:
   - Locating your Espanso configuration
   - Importing existing expansions
   - Setting up GitHub sync (optional)

### Basic Usage

**Add an Expansion:**
- Click the "+" button or use the quick-add hotkey (Ctrl+Shift+E)
- Enter trigger and replacement text
- Add tags for organization
- Save

**Search and Filter:**
- Use the search bar to find expansions
- Click tags to filter by category
- View deleted items in the Trash

**Sync with GitHub:**
- Go to Settings > GitHub Sync
- Create a GitHub token with repo access
- Enter repository name (or create new)
- Enable auto-sync or sync manually

## Configuration

### Espanso Path

Espanded automatically detects Espanso installations at:
- **Linux/macOS**: `~/.config/espanso`
- **Windows**: `%APPDATA%\espanso`

You can override this in Settings if needed.

### GitHub Sync Setup

1. **Create GitHub Token:**
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Create a fine-grained token with repository access
   - See [OAUTH_GUIDE.md](OAUTH_GUIDE.md) for detailed instructions

2. **Configure Repository:**
   - Use existing repo: `username/repo-name`
   - Or let Espanded create a new private repo for you

3. **Sync Settings:**
   - Auto-sync interval (default: 5 minutes)
   - Conflict resolution preferences
   - Sync on startup

### Hotkeys

**Global Hotkeys:**
- Quick Add: `Ctrl+Shift+E` (customizable)

**In-App Shortcuts:**
- New Entry: `Ctrl+N`
- Search: `Ctrl+F`
- Save: `Ctrl+S`
- Delete: `Delete`

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/espanded.git
cd espanded

# Install with development dependencies
uv pip install -e ".[hotkeys,dev]"
```

### Project Structure

```
espanded/
├── src/espanded/
│   ├── core/              # Core business logic
│   │   ├── models.py      # Data models
│   │   ├── database.py    # SQLite database
│   │   ├── entry_manager.py  # Entry CRUD operations
│   │   ├── yaml_handler.py   # Espanso YAML I/O
│   │   └── espanso.py     # Espanso integration
│   ├── sync/              # GitHub synchronization
│   │   ├── github_sync.py # GitHub API client
│   │   ├── conflict_resolver.py  # Conflict detection
│   │   └── sync_manager.py       # Sync orchestration
│   ├── ui/                # Flet UI components
│   │   ├── main_window.py
│   │   ├── entry_editor.py
│   │   ├── settings_view.py
│   │   └── ...
│   ├── hotkeys/           # Global hotkey support
│   │   ├── listener.py
│   │   └── clipboard.py
│   └── main.py            # Application entry point
├── tests/                 # Test suite
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── assets/                # UI assets
├── pyproject.toml         # Project configuration
└── README.md
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=espanded --cov-report=html

# Run specific test file
pytest tests/unit/test_entry_manager.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format and lint with ruff
ruff check .
ruff format .

# Type checking (if mypy is configured)
mypy src/espanded
```

### Running from Source

```bash
# Run directly
python -m espanded.main

# Or use the convenience script
python run.py
```

## Architecture

### Data Models

**Entry**: Represents a single text expansion with:
- Trigger and prefix
- Replacement text
- Tags for organization
- Espanso options (word, case, regex, etc.)
- Metadata (timestamps, source file)

**Settings**: Application configuration including:
- GitHub sync settings
- UI preferences
- Hotkey configuration
- Espanso path

**HistoryEntry**: Change tracking for:
- Create, update, delete, restore actions
- Timestamps
- Change details

### Database

Uses SQLite for local storage:
- Entries table with soft-delete support
- History table for change tracking
- Settings table for configuration

### Sync Architecture

1. **GitHub Sync**: GitHub API client for file operations
2. **Conflict Resolver**: Detects and resolves sync conflicts
3. **Sync Manager**: Orchestrates sync operations
4. **Strategies**:
   - Auto-resolve based on timestamps
   - Manual resolution for major conflicts
   - Keep both versions option

## Troubleshooting

### Espanso Not Detected

- Verify Espanso is installed: `espanso --version`
- Check the configuration path in Settings
- Ensure you have read/write permissions

### GitHub Sync Issues

- Verify token has repository access
- Check repository exists and you have write permissions
- Review sync logs in Settings > GitHub Sync

### Hotkeys Not Working

- Ensure hotkey dependencies are installed: `pip install ".[hotkeys]"`
- Check for conflicting global hotkeys
- Try running with administrator/sudo privileges

### Database Issues

- Database location: `~/.local/share/espanded/espanded.db`
- Backup before manual modifications
- Delete to reset (will lose local data)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details

## Acknowledgments

- [Espanso](https://espanso.org/) - The amazing text expander
- [Flet](https://flet.dev/) - Beautiful Python UI framework
- [httpx](https://www.python-httpx.org/) - Modern HTTP client

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/espanded/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/espanded/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/espanded/wiki)

---

Built with love for the Espanso community
