# NeuroCare AI — Technology and Algorithm Quick Reference

**Evidence date:** 29 October 2026.  
**Read first:** this is an educational survey-label classifier, not a medical diagnosis, screening service or calibrated future-risk estimator. The active policy prioritizes recall and has many false positives.

## 1. Project at a glance

| Item | Verified implementation / recorded value |
| --- | --- |
| Public interface | React/TypeScript single-page application with Home, prediction, model, About and 404 views |
| Backend | FastAPI JSON API, no implemented authentication or public history browsing |
| Persistence | PostgreSQL `neurocare_db`, configured port 5432; SQLAlchemy/Psycopg |
| Current model version | `20261029T043159Z-bd9e866c` |
| Current source contract | `cdc-brfss2021-binary-v1` |
| Target | 2021 `DIABETE4` yes = 1; pregnancy-only, no and borderline/prediabetes = 0 |
| Input count | 21 required integer features |
| Model type | Feedforward multilayer perceptron / artificial neural network |
| Current decision threshold | `0.132127583026886` |
| Model weights | Same as 2021 parent `20261028T222429Z-e5a45f4d`; restoration did not retrain |
| Single-command local startup | `.\scripts\dev.ps1 start` |
| Secrets | Read from ignored local configuration; never included in documentation |

## 2. Important technologies

| Layer | Technology and inspected version | What to explain in a presentation |
| --- | --- | --- |
| Languages | Python 3.11.9; TypeScript 5.8.3; CSS/HTML | Python handles data/model/backend work; TypeScript organizes typed frontend behavior |
| Interface | React/React DOM 19.0.0; React Router 7.5.1 | Components, state and public route navigation |
| Build/styling | Vite 6.3.3; Tailwind 4.1.4; shared CSS tokens | Development/build pipeline and consistent responsive styling |
| HTTP client | Axios 1.8.4 | Shared origin, cancellation and bounded request timeouts |
| Visuals | Lucide React 0.468.0; native SVG/CSS | Icons, actual ANN structure and actual confusion-count bars; no invented chart data |
| Installed but not central to current visuals | Recharts 3.0.2 | Dependency presence alone does not mean a chart dashboard is implemented |
| API | FastAPI 0.115.12; Uvicorn 0.34.2 | Typed routes, generated API documentation and ASGI serving |
| Validation/settings | Pydantic 2.11.4; pydantic-settings direct pin 2.9.1 | Exact required integers/ranges and environment configuration |
| Database access | SQLAlchemy 2.0.40; Psycopg 3.2.9 | ORM sessions and PostgreSQL transactions |
| Database/schema | PostgreSQL; Alembic 1.15.2 | Durable rows/JSONB; source revision `0001`; live state not reverified |
| Data | pandas 2.2.3; NumPy 2.1.3 | XPORT conversion, arrays and split files |
| ML | TensorFlow 2.19.0; Keras 3.15.1; scikit-learn 1.6.1 | ANN learning/inference, grouped splitting, reference classifiers and metrics |
| Quality tools | pytest 8.3.5; Ruff 0.11.8; ESLint 9.25.1; Node 26.3.1 | Regression checks, lint, type checking and build |
| Operations | PowerShell; optional Compose `postgres:18` | Existing-service reuse and process ownership; Compose is not the selected running database |

Installed backend/frontend versions are recorded in [runtime-check.json](runtime-check.json) and [source-evidence.json](source-evidence.json). The actual running PostgreSQL version was not obtained.

## 3. Dataset and encoding

