"""Write a human review sheet for one batch file: python make_review_sheet.py <batch.jsonl> <out.md>"""

import json
import os
import sys
from pathlib import Path

REPO = Path(os.environ.get("RCSP_REPO", str(Path(__file__).resolve().parents[4])))
batch, out = Path(sys.argv[1]), Path(sys.argv[2])
recs = [json.loads(l) for l in batch.read_text(encoding="utf-8").splitlines() if l.strip()]
man = {json.loads(l)["family_id"]: json.loads(l)
       for l in (REPO / "datasets/raw/augmentation/family_manifest.jsonl").read_text(encoding="utf-8").splitlines()
       if l.strip()}
order = ["shared_malicious", "semantic_benign", "random_benign", "keyword_benign"]
names = {"shared_malicious": "MALICIOUS MEMBER", "semantic_benign": "BENIGN TWIN",
         "random_benign": "RANDOM BENIGN (M1)", "keyword_benign": "KEYWORD BENIGN (M2)"}
lines = [f"# Review sheet: {batch.name}", "",
         "For each family read the four cards, then record a verdict (accepted / ambiguous / rejected) "
         "and any wording fix. Labels: 1 = malicious, 0 = benign; * marks the target sentence.", ""]
by_fam = {}
for r in recs:
    by_fam.setdefault(r["group_id"].replace("unit_", ""), []).append(r)
for fam, items in by_fam.items():
    m = man[fam]
    seed = next(r for r in items if r["condition_source"] == "shared_malicious")["provenance"]["source_record_id"]
    lines += [f"## {fam}  |  domain: {items[0]['domain']}  |  role: {m['semantic_role']}  |  cue: {m['cue_position']}",
              f"Justification: {m['justification']}", f"Seed: {seed}", ""]
    for src in order:
        r = next(x for x in items if x["condition_source"] == src)
        lines.append(f"**{names[src]}**  q: {r['query']}")
        for s in r["sentences"]:
            lines.append(f"- [{s['label']}]{'*' if s['is_target'] else ' '} {s['text']}")
        lines.append("")
    lines += ["Verdict: ______    Fix: ______", "", "---", ""]
out.write_text("\n".join(lines), encoding="utf-8")
print("review sheet", out, len(by_fam), "families")
