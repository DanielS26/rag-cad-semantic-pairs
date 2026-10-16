"""Bag-of-words baseline on the family folds (D-20261016-49 (d), D-20261017-51 (c)).

Ported from the audit probe (docs/archive/audit_200_2026-10-16/pilot40_probe.py): twin
(semantic_benign) against malicious (shared_malicious), target sentence left out, unigrams and
bigrams over the normalised query and non-target sentences, multinomial naive Bayes with
add-one smoothing; a positive log-odds margin predicts the twin. Trained on each round's
training families and scored on its held-out families.
"""

import math
from collections import Counter

from rag_cad.data.folds import validate_folds
from rag_cad.data.similarity import normalise
from rag_cad.data.validate import unique_records

SCHEMA = "rag_cad.bow_baseline/1"
TWIN, MALICIOUS = 1, 0
SOURCES = {"semantic_benign": TWIN, "shared_malicious": MALICIOUS}


def features(record: dict) -> list[str]:
    tokens = []
    for text in [record["query"]] + [sentence["text"] for sentence in record["sentences"]
                                     if not sentence["is_target"]]:
        words = normalise(text).split()
        tokens += words + [left + "_" + right for left, right in zip(words, words[1:])]
    return tokens


class NaiveBayes:
    """Multinomial naive Bayes with add-one smoothing over a shared vocabulary; words unseen in
    training are ignored at scoring time, as in the audit probe."""

    def __init__(self, examples, labels):
        self.counts = {TWIN: Counter(), MALICIOUS: Counter()}
        self.prior = Counter(labels)
        for tokens, label in zip(examples, labels):
            self.counts[label].update(tokens)
        self.vocabulary = set(self.counts[TWIN]) | set(self.counts[MALICIOUS])
        self.totals = {label: sum(count.values()) for label, count in self.counts.items()}
        if not self.prior[TWIN] or not self.prior[MALICIOUS]:
            raise ValueError("Training needs both twin and malicious examples")

    def log_probability(self, tokens, label: int) -> float:
        denominator = self.totals[label] + len(self.vocabulary)
        return math.log(self.prior[label] / sum(self.prior.values())) + sum(
            math.log((self.counts[label][token] + 1) / denominator) for token in tokens
            if token in self.vocabulary)

    def margin(self, tokens) -> float:
        """Log-odds of twin over malicious; positive predicts the twin."""
        return self.log_probability(tokens, TWIN) - self.log_probability(tokens, MALICIOUS)


def _rate(hits: int, total: int) -> float | None:
    return round(hits / total, 4) if total else None


def _summary(rows) -> dict:
    """Accuracy, balanced accuracy and the within-family paired share over scored families."""
    correct = Counter()
    for row in rows:
        correct[TWIN] += row["twin_correct"]
        correct[MALICIOUS] += row["malicious_correct"]
    count = len(rows)
    twin_recall, malicious_recall = _rate(correct[TWIN], count), _rate(correct[MALICIOUS], count)
    return {"families": count, "records": 2 * count,
            "accuracy": _rate(correct[TWIN] + correct[MALICIOUS], 2 * count),
            "balanced_accuracy": None if not count else round((correct[TWIN] / count + correct[MALICIOUS] / count) / 2, 4),
            "twin_accuracy": twin_recall, "malicious_accuracy": malicious_recall,
            "paired_share": _rate(sum(row["twin_above_malicious"] for row in rows), count)}


