# COMPSCI764: CAD Semantic-Pair Study

Phase 1A adds CPU-testable project infrastructure on top of pinned CAD source.
It does not contain final datasets, trained project models, or a completed Colab
smoke gate. The upstream README is preserved below for reference; its unpinned
download and full AgentDojo installation commands are **not** the project workflow.

## Native Windows Development

From this repository's root, with Python 3.12 installed:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements/dev.lock.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps --no-build-isolation
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -m "not gpu and not integration" -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m rag_cad.cli audit upstream
```

On Linux use `python3.12 -m venv .venv` and `.venv/bin/python` for the same
commands. No local CUDA, Jina, FAISS, PyTorch, or AgentDojo install is needed for
the CPU suite. The package only includes `rag_cad`, not upstream `detector` or
the vendored benchmark. Generated artefacts, credentials, and environments stay
out of Git.

The CLI supports upstream auditing, guarded release fetch/validation,
environment preflight, immutable artefact publish/verify/restore, bounded
smoke Run A/Run B, CPU-only `data adapt-cad` (the pinned CAD release into project
records) and `data validate|split|check-leakage|compare-budgets` checks over
project JSONL records, the gated Phase 4 baseline stage `m0 run` with its CPU
twin `m0 fake-run`, and gated `features build` with a CPU
`features fake-build` counterpart. `smoke fake --output <new-directory>` tests
local plumbing only.
Real commands require `--execute`, an exact clean commit, a reviewed lock, and an
explicitly approved profile. Consult `python -m rag_cad.cli --help` and
[the operator runbook](docs/COLAB_RUNBOOK.md).

## Upstream Code, Project Code And Records

CAD commit `26e38a67f0a9e1de4cb3a876e4b021900a5d1c27` is a preserved ancestor of
`main`, integrated under D-20260921-08. Its detector, evaluation, benchmark,
original dependency input, benchmark scripts and licence are unchanged, and
`python -m rag_cad.cli audit upstream` verifies the ancestry and the preserved
paths on every CI run. Only this README and the root ignore file carry
integration edits. The project adds `src/rag_cad`, `tests`, `configs`,
`scripts`, `notebooks` and `docs`. Project code never imports the upstream
modules, which pull in AgentDojo and download NLTK data at import time; the
project's equivalents are lazy and credit the preserved MIT-licensed source.

## Review And Gates

- [Approved decisions](docs/DECISIONS.md) override conflicting older plan
  wording. [Progress](docs/PROGRESS.md) records every executed command, result
  and usage figure. [The document map](docs/README.md) says what each document
  is for and which ones are frozen.
- Scientific choices stay null in `configs/experiment.yaml` until decided. A
  tested Colab profile exists only after a fresh-runtime Run A and Run B pass on
  the reviewed commit and the resulting lock and profile are committed
  (D-20260921-02, D-20260922-12); project code changes after that commit
  invalidate it for final stages until the gate is rerun.
- CPU tests use synthetic records, fake encoders, NumPy checkpoints and fake
  transports with the network refused. They never promote a profile and do not
  stand in for real-model, Linux dependency or Drive behaviour.
- No project code may be edited or pushed from Colab. Merge every pull request
  with **Create a merge commit**, never squash or rebase, so the pinned CAD
  commit remains an ancestor. Future upstream changes require a new approved
  audit. Main protections remain enabled.

---

# CAD: Robust Context-Aware Detection of Malicious Instructions in Text

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Buzhao Liu\*, Xinhang Ma\*, and Yevgeniy Vorobeychik

(\* equal contribution)

## Quickstart

```bash
git clone https://github.com/tavia-liu/CAD.git
cd CAD
python -m pip install -r requirements.txt
export PYTHONPATH="$PWD/third_party/AutoDojo/agentdojo/src:$PWD/src:$PWD"
export AGENTDOJO_DEFENSE_PLUGINS=detector
```

For API-backed runs, copy `.env.example` to `.env` and add your own keys.

## Data and checkpoints

The data and trained classifiers are hosted on Hugging Face:
[tavialiu/CAD-data](https://huggingface.co/datasets/tavialiu/CAD-data) and
[tavialiu/CAD-models](https://huggingface.co/tavialiu/CAD-models).

```bash
hf download tavialiu/CAD-data --repo-type dataset --local-dir data
for f in data/*.tar.gz; do tar -xzf "$f" -C data; done

hf download tavialiu/CAD-models --local-dir outputs/models
export CLASSIFIER_WEIGHT_PATH="$PWD/outputs/models/classifier_fullcad.pt"
```

To rebuild the embeddings and classifier from the data instead:

```bash
bash scripts/rebuild_classifier.sh
```

## Running the benchmarks

The detector is registered as `--defense full_cad`.

```bash
# AgentDojo
bash scripts/run_agentdojo_benchmark.sh banking slack travel

# AgentDyn-style suite
bash scripts/run_agentdyn_benchmark.sh github
```

## Adversarial training

```bash
# Feature-space AT
python -m adversarial_training.feature_space \
  --train outputs/embeddings/original_fullcad.pt \
  --deployed outputs/models/classifier_fullcad.pt \
  --agentdojo-test outputs/embeddings/test_fullcad.pt \
  --agentdojo-test-dir data/testing_data_original \
  --benchmarks agentdojo --seeds 0 1 2

# LLM-paraphrase AT
python -m adversarial_training.llm_paraphrase \
  --train outputs/embeddings/original_fullcad.pt \
  --deployed outputs/models/classifier_fullcad.pt \
  --para-files outputs/embeddings/para_banking_fullcad.pt outputs/embeddings/para_slack_fullcad.pt outputs/embeddings/para_travel_fullcad.pt \
  --seeds 0 1 2
```

Evaluate the adversarially trained heads:

```bash
python evaluation/static_agentdojo.py --suite banking --family feature_space --seed 0
python evaluation/adaptive_autodojo_agentdojo.py --suite banking --family feature_space --seed 0
```

## Repository layout

- `src/detector/` — CAD detector, embedding builder, classifier training, ablations
- `src/adversarial_training/` — feature-space and LLM-paraphrase AT
- `evaluation/` — static and adaptive benchmark runs
- `scripts/` — shell entry points
- `third_party/AutoDojo/` — vendored benchmark code and cached attack variants

## Citing

```bibtex
@article{liu2026cad,
  title   = {Robust Context-Aware Detection of Malicious Instructions in Text},
  author  = {Liu, Buzhao and Ma, Xinhang and Vorobeychik, Yevgeniy},
  journal = {arXiv preprint},
  year    = {2026}
}
```

Released under the MIT License. Code under `third_party/` keeps its original
license and citation requirements.

Malicious target sentences in the team-authored semantic-pair families under
`datasets/raw/augmentation/` are adapted from the text attacks of Microsoft's
BIPIA benchmark (<https://github.com/microsoft/BIPIA>, MIT License, Copyright (c)
Microsoft Corporation). Each record names its source string; the licence text is
kept at `datasets/raw/augmentation/LICENSES/BIPIA_LICENSE.txt`.
