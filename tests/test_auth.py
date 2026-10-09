def test_signup_success(client):
    r = client.post("/newusers", json={"username": "alice", "password": "Passw0rd!"})
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_signup_duplicate_username_rejected(client):
    body = {"username": "alice", "password": "Passw0rd!"}
    client.post("/newusers", json=body)
    r = client.post("/newusers", json=body)
    assert r.status_code == 400


def test_login_returns_bearer_token(client):
    client.post("/newusers", json={"username": "alice", "password": "Passw0rd!"})
    r = client.post("/login", data={"username": "alice", "password": "Passw0rd!"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password_rejected(client):
    client.post("/newusers", json={"username": "alice", "password": "Passw0rd!"})
    r = client.post("/login", data={"username": "alice", "password": "wrong"})
    assert r.status_code == 401


def test_protected_route_without_token_rejected(client):
    r = client.get("/user/all_links")
    assert r.status_code == 401