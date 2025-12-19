# Espanded - Quick Start Guide

## Installation

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- [Espanso](https://espanso.org/) installed

### Install

```bash
# Clone and install
git clone https://github.com/yourusername/espanded.git
cd espanded
uv pip install -e .

# With hotkey support
uv pip install -e ".[hotkeys]"

# For development
uv pip install -e ".[hotkeys,dev]"
```

## Running

```bash
# Run the application
espanded

# Or run from source
python run.py
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=espanded --cov-report=html

# Format code
ruff format .

# Lint code
ruff check .
```

## Quick Commands

| Command | Description |
|---------|-------------|
| `espanded` | Launch the app |
| `pytest` | Run all tests |
| `pytest -v` | Verbose test output |
| `pytest --cov` | Coverage report |
| `ruff check .` | Lint code |
| `ruff format .` | Format code |

## File Structure

```
espanded/
├── src/espanded/        # Source code
│   ├── core/           # Business logic
│   ├── sync/           # GitHub sync
│   ├── ui/             # Flet UI
│   └── hotkeys/        # Global hotkeys
├── tests/              # Test suite
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── README.md          # Full documentation
├── TESTING.md         # Test guide
└── run.py             # Launch script
```

## Key Features

- Manage Espanso expansions with GUI
- GitHub sync across devices
- Search and tag organization
- History tracking
- Quick add with hotkey
- Conflict resolution

## Next Steps

1. Read [README.md](../README.md) for full documentation
2. Check [TESTING.md](../TESTING.md) for testing guide
3. See [CONTRIBUTING.md](../CONTRIBUTING.md) to contribute
4. Review [OAUTH_GUIDE.md](../OAUTH_GUIDE.md) for GitHub setup

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/espanded/issues)
- Docs: [Wiki](https://github.com/yourusername/espanded/wiki)
