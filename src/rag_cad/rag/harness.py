"""Phase 8 retrieval harness (D-20261017-58): each Phase 7 scorer as a trust gate between a fixed
retriever and the prompt, measured on what it forwards. No language model is called.

Inputs, all read only: the Phase 4 root and the Phase 6 family artefact (read through the
two-cache reader, so their identities are compared first), the family records (texts, queries
and cue positions), the Phase 7 run (every cell verified by hash, every condition on the planned
seeds) and the bag-of-words baseline. Per round the store is built and the 160 family queries
retrieved once; then every row (no gate, the baseline under the document gate, N0, M0 and M1 to
M3 on every seed) gates those same retrievals with the held-out predictions of the matching
cell. A distractor is scored from the same cell's released-test predictions, which cover every
released-test sentence; a sentence they do not cover refuses the run. Figures are pooled over
the rounds per seed, then given as the mean over seeds with the population sd.
"""

import json
import time
from pathlib import Path

import numpy as np

from rag_cad.data.jsonl import read_jsonl, write_jsonl
from rag_cad.data.schema import record_content_hash
from rag_cad.data.selfcheck import _cue_sentence_ids
from rag_cad.evaluation.fold_tables import _spread, check_complete, load_run, pooled_records
from rag_cad.evaluation.posthoc import ADAPTED_TEST, exclusion_sets
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import digest, sha256, write_json
from rag_cad.rag.gates import (
    DOCUMENT_GATE,
    GATES,
    METRICS,
    THRESHOLD,
    ScoreView,
    flagged,
    forward,
    gate_metrics,
    outcome,
)
from rag_cad.rag.retrieval import (
    DISTRACTOR,
    DISTRACTOR_SEED,
    QUERY_SENTENCES,
    TOP_K,
    Document,
    Retrieval,
    Store,
    build_store,
    passage_bounds,
    retrieve,
    select_distractors,
    sentence_embeddings,
)
from rag_cad.training.fold_driver import (
    CONDITIONS,
    HELD_RECORDS,
    HELD_ROWS,
    LEAKED_FILE,
    M0,
    N0,
    TEST_ROWS,
)
from rag_cad.training.two_cache import FAMILY_POOLS, RECORD_KINDS, TwoCache

SCHEMA = "rag_cad.retrieval_harness/1"
NO_GATE = "no_gate"
BOW = "bow_baseline"
ROWS = (NO_GATE, BOW) + CONDITIONS
BREAKDOWN = ("semantic_role", "cue_position")
DISTRACTOR_SETS = ("minus_near", "full")
SEED_NONE = "none"
JSON_FILE = "harness.json"
MARKDOWN_FILE = "harness.md"
RETRIEVALS_FILE = "retrievals.jsonl"
NAMES = {NO_GATE: "no gate", BOW: "BoW baseline", N0: "N0 released", M0: "M0 base",
         "m1_random": "M1 random", "m2_keyword": "M2 keyword", "m3_semantic": "M3 semantic"}
LABELS = {"injected_pass_through": "injected pass-through", "twin_loss": "twin loss",
          "random_control_loss": "random loss", "keyword_control_loss": "keyword loss",
          "context_survival_family": "family context survival",
          "context_survival": "context survival (all slots)", "distractor_loss": "distractor loss",
          "context_survival_distractor": "distractor context"}
CONCENTRATION_TOP = 10


def family_documents(cache: TwoCache, records: list[dict]) -> dict[str, Document]:
    """Every family record of the cache as a document: sentences from the cached rows (checked
    against the record's content hash), embeddings from the cached features, texts, query and cue
    sentences from the record, role and cue position from the fold table."""
    by_id = {record["record_id"]: record for record in records}
    documents = {}
    for pool in FAMILY_POOLS:
        current = cache.pools[pool]
        positions: dict[str, list[int]] = {}
        for index, row in enumerate(current.rows):
            positions.setdefault(row["record_id"], []).append(index)
        for record_id, indices in positions.items():
            record = by_id.get(record_id)
            if record is None:
                raise ValueError(f"Family record {record_id} of the cache is not among the records")
            indices = sorted(indices, key=lambda i: current.rows[i]["sentence_id"])
            rows = [current.rows[i] for i in indices]
            if any(row["record_content_hash"] != record_content_hash(record) for row in rows):
                raise ValueError(f"Record {record_id} differs from the record that was encoded")
            texts = {s["sentence_id"]: s["text"] for s in record["sentences"]}
            ids = tuple(row["sentence_id"] for row in rows)
            if sorted(texts) != list(ids):
                raise ValueError(f"Cached rows of {record_id} do not cover its sentences")
            fold = cache.folds[record["group_id"]]
            kind = RECORD_KINDS[pool]
            cue = frozenset(_cue_sentence_ids(fold, record)) if kind == "twin" else frozenset()
            documents[record_id] = Document(
                record_id, kind, ids, tuple(int(row["label"]) for row in rows),
                tuple(bool(row["is_target"]) for row in rows), tuple(texts[i] for i in ids),
                sentence_embeddings(current.features[indices]), group_id=record["group_id"],
                query=record["query"], cue_ids=cue, semantic_role=fold["semantic_role"],
                cue_position=fold["cue_position"])
    return documents


