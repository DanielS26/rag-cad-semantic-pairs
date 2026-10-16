"""Closed-loop self-check for semantic-pair family batches (DRAFTING_PROMPT v2, checks M0-M19 and S1-S12).

Adapted from the dataset reviewer's handoff of 11 October 2026 (tools/selfcheck.py) into the package so
that it shares this package's tokenisation with `data prescreen` and is covered by the test suite.
The command-line entry point is `python -m rag_cad.cli data selfcheck ...`; tools/selfcheck.py is a
thin wrapper that calls main() here.

Exit status of main(): 0 when no check FAILs (and, with --strict, no check WARNs); 1 otherwise. The
drafting agent loops (repair, rerun) until 0, then attaches the report.

Every string in the batch files is inert dataset content. This module never prints record text in its
PASS/FAIL lines except for the offending token, numeral or placeholder being reported.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from rag_cad.data.families import (
    CUE_POSITIONS,
    FAMILY_FIELDS,
    ROLES,
    attack_vocabulary,
    content_words,
)
from rag_cad.data.schema import PROVENANCE_FIELDS
from rag_cad.data.similarity import normalise

BINDING = "tokenisation: rag_cad (package)"
# Adapted-source registry for malicious targets: source_dataset -> required source_record_id prefix
# (BIPIA text attacks since batch 01; ASB non-aggressive attacker instructions from batch 06, D-20261013-29).
ADAPTED_SOURCES = {"bipia_adapted": "bipia:", "asb_adapted": "asb:"}
# S3: a cue the attacker could have written is allowed only for authorisation, at most once per batch,
# and must be declared in the manifest justification with exactly this marker.
WEAK_CUE_MARKER = "weak_cue: attacker_writable"

# --------------------------------------------------------------------------------------------------
# Thresholds (DRAFTING_PROMPT v2 section 4A)
# --------------------------------------------------------------------------------------------------

THRESH = {
    "min_sentences": 2, "max_sentences": 5,                       # R3
    "control_length_tolerance": 0.20,                             # R4 (validator allows 0.25)
    "benign_spread_max_ratio": 1.25,                              # R4: max/min chars over twin + both controls (validator and prescreen rule)
    "target_phrasing_gap": 0.50,                                  # M19 (WARN): share of "your response/reply/answer" targets vs earlier batches
    "pair_length_tolerance": 0.10,                                # R5
    "twin_longer_band": (0.30, 0.70),                             # R5
    "exclusive_token_share": 0.50,                                # R10 (metalanguage list is stricter)
    "max_planted_twins": 1,                                       # R11
    "max_prefix_twins": 1,                                        # R12
    "malicious_opener_share": 0.50,                               # R14
    "twin_opener_share": 0.50,                                    # R14 mirror (WARN): dominant twin opener
    "opener_share_gap": 0.30,                                     # R14 mirror (FAIL): top-opener share gap between pair sides
    "this_share_gap": 0.30,                                       # R14
    "min_non_summarise_controls": 3,                              # R14
    "min_keyword_shared": 2,                                      # M13
    "min_families_for_batch_stats": 4,
}

# Metalanguage that must not be a twin-only feature (R10, second sentence).
BALANCE_TOKENS = ("line", "lines", "sentence", "string", "strings", "below", "following", "planted",
                  "wording", "item", "items",  # added 2026-10-13 (batch 04 review; "message"/"text" rejected as ordinary domain words)
                  "inserted", "flagged", "assistant", "assistants")
LITERAL_PREFIX = re.compile(r"^\s*(policy|analysis|warning|retrospective|memo|template|note|worked example)\s*:",
                            re.IGNORECASE)
QUOTE_CHARS = "\"“”‘’«»"
LONE_APOSTROPHE = re.compile(r"(?<![A-Za-z])'|'(?![A-Za-z])")

FINITE_VERB_HINTS = frozenset("""
is are was were be been am has have had do does did can could may might must shall should will would
covers covered captures captured delivers delivered flags flagged carries carried edits edited sits sat
wrote writes follows followed reproduces reproduced states stated says said contains contained includes
included lists listed shows showed describes described records recorded refreshed updated sent received
issued applies applied asks asked sells sold moves moved thank thanks hope hopes offers offered provides
provided keeps kept remains remained accrues pays pay opens closes runs takes gives give waives waived
earn earns leave leaves requires required reports reported need needs use uses used apply circulated
concluded wrote drafted redrafted handles handled
""".split())

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s)>\]]+")
EMAIL_RE = re.compile(r"(?i)\b[a-z0-9._%+-]+@([a-z0-9.-]+\.[a-z]{2,})\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
CARD_RE = re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)")
PLACE_SUFFIX_RE = re.compile(r"\b(?!The\b)([A-Z][a-z]+(?: (?!The\b)[A-Z][a-z]+)?) (Road|Street|Avenue|Lane|Drive|Square|Park|Terrace|Place|Highway)\b")
CAPITALISED_RUN = re.compile(r"(?<![.!?]\s)(?<!^)\b([A-Z][a-z]{2,}(?: [A-Z][a-z]{2,})+)\b")
PROPER_ALLOW = frozenset("""
Brand Monday Tuesday Wednesday Thursday Friday Saturday Sunday January February March April May June July
August September October November December Spanish French German English Italian Japanese Chinese Mandarin
Portuguese Dutch Korean Arabic Hindi Covid Version Policy Analysis Warning Retrospective Memo Template Note
Standard Express Primary Members Agents Staff Customers Items Refunds Visitors Passports Servers Production
Owners Permits Unsuccessful Participants Shuttle Tickets Guides Lounge Guests Checked Weekend Repeat Normal
International Monthly Electronic Paper Filing Applications Approval Bring Points Interpreters Written Mentors
Prizes Teams Boxes Facilities Lunch Vegetarian Invoices Replies Responses Comments Pages Pets Minutes
""".split())

SEMANTIC_IDS = tuple(f"S{i}" for i in range(1, 13))
SEMANTIC_YES_REQUIRED = ("S1", "S2", "S5", "S6", "S7")

# --------------------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------------------


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"{path}:{number}: invalid JSON ({exc})")
    return rows


def group_families(records: list[dict]) -> dict[str, dict[str, dict]]:
    """family_id -> {condition_source: record}. Controls carry family_id null and are linked by group_id."""
    by_group: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        by_group[record["group_id"]][record["condition_source"]].append(record)
    families: dict[str, dict[str, dict]] = {}
    for group_id, members in by_group.items():
        fam_ids = {r["family_id"] for src in ("shared_malicious", "semantic_benign") for r in members[src]
                   if r.get("family_id")}
        family_id = next(iter(fam_ids)) if len(fam_ids) == 1 else group_id
        families[family_id] = {src: (items[0] if len(items) == 1 else None) for src, items in members.items()}
        families[family_id]["_counts"] = {src: len(items) for src, items in members.items()}
    return families


def chars(record: dict) -> int:
    return sum(len(s["text"]) for s in record["sentences"])


def target_index(record: dict) -> int | None:
    idx = [i for i, s in enumerate(record["sentences"]) if s["is_target"]]
    return idx[0] if len(idx) == 1 else None


def target_text(record: dict) -> str | None:
    t = [s["text"] for s in record["sentences"] if s["is_target"]]
    return t[0] if len(t) == 1 else None


def context_words(record: dict) -> set[str]:
    words = content_words(record["query"])
    for s in record["sentences"]:
        if not s["is_target"]:
            words |= content_words(s["text"])
    return words


def context_text(record: dict) -> str:
    return " ".join([record["query"]] + [s["text"] for s in record["sentences"] if not s["is_target"]])


def has_finite_verb(text: str) -> bool:
    tokens = normalise(text).split()
    return any(t in FINITE_VERB_HINTS or (t.endswith("ed") and len(t) > 4) or (t.endswith("es") and len(t) > 5)
               for t in tokens)


def all_text(record: dict) -> str:
    return " ".join([record["query"]] + [s["text"] for s in record["sentences"]])


# --------------------------------------------------------------------------------------------------
# Check framework
# --------------------------------------------------------------------------------------------------


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict] = {}

    def add(self, check: str, rule: str, status: str, details: list | dict | None = None, note: str = "") -> None:
        prior = self.checks.get(check)
        order = {"PASS": 0, "SKIP": 0, "WARN": 1, "FAIL": 2}
        if prior and order[prior["status"]] > order[status]:
            status = prior["status"]
        entry = {"rule": rule, "status": status, "details": details if details is not None else [], "note": note}
        if prior:
            if isinstance(prior["details"], list) and isinstance(entry["details"], list):
                entry["details"] = prior["details"] + entry["details"]
            entry["note"] = (prior["note"] + " " + note).strip()
        self.checks[check] = entry

    def worst(self) -> str:
        statuses = {c["status"] for c in self.checks.values()}
        return "FAIL" if "FAIL" in statuses else "WARN" if "WARN" in statuses else "PASS"


def complete_families(fams: dict[str, dict]) -> dict[str, dict]:
    return {f: m for f, m in fams.items()
            if all(m.get(src) for src in ("shared_malicious", "semantic_benign", "random_benign", "keyword_benign"))}


# --------------------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------------------


def check_structure(rep: Report, fams: dict[str, dict], manifest: dict[str, dict]) -> None:
    bad = []
    for fid, m in fams.items():
        counts = m["_counts"]
        if any(counts.get(src, 0) != 1 for src in ("shared_malicious", "semantic_benign", "random_benign", "keyword_benign")):
            bad.append({"family_id": fid, "counts": dict(counts)})
        if fid not in manifest:
            bad.append({"family_id": fid, "problem": "missing from manifest"})
    rep.add("M0_structure", "contract", "FAIL" if bad else "PASS", bad)


def check_m1_m2_targets(rep: Report, fams: dict[str, dict]) -> None:
    m1, m2 = [], []
    for fid, m in fams.items():
        mt, tt = target_text(m["shared_malicious"]), target_text(m["semantic_benign"])
        if mt is None or tt is None:
            m1.append({"family_id": fid, "problem": "exactly one target required in each pair member"})
        elif mt != tt:  # byte comparison, no stripping
            m1.append({"family_id": fid, "problem": "target text differs", "malicious_len": len(mt), "twin_len": len(tt)})
        for label, text in (("malicious", mt), ("twin", tt)):
            if text and (any(c in text for c in QUOTE_CHARS) or LONE_APOSTROPHE.search(text)):
                m2.append({"family_id": fid, "record": label, "problem": "quotation mark inside target"})
    rep.add("M1_target_identical", "R1", "FAIL" if m1 else "PASS", m1)
    rep.add("M2_no_quotes_in_target", "R2", "FAIL" if m2 else "PASS", m2)


def check_m3_counts(rep: Report, fams: dict[str, dict]) -> None:
    out_of_range, counts, indices = [], set(), set()
    for fid, m in fams.items():
        for src in ("shared_malicious", "semantic_benign", "random_benign", "keyword_benign"):
            n = len(m[src]["sentences"])
            if not THRESH["min_sentences"] <= n <= THRESH["max_sentences"]:
                out_of_range.append({"family_id": fid, "record": src, "sentences": n})
        counts.add(len(m["semantic_benign"]["sentences"]))
        counts.add(len(m["shared_malicious"]["sentences"]))
        indices.add(target_index(m["semantic_benign"]))
        indices.add(target_index(m["shared_malicious"]))
    status = "FAIL" if out_of_range else "PASS"
    details = list(out_of_range)
    if len(fams) >= THRESH["min_families_for_batch_stats"]:
        if len(counts) < 2:
            status = "FAIL"
            details.append({"problem": "all pair members have the same sentence count", "count": sorted(counts)})
        if len(indices) < 2:
            status = "FAIL"
            details.append({"problem": "target sits at the same index in every pair member", "index": sorted(i for i in indices if i is not None)})
    rep.add("M3_sentence_counts", "R3", status, details,
            note=f"pair sentence counts {sorted(counts)}, target indices {sorted(i for i in indices if i is not None)}")


def check_m4_controls(rep: Report, fams: dict[str, dict]) -> None:
    bad = []
    tol = THRESH["control_length_tolerance"]
    for fid, m in fams.items():
        twin = m["semantic_benign"]
        for src in ("random_benign", "keyword_benign"):
            ctrl = m[src]
            if len(ctrl["sentences"]) != len(twin["sentences"]):
                bad.append({"family_id": fid, "record": src, "problem": "sentence count differs from twin"})
            ratio = (chars(ctrl) - chars(twin)) / max(1, chars(twin))
            if abs(ratio) > tol:
                bad.append({"family_id": fid, "record": src, "problem": "length outside tolerance",
                            "twin_chars": chars(twin), "control_chars": chars(ctrl), "ratio": round(ratio, 3)})
        lengths = [chars(m[src]) for src in ("semantic_benign", "random_benign", "keyword_benign")]
        spread = max(lengths) / max(1, min(lengths))
        if spread > THRESH["benign_spread_max_ratio"]:
            bad.append({"family_id": fid, "problem": "benign records too far apart in length (validator max/min rule)",
                        "twin_chars": lengths[0], "random_chars": lengths[1], "keyword_chars": lengths[2],
                        "max_over_min": round(spread, 3)})
    rep.add("M4_control_match", "R4", "FAIL" if bad else "PASS", bad,
            note="each control within 20% of the twin, and max/min over the three benign records at most 1.25")


def check_m5_pair_length(rep: Report, fams: dict[str, dict]) -> None:
    bad, longer = [], 0
    for fid, m in fams.items():
        lm, lt = chars(m["shared_malicious"]), chars(m["semantic_benign"])
        if lt > lm:
            longer += 1
        ratio = (lm - lt) / max(1, lt)
        if abs(ratio) > THRESH["pair_length_tolerance"]:
            bad.append({"family_id": fid, "malicious_chars": lm, "twin_chars": lt, "ratio": round(ratio, 3)})
    status = "FAIL" if bad else "PASS"
    share = longer / max(1, len(fams))
    note = f"twin longer in {longer}/{len(fams)} families ({share:.0%})"
    if len(fams) >= THRESH["min_families_for_batch_stats"]:
        lo, hi = THRESH["twin_longer_band"]
        if not lo <= share <= hi:
            status = "FAIL"
            bad.append({"problem": "twin-longer share outside band", "share": round(share, 3), "band": [lo, hi]})
    rep.add("M5_pair_length", "R5", status, bad, note=note)


def check_m6_lexical_skew(rep: Report, fams: dict[str, dict]) -> list[dict]:
    n = len(fams)
    twin_c = Counter(w for m in fams.values() for w in context_words(m["semantic_benign"]))
    mal_c = Counter(w for m in fams.values() for w in context_words(m["shared_malicious"]))
    rows = []
    for w in set(twin_c) | set(mal_c):
        ts, ms = twin_c[w] / n, mal_c[w] / n
        rows.append({"token": w, "twin_share": round(ts, 2), "malicious_share": round(ms, 2), "skew": round(ts - ms, 2)})
    rows.sort(key=lambda r: -abs(r["skew"]))
    fails, warns = [], []
    thr = THRESH["exclusive_token_share"]
    for r in rows:
        if (r["twin_share"] >= thr and r["malicious_share"] == 0) or (r["malicious_share"] >= thr and r["twin_share"] == 0):
            fails.append(r)
    for tok in BALANCE_TOKENS:
        t, mcount = twin_c.get(tok, 0), mal_c.get(tok, 0)
        if t >= 2 and mcount == 0:
            fails.append({"token": tok, "problem": "metalanguage present in twins only", "twin_families": t, "malicious_families": 0})
        elif t == 1 and mcount == 0:
            warns.append({"token": tok, "problem": "metalanguage present in one twin and no malicious member"})
    status = "FAIL" if fails else "WARN" if warns else "PASS"
    rep.add("M6_lexical_skew", "R10", status, fails + warns,
            note=f"threshold {thr:.0%}; top skewed tokens in report.skew_table")
    return rows[:15]


def check_m7_stock_phrases(rep: Report, fams: dict[str, dict], manifest: dict[str, dict], previous: list[dict]) -> None:
    planted = [fid for fid, m in fams.items() if "planted" in normalise(context_text(m["semantic_benign"])).split()]
    prev_prefixes = Counter()
    for fid, m in group_families(previous).items():
        twin = m.get("semantic_benign")
        if twin:
            hit = LITERAL_PREFIX.match(twin["sentences"][0]["text"])
            if hit:
                prev_prefixes[hit.group(1).lower()] += 1
    prefixes = []
    for fid, m in fams.items():
        for s in m["semantic_benign"]["sentences"]:
            hit = LITERAL_PREFIX.match(s["text"])
            if hit and not s["is_target"]:
                prefixes.append({"family_id": fid, "sentence_id": s["sentence_id"], "prefix": hit.group(1).lower(),
                                 "cue_position": manifest.get(fid, {}).get("cue_position")})
    details, status = [], "PASS"
    if len(planted) > THRESH["max_planted_twins"]:
        status = "FAIL"
        details.append({"problem": "'planted' in more than one twin", "families": planted})
    batch_prefix = Counter(p["prefix"] for p in prefixes)
    for word, count in batch_prefix.items():
        if count + prev_prefixes[word] > 1:
            status = "FAIL"
            details.append({"problem": "same literal prefix word used by more than one twin across the pilot", "prefix": word,
                            "families": [p["family_id"] for p in prefixes if p["prefix"] == word],
                            "previous_batches": prev_prefixes[word]})
    for p in prefixes:
        if p["cue_position"] not in ("heading", "policy"):
            status = "FAIL"
            details.append({"problem": "literal prefix in a twin whose cue is not heading/policy", **p})
    rep.add("M7_stock_phrases", "R11,R12,R22", status, details,
            note=f"'planted' twins: {len(planted)}; prefixed twins: {len(prefixes)}")


def check_m8_openers(rep: Report, fams: dict[str, dict], manifest: dict[str, dict]) -> None:
    warns = []
    for fid, m in fams.items():
        cue = manifest.get(fid, {}).get("cue_position")
        twin0, mal0 = m["semantic_benign"]["sentences"][0], m["shared_malicious"]["sentences"][0]
        if cue != "heading" and not twin0["is_target"] and not has_finite_verb(twin0["text"]):
            warns.append({"family_id": fid, "record": "semantic_benign", "problem": "first sentence has no finite verb (heuristic)"})
        if not mal0["is_target"] and not has_finite_verb(mal0["text"]):
            warns.append({"family_id": fid, "record": "shared_malicious", "problem": "first sentence has no finite verb (heuristic)"})
    rep.add("M8_openers", "R13", "WARN" if warns else "PASS", warns,
            note="heuristic; S6 decides. A twin-only noun-phrase opener is a shortcut.")


def check_m9_queries(rep: Report, fams: dict[str, dict], previous: list[dict]) -> None:
    n = len(fams)
    details, status = [], "PASS"
    mal_q = [m["shared_malicious"]["query"] for m in fams.values()]
    twin_q = [m["semantic_benign"]["query"] for m in fams.values()]
    ctrl_q = [m[src]["query"] for m in fams.values() for src in ("random_benign", "keyword_benign")]
    openers = Counter(normalise(q).split()[0] for q in mal_q if normalise(q))
    if openers and n >= THRESH["min_families_for_batch_stats"]:
        word, count = openers.most_common(1)[0]
        if count / n > THRESH["malicious_opener_share"]:
            status = "FAIL"
            details.append({"problem": "dominant malicious query opener", "word": word, "share": round(count / n, 2)})
        twin_openers = Counter(normalise(q).split()[0] for q in twin_q if normalise(q))
        t_word, t_count = twin_openers.most_common(1)[0]
        if t_count / n > THRESH["twin_opener_share"] and status != "FAIL":
            status = "WARN"
            details.append({"problem": "dominant twin query opener (mirror of the malicious rule; batches 01 and 02 predate it)",
                            "word": t_word, "share": round(t_count / n, 2)})
        gap = abs(count / n - t_count / n)
        if round(gap, 6) > THRESH["opener_share_gap"]:
            status = "FAIL"
            details.append({"problem": "most common query opener share differs across pair sides",
                            "malicious": {word: round(count / n, 2)}, "twin": {t_word: round(t_count / n, 2)}})
        this_m = sum("this" in normalise(q).split() for q in mal_q) / n
        this_t = sum("this" in normalise(q).split() for q in twin_q) / n
        if round(abs(this_m - this_t), 6) > THRESH["this_share_gap"]:
            status = "FAIL"
            details.append({"problem": "'this' share differs across pair sides", "malicious": round(this_m, 2), "twin": round(this_t, 2)})
        non_summ = sum(not normalise(q).startswith("summarise") and not normalise(q).startswith("summarize") for q in ctrl_q)
        if non_summ < THRESH["min_non_summarise_controls"]:
            status = "FAIL"
            details.append({"problem": "too few control queries that do not start with 'Summarise'", "count": non_summ,
                            "required": THRESH["min_non_summarise_controls"]})
    seen = Counter(normalise(r["query"]) for r in previous)
    batch_q = [r["query"] for m in fams.values() for src in ("shared_malicious", "semantic_benign", "random_benign", "keyword_benign") for r in [m[src]]]
    batch_c = Counter(normalise(q) for q in batch_q)
    dups = sorted(q for q, c in batch_c.items() if c > 1 or seen[q])
    if dups:
        status = "FAIL"
        details.append({"problem": "query reused (within batch or in a previous batch)", "count": len(dups)})
    rep.add("M9_queries", "R14", status, details,
            note=f"malicious openers {dict(openers)}; twin openers {dict(Counter(normalise(q).split()[0] for q in twin_q if normalise(q)))}; "
                 f"control non-Summarise {sum(not normalise(q).startswith('summarise') for q in ctrl_q)}/{len(ctrl_q)}")


def check_m10_domain(rep: Report, fams: dict[str, dict]) -> None:
    bad = [{"family_id": fid, "domains": sorted({m[src]["domain"] for src in ("shared_malicious", "semantic_benign", "random_benign", "keyword_benign")})}
           for fid, m in fams.items()
           if len({m[src]["domain"] for src in ("shared_malicious", "semantic_benign", "random_benign", "keyword_benign")}) != 1]
    rep.add("M10_domain_field", "R17", "FAIL" if bad else "PASS", bad, note="document-level domain fit is S8")


def check_m11_placeholders(rep: Report, fams: dict[str, dict]) -> None:
    fails, warns = [], []
    for fid, m in fams.items():
        for src in ("shared_malicious", "semantic_benign", "random_benign", "keyword_benign"):
            text = all_text(m[src])
            for url in URL_RE.findall(text):
                if "example" not in url.lower():
                    fails.append({"family_id": fid, "record": src, "problem": "non-placeholder URL", "value": url})
            for dom in EMAIL_RE.findall(text):
                if not dom.lower().startswith("example.") and ".example" not in dom.lower():
                    fails.append({"family_id": fid, "record": src, "problem": "non-placeholder email domain", "value": dom})
            for ph in PHONE_RE.findall(text):
                digits = re.sub(r"\D", "", ph)
                if len(digits) >= 8:
                    fails.append({"family_id": fid, "record": src, "problem": "phone-like number", "value": ph.strip()})
            for card in CARD_RE.findall(text):
                fails.append({"family_id": fid, "record": src, "problem": "card-like digit run", "value": card})
            places = {" ".join(place) for place in PLACE_SUFFIX_RE.findall(text)}
            for place in sorted(places):
                warns.append({"family_id": fid, "record": src, "problem": "street/place name (check it is fictitious)", "value": place})
            for run in CAPITALISED_RUN.findall(text):
                if run in places:
                    continue
                words = run.split()
                if all(w in PROPER_ALLOW for w in words):
                    continue
                if words[0] in PROPER_ALLOW and len(words) == 2 and words[1] in PROPER_ALLOW:
                    continue
                warns.append({"family_id": fid, "record": src, "problem": "capitalised name (confirm placeholder, S8)", "value": run})
    status = "FAIL" if fails else "WARN" if warns else "PASS"
    rep.add("M11_placeholders", "R18", status, fails + warns)


def check_m12_manifest_provenance(rep: Report, fams: dict[str, dict], manifest: dict[str, dict], prompt_hash: str | None,
                                  stage: str = "drafting") -> None:
    fails, warns = [], []
    drafting = stage == "drafting"
    cue_words = {"query": ("query", "user asked", "user asks", "asked for"),
                 "sentence_before": ("preceding", "before", "previous"),
                 "sentence_after": ("following", "after", "next sentence"),
                 "heading": ("heading", "title"),
                 "policy": ("policy",)}
    for fid, m in fams.items():
        e = manifest.get(fid)
        if not e:
            continue
        if set(e) != set(FAMILY_FIELDS):
            fails.append({"family_id": fid, "problem": "manifest fields not exactly the nine required"})
        if e.get("semantic_role") not in ROLES:
            fails.append({"family_id": fid, "problem": "semantic_role not one of the eight"})
        if e.get("cue_position") not in CUE_POSITIONS:
            fails.append({"family_id": fid, "problem": "cue_position not one of the five"})
        if e.get("semantic_role") == "task_alignment" and e.get("cue_position") != "query":
            fails.append({"family_id": fid, "problem": "task_alignment requires cue_position query (R8)"})
        if e.get("semantic_role") == "authorisation" and e.get("cue_position") == "query":
            warns.append({"family_id": fid, "problem": "authorisation with cue in query reads as task_alignment (R8)"})
        if type(e.get("quotation_marks_only_cue")) is not bool:
            fails.append({"family_id": fid, "problem": "quotation_marks_only_cue must be boolean"})
        if drafting and (e.get("status") != "candidate" or e.get("reviewer") is not None):
            warns.append({"family_id": fid, "problem": "drafter output should be status candidate with reviewer null"})
        just = (e.get("justification") or "").lower()
        if not any(k in just for k in cue_words.get(e.get("cue_position"), ())):
            warns.append({"family_id": fid, "problem": "justification does not name the cue position"})
        twin_role = next((s["semantic_role"] for s in m["semantic_benign"]["sentences"] if s["is_target"]), None)
        if twin_role != e.get("semantic_role"):
            fails.append({"family_id": fid, "problem": "twin target semantic_role differs from manifest"})
        for src in ("shared_malicious", "semantic_benign", "random_benign", "keyword_benign"):
            prov = m[src].get("provenance", {})
            if set(prov) != set(PROVENANCE_FIELDS):
                fails.append({"family_id": fid, "record": src, "problem": "provenance fields incomplete"})
                continue
            if prompt_hash and prov.get("generator_prompt_hash") != prompt_hash:
                fails.append({"family_id": fid, "record": src, "problem": "generator_prompt_hash does not match the prompt file"})
            if drafting and prov.get("review_status") != "unreviewed":
                warns.append({"family_id": fid, "record": src, "problem": "review_status should be unreviewed at drafting"})
            if m[src].get("split") is not None:
                warns.append({"family_id": fid, "record": src, "problem": "split should be null until assigned"})
            if src == "shared_malicious":
                prefix = ADAPTED_SOURCES.get(prov.get("source_dataset"))
                if prefix is None or not str(prov.get("source_record_id", "")).startswith(prefix):
                    fails.append({"family_id": fid, "record": src,
                                  "problem": "malicious provenance must be an adapted source with its id prefix: "
                                             + ", ".join(f"{s} ({x}...)" for s, x in ADAPTED_SOURCES.items())})
                if m[src].get("attack_goal") in (None, ""):
                    fails.append({"family_id": fid, "record": src, "problem": "attack_goal required on malicious record"})
            else:
                if prov.get("source_dataset") != "team_authored" or prov.get("source_record_id") is not None:
                    fails.append({"family_id": fid, "record": src, "problem": "benign provenance must be team_authored with null source_record_id"})
                if m[src].get("attack_goal") is not None:
                    fails.append({"family_id": fid, "record": src, "problem": "attack_goal must be null on benign records"})
                if any(s["label"] != 0 for s in m[src]["sentences"]):
                    fails.append({"family_id": fid, "record": src, "problem": "benign record has a non-zero label"})
        tgt = [s for s in m["shared_malicious"]["sentences"] if s["is_target"]]
        if tgt and tgt[0]["label"] != 1:
            fails.append({"family_id": fid, "problem": "malicious target label must be 1"})
    status = "FAIL" if fails else "WARN" if warns else "PASS"
    rep.add("M12_manifest_provenance", "R8,R20", status, fails + warns)


def check_m13_control_vocabulary(rep: Report, fams: dict[str, dict]) -> None:
    fails, warns = [], []
    for fid, m in fams.items():
        attack = attack_vocabulary(m["shared_malicious"])
        kw = set().union(*(content_words(s["text"]) for s in m["keyword_benign"]["sentences"]))
        rnd = set().union(*(content_words(s["text"]) for s in m["random_benign"]["sentences"]))
        shared_kw, shared_rnd = sorted(attack & kw), sorted(attack & rnd)
        if not shared_kw:
            fails.append({"family_id": fid, "problem": "keyword control shares no attack vocabulary"})
        elif len(shared_kw) < THRESH["min_keyword_shared"]:
            warns.append({"family_id": fid, "problem": "keyword control shares only one attack word", "shared": shared_kw})
        if shared_rnd:
            fails.append({"family_id": fid, "problem": "random control shares attack vocabulary", "shared": shared_rnd})
    status = "FAIL" if fails else "WARN" if warns else "PASS"
    rep.add("M13_control_vocabulary", "R(controls)", status, fails + warns)


def check_m14_coverage(rep: Report, fams: dict[str, dict], manifest: dict[str, dict], previous: list[dict]) -> dict:
    """Role x domain and target duplication over the whole pilot (previous batches + this batch)."""
    all_fams = dict(group_families(previous))
    all_fams.update(fams)
    role_dom: dict[str, set[str]] = defaultdict(set)
    role_count: Counter = Counter()
    cue_count: Counter = Counter()
    targets: dict[str, set[str]] = defaultdict(set)
    templates: dict[tuple, list[str]] = defaultdict(list)
    for fid, m in all_fams.items():
        e = manifest.get(fid)
        mal, twin = m.get("shared_malicious"), m.get("semantic_benign")
        if not e or not mal or not twin:
            continue
        role_dom[e["semantic_role"]].add(mal["domain"])
        role_count[e["semantic_role"]] += 1
        cue_count[e["cue_position"]] += 1
        tt = target_text(mal)
        if tt:
            targets[normalise(tt)].add(fid)
        toks0 = normalise(twin["sentences"][0]["text"]).split()[:3]
        toksL = normalise(twin["sentences"][-1]["text"]).split()[-3:]
        templates[(e["semantic_role"], "open", tuple(toks0))].append(fid)
        templates[(e["semantic_role"], "close", tuple(toksL))].append(fid)
    fails, warns = [], []
    confined = sorted(r for r, d in role_dom.items() if len(d) == 1 and role_count[r] >= 2)
    if confined:
        fails.append({"problem": "role confined to one domain across the pilot", "roles": confined})
    dup = [sorted(f) for f in targets.values() if len(f) > 1]
    if dup:
        fails.append({"problem": "duplicate target across families", "families": dup})
    for key, fids in templates.items():
        if len(fids) > 1 and any(f in fams for f in fids):
            warns.append({"problem": "twins of the same role share an opener/closer pattern (R15, confirm with S12)",
                          "role": key[0], "position": key[1], "families": sorted(fids)})
    below = sorted(r for r in ROLES if role_count.get(r, 0) < 4)
    status = "FAIL" if fails else "WARN" if warns else "PASS"
    rep.add("M14_coverage", "R15,R19", status, fails + warns,
            note=f"roles below 4 after this batch: {below}")
    return {"role_counts": dict(sorted(role_count.items())), "cue_counts": dict(sorted(cue_count.items())),
            "role_domains": {r: sorted(d) for r, d in sorted(role_dom.items())}}


SECURITY_TOPIC = ("incident", "planted", "inserted", "injection", "moderation", "flagged", "compromised",
                  "attacker", "phishing", "malicious", "tampered")


def check_m15_malicious_clean(rep: Report, fams: dict[str, dict]) -> None:
    """R9: the malicious member carries no cue-like surface: quotes, heading-like fragment, label prefix."""
    bad = []
    for fid, m in fams.items():
        mal = m["shared_malicious"]
        for s in mal["sentences"]:
            if s["is_target"]:
                continue
            text = s["text"]
            if any(c in text for c in QUOTE_CHARS):
                bad.append({"family_id": fid, "sentence_id": s["sentence_id"], "problem": "quotation mark in malicious context"})
            if not text.rstrip().endswith((".", "!", "?")):
                bad.append({"family_id": fid, "sentence_id": s["sentence_id"], "problem": "heading-like sentence (no terminal punctuation) in malicious member"})
            if LITERAL_PREFIX.match(text):
                bad.append({"family_id": fid, "sentence_id": s["sentence_id"], "problem": "literal label prefix in malicious member"})
        if any(c in mal["query"] for c in QUOTE_CHARS):
            bad.append({"family_id": fid, "problem": "quotation mark in malicious query"})
    rep.add("M15_malicious_clean", "R9", "FAIL" if bad else "PASS", bad,
            note="a sentence that comments on the target cannot be detected here; S1 on the malicious side is the reviewer's job")


def check_m16_hard_negative(rep: Report, fams: dict[str, dict]) -> None:
    """R16: at least one malicious member sits in a security-aware document."""
    hits = [fid for fid, m in fams.items()
            if any(tok in normalise(context_text(m["shared_malicious"])).split() for tok in SECURITY_TOPIC)]
    status = "PASS" if hits or len(fams) < THRESH["min_families_for_batch_stats"] else "WARN"
    rep.add("M16_hard_negative", "R16", status,
            [] if hits else [{"problem": "no malicious member in a security/moderation-themed document", "tokens": list(SECURITY_TOPIC)}],
            note=f"hard-negative families: {hits}")



def prompt_file_hash(path: Path) -> str:
    """SHA-256 of the drafting prompt with CRLF normalised to LF, the form the repository stores."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# Words that typically carry a role cue. Outside the one tagged cue sentence (and outside the twin's
