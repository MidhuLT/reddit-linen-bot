import sqlite3
from datetime import datetime, timedelta
from config import DB_FILE

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_posts (
            post_id TEXT PRIMARY KEY,
            link    TEXT,
            title   TEXT,
            sent_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    # Purge records older than 90 days so the DB doesn't grow forever
    _cleanup_old_records(days=90)

def was_sent(post_id: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()
    cur.execute("SELECT 1 FROM sent_posts WHERE post_id = ?", (post_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None

def mark_sent(post_id: str, link: str, title: str):
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO sent_posts (post_id, link, title, sent_at) VALUES (?, ?, ?, ?)",
        (post_id, link, title, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

def _cleanup_old_records(days: int = 90):
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()
    cur.execute("DELETE FROM sent_posts WHERE sent_at < ?", (cutoff,))
    conn.commit()
    conn.close()