def distractor_documents(cache: TwoCache, test_records: list[dict], chosen: list[dict]) -> list[Document]:
    """The chosen benign remainders cut into passages of at most five consecutive sentences, each
    a document that names its parent record, with embeddings from the cached released-test rows."""
    rows = cache.released_test.rows
    positions = {(row["record_id"], row["sentence_id"]): index for index, row in enumerate(rows)}
    by_id = {record["record_id"]: record for record in test_records}
    documents = []
    for item in chosen:
        record = by_id[item["record_id"]]
        texts = {s["sentence_id"]: s["text"] for s in record["sentences"]}
        indices = []
        for sentence_id in item["sentence_ids"]:
            key = (item["record_id"], sentence_id)
            if key not in positions or rows[positions[key]]["label"] != 0:
                raise ValueError(f"Distractor sentence {key} is not a cached benign row")
            if rows[positions[key]]["record_content_hash"] != record_content_hash(record):
                raise ValueError(f"Released-test record {item['record_id']} differs from its encoding")
            indices.append(positions[key])
        embeddings = sentence_embeddings(cache.released_test.features[indices])
        for number, (start, end) in enumerate(passage_bounds(len(indices)), 1):
            ids = tuple(item["sentence_ids"][start:end])
            documents.append(Document(f"{item['record_id']}#p{number}", DISTRACTOR, ids, (0,) * len(ids),
                                      (False,) * len(ids), tuple(texts[i] for i in ids),
                                      embeddings[start:end], group_id=record["group_id"],
                                      parent_id=item["record_id"]))
    return documents


def cell_view(manifest: dict) -> ScoreView:
    """A cell's held-out and released-test sentence probabilities; the record flags recomputed
    from them must equal the cell's own heldout_records.jsonl."""
    directory = manifest["directory"]
    probabilities: dict[str, dict[int, float]] = {}
    for name in (HELD_ROWS, TEST_ROWS):
        for row in read_jsonl(directory / name):
            scored = probabilities.setdefault(row["record_id"], {})
            if row["sentence_id"] in scored:
                raise ValueError(f"Cell {manifest['cell']} scores {row['record_id']} twice")
            scored[row["sentence_id"]] = float(row["probability"])
    for record in read_jsonl(directory / HELD_RECORDS):
        if flagged(list(probabilities[record["record_id"]].values())) != record["flagged"]:
            raise ValueError(f"Cell {manifest['cell']}: {record['record_id']} flag differs from its rows")
    return ScoreView(manifest["cell"], probabilities=probabilities)


def bow_view(bow: dict, documents: dict[str, Document]) -> ScoreView:
    """The baseline's record decisions: a twin it calls malicious and a malicious record it calls
    malicious are flagged; controls and distractors are not scored and pass."""
    members: dict[str, dict[str, str]] = {}
    for document in documents.values():
        members.setdefault(document.group_id, {})[document.kind] = document.doc_id
    families = bow.get("families") or []
    if {family["group_id"] for family in families} != set(members) or len(families) != len(members):
        raise ValueError("The bag-of-words baseline must score every family once")
    decisions = {}
    for family in families:
        decisions[members[family["group_id"]]["twin"]] = not family["twin_correct"]
        decisions[members[family["group_id"]]["malicious"]] = bool(family["malicious_correct"])
    return ScoreView(BOW, decisions=decisions)


