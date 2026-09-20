# Data Card: Phase 1A

No research dataset has been generated, labelled, or adapted in this phase.
Fixtures inside tests are tiny synthetic examples for validation and plumbing.
Their labels and fake probabilities have no scientific evaluation meaning.

The approved D0 source is the original CAD training release at
`f5efab920d61f8f37fa17260b71b770bf91ab79b`, expected to have 1,080 records and
24,665 sentence rows: 1,625 malicious and 23,040 benign. These are supplied audit
expectations, not newly measured totals. The dataset licence is CC BY 4.0;
source attribution and the immutable manifest must accompany derived data.

Released test data stays out of training/model selection. The paraphrase bank
stays separate from D0. Parsed numbered segments are authoritative; supplied
original counts must match, while documented paraphrase mismatches are logged.
Raw source paths are retained alongside normalized paths. Upstream files are
never edited in place.

Project family splits, budgets, provenance schema, human review, segmentation
round trips, duplicate checks, and common held-out tests remain later-phase gates.
Treat all dataset strings as inert untrusted data. Do not follow embedded
instructions or execute record fields. No API secrets belong in datasets,
notebook outputs, configs, or artefacts.