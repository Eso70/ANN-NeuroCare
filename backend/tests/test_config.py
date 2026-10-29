import pytest
from sqlalchemy.engine import make_url

from app.core.config import Settings


def settings(origin, environment="development"):
    return Settings(
        _env_file=None, database_url="postgresql+psycopg://unit:unit@127.0.0.1/unit",
        secret_key="unit-test-secret-" * 4, frontend_url=origin, app_env=environment,
    )


@pytest.mark.parametrize("origin,alias", [
    ("http://localhost:5173", "http://127.0.0.1:5173"),
    ("http://127.0.0.1:15173", "http://localhost:15173"),
])
def test_development_alias_keeps_the_configured_port(origin, alias):
    assert settings(origin).cors_origins == [origin, alias]


@pytest.mark.parametrize("environment", ["production", "testing"])
def test_non_development_has_only_explicit_origin(environment):
    origin = "http://localhost:5173"
    assert settings(origin, environment).cors_origins == [origin]


def test_external_origin_does_not_enable_loopback_aliases():
    origin = "https://demo.example.org"
    assert settings(origin).cors_origins == [origin]


def test_database_fields_encode_literal_password_and_port():
    password = "local@password:/?#% with spaces"
    config = Settings(
        _env_file=None, db_host="localhost", db_port=5432, db_name="neurocare_db",
        db_user="neurocare", db_password=password, secret_key="test-secret-" * 4,
    )
    url = make_url(config.database_url)
    assert (url.host, url.port, url.database, url.username, url.password) == (
        "localhost", 5432, "neurocare_db", "neurocare", password,
    )
    assert password not in repr(config)


def test_explicit_database_url_overrides_separate_fields():
    override = "postgresql+psycopg://override:password@localhost:55432/legacy"
    config = Settings(
        _env_file=None, database_url=override, db_port=5432, db_password="unused",
        secret_key="test-secret-" * 4,
    )
    assert config.database_url == override


@pytest.mark.parametrize("port", [0, 65536])
def test_invalid_database_ports_are_rejected(port):
    with pytest.raises(ValueError, match="db_port"):
        Settings(_env_file=None, db_port=port, db_password="test", secret_key="test-secret-" * 4)


def test_database_password_is_required_without_url():
    with pytest.raises(ValueError, match="DB_PASSWORD"):
        Settings(_env_file=None, secret_key="test-secret-" * 4)
