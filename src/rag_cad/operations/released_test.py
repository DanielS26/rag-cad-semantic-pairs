"""Bounded evaluation of the released checkpoint on the released test set under both modes.

No sentence-level oracle is published for the base detector (paper, model card and
dataset card checked on 23 September 2026). The discriminator for D-20260921-05 is
therefore which representation mode the released checkpoint fits, measured with the
upstream boundary-masked evaluator. Conformance-stage work; it selects no mode.
"""

import json
import tarfile
import time
from pathlib import Path, PurePosixPath

import numpy as np

from rag_cad.cad.representation import MODES, build_mode_features
from rag_cad.data.cad_release_adapter import adapt_record
from rag_cad.data.jsonl import write_jsonl
from rag_cad.evaluation.detector_metrics import THRESHOLD, summarise, upstream_boundary_mask
from rag_cad.operations.artefacts import checked_members, safe_path
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import sha256, write_json
from rag_cad.operations.smoke import mark, resource_snapshot

ARCHIVE = "testing_data_original.tar.gz"
REPORT = "released_test_evaluation.json"
PREDICTIONS = "predictions.jsonl"
ARCHIVE_ROOT = ARCHIVE[: -len(".tar.gz")]


def record_domain(path: str) -> str:
    """The upstream domain of a test file: the first directory under the extracted test folder.

    Mirrors build_eval_mask in the pinned detector/train_and_eval.py, which takes the first
    component of each JSON path relative to the test directory (banking, slack or travel).
    Archive members carry that folder as their own first component, so it is stripped first.
    """
    parts = PurePosixPath(path).parts
    if parts and parts[0] == ARCHIVE_ROOT:
        parts = parts[1:]
    return parts[0] if len(parts) > 1 else "unknown"


def load_released_test(archive: Path) -> list[dict]:
    """Adapted records in the upstream sorted-path order; domain is the first path component."""
    local_path(archive)
    items = []
    with tarfile.open(archive, "r:gz") as handle:
        for member in checked_members(handle):
            if not member.isfile() or not member.name.endswith(".json"):
                continue
            path = str(safe_path(member.name))
            with handle.extractfile(member) as source:
                items.append((path, json.load(source)))
    items.sort(key=lambda item: item[0])
    records = []
    for path, raw in items:
        adapted = adapt_record(raw, "original_test")
        span = raw["injection_span_unit"]
        records.append({"source_file": path, "domain": record_domain(path),
                        "query": adapted["query"], "sentences": adapted["sentences"],
                        "labels": adapted["labels"], "span": [span["start"], span["end"]],
                        "upstream_mask": upstream_boundary_mask(len(adapted["sentences"]),
                                                                span["start"], span["end"])})
    return records


def evaluate_released_test(backend, archive: Path, output: Path, metadata: dict, identity: str, *,
                           records: int = 0, domains: tuple[str, ...] = ()) -> dict:
    if type(records) is not int or records < 0:
        raise ValueError("Record limit must be a non-negative integer (0 means all)")
    local_path(output)
    started = time.perf_counter()
    selected = load_released_test(archive)
    if domains:
        selected = [record for record in selected if record["domain"] in set(domains)]
    if records:
        selected = selected[:records]
    if not selected:
        raise ValueError("No released test records selected")
    output.mkdir(parents=True, exist_ok=False)
    mark("released_test_extracted")
    before = resource_snapshot(output)
    rows, skipped = [], []
    encode_seconds, passes = 0.0, 0
    for record in selected:
        probabilities = {}
        try:
            encode_started = time.perf_counter()
            features = build_mode_features(record["query"], record["sentences"], backend.encoder)
            encode_seconds += time.perf_counter() - encode_started
            passes += 1 + 2 * len(record["sentences"])
            for mode in MODES:
                scored = np.asarray(backend.reference_score(features[mode]))
                if scored.shape != (len(record["sentences"]), 2) or not np.isfinite(scored).all():
                    raise ValueError("Reference checkpoint returned invalid probabilities")
                probabilities[mode] = scored[:, 1]
        except ValueError as error:
            if "token limit" not in str(error):
                raise
            skipped.append(record["source_file"])
            continue
        for index in range(len(record["sentences"])):
            rows.append({"source_file": record["source_file"], "domain": record["domain"],
                         "sentence_id": index, "label": record["labels"][index],
                         "upstream_mask": record["upstream_mask"][index],
                         **{f"p_{mode}": float(probabilities[mode][index]) for mode in MODES}})
    mark("released_test_encoded")
    if not rows:
        raise ValueError("Every selected record exceeded the encoder token limit")
    labels = np.array([row["label"] for row in rows])
    mask = np.array([row["upstream_mask"] for row in rows])
    domain_of = np.array([row["domain"] for row in rows])
    scores = {mode: np.array([row[f"p_{mode}"] for row in rows]) for mode in MODES}
    metrics = {mode: {"all_rows": summarise(labels, scores[mode]),
                      "upstream_masked": summarise(labels, scores[mode], mask=mask),
                      "by_domain_masked": {domain: summarise(labels, scores[mode], mask=mask & (domain_of == domain))
                                           for domain in sorted(set(domain_of))}} for mode in MODES}
    first, second = MODES
    masked_ap = {mode: metrics[mode]["upstream_masked"]["average_precision"] for mode in MODES}
    masked_auc = {mode: metrics[mode]["upstream_masked"]["roc_auc"] for mode in MODES}
    comparable = all(value is not None for value in masked_ap.values())
    comparison = {"decision_agreement_rate": float(((scores[first] > THRESHOLD) == (scores[second] > THRESHOLD)).mean()),
                  "masked_average_precision": masked_ap, "masked_roc_auc": masked_auc,
                  "higher_masked_average_precision": (max(MODES, key=lambda mode: masked_ap[mode])
                                                      if comparable and masked_ap[first] != masked_ap[second] else None),
                  "primary_mode_selected": False}
    mark("released_test_scored")
    write_jsonl(output / PREDICTIONS, rows)
    total = time.perf_counter() - started
    report = {"execution_kind": backend.kind, "stage": "released_test", "runtime_identity": identity,
              "metadata": metadata, "archive_sha256": sha256(archive),
              "records_selected": len(selected), "records_scored": len(selected) - len(skipped),
              "skipped_over_length": skipped, "rows": len(rows), "positives": int(labels.sum()),
              "masked_out_rows": int((~mask).sum()), "masked_out_malicious": int((~mask & (labels == 1)).sum()),
              "domains": {domain: int((domain_of == domain).sum()) for domain in sorted(set(domain_of))},
              "metrics": metrics, "comparison": comparison,
              "maximum_token_length": backend.max_token_length,
              "encoder_passes": passes,
              "timings_seconds": {"total": total, "encode_both_modes": encode_seconds,
                                  "backend_load": backend.load_seconds},
              "rows_per_second_both_modes": len(rows) / max(encode_seconds, 1e-9),
              "resources_before": before, "resources_after": resource_snapshot(output),
              "predictions_sha256": sha256(output / PREDICTIONS),
              "oracle": "none published; discriminator is which mode the released checkpoint fits"}
    if backend.kind == "real":
        import torch

        report["peak_gpu_memory_bytes"] = torch.cuda.max_memory_allocated()
    write_json(output / "preflight.json", metadata)
    write_json(output / REPORT, report)
    mark("released_test_report_written")
    return report
