# NeuroCare AI

NeuroCare is a university ANN project that classifies a historical CDC health-survey
dataset. Its public-style research website explains the methodology, dataset and ANN,
with a validated 21-input demonstration form, saved evaluation and persisted results.
It is an **educational prototype, not a diagnostic, screening, or future-risk tool**.
Use synthetic, non-identifying values for application demonstrations.

The latest redesign implements root `newdesign.md`: an original light lavender/ink
design system, Georgia display typography, compact navigation, a split scientific hero,
an interactive explorer of the actual input schema, a numbered prediction journey,
saved evaluation and an editorial project story. Home, prediction, model/methodology,
About, result and not-found views share the same controls and page frame.
The 21-field contract, custom keyboard-operated dropdowns, review step and PostgreSQL
submission remain intact. No patient records, dashboard feeds, testimonials or metric
values were invented. Scrollbars remain hidden while scrolling is enabled.
See [the completed design checklist and live verification](docs/newdesign-completion.md)
for current checks. The homepage and methodology now visualize actual detected,
missed and falsely flagged test records alongside measured accuracy, recall and precision.
The [initial design report](docs/newdesign-implementation.md) remains historical.

Backend code, database schema, environment and trained artifacts are retained.
[Phase 4](docs/phase4-redesign.md), [Phase 5](docs/phase5-readiness.md),
[Phase 6](docs/phase6-redesign.md), [Phase 7](docs/phase7-redesign.md) and earlier
[demonstration verification](docs/demo-readiness.md) are historical reports; use this README
for current setup and the completion report for current UI verification status.

## Architecture and structure

| Path | Responsibility |
| --- | --- |
| `frontend/src/pages/` | Home, guided prediction, model/methodology, About and not-found routes |
| `frontend/src/components/`, `layouts/` | Shared site shell, UI primitives, ANN pipeline diagram, evaluation, guided fields, review and results |
| `frontend/src/services/`, `hooks/`, `types/` | Central Axios client, live health checks, contracts |
| `frontend/src/styles/`, `lib/`, `tests/` | Design tokens, responsive styles, survey/select behavior and regression tests |
| `backend/app/api/routes/` | Thin HTTP endpoints |
| `backend/app/schemas/` | Strict input validation and response models |
| `backend/app/core/` | Environment configuration and reserved security utilities |
| `backend/app/db/`, `models/` | SQLAlchemy sessions, User and Prediction tables |
| `backend/app/repositories/`, `services/` | Persistence and prediction orchestration |
| `backend/app/ml/` | CSV contract, splitting/scaling, training, threshold selection, inference, audit |
| `backend/alembic/`, `backend/tests/` | Schema migrations and automated tests |
| `data/`, `artifacts/` | Local datasets (ignored) and trained model versions (allowed in Git) |
| `scripts/`, `docs/` | PowerShell helpers, setup, reports and browser evidence |

Stack: React 19, Vite 6, Tailwind 4, FastAPI, SQLAlchemy 2, psycopg 3, PostgreSQL,
Alembic, TensorFlow/Keras and scikit-learn. No database is replaced by SQLite or
browser storage. Recharts remains installed; lightweight SVG/CSS is sufficient for
the original diagrams and split visualization. All displayed evaluation values, matrix
counts and split sizes come from saved model metadata through the existing API.

## Prerequisites and installation

- Python **3.11 x64** for the pinned TensorFlow 2.19 environment.
- Node.js 22+ and npm; the production build was verified here with Node 26.3.1.
  The frontend regression runner requires support for `--experimental-strip-types`;
  it was also verified with Node 26.3.1.
- PostgreSQL 18 for the existing native cluster, or Docker Compose. Match native
  server binaries to the cluster's major version; do not open an 18 cluster with 17.
- Registry access when installing dependencies. TensorFlow uses CPU on this native
  Windows setup. If its DLL import fails, check the Microsoft Visual C++ runtime.