def gate_outcomes(store: Store, retrieval: Retrieval, gate: str | None, view: ScoreView | None) -> list[dict]:
    result = []
    for top in retrieval.top:
        for doc_id in top:
            document = store.documents[store.index[doc_id]]
            result.append(outcome(document, forward(document, gate, view)))
    return result


def row_table(outcomes: dict[str, dict[int, list[dict]]], digests: dict[int, str]) -> dict:
    """Per seed: every round's slots pooled, overall and by role and cue position; then the mean
    and population sd over seeds."""
    per_seed = {}
    for seed, rounds in sorted(outcomes.items()):
        pooled = [item for number in sorted(rounds) for item in rounds[number]]
        by = {name: {value: gate_metrics([item for item in pooled if item[name] == value])
                     for value in sorted({item[name] for item in pooled if item[name] is not None})}
              for name in BREAKDOWN}
        per_seed[seed] = {"overall": gate_metrics(pooled), "by": by,
                          "per_round": {str(number): gate_metrics(rounds[number]) for number in sorted(rounds)}}
    keys = METRICS + ("dropped_share",)
    overall = {metric: _spread([entry["overall"][metric] for entry in per_seed.values()]) for metric in keys}
    by = {}
    for name in BREAKDOWN:
        values = sorted({value for entry in per_seed.values() for value in entry["by"][name]})
        by[name] = {value: {metric: _spread([entry["by"][name][value][metric] for entry in per_seed.values()
                                             if value in entry["by"][name]]) for metric in keys}
                    for value in values}
    return {"seeds": sorted(per_seed), "overall": overall, "by": by, "per_seed": per_seed,
            "retrieval_digests": {str(number): value for number, value in sorted(digests.items())}}


def _cells_by_key(cells: dict[str, dict]) -> dict[tuple, dict]:
    keyed = {}
    for manifest in cells.values():
        seed = SEED_NONE if manifest["seed"] is None else str(manifest["seed"])
        keyed[(manifest["condition"], manifest["round"], seed)] = manifest
    return keyed