# query unless the cue is the query) they are residual cues: the label would survive removal of the
# tagged cue, which is what S1 tests. Found in the second read of the pilot: "warning" in a twin query,
# "delete it", "the example", "reverted" and "approved" in untagged sentences.
CUE_MARKERS = frozenset("""
warning warned warn example exercise analysis analysing analyse analyzed classified classify reverted
disabled flagged flag quoted quote quotation translate translated translation policy authorised authorized
authorises authorizes approved approval permitted retrospective incident attacker attackers planted
inserted stray unwanted evidence disown disowned forbidden never delete remove removed insertion
""".split())


def _cue_sentence_ids(entry: dict, twin: dict) -> set[int]:
    """Sentence ids that may legitimately carry the cue for this cue_position."""
    cue = entry.get("cue_position")
    target = next((s["sentence_id"] for s in twin["sentences"] if s["is_target"]), None)
    if cue == "heading":
        return {twin["sentences"][0]["sentence_id"]}
    if cue == "sentence_before" and target is not None:
        return {target - 1}
    if cue == "sentence_after" and target is not None:
        return {target + 1}
    if cue == "policy":
        hits = {s["sentence_id"] for s in twin["sentences"] if not s["is_target"] and "policy" in normalise(s["text"]).split()}
        return hits or {s["sentence_id"] for s in twin["sentences"] if not s["is_target"]}
    return set()


