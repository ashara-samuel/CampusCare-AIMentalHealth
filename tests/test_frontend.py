def test_spa_is_served(client):
    r = client.get("/ui/")
    assert r.status_code == 200
    assert "CampusCare" in r.text
    assert "text/html" in r.headers["content-type"]


def test_privacy_policy_is_served(client):
    r = client.get("/privacy")
    assert r.status_code == 200
    assert "Privacy Policy" in r.text
    assert "text/html" in r.headers["content-type"]