def run_harness(cache: TwoCache, records: list[dict], test_records: list[dict], leaked: dict,
                cells: dict[str, dict], bow: dict, *, distractors: int = 160,
                distractor_set: str = "minus_near") -> tuple[dict, list[dict]]:
    if distractor_set not in DISTRACTOR_SETS:
        raise ValueError(f"Distractor set must be one of {DISTRACTOR_SETS}")
    documents = family_documents(cache, records)
    excluded = exclusion_sets(leaked)[distractor_set]
    chosen, summary = select_distractors(test_records, excluded, distractors)
    if not chosen:
        raise ValueError("No released-test record outside the excluded set has a benign remainder")
    pool = distractor_documents(cache, test_records, chosen)
    stores, retrievals = {}, {}
    for number in cache.rounds:
        family = [d for d in documents.values() if cache.folds[d.group_id]["fold"] == number]
        stores[number] = build_store(number, family, pool)
        queries = [(d.doc_id, d.query) for d in sorted(family, key=lambda d: d.doc_id)]
        retrievals[number] = retrieve(stores[number], queries)
    digests = {number: retrieval.digest for number, retrieval in retrievals.items()}
    keyed = _cells_by_key(cells)
    views: dict[str, ScoreView] = {}
    checked: set[tuple[str, int]] = set()

    def view_of(manifest: dict) -> ScoreView:
        if manifest["cell"] not in views:
            views[manifest["cell"]] = cell_view(manifest)
        return views[manifest["cell"]]

    tables = {gate: {} for gate in GATES}
    plain = {SEED_NONE: {n: gate_outcomes(stores[n], retrievals[n], None, None) for n in cache.rounds}}
    for gate in GATES:
        tables[gate][NO_GATE] = row_table(plain, digests)
    baseline = bow_view(bow, documents)
    tables[DOCUMENT_GATE][BOW] = row_table(
        {SEED_NONE: {n: gate_outcomes(stores[n], retrievals[n], DOCUMENT_GATE, baseline) for n in cache.rounds}},
        digests)
    for condition in CONDITIONS:
        seeds = sorted({seed for (name, _, seed) in keyed if name == condition})
        for gate in GATES:
            outcomes: dict[str, dict[int, list[dict]]] = {}
            for seed in seeds:
                outcomes[seed] = {}
                for number in cache.rounds:
                    key = (condition, None, seed) if condition in (N0, M0) else (condition, number, seed)
                    if key not in keyed:
                        raise ValueError(f"No cell for {condition} round {number} seed {seed}")
                    manifest = keyed[key]
                    if (manifest["cell"], number) not in checked:
                        held = {r["record_id"] for r in read_jsonl(manifest["directory"] / HELD_RECORDS)}
                        family_ids = {d.doc_id for d in stores[number].documents if d.kind != DISTRACTOR}
                        if not family_ids <= held or (condition not in (N0, M0) and held != family_ids):
                            raise ValueError(f"Cell {manifest['cell']} does not hold exactly the round's "
                                             "records")
                        for document in stores[number].documents:  # every store document, retrieved or not
                            view_of(manifest).sentence_scores(document)
                        checked.add((manifest["cell"], number))
                    outcomes[seed][number] = gate_outcomes(stores[number], retrievals[number], gate,
                                                           view_of(manifest))
            tables[gate][condition] = row_table(outcomes, digests)
    facts = [retrievals[n].facts(stores[n]) for n in cache.rounds]
    ranks = np.asarray([rank for n in cache.rounds for rank in retrievals[n].own_rank], dtype=float)
    masked = np.asarray([rank for n in cache.rounds for rank in retrievals[n].masked_rank], dtype=float)
    shares = [d["own_match_share"] for n in cache.rounds for d in retrievals[n].details]
    benign: dict[str, int] = {}
    for item in (item for n in cache.rounds for item in plain[SEED_NONE][n]):
        benign[item["kind"]] = benign.get(item["kind"], 0) + item["benign"]
    pooled = {"queries": int(len(ranks)), "hit_at_k": round(float((ranks <= TOP_K).mean()), 6),
              "mean_rank": round(float(ranks.mean()), 6), "median_rank": float(np.median(ranks)),
              "hit_at_k_masked": round(float((masked <= TOP_K).mean()), 6),
              "mean_rank_masked": round(float(masked.mean()), 6),
              "median_rank_masked": float(np.median(masked)),
              "own_match_share": round(float(np.mean(shares)), 6),
              "benign_sentences_by_kind": {kind: benign.get(kind, 0) for kind in facts[0]["slots_by_kind"]},
              "slots": sum(f["slots"] for f in facts),
              "slots_by_kind": {kind: sum(f["slots_by_kind"][kind] for f in facts)
                                for kind in facts[0]["slots_by_kind"]},
              "own_family_slot_share": round(float(np.mean([f["own_family_slot_share"] for f in facts])), 6),
              "centroid_fallback_queries": sum(f["centroid_fallback_queries"] for f in facts)}
    sizes = {d.doc_id: (d.scored_id, len(d.sentence_ids)) for d in pool}
    slots: dict[str, int] = {}
    for number in cache.rounds:
        for top in retrievals[number].top:
            for doc_id in top:
                if doc_id in sizes:
                    slots[doc_id] = slots.get(doc_id, 0) + 1
    parents: dict[str, int] = {}
    for doc_id, count in slots.items():
        parents[sizes[doc_id][0]] = parents.get(sizes[doc_id][0], 0) + count
    ranked = sorted(slots.items(), key=lambda item: (-item[1], item[0]))
    total = sum(slots.values())
    concentration = {"distractor_slots": total, "passages_retrieved": len(slots), "passages": len(pool),
                     "top_passages": [{"doc_id": doc_id, "parent_id": sizes[doc_id][0],
                                       "sentences": sizes[doc_id][1], "slots": count}
                                      for doc_id, count in ranked[:CONCENTRATION_TOP]],
                     "top_three_share": round(sum(c for _, c in ranked[:3]) / total, 6) if total else None,
                     "slots_by_parent": dict(sorted(parents.items(), key=lambda item: (-item[1], item[0])))}
    summary = {**summary, "passages": len(pool), "passage_sentences": sum(len(d.sentence_ids) for d in pool),
               "passage_lengths": sorted(len(d.sentence_ids) for d in pool),
               "max_passage_sentences": max(len(d.sentence_ids) for d in pool)}
    lines = []
    for number in cache.rounds:
        store, retrieval = stores[number], retrievals[number]
        for query_id, top, scores, rank, details in zip(retrieval.query_ids, retrieval.top, retrieval.scores,
                                                        retrieval.own_rank, retrieval.details):
            lines.append({"round": number, "query_id": query_id, "own_rank": rank, "source": details["source"],
                          "own_match_share": details["own_match_share"],
                          "matched_sentences": details["matched"],
                          "top": [[doc_id, store.documents[store.index[doc_id]].kind, score]
                                  for doc_id, score in zip(top, scores)]})
    report = {"schema": SCHEMA, "rows": list(ROWS),
              "settings": {"top_k": TOP_K, "query_sentences": QUERY_SENTENCES, "threshold": THRESHOLD,
                           "distractor_seed": DISTRACTOR_SEED, "distractor_set": distractor_set,
                           "distractors_requested": distractors, "rounds": cache.rounds},
              "distractors": summary,
              "stores": [stores[n].composition() for n in cache.rounds],
              "retrieval": {"per_round": facts, "pooled": pooled, "digest": digest(digests),
                            "distractor_concentration": concentration},
              "gates": tables}
    return report, lines


