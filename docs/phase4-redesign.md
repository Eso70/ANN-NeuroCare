# Phase 4 — Public research website redesign

Implemented and verified on 2026-10-28, following the root `phase4.md` instructions.
This is an extension of the existing React/Vite application, not a replacement project.

## Inspection and integration decisions

Before editing, inspected the routes, existing form and health hook, Axios client,
dependencies, API endpoints, PostgreSQL models, prediction service and tests,
CDC field contract, training code, and active model's saved metadata.

The working foundations already provided all necessary capabilities:

- The model contract API supplies the exact 21 input definitions, integer ranges and options.
- The model API supplies real saved evaluation, split sizes, version and decision threshold.
- Predictions run the real ANN and return success only after PostgreSQL persistence.
- No GET prediction-history endpoint exists; the redesign introduces no public history.

No backend, migration, schema, environment secret, dataset, model artifact or dependency
changes were required. The active model's SHA-256 remains
`1e1a6da1490d36f0743f4a71503d0c76416058bf33725c0736c4a883e2dc97ce`.

## Implemented design and interactions

- Warm ivory, forest green, sage and restrained clay colors, reusable CSS design tokens,
  system sans-serif body text and Georgia editorial headings. No remote font dependency.
- Responsive shared header/footer, original botanical wordmark/favicon and original
  SVG scientific artwork. The network diagram shows the inspected architecture and
  explicitly identifies representative nodes rather than learned weights.
- `/`: research context, four actual workflow steps, ANN explanation, live saved
  evaluation, labeled confusion-matrix table, data-driven split visualization,
  dataset sources and limitations, project stack, keyboard-operable FAQ and live health checks.
- `/predictions`: all 21 contract fields in five groups, descriptions, styled native
  controls, custom inline required/range/integer errors, associated ARIA descriptions,
  focus on invalid input, synchronous pending-request lock, disabled loading controls,
  retry handling, reset and make-another-prediction actions, actual persisted result.
- Unknown routes: custom not-found page and working return links.
- Mobile navigation supports toggle, Escape and closing after navigation. Skip link,
  visible focus, native fieldset/legend semantics, accessible details/summary FAQ,
  semantic table headings and reduced-motion styles are included.
- Meaningful page titles, meta description and favicon. Direct route loading verified.

Shared building blocks live in `SiteElements`, `ScientificDiagram`, `ModelEvaluation`,
`LandingSections`, `SurveyField`, `PredictionResult`, the existing `StatusCard`, and
the updated `AppLayout`. `useModel` separates cancellable loading/retry state from
rendering; centralized Axios and existing health hooks remain in use.

No packages, component libraries, 3D runtime, analytics, browser input storage,
authentication, accounts, pricing or public history were added. All artwork is original;
no third-party component or artwork license obligations were introduced.

## Honest research and project information

Metrics, confusion-matrix counts and split sample counts are fetched from the model API.
Unavailable model data gets an explicit unavailable state, not substitute values. The
actual artifact saves F2 rather than F1, which the interface explains. The ANN architecture
and training discussion describe the inspected code. Dataset links are the actual sources
already recorded in project metadata.

The site states that the classifier is educational, not a diagnosis, screening service,
or future-risk estimate. It explains the low precision / higher recall tradeoff, repeated
development test partition, historical self-reporting, class imbalance and lack of clinical
validation. Synthetic input storage is disclosed before submission.

There is no supplied public repository URL or open-source license. The site states this
rather than claiming unspecified reuse rights. Optional `VITE_REPOSITORY_URL` and
`VITE_DOCS_URL` accept real HTTPS destinations; links are omitted when absent or invalid.
Changing these Vite variables requires restarting the development server or rebuilding.

## Executed verification

Commands from the root (backend tests from `backend/`):

