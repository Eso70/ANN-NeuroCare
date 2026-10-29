# Restore the recall-focused educational policy - 29 October 2026

The user asked to fix the low-recall accuracy-first default. Restore the existing,
validation-selected 2021 parent operating point, without training or searching for
another cutoff. Parent: `20261028T222429Z-e5a45f4d`; cutoff: 0.132127583026886.

The parent's existing objective maximizes validation accuracy subject to its saved
83.253968% validation recall floor. Preserve that objective, cohort, splits,
preprocessing and weights. Save a separate version so original artifacts remain intact.

Recompute its saved validation and test metrics with the independent audit. These
are previously evaluated partitions, not new independent evidence. Do not adjust the
cutoff after inspecting the test results. No claim of improved learned discrimination.

For public 2021 inference require explicit recall-policy review, validation-only
selection, a saved validation recall floor of at least 80%, observed validation recall
meeting that floor, and observed test recall of at least 80%. The test requirement is
a deployment review check, not an optimization objective. This 80% guard is a project
policy, not a clinical standard, certification or future-performance guarantee.
Retire public support for accuracy-first variants; preserve them for offline inspection.

Expose accuracy, recall, precision, specificity, AUC and false-positive counts honestly.
Restore only MODEL_DIR in root .env after review and tests; preserve all other bytes.
Do not modify data, database records, launcher, model weights or the frontend design.
