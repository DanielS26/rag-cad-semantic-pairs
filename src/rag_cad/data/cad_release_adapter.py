"""Strict parsing of the pinned CAD release without altering source records.

The second half adapts whole archives into scorer records (handoff Section 7.1 and Phase 4):
upstream JSON is read, never rewritten; labels come from the inclusive injection span; the
raw metadata that the record contract has no field for is kept in a notes file beside the
records, and every transformation is counted in the adaptation manifest.
"""

import json
import re
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath

from rag_cad.data.jsonl import write_jsonl
from rag_cad.data.schema import (
    LICENCES,
    TOKEN,
    dataset_digest,
    record_content_hash,
    validate_record,
)
from rag_cad.operations.artefacts import checked_members, safe_path
from rag_cad.operations.provenance import sha256, write_json

SUITES = ("banking", "slack", "travel")
RELEASE_KINDS = {
    "original_train": {"source_dataset": "cad_original_train", "condition_source": "base"},
    "original_test": {"source_dataset": "cad_original_test", "condition_source": "test_only"},
    "paraphrased_train": {"source_dataset": "cad_paraphrased_train", "condition_source": "base"},
}
ADAPTATION_ORDER = ("original_train", "original_test", "paraphrased_train")
OUTPUT_FILES = {kind: f"{RELEASE_KINDS[kind]['source_dataset']}.jsonl" for kind in RELEASE_KINDS}
NOTES_FILES = {kind: f"{RELEASE_KINDS[kind]['source_dataset']}.notes.jsonl" for kind in RELEASE_KINDS}
ADAPTATION_MANIFEST = "adaptation_manifest.json"
ADAPTATION_SCHEMA = "rag_cad.cad_adaptation/1"
INJECTED_ROLE = "injected_instruction"
FALLBACK_GOAL = "agentdojo_injection"
_CONTAINER = re.compile(r"agentdojo_(banking|slack|travel)_scenarios")
_SCENARIO = re.compile(r"(banking|slack|travel)_scenario_\d+")


def parse_segments(raw: str | list) -> list[str]:
    if isinstance(raw, list):
        sentences = raw
    elif isinstance(raw, str):
        matches = list(re.finditer(r"(?m)^\[(\d+)\][ \t]?", raw))
        if not matches or raw[:matches[0].start()].strip():
            raise ValueError("Missing numbered sentence segments")
        if [int(match[1]) for match in matches] != list(range(len(matches))):
            raise ValueError("Sentence indices must be unique and sequential from zero")
        sentences = [raw[match.end():matches[index + 1].start() if index + 1 < len(matches)
                        else len(raw)].strip() for index, match in enumerate(matches)]
    else:
        raise ValueError("Invalid sentence_segments type")
    if not sentences or any(not isinstance(text, str) or not text.strip() for text in sentences):
        raise ValueError("Empty or invalid sentence unit")
    return sentences


def adapt_record(record: dict, kind: str) -> dict:
    if kind not in {"original_train", "original_test", "paraphrased_train"}:
        raise ValueError("Unknown release split")
    sentences = parse_segments(record["sentence_segments"])
    if not isinstance(record.get("user"), str) or not record["user"].strip():
        raise ValueError("Missing user query")
    span = record["injection_span_unit"]
    start, end = span["start"], span["end"]
    if type(start) is not int or type(end) is not int or not 0 <= start <= end < len(sentences):
        raise ValueError("Injection span is invalid")
    supplied = record.get("total_units")
    if supplied is not None and type(supplied) is not int:
        raise ValueError("total_units must be an integer when supplied")
    mismatch = supplied is not None and supplied != len(sentences)
    if mismatch and kind != "paraphrased_train":
        raise ValueError("Original record total_units mismatch")
    raw_path = record.get("source_file")
    normalized = raw_path
    if raw_path is not None:
        safe_path(raw_path)
        normalized = re.sub(r"^agentdojo_(banking|slack|travel)_scenarios/", "", raw_path)
    return {
        "query": record["user"], "sentences": sentences,
        "labels": [int(start <= index <= end) for index in range(len(sentences))],
        "provenance": {"supplied_total_units": supplied, "parsed_total_units": len(sentences),
                       "total_units_mismatch": mismatch, "raw_source_file": raw_path,
                       "normalized_source_file": normalized, "release_kind": kind},
    }


