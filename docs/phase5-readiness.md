# Phase 5 — QA and release readiness

Review: 2026-10-28. The Phase 4 design, trained weights, schema and existing stack
were preserved. The active connection remains `postgres` / `neurocare_db` on 5432;
no credential value appears in this report. No database, role or existing record was
deleted, and no model was trained.

**Status: the core university demonstration worked in the real browser; complete
release sign-off remains pending.** The full HTTP/database suite, independent SQL
read-back and repeated launcher checks could not be completed from this restricted
process. One browser CSP diagnostic remains unattributed. This is not a public-hosting
or clinical-readiness approval.

## Confirmed defects fixed

| Finding | Final behavior |
| --- | --- |
| Production frontend defaulted to the visitor's localhost:8000 | Unconfigured production uses same-origin `/api/*`; development retains its local default. Explicit VITE_API_URL overrides both. The final production JS contains no localhost API fallback. |
| Empty form focused HighBP before visually earlier unanswered Age fields | Client and server field errors focus the first invalid control in rendered form order. Empty answers remain missing; literal zero remains valid. |
| Menu state could survive navigation through the brand/other links | Route/hash changes close the menu. Path changes focus main content without disturbing the chosen scroll position. |
| Four small-text styles had insufficient contrast | Existing darker palette token replaces those colors; regression checks require at least 4.5:1 on their actual backgrounds. |
| Generated Vite/type-check caches lacked explicit ignore coverage | Added `.vite`, `.mypy_cache` and TypeScript build-info ignore patterns. Existing private-file exclusions remain. |

Original contrast calculations: context italic 4.49:1, stack numbers 3.52:1,
fieldset numbers 4.05:1 and required marks 4.32:1. The updated text uses `--muted`:
approximately 5.39:1 on paper, 4.9:1 on the about background and 5.8:1 on form white.
These are CSS color calculations, not a complete automated accessibility certification.

## Checks actually executed

| Check | Outcome |
| --- | --- |
| Focused backend/model/privacy/setup suite, RUN_MODEL_TESTS=1 | **65 passed, 3 deselected**, 9.28 seconds; existing Starlette/AnyIO deprecation warning |
| Full backend suite with database/model flags | **Not completed**: stalled at the first TestClient health test; watchdog terminated after 25 seconds, exit 1. No full-suite pass claimed. |
| Frontend regression suite | **8 passed**, covering production origin, zero/empty/range inputs, focus order and contrast |
| Frontend ESLint | Passed |
| TypeScript `tsc -b` | Passed |
| Vite production build | Passed; final JS 298.03 kB / 98.46 kB gzip, CSS 29.63 kB / 7.13 kB gzip |
| Backend/scripts Ruff | Passed |
| Installed Python dependency consistency (`pip check`) | Passed; no broken requirements |
| PowerShell parser: dev/start/stop-project-apps | Passed |
| Independent saved-model integrity audit | Passed; real weights, CSV, saved splits, preprocessing, threshold and recomputed test metrics |
| Git ignore behavior in a disposable repository | Passed for 15 private/generated paths; five examples/docs remained includable |
| Configured secret literal scan | No matches outside ignored `.env` in the 105 source/document files scanned |

The focused suite ran from `backend/` with:

```powershell
$env:RUN_MODEL_TESTS='1'
.\.venv\Scripts\python.exe -m pytest -q tests/test_config.py tests/test_db_setup.py tests/test_public_contract.py tests/test_evaluation.py tests/test_ml_data.py tests/test_prediction_service.py tests/test_model_artifact.py -k 'not endpoint and not incomplete_artifact'
Remove-Item Env:RUN_MODEL_TESTS
```

Unit tests with mock sessions are identified as unit checks. They were not counted as
real database persistence. No SQLite, fake model, mock API responses or invented
metrics replaced the actual application integrations.

## Real browser journey

Native Chrome accessed the actual running application at `http://localhost:5173`.
The in-app browser failed with a session mismatch; native Chrome was the fallback.

- Homepage and prediction route loaded; homepage health showed API and PostgreSQL connected.
- The form rendered all 21 fields from FastAPI's real contract; labels and source-code
  descriptions were present. No sign-in/private dashboard was introduced.
- Empty submission displayed required-field errors. A synthetic profile with BMI 10
  was rejected with the 12–98 range message.
