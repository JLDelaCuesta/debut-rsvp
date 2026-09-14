import sqlite3
from datetime import datetime, timezone

from flask import current_app, g
import json
from datetime import timezone

try:
    from supabase import create_client
except ImportError:  # Local SQLite development does not require the Supabase package.
    create_client = None

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
    "court_gifts": "Amiel Subia\nAubprex Subia\nAriel Subia\nRuben Quequing\nRaniedel Arrogancia\nArvhee Latayan\nCarlo Latayan\nJohn Karl Comendador\nJonnelle Molina\nJarrel Catapang\nYves Mcguire\nJohn Rei Subia\nDustin Manalang\nMark Anthony Subia\nJohn Lester Quequing\nArbench Subia\nZid Andrei Vela\nMJ Molina",
    "court_bluebills": "Amiel Subia\nAubprex Subia\nAriel Subia\nRuben Quequing\nRaniedel Arrogancia\nArvhee Latayan\nCarlo Latayan\nJohn Karl Comendador\nJonnelle Molina\nJarrel Catapang\nYves Mcguire\nJohn Rei Subia\nDustin Manalang\nMark Anthony Subia\nJohn Lester Quequing\nArbench Subia\nZid Andrei Vela\nMJ Molina",
    "court_roses": "Kwin Lyka Esclamado\nSheena Rayne Espiritu\nDaniella Jaile Lacap\nElyssa Fhay Zoilo\nHannah Dela Cueva\nJhorlyn Cornejo\nSarah Garcia\nEricka Quequing\nJayanne Manalang\nFlorentine Principe\nAmiel Subia\nAubprex Subia\nAriel Subia\nRuben Quequing\nRaniedel Arrogancia\nArvhee Latayan\nCarlo Latayan\nJonnelle Molina",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS event (id INTEGER PRIMARY KEY CHECK (id = 1), draft_json TEXT NOT NULL, published_json TEXT NOT NULL, is_published INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS rsvp (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, attending TEXT NOT NULL, party_size INTEGER NOT NULL DEFAULT 1, contact TEXT, notes TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS photo (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, caption TEXT NOT NULL DEFAULT '', sort_order INTEGER NOT NULL DEFAULT 0, visible INTEGER NOT NULL DEFAULT 1);
"""

def using_supabase():
    return bool(current_app.config.get("SUPABASE_URL") and current_app.config.get("SUPABASE_SERVICE_ROLE_KEY"))

def get_supabase():
    if "supabase" not in g:
        if not using_supabase() or create_client is None:
            raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
        g.supabase = create_client(current_app.config["SUPABASE_URL"], current_app.config["SUPABASE_SERVICE_ROLE_KEY"])
    return g.supabase

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
    g.pop("supabase", None)

def init_db(app):
    if using_supabase_for_app(app):
        return
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        if db.execute("SELECT id FROM event WHERE id = 1").fetchone() is None:
            content = json.dumps(DEFAULT_CONTENT)
            db.execute("INSERT INTO event (id, draft_json, published_json, updated_at) VALUES (1, ?, ?, ?)", (content, content, datetime.now(timezone.utc).isoformat()))
        db.commit()
    app.teardown_appcontext(close_db)

def using_supabase_for_app(app):
    return bool(app.config.get("SUPABASE_URL") and app.config.get("SUPABASE_SERVICE_ROLE_KEY"))

def fetch_event():
    if using_supabase():
        result = get_supabase().table("event").select("*").eq("id", 1).limit(1).execute()
        rows = result.data if result is not None and result.data else []
        if not rows:
            content = {**DEFAULT_CONTENT}
            get_supabase().table("event").insert({"id": 1, "draft_json": content, "published_json": content, "is_published": False}).execute()
            return {"draft_json": content, "published_json": content, "is_published": False}
        return rows[0]
    return get_db().execute("SELECT * FROM event WHERE id = 1").fetchone()

def read_event(published=True):
    row = fetch_event()
    key = "published_json" if published else "draft_json"
    value = row[key]
    content = json.loads(value) if isinstance(value, str) else value
    content = {**DEFAULT_CONTENT, **content}
    return content, bool(row["is_published"])

def fetch_photos(visible_only=True):
    if using_supabase():
        query = get_supabase().table("photo").select("*").order("sort_order").order("id")
        if visible_only:
            query = query.eq("visible", True)
        return query.execute().data or []
    query = "SELECT * FROM photo WHERE visible = 1 ORDER BY sort_order, id" if visible_only else "SELECT * FROM photo ORDER BY sort_order, id"
    return get_db().execute(query).fetchall()

def insert_rsvp(name, attending, party_size, contact, notes):
    values = {"name": name, "attending": attending, "party_size": party_size, "contact": contact, "notes": notes}
    if using_supabase():
        get_supabase().table("rsvp").insert(values).execute()
        return
    get_db().execute("INSERT INTO rsvp (name, attending, party_size, contact, notes, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))", (name, attending, party_size, contact, notes))
    get_db().commit()

def fetch_rsvps():
    if using_supabase():
        return get_supabase().table("rsvp").select("*").order("created_at", desc=True).execute().data or []
    return get_db().execute("SELECT * FROM rsvp ORDER BY created_at DESC").fetchall()

def save_event(content, publish=False):
    if using_supabase():
        values = {"draft_json": content, "updated_at": datetime.now(timezone.utc).isoformat()}
        if publish:
            values.update({"published_json": content, "is_published": True})
        get_supabase().table("event").update(values).eq("id", 1).execute()
        return
    db = get_db()
    db.execute("UPDATE event SET draft_json = ?, updated_at = datetime('now') WHERE id = 1", (json.dumps(content),))
    if publish:
        db.execute("UPDATE event SET published_json = ?, is_published = 1 WHERE id = 1", (json.dumps(content),))
    db.commit()

def insert_photo(filename, caption, sort_order):
    values = {"filename": filename, "caption": caption, "sort_order": sort_order, "visible": True}
    if using_supabase():
        return get_supabase().table("photo").insert(values).execute().data[0]
    row = get_db().execute("INSERT INTO photo (filename, caption, sort_order) VALUES (?, ?, ?)", (filename, caption, sort_order))
    get_db().commit()
    return {"id": row.lastrowid, **values}

def next_photo_order():
    if using_supabase():
        photos = fetch_photos(False)
        return max((photo["sort_order"] for photo in photos), default=-1) + 1
    return get_db().execute("SELECT COALESCE(MAX(sort_order), -1) + 1 AS next FROM photo").fetchone()["next"]

def find_photo(photo_id):
    if using_supabase():
        result = get_supabase().table("photo").select("*").eq("id", photo_id).limit(1).execute()
        rows = result.data if result is not None and result.data else []
        return rows[0] if rows else None
    return get_db().execute("SELECT * FROM photo WHERE id = ?", (photo_id,)).fetchone()

def delete_photo_record(photo_id):
    if using_supabase():
        get_supabase().table("photo").delete().eq("id", photo_id).execute()
        return
    get_db().execute("DELETE FROM photo WHERE id = ?", (photo_id,))
    get_db().commit()


def upload_photo_file(filename, image_bytes):
    if not using_supabase():
        return
    bucket = current_app.config["SUPABASE_STORAGE_BUCKET"]
    get_supabase().storage.from_(bucket).upload(filename, image_bytes, {"content-type": "image/jpeg", "upsert": "false"})


def delete_photo_file(filename):
    if using_supabase():
        get_supabase().storage.from_(current_app.config["SUPABASE_STORAGE_BUCKET"]).remove([filename])
    else:
        import os
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(path):
            os.remove(path)


def public_photo_url(filename):
    if using_supabase():
        return get_supabase().storage.from_(current_app.config["SUPABASE_STORAGE_BUCKET"]).get_public_url(filename)
    return None
