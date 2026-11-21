"""Test fixtures. A fresh SQLite DB, a stubbed LLM, generous rate limit."""

import os
import pathlib

# Must be set BEFORE importing the app (settings are read at import).
_DB = pathlib.Path(__file__).parent / "_test.db"
if _DB.exists():
    _DB.unlink()
os.environ.update({
    "DATABASE_URL": f"sqlite:///{_DB}",
    "SECRET_KEY": "test-secret-key-not-for-prod",
    "RATE_LIMIT_REQUESTS": "1000",
    "DEBUG": "true",
    "OPENAI_API_KEY": "",
})

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import chat as chat_router


@pytest.fixture(autouse=True)
def _stub_llm(monkeypatch):
    # Never hit the network; return a deterministic reply.
    monkeypatch.setattr(chat_router, "generate_reply",
                        lambda messages: "STUB_REPLY")
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _register(client, email, password="password123"):
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


@pytest.fixture
def auth():
    """Factory: returns an Authorization header dict for a fresh user."""
    def _make(client, email):
        token = _register(client, email)
        return {"Authorization": f"Bearer {token}"}
    return _make
