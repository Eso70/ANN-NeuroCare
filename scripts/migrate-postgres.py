"""One-time, fail-closed NeuroCare copy from 55432 to the existing server on 5432.

Run using the project venv in a normal local terminal. Never prints credentials.
Existing target data is accepted only when it exactly matches the source.
"""
import argparse
import getpass
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

import psycopg
from psycopg import sql
from dotenv import dotenv_values
from sqlalchemy.engine import URL, make_url

ROOT = Path(__file__).resolve().parents[1]
DATABASE = "neurocare_db"
ROLE = "neurocare"
CONNECTION_KEYS = {"DATABASE_URL", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def configured_url(values):
    if values.get("DATABASE_URL"):
        return make_url(values["DATABASE_URL"])
    return URL.create(
        "postgresql+psycopg", host=values.get("DB_HOST", "127.0.0.1"),
        port=int(values.get("DB_PORT", "5432")), database=values.get("DB_NAME", DATABASE),
        username=values.get("DB_USER", "postgres"), password=values.get("DB_PASSWORD"),
    )


def reject_connection_overrides():
    require(not any(key.upper() in CONNECTION_KEYS for key in os.environ),
            "Remove database connection shell overrides so setup uses only the root .env.")


def connection_error_detail(error, user=None, database=None, port=None):
    """Classify known failures; never echo raw libpq errors, DSNs or passwords."""
    message = str(error).lower()
    state = getattr(error, "sqlstate", None)
    if user == "postgres":
        context = f"Postgres account connection (database {database}, port {port})"
    elif user == ROLE:
        context = f"Application connection (neurocare, database {database}, port {port})"
    else:
        context = "PostgreSQL connection"
    if state == "28P01" or "password authentication failed" in message:
        if user == "postgres":
            return (f"{context}: PostgreSQL rejected the administrator login. "
                    "For DB_USER=postgres, set DB_PASSWORD in the root .env to the existing "
                    "account's password; setup reads it directly without prompting or resetting it.")
        return (f"{context}: PostgreSQL rejected the application login. DB_PASSWORD must match "
                "the existing neurocare role's password; setup does not reset an existing password.")
    if "no pg_hba.conf entry" in message or state == "28000":
        return f"{context}: PostgreSQL authentication rules rejected this connection. Check pg_hba.conf."
    if state == "3D000" or ("database" in message and "does not exist" in message):
        return f"{context}: the requested database does not exist."
    if "10013" in message or "forbidden by its access permissions" in message:
        return f"{context}: Windows blocked socket access (10013). Run in a normal local terminal."
    if "refused" in message:
        return f"{context}: the server refused the connection. Check that its PostgreSQL service is running."
    if "timeout" in message or "timed out" in message:
        return f"{context}: connection timed out. Check the service and local firewall."
    return (f"{context}: connection failed for an unclassified reason. "
            "Check the PostgreSQL server log for the matching attempt; raw errors are hidden to protect credentials.")


def connect(port, user, password, database=DATABASE, **kwargs):
    require(database in {DATABASE, "postgres"}, "Database is outside migration scope.")
    try:
        return psycopg.connect(
            host="127.0.0.1", port=port, user=user, password=password,
            dbname=database, connect_timeout=5, application_name="neurocare-migration",
            **kwargs,
        )
    except psycopg.OperationalError as error:
        raise RuntimeError(connection_error_detail(error, user, database, port)) from None


def pg_tool(bin_dir, tool, port, user, password, *args):
    env = os.environ.copy()
    # Avoid unrelated libpq defaults, service files, and command-line passwords.
    for key in list(env):
        if key.startswith("PG"):
            del env[key]
    env.update(PGPASSWORD=password, PGCONNECT_TIMEOUT="5")
    result = subprocess.run(
        [str(bin_dir / f"{tool}.exe"), "--host=127.0.0.1", f"--port={port}",
         f"--username={user}", "--no-password", *map(str, args)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    # Raw tool errors can include connection information; do not print them.
    require(result.returncode == 0, f"{tool} failed (exit {result.returncode}); configuration preserved.")
    return result.stdout


def manifest(connection):
    schemas = connection.execute(
        "select nspname from pg_namespace where nspname !~ '^pg_' "
        "and nspname <> 'information_schema' order by nspname"
    ).fetchall()
    require(schemas == [("public",)], "Unexpected schemas; refusing a partial copy.")
    tables = connection.execute(
        "select tablename from pg_tables where schemaname='public' order by tablename"
    ).fetchall()
    result = {"tables": {}, "sequences": {}}
    for (table,) in tables:
        rows = connection.execute(sql.SQL(
            "select to_jsonb(t)::text from public.{} t order by to_jsonb(t)::text collate \"C\""
        ).format(sql.Identifier(table)))
        digest = hashlib.sha256()
        count = 0
        for (row,) in rows:
            digest.update(row.encode("utf-8") + b"\n")
            count += 1
        result["tables"][table] = {"count": count, "sha256": digest.hexdigest()}
    for (sequence,) in connection.execute(
        "select sequencename from pg_sequences where schemaname='public' order by sequencename"
    ).fetchall():
        result["sequences"][sequence] = list(connection.execute(sql.SQL(
            "select last_value, is_called from public.{}"
        ).format(sql.Identifier(sequence))).fetchone())
    return result


def schema_hash(bin_dir, port, user, password, snapshot=None):
    args = ["--dbname=" + DATABASE, "--schema-only", "--no-owner", "--no-acl"]
    if snapshot:
        args.append("--snapshot=" + snapshot)
    content = pg_tool(bin_dir, "pg_dump", port, user, password, *args).decode("utf-8")
    # PostgreSQL 18 generates a fresh random psql restriction token per dump.
    content = re.sub(r"^\\(?:un)?restrict .*\n", "", content, flags=re.MULTILINE)
    return hashlib.sha256(content.replace("\r\n", "\n").encode()).hexdigest()


def switch_env(original, password):
    config = dotenv_values(ROOT / ".env")
    url = configured_url(config)
    if config.get("DATABASE_URL"):
        updates = {"DATABASE_URL": url.set(host="127.0.0.1", port=5432, username=ROLE,
                                          password=password, database=DATABASE).render_as_string(hide_password=False)}
    else:
        updates = {"DB_HOST": "127.0.0.1", "DB_PORT": "5432", "DB_USER": ROLE,
                   "DB_PASSWORD": password, "DB_NAME": DATABASE}
    updates.update({key: value for key, value in {
        "POSTGRES_USER": ROLE, "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": DATABASE, "POSTGRES_PORT": "5432",
    }.items() if key in config})
    update_env(original, updates)


def update_env(original, updates):
    """Atomically change named settings while preserving all unrelated values."""
    text = original.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"
    for key, value in updates.items():
        value = "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
        pattern = rf"(?m)^{key}=[^\r\n]*"
        if re.search(pattern, text):
            text = re.sub(pattern, lambda _: f"{key}={value}", text)
        else:
            text = text.rstrip("\r\n") + newline + f"{key}={value}" + newline
    parsed = dotenv_values(stream=StringIO(text))
    previous = dotenv_values(stream=StringIO(original.decode("utf-8-sig")))
    require(all(parsed.get(key) == value for key, value in previous.items() if key not in updates),
            "An unrelated setting would change; .env preserved.")
    require(all(parsed.get(key) == value for key, value in updates.items()),
            "Could not safely encode database settings; .env preserved.")
    # Ensure no concurrent local edit is lost. Replace is atomic on this filesystem.
    require((ROOT / ".env").read_bytes() == original, ".env changed during migration; preserving that edit.")
    staging = ROOT / ".env.migration-pending"
    require(not staging.exists(), "An earlier .env staging file exists; inspect it before retrying.")
    try:
        staging.write_bytes(text.encode("utf-8"))
        staging.replace(ROOT / ".env")
    finally:
        staging.unlink(missing_ok=True)


def setup_target():
    """Provision only the configured NeuroCare destination; never copy or delete data."""
    reject_connection_overrides()
    url = configured_url(dotenv_values(ROOT / ".env"))
    require(url.drivername == "postgresql+psycopg" and url.host in {"127.0.0.1", "localhost"}
            and url.port == 5432 and url.database == DATABASE and url.username in {ROLE, "postgres"}
            and bool(url.password), "Expected neurocare_db with postgres or neurocare on local port 5432.")
    # A denied/refused connection must fail before asking for a password.
    with __import__("socket").create_connection(("127.0.0.1", 5432), timeout=3):
        pass
    if url.username == "postgres":
        password = url.password
        with connect(5432, "postgres", password, "postgres", autocommit=True) as admin:
            print("Postgres login succeeded. Checking neurocare_db; account permissions will not change.")
            target = admin.execute("select 1 from pg_database where datname=%s", (DATABASE,)).fetchone()
            if not target:
                admin.execute(sql.SQL("create database {} owner postgres").format(sql.Identifier(DATABASE)))
        with connect(5432, "postgres", password) as application:
            require(application.execute("select current_database(), current_user").fetchone() == (DATABASE, "postgres"),
                    "Application connection verification failed.")
            counts = manifest(application)
        print("NeuroCare database ready on 5432 using postgres. Existing records and account permissions preserved.")
        print("Current row counts:", {k: v["count"] for k, v in counts["tables"].items()})
        print(r"Apply schema migrations: .\scripts\dev.ps1 migrate")
        return
    require(sys.stdin.isatty(), "Run in an interactive local terminal so the password prompt stays hidden.")
    password = getpass.getpass("Local PostgreSQL 5432 administrator password (hidden): ")
    with connect(5432, "postgres", password, "postgres", autocommit=True) as admin:
        print("Administrator login succeeded. Checking the NeuroCare role and database.")
        role = admin.execute(
            "select rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, rolcanlogin "
            "from pg_roles where rolname=%s", (ROLE,),
        ).fetchone()
        if role:
            require(role == (False, False, False, False, False, True),
                    "Existing neurocare role has unexpected privileges; it was not changed.")
            require(not admin.execute(
                "select 1 from pg_auth_members where member=(select oid from pg_roles where rolname=%s)",
                (ROLE,),
            ).fetchone(), "Existing neurocare role has memberships; it was not changed.")
        target = admin.execute(
            "select pg_get_userbyid(datdba) from pg_database where datname=%s", (DATABASE,),
        ).fetchone()
        require(not target or target[0] == ROLE,
                "Existing neurocare_db has another owner; it was preserved.")
        if not role:
            admin.execute(sql.SQL(
                "create role {} login nosuperuser nocreatedb nocreaterole noreplication nobypassrls password {}"
            ).format(sql.Identifier(ROLE), sql.Literal(url.password)))
        if not target:
            admin.execute(sql.SQL("create database {} owner {}").format(
                sql.Identifier(DATABASE), sql.Identifier(ROLE)))
    print("Verifying the neurocare application login using DB_PASSWORD from .env.")
    with connect(5432, ROLE, url.password) as application:
        require(application.execute("select current_database(), current_user").fetchone() == (DATABASE, ROLE),
                "Application connection verification failed.")
        counts = manifest(application)
    print("NeuroCare database/login ready on 5432. Existing data preserved.")
    print("Current row counts:", {k: v["count"] for k, v in counts["tables"].items()})
    print(r"Apply schema migrations: .\scripts\dev.ps1 migrate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres-bin", type=Path, default=Path(r"C:\Program Files\PostgreSQL\18\bin"))
    parser.add_argument("--setup-only", action="store_true",
                        help="Provision the configured database/login on 5432 without copying source data")
    args = parser.parse_args()
    if args.setup_only:
        setup_target()
        return
    for name in ("pg_dump", "pg_restore"):
        require((args.postgres_bin / f"{name}.exe").is_file(), f"Missing {name} executable.")
    reject_connection_overrides()
    original = (ROOT / ".env").read_bytes()
    config = dotenv_values(ROOT / ".env")
    url = configured_url(config)
    require(url.host in {"localhost", "127.0.0.1"} and url.port == 55432
            and url.database == DATABASE and url.username == ROLE,
            "Expected the original local neurocare_db connection on 55432; .env was preserved.")
    require(bool(url.password), "Source application password is missing.")
    # Fail before prompting or mutating anything if either server is inaccessible.
    with connect(55432, ROLE, url.password) as source:
        source_counts = manifest(source)
    with __import__("socket").create_connection(("127.0.0.1", 5432), timeout=3):
        pass
    print("Source row counts:", {k: v["count"] for k, v in source_counts["tables"].items()})
    require(sys.stdin.isatty(), "Run in an interactive local terminal so the password prompt stays hidden.")
    admin_password = getpass.getpass("Local PostgreSQL 5432 administrator password (hidden): ")
    with connect(5432, "postgres", admin_password, "postgres", autocommit=True) as admin:
        require(admin.execute("select rolsuper from pg_roles where rolname=current_user").fetchone()[0],
                "The setup connection is not a PostgreSQL administrator.")
        role = admin.execute(
            "select rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, rolcanlogin "
            "from pg_roles where rolname=%s", (ROLE,),
        ).fetchone()
        if role:
            require(role == (False, False, False, False, False, True),
                    "Existing neurocare role has unexpected privileges; it was not changed.")
            require(not admin.execute(
                "select 1 from pg_auth_members where member=(select oid from pg_roles where rolname=%s)",
                (ROLE,),
            ).fetchone(), "Existing neurocare role has memberships; it was not changed.")
        target = admin.execute(
            "select pg_get_userbyid(datdba), pg_encoding_to_char(encoding) "
            "from pg_database where datname=%s", (DATABASE,),
        ).fetchone()
        if target:
            require(role and target[0] == ROLE, "Existing target has another owner; preserved without changes.")
            with connect(5432, ROLE, url.password) as destination:
                target_before = manifest(destination)
            print("Existing target row counts:", {k: v["count"] for k, v in target_before["tables"].items()})
            require(not target_before["tables"] or target_before == source_counts,
                    "Target contains different data. No rows were overwritten; reconcile it separately.")
        else:
            target_before = None

        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-File", str(ROOT / "scripts/stop-project-apps.ps1")],
            check=False,
        )
        require(result.returncode == 0, "Could not safely stop application processes; .env preserved.")
        backup_dir = ROOT / ".db-backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_dir.mkdir(parents=True, exist_ok=False)
        backup = backup_dir / "neurocare-55432.dump"
        # Hold write-blocking locks through copy, verification, and configuration switch.
        with connect(55432, ROLE, url.password) as source:
            source.execute("set transaction isolation level repeatable read")
            source.execute("set local lock_timeout='5s'")
            tables = source.execute(
                "select tablename from pg_tables where schemaname='public' order by tablename"
            ).fetchall()
            require({t[0] for t in tables} >= {"users", "predictions", "alembic_version"},
                    "Source schema is incomplete.")
            for (table,) in tables:
                source.execute(sql.SQL("lock table public.{} in share mode").format(sql.Identifier(table)))
            baseline = manifest(source)
            snapshot = source.execute("select pg_export_snapshot()").fetchone()[0]
            pg_tool(args.postgres_bin, "pg_dump", 55432, ROLE, url.password,
                    "--dbname=" + DATABASE, "--format=custom", "--no-owner", "--no-acl",
                    "--snapshot=" + snapshot, "--file=" + str(backup))
            require(backup.stat().st_size > 0, "Source backup is empty.")
            # Read the archive catalog without database access or credentials.
            catalog = subprocess.run([str(args.postgres_bin / "pg_restore.exe"), "--list", str(backup)],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            require(catalog.returncode == 0, "Backup archive catalog could not be read.")
            expected_schema = schema_hash(args.postgres_bin, 55432, ROLE, url.password, snapshot)
            report = {"status": "backup_complete", "source_port": 55432, "target_port": 5432,
                      "database": DATABASE, "source": baseline, "schema_sha256": expected_schema,
                      "backup_sha256": hashlib.sha256(backup.read_bytes()).hexdigest()}
            report_path = backup_dir / "verification.json"
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print("Source backup created:", backup)
            if not role:
                admin.execute(sql.SQL(
                    "create role {} login nosuperuser nocreatedb nocreaterole noreplication nobypassrls password {}"
                ).format(sql.Identifier(ROLE), sql.Literal(url.password)))
            if not target:
                encoding = source.execute("show server_encoding").fetchone()[0]
                admin.execute(sql.SQL("create database {} owner {} template template0 encoding {}").format(
                    sql.Identifier(DATABASE), sql.Identifier(ROLE), sql.Literal(encoding)))
            with connect(5432, ROLE, url.password) as destination:
                current = manifest(destination)
            if not current["tables"]:
                # No clean/drop flags; all schema/data creation is one transaction.
                pg_tool(args.postgres_bin, "pg_restore", 5432, ROLE, url.password,
                        "--dbname=" + DATABASE, "--single-transaction", "--exit-on-error",
                        "--no-owner", "--no-acl", backup)
            with connect(5432, ROLE, url.password) as destination:
                actual = manifest(destination)
            require(actual == baseline, "Target rows or sequences differ; .env preserved.")
            require(schema_hash(args.postgres_bin, 5432, ROLE, url.password) == expected_schema,
                    "Target schema differs; .env preserved.")
            require(manifest(source) == baseline, "Source sequences changed during copy; .env preserved.")
            require((ROOT / ".env").read_bytes() == original, ".env changed; preserving local edits.")
            # Validate the copied database/model before changing the active file.
            env = os.environ.copy()
            env.update(DATABASE_URL=url.set(host="127.0.0.1", port=5432).render_as_string(hide_password=False),
                       RUN_DB_TESTS="1", RUN_ML_TESTS="1", RUN_MODEL_TESTS="1")
            check = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                                   cwd=ROOT / "backend", env=env, check=False)
            require(check.returncode == 0, "Target migrations failed; .env preserved.")
            check = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                                   cwd=ROOT / "backend", env=env, check=False)
            require(check.returncode == 0, "Target database/model tests failed; .env preserved.")
            # Integration tests remove their own rows but legitimately advance sequences.
            with connect(5432, ROLE, url.password) as destination:
                tested = manifest(destination)
            require(tested["tables"] == baseline["tables"], "Tests left different data; .env preserved.")
            require(manifest(source) == baseline, "Source changed during verification; .env preserved.")
            switch_env(original, url.password)
            report.update(status="copied_verified_configured", target_before_tests=actual,
                          target_after_tests=tested, backend_tests="passed", config_port=5432)
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print("Verified schema, all rows, Alembic state, sequence copy, and database/model tests.")
            print("Active configuration now uses neurocare_db on 5432. Original database preserved.")
            print("Verification report:", report_path)
    print(r"Start/reuse the application: .\scripts\dev.ps1 start")


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        # Connection errors and tracebacks may include DSNs. Only our own fixed messages are shown.
        detail = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        setup_only = "--setup-only" in sys.argv
        operation = "Database setup" if setup_only else "Migration"
        print(f"{operation} stopped: {detail}", file=sys.stderr)
        if setup_only:
            print("No database or role was dropped. Any NeuroCare objects already created remain for a retry.", file=sys.stderr)
        else:
            print("No database or role was dropped. Original source and any completed backup are preserved.", file=sys.stderr)
        sys.exit(1)
