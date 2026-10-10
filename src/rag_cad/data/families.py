"""Family manifest and the automated pre-screen for semantic-pair families (D-20261010-20 to -22).

A family is one malicious record, its benign semantic twin (same family_id) and the two control
records (random_benign, keyword_benign) that share the family's group_id. Family-level facts the
decisions require but the record contract (handoff Section 7.1) does not carry live in a separate
manifest, one JSON object per family. Dataset strings are inert data; reports name identifiers
and rule names only, never record text.
"""

import re
from collections import Counter, defaultdict

from rag_cad.data.schema import IDENTIFIER, ContractError, validate_record
from rag_cad.data.similarity import normalise

ROLES = ("quotation", "negation", "warning", "analysis", "translation", "historical_description",
         "task_alignment", "authorisation")
CUE_POSITIONS = ("query", "sentence_before", "sentence_after", "heading", "policy")
STATUSES = ("candidate", "accepted", "ambiguous", "rejected")
HAND_WRITTEN = "hand-written"
FAMILY_FIELDS = ("family_id", "group_id", "semantic_role", "cue_position", "drafter", "reviewer",
                 "justification", "quotation_marks_only_cue", "status")
MIN_SENTENCES, MAX_SENTENCES = 2, 5
MAX_QUOTATION_SHARE = 0.25
MIN_DOMAINS = 4
EXAMPLE_LIMIT = 20
STOPWORDS = frozenset("""
a an the and or but if then than that this these those there here is are was were be been being am
do does did done to of in on at by for from with without into onto over under about as it its
they them their he she his her you your we our i me my not no yes all any each every some such
so very just also only more most less least can could may might must shall should will would
please make sure ensure before after when while where which who whom whose what why how now
""".split())
WORD = re.compile(r"[a-z][a-z0-9']*")


def content_words(text: str) -> set[str]:
    """Lower-cased words of three or more letters that are not function words."""
    return {word for word in WORD.findall(normalise(text))
            if len(word) >= 3 and word not in STOPWORDS}


def _identifier(value) -> bool:
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def validate_family_entry(value) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Family entry must be a JSON object")
    family_id = value.get("family_id")
    if not _identifier(family_id):
        raise ValueError("Family entry requires a valid family_id")
    if set(value) != set(FAMILY_FIELDS):
        raise ValueError(f"Family entry fields must be exactly the manifest fields [{family_id}]")
    if not _identifier(value["group_id"]):
        raise ValueError(f"group_id must be an identifier [{family_id}]")
    if value["semantic_role"] not in ROLES:
        raise ValueError(f"semantic_role must be one of the eight roles [{family_id}]")
    if value["cue_position"] not in CUE_POSITIONS:
        raise ValueError(f"cue_position must be one of the five positions [{family_id}]")
    for field in ("drafter", "justification"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValueError(f"{field} must be a non-empty string [{family_id}]")
    reviewer = value["reviewer"]
    if reviewer is not None and (not isinstance(reviewer, str) or not reviewer.strip()):
        raise ValueError(f"reviewer must be a non-empty string or null [{family_id}]")
    if type(value["quotation_marks_only_cue"]) is not bool:
        raise ValueError(f"quotation_marks_only_cue must be boolean [{family_id}]")
    if value["status"] not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES} [{family_id}]")
    if value["status"] == "accepted" and reviewer is None:
        raise ValueError(f"accepted families require a reviewer [{family_id}]")
    return {name: value[name] for name in FAMILY_FIELDS}


def load_family_manifest(entries) -> dict[str, dict]:
    checked = [validate_family_entry(entry) for entry in entries]
    counts = Counter(entry["family_id"] for entry in checked)
    repeated = sorted(family for family, count in counts.items() if count > 1)
    if repeated:
        raise ValueError(f"Duplicate family_id values in the manifest: {repeated[:EXAMPLE_LIMIT]}")
    return {entry["family_id"]: entry for entry in checked}


def _targets(record: dict) -> list[str]:
    return [sentence["text"].strip() for sentence in record["sentences"] if sentence["is_target"]]


def _characters(record: dict) -> int:
    return sum(len(sentence["text"]) for sentence in record["sentences"])


def attack_vocabulary(malicious: dict) -> set[str]:
    """Content words of the target that the record's own benign sentences and query do not use.

    Domain nouns shared with the surrounding context (a customer-support passage will say
    "customer") are not attack vocabulary; the action words that only the target carries are.
    Falls back to every target content word when nothing distinguishes the target.
    """
    target = set().union(*(content_words(s["text"]) for s in malicious["sentences"] if s["is_target"]), set())
    context = set().union(*(content_words(s["text"]) for s in malicious["sentences"] if not s["is_target"]),
                          content_words(malicious["query"]))
    distinctive = target - context
    return distinctive or target


def _drafter_consistent(entry: dict, records: list[dict]) -> bool:
    generated = entry["drafter"] != HAND_WRITTEN
    return all((record["provenance"]["generator_model"] is not None) == generated for record in records)


