"""Strict parsing of the pinned CAD release without altering source records."""

import json
import re
import tarfile
from pathlib import Path

from rag_cad.operations.artefacts import checked_members, safe_path
from rag_cad.operations.provenance import sha256


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