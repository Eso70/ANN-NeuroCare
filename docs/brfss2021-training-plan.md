# BRFSS 2021 experiment plan — 29 October 2026

The supplied `LLCP2021.XPT` was moved from the root to `data/raw/LLCP2021.XPT`.
It is 1,055,538,560 bytes, SHA-256
`ae7fea17e09740fd2bd306b217c58df42d86060eab85baf0d6af67e977a1eca2`.

Use explicit CDC 2021 recoding with all 21 supported inputs. Keep raw and old 2015 data.
Do not blindly concatenate years: 2021 income/insurance/questions changed, and source
descriptions of the original binary target conflict. Define the 2021 target explicitly:
DIABETE4 1 -> 1; 2/3/4 -> 0; unknown/refused excluded. Income is nominal 2021 USD,
with upper categories collapsed, not inflation-adjusted 2015 income.

Before fitting, quarantine 2021 profiles matching old validation/test profiles. Profiles
matching prior training may be used only for training. Fresh 2021 validation/test
profiles must have no identical input profile anywhere in the original dataset.
Assign novel 2021 profiles to grouped stratified 60/20/20 train/validation/test partitions.

Compare two predeclared candidates: a fresh 64/32 ANN, and fine-tuning the current 64/32
ANN on the new training rows. Fine-tuning transfers existing learned weights without
mixing uncertain old labels into the new training objective. Fit scaling only on new
training rows; adapt the transferred first layer algebraically so the new scaling
preserves the parent's initial function. Check that equivalence before fine-tuning.
Use early stopping and learning-rate reduction, at most 60 epochs. Choose the candidate
using validation accuracy at a recall floor set from the parent's measured 2021 validation
recall (minimum 80%). Select no configuration or cutoff from test results.

Freeze the winner before any fresh test evaluation. Compare original and validation-
adapted parent cutoffs plus the frozen winner on the same new test rows. Report recall,
precision, AUC, average precision, Brier and confusion counts alongside accuracy.
Promote only after integrity checks and if its observed fresh-test accuracy and recall
both exceed or equal the validation-adapted parent's, with strictly higher accuracy.
Otherwise retain the current model and report the outcome. No re-tuning after test.
The old 68.96% result is on a different cohort; do not present it as a direct before/after
comparison with new-year results. No database or prediction record may be altered.
