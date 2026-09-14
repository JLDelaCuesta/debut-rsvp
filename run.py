import os

from flask import Flask

from app.db import init_db
from app.routes import admin, public


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-this-key"),
        DATABASE=os.path.join(app.instance_path, "debut.sqlite3"),
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
        SUPABASE_URL=os.environ.get("SUPABASE_URL"),
        SUPABASE_SERVICE_ROLE_KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
        SUPABASE_STORAGE_BUCKET=os.environ.get("SUPABASE_STORAGE_BUCKET", "photos"),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    init_db(app)
    app.register_blueprint(public)
    app.register_blueprint(admin, url_prefix="/admin")
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)