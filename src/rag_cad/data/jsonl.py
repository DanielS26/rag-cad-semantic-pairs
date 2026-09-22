"""Strict JSONL reading and writing for scorer records."""

import json
from pathlib import Path

from rag_cad.data.schema import validate_record
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import canonical_json, reject_secrets, sha256


def read_jsonl(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    records = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            raise ValueError(f"Blank line {number} in {path.name}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON on line {number} of {path.name}") from None
        if not isinstance(value, dict):
            raise ValueError(f"Line {number} of {path.name} is not a JSON object")
        records.append(value)
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    """Write canonical one-object-per-line JSON; never overwrite and never store secrets."""
    records = list(records)
    reject_secrets(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        for record in records:
            handle.write(canonical_json(record) + "\n")


def dataset_files(source: Path) -> list[Path]:
    source = local_path(source)
    if source.is_file():
        files = [source]
    elif source.is_dir():
        files = sorted(path for path in source.rglob("*.jsonl") if not path.is_symlink())
    else:
        raise ValueError("Dataset source must be a JSONL file or a directory")
    files = [path for path in files if path.is_file() and path.suffix == ".jsonl"]
    if not files:
        raise ValueError("No JSONL dataset files were found")
    return files


def load_records(source: Path, *, require_split: bool = False) -> tuple[list[dict], dict]:
    """Load, validate and de-duplicate records; return them with a file inventory."""
    files = dataset_files(source)
    base = local_path(source)
    inventory = {}
    records = []
    seen = set()
    for path in files:
        relative = path.name if base.is_file() else path.relative_to(base).as_posix()
        inventory[relative] = sha256(path)
        for value in read_jsonl(path):
            record = validate_record(value, require_split=require_split)
            if record["record_id"] in seen:
                raise ValueError(f"Duplicate record_id across dataset files [{record['record_id']}]")
            seen.add(record["record_id"])
            records.append(record)
    return records, {"files": inventory, "records": len(records)}
