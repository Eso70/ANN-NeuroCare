# University demonstration review

Review date: 2026-10-27. The existing React/FastAPI/PostgreSQL/ANN architecture and
trained weights were retained. No authentication, history screens, new charts or public
hosting were added. [README.md](../README.md) is the current setup/run guide; older phase
reports preserve earlier results and are not the source of current setup instructions.

## Findings and corrections

| Finding from inspection | Action |
| --- | --- |
| API validation returned only “Invalid request” | Added field-specific 422 messages without raw inputs, arbitrary submitted names or exception context |
| Frontend did not render server field messages | Added accessible field errors and retained native required/range checks |
| Successful reconnection left an old missing-model alert visible | Retry now clears stale errors/results, shows a loading state and prevents concurrent retry clicks |
| Cold TensorFlow imports could outlast the original 6-second model timeout | Model metadata/inference requests have bounded 20-second timeouts; absent/corrupt file checks now precede TensorFlow import |
| Running API initially served the older model despite updated `.env` | Confirmed after reload that live version/threshold match configuration; README requires process restart after config/artifact changes |
| “Holdout” labeling could imply a new independent evaluation | UI explicitly says saved test-set results from the previously reported partition |
| README contained obsolete phase and database-blocked claims | Replaced chronological setup claims with a single current installation/run/test guide |
| Project had no history browsing feature | Verified PostgreSQL history retrieval across fresh sessions; documented that no history UI/API exists |
| Workspace was not a Git repository | Tested actual ignore semantics separately; no tracked-secret audit or repository initialization was falsely claimed |

## Executed checks

| Check | Actual outcome |
| --- | --- |
| Baseline full backend suite, database/model flags enabled | 39 passed, no skips |
| Final expanded backend suite, same flags enabled | **49 passed, no skips**, 10.66 seconds |
| PostgreSQL health/schema | Real configured PostgreSQL; table presence checked by integration tests |
| Prediction persistence/history | Real ANN requests saved and retrieved from new sessions; multi-record history order/inputs verified; automated test rows cleaned up |
| Missing/corrupt artifacts | Explicit 503 behavior, checksum rejection and invalid threshold checks passed |
| Invalid request handling | Required/type/range/extra-field/invalid JSON cases passed; messages do not echo private submitted values |
| Saved model | Reload consistency, version/threshold propagation and metadata equality passed |
| Frontend | ESLint and TypeScript/Vite production build passed after final source changes |
| Backend | Ruff over `backend/`, Python compilation and `pip check` passed |
| PowerShell helper | Parser reported no syntax errors |
| Alembic | Upgrade/current/check succeeded; revision `0001 (head)`, no pending schema operations |
| Git ignore rules | Tested with Git in a disposable temporary repository; real root/nested envs and private artifacts ignored, env examples includable |
| Independent model audit | Dataset checksum, every-row-once partition, profile disjointness, train-only scaling, validation threshold and recomputed test metrics passed |

The tests were expanded for field-message safety, malformed JSON, history persistence
across new sessions, incomplete/damaged artifacts and invalid artifact thresholds.
Existing assertions were retained. There is no substitute SQLite/in-memory application
database. Dependency deprecation warnings were recorded rather than hidden or suppressed.

## Browser verification

The actual browser was opened at `http://localhost:5173` against the running API at
`http://localhost:8000`. The dashboard showed frontend, backend and PostgreSQL connected.
The form displayed the active version `20261027T204111Z-db7cb83c`, cutoff 0.128489,
and saved evaluation values matching the configured artifact.

Verified through browser controls:

- Empty submission showed required-field validation, without a saved-success state.
- BMI 10 was rejected with the source-range minimum of 12.
- A complete synthetic submission returned a real saved prediction, ID **7**, class 0,
  approximately 4.6% model score, active cutoff/version, and educational notice.
- That exact row was retrieved using a new SQLAlchemy session; its inputs matched the
  synthetic form. It is retained as one demonstration record, not a real person's data.
- On isolated localhost ports 15173/18080, a deliberately absent model returned a visible
  “Model unavailable. Train and configure a trusted model first.” alert with no fake success.
- Restoring the configured model and Retry connection exercised recovery. The test first
  exposed the stale-alert bug listed above; after correction the old alert cleared during
  loading and successful model information returned.

Evidence: [successful browser result](demo-prediction.png),
[missing-model response](demo-model-error.png), and
[recovered model with no stale alert](demo-model-recovery.png), plus
[database verification of the browser record](browser-demo-verification.json).
Isolated test processes used per-process environment overrides; the normal application
configuration and user servers were not switched to a missing model.

## Machine-learning integrity

The independent [audit output](integrity-audit.json) recomputed all reported metrics
from the 50,901 saved test rows and verified the persisted preprocessing statistics
against the 152,419 training rows. The remaining 50,360 rows are validation data.
Identical input profiles do not overlap across partitions. Validation-only F2 selection
reproduced the saved threshold. No fitting, threshold adjustment or metric substitution
was performed during this review.

The model weights are unchanged from the original ANN. Active test results:

| Metric | Value |
| --- | ---: |
| Accuracy | 68.87% |
| Precision | 28.03% |
| Recall | 82.91% |
| Specificity | 66.67% |
| ROC AUC | 0.8251 |
| Average precision | 0.4167 |
| Brier score | 0.09553 |

There are no implemented charts to audit. The displayed evaluation card reads actual
saved metadata, and an HTTP test checks exact metric equality with that file. Dataset
provenance, ANN architecture, splitting and the cutoff policy are documented in README.

## Remaining limitations

- This is an educational classifier, not a diagnostic or screening tool. At this cutoff,
  only 28.03% of positive flags are positive test labels. Class 0 does not mean healthy.
- The test partition was already reported during development. This recomputation is not
  a fresh independent validation, although no test labels enter threshold selection.
- Historical US survey self-reporting, absent survey design weights and coarse input
  categories limit generalization. Source label recoding must be established before
  making specific clinical claims about diabetes versus prediabetes.
- No authentication or history browsing screen/API is implemented. Persisted history
  can be inspected with the documented SQLAlchemy command for the university demo.
- Ignore rules were verified, but tracked-secret status cannot be inspected until the
  workspace is a Git repository. See [security audit](security-audit.json).
- Non-failing warnings remain: Starlette/AnyIO BlockingPortal deprecation, Node's
  module.register deprecation, and an npm http-proxy environment warning. `pip check`
  reports no broken requirements; this is not a dependency vulnerability audit.

## Local startup

Run from `D:\Coding - Projects\NeuroCare`. Reuse healthy existing servers; do not start
another PostgreSQL instance against the same directory.

```powershell
# Terminal 1, only if the project database is not already running:
.\scripts\dev.ps1 db-run
```

```powershell
# Terminal 2:
.\scripts\dev.ps1 migrate
.\scripts\dev.ps1 backend
```

```powershell
# Terminal 3:
.\scripts\dev.ps1 frontend
```

Open http://localhost:5173/predictions. Prerequisites, fresh installation, database setup,
training, artifact selection, tests and troubleshooting are all in the README.
