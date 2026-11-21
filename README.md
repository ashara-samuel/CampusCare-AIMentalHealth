# CampusCare

A student wellbeing companion — a clean, hostable rebuild of the CampusCare /
MoralPath mental-health app, built so it starts from a security- and
safety-pass-able baseline rather than needing one bolted on.

FastAPI + SQLAlchemy, pure-env configuration, JWT auth, per-user data isolation,
and a crisis-detection safety layer that runs **before** the model.

## Why it's built this way

The hard part of a mental-health AI isn't the chat — it's the guardrails. So the
guardrails are the architecture:

- **Secrets only from env.** Nothing hardcoded; `.env` is gitignored; config warns
  loudly if production is misconfigured.
- **Real auth.** Passwords bcrypt-hashed, JWT bearer tokens, generic error messages
  (no user enumeration).
- **Per-user isolation.** Every note query is scoped to the authenticated user —
  one student can never read, edit, or delete another's notes (no IDOR). Covered
  by tests.
- **Two-layer crisis safety.** `app/safety/` runs a deterministic rule-based
  detector (the guaranteed floor) **and** a model-based classifier (for subtler
  signals — passive ideation, hopelessness) *before* the model. On a crisis hit
  from either layer, the LLM is **bypassed entirely** and the user gets a caring
  hand-off plus real crisis resources; an "elevated" reading still gives a
  supportive reply with resources gently attached. The classifier is fail-safe
  (errors degrade to the rule-based floor) and never lowers risk. The counselor
  prompt is non-clinical and never claims to replace professional care.
- **Conversation memory, handled with care.** The counselor remembers recent
  turns (a bounded window) so it has continuity instead of answering each message
  cold. That history is sensitive, so it's scoped to the owning user, never logged,
  and the user can wipe it any time (`DELETE /chat/history`). The crisis gate runs
  on every new message regardless of history. (Production: encrypt at rest + set a
  retention policy.)
- **No sensitive logging.** Chat content is never written to logs.
- **Hardened transport.** Security headers (CSP, HSTS, nosniff, frame-deny),
  locked-down CORS, in-memory rate limiting, docs hidden outside debug.
- **ORM everywhere.** No string-built SQL → no SQL injection.

## Run it

```bash
cp .env.example .env            # set SECRET_KEY (and OPENAI_API_KEY if you have one)
make install
make test                       # 15 tests
make dev                        # http://localhost:8000
```

Then open the app UI at **http://localhost:8000/ui/** (register, chat, notes).
API docs are at `/docs` in debug mode.

Or containerized (app + Postgres):

```bash
export SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(48))")
make docker
```

## Deploy

Deploy-ready: binds `$PORT`, Postgres driver included, tables auto-created on
first boot, `/healthz` check. One-click on **Render** via `render.yaml` (web
service + free Postgres, auto-generated secret). Full steps — and Fly/Railway
alternatives — in [`DEPLOY.md`](./DEPLOY.md).

## API

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/auth/register` | — | create account, returns JWT |
| POST | `/auth/login` | — | returns JWT |
| GET  | `/auth/me` | ✓ | current user |
| GET/POST | `/notes` | ✓ | list / create (own only) |
| GET/PUT/DELETE | `/notes/{id}` | ✓ | read / update / delete (own only) |
| POST | `/chat` | ✓ | counselor reply, crisis-gated, with memory |
| GET/DELETE | `/chat/history` | ✓ | view / clear your conversation (own only) |
| POST | `/voice/speak` | ✓ | text-to-speech of a reply (503 if unconfigured) |
| GET | `/healthz` | — | liveness |

## Voice

Hands-free, and privacy-first by design:

- **Speech-to-text (input)** runs entirely **in the browser** (Web Speech API) — a
  student's audio never leaves their device; only the final text is sent, through
  the same auth + crisis-safety path as typed chat.
- **Text-to-speech (output)** uses the browser's built-in `SpeechSynthesis` by
  default — **free, no API key, no backend call, works offline.** Toggle "🔊 Voice"
  in the chat header to hear replies; tap 🎤 to speak.
- **Optional upgrade:** an auth-gated `/voice/speak` endpoint can proxy ElevenLabs
  (key from env) for higher-quality voices. It's there if you want it; the UI
  doesn't require it.

## Layout

```
app/
  main.py          # app + middleware (headers, rate limit, CORS), lifespan
  config.py        # env-based settings + production safety assertions
  db.py models.py  # SQLAlchemy engine + User/Note
  security.py      # bcrypt hashing, JWT
  deps.py          # auth dependency (get_current_user)
  schemas.py       # validated request/response models
  safety/          # crisis.py (detection + escalation) + guardrails.py (prompt)
  services/llm.py  # provider wrapper (swappable, safe fallback)
  routers/         # auth / notes / chat
frontend/          # static SPA (index.html + app.js + styles.css), served at /ui
tests/             # auth, per-user scoping, crisis, security headers, SPA
Dockerfile docker-compose.yml .github/workflows/ci.yml
```

## Scope & limits (honest notes)

- Crisis detection here is a deterministic first layer tuned to over-escalate. For
  production, pair it with a model-based classifier — this is the floor, not the
  ceiling.
- Rate limiting is in-memory (single instance). Use Redis for multi-instance.
- This is a support tool, **not** a therapist or crisis service, and it says so to
  users.

## License

MIT.
