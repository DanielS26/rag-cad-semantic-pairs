# Data Card

No research dataset has been generated, labelled, or adapted yet.
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
test split. The split ratios (0.7/0.15/0.15 by family), the near-duplicate
threshold (0.8) and the benign length tolerance (0.25) are set by
D-20261004-15; the augmentation budget in sentence rows stays null until the
family pilot measures rows per family, and the commands that need it refuse
execution until it is set.

`tests/fixtures/phase2_families.jsonl` holds ten hand-written synthetic
families, 40 records in all: one malicious record, its benign semantic
counterpart with identical target wording, and matched keyword and random
benign controls per augmentation unit, covering ten benign semantic roles.
They exist only to exercise the validators, splitting, leakage and budget
checks. They are `team_authored`, `team-owned`, `review_status: unreviewed`,
carry no research meaning, and are not part of any experimental dataset. Their
attack sentences are inert examples.

## Phase 4: Official CAD Release Adapted As D0

`data adapt-cad` turns the three pinned CAD archives (tavialiu/CAD-data at
revision f5efab92, CC-BY-4.0) into project records without rewriting any
upstream JSON. Each archive becomes one records file and one notes file under
`datasets/processed/cad_release/` (ignored by Git; regenerate from the
hash-verified archives with the same command), plus `adaptation_manifest.json`
with the archive hashes, counts, digests and every transformation count.

| Archive | Records file | Records | Rows | Malicious | Groups |
|---|---|---:|---:|---:|---:|
| training_data_original | `cad_original_train.jsonl` (`condition_source: base`) | 1,080 | 24,665 | 1,625 | 9 |
| testing_data_original | `cad_original_test.jsonl` (`condition_source: test_only`) | 389 | 9,776 | 3,729 | 57 |
| training_data_paraphrased | `cad_paraphrased_train.jsonl` (secondary analysis only) | 3,376 | 86,341 | 10,052 | 9 |

Field mapping: `record_id` is the source dataset plus the member path inside
the archive without `.json` (for example
`cad_original_train:agentdojo_banking_scenarios/banking_scenario_0/user_task_1/injection_task_1`);
`source_record_id` is the exact member path; `domain` is the AgentDojo suite
(banking, slack or travel) read from the path and cross-checked against
`suite_name` where the archive supplies it; `group_id` is the scenario for the
training archives (paraphrases share their original's group) and the suite
plus user task for the released test archive; `attack_goal` is the suite and
upstream injection task identifier, for example `banking_injection_task_1`;
`family_id` is null and `pair_member` is `unpaired`; labels are 1 inside the
inclusive injection span, those units are targets with `semantic_role:
injected_instruction`; `split` is null in the raw files and `data split` pins
every released test record to the test split; `review_status` is `unreviewed`
because the labels are the authors' and have not been re-reviewed by the team.
The notes files keep, per record and without text, the supplied and parsed
unit counts, the span, the user and injection task identifiers, the paraphrase
style, the raw and normalised `source_file`, and the record content hash.

Facts recorded by the adaptation and the validators on 4 October 2026:
`total_units` is absent from all 360 banking training records and from 1,353
paraphrase records, and stale in 1,278 paraphrase records; 2,199 paraphrase
`source_file` values carry the `agentdojo_<suite>_scenarios/` prefix and all
3,376 paraphrases map to 60 distinct original records; the test archive also
holds three YAML files that the adapter skips. The training archive contains
only nine scenario groups and the released test set is highly repetitive (the
same injection sentences recur across user tasks: 754,690 near-duplicate
target-sentence pairs across its 57 groups at threshold 0.8), which is a
property of the released data worth stating in the report. Under the frozen
segmenter the whole released test set round-trips (join with newlines and
re-segment), but 620 of the 1,080 training records do not: all 300 slack and
320 of 420 travel records contain upstream units that the segmenter splits
further, typically at a dot inside a URL or an address. Training builds
features on the upstream units directly, so this affects neither D0's counts
nor its features; it is a documented train-time versus inference-time
segmentation difference inherited from the release, and the round-trip
requirement remains binding for team-authored records.

Splitting: `data split` pins every D0 record and paraphrase to train and every
released test record to test, under the "none" holdout policy of
D-20261004-15, and the split manifest records that policy. The Phase 4 stage
keeps the released train/test split exactly as published; the project's
leakage report between the two is recorded in `phase4_report.json` but not
enforced, because that split is the authors' and the released test set serves
only as the upstream reference test. That report shows the two sides share
malicious wording: one injected sentence appears verbatim in 128 released test
records and 45 training records, with 20 further near-duplicate target pairs
and 14 shared benign context sentences. The project keeps the released split as
published and applies its own leakage rules to the families it writes.