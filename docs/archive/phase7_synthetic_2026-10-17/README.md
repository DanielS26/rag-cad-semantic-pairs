# Phase 7 synthetic end-to-end run, 2026-10-17

These files have no scientific meaning. They show that the Phase 7 commands run from start to
finish; none of the numbers in them is a result of the project.

## What was run

1. A synthetic Phase 4 root, made with `m0 fake-run` on the synthetic CAD release archives of the
   tests (18 D0 rows, 12 released-test rows, fake encoder, fake identity).
2. A synthetic family artefact, made with `features fake-build-families` on the 800 family records
   (fake encoder, both modes, 704 rows per pool, the same fake identity).
3. `training run-folds` with the torch trainer on CPU, every condition, seed 0, all five rounds of
   folds_v1, 3 epochs (the real run uses 30), `--threads 6`: 17 cells (N0, M0, and M1 to M3 in five rounds each),
   all completed, exit 0. A second run into the same output skipped all 17 cells; a second run into
   a fresh output gave byte-identical prediction files.
4. `evaluation fold-tables` on that output with bow_baseline_v1.json, exit 0.

Regenerated on 2026-10-17 after the review of PR #67, at commit
daf261875a918929b0f844e0a2b0012aae8ceea4, with configuration fingerprint
06f2a0b14629c61a1172e9493e52a4a124c8cf1247f678b765349727c889a514 (the first version was
f2780d6d...). The predictions now carry logit margins, and the paired share compares margins and
counts an exact tie as one half; this moved the synthetic paired share of M0 from 0.545 to 0.550 and
of M3 from 0.480 to 0.485, where float32 probabilities had tied. The tables gained the tie column,
the planned seeds, the commit and the thread count.

The released checkpoint scored for N0 is the real pinned file, applied to fake features.

## Files

- `driver_report.json`: the driver's report: seconds per cell (train, predict, total).
- `fold_tables.json` and `fold_tables.md`: the table builder's output.
- `timing_benchmark.json`: one 30-epoch fit at the real size (25,799 rows of 2,048 random values) on
  the laptop CPU, plus the time to load the real caches (read only, no training). These two figures
  are the basis of the real-run estimate in docs/PHASE7_TRAINING_PLAN.md.

## Figures

- Synthetic cells: 17, 0.36 s per cell on average (about 1.2 s for M0, about 0.3 s for each M1 to
  M3 cell), 6.7 s for the whole run. These are small because the synthetic D0 has 18 rows.
- Real size: 58.5 s for a 30-epoch fit of 25,799 rows (1.95 s per epoch, 6 threads), 0.05 s to
  score the held-out and released-test rows, 3.0 s to load the two real caches.
- The released-test minus_near rows are 0 here because the synthetic test texts copy the synthetic
  training texts; the full-set rows are reported beside them.
