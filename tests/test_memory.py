"""Conversation memory: persistence, context passed to the model, per-user
scoping, and user-controlled deletion."""

from app.routers import chat as chat_router


def test_history_persists_and_is_returned(client, auth):
    headers = auth(client, "mem1@uni.edu")
    client.post("/chat", json={"message": "hello"}, headers=headers)
    client.post("/chat", json={"message": "how are you"}, headers=headers)
    hist = client.get("/chat/history", headers=headers).json()
    assert len(hist) == 4                       # 2 user + 2 assistant turns
    assert hist[0]["role"] == "user" and hist[0]["content"] == "hello"
    assert hist[1]["role"] == "assistant"


def test_prior_turns_are_passed_to_the_model(client, auth, monkeypatch):
    captured = {}

    def recorder(messages):
        captured["messages"] = messages
        return "REPLY"

    headers = auth(client, "mem2@uni.edu")
    client.post("/chat", json={"message": "my name is Sam"}, headers=headers)  # autouse stub
    monkeypatch.setattr(chat_router, "generate_reply", recorder)
    client.post("/chat", json={"message": "what is my name?"}, headers=headers)

    contents = [m["content"] for m in captured["messages"]]
    assert "my name is Sam" in contents          # prior turn is in context
    assert "what is my name?" in contents         # new message is last


def test_history_is_scoped_per_user(client, auth):
    a = auth(client, "mem_a@uni.edu")
    b = auth(client, "mem_b@uni.edu")
    client.post("/chat", json={"message": "private thing"}, headers=a)
    assert client.get("/chat/history", headers=b).json() == []


def test_clear_history(client, auth):
    headers = auth(client, "mem3@uni.edu")
    client.post("/chat", json={"message": "remember this"}, headers=headers)
    assert client.delete("/chat/history", headers=headers).status_code == 204
    assert client.get("/chat/history", headers=headers).json() == []


def test_crisis_turn_is_persisted(client, auth):
    headers = auth(client, "mem4@uni.edu")
    r = client.post("/chat", json={"message": "I want to kill myself"}, headers=headers)
    assert r.json()["crisis_detected"] is True
    hist = client.get("/chat/history", headers=headers).json()
    assert len(hist) == 2                         # user turn + crisis hand-off stored
    assert hist[1]["role"] == "assistant"


def test_history_requires_auth(client):
    assert client.get("/chat/history").status_code == 401
    assert client.delete("/chat/history").status_code == 401
