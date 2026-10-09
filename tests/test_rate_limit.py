def test_login_is_rate_limited_after_5_attempts(client):
    for _ in range(5):
        r = client.post("/login", data={"username": "x", "password": "y"})
        assert r.status_code == 401          # wrong creds, but allowed through

    r = client.post("/login", data={"username": "x", "password": "y"})
    assert r.status_code == 429
    assert "retry-after" in r.headers


def test_redirect_is_rate_limited_after_60_requests(client, make_user, make_link):
    code = make_link(make_user())
    for _ in range(60):
        assert client.get(f"/{code}", follow_redirects=False).status_code == 307

    assert client.get(f"/{code}", follow_redirects=False).status_code == 429


def test_rate_limit_scopes_are_independent(client, make_user, make_link):
    code = make_link(make_user())
    for _ in range(6):
        client.post("/login", data={"username": "x", "password": "y"})  # exhaust login limit

    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 307  # redirects are unaffected