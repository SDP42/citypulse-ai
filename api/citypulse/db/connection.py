import sqlite3
from pathlib import Path

from citypulse.core.settings import ROOT, get_settings

MIGRATIONS = ROOT / "api" / "migrations"


def connect(path: Path | None = None, read_only: bool = False) -> sqlite3.Connection:
    path = path or get_settings().db_path
    if read_only:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(path, check_same_thread=False)
        con.execute("PRAGMA journal_mode=WAL")
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def migrate(con: sqlite3.Connection, directory: Path = MIGRATIONS) -> list[str]:
    con.execute("CREATE TABLE IF NOT EXISTS schema_migration (name TEXT PRIMARY KEY, applied_at TEXT)")
    done = {r[0] for r in con.execute("SELECT name FROM schema_migration")}
    applied = []
    for f in sorted(directory.glob("*.sql")):
        if f.name in done:
            continue
        con.executescript(f"BEGIN;\n{f.read_text()}\nINSERT INTO schema_migration VALUES ('{f.name}', datetime('now'));\nCOMMIT;")
        applied.append(f.name)
    return applied
