import sqlite3
from collections.abc import Iterator

from citypulse.db.connection import connect


def get_db() -> Iterator[sqlite3.Connection]:
    con = connect()
    try:
        yield con
    finally:
        con.close()
