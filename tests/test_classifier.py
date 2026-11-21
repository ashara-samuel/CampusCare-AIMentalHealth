"""The second safety layer: model classifier escalation + elevated tier."""

from app.routers import chat as chat_router
from app.safety.classifier import classify


def test_classify_disabled_without_key_returns_none():
    # No OPENAI_API_KEY in tests -> fail-safe to 'none'; the rule-based floor still
    # catches explicit risk regardless.
    assert classify("I feel a bit low today") == "none"


def test_classifier_crisis_bypasses_llm(client, auth, monkeypatch):
    def _boom(messages):
        raise AssertionError("LLM must not be called when the classifier flags crisis")
    monkeypatch.setattr(chat_router, "classify", lambda m: "crisis")
    monkeypatch.setattr(chat_router, "generate_reply", _boom)

    headers = auth(client, "c1@uni.edu")
    r = client.post("/chat", json={"message": "everything feels pointless lately"},
                    headers=headers)
    body = r.json()
    assert body["crisis_detected"] is True
    assert body["resources"]


def test_classifier_elevated_attaches_resources(client, auth, monkeypatch):
    monkeypatch.setattr(chat_router, "classify", lambda m: "elevated")
    headers = auth(client, "c2@uni.edu")
    r = client.post("/chat", json={"message": "I've been really down and hopeless"},
                    headers=headers)
    body = r.json()
    assert body["crisis_detected"] is False
    assert body["elevated"] is True
    assert body["reply"] == "STUB_REPLY"      # still gets a supportive reply
    assert body["resources"]                  # with resources gently attached


def test_classifier_none_is_normal(client, auth, monkeypatch):
    monkeypatch.setattr(chat_router, "classify", lambda m: "none")
    headers = auth(client, "c3@uni.edu")
    r = client.post("/chat", json={"message": "excited about the weekend"}, headers=headers)
    body = r.json()
    assert body["crisis_detected"] is False
    assert body["elevated"] is False
    assert body["reply"] == "STUB_REPLY"
