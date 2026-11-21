"""The core authorization property: no user can touch another user's notes."""


def test_notes_are_private_between_users(client, auth):
    alice = auth(client, "alice@uni.edu")
    bob = auth(client, "bob@uni.edu")

    created = client.post("/notes", json={"title": "mine", "text": "secret"}, headers=alice)
    assert created.status_code == 201
    note_id = created.json()["id"]

    # Bob cannot read, edit, or delete Alice's note -> 404 (not 403, no existence leak).
    assert client.get(f"/notes/{note_id}", headers=bob).status_code == 404
    assert client.put(f"/notes/{note_id}", json={"title": "x", "text": "y"},
                      headers=bob).status_code == 404
    assert client.delete(f"/notes/{note_id}", headers=bob).status_code == 404

    # Bob's list does not include Alice's note.
    assert client.get("/notes", headers=bob).json() == []

    # Alice still can.
    assert client.get(f"/notes/{note_id}", headers=alice).status_code == 200


def test_notes_require_auth(client):
    assert client.get("/notes").status_code == 401
    assert client.post("/notes", json={"title": "t", "text": "x"}).status_code == 401