- Correcting BMI to 25 returned **saved demonstration #1**, class **1**, displayed
  score **14.0%**, cutoff **12.85%**, version `20261027T204111Z-db7cb83c`.
  The synthetic demonstration row was retained. The backend commits and refreshes
  before returning success; independent fresh-session SQL retrieval was not executed.
- Responsive navigation opened at tablet width; Escape closed it. Keyboard brand
  navigation returned to the homepage. FAQ anchor navigation worked; click opened
  an accordion and Enter closed it.
- Loading indicators were observed during real navigation. Missing/corrupt model
  checks passed in the focused suite; no live outage was deliberately introduced
  into the user's running services.

| CSS viewport | Reviewed views |
| --- | --- |
| 400 × 858, mobile | Homepage, single-column form controls and saved result |
| 768 × 1024, tablet | Homepage, two-column form fields, collapsible navigation |
| 1366 × 900, laptop | Homepage hero and desktop navigation |
| 1920 × 1080, desktop | Homepage, FAQ anchor and accordion |

No clipping or horizontal overflow was visible in those reviewed views. This was
visual inspection, not an all-elements DOM geometry, axe, Lighthouse or screen-reader
audit. Semantic fieldsets/labels, native details/summary accordions, focus styles,
skip link and reduced-motion rules were also inspected in source.

Real captures: [desktop homepage](phase5-home-desktop.png),
[mobile saved prediction](phase5-prediction-mobile.png).
[Browser observations and hashes](phase5-browser-verification.json) record the scope.

Chrome displayed the React DevTools informational message and **one CSP blocked-eval
issue**. Its affected-resource table supplied no source location, so attribution to
the app or an extension is unresolved. The production JS contains no `eval(` or
`new Function(` match. No CSP or browser protection was weakened to hide the warning.

## Privacy and ML integrity

The public GET route inventory is limited to health, API identity and model/contract
information. Regression checks found no matching GET route for prediction lists,
prediction IDs, users or history. The prediction response schema excludes stored
input JSON, identifying references, names and email. Backend inputs reject extra
fields, booleans, strings, floats and out-of-range codes. Error-handler inspection
confirmed generic database/internal failures and validation messages without raw
input values. HTTP-level privacy/error tests still need the full local test run.

The [model audit](phase5-model-audit.json) verified all 253,680 rows partition exactly
once, with no identical feature profiles crossing splits. Training-only scaling
matches the saved pipeline; validation-only F2 selection reproduces cutoff
0.1284888238. Recomputed test metrics match the saved 50,901-row test partition.
The UI architecture matches 21 inputs → Dense(32, ReLU) → Dropout(0.2) →
Dense(16, ReLU) → sigmoid. Inference disables training/dropout.

This reuses a previously reported test partition; it is not new independent
validation. Scores are not established personal disease probabilities. The public
copy retains historical-survey, population, imbalance and self-report limitations.

## Remaining release and GitHub gates

1. Run the complete backend suite locally with PostgreSQL/model flags, verify Alembic
   head/schema checks and retrieve the browser's synthetic record using a fresh SQL
   session. This execution process receives Windows socket error 10013 on 5432,
   8000 and 5173; that does not establish those services are stopped.
2. Repeat the single-command launcher in another terminal and verify service reuse
   and cleanup ownership. These live process checks were not performed here.
3. Isolate the browser CSP warning in a clean profile before claiming a clean console.
   External dataset links and every page at every viewport were not exhaustively tested.
4. No Git repository exists in this workspace. Ignore behavior and a source scan
   cannot establish whether secrets exist in a future repository's tracked history.
   Review staged files/history before pushing. License choice and a public repository
   URL remain owner decisions; no license was invented.
5. Registry-based vulnerability auditing, public hosting, rate limits and production
   operations were outside this executed pass. The explicitly selected local `postgres`
   account remains privileged; use an appropriate dedicated role for public deployment.

## Exact local commands

From the project root, one-time setup and migrations if needed:

```powershell
.\scripts\dev.ps1 db-setup
.\scripts\dev.ps1 migrate
```

Normal startup remains one command:

```powershell
.\scripts\dev.ps1 start
```

Open `http://localhost:5173`. For the selected `postgres` account, setup reads the
literal password from ignored `.env` without prompting. It creates only a missing
`neurocare_db` and does not reset the account or delete data. The launcher reuses
the existing PostgreSQL service on 5432; cluster management helpers refuse to start
or stop a server on that port. Follow README for the full test flags, model-audit
command and frontend checks. No retraining is required for this review.
