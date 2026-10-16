# Phase 8 synthetic end-to-end run, 2026-10-17

These files have no scientific meaning. They show that the retrieval harness runs from start to
finish on synthetic inputs. None of the numbers in them is a result of the project.

## What was run

1. The synthetic inputs of the Phase 7 synthetic run were reused: a synthetic Phase 4 root
   (`C:\p7\syn\src\phase4`, made with `m0 fake-run`: 18 D0 rows, 3 released-test records, fake
   encoder) and a synthetic family artefact (`C:\p7\syn\families`, made with
   `features fake-build-families` on the 800 family records, fake encoder).
2. A synthetic Phase 7 run was made with the fake trainer into the temporary path
   `C:\p8\syn\p7`: `training run-folds --trainer fake`, every condition, seeds 0 to 2, all five
   rounds. 49 cells, exit 0, about 6 s.
3. `rag harness-run` on that run into `C:\p8\syn\harness`, exit 0, 3.8 s, with
   `--distractor-set full`. The three synthetic test records are near duplicates of the synthetic
   training records, so the leak-excluded set is empty. A second run into a fresh output gave
   identical retrievals, Markdown and JSON (apart from the timing).

Made at commit 8d39534 on branch phase8-harness. The command lines are in
`docs/PHASE8_HARNESS_PLAN.md`. `C:\p8\syn` is a temporary folder and may be deleted.

## Files

- `harness.json` and `harness.md`: the harness output. The per-query `retrievals.jsonl` (about
  0.4 MB) is not archived.
- `harness_stdout.json`: the command's printed summary.
- `real_input_load_benchmark.json`: a read-only load of the real inputs (verify the 49 Phase 7
  cells, load the two caches, build the 800 family documents, draw the distractors, read one cell's
  predictions). No store, retrieval or gate was built on the real data. This file is the basis of
  the real-run estimate and of the distractor count (23 distinct benign remainders among the 241
  leak-excluded released-test records).

## Why the synthetic figures look as they do

The fake encoder's standalone sentence embeddings all point the same way, so every retrieved
cosine is 1.0 and the ranking falls back to store order. The hit rate at five (0.040) is therefore
meaningless. The fake trainer flags almost everything, so the trained
rows drop or strip nearly every document. No distractor was retrieved, so the distractor columns
read n/a. The tests score distractors through the same cell's released-test predictions directly.
