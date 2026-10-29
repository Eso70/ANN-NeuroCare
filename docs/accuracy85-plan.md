# User-requested 85% accuracy operating point — 29 October 2026

The user explicitly revised the objective to at least 85% overall accuracy. Previous
experiments prioritized approximately 83% recall and therefore used much lower cutoffs.
Changing that objective can improve measured accuracy while missing more positives.
Do not describe a cutoff change as improved learned discrimination or clinical validity.

Primary candidate: the already trained BRFSS 2021 transfer ANN
`20261028T222429Z-e5a45f4d`. No further weight/hyperparameter search is planned.
Select the cutoff on its validation partition only: highest recall subject to at
least 85.5% validation accuracy (a 0.5-point buffer above the requested target).
If that floor is infeasible, check 85% on validation before any test evaluation;
if even 85% is infeasible, report that limitation instead of inventing a result.
Validation found 85.5% infeasible and 85% feasible. For this fallback, use the maximum
validation-accuracy cutoff (ties favor recall) to give the requested overall-accuracy
objective the strongest validation result. This choice was made before evaluating
the new cutoff on test rows. Report the resulting additional recall loss explicitly.
Freeze the chosen cutoff before computing test metrics. Never adjust it from test
results. Evaluate the original cutoff, the new cutoff and the majority-only baseline
on identical test rows, reporting recall, precision, specificity, AUC and confusion
counts as well as accuracy.

These partitions have been evaluated previously. This is a user-requested policy
comparison, not a fresh independent test or a new model-training improvement. Report
that limitation and any recall loss explicitly. Configure a separate artifact only
if its measured test accuracy reaches 85%, beats the majority-only baseline and
still detects positive cases. Preserve all existing weights/artifacts and prediction
records. Before serving a 2021 artifact, update the public contract/source-year copy
and show its accuracy-prioritizing cutoff policy. Keep the design and database intact.
