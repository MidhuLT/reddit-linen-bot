import os
import logging
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = bool(DATABASE_URL)

from config import DB_FILE


# --------------------------------------------------------------------------- #
# Postgres helpers
# --------------------------------------------------------------------------- #

def _pg_conn():
    import psycopg2
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def _pg_init():
    conn = _pg_conn()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_posts (
            post_id TEXT PRIMARY KEY,
            link    TEXT,
            title   TEXT,
            sent_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def _pg_was_sent(post_id: str) -> bool:
    conn = _pg_conn()
    cur  = conn.cursor()
    cur.execute("SELECT 1 FROM sent_posts WHERE post_id = %s", (post_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row is not None


def _pg_mark_sent(post_id: str, link: str, title: str):
    conn = _pg_conn()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO sent_posts (post_id, link, title) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        (post_id, link, title),
    )
    conn.commit()
    cur.close()
    conn.close()


def _pg_cleanup(days: int = 90):
    cutoff = datetime.utcnow() - timedelta(days=days)
    conn = _pg_conn()
    cur  = conn.cursor()
    cur.execute("DELETE FROM sent_posts WHERE sent_at < %s", (cutoff,))
    conn.commit()
    cur.close()
    conn.close()


# --------------------------------------------------------------------------- #
# SQLite helpers
# --------------------------------------------------------------------------- #

def _sq_init():
    import sqlite3
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()
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


def _sq_was_sent(post_id: str) -> bool:
    import sqlite3
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()
    cur.execute("SELECT 1 FROM sent_posts WHERE post_id = ?", (post_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def _sq_mark_sent(post_id: str, link: str, title: str):
    import sqlite3
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO sent_posts (post_id, link, title, sent_at) VALUES (?, ?, ?, ?)",
        (post_id, link, title, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def _sq_cleanup(days: int = 90):
    import sqlite3
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()
    cur.execute("DELETE FROM sent_posts WHERE sent_at < ?", (cutoff,))
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def init_db():
    if USE_POSTGRES:
        log.info("Using PostgreSQL for dedup storage.")
        _pg_init()
        _pg_cleanup(days=90)
    else:
        log.info("Using SQLite for dedup storage.")
        _sq_init()
        _sq_cleanup(days=90)


def was_sent(post_id: str) -> bool:
    if USE_POSTGRES:
        return _pg_was_sent(post_id)
    return _sq_was_sent(post_id)


def mark_sent(post_id: str, link: str, title: str):
    if USE_POSTGRES:
        _pg_mark_sent(post_id, link, title)
    else:
        _sq_mark_sent(post_id, link, title)