def validate_archive(path: Path, specification: dict) -> dict:
    if path.stat().st_size != specification["bytes"] or sha256(path) != specification["sha256"]:
        raise ValueError("Release file size/hash mismatch")
    counts = {"records": 0, "rows": 0, "malicious": 0, "benign": 0, "count_mismatches": 0}
    with tarfile.open(path, "r:gz") as archive:
        for member in checked_members(archive):
            if not member.isfile() or not member.name.endswith(".json"):
                continue
            with archive.extractfile(member) as handle:
                record = adapt_record(json.load(handle), specification["kind"])
            counts["records"] += 1
            counts["rows"] += len(record["labels"])
            counts["malicious"] += sum(record["labels"])
            counts["benign"] += record["labels"].count(0)
            counts["count_mismatches"] += record["provenance"]["total_units_mismatch"]
    if counts != specification["counts"]:
        raise ValueError("Release record/row/class/schema counts mismatch")
    return {"file": path.name, "sha256": sha256(path), "counts": counts}


def member_suite(path: str) -> str:
    """The AgentDojo suite named by an archive path, or "unknown".

    A component names the suite when it is the suite itself (the released test archive puts
    it directly under the extracted folder, which is the domain rule of the pinned
    detector/train_and_eval.py), its agentdojo_<suite>_scenarios container, or a
    <suite>_scenario_<n> directory (the training archives).
    """
    for part in PurePosixPath(path).parts:
        if part in SUITES:
            return part
        match = _CONTAINER.fullmatch(part) or _SCENARIO.fullmatch(part)
        if match:
            return match[1]
    return "unknown"


def _goal_token(suite: str, injection_task_id) -> str:
    if injection_task_id is None:
        return FALLBACK_GOAL
    text = re.sub(r"[^a-z0-9_]+", "_", f"{suite}_{injection_task_id}".lower()).strip("_")
    return text if TOKEN.fullmatch(text) else FALLBACK_GOAL


def _group_id(kind: str, parts: tuple[str, ...], suite: str) -> str:
    """Leakage group: the scenario for training archives (paraphrases join their originals), the
    suite and user task for the released test archive."""
    scenario = next((part for part in parts if _SCENARIO.fullmatch(part)), None)
    if scenario is not None:
        return f"cad_scenario:{scenario}"
    directory = "/".join(parts[1:-1]) if len(parts) > 2 else suite
    return f"cad_{kind}:{directory}"


def scorer_record(member_name: str, raw: dict, kind: str) -> tuple[dict, dict]:
    """A schema-valid scorer record for one archive member, plus a note holding the raw
    metadata the record contract has no field for (identifiers and counts, never text)."""
    spec = RELEASE_KINDS[kind]
    adapted = adapt_record(raw, kind)
    parts = PurePosixPath(member_name).parts
    suite = member_suite(member_name)
    if suite == "unknown":
        raise ValueError("Release member lies outside the known AgentDojo suites")
    declared = raw.get("suite_name")
    if declared is not None and declared != suite:
        raise ValueError("Declared suite_name disagrees with the archive path")
    relative = "/".join(parts[1:]) if len(parts) > 1 else parts[0]
    stem = relative[:-5] if relative.endswith(".json") else relative
    record_id = f"{spec['source_dataset']}:{stem}"
    sentences = [{"sentence_id": index, "text": text, "label": label,
                  "semantic_role": INJECTED_ROLE if label else None, "is_target": bool(label)}
                 for index, (text, label) in enumerate(zip(adapted["sentences"], adapted["labels"]))]
    record = {"record_id": record_id, "group_id": _group_id(kind, parts, suite), "family_id": None,
              "split": None, "condition_source": spec["condition_source"], "query": adapted["query"],
              "domain": suite, "attack_goal": _goal_token(suite, raw.get("injection_task_id")),
              "pair_member": "unpaired", "sentences": sentences,
              "provenance": {"source_dataset": spec["source_dataset"], "source_record_id": member_name,
                             "generator_model": None, "generator_prompt_hash": None,
                             "licence": LICENCES[spec["source_dataset"]], "review_status": "unreviewed"}}
    checked = validate_record(record, require_split=False)
    span = raw["injection_span_unit"]
    note = {"record_id": record_id, "source_record_id": member_name, "suite": suite,
            "user_task_id": raw.get("user_task_id"), "injection_task_id": raw.get("injection_task_id"),
            "injection_span_unit": [span["start"], span["end"]], "style": raw.get("style"),
            **adapted["provenance"], "content_hash": record_content_hash(checked)}
    return checked, note


