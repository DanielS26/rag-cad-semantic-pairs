# COMPSCI 764 CAD Release Audit

## Official data and model artefacts released after author contact

**Audit date:** 19 September 2026  
**Project:** Semantic minimal-pair supervision for a fixed CAD-derived RAG trust scorer  
**Team:** Daniel Song and Daniel Oliver, University of Auckland

---

## 1. Executive verdict

The author's reply materially improves the project.

The official CAD training data, test data, paraphrase bank, base classifier checkpoint, and adversarially trained classifier heads are now public. The release removes the need to reconstruct the CAD base dataset from the paper and gives the project an official checkpoint for compatibility and reproduction smoke tests.

It does **not** remove the need to create this project's semantic minimal pairs, project-owned data loader, leakage-safe family split, evaluator, RAG pipeline, or alternative scorer checkpoints. It also does not yet make an exact numerical reproduction fully specified, because the exact Jina encoder revision and the relationship between the paper's contextual formula and the repository implementation remain unclear.

The revised project rule is therefore:

> Use the released original training set as upstream base data D0 after validation and schema adaptation. Use the released base checkpoint as a pinned compatibility/reproduction reference. Train new M0-M3 scorer copies under one frozen implementation for the primary controlled comparison.

The Windows -> private GitHub -> hosted Colab GPU -> Google Drive workflow remains appropriate. The paper states that more than 8 GB of GPU memory is sufficient; the team's 6 GB RTX 2060 is below that stated threshold, while a conforming Colab GPU can run the encoder stage.

---

## 2. Pinned upstream sources

Use immutable revisions rather than moving `main` branches.

