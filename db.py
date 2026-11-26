"""Database layer: everything that talks to SQLite lives here (US01, US03)."""
import os
import sqlite3
from contextlib import closing
from decimal import Decimal


DB_PATH = os.environ.get("DATABASE", "gosolo.db")

SAMPLE_OFFERS = [
    ("Warszawa", "Chorwacja - Split", "2027-06-10", "2027-06-17", 2900, 20, "plażowy"),
    ("Kraków", "Włochy - Rzym", "2027-04-02", "2027-04-06", 2100, 15, "miejski"),
    ("Katowice", "Słowacja - Tatry", "2027-07-05", "2027-07-12", 1800, 12, "aktywny"),
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _has_column(conn, table_name, column_name):
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(col["name"] == column_name for col in cols)


def init_db():
    """Create tables if they do not exist, migrate existing schema, and add sample offers once."""
    conn = get_conn()
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS offers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            origin      TEXT    NOT NULL DEFAULT 'Warszawa',
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
            user_id INTEGER REFERENCES users(id),
            participants INTEGER NOT NULL CHECK (participants > 0),
            total_grosz INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'confirmed', 'cancelled')),
            payment_status TEXT NOT NULL DEFAULT 'unpaid'
                CHECK (payment_status IN ('unpaid', 'deposit', 'paid'))
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS reservations_offer ON reservations(offer_id)")

    if not _has_column(conn, "offers", "origin"):
        conn.execute("ALTER TABLE offers ADD COLUMN origin TEXT NOT NULL DEFAULT 'Warszawa'")

    if not _has_column(conn, "reservations", "payment_status"):
        conn.execute(
            "ALTER TABLE reservations ADD COLUMN payment_status TEXT NOT NULL DEFAULT 'unpaid' "
            "CHECK (payment_status IN ('unpaid', 'deposit', 'paid'))"
        )

    if not _has_column(conn, "reservations", "user_id"):
        conn.execute("ALTER TABLE reservations ADD COLUMN user_id INTEGER REFERENCES users(id)")

    conn.execute("CREATE INDEX IF NOT EXISTS reservations_user ON reservations(user_id)")

    count = conn.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO offers (origin, destination, start_date, end_date, price, seats, trip_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            SAMPLE_OFFERS,
        )
    conn.commit()
    conn.close()


def create_user(email, password_hash):
    with closing(get_conn()) as conn, conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None


def get_user_by_email(email):
    with closing(get_conn()) as conn:
        return conn.execute(
            "SELECT * FROM users WHERE lower(email) = lower(?)",
            (email,),
        ).fetchone()


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
        "INSERT INTO offers (origin, destination, start_date, end_date, price, seats, trip_type) "
        "VALUES (:origin, :destination, :start_date, :end_date, :price, :seats, :trip_type)",
        data,
    )
    conn.commit()
    conn.close()


def update_offer(offer_id, data):
    conn = get_conn()
    result = conn.execute(
        "UPDATE offers SET origin = :origin, destination = :destination, start_date = :start_date, "
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


def popular_offers(limit=3):
    with closing(get_conn()) as conn:
        return conn.execute(
            f"SELECT * FROM ({AVAILABLE_OFFERS}) WHERE available_seats > 0 "
            "ORDER BY (seats - available_seats) DESC, start_date ASC LIMIT ?",
            (limit,),
        ).fetchall()


def bookable_offer(offer_id):
    with closing(get_conn()) as conn:
        return conn.execute(AVAILABLE_OFFERS + " WHERE offers.id = ?", (offer_id,)).fetchone()


def create_reservation(offer_id, participants, user_id=None):
    with closing(get_conn()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        offer = conn.execute(
            AVAILABLE_OFFERS + " WHERE offers.id = ?", (offer_id,)
        ).fetchone()
        if offer is None or not 1 <= participants <= offer["available_seats"]:
            return None
        unit_grosz = round(Decimal(str(offer["price"])) * 100)
        reservation = conn.execute(
            "INSERT INTO reservations (offer_id, user_id, participants, total_grosz) VALUES (?, ?, ?, ?)",
            (offer_id, user_id, participants, unit_grosz * participants),
        )
        return reservation.lastrowid, unit_grosz * participants


def list_reservations():
    with closing(get_conn()) as conn:
        return conn.execute(
            "SELECT reservations.*, offers.origin, offers.destination, users.email AS user_email "
            "FROM reservations "
            "JOIN offers ON offers.id = reservations.offer_id "
            "LEFT JOIN users ON users.id = reservations.user_id "
            "ORDER BY reservations.id DESC"
        ).fetchall()


def list_user_reservations(user_id):
    with closing(get_conn()) as conn:
        return conn.execute(
            "SELECT reservations.*, offers.origin, offers.destination, offers.start_date, offers.end_date "
            "FROM reservations "
            "JOIN offers ON offers.id = reservations.offer_id "
            "WHERE reservations.user_id = ? "
            "ORDER BY reservations.id DESC",
            (user_id,),
        ).fetchall()


def update_reservation_status(reservation_id, status):
    with closing(get_conn()) as conn, conn:
        result = conn.execute(
            "UPDATE reservations SET status = ? WHERE id = ? AND status != 'cancelled'",
            (status, reservation_id),
        )
        return result.rowcount == 1


def update_payment_status(reservation_id, status):
    with closing(get_conn()) as conn, conn:
        result = conn.execute(
            "UPDATE reservations SET payment_status = ? WHERE id = ?",
            (status, reservation_id),
        )
        return result.rowcount == 1