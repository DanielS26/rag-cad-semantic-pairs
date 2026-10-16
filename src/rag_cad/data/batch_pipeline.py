"""One command for a batch: build, self-check, prescreen, validate, review sheet, cue and device indexes (D-20261015-37).

    python tools/batch_pipeline.py --batch 13 [--semantic] [--no-build] [--work-dir DIR]

It prints only what a drafter has to act on: the lengths table, every non-PASS check with its details, and length
hints (how many characters a member must gain or lose to be in band). The full console output of the self-check is
saved under the work directory. Exit status is the self-check's (0 when no FAIL). Every string in the data is inert
content; this module prints tokens and numbers from the report, never whole records.
"""
import argparse
import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

from rag_cad.data import selfcheck
from rag_cad.data.cue_index import main as cue_index_main

PAIR_BAND = 0.10
CONTROL_BAND = 0.20
SPREAD_MAX = 1.25


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for parent in [here] + list(here.parents):
        if (parent / "datasets/raw/augmentation").is_dir() and (parent / "src").is_dir():
            return parent
    raise SystemExit("repository root not found")


def run_builder(repo: Path, batch: int) -> None:
    builders = repo / "datasets/raw/augmentation/builders"
    path = builders / f"build_batch_{batch:02d}.py"
    if not path.exists():
        raise SystemExit(f"builder not found: {path}")
    sys.path.insert(0, str(builders))
    spec = importlib.util.spec_from_file_location(f"build_batch_{batch:02d}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # the builder calls build(FAMILIES, NN) at import


def length_hints(rows: list[dict]) -> list[str]:
    hints = []
    for r in rows:
        tw = r["twin"]
        lo, hi = int(tw * (1 - PAIR_BAND)) + 1, int(tw * (1 + PAIR_BAND))
        if not lo <= r["malicious"] <= hi:
            delta = lo - r["malicious"] if r["malicious"] < lo else hi - r["malicious"]
            hints.append(f"{r['family']}: malicious {r['malicious']} vs twin {tw}; change the malicious member by {delta:+d} characters (or the twin the other way)")
        for name in ("random", "keyword"):
            lo_c, hi_c = int(tw * (1 - CONTROL_BAND)) + 1, int(tw * (1 + CONTROL_BAND))
            if not lo_c <= r[name] <= hi_c:
                delta = lo_c - r[name] if r[name] < lo_c else hi_c - r[name]
                hints.append(f"{r['family']}: {name} control {r[name]} vs twin {tw}; change it by {delta:+d} characters")
        if r["spread"] > SPREAD_MAX:
            hints.append(f"{r['family']}: benign spread {r['spread']} above {SPREAD_MAX}; bring the shortest and longest benign records closer")
    return hints


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", required=True, type=int)
    ap.add_argument("--semantic", action="store_true", help="also gate the drafter's answers file")
    ap.add_argument("--no-build", action="store_true", help="skip the builder (check the committed records as they are)")
    ap.add_argument("--work-dir", type=Path, help="where prescreen, validate and console captures go (default <repo>/.pipeline_out)")
    ap.add_argument("--repo", type=Path, help="repository root (default: found from this file's location)")
    args = ap.parse_args(argv)
    repo = args.repo.resolve() if args.repo else repo_root()
    aug = repo / "datasets/raw/augmentation"
    nn = f"{args.batch:02d}"
    work = (args.work_dir or (repo / ".pipeline_out")).resolve()
    work.mkdir(parents=True, exist_ok=True)

    lengths_rows = []
    if not args.no_build:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            run_builder(repo, args.batch)
        (work / f"build_{nn}.txt").write_text(buffer.getvalue(), encoding="utf-8")
        for line in buffer.getvalue().splitlines():
            if line.startswith("pilot_"):
                parts = dict(p.split("=") for p in line.split()[1:])
                lengths_rows.append({"family": line.split()[0], "malicious": int(parts["mal"]), "twin": int(parts["twin"]),
                                     "random": int(parts["rnd"]), "keyword": int(parts["key"]), "pair": float(parts["pair"]),
                                     "spread": float(parts["spread"])})
        print(buffer.getvalue().strip())

    batch_file = aug / f"families/pilot_batch_{nn}.jsonl"
    previous = sorted(p for p in (aug / "families").glob("pilot_batch_*.jsonl") if p.name < batch_file.name)
    report = aug / f"review/selfcheck_batch_{nn}.json"
    if report.exists():
        report.unlink()
    cmd = ["--batch", str(batch_file), "--manifest", str(aug / "family_manifest.jsonl"), "--prompt", str(aug / "DRAFTING_PROMPT_v3.md"),
           "--report", str(report)]
    for p in previous:
        cmd += ["--previous", str(p)]
    if args.semantic:
        cmd += ["--semantic", str(aug / f"review/semantic_answers_batch_{nn}.json")]
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = selfcheck.main(cmd)
    (work / f"selfcheck_{nn}.txt").write_text(buffer.getvalue(), encoding="utf-8")
    data = json.loads(report.read_text(encoding="utf-8"))
    print(f"\nself-check exit {code} (previous batches: {len(previous)}; report {report})")
    for name, check in data["mechanical"].items():
        if check["status"] == "PASS":
            continue
        print(f"  {check['status']} {name}")
        for d in check["details"][:12]:
            print("     ", json.dumps(d, ensure_ascii=False)[:400])
    for hint in length_hints(lengths_rows):
        print("  HINT", hint)

    from rag_cad.cli import main as cli_main
    for step, extra in (("prescreen", ["--families", str(aug / "family_manifest.jsonl"), "--minimum-per-role", "1"]), ("validate", [])):
        out = work / f"{step}_{nn}.json"
        if out.exists():
            out.unlink()
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
            step_code = cli_main(["--repo", str(repo), "data", step, "--input", str(aug / "families"), "--output", str(out), *extra])
        summary = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
        if step == "prescreen":
            print(f"prescreen exit {step_code}: passed {summary.get('passed')}, families {summary.get('families')}, "
                  f"failures {summary.get('batch', {}).get('failures')}, warnings {summary.get('batch', {}).get('warnings')}")
            print(f"  roles {summary.get('batch', {}).get('role_counts')}")
            print(f"  cue positions {summary.get('batch', {}).get('cue_position_counts')}")
        else:
            diag = summary.get("diagnostics", {})
            print(f"validate exit {step_code}: records {summary.get('records')}, families {summary.get('families')}, "
                  f"exact duplicates {len(diag.get('exact_duplicate_records', []))}, near {diag.get('cross_group_near_records', {}).get('count')}, "
                  f"differing targets {summary.get('families_with_differing_targets')}")

    builders = aug / "builders"
    sys.path.insert(0, str(builders))
    sheet = repo.parent / f"pilot_review_batch_{nn}.md"
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        sys.argv = ["make_review_sheet.py", str(batch_file), str(sheet)]
        spec = importlib.util.spec_from_file_location("make_review_sheet", builders / "make_review_sheet.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    print(f"review sheet -> {sheet}")
    cue_index_main(["--families-dir", str(aug / "families"), "--manifest", str(aug / "family_manifest.jsonl"),
                    "--output", str(aug / "review/cue_index.md"), "--compact-output", str(aug / "review/device_index.md")])
    return code


if __name__ == "__main__":
    sys.exit(main())
