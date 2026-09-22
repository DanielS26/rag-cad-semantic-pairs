"""Scorer record contract from handoff Section 7.1.

Dataset strings are inert untrusted data. Validation messages name fields and
already-validated identifiers only, never record text.
"""

import re
from dataclasses import dataclass

from rag_cad.operations.provenance import digest

SPLITS = ("train", "validation", "test")
CONDITION_SOURCES = ("base", "shared_malicious", "random_benign", "keyword_benign",
                     "semantic_benign", "test_only")
PAIR_MEMBERS = ("benign", "malicious", "unpaired")
REVIEW_STATUSES = ("unreviewed", "single_reviewed", "double_reviewed", "excluded")
LICENCES = {"team_authored": "team-owned", "cad_original_train": "CC-BY-4.0",
            "cad_original_test": "CC-BY-4.0", "cad_paraphrased_train": "CC-BY-4.0"}
RECORD_FIELDS = ("record_id", "group_id", "family_id", "split", "condition_source", "query",
                 "domain", "attack_goal", "pair_member", "sentences", "provenance")
SENTENCE_FIELDS = ("sentence_id", "text", "label", "semantic_role", "is_target")
PROVENANCE_FIELDS = ("source_dataset", "source_record_id", "generator_model",
                     "generator_prompt_hash", "licence", "review_status")
EXPECTED_MEMBER = {"base": "unpaired", "shared_malicious": "malicious", "random_benign": "unpaired",
                   "keyword_benign": "unpaired", "semantic_benign": "benign"}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}")
TOKEN = re.compile(r"[a-z][a-z0-9_]{0,63}")
HEX64 = re.compile(r"[0-9a-f]{64}")
MAX_TEXT = 20_000


class ContractError(ValueError):
    """A refused check whose structured report may still be written for review."""

    def __init__(self, message: str, report: dict):
        super().__init__(message)
        self.report = report


def _identifier(value) -> bool:
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def _token(value) -> bool:
    return isinstance(value, str) and TOKEN.fullmatch(value) is not None


def _text(value, *, single_line: bool) -> bool:
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT or "\x00" in value:
        return False
    return not (single_line and ("\n" in value or "\r" in value))


def _fail(record_id: str, message: str):
    raise ValueError(f"{message} [{record_id}]")


def validate_sentences(value, record_id: str, pair_member: str) -> list[dict]:
    if not isinstance(value, list) or not value:
        _fail(record_id, "Record requires a non-empty sentence list")
    sentences = []
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != set(SENTENCE_FIELDS):
            _fail(record_id, f"Sentence {index} fields must be exactly the contract fields")
        if type(item["sentence_id"]) is not int or item["sentence_id"] != index:
            _fail(record_id, "Sentence identifiers must be sequential from zero")
        if not _text(item["text"], single_line=True):
            _fail(record_id, f"Sentence {index} text must be a non-empty single line")
        if type(item["label"]) is not int or item["label"] not in (0, 1):
            _fail(record_id, f"Sentence {index} label must be the integer 0 or 1")
        if type(item["is_target"]) is not bool:
            _fail(record_id, f"Sentence {index} is_target must be boolean")
        role = item["semantic_role"]
        if role is not None and not _token(role):
            _fail(record_id, f"Sentence {index} semantic_role must be a snake_case token or null")
        if item["label"] == 1 and not item["is_target"]:
            _fail(record_id, f"Sentence {index} is malicious but not marked as a target")
        if item["is_target"] and role is None:
            _fail(record_id, f"Sentence {index} is a target without a semantic role")
        if item["is_target"] and item["label"] == 0 and pair_member != "benign":
            _fail(record_id, f"Sentence {index} is a benign target outside a benign pair member")
        sentences.append({name: item[name] for name in SENTENCE_FIELDS})
    return sentences


def validate_provenance(value, record_id: str, split: str | None) -> dict:
    if not isinstance(value, dict) or set(value) != set(PROVENANCE_FIELDS):
        _fail(record_id, "Provenance fields must be exactly the contract fields")
    source = value["source_dataset"]
    if source not in LICENCES:
        _fail(record_id, "Unknown source dataset")
    if value["licence"] != LICENCES[source]:
        _fail(record_id, "Licence does not match the source dataset registry")
    source_record = value["source_record_id"]
    if source_record is not None and not _identifier(source_record):
        _fail(record_id, "source_record_id must be an identifier or null")
    if source != "team_authored" and source_record is None:
        _fail(record_id, "Upstream-derived records require a source_record_id")
    model, prompt_hash = value["generator_model"], value["generator_prompt_hash"]
    if model is not None and not _text(model, single_line=True):
        _fail(record_id, "generator_model must be a non-empty string or null")
    if (model is None) != (prompt_hash is None):
        _fail(record_id, "generator_model and generator_prompt_hash must be set together")
    if prompt_hash is not None and not (isinstance(prompt_hash, str) and HEX64.fullmatch(prompt_hash)):
        _fail(record_id, "generator_prompt_hash must be a SHA-256 hex digest")
    if value["review_status"] not in REVIEW_STATUSES:
        _fail(record_id, "Unknown review status")
    if source == "cad_original_test" and split not in (None, "test"):
        _fail(record_id, "Released CAD test records may only be used in the test split")
    return {name: value[name] for name in PROVENANCE_FIELDS}


