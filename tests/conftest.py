import os

# Must be set BEFORE importing the app, because security.py reads these at import time
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app, get_db


@pytest.fixture
def db_session(monkeypatch):
    """A fresh in-memory SQLite database for every single test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # all sessions share one connection to the in-memory DB
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # log_click() opens SessionLocal directly (not via Depends), so patch it too,
    # otherwise background click logging would write to your REAL database
    monkeypatch.setattr("app.main.SessionLocal", TestingSession)

    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def fake_redis():
    # A new FakeServer per test means no cache or rate limit counters leak between tests
    return fakeredis.FakeRedis(server=fakeredis.FakeServer())


@pytest.fixture
def client(db_session, fake_redis):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.state.redis = fake_redis
    # Deliberately NOT `with TestClient(app)`: that would run your startup event
    # and replace the fake Redis with a real connection to localhost
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(client):
    """Signs up + logs in, returns auth headers."""
    def _make(username="alice", password="Passw0rd!"):
        client.post("/newusers", json={"username": username, "password": password})
        r = client.post("/login", data={"username": username, "password": password})
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
    return _make


@pytest.fixture
def make_link(client):
    """Creates a link, returns its short_code."""
    def _make(headers, url="https://example.com"):
        r = client.post("/create_link", json={"original_url": url}, headers=headers)
        return r.json()["short_code"]
    return _make