Run commands from `D:\Coding - Projects\NeuroCare` unless stated otherwise.
The current workspace already has its environment, database and artifacts. The following
installation commands are for a fresh checkout/machine; do not overwrite an existing `.env`.

```powershell
$pythonExe = 'C:\Users\esma3\AppData\Local\Programs\Python\Python311\python.exe'
# Change this path to your Python 3.11 executable if necessary.
& $pythonExe -m venv backend/.venv
& $pythonExe scripts/init-env.py
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
npm ci --prefix frontend
```

`scripts/init-env.py` generates an application secret and securely prompts for the
existing `postgres` password without displaying it. It refuses to overwrite `.env`. Activation is optional; direct interpreter paths avoid
PowerShell activation-policy problems. If desired, activate with
`.\backend\.venv\Scripts\Activate.ps1`.

Direct dependency versions are in `requirements.txt`/`package.json`; resolved dependencies
are in `requirements.lock.txt`/`package-lock.json`. The `scripts/dev.ps1 install` helper
installs from direct manifests and regenerates locks; use the commands above when you
want to reproduce the supplied resolved environment.

## Environment configuration

FastAPI reads the root `.env` by absolute path. Frontend settings belong in
`frontend/.env`; that file is optional because the API origin defaults to
`http://localhost:8000` in development. Production builds default to the same origin:
route `/api/*` to FastAPI through the hosting proxy. For a separate API origin, set
`VITE_API_URL=https://your-api-host` before building and set backend `FRONTEND_URL`
to the actual site origin with `APP_ENV=production`. Rebuild after changing Vite values.
Copy `frontend/.env.example` only when creating a new file.
Restart FastAPI after changing `.env` or model files; restart Vite after changing
frontend environment values. Model loading and settings are cached per process.

| Variable | Meaning |
| --- | --- |
| `DB_HOST` | PostgreSQL host, normally `127.0.0.1` |
| `DB_PORT` | Existing PostgreSQL service port, `5432` |
| `DB_NAME` | Dedicated database, `neurocare_db` |
| `DB_USER` | Existing local PostgreSQL account, `postgres` |
| `DB_PASSWORD` | Existing `postgres` password; keep quoted; no URL encoding needed |
| `DATABASE_URL` | Optional deployment/legacy override; when set, takes precedence over `DB_*` |
| `APP_ENV` | Development environment label |
| `SECRET_KEY` | At least 32 random characters; reserved, does not imply authentication exists |
| `FRONTEND_URL` | CORS origin, normally `http://localhost:5173`; development also permits the matching 127.0.0.1/localhost alias on that port |
| `MODEL_DIR` | Trusted version directory, relative to the project root or absolute; empty disables inference |
| `VITE_API_URL` | Optional public API URL; unset uses localhost:8000 in development and the site origin in production; never put secrets here |
| `VITE_REPOSITORY_URL`, `VITE_DOCS_URL` | Optional real public HTTPS links; absent or invalid links are omitted |

The root `.env` is grouped into Application, PostgreSQL and Model sections. Change
only the `DB_*` fields to change the connection; the backend builds and encodes its
connection URL automatically. Do not add a second password or a `POSTGRES_*` copy.
Compose also reads the same `DB_USER`, `DB_PASSWORD`, `DB_NAME` and `DB_PORT` values.
Leave `DATABASE_URL` unset for this local setup. Shell environment variables override
`.env`, so remove stale overrides before troubleshooting. Restart the API after edits.
Changing `DB_PASSWORD` configures the client; it does not reset an existing server
login's password. Change that login separately through an administrator when intended.

The configured artifact is `artifacts/20261029T043159Z-bd9e866c`. Trained model
bundles in `artifacts/` are allowed in Git; add and commit them to include them in
new checkouts. `.env.example` uses `MODEL_DIR=artifacts/20261029T043159Z-bd9e866c`.
Relative model paths resolve from the project root regardless of the launch directory,
so this setting works when the checkout moves to another machine. Raw datasets
in `data/` remain ignored; inference uses the saved model without retraining.
Missing artifacts produce 503, not simulated output.
The current [recall policy report](docs/recall-policy-results.md) records the restored
82.82% recall / 67.04% accuracy operating point, preserved artifacts and executed checks.