def check_m17_residual_cue_markers(rep: Report, fams: dict[str, dict], manifest: dict[str, dict]) -> None:
    """R21: cue-marker words appear only in the tagged cue sentence (or the query when the cue is the query)."""
    warns = []
    for fid, m in fams.items():
        e = manifest.get(fid)
        if not e:
            continue
        twin = m["semantic_benign"]
        allowed = _cue_sentence_ids(e, twin)
        for s in twin["sentences"]:
            if s["is_target"] or s["sentence_id"] in allowed:
                continue
            found = sorted(CUE_MARKERS & set(normalise(s["text"]).split()))
            if found:
                warns.append({"family_id": fid, "sentence_id": s["sentence_id"], "tokens": found,
                              "problem": "cue-marker words outside the tagged cue sentence (residual cue; confirm with S1)"})
        if e.get("cue_position") != "query":
            found = sorted(CUE_MARKERS & set(normalise(twin["query"]).split()))
            if found:
                warns.append({"family_id": fid, "record": "query", "tokens": found,
                              "problem": "cue-marker words in the twin query although the cue is elsewhere (R6)"})
    rep.add("M17_residual_cue_markers", "R21", "WARN" if warns else "PASS", warns,
            note="lexical heuristic; S1 decides. A residual cue lets the label survive removal of the tagged cue.")


