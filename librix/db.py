"""
Database layer (SQLite). This is the ONLY module that opens a connection.
Services talk to the database exclusively through this class using
parameterised queries - never string-concatenated SQL values.
"""
import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from . import config
from .security import hash_password

TABLE_ORDER = ["users", "books", "members", "issues", "returns", "fines", "test_cases",
               "bug_logs", "boundary_tests", "system_logs", "audit_logs"]


def _dict_factory(cursor, row):
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


class Database:
    def __init__(self, path):
        self.path = str(path)
        self.lock = threading.RLock()  # serialises access: one request touches the DB at a time
        self.conn = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self.conn.row_factory = _dict_factory
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self._tx_depth = 0

    # ---- basic helpers -----------------------------------------------------
    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def one(self, sql, params=()):
        return self.conn.execute(sql, params).fetchone()

    def execute(self, sql, params=()):
        return self.conn.execute(sql, params)

    def insert(self, sql, params=()) -> int:
        return self.conn.execute(sql, params).lastrowid

    @contextmanager
    def transaction(self):
        """BEGIN ... COMMIT, rolling back if the block raises. Re-entrant (inner blocks join the outer one)."""
        if self._tx_depth > 0:
            self._tx_depth += 1
            try:
                yield
            finally:
                self._tx_depth -= 1
            return
        self.conn.execute("BEGIN IMMEDIATE")
        self._tx_depth = 1
        try:
            yield
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise
        finally:
            self._tx_depth = 0

    def close(self):
        self.conn.close()


_db = None
_db_lock = threading.Lock()


def get_db() -> Database:
    global _db
    if _db is None:
        raise RuntimeError("Database not initialised - call init_db() first.")
    return _db


def init_db(path=None, reset=False) -> Database:
    """Open (creating if needed) the database, apply the schema and seed demo data on first run."""
    global _db
    with _db_lock:
        path = path or config.DB_PATH
        if _db is not None:
            _db.close()
            _db = None
        if reset and str(path) != ":memory:":
            for suffix in ("", "-wal", "-shm"):
                try:
                    Path(str(path) + suffix).unlink()
                except FileNotFoundError:
                    pass
        db = Database(path)
        db.conn.executescript(config.SCHEMA_FILE.read_text(encoding="utf-8"))
        # lightweight migration: databases created before the book "description" column existed
        if "description" not in [c["name"] for c in db.query("PRAGMA table_info(books)")]:
            db.execute("ALTER TABLE books ADD COLUMN description TEXT")
        fresh = db.one("SELECT COUNT(*) AS n FROM users")["n"] == 0
        if fresh:
            seed(db)
        _db = db
        return db


def seed(db: Database) -> None:
    data = json.loads(config.SEED_FILE.read_text(encoding="utf-8"))
    with db.transaction():
        for table in TABLE_ORDER:
            for row in data.get(table, []):
                row = dict(row)
                if table == "users":
                    row["password_hash"] = hash_password(config.DEFAULT_PASSWORDS[row["username"]])
                cols = ", ".join(row.keys())
                marks = ", ".join("?" for _ in row)
                db.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", list(row.values()))