DEFINITIONS = {
    "document": "a family record or a distractor; its vector is the mean of its sentence embeddings "
                "(the standalone half of the cached CAD feature, columns 0 to 1,023), unit-normalised",
    "query_vector": "the mean embedding of the five store sentences that best match the query field by "
                    "TF-IDF cosine (no cache holds a query embedding and the encoder is not called); the "
                    "store centroid when no term matches. The query's own record's sentences are "
                    "among the matched sentences (the own-match share), so hit@5 describes this "
                    "placement as much as the retriever and is not a measure of retriever quality; "
                    "the figure with the own record's sentences masked is given beside it. Retrieval "
                    "is identical for every row, so the gate comparisons do not depend on it",
    "retrieval": "exact cosine search, top five per query, ties by store order; one retrieval per round "
                 "serves every row",
    "distractor": "the benign (label 0) sentences of a released CAD test record outside the excluded set; "
                  "one record per distinct remainder text, drawn once with seed 764, cut into passages of "
                  "at most five consecutive sentences (as even as possible), each passage a document, "
                  "the same in every round; scored by its parent record's predictions in the same "
                  "cell's released-test rows, which were made with the injected sentence still in "
                  "context",
    "document_gate": "drop a retrieved document the scorer flags (any sentence probability above 0.5); "
                     "the bag-of-words baseline scores twin and malicious records only, so controls and "
                     "distractors pass it unscored",
    "sentence_filter": "remove the sentences scoring above 0.5 and forward the rest",
    "injected_pass_through": "share of retrieved shared_malicious documents forwarded with their target "
                             "sentence",
    "twin_loss": "share of retrieved semantic twins dropped or forwarded without their target sentence "
                 "or a cue sentence (a query cue sits in the query, which no gate touches)",
    "control_loss": "share of retrieved random or keyword controls dropped or forwarded with any "
                    "sentence removed; distractor loss the same for distractors",
    "context_survival": "share of retrieved benign sentences forwarded: family records only (the "
                        "headline), all slots, and distractors only; the retrieved benign sentence "
                        "counts per kind are printed under each gate table",
    "slots": "every document in every query's top five; a document retrieved by several queries counts "
             "each time",
    "spread": "each seed's slots pooled over the rounds; mean over seeds with the population sd (ddof 0); "
              "N0, the baseline and no gate have one value",
}


def _cell(entry: dict | None) -> str:
    if entry is None or entry.get("mean") is None:
        return "n/a"
    text = f"{entry['mean']:.3f}"
    if entry.get("n", 0) > 1:
        text += f" ± {entry['sd']:.3f}"
    return text


