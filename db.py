"""Database layer: everything that talks to SQLite lives here (US01, US03)."""
import os
import sqlite3
from contextlib import closing
from decimal import Decimal

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
    conn.execute("PRAGMA foreign_keys = ON")
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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY,
            offer_id INTEGER NOT NULL REFERENCES offers(id),
            participants INTEGER NOT NULL CHECK (participants > 0),
            total_grosz INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'confirmed', 'cancelled'))
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS reservations_offer ON reservations(offer_id)")
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
    result = conn.execute(
        "UPDATE offers SET destination = :destination, start_date = :start_date, "
        "end_date = :end_date, price = :price, seats = :seats, trip_type = :trip_type "
        "WHERE id = :id AND :seats >= COALESCE(("
        "SELECT SUM(participants) FROM reservations WHERE offer_id = :id AND status != 'cancelled'"
        "), 0)",
        {**data, "id": offer_id},
    )
    conn.commit()
    conn.close()
    return result.rowcount == 1


def delete_offer(offer_id):
    with closing(get_conn()) as conn, conn:
        result = conn.execute(
            "DELETE FROM offers WHERE id = ? AND NOT EXISTS "
            "(SELECT 1 FROM reservations WHERE offer_id = offers.id)", (offer_id,)
        )
        return result.rowcount == 1


AVAILABLE_OFFERS = """
    SELECT offers.*, seats - COALESCE((
        SELECT SUM(participants) FROM reservations
        WHERE offer_id = offers.id AND status != 'cancelled'
    ), 0) AS available_seats
    FROM offers
"""


def catalog_offers():
    with closing(get_conn()) as conn:
        return conn.execute(AVAILABLE_OFFERS + " ORDER BY start_date").fetchall()


def bookable_offer(offer_id):
    with closing(get_conn()) as conn:
        return conn.execute(AVAILABLE_OFFERS + " WHERE offers.id = ?", (offer_id,)).fetchone()


def create_reservation(offer_id, participants):
    with closing(get_conn()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        offer = conn.execute(
            AVAILABLE_OFFERS + " WHERE offers.id = ?", (offer_id,)
        ).fetchone()
        if offer is None or not 1 <= participants <= offer["available_seats"]:
            return None
        unit_grosz = round(Decimal(str(offer["price"])) * 100)
        reservation = conn.execute(
            "INSERT INTO reservations (offer_id, participants, total_grosz) VALUES (?, ?, ?)",
            (offer_id, participants, unit_grosz * participants),
        )
        return reservation.lastrowid, unit_grosz * participants
