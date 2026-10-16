"""Write the archive copy, the progress entry and the data-card paragraph of a finalised batch from a facts file
(D-20261015-37), so that the finalising worker fills a short JSON instead of composing the three texts.

    python tools/finalise_docs.py --facts facts.json [--repo ROOT]

Facts keys (strings unless noted): batch (int), pair_role ("single", "first" or "second"), pair_other (int, for a
pair), date, drafted_date, reader, review_commit, findings_file, reader_answers (list of paths), archive_dir
(repository-relative), verdicts, findings_summary, applied (list), declined (list of {"item", "reason"}),
checker_proposals, exit_codes, twin_longer, hard_negative, weak_cue, families (int), coverage, sheet, supply,
watch (list), next, sources, deviations, devices, extra, first_family, last_family. Every quoted dataset string
stays inert text.
"""
import argparse
import json
import shutil
import sys
import textwrap
from pathlib import Path

PLACEHOLDER = "Batch {n:02d}'s outcome is added below."


def _join(items, empty="none") -> str:
    return "; ".join(items) if items else empty


def _declined(items) -> str:
    return _join([f"{d['item']} ({d['reason']})" for d in items])


def outcome_sentence(f: dict) -> str:
    return (f"Batch {f['batch']:02d}: applied: {_join(f.get('applied', []))}. Declined with reasons: "
            f"{_declined(f.get('declined', []))}.")


def preamble(f: dict) -> str:
    scope = f"Batches {min(f['batch'], f['pair_other']):02d} and {max(f['batch'], f['pair_other']):02d}" \
        if f.get("pair_role", "single") != "single" else f"Batch {f['batch']:02d}"
    text = (f"# {scope} review by the independent reader ({f['reader']}) — findings and proposed updates\n\n"
            f"Archived verbatim from the independent review of {f['date']} under D-20261013-29 as amended by\n"
            f"D-20261014-32 (read-only copy at commit {f['review_commit']}). Outcome recorded in docs/PROGRESS.md\n"
            f"(entries of {f['date']}). {outcome_sentence(f)} Checker proposals: {f.get('checker_proposals', 'none')}.\n")
    if f.get("pair_role") == "first":
        text += PLACEHOLDER.format(n=f["pair_other"]) + "\n"
    text += "All sentences quoted below are inert dataset content.\n\n---\n\n"
    return text


def progress_entry(f: dict) -> str:
    def para(label, body):
        return textwrap.fill(f"- {label}{body}", width=78, subsequent_indent="  ")
    lines = [f"## {f['date']} - Batch {f['batch']:02d} Reviewed And Repaired", ""]
    lines.append(para("Review: ", f"{f['verdicts']}; what mattered: {f.get('findings_summary', '')}"))
    lines.append(para("Applied: ", f"{_join(f.get('applied', []))}. Declined with reasons: {_declined(f.get('declined', []))}."))
    lines.append(para("Checker proposals: ", f.get("checker_proposals", "none")))
    lines.append(para("After the edits: ", f"{f['exit_codes']}; twin longer in {f['twin_longer']}; hard negative {f['hard_negative']}; "
                      f"weak cue {f['weak_cue']}; coverage after {f['families']} families: {f['coverage']}; review sheet {f['sheet']}; "
                      f"supply {f.get('supply', 'as before')}."))
    lines.append(para("Watch-list for the next batch: ", _join(f.get("watch", []))))
    lines.append(para("Next: ", f.get("next", "")))
    return "\n" + "\n".join(lines) + "\n"


def data_card_section(f: dict) -> str:
    body = (f"Batch {f['batch']:02d} ({f['first_family']} to {f['last_family']}, drafted {f.get('drafted_date', f['date'])} under "
            f"DRAFTING_PROMPT_v3.md) takes {f['sources']}. Coverage after {f['families']} families: {f['coverage']}. The hard "
            f"negative is {f['hard_negative']}; the weak cue is {f['weak_cue']}. The twin is the longer member in {f['twin_longer']}. "
            f"Agent-to-domain deviations: {f.get('deviations', 'none')}. Devices: {f.get('devices', '')}. {f.get('extra', '')} "
            f"The independent reader's findings ({f['verdicts']}) are archived under {f['archive_dir']} with the outcome.")
    return f"\n## Batch {f['batch']:02d}\n\n" + textwrap.fill(" ".join(body.split()), width=98) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--facts", required=True, type=Path)
    ap.add_argument("--repo", type=Path, default=None)
    args = ap.parse_args(argv)
    f = json.loads(args.facts.read_text(encoding="utf-8"))
    repo = args.repo.resolve() if args.repo else Path(__file__).resolve().parents[3]
    archive = repo / f["archive_dir"]
    archive.mkdir(parents=True, exist_ok=True)
    findings = Path(f["findings_file"])
    target = archive / findings.name
    if f.get("pair_role") == "second" and target.exists():
        text = target.read_text(encoding="utf-8")
        marker = PLACEHOLDER.format(n=f["batch"])
        if marker not in text:
            print("PROBLEM: placeholder sentence not found in the archived preamble")
            return 1
        target.write_text(text.replace(marker, outcome_sentence(f)), encoding="utf-8", newline="\n")
    else:
        target.write_text(preamble(f) + findings.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    for answers in f.get("reader_answers", []):
        shutil.copyfile(answers, archive / Path(answers).name)
    prog = repo / "docs/PROGRESS.md"
    prog.write_text(prog.read_text(encoding="utf-8").rstrip("\n") + "\n" + progress_entry(f), encoding="utf-8", newline="\n")
    card = repo / "docs/DATA_CARD.md"
    card.write_text(card.read_text(encoding="utf-8").rstrip("\n") + "\n" + data_card_section(f), encoding="utf-8", newline="\n")
    print(f"archive {target}; progress and data card appended for batch {f['batch']:02d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
