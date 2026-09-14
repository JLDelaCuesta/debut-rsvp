# Deployment

## Render

Create a Render Web Service connected to this repository. The included `render.yaml` can also create the service configuration automatically from Render's Blueprint flow.

This deployment uses Supabase for the database and photo storage, so it does not require a paid Render persistent disk.

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
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<server-only-service-role-key>
SUPABASE_STORAGE_BUCKET=photos
```

## Supabase setup

1. Create a Supabase project.
2. Open the Supabase SQL Editor and run [supabase/schema.sql](supabase/schema.sql).
3. Copy the project URL and the server-only `service_role` key into Render environment variables.
4. Keep the `photos` Storage bucket public because guest photo URLs are served from it.
5. Do not expose `SUPABASE_SERVICE_ROLE_KEY` in templates, JavaScript, or client-side code.

The Blueprint generates `SECRET_KEY` automatically. Enter the admin and Supabase values as secret values when Render prompts for them. `SUPABASE_STORAGE_BUCKET` can remain `photos`.

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

For a larger deployment, use Supabase backups and review Row Level Security policies before exposing additional APIs.