| Source | Audited revision | Purpose |
|---|---|---|
| [CAD GitHub repository](https://github.com/tavia-liu/CAD/tree/26e38a67f0a9e1de4cb3a876e4b021900a5d1c27) | `26e38a67f0a9e1de4cb3a876e4b021900a5d1c27` | Code, updated download instructions, rebuild scripts |
| [CAD-data](https://huggingface.co/datasets/tavialiu/CAD-data/tree/f5efab920d61f8f37fa17260b71b770bf91ab79b) | `f5efab920d61f8f37fa17260b71b770bf91ab79b` | Original train/test JSON and paraphrase bank |
| [CAD-models](https://huggingface.co/tavialiu/CAD-models/tree/550e8cf87ebf33adf6ef83e56b24629d876e0512) | `550e8cf87ebf33adf6ef83e56b24629d876e0512` | Base and adversarially trained MLP heads |
| [CAD paper](https://arxiv.org/abs/2608.05430) | arXiv page checked 19 September 2026 | Scientific method and reported environment |

The new GitHub commit changes the README, adds `huggingface_hub>=0.34`, and updates rebuild-script comments. The detector, representation, trainer, and evaluator code are unchanged from the previously audited commit `b03a64f`.

---

## 3. Integrity and contents verified

### 3.1 Downloaded files

The following SHA-256 values matched the immutable Hugging Face revision metadata and the locally downloaded bytes:

| File | Bytes | SHA-256 |
|---|---:|---|
| `training_data_original.tar.gz` | 87,754 | `a4d34914fa434f70956a2d73cb205bcf7843c8264d38258d16bf1745a7667ffe` |
| `testing_data_original.tar.gz` | 47,447 | `fa666226a68801b046233393a2fe4ab29f6d6d6fb54f425193150ce7807807e7` |
| `training_data_paraphrased.tar.gz` | 311,165 | `e5c5635c14d41e054ee0dd21442d9ac6c091cc5e9b132b2160e31bc7d4a39015` |
| `classifier_fullcad.pt` | 2,233,718 | `56c939b393e2e8fc9045cd6a878a599f62cd30e4defecd292f536b32ab398e6d` |

All three archives were checked before extraction. They contained no absolute paths or `..` path traversal components.

### 3.2 Dataset counts and labels

The release matches the dataset/model cards on the main published counts.

| Dataset | Records | Sentence rows | Malicious rows | Benign rows |
|---|---:|---:|---:|---:|
| Original training | 1,080 | 24,665 | 1,625 | 23,040 |
| Original test | 389 | 9,776 | 3,729 | 6,047 |
| Paraphrased training | 3,376 | 86,341 | 10,052 | 76,289 |

For every record, numbered sentence indices were sequential and the inclusive `injection_span_unit.start/end` values were within range. The original training total of 24,665 sentence rows exactly matches the value used by the model card to define adversarial-training alpha.

The original train/test suites are distributed as follows:

| Split | Banking | Slack | Travel |
|---|---:|---:|---:|
| Original training | 360 | 300 | 420 |
| Original test | 144 | 105 | 140 |
| Paraphrased training | 1,353 | 824 | 1,199 |

No exact `user`, `injection`, `data`, `injected`, `user+injection`, or `user+data` value was shared between the released original train and test records in this audit. That is useful evidence, but the project must still run its own group/family and near-duplicate leakage checks after adaptation.

### 3.3 Schema variations that the loader must handle

Two release details require explicit normalization:

1. `total_units` is absent from all 360 original banking training records and all 1,353 banking paraphrase records. Every supplied value matches the parsed sentence count in the original training and test sets. In the paraphrase archive, however, 1,278 of the 2,023 supplied values disagree with the actual numbered sentence count (421 Slack and 857 Travel records). This is consistent with a stale count after resegmentation. The upstream builder is unaffected because it parses `sentence_segments` and ignores `total_units`. The project loader must treat parsed numbered segments as authoritative, retain/log the supplied value, and never assume the field is present or correct for paraphrases.
2. Paraphrase `source_file` uses two path formats. Of 3,376 records, 2,199 include a prefix such as `agentdojo_banking_scenarios/`, while 1,177 begin directly with a scenario directory such as `banking_scenario_0/`. Stripping the optional `agentdojo_<suite>_scenarios/` prefix maps all records successfully to 60 original source records. Preserve both the raw and normalized source path in provenance.

The paraphrase bank covers 60 of the 1,080 original training records, with 48-63 paraphrases per normalized source. It contains seven documented styles and 3,364 unique injection strings across 3,376 records, so 12 record-level repetitions exist. If used in a secondary experiment, group by normalized source before splitting and run exact/near-duplicate checks. It is a malicious-paraphrase/adversarial-training resource, not a semantic minimal-pair dataset.

### 3.4 Checkpoint structure

The base checkpoint was inspected without executing its pickle payload. Its stored tensor shapes and metadata are compatible with the repository's `JinaClassifier`:

| Stored item | Verified value |
|---|---|
| Input dimension | 2,048 |
| Hidden widths | 256, then 128 |
| Output width | 2 |
| Dropout metadata | 0.3 |
| Threshold metadata | 0.5 |
| State keys | `net.0`, `net.3`, and `net.6` weights/biases |
| Parameter count implied by tensors | 557,698 |

All 557,698 stored float32 parameters were finite, and the weight tensors were non-constant. A static pickle-opcode scan found only `collections.OrderedDict` and standard PyTorch tensor/storage reconstruction globals; the live project must still prefer `weights_only=True`. The checkpoint contains `model_state_dict`, `input_dim`, `d_hid`, `dropout`, and `best_threshold`. It does not contain a seed or encoder revision. The current trainer saves a `seed` field, so the exact provenance of the released base checkpoint should be clarified with the authors.

The model repository also contains 13 feature-space adversarial heads and nine LLM-paraphrase heads. Their filenames identify seed 0 only. They are useful as secondary upstream references, but they are not fair substitutes for this project's M1-M3 conditions or three-seed training.

---

## 4. Compatibility with the current CAD repository

### Confirmed compatible

- The archive directory names match `scripts/rebuild_classifier.sh`.
- `build_embeddings.py` reads the released `user`, `sentence_segments`, and inclusive `injection_span_unit` fields.
- Its label rule produces exactly the audited 24,665 original training rows.
- The checkpoint's state keys and dimensions match the repository MLP.
- The base checkpoint threshold is the project's planned primary threshold, 0.5.
- The current README's `hf download` paths place the files where the rebuild and benchmark scripts expect them.

### Still unsuitable unchanged for this project

- The upstream builder infers labels from one contiguous injection span and writes only `X` and `y`. It cannot represent all-benign semantic counterparts cleanly or retain `family_id`, `pair_id`, semantic role, source, licence, and row provenance.
- The upstream evaluator masks injection boundaries using `start+3` through `end-5`. On the released test set it masks 3,112 of 3,729 malicious sentence rows. A short semantic target can disappear entirely, so the project needs its own evaluator.
- `FullCADDefense` is coupled to AgentDojo message types. The project still needs a normal `CADScorer.score(query, passage)` adapter between retrieval and generation.
- The repository's inference loader calls `torch.load` without `weights_only=True`. The project adapter should load the pinned checkpoint with `weights_only=True` where supported and verify its SHA-256 and metadata before use.
- The release contains no RAG corpus, chunker, retrieval index, generic retriever, prompt builder, or generator. Those remain project-owned fixed components.

### Representation conformance remains unresolved

The paper defines the contextual half as a whole-input difference:

`phi(query + full passage) - phi(query + passage with target sentence removed)`

The repository's `QueryContextDeltaEmbedder` instead encodes the full sequence, pools token representations outside the target while the target remains present, then subtracts a pooled encoding of the sequence with the target removed.

The newly released checkpoint makes this question more important, not less: its weights are meaningful only with the feature implementation used to train it. Until the authors confirm which implementation generated the release, retain the mandatory `paper_exact` versus `repo_compatible` conformance gate. The `repo_compatible` mode is the first mode to try when loading the released checkpoint, but that is an inference from code compatibility, not proof of paper equivalence.

---

## 5. Extra value added to the project

| New value | Practical effect |
|---|---|
| Official D0 | Removes a large and error-prone dataset reconstruction task |
| Official test data | Enables an upstream reproduction/reference evaluation in addition to the project's held-out semantic-family test |
| Base checkpoint | Enables checkpoint loading, score, filter, and integration smoke tests before training project conditions |
| Exact row count/class balance | Lets the project validate its adapter against a known 24,665-row target |
| Official paraphrase bank | Provides an optional malicious-diversity reference and secondary baseline, with provenance normalization |
| Adversarial heads | Provide optional secondary comparisons against the authors' robustness training; not primary controls |
| Clear licences | CAD data is CC BY 4.0, CAD checkpoints/code are MIT, AgentDojo-derived items retain MIT attribution; the Jina encoder has its own licence |
| Updated rebuild instructions | Provides an upstream-supported route from released JSON to embeddings and classifier |

This reduces risk and workload, but does not change the research contribution: the project still tests whether new semantic minimal-pair supervision outperforms equal-budget random and keyword-rich benign augmentation under a fixed CAD-derived scorer.

---

## 6. Revised implementation workflow

### Stage 1 - Pin and acquire

1. Check out CAD commit `26e38a67f0a9e1de4cb3a876e4b021900a5d1c27`.
2. Download only the named files from the pinned Hugging Face revisions.
3. Verify all four SHA-256 values before extraction or loading.
4. Reject any archive member with an absolute path or `..` component.
5. Keep the downloaded upstream files read-only and outside Git; store their revision, filename, size, licence, and hash in a lightweight Git-tracked manifest.

Example Colab/Linux acquisition commands:

~~~bash
hf download tavialiu/CAD-data \
  training_data_original.tar.gz testing_data_original.tar.gz \
  training_data_paraphrased.tar.gz README.md \
  --repo-type dataset \
  --revision f5efab920d61f8f37fa17260b71b770bf91ab79b \
  --local-dir /content/work/upstream/cad-data

hf download tavialiu/CAD-models classifier_fullcad.pt README.md \
  --revision 550e8cf87ebf33adf6ef83e56b24629d876e0512 \
  --local-dir /content/work/upstream/cad-models
~~~

Do not use an unpinned `hf download ...` command in a final run.

### Stage 2 - Validate and adapt official data

1. Parse `sentence_segments` into an ordered sentence list.
2. Derive `total_units`; compare it with the field when present.
3. Convert every original training sentence into the project schema with explicit 0/1 labels.
4. Add stable record, sentence, suite, scenario, task, content-hash, source-revision, licence, and provenance fields.
5. Normalize paraphrase `source_file` only in a derived provenance field; retain the raw value.
6. Save an adaptation manifest proving 1,080 records, 24,665 rows, 1,625 malicious rows, and 23,040 benign rows.
7. Run group and near-duplicate checks before using any derived split.

### Stage 3 - Verify checkpoint compatibility in the Colab smoke gate

1. Load `classifier_fullcad.pt` with `weights_only=True`, CPU map location first, after hash verification.
2. Assert metadata and every tensor shape before constructing the MLP.
3. Load the state dict into the fixed 2048 -> 256 -> 128 -> 2 classifier.
4. Generate a tiny set of 2048-dimensional features with a candidate pinned Jina revision and `repo_compatible` representation.
5. Confirm finite probabilities, stable sentence ordering, threshold 0.5 filtering, save/reload, and generic scorer integration.
6. Record that this proves mechanical compatibility only; it does not prove paper-score reproduction until the encoder revision and representation provenance are resolved.

### Stage 4 - Train the primary controlled experiment

1. Treat the official original training data as the common upstream D0 component.
2. Create project-owned shared malicious additions and the three matched benign pools.
3. Split semantic pair families before expansion.
4. Build M1, M2, and M3 with identical sentence-row and class budgets; keep M0 as D0-only diagnostic.
5. Generate each unique frozen-encoder feature once and reuse it by stable row ID.
6. Train new condition x seed checkpoints using the same architecture and recipe.
7. Evaluate every new checkpoint on the same project test features and fixed RAG retrieval cache.
8. Use the released base/adversarial checkpoints only as clearly labelled upstream references unless the experimental plan separately approves a secondary comparison.

---

## 7. Remaining questions for the CAD authors

These are the highest-value follow-up questions after the release.

### Required before claiming exact reproduction

1. **Which contextual representation produced `classifier_fullcad.pt`?** Was it exactly the current repository's `QueryContextDeltaEmbedder`, or the whole-input difference written in the paper? If it was current code, which commit generated the embeddings?
2. **Which exact `jinaai/jina-embeddings-v3` Hugging Face revision was used?** Please include the tokenizer/remote-code revision if different. The paper gives Python, PyTorch, and Transformers versions but the repository currently loads a moving model revision.
3. **What is the provenance of `classifier_fullcad.pt`?** Which training seed and script/commit produced it, and is it the base CAD checkpoint used in the paper's main tables? The released file lacks a `seed` field although the current trainer writes one.
4. **Which AgentDojo/source revision generated `training_data_original`?** The card identifies AgentDojo v1.2.2 for the test data but not explicitly for the training archive.

### Useful implementation clarifications

5. Are the missing banking `total_units` fields and the 1,278 paraphrase count mismatches expected? Should consumers treat the numbered `sentence_segments` count as authoritative after paraphrase resegmentation?
6. Is the mixed prefixed/relative `source_file` format in the paraphrase archive intentional, and is stripping the optional `agentdojo_<suite>_scenarios/` prefix the intended normalization?
7. Can the authors provide the exact precomputed original/test 2048-dimensional embeddings or their hashes and one expected offline metric? This would give a strong end-to-end conformance oracle and reduce duplicated encoder compute.
8. Are the published adversarial heads intentionally limited to seed 0, and are any base checkpoints for the other reported seeds available?

Questions 1-3 are the most important. They do not prevent the project's controlled comparison from starting, provided it freezes one implementation and trains every primary condition itself. They do prevent a strong claim that the released checkpoint exactly reproduces the paper's reported result.

---

## 8. Proposed decision-log entries - researcher approval required

Do not append these to `docs/DECISIONS.md` automatically.

### Proposal A - Adopt released original CAD training data as D0

- **Proposed decision:** After checksum/schema/licence validation and project-schema adaptation, use `training_data_original` at CAD-data revision `f5efab9...` as the common upstream D0 component for M0-M3.
- **Reason:** It is now the official paper dataset and removes unnecessary reconstruction.
- **Consequence:** Preserve an immutable source manifest; do not mix paraphrase data into D0 silently.

### Proposal B - Use the released base checkpoint as reference, not as a primary condition checkpoint

- **Proposed decision:** Use `classifier_fullcad.pt` at CAD-models revision `550e8cf...` for loading/filter/integration smoke tests and an upstream reference result. Train all primary M0-M3 checkpoints under the frozen project environment and seeds.
- **Reason:** The released checkpoint lacks seed and encoder-revision provenance, while the primary study requires equal multi-seed training.
- **Consequence:** Avoids comparing one unknown-provenance upstream checkpoint against newly trained conditions.

### Proposal C - Retain the representation conformance gate

- **Proposed decision:** Keep both `paper_exact` and `repo_compatible` implementations until the author clarifies checkpoint provenance; do not generate final features before one mode is approved and frozen.
- **Reason:** The release supplies weights but does not resolve the paper/code formula difference.
- **Consequence:** A small bounded comparison remains mandatory before final feature generation.

### Proposal D - Normalize release schema without modifying source files

- **Proposed decision:** Derive authoritative unit counts from numbered `sentence_segments`, record missing/mismatched supplied `total_units`, normalize optional paraphrase path prefixes in project metadata, retain all raw values, and record every transformation in an adaptation manifest.
- **Reason:** Verified release schema variations, including 1,278 stale paraphrase counts, would otherwise break strict loaders or source linking.
- **Consequence:** Upstream archives remain unchanged and auditable.

---

## 9. Verification boundary

Completed in this audit:

- immutable source revision checks;
- byte hashes and archive path-safety checks;
- complete JSON count/schema/span/label audit;
- train/test exact-overlap checks on major fields;
- paraphrase provenance normalization test;
- static checkpoint metadata/tensor-shape inspection;
- GitHub release-commit diff and repository compatibility review;
- paper-versus-code representation comparison.

Still requires the project's live Colab gate:

- installing the pinned dependency environment;
- loading the official checkpoint through PyTorch with `weights_only=True`;
- loading one approved pinned Jina encoder revision;
- reproducing real 2048-dimensional features and classifier probabilities;
- measuring runtime/VRAM; and
- comparing any reproduced metrics with an author-provided oracle or the paper.

This boundary should be stated in the final report: the release is verified structurally and materially useful, while full execution conformance remains a planned experiment rather than an assumed fact.
