# Deployment

## Render

Create a Render Web Service connected to this repository. The included `render.yaml` can also create the service configuration automatically from Render's Blueprint flow.

Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
gunicorn --bind 0.0.0.0:$PORT run:app
```

Add these environment variables in Render. Use real values and do not commit them:

```text
SECRET_KEY=<long-random-secret>
ADMIN_USERNAME=<admin-username>
ADMIN_PASSWORD=<strong-admin-password>
```

The app stores its SQLite database and uploaded photos under `instance/`. Attach a persistent Render disk and mount it at:

```text
/opt/render/project/src/instance
```

Without a persistent disk, the database and uploaded photos can be lost during a redeploy.

The Blueprint generates `SECRET_KEY` automatically. Enter `ADMIN_USERNAME` and `ADMIN_PASSWORD` as secret values when Render prompts for them.

After deployment:

```text
https://your-service.onrender.com/
https://your-service.onrender.com/admin/login
```

## Local production-style check

From PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m gunicorn --bind 127.0.0.1:8000 run:app
```

For a larger deployment, move the database to PostgreSQL and uploaded images to persistent object storage such as S3-compatible storage.