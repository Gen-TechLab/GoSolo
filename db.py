"""Database layer: everything that talks to SQLite lives here (US01, US03)."""
import os
import sqlite3

# Path to the SQLite file. Tests change this to a temporary file.
DB_PATH = os.environ.get("DATABASE", "gosolo.db")

SAMPLE_OFFERS = [
    ("Chorwacja - Split", "2027-06-10", "2027-06-17", 2900, 20, "plażowy"),
    ("Włochy - Rzym", "2027-04-02", "2027-04-06", 2100, 15, "miejski"),
    ("Słowacja - Tatry", "2027-07-05", "2027-07-12", 1800, 12, "aktywny"),
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts: row["destination"]
    return conn


def init_db():
    """Create the table if it does not exist and add sample offers once."""
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS offers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT    NOT NULL,
            start_date  TEXT    NOT NULL,
            end_date    TEXT    NOT NULL,
            price       REAL    NOT NULL,
            seats       INTEGER NOT NULL,
            trip_type   TEXT    NOT NULL
        )
        """
    )
    count = conn.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO offers (destination, start_date, end_date, price, seats, trip_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            SAMPLE_OFFERS,
        )
    conn.commit()
    conn.close()


def list_offers():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM offers ORDER BY start_date").fetchall()
    conn.close()
    return rows


def get_offer(offer_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,)).fetchone()
    conn.close()
    return row


def add_offer(data):
    conn = get_conn()
    conn.execute(
        "INSERT INTO offers (destination, start_date, end_date, price, seats, trip_type) "
        "VALUES (:destination, :start_date, :end_date, :price, :seats, :trip_type)",
        data,
    )
    conn.commit()
    conn.close()


def update_offer(offer_id, data):
    conn = get_conn()
    conn.execute(
        "UPDATE offers SET destination = :destination, start_date = :start_date, "
        "end_date = :end_date, price = :price, seats = :seats, trip_type = :trip_type "
        "WHERE id = :id",
        {**data, "id": offer_id},
    )
    conn.commit()
    conn.close()


def delete_offer(offer_id):
    conn = get_conn()
    conn.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
    conn.commit()
    conn.close()