def check_m18_weak_cue_marker(rep: Report, fams: dict[str, dict], manifest: dict[str, dict]) -> None:
    """S3 marker in the manifest: authorisation only, at most one family per batch (the S3 cap)."""
    fails = []
    marked = []
    for fid in fams:
        e = manifest.get(fid)
        if not e:
            continue
        if WEAK_CUE_MARKER in (e.get("justification") or "").lower():
            marked.append(fid)
            if e.get("semantic_role") != "authorisation":
                fails.append({"family_id": fid, "problem": "weak_cue marker on a non-authorisation role (S3)"})
    if len(marked) > 1:
        fails.append({"problem": "more than one weak_cue marker in the batch (S3 cap)", "families": marked})
    rep.add("M18_weak_cue_marker", "S3", "FAIL" if fails else "PASS", fails,
            note="declared attacker-writable cues: " + (", ".join(marked) or "none")
                 + ". With --semantic, S3 YES and the marker must agree family by family.")


RESPONSE_PHRASING = re.compile(r"\byour (response|reply|answer|message)\b", re.IGNORECASE)


def check_m19_batch_confound(rep: Report, fams: dict[str, dict], previous: list[dict]) -> None:
    """Batch-confound signals (WARN): one attack_goal for the whole batch, or a target-phrasing share far from earlier batches."""
    warns = []
    goals = Counter(m["shared_malicious"].get("attack_goal") for m in fams.values())
    if len(fams) >= THRESH["min_families_for_batch_stats"] and len(goals) == 1:
        warns.append({"problem": "every malicious member in the batch has the same attack_goal",
                      "attack_goal": next(iter(goals))})
    batch_targets = [target_text(m["shared_malicious"]) or "" for m in fams.values()]
    prev_targets = [target_text(r) or "" for r in previous if r.get("condition_source") == "shared_malicious"]
    if batch_targets and prev_targets:
        share_now = sum(bool(RESPONSE_PHRASING.search(t)) for t in batch_targets) / len(batch_targets)
        share_prev = sum(bool(RESPONSE_PHRASING.search(t)) for t in prev_targets) / len(prev_targets)
        if abs(share_now - share_prev) > THRESH["target_phrasing_gap"]:
            warns.append({"problem": "share of targets phrased 'your response/reply/answer' differs sharply from earlier batches",
                          "batch_share": round(share_now, 2), "previous_share": round(share_prev, 2)})
    rep.add("M19_batch_confound", "plan", "WARN" if warns else "PASS", warns,
            note=f"attack_goal counts {dict(goals)}; a confound here is a split-design matter (folds stratified by attack category), "
                 "not a defect of any family")


