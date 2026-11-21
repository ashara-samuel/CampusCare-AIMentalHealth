"""Text-to-speech via ElevenLabs. Isolated + injectable so it's mockable in tests.

Replaces the old insecure PHP endpoint: the key lives in env (never in code), the
caller must be authenticated (see routers/voice.py), input is length-bounded, and
nothing is logged. Raises TTSUnavailable when no key is configured so the API can
return a clean 503 and the UI can fall back to text-only.
"""

from __future__ import annotations

import httpx

from ..config import get_settings

settings = get_settings()


class TTSUnavailable(RuntimeError):
    """No TTS provider configured, or the provider failed."""


def synthesize(text: str) -> bytes:
    if not settings.elevenlabs_api_key:
        raise TTSUnavailable("voice synthesis is not configured")
    try:
        resp = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}",
            headers={
                "xi-api-key": settings.elevenlabs_api_key,
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": settings.elevenlabs_model,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.content
    except httpx.HTTPError as e:
        raise TTSUnavailable("voice synthesis failed") from e
