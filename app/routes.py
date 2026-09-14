import json
import os
from functools import wraps

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash

from .db import get_db
from .images import save_image

public = Blueprint("public", __name__)
admin = Blueprint("admin", __name__)


def event_content(published=True):
    row = get_db().execute("SELECT * FROM event WHERE id = 1").fetchone()
    key = "published_json" if published else "draft_json"
    return json.loads(row[key]), bool(row["is_published"])


@public.get("/")
def home():
    content, is_published = event_content()
    photos = get_db().execute("SELECT * FROM photo WHERE visible = 1 ORDER BY sort_order, id").fetchall()
    return render_template("rsvp.html", content=content, photos=photos, is_published=is_published)


@public.get("/media/<path:filename>")
def media(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@public.post("/rsvp")
def rsvp():
    content, is_published = event_content()
    if not is_published:
        flash("The invitation is not accepting responses yet.", "error")
        return redirect(url_for("public.home") + "#rsvp")
    name = request.form.get("name", "").strip()
    attending = request.form.get("attending", "").strip()
    if not name or attending not in {"yes", "no"}:
        flash("Please add your name and choose an RSVP response.", "error")
        return redirect(url_for("public.home") + "#rsvp")
    party_size = request.form.get("party_size", "1") if content.get("show_party_size") else "1"
    try:
        party_size = max(1, min(12, int(party_size)))
    except ValueError:
        party_size = 1
    get_db().execute(
        "INSERT INTO rsvp (name, attending, party_size, contact, notes, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
        (name, attending, party_size, request.form.get("contact", "").strip(), request.form.get("notes", "").strip()),
    )
    get_db().commit()
    flash("Your response has been tucked safely into our guest book.", "success")
    return redirect(url_for("public.home") + "#rsvp")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapped


@admin.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        expected_user = os.environ.get("ADMIN_USERNAME", "admin")
        expected_hash = os.environ.get("ADMIN_PASSWORD_HASH")
        valid = expected_hash and username == expected_user and check_password_hash(expected_hash, password)
        if not expected_hash:
            valid = username == expected_user and password == os.environ.get("ADMIN_PASSWORD", "admin123")
        if valid:
            session["admin"] = username
            return redirect(url_for("admin.dashboard"))
        flash("Those admin details do not match.", "error")
    return render_template("admin/login.html")


@admin.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("public.home"))


@admin.get("/")
@login_required
def dashboard():
    content, is_published = event_content(False)
    rsvps = get_db().execute("SELECT * FROM rsvp ORDER BY created_at DESC").fetchall()
    photos = get_db().execute("SELECT * FROM photo ORDER BY sort_order, id").fetchall()
    return render_template("admin/dashboard.html", content=content, is_published=is_published, rsvps=rsvps, photos=photos)


@admin.route("/event", methods=["GET", "POST"])
@login_required
def event_editor():
    content, _ = event_content(False)
    if request.method == "POST":
        fields = ["celebrant", "title", "intro", "date", "time", "venue", "address", "story", "dress_code", "gifts", "contact", "rsvp_deadline"]
        content.update({field: request.form.get(field, "").strip() for field in fields})
        content.update({field: request.form.get(field) == "on" for field in ["show_party_size", "show_contact", "show_notes"]})
        db = get_db()
        db.execute("UPDATE event SET draft_json = ?, updated_at = datetime('now') WHERE id = 1", (json.dumps(content),))
        if request.form.get("action") == "publish":
            db.execute("UPDATE event SET published_json = ?, is_published = 1 WHERE id = 1", (json.dumps(content),))
        db.commit()
        message = "The invitation is now live." if request.form.get("action") == "publish" else "The invitation draft was saved."
        flash(message, "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/event.html", content=content)


@admin.post("/photos")
@login_required
def upload_photo():
    uploaded = request.files.get("photo")
    if not uploaded or not uploaded.filename:
        flash("Choose an image before uploading.", "error")
        return redirect(url_for("admin.dashboard"))
    try:
        filename = save_image(uploaded, current_app.config["UPLOAD_FOLDER"])
        next_order = get_db().execute("SELECT COALESCE(MAX(sort_order), -1) + 1 AS next FROM photo").fetchone()["next"]
        get_db().execute("INSERT INTO photo (filename, caption, sort_order) VALUES (?, ?, ?)", (filename, request.form.get("caption", "").strip(), next_order))
        get_db().commit()
        flash("Photo added to the gallery.", "success")
    except (ValueError, OSError):
        flash("That image could not be uploaded. Use a valid JPG, PNG, or WEBP file.", "error")
    return redirect(url_for("admin.dashboard"))


@admin.post("/photos/<int:photo_id>/delete")
@login_required
def delete_photo(photo_id):
    photo = get_db().execute("SELECT * FROM photo WHERE id = ?", (photo_id,)).fetchone()
    if photo:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], photo["filename"])
        if os.path.exists(path):
            os.remove(path)
        get_db().execute("DELETE FROM photo WHERE id = ?", (photo_id,))
        get_db().commit()
    return redirect(url_for("admin.dashboard"))