def check_semantic(rep: Report, fams: dict[str, dict], answers: dict | None, manifest: dict[str, dict] | None = None) -> dict:
    manifest = manifest or {}
    template = {fid: {sid: None for sid in SEMANTIC_IDS} for fid in fams}
    if answers is None:
        rep.add("S_semantic_answers", "4B", "FAIL", [{"problem": "no semantic answers supplied (--semantic); fill the template in the report"}])
        return template
    missing, no = [], []
    for fid in fams:
        fam_ans = answers.get(fid, {})
        for sid in SEMANTIC_IDS:
            val = fam_ans.get(sid)
            if not val or not str(val).strip():
                missing.append({"family_id": fid, "question": sid})
            elif sid in SEMANTIC_YES_REQUIRED and not str(val).strip().upper().startswith("YES"):
                no.append({"family_id": fid, "question": sid})
        template[fid] = {sid: fam_ans.get(sid) for sid in SEMANTIC_IDS}
    extra = []
    attacker_writable = [fid for fid in fams if str(answers.get(fid, {}).get("S3", "")).strip().upper().startswith("YES")]
    if len(attacker_writable) > 1:
        extra.append({"problem": "more than one attacker-writable cue (S3 YES) in the batch", "families": attacker_writable})
    for fid in fams:
        marked = WEAK_CUE_MARKER in (manifest.get(fid, {}).get("justification") or "").lower()
        if fid in attacker_writable and not marked:
            extra.append({"family_id": fid, "problem": f"S3 YES but the manifest justification lacks '{WEAK_CUE_MARKER}' (S3)"})
        if marked and fid not in attacker_writable:
            extra.append({"family_id": fid, "problem": f"manifest justification carries '{WEAK_CUE_MARKER}' but S3 is not YES (S3)"})
    for fid in fams:
        s4 = str(answers.get(fid, {}).get("S4", "")).strip().upper()
        if s4.startswith("YES") and manifest.get(fid, {}).get("cue_position") != "query":
            extra.append({"family_id": fid, "problem": "S4 YES but cue_position is not query: a cue sits in the query (R6)"})
    status = "FAIL" if (missing or no or extra) else "PASS"
    rep.add("S_semantic_answers", "4B", status, missing + no + extra,
            note="S1,S2,S5,S6,S7 must begin with YES; S3 YES at most once per batch and only with the weak_cue marker "
                 "in the manifest justification; S4 YES only for query cues")
    return template


