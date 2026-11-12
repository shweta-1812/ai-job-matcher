import sqlite3
from pathlib import Path

DEFAULT_DB = Path('data/employer_boards.sqlite3')

def connect_registry(db_path=DEFAULT_DB):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS employer_boards (
        provider TEXT NOT NULL,
        token TEXT NOT NULL,
        status TEXT NOT NULL,
        discovered_from TEXT NOT NULL,
        last_checked TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (provider, token)
    )''')
    conn.commit()
    return conn

def save_board(conn, provider, token, status, source):
    conn.execute('''INSERT INTO employer_boards(provider, token, status, discovered_from)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(provider, token) DO UPDATE SET
        status=excluded.status, last_checked=CURRENT_TIMESTAMP''',
        (provider, token, status, source))
    conn.commit()

def get_boards(conn, status='valid'):
    return conn.execute('SELECT provider, token FROM employer_boards WHERE status=?', (status,)).fetchall()
