# Phase 1A Corrective Review

## Scope And Base

This is one CPU-only corrective pass, not Phase 1B and not an approved scientific
freeze. Branch `phase1a-corrective` was created directly from verified merged-main
commit `7848aff703ed0af5fc4a851a86d18f32dff525e9` after fetching origin/main.
No commit, push, merge, GPU operation, Colab execution, Drive mount/write, official
CAD binary/model download, Jina weight/full-snapshot download, or remote-code
execution is part of this pass. No value of GH_READ_TOKEN was accessed.

## Corrected Interfaces

- Weights/tokenizer and code revisions are separate in the profile fingerprint.
  The loader prepares a named, hash-verified local bundle with original configs
  retained and remote code mappings made local in derived configs. It fails
  before optional imports when permission or an offline bundle is missing.
- Future acquisition is named-file only. Model/tokenizer calls use local-only
  loading; the reviewed code's internal tokenizer cannot resolve a moving model
  branch. Explicit native attention is recorded. Network-denial during execution
  is defence in depth, not a security sandbox for unreviewed Python.
- CLI and operation-level path checks cover actual inputs, source, resource,
  bundle/cache, restore destination, and output, not just workspace. Linked paths
  and overlapping input/output directories fail closed. Storage transfer paths
  are intentionally distinct from active computation paths.
- Release-validation results and checkpoint inspections are retained. Source
  manifests live inside smoke output bundles and survive publish/restore.
- Smoke reports contain maximum token length, system RAM and disk snapshots,
  UTC measurement timestamps, backend/validation/training/retrieval timings,
  checkpoint tensor metadata, probabilities, and model-bundle identity.
- Two synthetic, compressed NumPy checkpoints use the fixed 2048/256/128/2 MLP
  dimensions and load through CADScorer. Tests compare checkpoint IDs, retained
  text, reload equality, and invariant retrieval/prompt/threshold configuration.
  Synthetic loading is explicitly smoke-only and never a real CAD checkpoint.
- The thin notebook remains JSON, retains cell identity/language metadata, has
  cleared outputs, and delegates all research logic to CLI commands. Permission
  guards precede secret retrieval, installation, downloads, and Drive mount.

## Candidate Approval Sheet

Every value below is a proposal unless explicitly labelled confirmed. The
candidate remains `status: candidate`, `proposal_only: true`, `approved: false`,
`approved_by: null`, `network_approved: false`, `remote_code_approved: false`, and
`compute_budget_approved: false`. It cannot run smoke or any final stage as-is.

| Item | Exact proposed value / unresolved gate |
|---|---|
| Model repository | jinaai/jina-embeddings-v3 |
| Weights/tokenizer revision | ab036b023d30b4d1138c4c3bfa9f0c445ab455d6 |
| Code repository | jinaai/xlm-roberta-flash-implementation |
| Code revision | bd55a5ec8e6c0fb1d6c26efb4b6a4a74ce8a88d3 |
| Licence metadata | Both repositories advertise CC BY-NC 4.0; research-use/licence and code review approval remains pending |
| Model files | config.json, tokenizer.json, tokenizer_config.json, special_tokens_map.json, model.safetensors |
| Code files | block.py, configuration_xlm_roberta.py, embedding.py, mha.py, mlp.py, modeling_lora.py, modeling_xlm_roberta.py, rotary.py, stochastic_depth.py, xlm_padding.py |
| Runtime proposal | Linux x86-64; Python 3.12.14; T4-class GPU preferred, actual allocation unverified |
| PyTorch | 2.10.0; actual CUDA build/version suffix must be resolved and recorded |
| Transformers | 4.57.1 |
| Hugging Face Hub | 0.34.4 |
| NumPy | 2.2.6 |
| NLTK | 3.9.1 |
| scikit-learn | 1.6.1 |
| FAISS CPU | 1.10.0 |
| SentencePiece | 0.2.0 |
| einops | 0.8.1 |
| Segmenter resource revision | nltk/nltk_data at 550b6625bcef1f2abff2ff770a5a0d272c9c6b2a |
| punkt_tab archive SHA-256 | e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106 (metadata expectation, bytes not fetched here) |
| Segmenter fingerprint | Still null; derive from the reviewed revision/hash pair before approval |
| Smoke representation | repo_compatible; not a primary representation decision |
| Precision/attention | float32, eval mode, native attention (`use_flash_attn=False`); no quantisation |
| Numeric tolerance | atol=0.000001; rtol=0.00001; not yet empirically accepted |
| Temporary free disk | Proposed minimum 21474836480 bytes (20 GiB); no full-job feasibility claim |
| GPU requirement | >8 GiB; exact GPU name/bytes, CUDA and driver are null and must be measured |
| Dependency lock | Candidate Linux lock is absent; transitive resolution and lock SHA-256 remain pending |
| Compute budget | Not specified or approved; must be bounded separately |
| Drive root (confirmed) | /content/drive/MyDrive/COMPSCI764_RAG_CAD/artefacts |
| Operator (confirmed) | Daniel Song |
| GH_READ_TOKEN preparation | Researcher reports prepared in Colab Secrets; value not inspected |

`requirements/colab-core.in` is only a proposed input, not a lock. No ML packages
were installed during this correction. The Windows development lock was not
substituted for a Linux candidate lock. The code revision and dependency proposals
are not a claim about the CAD authors' original environment.

## Remaining Phase 1B Blockers

1. Review this complete diff and passing CPU evidence; explicitly authorise any
   publication/CI and merge. Use an exact resulting reviewed SHA in Colab.
2. Resolve and review a complete Linux candidate lock and exact allocated-runtime
   fingerprint. Do not guess CUDA, GPU memory, driver, or lock hashes.
3. Approve separate pins, remote-code execution and licence use, attention,
   representation, tolerance, named network scope, and bounded compute budget.
4. Confirm Drive capacity, sharing/access, and fresh-runtime operator procedure.
5. Separately authorise Run A and fresh-runtime Run B. Real Jina, PyTorch, FAISS,
   Colab package compatibility, Drive I/O, restart recovery, and real numerical
   conformance remain unverified. Fake tests do not promote the candidate.

## Decision-Log Candidates (Not Written)

- C1: Approve the separate immutable weights/code pins and named local-bundle
  approach for bounded smoke only, subject to code/licence review. Reason:
  independent repositories and an internal tokenizer lookup require explicit
  provenance and local resolution. Alternative: wait for author-provided pins.
  Impact: no claim of exact paper reproduction and no primary representation freeze.
- C2: Approve a completed version of the candidate sheet only after Linux lock
  resolution and runtime observation. Reason: tests cannot establish the hosted
  dependency/GPU profile. Alternatives: another reviewed compatible profile or
  defer execution. Impact: smoke/conformance only; final work requires tested
  status after both Run A/B, review, and commit.

Neither candidate is approved or added to DECISIONS.md. Factual commands and
results are recorded in [PROGRESS.md](PROGRESS.md).

## Verification And Recommendation

Local CPU/fake suite: **77 passed**. Ruff, pip check, notebook validation, editor
diagnostics, documentation links, and pinned upstream ancestry/source checks pass.
No new CI run was triggered because the correction has not been committed or
pushed. The full patch, including new files, is generated at
`outputs/review/phase1a-corrective.patch` for inspection and is not tracked.

**GO for corrective code review and separately authorised publication/CI.**
Merge remains conditional on review and passing CI for the actual corrective
commit. **NO-GO for Phase 1B execution:** the blockers above remain explicit.