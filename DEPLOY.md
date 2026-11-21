# Deploying CampusCare

The repo is deploy-ready: a `Dockerfile` (non-root, binds `$PORT`), a Postgres
driver, auto table creation on first boot, and a `/healthz` check. Below is the
fastest path (Render), plus notes for Fly and Railway.

Tables are created automatically on startup, so there is no separate migration
step for the first deploy.

## Render (recommended — free tier, one blueprint)

1. Push this repo to GitHub (done).
2. In **Render → New → Blueprint**, connect this repo. Render reads
   `render.yaml` and provisions a **web service** (from the Dockerfile) + a
   **free Postgres** database, and auto-generates `SECRET_KEY`.
3. Click **Apply**. First build takes a few minutes.
4. (Optional) In the service's **Environment** tab, set:
   - `OPENAI_API_KEY` — your **new** key, for real counselor replies (without it,
     chat returns the safe fallback).
   - `ELEVENLABS_API_KEY` — your **new** key, for spoken replies (without it,
     voice output is disabled and the UI stays text-only).
5. Open the service URL → the API is at `/`, the app UI at **`/ui/`**.

Notes: Render's free web service sleeps when idle (first request after a nap is
slow), and free Postgres is time-limited — fine for a demo, upgrade for real use.

## Fly.io (Docker, global)

```bash
fly launch --no-deploy          # generates fly.toml from the Dockerfile
fly postgres create             # then: fly postgres attach <db>  (sets DATABASE_URL)
fly secrets set SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(48))")
fly secrets set OPENAI_API_KEY=...   ELEVENLABS_API_KEY=...   # optional
fly deploy
```
Make sure the internal port matches `$PORT` (the Dockerfile already honours it).

## Railway

New Project → Deploy from GitHub repo → add a **Postgres** plugin (sets
`DATABASE_URL`) → set `SECRET_KEY` (and optional keys) in **Variables**. Railway
builds from the Dockerfile and injects `$PORT` automatically.

## Before a real (non-demo) launch

This handles students' mental-health data, so beyond "it runs":
- Put it behind HTTPS (all three providers give you TLS by default).
- Encrypt conversation history at rest and set a retention policy.
- Swap the in-memory rate limiter for Redis if you run more than one instance.
- Use Alembic migrations instead of `create_all` once the schema is live.
- Lock `CORS_ORIGINS` to your real domain if you split the frontend off.
