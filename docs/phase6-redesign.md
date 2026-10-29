# Phase 6 visual redesign and verification

Date: 2026-10-28. Implemented in the existing NeuroCare workspace.

## Design and structure

A new warm-ivory, evergreen and muted botanical identity replaces the previous
composition. Palatino/Georgia display text pairs with the system Segoe UI family;
no external font download or animation framework was added. Lightweight original
SVG linework is decorative and explicitly does not represent learned weights.
The homepage has a short introduction, three unboxed steps, a brief model section,
verified project facts and a final invitation. `/model` holds methodology, real saved
evaluation, dataset sources and progressive detail. `/about` holds project information,
FAQs and collapsed live local-service checks. Public navigation has Home, How it works,
The model, About and one prediction action. No authentication or history endpoint was added.

## Shared components and form

`components/ui` now contains Button/ButtonLink/LoadingButton, Input, Select,
RadioGroup, FormField/FormSection/FieldHint/FieldError, ProgressIndicator, Accordion
and SectionContainer. Navigation, SurveyField, SurveyReview and PredictionResult use
the shared system. Design tokens and responsive rules are split into
`styles/tokens.css`, `site.css` and `forms.css`.

The form has four input groups (Background 4, Health 8, Daily life 5, Wellbeing 4)
and a review step. All 21 API field names, numeric types, bounds and source options
remain intact. Unknown future contract fields are retained in an additional group.
Values are controlled in memory across Back, Edit, failed submission and retry;
zero is a valid answer. Final submission validates every field and uses the existing
POST endpoint. Repeated requests are locked while pending and never retried automatically.
Reset clears the form and returns to the first input. No browser storage was added.

The dense metrics sidebar is removed. Results show the actual dataset label, sigmoid
score and returned classification cutoff in a neutral view. Saved ID/version and the
backend notice remain available in a disclosure. No clinical meaning is assigned.

## Dropdown and focus implementation

No maintained select primitive was installed or cached. Installing Radix from npm was
attempted and failed with ENOTFOUND for registry.npmjs.org; manifests and locks were
not changed by the failed install. The implementation therefore uses the browser's
Popover API for top-layer presentation and light dismissal, with an ARIA select-only
combobox/listbox, styled options and a fixed-position fallback for older browsers.
It never opens a native HTML select menu. Arrow/Home/End/Page keys, prefix typeahead,
Enter/Space selection, Escape cancellation, Tab commit, outside dismissal and viewport
clamping are implemented. Typeahead normalizes Arabic and Persian digits to Latin
digits for matching only; submitted source codes are unchanged. The active local
keyboard emitted Arabic digits, which exposed and verified this fix. Binary source fields use styled native radio inputs so native
radio keyboard behavior remains available. Numeric controls have a consistent appearance.

Keyboard focus uses one 2px outline and offset from the token file, without added focus
border changes or ring shadows. The visually hidden radio delegates its outline to its
visible label. Focus is retained for invalid fields, step headings and results. Generic
submission errors now receive focus so mobile users can see failures below a long review.
Reduced-motion CSS disables transitions/animations and smooth scrolling.

References used during implementation:
- https://developer.mozilla.org/en-US/docs/Web/API/Popover_API/Using
- https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-select-only/

## Executed checks

| Check | Result |
| --- | --- |
| `npm run test --prefix frontend` | 17 passed, 0 failed |
| `npm run typecheck --prefix frontend` | Passed |
| `npm run lint --prefix frontend` | Passed, no warnings after fixing the effect dependency |
| `npm run build --prefix frontend` | Passed; CSS 33.50 kB, JS 306.77 kB before gzip |
| Blank first step | Required errors displayed; form stayed on step one |
| Desktop dropdown keyboard | Home, Down and Enter selected age 25–29; End/Enter selected final education/income categories |
| Dropdown dismissal | Escape preserved the committed selection; outside click closed the custom panel |
| Numeric typeahead | Active Arabic keyboard digit ٥ found 50–54; Tab committed the source category |
| Mobile custom menu | Styled panel stayed within a 390 × 844 viewport; selected state and scrollable options visible |
| Review/Edit | All 21 fictional answers displayed; editing Background retained selected values |
| Network failure | Browser-only Offline mode caused the actual POST to fail; review/answers retained, no automatic retry |
| Error-focus fix | Repeated offline failure brought its message into view on mobile |
| Loading | Browser 3G throttling exposed Running & saving and disabled editing/actions |
| Real prediction | Actual API returned saved record #2, label 0, score displayed 0.3%, cutoff 12.85%, model 20261027T204111Z-db7cb83c |
| Reset | Returned to step one; age, education and income empty |
| Responsive inspections | Home at 768 × 1024, 1280 × 800 and 1920 × 800, and prediction at 390 × 844; model introduction at tablet and mobile, mobile saved metrics/detail and About FAQ viewed |
| Saved metrics | Browser showed recall 82.9%, precision 28.0%, ROC AUC 0.825; matched local saved metadata |
| About FAQ | Direct /about#faq navigation and answers disclosure worked |
| Fresh console | About direct-load showed React development notice and no runtime error entries; existing CSP issue counter remained |
| Integrity | Root .env, prediction route, inference.py and model.keras SHA-256 unchanged from the pre-redesign baseline |

The actual POST response is returned only after the unchanged repository commits to
PostgreSQL. This pass observed that successful response; it did not independently read
record #2 through a fresh SQL session. The synthetic row was retained, not deleted.
Backend code was not changed, so the backend test suite was not rerun for Phase 6.
The one-command launcher scripts were not changed or restarted during this visual pass.

Screenshots are real browser captures in `phase6-home-desktop.png`,
`phase6-dropdown-mobile.png` and `phase6-result-mobile.png`. Inspected regions showed
no visible horizontal overflow. This was a representative visual pass, not an automated
full-page overflow assertion for every page and breakpoint. Earlier phase screenshots
are historical.

## Limitations

Native Chrome with responsive emulation was used, not physical iOS/Android hardware.
No screen-reader certification or cross-browser compatibility pass was performed;
the custom ARIA behavior and older-browser fallback still need those checks.
Unit tests cover select navigation/typeahead/position math and full survey serialization;
they do not replace assistive-technology testing.

Intentional offline requests and editing a hook dependency list during Vite hot refresh
produced expected network/HMR console messages. A fresh-page console check was performed
after restoring connectivity, as recorded above. The existing Chrome CSP issue remains unresolved;
no security policy was weakened. The build emitted Node's module.register deprecation
notice. No database service, schema, password or model training was changed.