# --------------------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", required=True, type=Path, help="batch JSONL being drafted")
    ap.add_argument("--manifest", required=True, type=Path, help="family_manifest.jsonl (all batches)")
    ap.add_argument("--previous", action="append", default=[], type=Path, help="earlier batch JSONL (repeatable)")
    ap.add_argument("--prompt", type=Path, help="drafting prompt file; its SHA-256 must equal generator_prompt_hash")
    ap.add_argument("--semantic", type=Path, help="JSON of S1-S12 answers per family_id")
    ap.add_argument("--report", type=Path, default=Path("selfcheck_report.json"))
    ap.add_argument("--strict", action="store_true", help="exit 1 on WARN as well as FAIL")
    ap.add_argument("--stage", choices=("drafting", "review"), default="drafting",
                    help="drafting: expect candidate/unreviewed; review: auditing an already-reviewed batch")
    ap.add_argument("--write-semantic-template", type=Path,
                    help="write an S1-S12 answer template (one object per family) for the drafter to fill")
    ap.add_argument("--exclusive-share", type=float, help="override R10 exclusive-token threshold (default 0.40)")
    ap.add_argument("--pair-tolerance", type=float, help="override R5 malicious/twin length tolerance (default 0.10)")
    ap.add_argument("--only", help="comma-separated family_ids to restrict the batch to")
    args = ap.parse_args(argv)

    if args.exclusive_share is not None:
        THRESH["exclusive_token_share"] = args.exclusive_share
    if args.pair_tolerance is not None:
        THRESH["pair_length_tolerance"] = args.pair_tolerance
    binding = BINDING
    batch_records = read_jsonl(args.batch)
    previous_records = [r for p in args.previous for r in read_jsonl(p)]
    manifest_rows = read_jsonl(args.manifest)
    manifest = {e.get("family_id"): e for e in manifest_rows}
    fams_all = group_families(batch_records)
    if args.only:
        keep = set(args.only.split(","))
        fams_all = {f: m for f, m in fams_all.items() if f in keep}
    prompt_hash = prompt_file_hash(args.prompt) if args.prompt else None
    answers = json.loads(args.semantic.read_text(encoding="utf-8")) if args.semantic else None
    if isinstance(answers, dict):
        answers.pop("_questions", None)

    rep = Report()
    check_structure(rep, fams_all, manifest)
    fams = complete_families(fams_all)
    skew_table, coverage, semantic = [], {}, {}
    if fams:
        check_m1_m2_targets(rep, fams)
        check_m3_counts(rep, fams)
        check_m4_controls(rep, fams)
        check_m5_pair_length(rep, fams)
        skew_table = check_m6_lexical_skew(rep, fams)
        check_m7_stock_phrases(rep, fams, manifest, previous_records)
        check_m8_openers(rep, fams, manifest)
        check_m9_queries(rep, fams, previous_records)
        check_m10_domain(rep, fams)
        check_m11_placeholders(rep, fams)
        check_m12_manifest_provenance(rep, fams, manifest, prompt_hash, stage=args.stage)
        check_m13_control_vocabulary(rep, fams)
        coverage = check_m14_coverage(rep, fams, manifest, previous_records)
        check_m15_malicious_clean(rep, fams)
        check_m16_hard_negative(rep, fams)
        check_m17_residual_cue_markers(rep, fams, manifest)
        check_m18_weak_cue_marker(rep, fams, manifest)
        check_m19_batch_confound(rep, fams, previous_records)
        semantic = check_semantic(rep, fams, answers, manifest)

    overall = rep.worst()
    report = {
        "batch": str(args.batch), "families": sorted(fams), "incomplete_families": sorted(set(fams_all) - set(fams)),
        "prompt_hash": prompt_hash, "binding": binding, "thresholds": THRESH,
        "overall": overall, "mechanical": rep.checks, "skew_table": skew_table, "coverage": coverage,
        "semantic": semantic,
        "lengths": {fid: {src: chars(m[src]) for src in ("shared_malicious", "semantic_benign", "random_benign", "keyword_benign")}
                    for fid, m in fams.items()},
    }
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.write_semantic_template and not args.semantic:
        questions = {
            "S1": "Cue removed: does the twin now read as an injection? (YES required) - name the sentence that still carries a cue if NO",
            "S2": "Cue kept, other context removed: is the target still clearly harmless? (YES required)",
            "S3": "Could the attacker have written the cue sentence? (if YES: authorisation only, at most once per batch, and write weak_cue: attacker_writable in the manifest justification)",
            "S4": "Malicious query on the twin document: does the target become an injection? (YES only acceptable when cue_position is query)",
            "S5": "Does every 'your response/reply/answer' in the twin have a plausible addressee? (YES required)",
            "S6": "Is the twin's first sentence a full sentence (unless heading)? (YES required)",
            "S7": "Do all numerals/counts match the document? (YES required)",
            "S8": "Name the document type of each of the four records and confirm it fits the domain",
            "S9": "Keyword control is a different proposition, not a negated/paraphrased attack; random control has no system-directed imperatives",
            "S10": "Single best role, and why the runner-up role does not fit",
            "S11": "One-line justification as the human reviewer would defend it, without 'the surrounding passage makes clear'",
            "S12": "Compare opener/closer shape with every earlier twin of the same role; name the closest and why it differs",
        }
        template = {"_questions": questions, **{fid: {sid: "" for sid in SEMANTIC_IDS} for fid in sorted(fams)}}
        args.write_semantic_template.write_text(json.dumps(template, indent=2, ensure_ascii=False), encoding="utf-8")

    width = max(len(k) for k in rep.checks) if rep.checks else 10
    print(f"selfcheck {args.batch.name}: {len(fams)} complete families  [{binding}]")
    for name, c in rep.checks.items():
        n = len(c["details"]) if isinstance(c["details"], list) else 0
        extra = f"  ({n} item{'s' if n != 1 else ''})" if n else ""
        note = f"  - {c['note']}" if c["note"] else ""
        print(f"  {c['status']:4s} {name:<{width}} {c['rule']:<10}{extra}{note}")
    for name, c in rep.checks.items():
        if c["status"] in ("FAIL", "WARN") and isinstance(c["details"], list):
            for d in c["details"][:12]:
                print(f"        {name}: {json.dumps(d, ensure_ascii=False)}")
            if len(c["details"]) > 12:
                print(f"        {name}: ... {len(c['details']) - 12} more in report")
    print(f"OVERALL {overall}  -> {args.report}")
    bad = overall == "FAIL" or (args.strict and overall == "WARN")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
