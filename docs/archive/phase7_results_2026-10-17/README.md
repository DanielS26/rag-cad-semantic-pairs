# Phase 7 fold training, repo_compatible, 2026-10-17

The real Phase 7 run: heads trained on the cached repo_compatible features over the five rounds of
folds_v1, scored on the held-out families and on the released CAD test.

## Run facts

- Command: `training run-folds --mode repo_compatible --threads 6` into `C:\p7\repo_compatible`,
  then `evaluation fold-tables` (commands in docs/PHASE7_TRAINING_PLAN.md)
- Commit: main e857b9d7d958381afab2e34c0753f639812fe23a
- Machine: laptop CPU, torch 2.10.0+cpu, 6 threads, torch trainer, 30 epochs, threshold 0.5,
  seeds 0, 1, 2
- Configuration fingerprint: 65e8db5e1b540cce41c84ec27ae2ff4e639702d41f78899fa76ca6552377bc89
- Inputs: Phase 4 root 20261004T101405Z_d40b6a6a_m0_8c0933ce (D0 24,665 rows, released test 9,776
  rows) and family artefact 20261016T143145Z_86f6f7a3_features_e8058efb (200 families, four pools of
  704 rows); identity check matched on representation, encoder and code revisions, segmenter and dtype
- Cells: 49 planned, 49 ran, 0 skipped: N0 (scored only), M0 for three seeds, and M1 random, M2
  keyword and M3 semantic for five rounds and three seeds each (48 trained cells); exit 0
- Wall-clock: started 2026-10-16T15:48:49Z, finished 16:36:28Z UTC, 48 minutes; about 59 s per
  trained cell (59.3 s mean, 55.8 to 61.7 s)

## Headline tables

Copied from `repo_compatible_tables.md`. Mean over seeds; ± is the seed spread, (f ...) the fold
spread. A record is flagged when any sentence's probability is above the threshold.

### Held-out families, pooled over rounds (record basis)

| row | twin FA | random FA | keyword FA | detection | ties (share) | paired share |
|---|---|---|---|---|---|---|
| BoW baseline | 0.190 (f 0.056) | n/a | n/a | 0.775 (f 0.052) | 0 (0.000) | 0.905 (f 0.024) |
| N0 released | 0.515 (f 0.051) | 0.595 (f 0.078) | 0.460 (f 0.025) | 0.660 (f 0.051) | 0 (0.000) | 0.595 (f 0.056) |
| M0 base | 0.542 ± 0.009 (f 0.044) | 0.597 ± 0.042 (f 0.084) | 0.475 ± 0.029 (f 0.039) | 0.677 ± 0.026 (f 0.060) | 0 (0.000) | 0.603 ± 0.013 (f 0.043) |
| M1 random | 0.935 ± 0.011 (f 0.056) | 0.022 ± 0.006 (f 0.026) | 0.058 ± 0.012 (f 0.051) | 0.947 ± 0.006 (f 0.048) | 0 (0.000) | 0.547 ± 0.017 (f 0.052) |
| M2 keyword | 0.943 ± 0.002 (f 0.035) | 0.040 ± 0.008 (f 0.030) | 0.028 ± 0.006 (f 0.034) | 0.965 ± 0.015 (f 0.030) | 0 (0.000) | 0.575 ± 0.023 (f 0.051) |
| M3 semantic | 0.485 ± 0.012 (f 0.072) | 0.037 ± 0.002 (f 0.037) | 0.013 ± 0.002 (f 0.018) | 0.750 ± 0.011 (f 0.083) | 0 (0.000) | 0.842 ± 0.012 (f 0.036) |

### Held-out families, target sentence basis (twin and malicious only)