| Item | Value / rule |
| --- | --- |
| Source | [CDC BRFSS 2021](https://www.cdc.gov/brfss/annual_data/annual_2021.html) |
| Raw local file | `data/raw/LLCP2021.XPT` |
| Raw wave records | 438,693 |
| Complete supported records | 236,376; class 0 = 202,810, class 1 = 33,566 |
| Complete-case exclusions | 202,317 raw records; approximately 46.12% |
| Historical held-out profile matches excluded | 13,776 additional processed rows |
| Prior training profile matches forced to training | 20,789 |
| Final cohort | 222,600; class 0 = 189,881, class 1 = 32,719 |
| Training | 141,834; positives 20,155 |
| Validation | 40,390; positives 6,300 |
| Test | 40,376; positives 6,264 |
| Split method | Stratified group folds, seed 42; identical profiles do not cross partitions |
| Missing values | Complete-case exclusion; unknown/refused values are not converted to No |
| Health-day zero | Raw 88 becomes 0 only for mental/physical health-day fields |
| BMI | Raw `_BMI5 / 100`, integer rounding, supported range 12–98; no clipping |
| Income | 2021 nominal USD; categories 8–11 merged into $75,000 or more; no inflation correction |
| Scaling | Training mean and population standard deviation; zero scales replaced by 1 |
| Sampling/weights | No class weighting, oversampling or survey weighting in the selected training workflow |

### Input groups

| Group | Actual fields |
| --- | --- |
| Background | `Age`, `Sex`, `Education`, `Income` |
| Health | `HighBP`, `HighChol`, `CholCheck`, `BMI`, `Stroke`, `HeartDiseaseorAttack`, `GenHlth`, `DiffWalk` |
| Daily life | `Smoker`, `PhysActivity`, `Fruits`, `Veggies`, `HvyAlcoholConsump` |
| Wellbeing | `MentHlth`, `PhysHlth`, `AnyHealthcare`, `NoDocbcCost` |

The 13 No/Yes indicators use 0–1. `Sex` separately uses source codes 0 Female/1 Male. `GenHlth` uses 1–5, `Age` 1–13 bands, `Education` 1–6, `Income` 1–8, BMI 12–98 and both day counts 0–30. All are integers; zero is valid where the contract permits it. The full feature/source mapping is in Section 4 of [the report](project-report.md).

## 4. ANN and training parameters

| Parameter | Actual selected setting |
| --- | --- |
| Architecture | 21 inputs → Dense 64 ReLU → Dropout 0.1 → Dense 32 ReLU → Dropout 0.1 → Dense 1 sigmoid |
| Dense layers | Two hidden layers plus one output layer |
| Parameter count | 3,521, derived including biases |
| Hidden kernel regularization | L2 = 0.0001 on both hidden layers; none specified on output kernel |
| Loss | Binary cross-entropy plus layer regularization losses |
| Optimizer | Adam |
| Initial learning rate | 0.0001 for the selected transfer configuration |
| Batch size | 512 |
| Maximum/completed epochs | 60 maximum; 19 completed |
| Best validation-loss epoch | 11, derived from saved parent trial history |
| Early stopping | Monitor `val_loss`, patience 8, restore best weights |
| Learning-rate schedule | Halve after 3 plateau epochs, minimum 0.00001 |
| Initialization | Prior 2015 model weights with first-layer adaptation to new standardization |
| Validation comparison | Fresh model: initial LR 0.001, 34 epochs; selected transfer model: initial LR 0.0001, 19 epochs |
| Candidate selection | Validation accuracy, then average precision, then lower Brier score |
| Cutoff selection | Maximum validation accuracy subject to saved validation recall floor 0.8325396825 |
| Threshold tie break | Greater recall, then higher cutoff |
| Public 2021 guard | Explicit review; validation-only recall-constrained selection; validation floor at least 80%, validation meets floor, measured test recall at least 80% |
| Inference | No training; dropout disabled; fixed saved scaling and cutoff |

The public guard is an internal project policy, not a clinical standard. Other scripts and historical artifacts use different settings; the original generic `train.py` 32/16 architecture is not the current model.

## 5. Equations worth understanding

| Method | Equation / explanation |
| --- | --- |
| Standardization | (z_j=(x_j-\mu_{j,train})/\sigma_{j,train}\); apply the same saved statistics to all later inputs |
| Dense layer | (a=\phi(Wx+b)\); weighted input combinations, bias and activation |
| ReLU | (\max(0,u)\); hidden nonlinear activation |
| Sigmoid | (1/(1+e^{-u})\); bounds the score, without proving calibration |
| Binary cross-entropy | (-[y\log s+(1-y)\log(1-s)]\), averaged across a batch, with L2 losses added |
| Backpropagation | Uses the chain rule to calculate gradients of loss with respect to weights |
| Adam | Updates weights using bias-corrected moving first/second gradient moments; initial LR is configured |
| Classification | Return label 1 if score ≥ 0.132127583026886; otherwise label 0 |

## 6. Actual evaluation

All current measurements use the previously evaluated 40,376-record test partition. The documentation-run audit recomputed them; this is not new independent validation.

| Metric | Current result | Meaning |
| --- | ---: | --- |
| Accuracy | 67.0423% | Correct classifications / all records |
| Precision | 29.7836% | TP / (TP + FP) |
| Recall | 82.8225% | TP / (TP + FN) |
| F1, derived in this report | 0.438120 | 2TP / (2TP + FP + FN) |
| Specificity | 64.1446% | TN / (TN + FP) |
| F2 | 0.610712 | F-score emphasizing recall |
| ROC AUC | 0.812885 | Ranking across thresholds, not accuracy |
| Average precision | 0.429336 | Precision–recall ranking summary |
| Brier score | 0.107429 | Mean squared score error; lower is better |
| Balanced accuracy, derived | 73.4835% | (Recall + specificity) / 2 |
| Always-negative accuracy, derived | 84.4858% | Majority fraction, with zero recall |

| Actual / predicted | Predicted 0 | Predicted 1 |
| --- | ---: | ---: |
| Actual 0 | TN 21,881 | FP 12,231 |
| Actual 1 | FN 1,076 | TP 5,188 |

F1 and balanced accuracy are calculated for the report; they are not claimed to be stored/returned by the current application. The retired 85.01% accuracy variant found only 13.95% of positive labels. Changing the cutoff changes classification errors but leaves the same model's ranking/ROC AUC unchanged.

## 7. API and persistence reference

| Endpoint / storage | Actual behavior |
| --- | --- |
| `GET /api/health` | Application liveness |
| `GET /api/health/db` | Real database health probe |
| `GET /api/v1/` | API identity/version |
| `GET /api/v1/model/contract` | Source-aware fields/options/ranges |
| `GET /api/v1/model` | Actual configured version, cutoff, architecture, metrics and limitations |
| `POST /api/v1/predictions` | Strict validation → inference → commit → 201 result |
| `/docs`, `/openapi.json` | Generated API documentation |
| `users` | Reserved ID/name/email/timestamp entity; no implemented account API |
| `predictions` | Feature JSONB, class, score, model version and timestamp; nullable legacy patient-reference column |
| Threshold provenance | Threshold is returned, not stored as a prediction-table column; preserve the versioned artifact |
| Public history | Not implemented or exposed |
| Expected errors | 422 invalid input; 503 unavailable model/database; generic 500 unexpected error |

The frontend prevents concurrent duplicate submission clicks but there is no server-side idempotency key. A commit may succeed before a response is lost; automatic POST retries are absent.

## 8. Verification and cautions

This report run passed **127 selected backend tests**, **27 frontend tests**, backend/frontend lint, explicit TypeScript checking, a production build and the active-model audit. Three HTTP artifact cases were deselected; the full HTTP/database integration suite was not run. The read-only database probe failed, so live schema state is not freshly verified.

Earlier browser evidence records a real 201/save and responsive/control checks, but those checks were not rerun for documentation. Physical touch remains unverified. There is no independent clinical validation, subgroup fairness evaluation, established personal-risk calibration, retention workflow or production security certification. The configured database login is `postgres`; its live privileges were not checked. No credentials are reproduced here.

For complete limitations, equations and the 20 primary-source references, see [project-report.md](project-report.md). For diagrams and transaction boundaries, see [architecture.md](architecture.md). Machine-readable evidence is supplied beside these documents.