def run_baseline(records, fold_rows) -> dict:
    """Train once per round on the training folds and score every held-out family's twin and
    malicious record; report overall, per fold, per role, per attack category and per cue position."""
    keyed = validate_folds(fold_rows)
    pairs = {}
    for record in unique_records(records):
        label = SOURCES.get(record["condition_source"])
        if label is None:
            continue
        if record["family_id"] not in keyed:
            raise ValueError(f"Family missing from the fold table: {record['family_id']}")
        member = pairs.setdefault(record["family_id"], {})
        if label in member:
            raise ValueError(f"Family has two records of one kind: {record['family_id']}")
        member[label] = features(record)
    if set(pairs) != set(keyed) or any(len(member) != 2 for member in pairs.values()):
        raise ValueError("Every fold family needs exactly one twin and one malicious record")
    folds = sorted({row["fold"] for row in keyed.values()})
    scored = []
    for fold in folds:
        training = [family for family in sorted(pairs) if keyed[family]["fold"] != fold]
        model = NaiveBayes([pairs[family][label] for family in training for label in (TWIN, MALICIOUS)],
                           [label for _ in training for label in (TWIN, MALICIOUS)])
        for family in sorted(pairs):
            if keyed[family]["fold"] != fold:
                continue
            twin, malicious = model.margin(pairs[family][TWIN]), model.margin(pairs[family][MALICIOUS])
            scored.append({**keyed[family], "margin_twin": round(twin, 4),
                           "margin_malicious": round(malicious, 4), "twin_correct": twin > 0,
                           "malicious_correct": malicious <= 0, "twin_above_malicious": twin > malicious})
    scored.sort(key=lambda row: row["family_id"])

    def grouped(field):
        return {key: _summary([row for row in scored if row[field] == key])
                for key in sorted({row[field] for row in scored})}

    overall = _summary(scored)
    return {"schema": SCHEMA, "task": "twin (semantic_benign) against malicious (shared_malicious)",
            "features": "unigrams and bigrams of the normalised query and non-target sentences",
            "model": "multinomial naive Bayes, add-one smoothing, positive log-odds predicts the twin",
            "paired_share_definition": "share of families whose twin's log-odds of twin exceeds its "
                                       "malicious partner's (twin scored more benign)",
            "overall": overall, "per_fold": {str(key): value for key, value in grouped("fold").items()},
            "per_fold_accuracy": [grouped("fold")[fold]["accuracy"] for fold in folds],
            "per_role": grouped("semantic_role"), "per_attack_category": grouped("attack_category"),
            "per_cue_position": grouped("cue_position"), "families": scored}


def format_table(result: dict) -> str:
    """Plain-text table of the headline figures, overall and per fold."""
    lines = [f"{'slice':<12}{'families':>9}{'accuracy':>10}{'balanced':>10}{'paired':>8}"]

    def line(name, values):
        lines.append(f"{name:<12}{values['families']:>9}{values['accuracy']:>10.4f}"
                     f"{values['balanced_accuracy']:>10.4f}{values['paired_share']:>8.4f}")

    for fold, values in result["per_fold"].items():
        line(f"fold {fold}", values)
    line("overall", result["overall"])
    return "\n".join(lines)


def bow_baseline_command(args) -> dict:
    """CLI body of evaluation bow-baseline: checks the fold table against the records and the
    manifest, runs the baseline, writes the JSON report and prints the table to standard error."""
    import sys

    from rag_cad.data.folds import FOLD_FIELDS, family_table
    from rag_cad.data.jsonl import load_records, read_jsonl
    from rag_cad.operations.paths import local_path
    from rag_cad.operations.provenance import sha256, write_json

    for path in (args.input, args.manifest, args.folds, args.output):
        local_path(path)
    records, inventory = load_records(args.input)
    fold_rows = read_jsonl(args.folds)
    expected = {row["family_id"]: row for row in family_table(records, read_jsonl(args.manifest))}
    for row in fold_rows:
        reference = expected.get(row.get("family_id"))
        if reference is None or any(row.get(field) != reference[field]
                                    for field in FOLD_FIELDS if field != "fold"):
            raise ValueError(f"Fold table disagrees with the records or manifest: {row.get('family_id')}")
    result = {"input": {**inventory, "manifest_sha256": sha256(args.manifest),
                        "folds_sha256": sha256(args.folds)}, **run_baseline(records, fold_rows)}
    write_json(args.output, result)
    print(format_table(result), file=sys.stderr)
    return result