| row | twin FA | detection | ties (share) | paired share |
|---|---|---|---|---|
| N0 released | 0.345 (f 0.043) | 0.340 (f 0.034) | 0 (0.000) | 0.530 (f 0.081) |
| M0 base | 0.370 ± 0.007 (f 0.053) | 0.372 ± 0.010 (f 0.058) | 0 (0.000) | 0.495 ± 0.018 (f 0.057) |
| M1 random | 0.923 ± 0.009 (f 0.061) | 0.947 ± 0.006 (f 0.048) | 0 (0.000) | 0.560 ± 0.015 (f 0.045) |
| M2 keyword | 0.935 ± 0.004 (f 0.042) | 0.963 ± 0.015 (f 0.033) | 0 (0.000) | 0.585 ± 0.023 (f 0.054) |
| M3 semantic | 0.465 ± 0.008 (f 0.068) | 0.750 ± 0.011 (f 0.083) | 0 (0.000) | 0.870 ± 0.011 (f 0.032) |

### Released CAD test (strict threshold)

minus_near removes test records whose malicious sentences are verbatim or near duplicates of D0
training sentences.

| row | set | rows | masked AP | masked TPR | all-rows AP | all-rows TPR | all-rows FPR |
|---|---|---|---|---|---|---|---|
| n0_released | minus_near | 4391 | 0.995 | 0.963 | 0.871 | 0.352 | 0.000 |
| n0_released | full | 9776 | 0.981 | 0.981 | 0.829 | 0.371 | 0.001 |
| m0_base | minus_near | 4391 | 0.996 ± 0.001 | 0.951 ± 0.019 | 0.854 ± 0.005 | 0.350 ± 0.003 | 0.000 ± 0.000 |
| m0_base | full | 9776 | 0.988 ± 0.007 | 0.975 ± 0.010 | 0.808 ± 0.001 | 0.370 ± 0.002 | 0.001 ± 0.000 |
| m1_random/all_rounds | minus_near | 4391 | 0.997 ± 0.001 | 1.000 ± 0.001 | 0.903 ± 0.016 | 0.524 ± 0.049 | 0.008 ± 0.006 |
| m1_random/all_rounds | full | 9776 | 0.985 ± 0.001 | 0.998 ± 0.005 | 0.864 ± 0.018 | 0.534 ± 0.048 | 0.007 ± 0.004 |
| m2_keyword/all_rounds | minus_near | 4391 | 0.997 ± 0.000 | 1.000 ± 0.000 | 0.895 ± 0.018 | 0.555 ± 0.035 | 0.009 ± 0.007 |
| m2_keyword/all_rounds | full | 9776 | 0.985 ± 0.001 | 1.000 ± 0.000 | 0.853 ± 0.019 | 0.568 ± 0.035 | 0.007 ± 0.004 |
| m3_semantic/all_rounds | minus_near | 4391 | 0.998 ± 0.002 | 0.923 ± 0.039 | 0.892 ± 0.017 | 0.295 ± 0.050 | 0.001 ± 0.001 |
| m3_semantic/all_rounds | full | 9776 | 0.998 ± 0.001 | 0.960 ± 0.021 | 0.844 ± 0.021 | 0.312 ± 0.048 | 0.002 ± 0.000 |

The per-role, per-category and per-cue-position slices and the per-round released-test rows are in
`repo_compatible_tables.md`.

## Files

- `repo_compatible_tables.md` and `repo_compatible_tables.json`: the table builder's output.
- `repo_compatible_driver.json` and `repo_compatible_driver.log`: the driver's report (seconds per
  cell) and its standard-error log.
- `run.json`: the run configuration, cache digests, identity check and provenance.
- `leaked.json`: the released-test records excluded as verbatim or near duplicates of D0 training
  sentences (threshold 0.8).
- `reports/run_20261016T163624900484Z.json`: the run report.
- `cells/<cell>/manifest.json`, `heldout_records.jsonl` (per-record predictions on the held-out
  families, all four record kinds) and `released_test_metrics.json` for each of the 49 cells.

Left out (about 199 MB, kept in `C:\p7\repo_compatible` and for backup): the 48 checkpoints
`model.pt` (2.2 MB each), the per-row predictions `heldout_rows.jsonl` (0.16 to 0.8 MB each, 10.5 MB
in all) and `released_test_rows.jsonl` (about 1.65 MB each, 81 MB in all). Their SHA-256 values are
in each cell's manifest.
