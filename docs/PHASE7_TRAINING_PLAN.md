# Phase 7 training plan: heads over the folds from cached features

This plan carries out D-20261017-55. It trains the detector heads over the five family folds of
D-20261013-28 from the features already cached in Phases 4 and 6, and builds the result tables.
Everything runs on the laptop CPU. Nothing is re-encoded.

## Inputs

- The Phase 4 restored root:
  `C:\Users\songh\Desktop\Master of AI 2025\COMPSCI764\Project\drive-artefacts\phase4\restored\20261004T101405Z_d40b6a6a_m0_8c0933ce\`.
  It holds `features/identity.json`, the D0 training rows (`features/assembled/m0_base/train`,
  24,665 rows), the released CAD test rows (`features/assembled/common/test`, 9,776 rows) and the
  adapted records under `adapted/` that the leak exclusion reads. It is in repo_compatible only.
- The Phase 6 family artefact: `C:\p6\20261016T143145Z_86f6f7a3_features_e8058efb\`, with
  `features/<mode>/` per mode: the four pools under `shards/` (704 rows each) and the assembled
  m1_random, m2_keyword and m3_semantic sets (1,408 rows each).
- The fold table `datasets/raw/augmentation/folds_v1.jsonl`, the experiment values
  `configs/experiment.yaml`, the release pin `configs/upstream/cad_release.yaml` and the released
  checkpoint `datasets/raw/cad_release/classifier_fullcad.pt` (verified against its pinned hash
  before it is loaded).
- The bag-of-words baseline `datasets/raw/augmentation/review/bow_baseline_v1.json`, computed on
  the same fold table.

Both caches are only read. The driver refuses an output directory inside the repository or inside
either cache.

## Commands

`training run-folds` reads the two caches and first compares their identities on
representation_id, encoder revision, encoder code revision, segmenter and dtype, the fields
`features check-families` compares. If any differs, it writes `identity_refused_<time>.json` to the
output directory and stops before any row is read for training. Commit, configuration hash and
feature environment differ between the two caches by design and are only reported. It then joins
the family rows to the fold table by group_id. It does not use family_id, because the control
records carry family_id null.

It then runs one cell per condition, round and seed:

- N0: the released checkpoint, scored as it is. One cell; no training.
- M0: the head trained on the 24,665 D0 rows alone, once per seed. M0 holds no family data, so it is
  scored once on all 200 families, and each prediction records the family's fold.
- M1, M2 and M3: the head trained on D0 plus the round's 160 training families from the condition's
  assembled set. That set holds the shared malicious additions and the condition's own benign
  counterparts (random, keyword or semantic), selected through `rag_cad.data.conditions` as
  D-20261004-15 sets out. One cell per round and seed. A round adds 1,114 to 1,134 family rows.

Every cell is scored on the four record kinds (malicious, twin, random control, keyword control) of
its round's 40 held-out families, and on the released CAD test. Training reuses the existing
`TorchTrainer` on CPU with the fixed recipe (AdamW, cosine schedule, batch 64, class-balanced
loss, 30 epochs, threshold 0.5). Seeds are fixed, and the same CPU path is used everywhere. Phase 4
trained its M0 heads on the GPU; Phase 7 retrains M0 on CPU so that every trained condition uses
the same path.

Each cell writes one directory under `<output>/cells/`:
`n0_released/`, `m0_base/seed_<s>/` or `<condition>/round_<k>/seed_<s>/`. It holds:

- `model.pt`: the checkpoint, for trained cells;
- `heldout_rows.jsonl`: one row per sentence, with the probability of the malicious class and
  the logit margin (malicious-class logit minus benign-class logit, in float64);
- `heldout_records.jsonl`: one row per record, with the maximum sentence probability and margin,
  the target sentence probability and margin where there is one, and the role, attack category and
  cue position from the fold table;
- `released_test_rows.jsonl` and `released_test_metrics.json`: the released test, full and with the
  leaked records excluded, as `evaluation leak-excluded` computes it;
- `manifest.json`: written last, to a temporary file renamed into place. It records the identity
  check, the configuration and its fingerprint, the seed, the round, the row counts, the training
  history and the timings, and the hashes of every file in the cell.

A cell counts as complete when its manifest parses and every hash in it verifies. A rerun skips
complete cells and removes and redoes an incomplete one, including one whose manifest was cut short.
The configuration of an output is fixed by its first sitting: the recipe, mode, fold table, caches,
the pinned hash of the released checkpoint (recorded even when a sitting does not score N0), the
planned seed set, the code commit and the torch thread count. A later sitting that differs in any of
these is refused with the reason. The run can therefore be stopped and resumed, or split across
several sittings with `--conditions` and `--rounds`, from the same commit with the same `--threads`.
A test checks that two runs of one cell give byte-identical predictions.

`evaluation fold-tables` verifies every cell of a run. It pools the held-out records of the five
rounds per condition and seed. It refuses unless every family is scored exactly once per condition
and seed, every condition is present, M0 to M3 hold exactly the run's planned seeds, and all cells
come from one commit and one thread count. It writes a JSON file and a Markdown file with:

- the family table, record basis: twin false-alarm rate, random and keyword control false-alarm
  rates, malicious detection rate, the tie count and share, and the within-family paired share.
  Rows are, in order, the bag-of-words baseline, N0, M0, M1, M2 and M3, with the paired share as the
  last column. Each value is the mean over seeds, with the seed standard deviation and the standard
  deviation over the per-fold values; both are population standard deviations (ddof 0), and the
  fold one mixes seed and fold variation;
- the same five figures by attack category (bipia_adapted task-type, asb_adapted operational), by
  semantic role and by cue position;
- the target-sentence basis: twin false alarm, detection and paired share from the target sentence
  alone. The controls have no target sentence;
- the released CAD test table: N0, M0, each round of M1 to M3, and M1 to M3 over all rounds. It gives
  masked and all-rows average precision, true-positive rate and false-positive rate, minus_near
  beside the full set.

A record is flagged when any of its sentences scores strictly above 0.5, because that is what the
passage filter removes. This record basis is the primary table. The target basis is reported beside
it so the review can see whether the twin's cue sentence itself or other sentences drive the false
alarms.

The paired share is the share of families whose twin's margin is below its malicious partner's,
that is, the twin is scored more trustworthy. It is computed on the logit margin, not the
probability: the float32 softmax rounds to exactly 1.0 once the logit gap passes about 17, so
saturated twin and malicious records would tie, which the review observed with the released
checkpoint. An exact tie of margins counts one half (the convention of the area under the ROC curve); the
tie count and share are reported beside the paired share in every table, and the JSON also holds the
strict share, with ties counted as failures. The flags and rates still use the probability against
the 0.5 threshold.

The baseline row is computed with the same rules from the baseline's scored families: a twin it
calls malicious is a false alarm, a malicious record it calls malicious is a detection, and its
margin is its negated log-odds of the twin. It has no control columns. Its log-odds are stored to
four decimals, so a tie there may be a rounding tie (there are none in bow_baseline_v1).

## Cell list and estimated time

| condition | rounds | seeds | cells | training rows per cell |
|---|---|---|---|---|
| N0 | - | - | 1 | none |
| M0 | - | 0, 1, 2 | 3 | 24,665 |
| M1 random | 1 to 5 | 0, 1, 2 | 15 | 25,779 to 25,799 |
| M2 keyword | 1 to 5 | 0, 1, 2 | 15 | 25,779 to 25,799 |
| M3 semantic | 1 to 5 | 0, 1, 2 | 15 | 25,779 to 25,799 |

That is 49 cells, 48 of them trained. On the laptop CPU (6 torch threads), one 30-epoch fit of
25,799 rows took 58.5 s (1.95 s per epoch), and scoring the held-out and released-test rows took
0.05 s. Loading the two real caches took 3.0 s. The 48 trained cells should therefore take about
48 minutes; with file writing and checkpoint reloads, allow about one hour. The synthetic run, the
benchmark and the read-only load of the real caches are archived in
`docs/archive/phase7_synthetic_2026-10-17/`. The output takes about 4 MB per cell (checkpoint
2.2 MB, released-test rows about 1.5 MB), about 200 MB in all.

## Real-run command lines (laptop, after the review)

From the repository root, in Git Bash:

    PYTHONPATH=src ./.venv/Scripts/python -m rag_cad.cli training run-folds \
      --phase4-root "C:/Users/songh/Desktop/Master of AI 2025/COMPSCI764/Project/drive-artefacts/phase4/restored/20261004T101405Z_d40b6a6a_m0_8c0933ce" \
      --families C:/p6/20261016T143145Z_86f6f7a3_features_e8058efb \
      --mode repo_compatible \
      --threads 6 \
      --output C:/p7/repo_compatible \
      > C:/p7/repo_compatible_driver.json 2> C:/p7/repo_compatible_driver.log

    PYTHONPATH=src ./.venv/Scripts/python -m rag_cad.cli evaluation fold-tables \
      --run C:/p7/repo_compatible \
      --output C:/p7/repo_compatible_tables.json \
      --markdown C:/p7/repo_compatible_tables.md

Create `C:\p7\` first (`mkdir -p /c/p7`). The output stays under that short root, never in the
repository, because the cell paths are long. If the driver stops, the same first command resumes
it, from the same commit and with the same `--threads`. Exit code 0 means every planned cell is
complete; 2 means refused. The cause of a refusal is written to standard error, so to the log, as
"training run-folds refused: <class>: <reason>"; an identity refusal also writes
`identity_refused_*.json` into the output.

After the run, the tables and the driver report are copied to an archive folder. The real-run
artefacts (checkpoints and predictions) go to Drive or another backup as the Phase 4 artefact did.
The figures are then recorded in a decision entry.

**Done, 16 October 2026.** The real run was made on the laptop CPU from main
e857b9d7d958381afab2e34c0753f639812fe23a with the command lines above: started
2026-10-16T15:48:49Z, finished 16:36:28Z UTC (48 minutes), 49 cells planned and run, 48 trained,
0 skipped, exit 0, identity check matched, configuration fingerprint 65e8db5e1b54. A trained cell
took about 59 s (55.8 to 61.7 s), close to the 58.5 s estimate. The tables, the driver report and
log, run.json, leaked.json and each cell's manifest, record predictions and released-test metrics
are archived in `docs/archive/phase7_results_2026-10-17/`; checkpoints and per-row predictions
stay in `C:\p7\repo_compatible`.

## Open points for the review

- paper_exact: the Phase 4 root was encoded in repo_compatible only, so `--mode paper_exact` is
  refused at the identity check (the representation_id differs). A secondary paper_exact table would
  need D0 and the released test encoded in paper_exact, which is a GPU stage. The family artefact
  already holds paper_exact.
- The record basis as the primary family table, with the target basis beside it.
- The tie rule of the paired share (margins, a tie counts one half), to be recorded in a decision
  entry with the real tables.
- M0 is retrained on CPU instead of reusing the GPU-trained Phase 4 checkpoints.
