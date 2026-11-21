"""LLM provider wrapper. Isolated so the provider/model is swappable and so tests
can stub it without network access. If no API key is configured, it returns a
safe, supportive fallback rather than failing."""

from __future__ import annotations

import httpx

from ..config import get_settings

settings = get_settings()

_FALLBACK = (
    "Thanks for sharing that with me. I'm here to listen. It sounds like a lot to "
    "carry — would it help to talk through what's been weighing on you most? And "
    "remember your campus wellbeing service is there for you too."
)


def generate_reply(messages: list[dict]) -> str:
    """Return the counselor reply for the given chat messages.

    Kept synchronous and dependency-light so it's trivial to stub in tests.
    Any provider error degrades to the safe fallback — the user still gets a
    caring response, never a stack trace.
    """
    if not settings.openai_api_key:
        return _FALLBACK
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.openai_model, "messages": messages,
                  "temperature": 0.7, "max_tokens": 400},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip() or _FALLBACK
    except Exception:  # noqa: BLE001 — never leak provider errors to the student
        return _FALLBACK