def adapt_archive(path: Path, kind: str) -> tuple[list[dict], list[dict], dict]:
    """Every JSON member of one release archive as scorer records, in sorted member order."""
    if kind not in RELEASE_KINDS:
        raise ValueError("Unknown release split")
    items, skipped = [], Counter()
    with tarfile.open(path, "r:gz") as archive:
        for member in checked_members(archive):
            if not member.isfile():
                continue
            if not member.name.endswith(".json"):
                skipped[PurePosixPath(member.name).suffix or "none"] += 1
                continue
            with archive.extractfile(member) as handle:
                items.append((member.name, json.load(handle)))
    items.sort(key=lambda item: item[0])
    records, notes = [], []
    for name, raw in items:
        record, note = scorer_record(name, raw, kind)
        records.append(record)
        notes.append(note)
    if len({record["record_id"] for record in records}) != len(records):
        raise ValueError("Duplicate record identifiers in release archive")
    return records, notes, {"skipped_members": dict(skipped)}


def _counts(records: list[dict], notes: list[dict]) -> dict:
    labels = [sentence["label"] for record in records for sentence in record["sentences"]]
    return {"records": len(records), "rows": len(labels), "malicious": sum(labels),
            "benign": labels.count(0), "count_mismatches": sum(note["total_units_mismatch"] for note in notes)}


def _original_reference(note: dict) -> str | None:
    normalized = note.get("normalized_source_file")
    if normalized is None:
        return None
    stem = normalized[:-5] if normalized.endswith(".json") else normalized
    return f"cad_original_train:agentdojo_{note['suite']}_scenarios/{stem}"


def adapt_release(spec: dict, source: Path, output: Path, *, include_paraphrased: bool = True) -> dict:
    """Adapt the pinned release archives under `source` into `output`, refusing on any count drift.

    Writes one records file and one notes file per archive plus the adaptation manifest. The
    paraphrased archive is adapted into its own file for the declared secondary analysis only,
    with each paraphrase mapped to its original record through the normalised source path.
    """
    by_kind = {entry.get("kind"): (filename, entry) for filename, entry in spec["files"].items()}
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": ADAPTATION_SCHEMA, "cad_commit": spec["cad_commit"],
                "data_revision": spec["data_revision"], "data_licence": spec.get("data_licence"),
                "files": {}}
    originals: set[str] = set()
    for kind in ADAPTATION_ORDER:
        if kind not in by_kind or (kind == "paraphrased_train" and not include_paraphrased):
            continue
        filename, entry = by_kind[kind]
        path = source / filename
        if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            raise ValueError("Release hash/size mismatch")
        records, notes, extras = adapt_archive(path, kind)
        counts = _counts(records, notes)
        if counts != entry["counts"]:
            raise ValueError("Adapted counts differ from the release specification")
        if kind == "original_train":
            originals = {record["record_id"] for record in records}
        mapping = None
        if kind == "paraphrased_train":
            references = []
            for note in notes:
                reference = _original_reference(note)
                note["original_record_id"] = reference if reference in originals else None
                references.append(note["original_record_id"])
            mapping = {"matched": sum(reference is not None for reference in references),
                       "unmatched": references.count(None),
                       "distinct_original_records": len({r for r in references if r is not None}),
                       "source_file_prefixed": sum(note["raw_source_file"] != note["normalized_source_file"]
                                                   for note in notes)}
        write_jsonl(output / OUTPUT_FILES[kind], records)
        write_jsonl(output / NOTES_FILES[kind], notes)
        manifest["files"][filename] = {
            "kind": kind, "bytes": entry["bytes"], "sha256": entry["sha256"],
            "records_file": OUTPUT_FILES[kind], "records_sha256": sha256(output / OUTPUT_FILES[kind]),
            "notes_file": NOTES_FILES[kind], "notes_sha256": sha256(output / NOTES_FILES[kind]),
            "counts": counts, "dataset_digest": dataset_digest(records),
            "suites": dict(Counter(record["domain"] for record in records)),
            "groups": len({record["group_id"] for record in records}),
            "total_units_missing": sum(note["supplied_total_units"] is None for note in notes),
            "total_units_mismatch_records": [note["record_id"] for note in notes if note["total_units_mismatch"]],
            "attack_goal_fallbacks": sum(record["attack_goal"] == FALLBACK_GOAL for record in records),
            "paraphrase_source_mapping": mapping, **extras}
    adapted_kinds = {entry["kind"] for entry in manifest["files"].values()}
    if not {"original_train", "original_test"} <= adapted_kinds:
        raise ValueError("Release specification lacks the original training or test archive")
    write_json(output / ADAPTATION_MANIFEST, manifest)
    return manifest