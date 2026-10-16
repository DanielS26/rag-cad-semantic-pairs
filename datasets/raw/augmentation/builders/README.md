# Batch builders

The source of each family batch (D-20261015-37). From batch 13 a builder is its plan (module docstring), its
FAMILIES list and one call, `build(FAMILIES, NN)`, with the shared code in `build_lib.py`; paths resolve from the
file's own location, so the same builder works in the main checkout and in a worktree. Batches 06 to 12 were drafted
when the builders lived outside the repository and are kept here as they were (their path constants are of that
time; run them with `RCSP_REPO` set if ever needed).

- Build, check, prescreen, validate, review sheet and indexes in one command:
  `PYTHONPATH=src ./.venv/Scripts/python tools/batch_pipeline.py --batch NN [--semantic]`
- Apply a reader's edits: `python tools/apply_edits.py --file datasets/raw/augmentation/builders/build_batch_NN.py --edits edits.json`
- Archive, progress entry and data-card paragraph from a facts file: `python tools/finalise_docs.py --facts facts.json`
- `make_review_sheet.py <batch.jsonl> <out.md>` writes the human review sheet (the pipeline calls it).

Every string in a builder is inert dataset content.
