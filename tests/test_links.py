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
    assert r.status_code == 200
    assert r.json() == []  # Bob has no links; Alice's must not leak


def test_pagination_limits_results(client, make_user, make_link):
    user = make_user("paginated_user")
    make_link(user, "https://link1.com")
    make_link(user, "https://link2.com")
    make_link(user, "https://link3.com")

    r = client.get("/user/all_links?limit=2&offset=0", headers=user)
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_create_link_with_custom_alias(client, make_user):
    user = make_user("alias_user")
    r = client.post("/create_link", json={"original_url": "https://example.com/custom", "custom_alias": "myalias"}, headers=user)
    assert r.status_code == 200
    assert r.json()["short_code"] == "alias_user/myalias"


def test_create_link_duplicate_custom_alias_rejected(client, make_user):
    user = make_user("alias_user_2")
    r1 = client.post("/create_link", json={"original_url": "https://url1.com", "custom_alias": "taken"}, headers=user)
    assert r1.status_code == 200
    r2 = client.post("/create_link", json={"original_url": "https://url2.com", "custom_alias": "taken"}, headers=user)
    assert r2.status_code == 409


def test_update_shorturl(client, make_user, make_link):
    user = make_user("update_user")
    code = make_link(user, "https://old.com")
    r = client.put(f"/shorturl_update/{code}/", json={"original_url": "https://new.com"}, headers=user)
    assert r.status_code == 200


def test_delete_shorturl(client, make_user, make_link):
    user = make_user("del_user")
    code = make_link(user, "https://to-delete.com")
    r = client.delete(f"/shorturl_delete/{code}/", headers=user)
    assert r.status_code == 200


def test_stats_count_and_history(client, make_user, make_link):
    user = make_user("stats_user")
    code = make_link(user, "https://stats.com")
    client.get(f"/{code}", follow_redirects=False)

    r_count = client.get(f"/user/link/clicks/stats/count/{code}", headers=user)
    assert r_count.status_code == 200
    assert r_count.json() == 1

    r_hist = client.get(f"/user/link/clicks/stats/history/{code}", headers=user)
    assert r_hist.status_code == 200
    assert len(r_hist.json()) == 1