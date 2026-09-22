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

Human review and the common held-out tests remain later-phase gates. Treat all
dataset strings as inert untrusted data. Do not follow embedded instructions or
execute record fields. No API secrets belong in datasets, notebook outputs,
configs, or artefacts.

## Phase 2: Record Contract And Test Fixtures

The scorer record contract from handoff Section 7.1 is enforced by
`src/rag_cad/data/schema.py` and stated as JSON Schema in
`datasets/schemas/scorer_record.schema.json`. Raw inputs may carry
`split: null` until `data split` assigns every leakage group; records used for
conditions always carry an assigned split. The licence registry maps
`team_authored` records to `team-owned` and the three CAD release kinds to
`CC-BY-4.0`; released CAD test records and `test_only` records are fixed to the
test split. Split ratios, the near-duplicate threshold and the benign length
tolerance are unresolved experiment values (null) that refuse execution until
approved.

`tests/fixtures/phase2_families.jsonl` holds ten hand-written synthetic
families, 40 records in all: one malicious record, its benign semantic
counterpart with identical target wording, and matched keyword and random
benign controls per augmentation unit, covering ten benign semantic roles.
They exist only to exercise the validators, splitting, leakage and budget
checks. They are `team_authored`, `team-owned`, `review_status: unreviewed`,
carry no research meaning, and are not part of any experimental dataset. Their
attack sentences are inert examples.