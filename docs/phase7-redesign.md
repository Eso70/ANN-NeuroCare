# Phase 7 — NeuroCare product website

Implemented 2026-10-28 in the existing local project.

## Direction and reference

Studied the current https://rootly.com/ homepage content, desktop/mobile hero and
navigation, plus its product-story sections. The reference informed a confident
headline, primary/secondary actions, one product focal point, consistent centered
widths and a progressive explanation. NeuroCare uses original teal/mint branding,
a new network monogram, system sans-serif typography and an original schematic of
its own ANN. No Rootly text, logos, screenshots, artwork or proprietary assets were
copied. No new animation, font or UI dependencies were installed.

The botanical-led editorial composition was replaced. Home now explains the actual
workflow, architecture, historical dataset, measured tradeoffs and limitations.
A dark final invitation contrasts with the clean light page. Model, About, prediction,
review, results, errors and 404 share the same typography and controls. The prediction
introduction is smaller and aligned with the form, with no metrics sidebar.

## Components and behavior

Created ModelDiagram, MetricDisplay and SiteFooter. Refactored LandingSections,
Dashboard, SiteElements/Brand, AppLayout, model/About copy and the prediction/result
presentation. Reused Navigation, Button/ButtonLink/LoadingButton, SectionContainer,
Input, Select, RadioGroup, FormField, FormSection, field hints/errors, progress,
SurveyReview and Accordion. Design tokens define colors, type, widths, spacing,
control height, borders/radii, shadows, motion and focus across three focused stylesheets.
The favicon and document metadata now match the identity.

The existing browser-Popover custom Select was retained: a styled top-layer panel,
ARIA combobox/listbox, arrow/Home/End/Page keys, Enter/Space, Escape, Tab, prefix
search and outside dismissal. Arabic/Persian digit matching remains supported.
Binary answers retain native radio semantics with custom visible choices; numeric
inputs retain bounds and types. Opened native select menus are never used.
The shared focus treatment is one 2px outline with offset; no focus-specific border
or ring shadow is layered on it. Hidden radios delegate the outline to their labels.
Reduced-motion rules disable animation, transitions and smooth scrolling.

Dropdown keyboard handling was strengthened: the active option scrolls only its own
panel, queued focus-scroll events do not close a stationary menu, and Home opens at
the first option. Responsive inspection also fixed an unbreakable FAQ heading at
320px and restored the word separator in the mobile hero when its line break is hidden.

The four input groups and review preserve all 21 original fields/codes. The POST URL,
validation, in-memory answer retention, submission lock and reset behavior remain.
No authentication, public history, database migration or new backend endpoint was added.

## Genuine information only

The 21 → 32 → 16 → 1 architecture and training-only scaling come from the implemented
ANN. The diagram is labeled schematic: no activation or learned-weight values are
invented. Historical CDC BRFSS 2015 provenance and the Diabetes_binary target come
from the contract and metadata. No patient examples or fabricated product dashboard
were placed on the website.

Homepage and methodology metrics come from GET /api/v1/model. Missing, non-finite or
out-of-range rate metrics show Unavailable. The homepage does not substitute saved
constants when the API is unavailable. Actual evaluation rendered during checks:
recall 82.9%, precision 28.0%, ROC AUC 0.825, model 20261027T204111Z-db7cb83c.
The detailed confusion matrix uses the real saved counts. Results are explicitly
historical-survey classifications, not clinical evidence or calibrated personal risk.
Repository/documentation URLs appear only when real HTTPS destinations are configured.

## Executed checks

| Check | Result |
| --- | --- |
| Frontend regression tests | 20 passed, 0 failed |
| TypeScript check | Passed |
| ESLint | Passed, no warnings |
| Production build | Passed; CSS 39.57 kB and JS 312.15 kB before gzip |
| Shared text contrast | Existing contrast test passed with the new palette |
| Server rendering against actual artifact | Evaluation values and all four matrix counts matched metadata |
| Missing and partial metadata | Honest unavailable states, no substitute metrics; valid zero preserved |
| Real backend contract rendering | 21 fields: 4 custom comboboxes, 14 radio groups, 3 numeric inputs |
| Internal URL checks | All rendered home/footer destinations mapped to existing routes/anchors |
| Browser desktop | New homepage, workflow anchor and form viewed at normal desktop size |
| Live homepage metrics | Browser displayed real API values matching the saved artifact |
| Blank form and focus | Required errors appeared; first missing input received focus |
| Keyboard controls | Home/End/arrows/Enter, prefix search/Tab, Escape and outside dismissal verified |
| Focus inspection | Focused combobox computed as one solid 2px outline with no shadow |
| Mobile dropdown | Panel fit inside 390 × 844 viewport, including when opened near the bottom |
| Back, Edit and review | Retained all 21 fictional answers, including both zero-day values |
| Failed POST | Browser-only offline request preserved answers and focused the visible error |
| Loading | Actual form showed Running & saving with submission disabled |
| Real POST | HTTP 201; saved record #4, label 0, displayed score 0.3%, cutoff 12.85% |
| Reset | Returned to step one with empty category controls |
| Responsive overflow | All 20 combinations of four routes and widths 320/390/768/1280/1920 passed after fixes |
| Missing live evaluation | Offline homepage showed no metric blocks; Retry recovered actual values |
| Mobile navigation | Open, route selection and Escape dismissal verified |
| Model details | Expanded matrix showed 29,343 / 14,667 / 1,178 / 5,713, with no mobile overflow |
| Other navigation | Model evaluation/dataset anchors, FAQ disclosure, live API/database service checks and 404 recovery verified |
| Fresh console | No warnings or errors on a fresh isolated homepage load after restoring network conditions |
| Integrity | Environment, prediction route, inference, model file and launcher hashes match their pre-change values |

`phase7-render-verification.json` records the server-rendered checks. These verify
HTML/data presentation, not browser layout or keyboard behavior. Backend code was
not modified, so backend tests were not rerun for this design pass.

`phase7-browser-verification.json` records executed browser checks. A separate review
session was used after the live Chrome form was seen changing during inspection;
the real POST above used only the explicitly constructed fictional test profile.
The successful backend response follows the unchanged repository's database commit.
The synthetic row was retained. No other visitor's history was fetched or exposed.

Actual browser evidence is saved in `phase7-home-preview.jpg`,
`phase7-home-mobile-viewport.jpg`, `phase7-dropdown-mobile.jpg`,
`phase7-review-mobile.jpg`, `phase7-error-mobile.jpg`,
`phase7-loading-mobile.jpg` and `phase7-result-mobile.jpg`.
The browser screenshot helper scaled some full-page captures; the two hero viewport
captures use the browser's raw screenshot command for accurate viewport dimensions.

## Operational limits

Command-line HTTP checks were attempted but the execution environment rejected
sockets with Windows error 10013. No password, database role, database schema,
PostgreSQL service or trained model was changed. The existing one-command launcher
was preserved and was not restarted during this pass. No unrelated database was used.
No records were read through a public history endpoint. Direct SQL readback was not
performed in this pass.

Browser responsive and prediction checks are recorded above. Real mobile
hardware, assistive-technology certification and other browser engines remain outside
this pass. Node emitted its non-failing module.register deprecation notice. The
previously observed Chrome CSP issue must be isolated before claiming a clean browser
security audit; no security policy was weakened.

Normal startup remains:

```powershell
.\scripts\dev.ps1 start
```
