"""Crisis handling: the most important behavior to get right."""

from app.routers import chat as chat_router
from app.safety.crisis import detect_crisis


def test_detector_flags_explicit_risk():
    assert detect_crisis("I want to kill myself")
    assert detect_crisis("sometimes I think I'd be better off dead")
    assert detect_crisis("I keep thinking about suicide")


def test_detector_ignores_ordinary_stress():
    assert not detect_crisis("I'm stressed about my exam tomorrow")
    assert not detect_crisis("I had a rough day and feel tired")


def test_crisis_message_bypasses_llm_and_returns_resources(client, auth, monkeypatch):
    # If the LLM is called during a crisis, that's a failure — make it explode.
    def _boom(messages):
        raise AssertionError("LLM must not be called on a crisis message")
    monkeypatch.setattr(chat_router, "generate_reply", _boom)

    headers = auth(client, "student@uni.edu")
    r = client.post("/chat", json={"message": "I want to end my life"}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["crisis_detected"] is True
    assert body["resources"]                      # real help is surfaced
    assert "STUB_REPLY" not in body["reply"]


def test_normal_message_uses_llm(client, auth):
    headers = auth(client, "student2@uni.edu")
    r = client.post("/chat", json={"message": "I'm nervous about my presentation"},
                    headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["crisis_detected"] is False
    assert body["reply"] == "STUB_REPLY"


def test_chat_requires_auth(client):
    assert client.post("/chat", json={"message": "hi"}).status_code == 401
