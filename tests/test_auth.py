def test_register_and_login(client):
    r = client.post("/auth/register", json={"email": "a@uni.edu", "password": "password123"})
    assert r.status_code == 201
    assert r.json()["access_token"]

    r = client.post("/auth/login", json={"email": "a@uni.edu", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_duplicate_registration_rejected(client):
    client.post("/auth/register", json={"email": "dup@uni.edu", "password": "password123"})
    r = client.post("/auth/register", json={"email": "dup@uni.edu", "password": "password123"})
    assert r.status_code == 409


def test_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "b@uni.edu", "password": "password123"})
    r = client.post("/auth/login", json={"email": "b@uni.edu", "password": "wrongpass"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401


def test_weak_password_rejected(client):
    r = client.post("/auth/register", json={"email": "c@uni.edu", "password": "short"})
    assert r.status_code == 422  # pydantic min_length