## PostgreSQL on the existing service (5432)

The active database configuration is `neurocare_db` on the independently managed local
PostgreSQL service, port **5432**, using the existing **`postgres`** account as requested.
That account normally has administrator privileges; a dedicated non-superuser remains
the recommended choice for deployment. Setup does not alter this account or its
permissions. Never use, reset or migrate an unrelated database.

The launcher uses the same backend settings, normally the `DB_*` fields. On 5432 it
only checks/reuses the existing server; it **never starts or stops PostgreSQL**.
If the service is unavailable, start it through its normal Windows service controls
and retry. `db-stop` and `db-create` refuse port 5432. Helpers default to
`C:\Program Files\PostgreSQL\18\bin`; pass `-PostgresBin 'your-path'` when needed.

### Provision and migrate the current 5432 database

The active `.env` is configured for 5432 with separate `DB_*` fields and `DB_USER=postgres`.
Set `DB_PASSWORD` in `.env` to that account's existing password. Setup reads it directly
and creates `neurocare_db` if missing, with no password prompt:

```powershell
.\scripts\dev.ps1 db-setup
```

With `DB_USER=postgres`, this uses the existing account and creates only `neurocare_db`
if missing. It preserves existing records, role permissions and database ownership.
It uses the literal `DB_PASSWORD` from ignored `.env` for both maintenance and
application database connections, without client-side hashing or rewriting the file.
PostgreSQL continues to manage its own server authentication. The optional
`DB_USER=neurocare` mode still prompts for a separate administrator password when
provisioning a dedicated non-superuser login instead. Then apply or reapply pending migrations:

If setup fails, its diagnostic identifies the administrator or application connection
without printing passwords. With `DB_USER=postgres`, `DB_PASSWORD` must match the
existing server's `postgres` password; there is no interactive setup prompt. Editing `.env` never
resets that account's server password. A PowerShell exit-code error only
reports the Python command failure; read the setup diagnostic immediately above it.

```powershell
.\scripts\dev.ps1 migrate
.\scripts\dev.ps1 start
```

`migrate` upgrades to the latest schema without resetting the database. On an already
current schema it has no new migration to apply. No copy from 55432 is required for
this setup. Provisioning, schema migration and live startup still require access to
the actual local PostgreSQL service.

### One-time copy from the preserved project cluster (55432)

This optional data-preserving copy is for a configuration that still selects 55432.
The active configuration has already been switched to 5432 at the user's request,
without copying source data. The copy command refuses to run against that target
configuration; use the provisioning/migration commands above for the current setup.
If source recovery is deliberately required, select the original `DB_PORT=55432`
with its matching source credentials before running this one-time copy.
Both servers must be running before copying. Run this in an **interactive local
PowerShell terminal** from the project root, with the project's existing environment
and dependencies. Do not paste the administrator password into a command or chat:

```powershell
.\backend\.venv\Scripts\python.exe scripts/migrate-postgres.py
if ($LASTEXITCODE -eq 0) { .\scripts\dev.ps1 start }
```

The migration reads the existing source credentials from ignored `.env` and prompts
for the `postgres` administrator password with input hidden. It connects only to
`neurocare_db` and the `postgres` maintenance database. It checks both endpoints and
existing target ownership/privileges before stopping application processes. Only
listeners whose executable command identifies this project's API or Vite are stopped;
unrecognized listeners cause an error. A reload-enabled API must be stopped normally
before retrying. PostgreSQL services are never stopped by the migration.

The command then locks source tables against writes, saves a custom-format backup
under ignored `.db-backups/<UTC timestamp>/neurocare-55432.dump`, and copies the schema,
rows, Alembic revision and sequences. Restore uses the non-superuser login and a single
transaction, without drop/clean flags. An existing target with different data or another
owner is preserved and causes an error; it is never silently merged or overwritten.
An existing role's password and privileges are never reset. A partially provisioned,
empty target can be retried after correcting the error.

