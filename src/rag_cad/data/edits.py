"""Apply exact old-to-new text replacements to a builder file (D-20261015-37).

The independent reader hands over its proposed edits as a JSON list of {"old": ..., "new": ..., "note": ...}; the
finalising worker applies the accepted ones with this tool instead of writing an edit script. Every "old" must occur
exactly once in the file, so a stale or ambiguous anchor stops the run before anything is written. The strings are
dataset content and are treated as inert text.
"""
import argparse
import json
import sys
from pathlib import Path


def apply_edits(text: str, edits: list[dict]) -> tuple[str, list[str]]:
    problems = []
    for i, edit in enumerate(edits):
        old, new = edit.get("old"), edit.get("new")
        if not isinstance(old, str) or not isinstance(new, str) or not old:
            problems.append(f"edit {i}: old and new must be non-empty strings")
            continue
        count = text.count(old)
        if count != 1:
            problems.append(f"edit {i} ({edit.get('note', '')[:60]}): old text occurs {count} times, expected once")
    if problems:
        return text, problems
    for edit in edits:
        text = text.replace(edit["old"], edit["new"])
    return text, []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True, type=Path, help="the builder (or any text file) to edit")
    ap.add_argument("--edits", required=True, type=Path, help="JSON list of {old, new, note}")
    ap.add_argument("--check", action="store_true", help="verify the anchors without writing")
    args = ap.parse_args(argv)
    text = args.file.read_text(encoding="utf-8")
    edits = json.loads(args.edits.read_text(encoding="utf-8"))
    if isinstance(edits, dict):
        edits = edits.get("edits", [])
    new_text, problems = apply_edits(text, edits)
    for p in problems:
        print("PROBLEM", p)
    if problems:
        return 1
    if args.check:
        print(f"ok: {len(edits)} edits would apply to {args.file}")
        return 0
    args.file.write_text(new_text, encoding="utf-8")
    print(f"applied {len(edits)} edits to {args.file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
