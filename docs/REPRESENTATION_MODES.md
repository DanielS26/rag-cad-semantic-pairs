# Representation Mode Evidence (D-20260921-05)

Status: evidence only. No primary mode has been selected. This page collects
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

## Options for deciding

1. Author answer. Ask which computation produced the paper's results (handoff
   Section 14, item 1; the question is already on the list for the authors).
2. Empirical reproduction. Score the released test set (389 records, 9,776
   sentence rows) with the released checkpoint under both modes and compare
   with the paper's reported base-CAD metrics; the mode that reproduces them
   is the mode the checkpoint was trained with. This is a bounded Colab job
   under the conformance stage of the candidate profile. Its cost must be
   estimated and approved separately; the full feature-job estimate is still
   an open checklist item.
3. Choice by argument. `repo_compatible` matches the released code and the
   checkpoint's origin; `paper_exact` matches the published description. The
   handoff notes that the released checkpoint makes `repo_compatible` the
   natural first compatibility test but not an automatic scientific choice.

Whichever mode is chosen, D-20260922-12 requires the smoke gate to be rerun in
that mode before final feature builds, and the choice must be recorded as a
decision before `representation` in `configs/experiment.yaml` is set.
