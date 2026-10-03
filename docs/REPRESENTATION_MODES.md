# Representation Mode Evidence (D-20260921-05)

Status: decided on 4 October 2026 (D-20261004-13): repo_compatible is the
primary mode and paper_exact a documented secondary variant. This page collects
the measurements needed for the decision and the options for making it.

## Why two modes exist

The CAD scorer turns each sentence into 2048 numbers: 1024 for the sentence on
its own (the isolated block) and 1024 for how the query-plus-passage embedding
changes when the sentence is removed (the contextual block). The paper
describes the contextual block as embed(query + passage) minus embed(query +
passage without the sentence). The authors' repository pools only the tokens
outside the target sentence in the first term. The two readings are
implemented as `paper_exact` and `repo_compatible` in
`src/rag_cad/cad/representation.py` (handoff Section 5.5). The released
checkpoint does not record which reading produced its training features.

## Measured on 22 September 2026 (Run A from commit 0cc9ad77)

Real Jina encoder (weights ab036b02, code bd55a5ec), NVIDIA L4, Python
3.13.15, released checkpoint `classifier_fullcad.pt` (SHA-256 56c939b3...),
query "Summarise the synthetic passage." and the three synthetic smoke
sentences "Synthetic context.", "A synthetic target." and "Synthetic
conclusion.". Source: `run_a.json`, key `representation_modes`, in artefact
`smoke/20260922T143040Z_0cc9ad77_smoke_5bd0f99b` (manifest SHA-256
8d68633803262f0f0490d96bbaf53cb7125ad99e3c638cc2d617b3ab0f247140).

| Measurement | repo_compatible | paper_exact |
|---|---|---|
| Feature shape | [3, 2048] | [3, 2048] |
| Finite and deterministic (atol 1e-6, rtol 1e-5) | yes | yes |
| Encoding time for the sample | 0.265 s | 0.264 s |
| p(malicious) for "Synthetic context." | 3.0e-11 | 2.7e-11 |
| p(malicious) for "A synthetic target." | 0.437 | 0.569 |
| p(malicious) for "Synthetic conclusion." | 7.0e-08 | 5.8e-08 |
| Sentences removed at threshold 0.5 | none | "A synthetic target." |

Isolated blocks identical across modes: yes. Largest absolute difference in
the contextual block: 0.111. Released-checkpoint removal decisions agree: no.

## What this shows and does not show

- Both modes run correctly on the real encoder: correct shape, finite values,
  deterministic, and the same cost.
- The modes differ enough to change the released checkpoint's decision on a
  borderline sentence (0.437 against 0.569 around the 0.5 threshold), while
  agreeing on the two clearly benign sentences.
- The sample is synthetic, so neither decision is "correct". The result does
  not identify which mode trained the released checkpoint. The Run A from
  a822b9a0 on 21 September (repo_compatible only) gave the same 0.437.

## No published sentence-level oracle (checked 23 September 2026)

The paper (arXiv 2608.05430v1), the CAD-models model card and the CAD-data
dataset card were searched for any sentence-level detector metric for the base
CAD classifier. None exists. The paper reports agent-level clean utility,
utility under attack and attack success rate on AgentDojo and AgentDyn, with
seed statistics in its appendix; the cards give file descriptions and counts
only. The pinned upstream evaluator (`src/detector/train_and_eval.py`)
computes AUPRC, ROC-AUC and TPR/FPR at threshold 0.5 on boundary-masked test
rows (an injection row is dropped unless it lies within [start + 3, end - 5]),
but no expected values were published. "Reproduce the paper's number" is
therefore not an available decision method.

Fidelity check of the upstream code (`src/detector/defense.py`,
`src/detector/variants.py`): the authors' embedder joins the query and the
sentences with single spaces, pools the mean over tokens that are both kept
and attended (falling back to the plain mean), and truncates inputs at 8,192
tokens. The project's `repo_compatible` mode matches it exactly, except that
over-length inputs are refused and reported rather than silently truncated.

## Revised empirical test: which mode does the released checkpoint fit?

The released checkpoint was trained on features from one recipe, so its
quality on the released test set should be clearly better under that recipe.
The `released-test` conformance stage scores every sentence of
`testing_data_original` (389 records, 9,776 rows) with the released checkpoint
under both modes and reports, per mode: AUPRC, ROC-AUC, TPR, FPR, precision,
recall and F1 at 0.5 under both the upstream ">=" rule and the deployed ">"
rule, on all rows, on the upstream-masked rows and per domain; plus the
decision agreement rate between modes and which mode has the higher masked
AUPRC. It records timings, token lengths, skipped over-length records and peak
GPU memory, publishes per-row predictions, and selects no mode. A large gap
identifies the training recipe. A small gap means the checkpoint is
insensitive to the choice, and the decision can then rest on option 3 below.
The stage runs under the candidate profile (conformance is a smoke-class
stage). A ten-record pilot precedes any full run so that the cost is measured
rather than guessed, and each run needs its own explicit authorisation.

## Ten-record pilot (23 September 2026, commit f4181bc8)

Run ID 20260923T060056Z_f4181bc8_released-test-pilot_5bd0f99b: the released
checkpoint on the first ten records in the upstream sorted-path order (which
puts the banking suite first), 180 rows, 99 malicious, 80 of them masked out
by the upstream boundary rule, threshold 0.5.

