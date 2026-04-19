import sqlite3
import os
from contextlib import closing

# Store the DB in the project root alongside the backend
_HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_HERE, '..', 'skillroute.db')


def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()


def log_action(user_id: str, action_type: str, details: str):
    """Insert a new action record into the audit log."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "INSERT INTO user_actions (user_id, action_type, details) VALUES (?, ?, ?)",
                (user_id, action_type, details)
            )
            conn.commit()


def get_recent_actions(limit: int = 10) -> list:
    """Return the most recent action records as a list of dicts."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                'SELECT * FROM user_actions ORDER BY timestamp DESC LIMIT ?',
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]


if __name__ == '__main__':
    init_db()
    print(f"Database initialized at: {os.path.abspath(DB_PATH)}")
