# Phase 8 harness plan: the scorers as trust gates in a retrieval pipeline

This plan carries out D-20261017-58. It places each Phase 7 scorer as a trust gate between a fixed
retriever and the prompt and measures what the gate does to the retrieved context. No language
model is called, nothing is encoded and nothing is trained. Everything runs on the laptop CPU from
files that already exist.

## Inputs

All inputs are only read. The command refuses an output directory inside the repository or inside
any input, and an output directory that already exists.

- The Phase 4 restored root:
  `C:\Users\songh\Desktop\Master of AI 2025\COMPSCI764\Project\drive-artefacts\phase4\restored\20261004T101405Z_d40b6a6a_m0_8c0933ce\`.
  The harness reads the released CAD test rows (`features/assembled/common/test`) and the adapted
  test records (`adapted/cad_original_test.jsonl`) for the distractor texts.
- The Phase 6 family artefact: `C:\p6\20261016T143145Z_86f6f7a3_features_e8058efb\`, the four
  family pools in repo_compatible.
- The Phase 7 run: `C:\p7\repo_compatible\`. Every cell is verified by its file hashes, every
  condition must be present on the planned seeds, and `leaked.json` must match the hash the run
  recorded.
- The family records `datasets/raw/augmentation/families/` (queries, sentence texts and the cue
  sentences), the fold table `folds_v1.jsonl` (the hash the Phase 7 run recorded) and the
  bag-of-words baseline `bow_baseline_v1.json` (computed on the same fold table).

The two caches are read through the Phase 7 two-cache reader, so their identities are compared
first, as in Phase 7. The harness also checks that the caches are the ones the Phase 7 run used
(D0, released-test and family row digests). Every family record's content hash must equal the
hash stored with its cached rows, so the texts the harness reads are the texts that were encoded.

## Store

One store per fold round. It holds the 160 records of the round's 40 held-out families (all four
kinds of every family; the store refuses an incomplete family) and a fixed set of distractor
passages, the same in every round.

Each document is the mean of its sentence embeddings, scaled to unit length. A sentence embedding
is the first half of the cached CAD feature (columns 0 to 1,023): the sentence encoded alone and
mean-pooled. This half is the same in both representation modes. The second half describes the
sentence in its passage, so it is not an embedding of the sentence.

### Distractors: a change from the decision entry

D-20261017-58 asks for benign records from the leak-excluded released CAD test set, as many as the
round's family records (160). The released CAD test has no wholly benign record. Each of its 389
records carries an injected span. So the harness uses each record's benign remainder: its label-0
sentences in their original order, with the injected sentences removed.

The leak exclusion (minus_near, from `leaked.json`) removes 148 records and leaves 241. Many of
these records share one tool output and differ only in the injection, so their remainders are the
same text. Only 23 distinct remainders exist. The harness keeps one record per distinct remainder
(normalised text) and draws the set once with seed 764. With 23 available, all 23 are used. They
hold 1 to 36 sentences each, 228 in all. The JSON records the shortfall ("capped": true).

Family records hold two to five sentences, but the remainders run up to 36. Whole remainders acted
as retrieval hubs, and their many sentences dominated the all-slot context survival. So each
remainder is cut into passages of at most five consecutive sentences, as even in length as
possible (seven sentences become four and three; 36 become four of five and four of four). Each
passage is a store document that records its parent record. The 23 remainders give 56 passages
of 1 to 5 sentences, so each round's store holds 216 documents. The passages are the same in every
round. The JSON reports the passage count, the passage lengths, and which passages and parent
records take the most retrieved slots.

A distractor passage is scored by its parent record's predictions in the same cell's
`released_test_rows.jsonl`, which covers every released-test sentence. Those scores were computed with the injected sentence still in the passage,
because the cached passage context includes it. Clean-context scores would need a new GPU
encoding. Before gating, every cell must score every store document, retrieved or not; otherwise the run is
refused. The decision entry before the real run records this change.

## Retriever

The queries are the family records' own query fields: 160 per round, 800 in all.

No cache holds an embedding of a query. The CAD features encode the query only as a prefix of the
whole passage and keep no pooled query vector. The encoder is not called. So the harness places
each query in the embedding space through the store's own sentences:

1. The query text is matched against every store sentence by TF-IDF cosine. Terms come from the
   project's `normalise`, and the inverse document frequency is log((1 + n) / (1 + df)), so a term
   found in every sentence counts for nothing.
2. The query vector is the mean embedding of the five best-matching sentences (positive matches
   only), scaled to unit length.
3. A query that shares no term with any store sentence falls back to the store centroid. The count
   of such queries is reported.

This uses the query field, keeps the dense document representation of the decision entry, and
calls nothing. The query's own record's sentences are among the matched sentences: about a quarter
of them on average, by the review's count on the real caches. So hit@5 is partly by construction
and is not a measure of retriever quality. The harness therefore also reports the same placement
with the own record's sentences masked (hit@5 and mean rank), and the mean own-match share. The
masked placement is reported only and never used for gating. Retrieval is identical for every row,
so the gate comparisons do not depend on how good it is. The rejected alternative was to use each record's own document vector as its query:
it ignores the query field and makes the hit rate 1.0 by construction.

Retrieval is exact cosine search over the unit document vectors and returns the top five documents
per query. Ties are broken by store order (records sorted by id, then distractors). One retrieval
per round serves every row. Each row's table carries the digests of the retrievals it used, and the
tests check that these digests are the same for every row and gate. Retrieval facts per round and
pooled: hit rate at five of the query's own record, mean and median rank of that record in the
whole store, the same two with the own sentences masked, the own-match share, retrieved slots by
kind, retrieved benign sentences by kind, the share of slots from the query's own family, the
fallback count, and the distractor slot concentration.

## Gates and rows

- No gate: every retrieved document goes through whole.
- Document gate: a retrieved document is dropped when its scorer flags it under the record rule
  of D-20261017-56 (a), that is, when any of its sentences scores strictly above 0.5.
- Sentence filter: the sentences scoring above 0.5 are removed and the rest are forwarded, the CAD
  filter's own behaviour.

The rows are no gate; the bag-of-words baseline (document gate only); N0; M0; and M1, M2 and M3,
each on every seed. M1 to M3 use the cell of the round the query belongs to. N0 and M0 hold every
family, so the round's records are taken from their single cell per seed. The baseline scores only
the twin and malicious records. A twin it calls malicious, or a malicious record it calls malicious,
is dropped. Controls and distractors pass it unscored, and the table says so.

## Metrics

A slot is one document in one query's top five. A document retrieved by two queries counts twice,
because the prompt would see it twice.

- Injected pass-through: the share of retrieved shared_malicious documents forwarded with their
  target sentence.
- Twin loss: the share of retrieved semantic twins dropped, or forwarded without their target
  sentence or a cue sentence. The cue sentences come from the cue position, by the locator that
  `data selfcheck` uses. A query cue sits in the query, which no gate touches (40 twins), so for
  those twins only the target sentence counts.
- Random and keyword control loss, and distractor loss: the share of retrieved controls or
  distractors dropped, or forwarded with any sentence removed.
- Context survival: the share of retrieved benign (label 0) sentences forwarded. The headline is
  over family records only. The all-slot figure and the distractor-only figure sit beside it, and
  the retrieved benign sentence counts per kind are printed under each gate table, so the
  distractors' weight in the all-slot figure can be read.

Each seed's slots are pooled over the five rounds. The table gives the mean over seeds with the
population standard deviation (ddof 0). N0, the baseline and no gate have one value. Per-round
figures stay in the JSON. Breakdowns by semantic role and by cue position cover the family records.

## Outputs

`rag harness-run` writes into a new directory:

- `harness.json`: settings, distractor summary, store composition per round, retrieval facts,
  and every row's tables per gate (overall, by role and cue position, per seed and per round);
- `harness.md`: the retrieval table, the two gate tables, the breakdowns and the definitions;
- `retrievals.jsonl`: per query, its top five with kind and cosine, its own rank, and the
  sentences that placed it.

## Estimated time

A read-only load of the real inputs on the laptop took 2.4 s to verify the 49 Phase 7 cells
(0.5 s on a warm rerun), 3.0 s to load the two caches, 0.07 s to build the 800 family documents
and 0.05 s to read one cell's predictions (2.5 s for all 49). No store, retrieval or gate was built on the real data. The
synthetic run, with the same 160 family records per round and 49 cells, took 3.8 s in all.
The real run should therefore take under 30 seconds. Allow one minute. Output is about 1 MB.

## Real-run command line (laptop, after the review)

From the repository root, in Git Bash:

    mkdir -p /c/p8
    PYTHONPATH=src ./.venv/Scripts/python -m rag_cad.cli rag harness-run \
      --phase4-root "C:/Users/songh/Desktop/Master of AI 2025/COMPSCI764/Project/drive-artefacts/phase4/restored/20261004T101405Z_d40b6a6a_m0_8c0933ce" \
      --families C:/p6/20261016T143145Z_86f6f7a3_features_e8058efb \
      --run C:/p7/repo_compatible \
      --mode repo_compatible \
      --output C:/p8/repo_compatible \
      > C:/p8/repo_compatible_harness.json 2> C:/p8/repo_compatible_harness.log

The defaults read `datasets/raw/augmentation/families`, `folds_v1.jsonl` and
`bow_baseline_v1.json`, request 160 distractors and draw them from the minus_near set. Exit code 0
means the run completed; 2 means it was refused, with the cause in the log as "rag harness-run
refused: <class>: <reason>". The command never overwrites, so a second run needs a new `--output`.
The output stays under `C:\p8\`, never in the repository. The tables are copied to an archive folder
afterwards, and the figures are recorded in a decision entry.

## Synthetic end to end

The synthetic run used the synthetic Phase 4 root and family artefact of the Phase 7 synthetic run
(`C:\p7\syn\src\phase4`, `C:\p7\syn\families`, fake encoder, all 200 families). A synthetic Phase 7
run was made with the fake trainer into `C:\p8\syn\p7`. All 49 cells (N0, M0 on three seeds, M1 to
M3 in five rounds on three seeds) took 5.8 s. The commands were:

    PYTHONPATH=src ./.venv/Scripts/python -m rag_cad.cli training run-folds \
      --phase4-root C:/p7/syn/src/phase4 --families C:/p7/syn/families \
      --mode repo_compatible --trainer fake --output C:/p8/syn/p7
    PYTHONPATH=src ./.venv/Scripts/python -m rag_cad.cli rag harness-run \
      --phase4-root C:/p7/syn/src/phase4 --families C:/p7/syn/families \
      --run C:/p8/syn/p7 --distractor-set full --output C:/p8/syn/harness

Each of the three synthetic released-test records is a near duplicate of a synthetic training
record, so the minus_near set is empty there. The synthetic run therefore draws from the full set
(`--distractor-set full`) and gets 3 distractors (one passage each). The tests cover the minus_near path with
leak-free synthetic test records. A second run into a fresh output gave identical retrievals,
Markdown and JSON (apart from the timing). The files are archived in
`docs/archive/phase8_synthetic_2026-10-17/`. They have no scientific meaning.

## Review applied (2026-10-17)

The independent review of the pull request accepted the gates and the reproducibility and asked for
three fixes, all applied:

- Retrieval facts: the masked hit@5 and mean rank and the own-match share are reported beside the
  as-built figures. The definitions state that hit@5 describes the proxy, not retriever quality,
  and that retrieval is identical for every row. Before the passages, the review measured on the
  real caches hit@5 0.771 as built against 0.244 masked.
- Distractors: the sentence count is 228, not 269. The remainders are cut into 56 passages of at
  most five sentences. Before the cut, the 36-sentence remainder took 77 of 327 distractor slots
  and 28 percent of the retrieved benign sentences were distractor sentences. Family context
  survival now leads the gate tables, with the all-slot figure and the sentence counts beside it.
- Three refusal tests were added: an unscored distractor sentence, a record flag that disagrees
  with its rows, and a cue outside its record.

## Done (2026-10-17)

The real run was made with the command line above from main cfd34d8 (after PR #69) on the laptop
CPU. It exited 0 in 9.05 s with an empty log, the identity check matched, and it read all 49
Phase 7 cells. Each round's store held 216 documents: 160 family records plus 56 distractor
passages from the 23 benign remainders. Retrieval, identical for every row: hit@5 0.771 (0.241
masked), mean rank 11.55 (46.18 masked), own-match share 0.262, no centroid fallback. The outputs
are archived in docs/archive/phase8_results_2026-10-17/, with the headline tables in its README.

## Open points for the decision entry

- The distractor change above: 23 benign remainders in 56 passages instead of 160 benign records,
  scored in their injected context.
- The query placement through TF-IDF-matched store sentences, instead of a query embedding, with
  the masked figure beside it.
- Control and distractor loss count any removed sentence as a loss. With passages of at most five
  sentences, this is comparable across kinds. Context survival gives the sentence-level view.