Before switching `.env`, verification compares every table's count and row hash,
sequence values/called state and normalized schema dumps. It also runs Alembic upgrade
and the full backend suite with database, model and persistence checks enabled against
the target. Those tests delete only their own synthetic records; sequence numbers
advance normally. Unrelated `.env` settings, including model configuration and secrets,
are preserved. The source database and backup remain available. Source table locks
are released when the command finishes, including on failure.

The backup folder's `verification.json` records completed stages without credentials.
If copying fails, the configuration is preserved; already stopped application processes
may need `.\scripts\dev.ps1 start` to resume using the unchanged source. If the source
changes after a failed copy, retrying refuses differing target data for manual review.
Do not drop either database to force a retry. After a successful switch, this one-time
command deliberately refuses to run again because `.env` no longer selects 55432.

The original `.postgres-data` cluster records port 55432 in `postmaster.opts` and is
retained as a fallback. `db-run`/`db-start` can manage it only while the active connection
selects its recorded local port. Missing port metadata, remote hosts and mismatched
ports fail closed. Do not reinitialize, rebind, delete or overwrite that cluster.
For a deliberate rollback, stop the application normally and restore its previous
55432 connection settings; newer target records must be reconciled before rollback.

See [migration verification status](docs/postgres-migration-status.md) for the checks
actually executed in the restricted development session. Preparing this helper does
not mean the database has already been copied or the active configuration switched.

### Docker Compose alternative for a separate fresh setup

Use Compose only when no other PostgreSQL server occupies the chosen host port.
Do not run it alongside the existing service on 5432. A different explicit
`DB_PORT` is required for concurrent use.

```powershell
docker compose up -d db
docker compose ps
```

Compose binds to loopback and retains its independent `postgres_data` volume. Its
bootstrap user is an administrator; provision a separate non-superuser application
login before using that instance with NeuroCare. Changing `.env` credentials does
not change an existing volume's roles or passwords. Stop with `docker compose stop db`;
never delete data or volumes as a connection fix.

## Migrations and application startup

For the configured native Windows workspace, start everything with **one command**:

```powershell
.\scripts\dev.ps1 start
```

This reuses the existing PostgreSQL service on 5432, applies Alembic migrations, starts
or reuses the API and Vite, checks database connectivity, and prints the site URL. It
requires the existing environment, installed dependencies, and provisioned database.
For an explicitly selected project cluster on its recorded port, it can start that
cluster. It does not install packages, initialize data, create the database, or train
a model. Keep its terminal open
when it starts services; Ctrl+C stops only the API/frontend it started. PostgreSQL and
already-running services remain running. If all services were already healthy, it
returns immediately without starting duplicates. Occupied unhealthy/unrecognized ports
produce an error instead of killing a process or silently changing the URL.

The launcher uses the backend without reload to avoid the Windows child-process problem
below. Its hidden service output is saved in ignored `.dev-logs/Backend.log`,
`Backend-error.log`, `Frontend.log` and `Frontend-error.log`. To change backend code,
stop/restart the launcher or use the individual reload-enabled backend command.
After a database or model configuration change, stop the old API first: a healthy
reused API retains its cached configuration until restarted. To check reuse, run
`.\scripts\dev.ps1 start` again in another terminal; it should return without duplicates.
Pass `-PostgresBin 'your-path'` for a different native PostgreSQL installation.

Individual commands remain available:

With PostgreSQL running, in terminal 2:

```powershell
.\scripts\dev.ps1 migrate
.\scripts\dev.ps1 backend
```

In terminal 3:

```powershell
.\scripts\dev.ps1 frontend
```

