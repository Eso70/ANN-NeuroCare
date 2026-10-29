# Phase 1 verification — 2026-10-27

**Superseded:** PostgreSQL migrations and real persistence tests now pass; see
[latest correction report](fixes.md). This document preserves the original session results.

The foundation source is implemented; Phase 1 is **not yet verified as working**.
Do not proceed to Phase 2 until the blocked checks below pass.

Historical Phase 1 report: Phase 2 was subsequently explicitly requested. Dependencies
became available during Phase 2, and frontend build/lint, backend lint, ML imports and
dependency consistency checks now pass. Socket and PostgreSQL integration restrictions
remain. See `phase2.md` for the newer results; the table below records the original run.

## Environment observed

- Windows 10.0.26300, PowerShell.
- Default Python 3.14.5; a usable Python 3.11.9 was found in the user programs folder.
- Node.js 26.3.1, npm 11.16.0, Git 2.54.0.windows.1.
- Docker command unavailable. PostgreSQL 18.4 binaries available; no response on 5432.
- Service-manager inspection denied; no existing service was changed.
- Workspace initially contained only Instruction.md, and was not a Git repository.

## Executed results

| Check | Actual result |
| --- | --- |
| Python 3.11 virtual environment | Created at backend/.venv |
| Python dependency installation | Failed: package index unreachable/no available distributions in this environment; no requested packages installed |
| Frontend dependency installation | Failed: registry DNS ENOTFOUND; offline attempt failed ENOTCACHED |
| Resolved dependency locks | Not generated; direct package versions pinned in manifests |
| PostgreSQL initdb | Succeeded; project-local cluster uses password authentication |
| PostgreSQL startup | pg_ctl reported success; log showed listening on 127.0.0.1:55432 and ready for connections |
| PostgreSQL client connection | Denied by sandbox: Windows socket error 10013 |
| Latest server status | Subsequent pg_ctl status reported no server running; persistent startup not verified |
| Application database creation | Failed due to connection denial; neurocare_db not created |
| Alembic upgrade head | Failed: Alembic not installed; no migration applied |
| Tables | Unverified; no application tables created by this session |
| Backend imports | Failed at FastAPI import: dependency not installed |
| Python source compileall | Passed for app, migrations, tests, and init-env.py; this checks syntax, not imports |
| PowerShell helper parsing | Passed |
| Frontend package.json parsing | Passed |
| Frontend build | Attempted; failed because tsc was unavailable |
| Frontend lint | Attempted; failed because ESLint was unavailable |
| Backend tests | Attempted; pytest unavailable, no tests executed |
| Backend lint | Attempted; Ruff unavailable |
| Browser/live API integration | Blocked by missing dependencies; not verified |
| Environment exclusions | .gitignore includes local envs, data, venv, logs, and temporary password file; Git tracking cannot be checked without a repository |

Local .env was generated with random credentials and no secrets were printed. The
temporary PostgreSQL password file was removed. No existing user file was overwritten.
The original PostgreSQL cluster selected the Windows default WIN1252 encoding;
the documented fresh-init command explicitly uses UTF8 for future setups.

## Recovery from a normal PowerShell terminal

Restore package registry/network access, then run from the project root:

```powershell
.\scripts\dev.ps1 install
.\scripts\dev.ps1 db-start
.\scripts\dev.ps1 db-create
.\scripts\dev.ps1 migrate
$env:RUN_DB_TESTS = '1'
.\scripts\dev.ps1 test
Remove-Item Env:RUN_DB_TESTS
.\scripts\dev.ps1 check
.\scripts\dev.ps1 backend
```

In a second terminal, run `.\scripts\dev.ps1 frontend` and open
http://localhost:5173. Confirm the real API and PostgreSQL connection cards turn
green, then stop the backend and refresh checks to verify error states.
Check `\dt` in psql for users, predictions and alembic_version.
If using Docker later, leave the project-local cluster stopped to avoid port conflicts.