| Rows | Metric | repo_compatible | paper_exact |
|---|---|---:|---:|
| all 180 | AUPRC | 0.8908 | 0.8910 |
| all 180 | ROC-AUC | 0.8662 | 0.8666 |
| all 180 | TPR / FPR at 0.5 | 0.394 / 0.0 | 0.394 / 0.0 |
| masked 100 | AUPRC | 1.0 | 1.0 |
| masked 100 | ROC-AUC | 1.0 | 1.0 |
| masked 100 | TPR / FPR at 0.5 | 1.0 / 0.0 | 1.0 / 0.0 |

Decision agreement between the modes: 1.0 on all 180 rows. Neither mode has
the higher masked AUPRC. Encoding took 14.6 s per mode (6.2 rows/s over both
modes, 39.5 ms per encoder pass); maximum token length 338; no over-length
records; peak GPU memory 2.33 GB; 9 minutes and 0.07 units in total.

What this shows: on these ten records the released checkpoint is equally good
under both recipes, and both detect every masked malicious sentence. The
all-row differences are in the fourth decimal place. The pilot therefore
predicts that the full run will land in the "small gap" case above, where the
decision rests on the argument from provenance (option 3) and any author
answer. The full run is still worth its measured cost (22 to 35 minutes)
because it gives the reference numbers on the whole released test set, per
suite, and the decision agreement rate over all 9,776 rows.

Two corrections came out of the pilot. The domain of every row had been
recorded as the archive folder name; it is now the first directory under that
folder, as the upstream evaluator defines it. And because the two modes share
every encoder pass, the stage now computes both from one set of passes, which
halves the encoder cost of the full run.

## Full released-test run (23 September 2026 UTC, commit d0b92eeb)

Run ID 20260923T080927Z_d0b92eeb_released-test-full_5bd0f99b: the released
checkpoint on all 389 records (9,776 rows, 3,729 malicious, 3,112 of them
masked out by the upstream boundary rule), threshold 0.5, the ">=" and ">"
rules identical throughout.

| Rows | Metric | repo_compatible | paper_exact |
|---|---|---:|---:|
| masked 6,664 | AUPRC | 0.98131 | 0.98161 |
| masked 6,664 | ROC-AUC | 0.99906 | 0.99907 |
| masked 6,664 | TP / FN / FP at 0.5 | 605 / 12 / 9 | 606 / 11 / 9 |
| all 9,776 | AUPRC | 0.8291 | 0.8303 |
| all 9,776 | ROC-AUC | 0.8842 | 0.8853 |
| all 9,776 | TP / FN / FP at 0.5 | 1,383 / 2,346 / 9 | 1,384 / 2,345 / 9 |
| banking, masked 4,403 | AUPRC; TP of 272; FP | 0.9664; 272; 9 | 0.9667; 272; 9 |
| slack, masked 390 | AUPRC; TP of 105; FP | 1.0; 100; 0 | 1.0; 102; 0 |
| travel, masked 1,871 | AUPRC; TP of 240; FP | 1.0; 233; 0 | 1.0; 232; 0 |

Decision agreement between the modes: 0.99969, three rows of 9,776. The
report names paper_exact as the higher masked AUPRC, by 0.0003, one row's
worth. Cost: 19,941 encoder passes in 823.6 s (41.3 ms per pass, 11.9 rows/s
over both modes); maximum token length 529; no over-length records; peak GPU
memory 2.35 GB; 13.7 minutes for the stage, and about 25 minutes and 0.12
units for the notebook in total as reported, including a first attempt that
failed at the environment preflight.

What this shows. The released checkpoint fits both recipes equally: one
detection and three decisions differ over the whole released test set. This
is what the arithmetic of the recipes predicts. The first contextual term is
the mean over the passage's tokens; paper_exact includes the sentence's own
tokens in that mean and repo_compatible excludes them, so the two differ by
the sentence's share of the passage times the gap between its tokens and the
rest. With about 25 sentences per record that share is a few per cent, which
is why the three-sentence smoke sample showed the largest differences (0.111
in feature space, a flipped borderline decision) and the full set shows
almost none. The fit test is in its "small gap" case: it cannot identify the
training recipe, and it shows that the choice has no measurable effect on
the released checkpoint's behaviour on the released test set.

These are also the project's reference numbers for the released checkpoint
on the released test set: masked AUPRC 0.981, ROC-AUC 0.999, TPR 0.98 and
FPR 0.0015 at 0.5. The paper reports no sentence-level figure to compare
them with.

## Options for deciding

1. Author answer. Ask which computation produced the paper's results (handoff
   Section 14, item 1; the question is on the list sent to the authors).
2. Empirical fit test, as described above: a ten-record pilot, then the full
   389-record run once its measured cost is approved.
3. Choice by argument. `repo_compatible` matches the released code and the
   checkpoint's origin; `paper_exact` matches the published description. The
   handoff notes that the released checkpoint makes `repo_compatible` the
   natural first compatibility test but not an automatic scientific choice.

Status after the full run: option 2 gave no separation. The decision,
recorded as D-20261004-13 on 4 October 2026, is option 3, repo_compatible:
it is the computation the released code performs, so it is the most likely
origin of the released checkpoint and of the paper's agent-level results,
and the fit test shows the released checkpoint behaves the same under either
recipe at realistic passage lengths. paper_exact stays implemented as a
documented secondary variant. An author answer (option 1) can still
supersede the entry.

Whichever mode is chosen, D-20260922-12 requires the smoke gate to be rerun in
that mode before final feature builds, and the choice must be recorded as a
decision before `representation` in `configs/experiment.yaml` is set.
