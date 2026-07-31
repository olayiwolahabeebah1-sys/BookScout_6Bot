import sqlite3
from contextlib import closing

DB_PATH = "reading_list.db"


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reading_list (
                user_id INTEGER NOT NULL,
                book_id TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                PRIMARY KEY (user_id, book_id)
            )
        """)
        conn.commit()


def add_book(user_id: int, book_id: str, title: str, author: str):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO reading_list (user_id, book_id, title, author) VALUES (?, ?, ?, ?)",
            (user_id, book_id, title, author),
        )
        conn.commit()


def remove_book(user_id: int, book_id: str):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "DELETE FROM reading_list WHERE user_id = ? AND book_id = ?",
            (user_id, book_id),
        )
        conn.commit()


def get_list(user_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute(
            "SELECT book_id, title, author FROM reading_list WHERE user_id = ?",
            (user_id,),
        )
        return cur.fetchall()
