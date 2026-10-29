"""Verify setup diagnostics identify the failing login without exposing secrets."""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg
import pytest


spec = importlib.util.spec_from_file_location(
    "neurocare_db_setup", Path(__file__).resolve().parents[2] / "scripts/migrate-postgres.py",
)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


@pytest.mark.parametrize("user,database,expected", [
    ("postgres", "postgres", "administrator login"),
    ("neurocare", "neurocare_db", "application login"),
])
def test_authentication_diagnostic_identifies_login_without_raw_error(user, database, expected):
    error = psycopg.OperationalError('password authentication failed: password=private-test-value')
    with patch.object(setup.psycopg, "connect", side_effect=error):
        with pytest.raises(RuntimeError) as captured:
            setup.connect(5432, user, "private-test-value", database)
    message = str(captured.value)
    assert expected in message
    assert "5432" in message
    assert "private-test-value" not in message
    if user == "postgres":
        assert "DB_PASSWORD" in message
        assert "without prompting" in message
    else:
        assert "does not reset" in message


@pytest.mark.parametrize("raw,expected", [
    ("no pg_hba.conf entry secret=private-test-value", "authentication rules"),
    ("connection refused secret=private-test-value", "server refused"),
    ("connection timeout expired secret=private-test-value", "timed out"),
    ("WinError 10013 secret=private-test-value", "Windows blocked"),
    ('database "postgres" does not exist secret=private-test-value', "does not exist"),
    ("unknown error password=private-test-value", "unclassified reason"),
])
def test_connection_diagnostics_never_echo_raw_errors(raw, expected):
    message = setup.connection_error_detail(psycopg.OperationalError(raw), "postgres", "postgres", 5432)
    assert expected in message
    assert "private-test-value" not in message


def test_connection_scope_refusal_happens_before_any_database_connection():
    with patch.object(setup.psycopg, "connect") as connection:
        with pytest.raises(RuntimeError, match="outside migration scope"):
            setup.connect(5432, "postgres", "private-test-value", "unrelated_db")
        connection.assert_not_called()


@pytest.mark.parametrize("database_exists", [True, False])
def test_postgres_setup_uses_configured_password_without_prompt_or_write(tmp_path, database_exists):
    values = {"DB_HOST": "127.0.0.1", "DB_PORT": "5432", "DB_NAME": "neurocare_db",
              "DB_USER": "postgres", "DB_PASSWORD": "old-test-value"}
    original = b"DB_USER=postgres\nDB_PASSWORD=old-test-value\n"
    (tmp_path / ".env").write_bytes(original)
    admin_context, app_context = MagicMock(), MagicMock()
    admin = admin_context.__enter__.return_value
    admin.execute.return_value.fetchone.return_value = (1,) if database_exists else None
    app_context.__enter__.return_value.execute.return_value.fetchone.return_value = ("neurocare_db", "postgres")
    with (patch.object(setup, "ROOT", tmp_path), patch.object(setup, "reject_connection_overrides"),
          patch.object(setup, "dotenv_values", return_value=values),
          patch("socket.create_connection"), patch.object(setup.sys.stdin, "isatty", return_value=False),
          patch.object(setup.getpass, "getpass") as prompt,
          patch.object(setup, "connect", side_effect=[admin_context, app_context]) as connect,
          patch.object(setup, "manifest", return_value={"tables": {}, "sequences": {}}),
          patch.object(setup, "update_env") as update):
        setup.setup_target()
    assert connect.call_args_list[0].args == (5432, "postgres", "old-test-value", "postgres")
    assert connect.call_args_list[1].args == (5432, "postgres", "old-test-value")
    assert admin.execute.call_count == (1 if database_exists else 2)
    if not database_exists:
        creation = admin.execute.call_args.args[0].as_string()
        assert creation == 'create database "neurocare_db" owner postgres'
    update.assert_not_called()
    prompt.assert_not_called()


def test_failed_postgres_setup_does_not_prompt_or_change_password(tmp_path):
    (tmp_path / ".env").write_text("DB_USER=postgres\n")
    values = {"DB_PORT": "5432", "DB_NAME": "neurocare_db", "DB_USER": "postgres",
              "DB_PASSWORD": "old-test-value"}
    with (patch.object(setup, "ROOT", tmp_path), patch.object(setup, "reject_connection_overrides"),
          patch.object(setup, "dotenv_values", return_value=values),
          patch("socket.create_connection"), patch.object(setup.sys.stdin, "isatty", return_value=False),
          patch.object(setup.getpass, "getpass") as prompt,
          patch.object(setup, "connect", side_effect=RuntimeError("Administrator login rejected")),
          patch.object(setup, "update_env") as update):
        with pytest.raises(RuntimeError, match="Administrator login rejected"):
            setup.setup_target()
    update.assert_not_called()
    prompt.assert_not_called()