Open [NeuroCare](http://localhost:5173) or [the prediction form](http://localhost:5173/predictions).
API documentation is at http://localhost:8000/docs. Both dev servers bind to loopback.
Ctrl+C stops each dev server. If Windows managed execution prevents Uvicorn’s reload
child process from starting (`WaitNamedPipe` / `WinError 2`), use the tested no-reload
fallback from the root in terminal 2:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

If an older backend is already running, stop/restart it
after configuration changes; verify the version and threshold displayed on the form.

Alembic owns the schema; startup does not silently create tables. From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m alembic current
# For future schema changes, review the generated migration before applying it:
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m 'describe change'
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## Dataset, model and evaluation

The configured **2021 ANN** restores the recall-focused cutoff with **82.82% recall,
67.04% accuracy and 29.78% precision** on 40,376 previously evaluated test records.
It missed 1,076 of 6,264 positive labels and flagged 12,231 negative labels as positive.
This is a deliberate detection-versus-false-positive tradeoff, not a clinical standard.
The weights are unchanged. This is not new independent validation or improved learning.
See [the current recall policy report](docs/recall-policy-results.md).

Source: [CDC BRFSS 2021](https://www.cdc.gov/brfss/annual_data/annual_2021.html), with
its [official codebook](https://www.cdc.gov/brfss/annual_data/2021/pdf/codebook21_llcp-v2-508.pdf).
The supplied XPORT file remains unchanged in `data/raw/LLCP2021.XPT`.
The derived complete-case CSV and mapping manifest are in `data/processed/`.
Conversion retained 236,376 of 438,693 records. Unknown/refused responses were excluded,
not changed to No. Only health-day code 88 becomes zero. BMI is divided by 100 and
rounded to the supported integer range. Income uses **2021 nominal USD**, with the
upper categories combined. Age is a source band, not years. The target is DIABETE4
survey yes=1; no, pregnancy-only and borderline/prediabetes=0. Neither label establishes
a person's health status.

Old 2015 data and artifacts are preserved. Their labels were not blindly merged into
2021 training. The 2021 cohort quarantined 13,776 profiles matching old held-out data
and forced 20,789 prior-training matches into training only. The resulting artifact
cohort has 222,600 rows: **141,834 training / 40,390 validation / 40,376 test**.
Identical profiles stay together, and new held-out profiles are absent from the entire
2015 dataset. This is a profile-overlap guard, not verified person identification.
Complete-case exclusions, changed questions, nominal income and absent survey weights
limit generalization; the holdout is not a weighted representative population sample.

ANN: 21 inputs -> Dense(64, ReLU) -> Dropout(0.1) -> Dense(32, ReLU)
-> Dropout(0.1) -> sigmoid. Hidden layers use L2 0.0001. The 2021 weights were previously
fine-tuned from the 2015 ANN, adapting the first layer to new training-only scaling.
That run completed 19 epochs with Adam (initial learning rate 0.0001), binary
cross-entropy, batch size 512, a 60-epoch ceiling, early stopping patience 8, restored
best weights and plateau learning-rate reduction. No extra training was needed for
this policy restoration. The original cutoff maximizes validation accuracy subject to
the saved 83.253968% validation recall floor, with ties favoring recall. It was originally
chosen on validation only; this restoration performs no new threshold search.

| Configured ANN test metric | Measured value |
| --- | ---: |
| Accuracy | 67.04% |
| Recall | 82.82% |
| Precision | 29.78% |
| Specificity | 64.14% |
| ROC AUC | 0.8129 |
| Average precision | 0.4293 |
| Brier score | 0.10743 |
| Decision threshold | 0.132128 |

Majority-only accuracy is **84.49%** with zero positive recall. Confusion counts are
TN 21,881; FP 12,231; FN 1,076; TP 5,188. The retired accuracy-first cutoff gave
85.01% accuracy but only 13.95% recall on these same rows and weights. Its artifact is
preserved for offline inspection and no longer accepted by the public 2021 inference
contract. Ranking and score metrics are unchanged by the cutoff. The historical 68.96%
result used a different 2015 cohort.
The model score is not established as a calibrated personal probability. This is an
educational dataset classifier, not a screening or diagnostic tool.

To independently verify the configured policy from `backend/` without retraining:

```powershell
.\.venv\Scripts\python.exe -m app.ml.audit --output ../docs/recall-policy-audit.json
```

The command checks hashes, scaling, splits, validation-only cutoff selection and saved
metrics; it never edits `.env` or trains. Preserve raw data and original artifacts.
Public 2021 inference requires explicit recall-policy review, validation-only selection,
a validation recall floor of at least 80%, validation results meeting that floor, and
test recall of at least 80%. This is a project guard, not a clinical standard or a
guarantee of future performance. Accuracy-first experiments and unreviewed artifacts
remain offline. Matching source-year semantics and a measured tradeoff notice are
shown with results. Review the tradeoff before
changing MODEL_DIR, and restart FastAPI after any change. Use forward slashes inside
quoted Windows paths to avoid dotenv escape sequences. Use trusted local artifacts;
checksums do not make an untrusted model safe.

Earlier experiments and commands remain documented in the [2021 data report](docs/brfss2021-results.md)
and the [historical 2015 comparison](docs/accuracy-improvement.md). The original
`app.ml.train` CLI remains 2015-only and rejects a 2021 conversion manifest.

## Tests and integrity audit

### Additional BRFSS 2021 data

The new dataset was converted and used in fresh training/transfer experiments. The
initial recall-focused comparison did not improve accuracy; it is recorded in the
[historical 2021 report](docs/brfss2021-results.md). The later user-requested accuracy
policy is retained as a historical experiment; its low recall prompted restoration
of the reviewed recall-focused variant described above. These are different objectives,
not contradictory measurements of one operating point.

### Application checks

Frontend regression tests, lint, explicit TypeScript checks and production build:

```powershell
npm run test --prefix frontend
npm run lint --prefix frontend
npm run typecheck --prefix frontend
npm run build --prefix frontend
```

The regression tests cover API origin selection, empty/zero/range validation,
visible invalid-field focus order and audited small-text contrast. They complement
live browser checks; they do not substitute for a real API/model/database submission.

With PostgreSQL running and MODEL_DIR configured, run all tests from the root:

```powershell
$env:RUN_DB_TESTS='1'
$env:RUN_ML_TESTS='1'
$env:RUN_MODEL_TESTS='1'
try { .\scripts\dev.ps1 test }
finally { Remove-Item Env:RUN_DB_TESTS,Env:RUN_ML_TESTS,Env:RUN_MODEL_TESTS }
.\scripts\dev.ps1 check
.\backend\.venv\Scripts\python.exe -m pip check
```

Without those flags, external-resource tests skip explicitly; that is not proof of
database/model verification. Integration tests create synthetic rows and delete only
their own records. They verify persistence across fresh sessions, input validation,
database errors, absent/corrupt models, saved metrics and threshold propagation.

Independently recompute model integrity from `backend/` without fitting anything:

```powershell
.\.venv\Scripts\python.exe -m app.ml.audit --output ../docs/integrity-audit.json
```

This checks dataset hash, full/disjoint split coverage, cross-split profile overlap,
training-only statistics, validation-selected cutoff and recomputed test metrics.
Floating-point comparisons allow documented numerical tolerances.

## API and prediction history

| Endpoint | Behavior |
| --- | --- |
| `GET /api/health` | Application health |
| `GET /api/health/db` | Real PostgreSQL check; 503 if unavailable |
| `GET /api/v1/` | API identity/version |
| `GET /api/v1/model/contract` | Shared 21-field form contract; does not require a model |
| `GET /api/v1/model` | Active artifact's saved metrics/version/cutoff; 503 if unavailable |
| `POST /api/v1/predictions` | Strict JSON input; 201 only after database commit; ID, class, score, version and cutoff |

Required/range checks run in the browser and are enforced again by Pydantic. Invalid
requests return 422 with safe field-specific messages; SQL/model errors return generic
503 messages. A lost response can follow a successful commit, so POSTs are not automatically
retried. There is no authentication or history browsing UI/API. PostgreSQL does retain
prediction history, including input JSON, output, version and timestamps.

For a university demonstration, inspect saved history from `backend/`:

```powershell
@'
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Prediction
with SessionLocal() as session:
    query = select(Prediction.id, Prediction.predicted_class, Prediction.predicted_probability,
                   Prediction.model_version, Prediction.created_at).order_by(Prediction.id.desc()).limit(5)
    for row in session.execute(query):
        print(row)
'@ | .\.venv\Scripts\python.exe -
```

Earlier browser verification retained synthetic demonstration row ID 7 in its then-active database;
Phase 6 retained record #2. Phase 7 retained fictional test record #4 returned by the real API
with HTTP 201, dataset label 0, displayed score 0.3% and cutoff 12.85%. No rows were deleted
in that redesign. See the historical [Phase 7 browser checks](docs/phase7-browser-verification.json) and
[Phase 7 report](docs/phase7-redesign.md); earlier browser records describe their own environments.

The latest design completion verified a full fictional browser submission with HTTP 201
and retained record **#6** in the current environment: label 0, displayed score 2.9%,
cutoff 0.132128, model `20261029T043159Z-bd9e866c`. No previous records were deleted.
Current [design browser checks](docs/newdesign-browser-verification.json) cover form
validation, review/edit/back/reset, keyboard controls and 25 route/viewport combinations.

## Security and troubleshooting

`.gitignore` excludes root/nested `.env` files, the venv, dependencies, logs, database
data, database backups, temporary password files and datasets in `data/`.
`.env.example` and trained model bundles in `artifacts/` remain includable.
Do not force-add secrets; ignore rules do not remove files already tracked by Git.
No credentials appear in frontend variables or API error responses. There is no
public repository URL or open-source license in the supplied workspace; the site
does not claim a specific license or invent a repository link. CORS allows only
the configured origin plus its same-port loopback alias in development only. The native bootstrap role is a local development administrator;
use a separate non-superuser role for an independently managed server. Keep this
unauthenticated educational application on loopback; public deployment is out of scope.

- **503 database unavailable:** keep PostgreSQL running, match host/port/credentials,
  and run migrations. Use `127.0.0.1` for this IPv4-only native cluster. Do not reset data.
- **Old model/version:** restart FastAPI after `.env` or artifact changes; a process cache
  can otherwise retain the previous model. Check `/api/v1/model` and the form's version.
- **Missing-model error:** set MODEL_DIR to the complete version directory, restart the
  backend, then use the form's Retry connection button. Metadata/inference cold starts
  have a bounded 20-second client timeout.
- **CORS/connection error:** localhost and 127.0.0.1 are distinct browser origins.
  Development permits both names on the configured FRONTEND_URL port. Other ports,
  schemes and external hosts are not implicitly allowed; non-development environments
  permit only the exact configured origin. VITE_API_URL must point to the backend.
- **Port busy:** reuse the known project server or stop it normally. Do not launch another
  instance against the same data directory or kill unrelated processes.
- **Wrong input codes:** use category dropdowns; a fractional value, age in years or
  a field from the older Pima schema is rejected. No invented values are substituted.
- **Package/DLL errors:** confirm the Python 3.11 venv and registry access; check the
  Windows runtime if TensorFlow cannot import. `pip check` validates installed dependencies.
- **Non-failing warnings:** Starlette/AnyIO deprecation and Node module.register/npm
  http-proxy environment notices were observed. They were recorded, not suppressed.

POSIX convenience commands remain in `Makefile`; Windows should use `scripts/dev.ps1`.
Authentication, history screens and public hosting remain outside scope. The website
is a public-facing visual design; it does not deploy or harden the server for
public hosting. Production hosts must serve the Vite output with SPA fallback for
`/predictions`, `/model` and `/about`, and configure the real API origin/CORS explicitly.
