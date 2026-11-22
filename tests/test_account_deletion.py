"""Account deletion — a hard App Store / Google Play requirement, so it must
actually remove the account and all its data."""


def test_delete_account_requires_auth(client):
    assert client.delete("/auth/me").status_code == 401


def test_delete_account_removes_user_and_data(client, auth):
    headers = auth(client, "gone@uni.edu")
    client.post("/notes", json={"title": "n", "text": "x"}, headers=headers)
    client.post("/chat", json={"message": "hello"}, headers=headers)

    assert client.delete("/auth/me", headers=headers).status_code == 204

    # Token no longer resolves to a user; login with the same creds fails.
    assert client.get("/auth/me", headers=headers).status_code == 401
    assert client.post("/auth/login",
                       json={"email": "gone@uni.edu", "password": "password123"}
                       ).status_code == 401
    # The email is free again (data really gone, not just flagged).
    assert client.post("/auth/register",
                       json={"email": "gone@uni.edu", "password": "password123"}
                       ).status_code == 201


def test_delete_account_is_scoped_to_caller(client, auth):
    a = auth(client, "keep@uni.edu")
    b = auth(client, "delete@uni.edu")
    client.post("/notes", json={"title": "a-note", "text": "x"}, headers=a)

    assert client.delete("/auth/me", headers=b).status_code == 204
    # The other user is untouched.
    assert client.get("/auth/me", headers=a).status_code == 200
    assert len(client.get("/notes", headers=a).json()) == 1
