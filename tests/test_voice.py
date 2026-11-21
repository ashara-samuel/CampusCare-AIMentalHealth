"""Voice output endpoint: auth-gated, 503 when unconfigured, audio when it is."""

from app.routers import voice as voice_router


def test_speak_requires_auth(client):
    assert client.post("/voice/speak", json={"text": "hello"}).status_code == 401


def test_speak_503_when_unconfigured(client, auth):
    # No ELEVENLABS_API_KEY in tests -> feature unavailable, clean 503.
    headers = auth(client, "v1@uni.edu")
    r = client.post("/voice/speak", json={"text": "hello"}, headers=headers)
    assert r.status_code == 503


def test_speak_returns_audio_when_configured(client, auth, monkeypatch):
    monkeypatch.setattr(voice_router, "synthesize", lambda text: b"ID3AUDIOBYTES")
    headers = auth(client, "v2@uni.edu")
    r = client.post("/voice/speak", json={"text": "hello there"}, headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
    assert r.content == b"ID3AUDIOBYTES"


def test_speak_validates_length(client, auth):
    headers = auth(client, "v3@uni.edu")
    assert client.post("/voice/speak", json={"text": ""}, headers=headers).status_code == 422