def screen_family(entry: dict, members: dict[str, list[dict]], *, length_tolerance: float) -> dict:
    """Blocking failures and non-blocking warnings for one family; rule names only."""
    failures, warnings = [], []
    expected = {"shared_malicious", "semantic_benign", "random_benign", "keyword_benign"}
    if {source for source, items in members.items() if items} != expected \
            or any(len(items) != 1 for items in members.values()):
        failures.append("family_structure")
        return {"passed": False, "failures": failures, "warnings": warnings}
    malicious, twin = members["shared_malicious"][0], members["semantic_benign"][0]
    random_benign, keyword_benign = members["random_benign"][0], members["keyword_benign"][0]
    records = [malicious, twin, random_benign, keyword_benign]
    if any(record["group_id"] != entry["group_id"] for record in records):
        failures.append("group_id_mismatch")
    malicious_targets, twin_targets = _targets(malicious), _targets(twin)
    if len(malicious_targets) != 1 or len(twin_targets) != 1:
        failures.append("single_target_required")
    elif malicious_targets != twin_targets:
        failures.append("target_wording_differs")
    if any(not MIN_SENTENCES <= len(record["sentences"]) <= MAX_SENTENCES for record in records):
        failures.append("sentence_count_out_of_range")
    twin_count = len(twin["sentences"])
    if any(len(record["sentences"]) != twin_count for record in (random_benign, keyword_benign)):
        failures.append("control_sentence_count")
    lengths = [_characters(record) for record in (twin, random_benign, keyword_benign)]
    if min(lengths) and max(lengths) / min(lengths) > 1 + length_tolerance:
        failures.append("control_length_tolerance")
    attack_words = attack_vocabulary(malicious)
    keyword_words = set().union(*(content_words(s["text"]) for s in keyword_benign["sentences"]))
    random_words = set().union(*(content_words(s["text"]) for s in random_benign["sentences"]))
    if attack_words and not attack_words & keyword_words:
        failures.append("keyword_benign_shares_no_attack_words")
    if attack_words & random_words:
        failures.append("random_benign_shares_attack_words")
    if not _drafter_consistent(entry, records):
        failures.append("drafter_provenance_mismatch")
    twin_role = next((s["semantic_role"] for s in twin["sentences"] if s["is_target"]), None)
    if twin_role != entry["semantic_role"]:
        warnings.append("record_role_token_differs_from_manifest")
    if entry["reviewer"] is None:
        warnings.append("awaiting_review")
    if any(record["domain"] != malicious["domain"] for record in records):
        warnings.append("mixed_domains_within_family")
    return {"passed": not failures, "failures": failures, "warnings": warnings}


def prescreen(records, manifest_entries, *, length_tolerance: float, minimum_per_role: int = 4,
              max_quotation_share: float = MAX_QUOTATION_SHARE) -> dict:
    """Screen every family in the manifest against the records; raise ContractError with the report
    when any family or batch rule fails."""
    if type(minimum_per_role) is not int or minimum_per_role < 0:
        raise ValueError("minimum_per_role must be a non-negative integer")
    checked = [validate_record(record, require_split=False) for record in records]
    manifest = load_family_manifest(manifest_entries)
    by_family = defaultdict(lambda: defaultdict(list))
    by_group = defaultdict(lambda: defaultdict(list))
    for record in checked:
        if record["family_id"] is not None:
            by_family[record["family_id"]][record["condition_source"]].append(record)
        by_group[record["group_id"]][record["condition_source"]].append(record)
    results, domains_by_role, target_texts = {}, defaultdict(set), defaultdict(set)
    for family_id, entry in sorted(manifest.items()):
        members = {source: list(by_family[family_id][source]) for source in ("shared_malicious", "semantic_benign")}
        for source in ("random_benign", "keyword_benign"):
            members[source] = list(by_group[entry["group_id"]][source])
        results[family_id] = screen_family(entry, members, length_tolerance=length_tolerance)
        for record in members["shared_malicious"]:
            domains_by_role[entry["semantic_role"]].add(record["domain"])
            for text in _targets(record):
                target_texts[normalise(text)].add(family_id)
    unlisted = sorted(set(by_family) - set(manifest))
    role_counts = Counter(entry["semantic_role"] for entry in manifest.values())
    cue_counts = Counter(entry["cue_position"] for entry in manifest.values())
    status_counts = Counter(entry["status"] for entry in manifest.values())
    quotation_only = sum(entry["quotation_marks_only_cue"] for entry in manifest.values())
    quotation_share = quotation_only / len(manifest) if manifest else 0.0
    domains = sorted({record["domain"] for record in checked if record["family_id"] is not None})
    duplicate_targets = sorted(sorted(families) for families in target_texts.values() if len(families) > 1)
    batch_failures, batch_warnings = [], []
    if unlisted:
        batch_failures.append("families_missing_from_manifest")
    if quotation_share > max_quotation_share:
        batch_failures.append("quotation_only_cue_share_exceeds_cap")
    if duplicate_targets:
        batch_failures.append("duplicate_target_sentences_across_families")
    roles_below = sorted(role for role in ROLES if role_counts.get(role, 0) < minimum_per_role)
    if roles_below:
        batch_warnings.append("roles_below_minimum")
    if len(domains) < MIN_DOMAINS:
        batch_warnings.append("fewer_than_minimum_domains")
    confined = sorted(role for role, found in domains_by_role.items() if len(found) == 1 and role_counts[role] > 1)
    if confined:
        batch_warnings.append("roles_confined_to_one_domain")
    failed = sorted(family for family, result in results.items() if not result["passed"])
    report = {"families": len(manifest), "records": len(checked),
              "family_results": results, "failed_families": failed,
              "unlisted_families": unlisted[:EXAMPLE_LIMIT],
              "batch": {"role_counts": dict(sorted(role_counts.items())), "minimum_per_role": minimum_per_role,
                        "roles_below_minimum": roles_below, "cue_position_counts": dict(sorted(cue_counts.items())),
                        "status_counts": dict(sorted(status_counts.items())),
                        "quotation_only_cue_share": round(quotation_share, 4),
                        "max_quotation_share": max_quotation_share, "domains": domains,
                        "roles_confined_to_one_domain": confined,
                        "duplicate_target_families": duplicate_targets[:EXAMPLE_LIMIT],
                        "failures": batch_failures, "warnings": batch_warnings},
              "passed": not failed and not batch_failures}
    if not report["passed"]:
        raise ContractError(f"Pre-screen failed: {len(failed)} families, batch {batch_failures}", report)
    return report
