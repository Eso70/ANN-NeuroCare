import os
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.db.session import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_and_version():
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/v1/").json() == {"name": "NeuroCare API", "version": "0.1.0"}


def test_db_success():
    session = Mock()
    session.execute.return_value.scalar_one.return_value = 1
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = client.get("/api/health/db")
        assert response.status_code == 200
        assert response.json()["database"] == "connected"
    finally:
        app.dependency_overrides.clear()


def test_db_failure_does_not_expose_credentials():
    session = Mock()
    session.execute.side_effect = OperationalError("secret connection", {}, Exception("password"))
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = client.get("/api/health/db")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}
    finally:
        app.dependency_overrides.clear()


def test_cors():
    response = client.options("/api/health", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET",
    })
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_development_loopback_alias_preflight():
    response = client.options("/api/v1/predictions", headers={
        "Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


@pytest.mark.parametrize("origin", [
    "http://127.0.0.1:5174", "https://127.0.0.1:5173",
    "http://localhost.evil.example:5173", "http://192.168.1.2:5173",
])
def test_unconfigured_origins_remain_blocked(origin):
    response = client.options("/api/health", headers={
        "Origin": origin, "Access-Control-Request-Method": "GET",
    })
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.integration
def test_real_database_and_migrated_schema():
    if os.environ.get("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 with a configured migrated PostgreSQL database")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
        assert {"users", "predictions", "alembic_version"} <= set(inspect(connection).get_table_names())
    assert client.get("/api/health/db").status_code == 200
