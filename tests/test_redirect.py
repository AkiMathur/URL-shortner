from app.models.clicks_model import Clicks


def test_redirect_sends_user_to_original_url(client, make_user, make_link):
    code = make_link(make_user(), "https://example.com")
    r = client.get(f"/{code}", follow_redirects=False)  # don't follow, inspect the redirect itself
    assert r.status_code == 307
    assert r.headers["location"].startswith("https://example.com")


def test_unknown_code_returns_404(client):
    r = client.get("/doesnotexist", follow_redirects=False)
    assert r.status_code == 404


def test_redirect_populates_cache(client, make_user, make_link, fake_redis):
    code = make_link(make_user())
    assert fake_redis.get(f"link:{code}") is None       # cold cache
    client.get(f"/{code}", follow_redirects=False)
    assert fake_redis.get(f"link:{code}") is not None   # warmed by the first request


def test_redirect_logs_a_click(client, make_user, make_link, db_session):
    code = make_link(make_user())
    client.get(f"/{code}", follow_redirects=False)
    assert db_session.query(Clicks).count() == 1


def test_deleted_link_stops_redirecting(client, make_user, make_link):
    headers = make_user()
    code = make_link(headers)
    client.get(f"/{code}", follow_redirects=False)  # warms the cache
    client.delete(f"/shorturl_delete/{code}/", headers=headers)

    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 404