```powershell
npm.cmd run lint --prefix frontend
npm.cmd run build --prefix frontend

cd backend
$env:RUN_DB_TESTS='1'
$env:RUN_ML_TESTS='1'
$env:RUN_MODEL_TESTS='1'
.\.venv\Scripts\python.exe -m pytest -q
```

- ESLint passed. Production build includes `tsc -b`; TypeScript and Vite passed.
  Final output: JS 297.64 kB / 98.31 kB gzip, CSS 29.58 kB / 7.14 kB gzip.
- All **59 backend tests passed, no skips**, in 17.10 seconds, including real PostgreSQL
  and model integration. Backend code was preserved; tests were run as a regression check.
- Non-failing npm `http-proxy`, Node `module.register` and Starlette/AnyIO deprecation
  notices remain visible; no warning was suppressed or test weakened.
- Browser verified actual saved metrics: accuracy 68.9%, precision 28.0%, recall 82.9%,
  ROC AUC 0.825; confusion matrix `[[29343,14667],[1178,5713]]`; split counts
  152419 / 50360 / 50901. All came from the configured API.
- Empty submission displayed 21 field errors; BMI 10 displayed the valid range 12–98.
- A complete synthetic form produced prediction **#50**, class 0, score
  `0.0456806905567646`, threshold `0.12848882377147675`, active model
  `20261027T204111Z-db7cb83c`. A fresh SQLAlchemy session confirmed that row, its
  21 input values, model version and timestamp. Retained as a synthetic demo record.
- Make-another/reset cleared all 21 inputs and removed the result; focus returned to Age.
- Homepage/navigation/model sections/FAQ/404 and direct `/predictions` loading worked.
  FAQ toggled by click and Enter; mobile menu toggled, closed after section navigation,
  and closed with Escape. Page titles changed correctly.
- Measured no horizontal overflow on `/` at 320, 390, 768, 1024, 1440, 1920 widths,
  and `/predictions` at 320, 390, 768, 1024, 1440. This is layout verification, not a
  comprehensive accessibility certification or physical-device test.
- Normal-operation browser console inspection returned no warnings or errors.
- Isolated Vite 15173/API 18080 verified offline API errors, missing-model real 503,
  21 fields but no metrics/disabled submit when the model was missing, recovery through
  Retry, and a failed POST after stopping only that test API. The failed POST showed
  a useful message, no result and a re-enabled submit control. Test services were stopped.
- Existing API 8000, Vite 5173 and native PostgreSQL 55432 were left running.

Browser evidence is in `phase4-home-desktop.png`, `phase4-home-mobile.png`,
`phase4-prediction-mobile.png`, `phase4-api-unavailable.png` and `phase4-model-evaluation.png`.
The API-unavailable screenshot intentionally captures a failure test, not normal status.
Responsive measurements are in `phase4-browser-verification.json`.

## Launch locally

Use separate PowerShell terminals, starting in the project root:

```powershell
# Terminal 1: reuses an already healthy server, preserves the existing cluster.
.\scripts\dev.ps1 db-run

# Terminal 2: run migrations when setting up the application, then start FastAPI.
.\scripts\dev.ps1 migrate
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

# Terminal 3:
.\scripts\dev.ps1 frontend
```

Open http://127.0.0.1:5173 or http://localhost:5173. The existing native database and
trained MODEL_DIR are already configured. Do not start a second API on an occupied port.
The normal `scripts/dev.ps1 backend` helper enables reload; during this verification its
Windows child process failed with `WaitNamedPipe` / `WinError 2`, so the tested no-reload
command above was used successfully. No execution policy or security setting was bypassed.

## Remaining limits

This work redesigns the public-facing interface; it does not deploy the application or
make it a production clinical service. Keep the existing unauthenticated demonstration
on loopback. A future public deployment needs its own hosting, operational/privacy
review, real API/CORS configuration, HTTPS and SPA fallback for direct routes.
Public repository/documentation URLs and a project license still need to be supplied
by the project owner if publication and open-source distribution are intended.
