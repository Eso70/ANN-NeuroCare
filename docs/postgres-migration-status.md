# PostgreSQL migration status — 2026-10-28

The database copy is **not executed**. At the user's subsequent request, the active
`.env` was switched to `127.0.0.1:5432`, database `neurocare_db`, initially login `neurocare`,
without copying the source. It now uses separate `DB_HOST`, `DB_PORT`, `DB_NAME`,
`DB_USER` and `DB_PASSWORD` fields instead of a manually encoded connection URL.
At the next explicit request, `DB_USER` was changed to `postgres` and defaults were
updated to match. Setup now uses that existing account without altering its privileges;
at the next request, its setup prompt was removed. It now reads the literal password
from ignored `.env` without client-side hashing or changing server credentials.
The supplied temporary password was saved only in that ignored configuration.
Model settings, application secrets and unrelated settings were preserved. No target
database was created, records copied, or application processes restarted by this
session. No source backup has been made by this session.

## Access limitation

Local TCP connection attempts to PostgreSQL fail with Windows error 10013 (access
forbidden). Service/CIM enumeration is also denied. Consequently, running-server
state and current source/target row counts could not be established. Readiness
results from this restricted session do not prove either server is stopped.
On-disk cluster metadata records the project cluster on 55432 and the separately
installed cluster on 5432; that metadata is not a live health check.

## Changes prepared

- `scripts/dev.ps1` refuses cluster start/stop/create operations on 5432. Its cluster
  guard also refuses missing port metadata, remote hosts and mismatched local ports.
  Existing healthy PostgreSQL remains eligible for reuse on the configured endpoint.
- `scripts/migrate-postgres.py` provides the one-time local copy with a hidden password
  prompt, source backup, dedicated non-superuser role, transactional restore, full
  table hashes, schema and sequence comparisons, target migrations and backend tests.
  It changes `.env` only after those checks pass. Existing differing target data causes
  an error and is preserved. The optional dedicated-role copy mode does not write its administrator credentials to files.
- `scripts/stop-project-apps.ps1` validates this project's listener command lines before
  stopping its API/Vite; it never manages PostgreSQL. Reload-enabled or unrecognized
  processes require normal shutdown through their existing terminal.
- Backups are ignored via `.db-backups/`. README instructions describe the destination,
  migration, existing service reuse, source preservation and rollback considerations.
- `.env.example`, `scripts/init-env.py` and Compose now use the same separate `DB_*`
  fields. SQLAlchemy builds the encoded URL from those fields; an explicit
  `DATABASE_URL` remains a backward-compatible override. `db-create` also resolves
  its credentials through backend settings instead of reading a duplicate password.
- `dev.ps1 db-setup` securely prompts for the administrator password and provisions
  only the missing application login/database on 5432; it never copies or drops data.
- Frontend sources and trained model artifacts were not changed.

## Checks actually executed

- After selecting `postgres`: **22 passed** across setup/configuration tests and Ruff
  passed. Added tests verify existing-database preservation, creation of only a missing
  `neurocare_db`, unchanged account permissions, direct use of the configured password without an
  interactive prompt, and no configuration write on successful or failed setup. Actual settings resolve to `postgres`
  on port 5432; these mock checks do not establish live login success.
- Follow-up setup diagnostic checks: **19 passed** across `test_db_setup.py` and
  `test_config.py`; Ruff passed for the changed diagnostic/configuration files.
  Diagnostics distinguish administrator/application authentication failures, rule
  rejection, missing database, refused/blocked/timed-out connections and unknown
  failures without printing raw errors or credentials. This does not establish the
  cause of the user's earlier generic OperationalError; a local retry is required.
- Ruff over `backend` and `scripts`: passed.
- Python compilation and migration CLI help: passed.
- Actual root settings load: separate DB_* fields resolve to neurocare_db on 5432;
  the configured model directory exists and settings repr hides credentials.
- Added connection-setting tests cover literal password encoding, explicit URL
  precedence, required password and port bounds.
- Before the requested configuration switch, the copy preflight was executed and
  refused restricted TCP access; a before/after .env hash matched and no backup
  directory was created.
- PowerShell parser checks for `dev.ps1`, `start.ps1` and `stop-project-apps.ps1`: passed.
- Executed extracted cluster guard with local 5432, remote host, wrong local port and
  missing metadata: all refused. Recorded project port 55432 was accepted.
- Executed migration configuration updates in a temporary workspace directory with
  synthetic credentials containing quotes, backslashes and spaces: URL/credential
  round trips, unrelated settings/CRLF preservation and concurrent-edit refusal passed.
- Focused backend/model suite: **39 passed, 3 deselected**, with one existing Starlette/
  AnyIO deprecation warning. This included real saved-model reload and inference, data
  contracts, preprocessing, evaluation, settings and prediction-service unit checks.

The focused suite ran with `RUN_MODEL_TESTS=1`:

```powershell
# From backend/, using .venv/Scripts/python.exe
python -m pytest -q tests/test_config.py tests/test_evaluation.py tests/test_ml_data.py tests/test_prediction_service.py tests/test_model_artifact.py -k 'not endpoint and not incomplete_artifact'
```

The initial full suite stalled after eleven progress markers at the TestClient health
test and was interrupted. An isolated `test_health_and_version` run also stalled and
was bounded by a 20-second watchdog. Neither run passed. No database integration or
live HTTP startup checks were completed. Saved-model inference success does not prove
that predictions persist on the destination.

## Remaining local verification

Run `.\scripts\dev.ps1 db-setup` in a normal local terminal to provision the
5432 database/login if missing. Then run `.\scripts\dev.ps1 migrate`, followed by
`.\scripts\dev.ps1 start`. Postgres mode reads `DB_PASSWORD` directly from the ignored root configuration,
without prompting or resetting the account password. In another terminal, repeat the startup command
to check service reuse. Live provisioning, database persistence, repeated startup and
ownership/cleanup behavior remain unverified in this session.

The optional 55432 copy helper remains available for an explicitly selected source
configuration. It refuses to copy when the active connection already selects 5432.