def markdown(report: dict) -> str:
    settings, retrieval = report["settings"], report["retrieval"]["pooled"]
    lines = ["# Retrieval harness", "",
             f"Mode {report['mode']}; rounds {settings['rounds']}; top {settings['top_k']}; threshold "
             f"{settings['threshold']}; distractors {report['distractors']['chosen']} of "
             f"{settings['distractors_requested']} requested ({settings['distractor_set']}, seed "
             f"{settings['distractor_seed']}, {report['distractors']['distinct_benign_remainders']} "
             f"distinct benign remainders available, cut into {report['distractors']['passages']} "
             f"passages of {report['distractors']['passage_sentences']} sentences, at most "
             f"{report['distractors']['max_passage_sentences']} each); Phase 7 run "
             f"{report['inputs']['run_config_fingerprint'][:12]}; commit {str(report['commit'])[:12]}.", "",
             "## Retrieval (identical for every row)", "",
             "hit@5 and mean rank describe the query placement as much as the retriever: the query's "
             "own record's sentences are among its matched sentences (own-match share). The masked "
             "columns place the query without them. Retrieval is the same for every row, so the gate "
             "comparisons do not depend on it.", "",
             "| round | documents | family records | distractor passages | queries | hit@5 | mean rank | "
             "hit@5 (own sentences masked) | mean rank (masked) | own-match share | "
             "slots: malicious / twin / random / keyword / distractor | centroid queries |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for store, facts in zip(report["stores"], report["retrieval"]["per_round"]):
        kinds = facts["slots_by_kind"]
        lines.append(f"| {facts['round']} | {store['documents']} | {store['documents'] - store['by_kind'][DISTRACTOR]}"
                     f" | {store['by_kind'][DISTRACTOR]} | {facts['queries']} | {facts['hit_at_k']:.3f} | "
                     f"{facts['mean_rank']:.2f} | {facts['hit_at_k_masked']:.3f} | "
                     f"{facts['mean_rank_masked']:.2f} | {facts['own_match_share']:.3f} | " +
                     " / ".join(str(kinds[k]) for k in kinds) + f" | {facts['centroid_fallback_queries']} |")
    kinds = retrieval["slots_by_kind"]
    lines.extend([f"| all | | | | {retrieval['queries']} | {retrieval['hit_at_k']:.3f} | "
                  f"{retrieval['mean_rank']:.2f} | {retrieval['hit_at_k_masked']:.3f} | "
                  f"{retrieval['mean_rank_masked']:.2f} | {retrieval['own_match_share']:.3f} | " +
                  " / ".join(str(kinds[k]) for k in kinds) + f" | {retrieval['centroid_fallback_queries']} |", ""])
    concentration = report["retrieval"]["distractor_concentration"]
    if concentration["distractor_slots"]:
        top = concentration["top_passages"][0]
        lines.extend([f"Distractor slots: {concentration['distractor_slots']} over "
                      f"{concentration['passages_retrieved']} of {concentration['passages']} passages; the "
                      f"most retrieved passage ({top['sentences']} sentences) takes {top['slots']}, the top "
                      f"three {concentration['top_three_share']:.3f} of them.", ""])
    benign = retrieval["benign_sentences_by_kind"]
    counts = ("Retrieved benign sentences (the survival denominators, the same for every row): " +
              ", ".join(f"{kind.replace('_', ' ')} {count}" for kind, count in benign.items()) +
              f"; family {sum(c for k, c in benign.items() if k != DISTRACTOR)}, all {sum(benign.values())}.")
    columns = tuple(LABELS)
    for gate in GATES:
        title = "Document gate" if gate == DOCUMENT_GATE else "Sentence filter"
        lines.extend([f"## {title}", "", "| row | " + " | ".join(LABELS[c] for c in columns) + " |",
                      "|" + "---|" * (len(columns) + 1)])
        rows = [(row, report["gates"][gate][row]) for row in ROWS if row in report["gates"][gate]]
        for row, table in rows:
            lines.append(f"| {NAMES[row]} | " + " | ".join(_cell(table["overall"][c]) for c in columns) + " |")
        lines.extend(["", counts, ""])
        if gate == DOCUMENT_GATE:
            lines.extend(["The BoW baseline scores twin and malicious records only: controls and distractors "
                          "pass it unscored, so its control and distractor loss are zero by construction.", ""])
        family_columns = columns[:5]
        for name in BREAKDOWN:
            lines.extend([f"### {title} by {name.replace('_', ' ')}", "",
                          "| slice | row | " + " | ".join(LABELS[c] for c in family_columns) + " |",
                          "|" + "---|" * (len(family_columns) + 2)])
            values = sorted({v for _, table in rows for v in table["by"][name]})
            for value in values:
                for row, table in rows:
                    entry = table["by"][name].get(value)
                    if entry is not None:
                        lines.append(f"| {value} | {NAMES[row]} | " +
                                     " | ".join(_cell(entry[c]) for c in family_columns) + " |")
            lines.append("")
    lines.extend(["## Definitions", ""] + [f"- {name.replace('_', ' ')}: {text}"
                                            for name, text in report["definitions"].items()])
    return "\n".join(lines) + "\n"


def harness_command(args) -> dict:
    """CLI body of rag harness-run; a refusal logs its cause before the CLI exits 2."""
    from rag_cad.training.fold_driver import REFUSALS, log_refusal

    try:
        return _harness_command(args)
    except REFUSALS as error:
        log_refusal("rag harness-run", error)
        raise


def _harness_command(args) -> dict:
    import rag_cad
    from rag_cad.config import load_config
    from rag_cad.data.jsonl import load_records
    from rag_cad.operations.provenance import git_output
    from rag_cad.training.two_cache import load_two_caches

    started = time.perf_counter()
    output = local_path(args.output)
    repo = Path(rag_cad.__file__).resolve().parents[2]
    for source in (args.phase4_root, args.families, args.run, repo, Path(args.repo)):
        source = local_path(source)
        if output.is_relative_to(source) or source.is_relative_to(output):
            raise ValueError(f"Output {output} must lie outside the repository and every input "
                             f"(conflicts with {source})")
    if output.exists():
        raise ValueError(f"Output {output} exists; the harness never overwrites")
    experiment = load_config(args.experiment)
    if float(experiment.get("threshold", THRESHOLD)) != THRESHOLD:
        raise ValueError("The gate threshold is fixed at 0.5")
    mode = args.mode or experiment.get("representation")
    run_file, cells = load_run(args.run)
    config = run_file["config"]
    if config["mode"] != mode:
        raise ValueError(f"The Phase 7 run is in {config['mode']}, not {mode}")
    folds_path = local_path(args.folds)
    if sha256(folds_path) != config["folds_sha256"]:
        raise ValueError("The Phase 7 run used another fold table")
    leaked_path = local_path(args.run) / LEAKED_FILE
    if sha256(leaked_path) != run_file.get("leaked_sha256"):
        raise ValueError("leaked.json differs from the one the Phase 7 run recorded")
    cache = load_two_caches(args.phase4_root, args.families, mode, read_jsonl(folds_path))
    for key in ("d0_row_digest", "released_test_row_digest", "family_rows"):
        if cache.summary[key] != config["cache"][key]:
            raise ValueError(f"The caches differ from the Phase 7 run's ({key})")
    pooled = pooled_records(cells, set(cache.folds))
    check_complete(run_file, pooled)
    bow_path = local_path(args.bow)
    bow = json.loads(bow_path.read_text(encoding="utf-8"))
    if bow.get("input", {}).get("folds_sha256") != config["folds_sha256"]:
        raise ValueError("The bag-of-words baseline was computed on another fold table")
    records, _ = load_records(args.records)
    test_path = local_path(args.phase4_root) / ADAPTED_TEST
    test_records = read_jsonl(test_path)
    report, lines = run_harness(cache, records, test_records,
                                json.loads(leaked_path.read_text(encoding="utf-8")), cells, bow,
                                distractors=args.distractors, distractor_set=args.distractor_set)
    try:
        commit = git_output(repo, "rev-parse", "HEAD")
    except (ValueError, OSError):
        commit = "unknown"
    report = {**report, "mode": mode, "commit": commit, "identity_check": cache.identity_check,
              "inputs": {"phase4_root": str(local_path(args.phase4_root)),
                         "families": str(local_path(args.families)), "run": str(local_path(args.run)),
                         "run_config_fingerprint": run_file["config_fingerprint"],
                         "run_commit": config.get("commit"), "folds_sha256": config["folds_sha256"],
                         "leaked_sha256": run_file["leaked_sha256"], "bow_sha256": sha256(bow_path),
                         "released_test_sha256": sha256(test_path),
                         "released_test_row_digest": cache.summary["released_test_row_digest"],
                         "cells": len(cells)},
              "definitions": DEFINITIONS}
    output.mkdir(parents=True)
    write_jsonl(output / RETRIEVALS_FILE, lines)
    report["seconds"] = round(time.perf_counter() - started, 3)
    write_json(output / JSON_FILE, report)
    with (output / MARKDOWN_FILE).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown(report))
    return {"schema": SCHEMA, "output": str(output), "mode": mode, "cells": len(cells),
            "rounds": report["settings"]["rounds"], "distractors": report["distractors"]["chosen"],
            "retrieval": report["retrieval"]["pooled"], "seconds": report["seconds"]}
