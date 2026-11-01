"""SQLite storage for Pocket Ledger. All SQL lives here."""
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import date, timedelta

DB_PATH = os.environ.get(
    "EXPENSE_DB",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db"),
)
EXPENSE_CATEGORIES = ["Food", "Travel", "Shopping", "Education",
                      "Entertainment", "Bills", "Healthcare", "Other"]
INCOME_CATEGORY = "Income"


class DatabaseError(Exception):
    """Raised for any problem talking to the database."""


@contextmanager
def _connect():
    try:
        con = sqlite3.connect(DB_PATH, timeout=10)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Database error: {exc}") from exc


def init_db():
    with _connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                type        TEXT NOT NULL CHECK (type IN ('Income', 'Expense')),
                amount      REAL NOT NULL CHECK (amount > 0),
                category    TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                date        TEXT NOT NULL
            )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date)")


def add_transaction(kind, amount, category, description, day):
    with _connect() as con:
        cur = con.execute(
            "INSERT INTO transactions (type, amount, category, description, date) "
            "VALUES (?, ?, ?, ?, ?)",
            (kind, amount, category, description, day))
        return cur.lastrowid


def update_transaction(tx_id, amount, category, description, day):
    with _connect() as con:
        cur = con.execute(
            "UPDATE transactions SET amount=?, category=?, description=?, date=? WHERE id=?",
            (amount, category, description, day, tx_id))
        if cur.rowcount == 0:
            raise DatabaseError("That entry no longer exists.")


def delete_transaction(tx_id):
    with _connect() as con:
        cur = con.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
        if cur.rowcount == 0:
            raise DatabaseError("That entry no longer exists.")


def get_transactions():
    """All transactions, newest first, as a list of dicts."""
    with _connect() as con:
        rows = con.execute(
            "SELECT id, type, amount, category, description, date "
            "FROM transactions ORDER BY date DESC, id DESC").fetchall()
    return [dict(r) for r in rows]


# ---------- sample data ----------
_BASE = [  # (days ago, type, amount, category, description)
    (2, "Income", 45000, "Income", "Monthly salary"),
    (12, "Income", 3500, "Income", "Freelance project"),
    (1, "Expense", 420, "Food", "Groceries"),
    (3, "Expense", 150, "Travel", "Bus pass top-up"),
    (4, "Expense", 2300, "Shopping", "New shoes"),
    (5, "Expense", 1200, "Bills", "Electricity bill"),
    (6, "Expense", 600, "Entertainment", "Movie night"),
    (8, "Expense", 850, "Healthcare", "Pharmacy"),
    (9, "Expense", 3000, "Education", "Online course"),
    (10, "Expense", 280, "Food", "Lunch with friends"),
    (14, "Expense", 499, "Bills", "Mobile recharge"),
    (16, "Expense", 90, "Other", "Stationery"),
]


def seed_sample_data():
    """Insert ~3 months of sample data, only if the table is empty."""
    if get_transactions():
        return 0
    today, count = date.today(), 0
    for shift, factor in ((0, 1.0), (30, 0.9), (60, 1.15)):
        for ago, kind, amount, cat, desc in _BASE:
            amt = amount if kind == "Income" else round(amount * factor, 2)
            day = (today - timedelta(days=ago + shift)).isoformat()
            add_transaction(kind, amt, cat, desc, day)
            count += 1
    return count


if __name__ == "__main__":
    init_db()
    if "--seed" in sys.argv:
        n = seed_sample_data()
        print(f"Inserted {n} sample transactions." if n else "Database not empty; nothing inserted.")
    else:
        print(f"Database ready at {DB_PATH}. Use --seed to load sample data.")
