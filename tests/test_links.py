def test_create_link_requires_auth(client):
    r = client.post("/create_link", json={"original_url": "https://example.com"})
    assert r.status_code == 401


def test_create_link_success(client, make_user):
    headers = make_user()
    r = client.post("/create_link", json={"original_url": "https://example.com"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["short_code"]


def test_same_url_twice_returns_existing_link(client, make_user):
    headers = make_user()
    body = {"original_url": "https://example.com"}
    first = client.post("/create_link", json=body, headers=headers).json()
    second = client.post("/create_link", json=body, headers=headers).json()
    assert second["message"] == "Link already exists"
    assert second["short_code"] == first["short_code"]


def test_users_only_see_their_own_links(client, make_user, make_link):
    alice = make_user("alice")
    bob = make_user("bob")
    make_link(alice, "https://alice.example.com")

    r = client.get("/user/all_links", headers=bob)
    assert r.status_code == 404  # Bob has no links; Alice's must not leak