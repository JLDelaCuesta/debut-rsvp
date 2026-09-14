import os
from functools import wraps

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash

from .db import court_names, delete_photo_file, delete_photo_record, fetch_photos, fetch_rsvps, find_photo, insert_photo, insert_rsvp, next_photo_order, public_photo_url, read_event, save_event, upload_photo_file
from .images import process_image, save_image_bytes

public = Blueprint("public", __name__)
admin = Blueprint("admin", __name__)


def event_content(published=True):
    return read_event(published)


@public.get("/")
def home():
    content, is_published = event_content()
    photos = fetch_photos()
    court_lists = {
        "gifts": court_names(content["court_gifts"]),
        "bluebills": court_names(content["court_bluebills"]),
        "roses": court_names(content["court_roses"]),
    }
    return render_template("rsvp.html", content=content, photos=photos, court_lists=court_lists, is_published=is_published)


@public.get("/media/<path:filename>")
def media(filename):
    remote_url = public_photo_url(filename)
    if remote_url:
        return redirect(remote_url)
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
    insert_rsvp(name, attending, party_size, request.form.get("contact", "").strip(), request.form.get("notes", "").strip())
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
    rsvps = fetch_rsvps()
    photos = fetch_photos(False)
    return render_template("admin/dashboard.html", content=content, is_published=is_published, rsvps=rsvps, photos=photos)


@admin.route("/event", methods=["GET", "POST"])
@login_required
def event_editor():
    content, _ = event_content(False)
    if request.method == "POST":
        fields = ["celebrant", "title", "intro", "date", "time", "venue", "address", "story", "dress_code", "gifts", "contact", "rsvp_deadline", "court_gifts", "court_bluebills", "court_roses"]
        content.update({field: request.form.get(field, "").strip() for field in fields})
        content.update({field: request.form.get(field) == "on" for field in ["show_party_size", "show_contact", "show_notes"]})
        save_event(content, request.form.get("action") == "publish")
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
        filename, image_bytes = process_image(uploaded)
        if current_app.config.get("SUPABASE_URL") and current_app.config.get("SUPABASE_SERVICE_ROLE_KEY"):
            upload_photo_file(filename, image_bytes)
        else:
            save_image_bytes(filename, image_bytes, current_app.config["UPLOAD_FOLDER"])
        insert_photo(filename, request.form.get("caption", "").strip(), next_photo_order())
        flash("Photo added to the gallery.", "success")
    except (ValueError, OSError):
        flash("That image could not be uploaded. Use a valid JPG, PNG, or WEBP file.", "error")
    return redirect(url_for("admin.dashboard"))


@admin.post("/photos/<int:photo_id>/delete")
@login_required
def delete_photo(photo_id):
    photo = find_photo(photo_id)
    if photo:
        delete_photo_file(photo["filename"])
        delete_photo_record(photo_id)
    return redirect(url_for("admin.dashboard"))
