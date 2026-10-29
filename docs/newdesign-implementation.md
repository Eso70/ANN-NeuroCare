# New design implementation

Historical initial report. See [the completion checklist](newdesign-completion.md) and
[current live browser verification](newdesign-browser-verification.json) for the latest
changes and successful browser/prediction checks. The connectivity limits below describe
the earlier session and do not apply to the completed checks in the current report.

## Plan and reference research — 29 October 2026

Read `newdesign.md` in full and inspected the current React routes, shared controls,
form state/validation, API integration and model metadata presentation before editing.
Source/tests were archived under `.dev-logs/` because this workspace has no Git repository.

Inspected the live homepage, pricing, integrations, insights, catalog and enterprise
pages at https://rootly.com using both web retrieval and browser screenshots/DOM.

| Reference | Observed pattern | NeuroCare adaptation |
| --- | --- | --- |
| Homepage | Centered headline, compact header, large product framing, varied feature compositions | Original scientific hero and clear prediction/method actions |
| Pricing | Quiet type hierarchy, white bordered surfaces, violet actions and a dark emphasis surface | Shared controls and measured evaluation presentation; no pricing route |
| Integrations | Split heading/visual, category navigation, grouped content | Interactive explorer of actual supported survey fields |
| Insights | Split product hero and focused evaluation storytelling | Real saved metrics with explicit limitations |
| Catalog | Product UI framed beside explanation, feature selectors | Schema explorer and actual model architecture |
| Enterprise | Broad hero, alternating product sections, large closing invitation | Editorial project story and focused final action |

Browser-computed reference typography was PP Mori (not copied or redistributed),
with a 72px desktop navigation and restrained heading weights. NeuroCare uses the
locally available Georgia display face and Segoe UI interface stack; no external font
requests or proprietary assets are introduced. Reference screenshots also showed
cloud backgrounds; those are not reused. The original visual direction here remains
predominantly light, with restrained lavender and violet, strong ink and scientific diagrams.

The reference Product navigation did not open on the attempted click; no successful
desktop submenu interaction is claimed. Mobile DOM inspection showed a menu toggle.
Not every reference hover, animation or accordion state was inspected.

Implementation sequence: unify tokens and controls; rebuild homepage compositions and
schema/architecture visuals; align model/about/prediction/404 pages and shared navigation/
footer; validate contracts, focus, responsive layouts and real data; record executed checks.
Keep backend, database, environment, launcher and model artifacts unchanged for this redesign.

## Implemented changes

- Centralized lavender, ink and violet semantic tokens, type scale, spacing, surface,
  border, focus and motion values. System Georgia and Segoe UI need no font download.
- Rebuilt the homepage with a split scientific hero, SVG network structure drawn from
  the real model architecture, actual schema explorer, numbered workflow, framed real
  evaluation, project principles, stack context and a contrasting final invitation.
- Added `FeatureExplorer` with API-sourced field names/options/ranges, four source
  groups, ARIA tabs/panels and Arrow/Home/End keyboard handling. Unavailable schema
  stays explicitly unavailable. All tab panels have stable ID relationships.
- Updated shared branding/footer, methodology, About, prediction, result and not-found
  presentation. No pricing, integrations product, account flow, fake license or
  endorsements were introduced. Public source links remain genuine or configured.
- Retained the existing custom select, original 21-feature submission/validation,
  review/edit/back behavior, error retention and actual backend result rendering.
- Preserved one deliberate focus outline, reduced-motion handling and hidden
  scrollbar chrome without disabling scroll.
- Hash verification confirms `.env`, both launch scripts, backend inference and
  prediction route code, and the configured model file are unchanged by this redesign.

## Executed checks and limits

Final checks executed after the source changes:

- Frontend ESLint: passed.
- Explicit TypeScript check: passed.
- Frontend regression suite: **23 passed**, including lavender/accent contrast,
  survey validation, feature coverage, dropdown behavior and metric/cutoff presentation.
- Production build: passed; compiled CSS 43.11 kB, JS 318.70 kB (before gzip).
- Backend public-contract tests: **14 passed**, including the absence of public
  user/prediction history routes and agreement between backend fields and form codes.
- Protected-file hashes: unchanged for the environment, launcher scripts, backend
  prediction/inference code and configured model artifact.

The temporary Vite process started for this verification was stopped after the checks.
No unrelated service or PostgreSQL process was stopped.

Initial in-app browser access to the local preview failed (localhost connection refused;
the Vite-advertised IPv4 endpoint timed out). Native Chrome also showed a connection
timeout. The development server itself reported ready. These are connectivity limits,
not successful live UI checks.

An isolated offline review was generated with `scripts/design-review.mjs`. It bundles
the actual React pages/components and compiled CSS with a snapshot exported from the
public backend contract/model readers. That snapshot contains genuine saved metrics,
architecture and source categories, never patient data or invented model results.
The review has explicit offline labeling, responsive viewport buttons, and blocks
prediction writes and live-health requests. It lives only under ignored `.dev-logs/`;
the production application still uses its real API with no snapshot transport.

The user stopped computer use before the offline review could be opened. No new
NeuroCare visual screenshot, successful responsive browser sweep, custom-control
browser check, console check or live prediction/database save is claimed. Those checks
remain outstanding. The six reference-page desktop screenshots/DOM were inspected;
the reference mobile DOM was inspected, with the limitations recorded above.

To review the real application, run `.\scripts\dev.ps1 start` from a normal local
terminal and visit the Vite URL. Exercise all public navigation/anchors, the four schema
tabs, the complete prediction/review/result flow, keyboard select and focus behavior,
and mobile/tablet/desktop layouts. A successful build alone does not establish those
live behaviors. Backend/database setup, launcher and model training were not changed.