def validate_record(value, *, require_split: bool = True) -> dict:
    """Return a field-ordered copy of a valid record or raise ValueError naming the defect."""
    if not isinstance(value, dict):
        raise ValueError("Record must be a JSON object")
    record_id = value.get("record_id")
    if not _identifier(record_id):
        raise ValueError("Record requires a valid record_id")
    if set(value) != set(RECORD_FIELDS):
        _fail(record_id, "Record fields must be exactly the contract fields")
    if not _identifier(value["group_id"]):
        _fail(record_id, "group_id must be an identifier")
    family = value["family_id"]
    if family is not None and not _identifier(family):
        _fail(record_id, "family_id must be an identifier or null")
    split = value["split"]
    if split is None:
        if require_split:
            _fail(record_id, "split must be assigned")
    elif split not in SPLITS:
        _fail(record_id, "Unknown split")
    source = value["condition_source"]
    if source not in CONDITION_SOURCES:
        _fail(record_id, "Unknown condition_source")
    member = value["pair_member"]
    if member not in PAIR_MEMBERS:
        _fail(record_id, "Unknown pair_member")
    if (family is None) != (member == "unpaired"):
        _fail(record_id, "family_id is required exactly for paired members")
    if not _text(value["query"], single_line=False):
        _fail(record_id, "query must be a non-empty string")
    if not _token(value["domain"]):
        _fail(record_id, "domain must be a snake_case token")
    goal = value["attack_goal"]
    if goal is not None and not _token(goal):
        _fail(record_id, "attack_goal must be a snake_case token or null")
    sentences = validate_sentences(value["sentences"], record_id, member)
    malicious = sum(sentence["label"] for sentence in sentences)
    targets = sum(sentence["is_target"] for sentence in sentences)
    if member == "malicious" and not malicious:
        _fail(record_id, "Malicious pair members require a malicious sentence")
    if member == "benign" and malicious:
        _fail(record_id, "Benign pair members must be entirely benign")
    if malicious and goal is None:
        _fail(record_id, "Records with malicious sentences require an attack_goal")
    expected = EXPECTED_MEMBER.get(source)
    if expected is not None and member != expected:
        _fail(record_id, "pair_member does not match condition_source")
    if source in ("random_benign", "keyword_benign") and (malicious or targets):
        _fail(record_id, "Control benign records must contain no malicious or target sentences")
    if source == "semantic_benign" and not targets:
        _fail(record_id, "Semantic benign counterparts require a target sentence")
    if source == "test_only" and split not in (None, "test"):
        _fail(record_id, "test_only records belong to the test split")
    provenance = validate_provenance(value["provenance"], record_id, split)
    checked = {name: value[name] for name in RECORD_FIELDS}
    checked["sentences"] = sentences
    checked["provenance"] = provenance
    return checked


def texts(record: dict) -> list[str]:
    return [sentence["text"] for sentence in record["sentences"]]


def passage(record: dict) -> str:
    """Canonical passage string: ordered sentences joined with newlines (Section 7.1)."""
    return "\n".join(texts(record))


def record_content_hash(record: dict) -> str:
    return digest({"query": record["query"],
                   "sentences": [[s["text"], s["label"], s["is_target"], s["semantic_role"]]
                                 for s in record["sentences"]]})


def dataset_digest(records: list[dict]) -> str:
    return digest(sorted((record["record_id"], record_content_hash(record)) for record in records))


@dataclass(frozen=True)
class Sentence:
    sentence_id: int
    text: str
    label: int
    semantic_role: str | None
    is_target: bool


@dataclass(frozen=True)
class Provenance:
    source_dataset: str
    source_record_id: str | None
    generator_model: str | None
    generator_prompt_hash: str | None
    licence: str
    review_status: str


@dataclass(frozen=True)
class ScorerRecord:
    record_id: str
    group_id: str
    family_id: str | None
    split: str | None
    condition_source: str
    query: str
    domain: str
    attack_goal: str | None
    pair_member: str
    sentences: tuple[Sentence, ...]
    provenance: Provenance

    @classmethod
    def from_dict(cls, value, *, require_split: bool = True) -> "ScorerRecord":
        checked = validate_record(value, require_split=require_split)
        return cls(**{**checked,
                      "sentences": tuple(Sentence(**item) for item in checked["sentences"]),
                      "provenance": Provenance(**checked["provenance"])})

    def to_dict(self) -> dict:
        value = {name: getattr(self, name) for name in RECORD_FIELDS}
        value["sentences"] = [{name: getattr(item, name) for name in SENTENCE_FIELDS}
                              for item in self.sentences]
        value["provenance"] = {name: getattr(self.provenance, name) for name in PROVENANCE_FIELDS}
        return value
