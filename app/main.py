"""Application entrypoint: wires middleware (security headers, rate limit, CORS),
routers, and startup. Secrets come from env; nothing sensitive is logged."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import init_db
from .routers import auth, chat, notes, voice
from .safety.guardrails import DISCLAIMER

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    for problem in settings.assert_production_safe():
        print(f"[CONFIG WARNING] {problem}")   # fail loud, never silently unsafe
    yield


app = FastAPI(
    title="CampusCare",
    version="1.0.0",
    description="Student wellbeing companion — scoped, safe, auditable.",
    docs_url="/docs" if settings.debug else None,   # hide schema in prod
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ---- security headers -------------------------------------------------

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    for k, v in _SECURITY_HEADERS.items():
        response.headers.setdefault(k, v)
    return response


# ---- naive fixed-window rate limiter ---------------------------------
# In-memory; fine for a single instance. Use Redis for multi-instance prod.
_hits: dict[str, list[float]] = defaultdict(list)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path in ("/healthz", "/"):
        return await call_next(request)
    client = request.client.host if request.client else "unknown"
    now = time.time()
    window = settings.rate_limit_window_seconds
    hits = [t for t in _hits[client] if now - t < window]
    if len(hits) >= settings.rate_limit_requests:
        return JSONResponse({"detail": "Rate limit exceeded"},
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS)
    hits.append(now)
    _hits[client] = hits
    return await call_next(request)


# ---- routes -----------------------------------------------------------

app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(chat.router)
app.include_router(voice.router)


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/", tags=["meta"])
def root() -> dict:
    return {"service": "CampusCare", "disclaimer": DISCLAIMER}


# Serve the static frontend at /ui (same-origin -> no CORS needed for the SPA).
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


@app.get("/privacy", include_in_schema=False)
def privacy() -> FileResponse:
    """Public privacy policy — a stable URL for store listings and the app footer."""
    return FileResponse(os.path.join(_FRONTEND_DIR, "privacy.html"))


if os.path.isdir(_FRONTEND_DIR):
    app.mount("/ui", StaticFiles(directory=_FRONTEND_DIR, html=True), name="ui")
