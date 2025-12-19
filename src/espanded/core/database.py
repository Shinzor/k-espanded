"""SQLite database for storing entries, settings, and history."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from espanded.core.models import Entry, Settings, HistoryEntry


class Database:
    """SQLite database manager for Espanded."""

    def __init__(self, db_path: str | Path | None = None):
        """Initialize database connection.

        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if db_path is None:
            # Use default location in user's app data
            from espanded.core.espanso import EspansoManager
            app_dir = Path.home() / ".espanded"
            app_dir.mkdir(exist_ok=True)
            db_path = app_dir / "espanded.db"

        self.db_path = Path(db_path)
        self.conn: sqlite3.Connection | None = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Create database connection."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                trigger TEXT NOT NULL,
                prefix TEXT DEFAULT ':',
                replacement TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                word INTEGER DEFAULT 1,
                propagate_case INTEGER DEFAULT 0,
                uppercase_style TEXT DEFAULT 'capitalize',
                regex INTEGER DEFAULT 0,
                case_insensitive INTEGER DEFAULT 0,
                force_clipboard INTEGER DEFAULT 0,
                passive INTEGER DEFAULT 0,
                markdown INTEGER DEFAULT 0,
                cursor_hint TEXT,
                filter_apps TEXT,
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL,
                deleted_at TEXT,
                source_file TEXT DEFAULT 'base.yml'
            )
        """)

        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY,
                entry_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                changes TEXT DEFAULT '{}',
                trigger_name TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_trigger ON entries(trigger)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_deleted ON entries(deleted_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_entry ON history(entry_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp)")

        self.conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    # Entry CRUD operations

    def save_entry(self, entry: Entry) -> Entry:
        """Save an entry to the database."""
        cursor = self.conn.cursor()

        entry.modified_at = datetime.now()

        cursor.execute("""
            INSERT OR REPLACE INTO entries
            (id, trigger, prefix, replacement, tags, word, propagate_case,
             uppercase_style, regex, case_insensitive, force_clipboard,
             passive, markdown, cursor_hint, filter_apps, created_at,
             modified_at, deleted_at, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id,
            entry.trigger,
            entry.prefix,
            entry.replacement,
            json.dumps(entry.tags),
            int(entry.word),
            int(entry.propagate_case),
            entry.uppercase_style,
            int(entry.regex),
            int(entry.case_insensitive),
            int(entry.force_clipboard),
            int(entry.passive),
            int(entry.markdown),
            entry.cursor_hint,
            json.dumps(entry.filter_apps) if entry.filter_apps else None,
            entry.created_at.isoformat(),
            entry.modified_at.isoformat(),
            entry.deleted_at.isoformat() if entry.deleted_at else None,
            entry.source_file,
        ))

        self.conn.commit()
        return entry

    def get_entry(self, entry_id: str) -> Entry | None:
        """Get an entry by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()

        if row:
            return self._row_to_entry(row)
        return None

    def get_all_entries(self, include_deleted: bool = False) -> list[Entry]:
        """Get all entries."""
        cursor = self.conn.cursor()

        if include_deleted:
            cursor.execute("SELECT * FROM entries ORDER BY modified_at DESC")
        else:
            cursor.execute(
                "SELECT * FROM entries WHERE deleted_at IS NULL ORDER BY modified_at DESC"
            )

        return [self._row_to_entry(row) for row in cursor.fetchall()]

    def get_deleted_entries(self) -> list[Entry]:
        """Get all soft-deleted entries (trash)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM entries WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC"
        )
        return [self._row_to_entry(row) for row in cursor.fetchall()]

    def search_entries(self, query: str, tags: list[str] | None = None) -> list[Entry]:
        """Search entries by trigger or replacement text."""
        cursor = self.conn.cursor()

        sql = """
            SELECT * FROM entries
            WHERE deleted_at IS NULL
            AND (trigger LIKE ? OR replacement LIKE ?)
        """
        params: list[Any] = [f"%{query}%", f"%{query}%"]

        cursor.execute(sql, params)
        entries = [self._row_to_entry(row) for row in cursor.fetchall()]

        # Filter by tags in Python (simpler than JSON parsing in SQL)
        if tags:
            entries = [e for e in entries if any(t in e.tags for t in tags)]

        return entries

    def soft_delete_entry(self, entry_id: str) -> bool:
        """Soft delete an entry (move to trash)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE entries SET deleted_at = ? WHERE id = ?",
            (datetime.now().isoformat(), entry_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def restore_entry(self, entry_id: str) -> bool:
        """Restore a soft-deleted entry from trash."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE entries SET deleted_at = NULL, modified_at = ? WHERE id = ?",
            (datetime.now().isoformat(), entry_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def permanent_delete_entry(self, entry_id: str) -> bool:
        """Permanently delete an entry."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def _row_to_entry(self, row: sqlite3.Row) -> Entry:
        """Convert a database row to an Entry object."""
        filter_apps = None
        if row["filter_apps"]:
            filter_apps = json.loads(row["filter_apps"])

        deleted_at = None
        if row["deleted_at"]:
            deleted_at = datetime.fromisoformat(row["deleted_at"])

        return Entry(
            id=row["id"],
            trigger=row["trigger"],
            prefix=row["prefix"],
            replacement=row["replacement"],
            tags=json.loads(row["tags"]),
            word=bool(row["word"]),
            propagate_case=bool(row["propagate_case"]),
            uppercase_style=row["uppercase_style"],
            regex=bool(row["regex"]),
            case_insensitive=bool(row["case_insensitive"]),
            force_clipboard=bool(row["force_clipboard"]),
            passive=bool(row["passive"]),
            markdown=bool(row["markdown"]),
            cursor_hint=row["cursor_hint"],
            filter_apps=filter_apps,
            created_at=datetime.fromisoformat(row["created_at"]),
            modified_at=datetime.fromisoformat(row["modified_at"]),
            deleted_at=deleted_at,
            source_file=row["source_file"],
        )

    # Settings operations

    def save_settings(self, settings: Settings):
        """Save settings to database."""
        cursor = self.conn.cursor()
        settings_dict = settings.to_dict()

        for key, value in settings_dict.items():
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )

        self.conn.commit()

    def get_settings(self) -> Settings:
        """Get settings from database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM settings")

        settings_dict = {}
        for row in cursor.fetchall():
            settings_dict[row["key"]] = json.loads(row["value"])

        if settings_dict:
            return Settings.from_dict(settings_dict)
        return Settings()

    # History operations

    def add_history(self, history: HistoryEntry):
        """Add a history entry."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO history (id, entry_id, action, timestamp, changes, trigger_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            history.id,
            history.entry_id,
            history.action,
            history.timestamp.isoformat(),
            json.dumps(history.changes),
            history.trigger_name,
        ))
        self.conn.commit()

    def get_history(self, limit: int = 100) -> list[HistoryEntry]:
        """Get recent history entries."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM history ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )

        return [self._row_to_history(row) for row in cursor.fetchall()]

    def get_entry_history(self, entry_id: str) -> list[HistoryEntry]:
        """Get history for a specific entry."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM history WHERE entry_id = ? ORDER BY timestamp DESC",
            (entry_id,)
        )
        return [self._row_to_history(row) for row in cursor.fetchall()]

    def _row_to_history(self, row: sqlite3.Row) -> HistoryEntry:
        """Convert a database row to a HistoryEntry object."""
        return HistoryEntry(
            id=row["id"],
            entry_id=row["entry_id"],
            action=row["action"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            changes=json.loads(row["changes"]),
            trigger_name=row["trigger_name"],
        )

    # Tag operations

    def get_all_tags(self) -> dict[str, int]:
        """Get all unique tags with their counts."""
        entries = self.get_all_entries()
        tag_counts: dict[str, int] = {}

        for entry in entries:
            for tag in entry.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return tag_counts

    # Statistics

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        cursor = self.conn.cursor()

        # Total entries
        cursor.execute("SELECT COUNT(*) FROM entries WHERE deleted_at IS NULL")
        total_entries = cursor.fetchone()[0]

        # Deleted entries
        cursor.execute("SELECT COUNT(*) FROM entries WHERE deleted_at IS NOT NULL")
        deleted_entries = cursor.fetchone()[0]

        # Entries modified today
        today = datetime.now().date().isoformat()
        cursor.execute(
            "SELECT COUNT(*) FROM entries WHERE deleted_at IS NULL AND date(modified_at) = ?",
            (today,)
        )
        modified_today = cursor.fetchone()[0]

        # Entries created today
        cursor.execute(
            "SELECT COUNT(*) FROM entries WHERE deleted_at IS NULL AND date(created_at) = ?",
            (today,)
        )
        created_today = cursor.fetchone()[0]

        # Last modified
        cursor.execute(
            "SELECT MAX(modified_at) FROM entries WHERE deleted_at IS NULL"
        )
        last_modified = cursor.fetchone()[0]

        return {
            "total_entries": total_entries,
            "deleted_entries": deleted_entries,
            "modified_today": modified_today,
            "created_today": created_today,
            "last_modified": last_modified,
            "tag_count": len(self.get_all_tags()),
        }
