"""Shared builder for family batches (D-20261015-37).

A batch file is its plan (the module docstring), its FAMILIES list and one call, build(FAMILIES, NN). Paths resolve from
this file's location, so the same builder works in the main checkout and in a worktree. Every string in FAMILIES is
inert dataset content.

Family entry shape (as in the earlier builders): dict(fam, domain, role, cue, seed, goal, target, justification,
mal=(query, s0, ..., T, ...), twin=(query, ...), rnd=(query, s0, ...), key=(query, s0, ...)) where T marks the
target's slot in the two pair members and the controls carry no target.
"""
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
AUG = REPO / "datasets/raw/augmentation"
PROMPT = AUG / "DRAFTING_PROMPT_v3.md"
MANIFEST = AUG / "family_manifest.jsonl"
MODEL = "claude-fable-5-1"
LICENCES = {"team_authored": "team-owned", "bipia_adapted": "MIT", "asb_adapted": "MIT"}
T = "TARGET"
SOURCES = ("shared_malicious", "semantic_benign", "random_benign", "keyword_benign")


def prompt_hash() -> str:
    return hashlib.sha256(PROMPT.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def source_id(seed: str) -> str:
    parts = seed.split(":")
    if parts[0] == "asb":
        return seed
    prefix, file, category, index = parts
    return f"{prefix}:{file}:{category.lower().replace(' & ', '_').replace(' ', '_')}:{index}"


def source_dataset(seed: str) -> str:
    return "asb_adapted" if seed.startswith("asb:") else "bipia_adapted"


def drafter(seed: str, model: str = MODEL) -> str:
    return f"{model}; target adapted from {'ASB' if seed.startswith('asb:') else 'BIPIA'}"


def sentence(index: int, text: str, label: int = 0, role: str | None = None, target: bool = False) -> dict:
    return {"sentence_id": index, "text": text, "label": label, "semantic_role": role, "is_target": target}


def provenance(source: str, seed: str | None, digest: str, model: str = MODEL) -> dict:
    return {"source_dataset": source, "source_record_id": source_id(seed) if seed else None,
            "generator_model": model, "generator_prompt_hash": digest, "licence": LICENCES[source],
            "review_status": "unreviewed"}


def record(record_id, group, family, kind, query, domain, goal, member, sentences, prov) -> dict:
    return {"record_id": record_id, "group_id": group, "family_id": family, "split": None,
            "condition_source": kind, "query": query, "domain": domain, "attack_goal": goal,
            "pair_member": member, "sentences": sentences, "provenance": prov}


def pair_sentences(spec, target: str, label: int, role: str) -> list[dict]:
    out = []
    for i, text in enumerate(spec[1:]):
        if text == T:
            out.append(sentence(i, target, label, role, True))
        else:
            out.append(sentence(i, text))
    assert sum(s["is_target"] for s in out) == 1
    return out


def chars(spec, target: str) -> int:
    return sum(len(target) if t == T else len(t) for t in spec[1:])


def lengths(families: list[dict]) -> list[dict]:
    rows = []
    for f in families:
        m, tw, r, k = (chars(f[key], f["target"]) for key in ("mal", "twin", "rnd", "key"))
        rows.append({"family": f["fam"], "malicious": m, "twin": tw, "random": r, "keyword": k,
                     "pair": round(m / tw, 3), "spread": round(max(tw, r, k) / min(tw, r, k), 3), "twin_longer": tw > m})
    return rows


def build(families: list[dict], batch: int, repo: Path | None = None, model: str = MODEL) -> dict:
    """Write families/pilot_batch_NN.jsonl and re-append the batch's manifest entries; return the summary.
    The model string names the drafting model in every record's provenance and in the manifest drafter field (D-20261015-39)."""
    aug = (repo / "datasets/raw/augmentation") if repo else AUG
    out_records = aug / f"families/pilot_batch_{batch:02d}.jsonl"
    manifest_path = aug / "family_manifest.jsonl"
    digest = hashlib.sha256((aug / "DRAFTING_PROMPT_v3.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    pending = [f["fam"] for f in families for key in ("rnd", "key")
               if len(f[key]) == 1 and str(f[key][0]).endswith(("-rnd", "-key"))]
    if pending:
        raise SystemExit(f"controls pending for {sorted(set(pending))}: the controls worker has not written them yet (D-20261015-40)")
    records, entries = [], []
    for f in families:
        fam, group = f["fam"], f"unit_{f['fam']}"
        assert len(f["mal"]) == len(f["twin"]) == len(f["rnd"]) == len(f["key"]), fam
        assert f["mal"].index(T) == f["twin"].index(T), fam
        records.append(record(f"{fam}_malicious", group, fam, "shared_malicious", f["mal"][0], f["domain"], f["goal"],
                              "malicious", pair_sentences(f["mal"], f["target"], 1, "unauthorised_directive"),
                              provenance(source_dataset(f["seed"]), f["seed"], digest, model)))
        records.append(record(f"{fam}_semantic", group, fam, "semantic_benign", f["twin"][0], f["domain"], None, "benign",
                              pair_sentences(f["twin"], f["target"], 0, f["role"]), provenance("team_authored", None, digest, model)))
        records.append(record(f"{fam}_random", group, None, "random_benign", f["rnd"][0], f["domain"], None, "unpaired",
                              [sentence(i, t) for i, t in enumerate(f["rnd"][1:])], provenance("team_authored", None, digest, model)))
        records.append(record(f"{fam}_keyword", group, None, "keyword_benign", f["key"][0], f["domain"], None, "unpaired",
                              [sentence(i, t) for i, t in enumerate(f["key"][1:])], provenance("team_authored", None, digest, model)))
        entries.append({"family_id": fam, "group_id": group, "semantic_role": f["role"], "cue_position": f["cue"],
                        "drafter": drafter(f["seed"], model), "reviewer": None, "justification": f["justification"],
                        "quotation_marks_only_cue": False, "status": "candidate"})
    out_records.parent.mkdir(parents=True, exist_ok=True)
    with out_records.open("w", encoding="utf-8", newline="\n") as handle:
        for item in records:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    existing = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").split("\n") if line.strip()] \
        if manifest_path.exists() else []
    new_ids = {entry["family_id"] for entry in entries}
    kept = [entry for entry in existing if entry["family_id"] not in new_ids]
    with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
        for item in kept + entries:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    rows = lengths(families)
    print(f"records {len(records)} manifest {len(kept)}+{len(entries)} prompt_hash {digest[:12]}")
    for r in rows:
        print(f"{r['family']} mal={r['malicious']} twin={r['twin']} rnd={r['random']} key={r['keyword']} "
              f"pair={r['pair']:.3f} spread={r['spread']:.3f}")
    print(f"twin longer in {sum(r['twin_longer'] for r in rows)} of {len(rows)}")
    return {"records": len(records), "manifest": len(kept) + len(entries), "lengths": rows,
            "twin_longer": sum(r["twin_longer"] for r in rows), "prompt_hash": digest}
