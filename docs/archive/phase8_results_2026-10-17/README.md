# Phase 8 retrieval harness, repo_compatible, 2026-10-17

The real Phase 8 run: the Phase 7 heads used as a document gate and as a sentence filter in a
retrieval pipeline over the held-out families of each round of folds_v1.

## Run facts

- Command: `rag harness-run --mode repo_compatible` into `C:\p8\repo_compatible` (command line in
  docs/PHASE8_HARNESS_PLAN.md); exit 0, 9.05 s; standard error empty
- Commit: main cfd34d8296491505f6680589ffd7256f9d9f7a51 (after PR #69)
- Inputs: Phase 4 root 20261004T101405Z_d40b6a6a_m0_8c0933ce, family artefact
  20261016T143145Z_86f6f7a3_features_e8058efb, Phase 7 run `C:\p7\repo_compatible` (49 cells, commit
  e857b9d, configuration fingerprint 65e8db5e1b54), folds_v1 and bow_baseline_v1; identity check
  matched on representation, encoder, code, segmenter and dtype
- Settings: rounds 1 to 5, top 5, threshold 0.5, five query sentences, distractors from minus_near
  with seed 764 (160 requested)
- Store per round: 216 documents, the 160 records of the 40 held-out families plus 56 distractor
  passages (at most five sentences each, 228 sentences) cut from the 23 distinct benign remainders
  available among the 241 leak-excluded released-test records
- Retrieval (identical for every row, 800 queries, 4,000 slots): hit@5 0.771, mean rank 11.55;
  with the own record's sentences masked hit@5 0.241, mean rank 46.18; own-match share 0.262; no
  centroid fallback. These figures describe the TF-IDF query proxy, not retriever quality
- Slots: malicious 957, twin 1,246, random control 653, keyword control 797, distractor 347 (over
  41 of 56 passages)

## Headline tables

Copied from `harness.md`. Pooled over rounds per seed, mean over seeds; ± is the seed spread.

### Document gate

| row | injected pass-through | twin loss | random loss | keyword loss | family context survival | context survival (all slots) | distractor loss | distractor context |
|---|---|---|---|---|---|---|---|---|
| no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| BoW baseline | 0.270 | 0.185 | 0.000 | 0.000 | 0.779 | 0.802 | 0.000 | 1.000 |
| N0 released | 0.321 | 0.492 | 0.593 | 0.507 | 0.427 | 0.483 | 0.049 | 0.955 |
| M0 base | 0.292 ± 0.019 | 0.513 ± 0.011 | 0.598 ± 0.028 | 0.517 ± 0.026 | 0.410 ± 0.018 | 0.468 ± 0.016 | 0.049 ± 0.000 | 0.955 ± 0.000 |
| M1 random | 0.071 ± 0.006 | 0.945 ± 0.010 | 0.023 ± 0.010 | 0.054 ± 0.018 | 0.436 ± 0.005 | 0.489 ± 0.003 | 0.073 ± 0.014 | 0.936 ± 0.012 |
| M2 keyword | 0.053 ± 0.020 | 0.935 ± 0.008 | 0.042 ± 0.001 | 0.032 ± 0.012 | 0.436 ± 0.005 | 0.488 ± 0.005 | 0.073 ± 0.006 | 0.935 ± 0.005 |
| M3 semantic | 0.275 ± 0.007 | 0.493 ± 0.005 | 0.042 ± 0.014 | 0.021 ± 0.008 | 0.643 ± 0.006 | 0.676 ± 0.005 | 0.051 ± 0.001 | 0.953 ± 0.002 |

### Sentence filter

| row | injected pass-through | twin loss | random loss | keyword loss | family context survival | context survival (all slots) | distractor loss | distractor context |
|---|---|---|---|---|---|---|---|---|
| no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| N0 released | 0.600 | 0.392 | 0.593 | 0.507 | 0.789 | 0.810 | 0.049 | 0.989 |
| M0 base | 0.567 ± 0.015 | 0.421 ± 0.014 | 0.598 ± 0.028 | 0.517 ± 0.026 | 0.779 ± 0.013 | 0.801 ± 0.012 | 0.049 ± 0.000 | 0.989 ± 0.000 |
| M1 random | 0.071 ± 0.006 | 0.943 ± 0.009 | 0.023 ± 0.010 | 0.054 ± 0.018 | 0.897 ± 0.002 | 0.906 ± 0.002 | 0.073 ± 0.014 | 0.982 ± 0.005 |
| M2 keyword | 0.055 ± 0.022 | 0.934 ± 0.009 | 0.042 ± 0.001 | 0.032 ± 0.012 | 0.900 ± 0.001 | 0.909 ± 0.001 | 0.073 ± 0.006 | 0.981 ± 0.004 |
| M3 semantic | 0.275 ± 0.007 | 0.487 ± 0.006 | 0.042 ± 0.014 | 0.021 ± 0.008 | 0.947 ± 0.002 | 0.952 ± 0.001 | 0.051 ± 0.001 | 0.988 ± 0.000 |

The bag-of-words baseline scores twin and malicious records only, so its control and distractor
loss are zero by construction. The by-role and by-cue-position slices and the per-round retrieval
table are in `harness.md`; the definitions are at its end.

## Files

- `harness.md` and `harness.json`: the harness tables and the full report (settings, inputs and
  their digests, identity check, distractor draw, stores, retrieval, every row and slice).
- `retrievals.jsonl`: the top five of every query in every round (0.45 MB).
- `repo_compatible_harness.json` and `repo_compatible_harness.log`: the command's standard output
  summary and its standard error (empty).

Nothing was left out.
