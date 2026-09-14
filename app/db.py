import sqlite3
from datetime import datetime, timezone

from flask import current_app, g


SCHEMA = """
CREATE TABLE IF NOT EXISTS event (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    draft_json TEXT NOT NULL,
    published_json TEXT NOT NULL,
    is_published INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rsvp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    attending TEXT NOT NULL,
    party_size INTEGER NOT NULL DEFAULT 1,
    contact TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS photo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    caption TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    visible INTEGER NOT NULL DEFAULT 1
);
"""

DEFAULT_CONTENT = {
    "celebrant": "Isabella Rose",
    "title": "A Night of Enchantment",
    "intro": "With hearts full of wonder, we invite you to celebrate a magical milestone.",
    "date": "Saturday, 14 November 2026",
    "time": "5:00 PM onwards",
    "venue": "The Starlit Garden",
    "address": "Garden Hall, Moonflower Avenue",
    "story": "Eighteen chapters have bloomed, and a beautiful new story begins. Come dressed in your favorite fairytale and make this evening unforgettable.",
    "dress_code": "Enchanted garden formal",
    "gifts": "Your presence is the loveliest gift. A handwritten wish is always welcome.",
    "contact": "For questions, please reach out to the family.",
    "rsvp_deadline": "Please respond by 30 October 2026.",
    "show_party_size": True,
    "show_contact": True,
    "show_notes": True,
}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        if db.execute("SELECT id FROM event WHERE id = 1").fetchone() is None:
            import json
            content = json.dumps(DEFAULT_CONTENT)
            db.execute(
                "INSERT INTO event (id, draft_json, published_json, updated_at) VALUES (1, ?, ?, ?)",
                (content, content, datetime.now(timezone.utc).isoformat()),
            )
        db.commit()
    app.teardown_appcontext(close_db)
