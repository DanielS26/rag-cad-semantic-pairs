import json, re, sys, math, random, statistics as st
from collections import Counter, defaultdict
from pathlib import Path
from rag_cad.data import selfcheck as sc
from rag_cad.data.similarity import normalise

R = Path(sys.argv[1]); O = Path(sys.argv[2])
AUG = R/"datasets/raw/augmentation"; FAM = AUG/"families"; REV = AUG/"review"
KINDS = ["shared_malicious","semantic_benign","random_benign","keyword_benign"]
SH = {"shared_malicious":"mal","semantic_benign":"twin","random_benign":"rand","keyword_benign":"kw"}
recs = []
for n in range(1,21):
    for r in sc.read_jsonl(FAM/f"pilot_batch_{n:02d}.jsonl"):
        r["_batch"] = n; recs.append(r)
manifest = {e["family_id"]: e for e in sc.read_jsonl(AUG/"family_manifest.jsonl")}
fams = sc.group_families(recs)
for r in recs:
    if not r.get("family_id"): r["family_id"] = r["group_id"].replace("unit_", "")
answers = {}
for n in range(1,21):
    a = json.loads((REV/f"semantic_answers_batch_{n:02d}.json").read_text(encoding="utf-8"))
    for k,v in a.items():
        if k.startswith("pilot_"): answers[k]=v
def nt(r): return [s for s in r["sentences"] if not s["is_target"]]
def wj(name, obj): (O/name).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
def pct(a,b): return round(100*a/b,1) if b else None
md = []
def table(head, rows):
    md.append("| "+" | ".join(map(str,head))+" |"); md.append("|"+"---|"*len(head))
    for r in rows: md.append("| "+" | ".join(map(str,r))+" |")
    md.append("")
bykind = {k:[r for r in recs if r["condition_source"]==k] for k in KINDS}

# ---------------- 1 full-set checks
md.append("# 200-family audit: measurements (D-20261016-46 d)\n")
md.append("Repository at phase5-batch-20 2b598dc; 800 records, 200 families. Measurement only; no repository file changed.\n")
md.append("## 1. Full-set checks\n")
ex = {}
for line in (O/"selfcheck_exits.txt").read_text().split("\n"):
    if line.strip(): b,stg,c = line.split(); ex[(int(b),stg)] = int(c)
md.append("prescreen over all_800.jsonl (manifest as --families): exit "+(O/"prescreen_exit.txt").read_text().split()[-1]
          +"; 200 families passed, 0 failed, role counts 25 each, cue positions 40 each, 200 'awaiting_review' family warnings (manifest status candidate).\n")
md.append("validate over all_800.jsonl: exit "+(O/"validate_exit.txt").read_text().split()[-1]
          +"; 800 records, 2816 sentence rows, 0 exact duplicate records, 0 cross-group exact or near (0.8) duplicates, 0 families with differing targets.\n")
sc_rows = []; retro = []; allcounts = {}
for n in range(1,21):
    cur = json.loads((O/f"selfcheck_{n:02d}_drafting.json").read_text(encoding="utf-8"))
    old = json.loads((REV/f"selfcheck_batch_{n:02d}.json").read_text(encoding="utf-8"))
    cnt = {}
    for cid, c in cur["mechanical"].items():
        if c["status"] in ("FAIL","WARN"):
            det = c["details"] if isinstance(c["details"], list) else []
            cnt[cid] = f'{c["status"]} {len(det)}'
            oc = old["mechanical"].get(cid, {"status":"absent","details":[]})
            olddet = {json.dumps(d, sort_keys=True) for d in (oc["details"] if isinstance(oc["details"], list) else [])}
            new = [d for d in det if json.dumps(d, sort_keys=True) not in olddet]
            if new or oc["status"] in ("PASS","SKIP","absent"):
                for d in (new or [{"note":"status changed, no detail list"}]):
                    retro.append({"batch":n,"check":cid,"status_now":c["status"],"status_at_finalisation":oc["status"],"item":d})
    allcounts[n] = cnt
    nf = sum(1 for v in cnt.values() if v.startswith("FAIL")); nw = sum(1 for v in cnt.values() if v.startswith("WARN"))
    sc_rows.append([f"{n:02d}", ex[(n,"drafting")], ex[(n,"review")], cur["overall"], old["overall"], nf, nw, "; ".join(f"{k} {v}" for k,v in cnt.items())])
md.append("Self-check per batch (current checker, --previous every earlier batch, prompt v3, semantic answers). Exit codes for --stage drafting and --stage review. Counts are detail items per FAIL/WARN check.\n")
table(["batch","exit drafting","exit review","overall now","overall at finalisation","FAIL checks","WARN checks","check: status items"], sc_rows)
m12 = [x for x in retro if x["check"].startswith("M12")]
md.append(f"Retroactive view (items in a FAIL/WARN check now that are absent from the batch's finalised report in review/): {len(retro)} items "
          f"({sum(1 for x in retro if x['status_now']=='FAIL')} under FAIL checks, {sum(1 for x in retro if x['status_now']=='WARN')} under WARN checks). "
          f"M12 accounts for {len(m12)}. Full list in retroactive.json.\n")
rc = Counter((x["batch"], x["check"], x["status_now"], x["status_at_finalisation"]) for x in retro)
table(["batch","check","status now","status at finalisation","new items"], [[f"{b:02d}",c,s,o,k] for (b,c,s,o),k in sorted(rc.items())])
nonm12 = [x for x in retro if not x["check"].startswith("M12")]
md.append("M12 example items: " + "; ".join(json.dumps(x["item"], ensure_ascii=False)[:200] for x in m12[:3]) + "\n")
v2 = (O/"selfcheck_v2prompt_exits.txt").read_text().split()
md.append("M12 check: batches 01 to 05 carry the DRAFTING_PROMPT_v2 hash (30d7b72f), batches 06 to 20 the v3 hash (09d56ad2). Rerun of 01 to 05 with --prompt v2: exits " + ", ".join(f"{a}:{b}" for a,b in zip(v2[::2], v2[1::2])) + "; M12 then passes, so the 200 M12 items are a prompt-version artefact of the v3 rerun. Batch 05 still FAILs S_semantic_answers: ten S13 answers are missing (pilot_0041 to pilot_0050; S13 was required after batch 05 was finalised).\n")
def pkey(x):
    it = x["item"]
    return (x["check"], x["status_now"], (it.get("problem") or ("S13 answer missing (required YES)" if it.get("question")=="S13" else it.get("question") or it.get("note","")))[:150])
gc = Counter(pkey(x) for x in nonm12); gb = defaultdict(set)
for x in nonm12: gb[pkey(x)].add(x["batch"])
md.append(f"Retroactive items other than M12 ({len(nonm12)}), grouped by check and problem (per-item list in retroactive.json):\n")
table(["check","status","problem","items","batches"], [[c,s_,p_,k,",".join(f"{b:02d}" for b in sorted(gb[(c,s_,p_)]))] for (c,s_,p_),k in gc.most_common()])
wj("selfcheck_summary.json", {"exits": {f"{b:02d} {s}":c for (b,s),c in ex.items()}, "counts": allcounts})
wj("retroactive.json", retro)

# ---------------- 2 lexical tells
md.append("## 2. Lexical tells by record kind\n")
L = {}
def cue_ids(fid):
    return sc._cue_sentence_ids(manifest[fid], fams[fid]["semantic_benign"])
rows=[]; L["a"]={}
for k in KINDS:
    rs = bykind[k]; hit = sum(1 for r in rs if any(s["text"].rstrip().endswith(":") for s in nt(r)))
    ns = sum(len(nt(r)) for r in rs); hs = sum(1 for r in rs for s in nt(r) if s["text"].rstrip().endswith(":"))
    qc = sum(1 for r in rs if r["query"].rstrip().endswith(":"))
    anyc = sum(1 for r in rs if any(":" in s["text"] for s in nt(r)))
    L["a"][k] = {"records":len(rs),"records_with_colon_ended_sentence":hit,"sentences":ns,"colon_ended_sentences":hs,"queries_ending_colon":qc,"records_with_any_colon_in_nontarget":anyc}
    rows.append([SH[k], f"{hit}/{len(rs)} ({pct(hit,len(rs))}%)", f"{hs}/{ns} ({pct(hs,ns)}%)", qc, anyc])
md.append("(a) Non-target sentences ending in a colon.\n"); table(["kind","records with >=1","sentences","queries ending ':'","records with any ':' in non-target"], rows)
cuecol = []; cuetot = 0; colpos = Counter(); colrole = Counter()
for fid in fams:
    tw = fams[fid]["semantic_benign"]; ids = cue_ids(fid); pos = manifest[fid]["cue_position"]
    cs = [s for s in tw["sentences"] if s["sentence_id"] in ids and not s["is_target"]]
    cuetot += 1 if cs else 0
    if any(s["text"].rstrip().endswith(":") for s in cs): cuecol.append(fid); colpos[pos]+=1; colrole[manifest[fid]["semantic_role"]]+=1
twin_noncue_colon = [r["family_id"] for r in bykind["semantic_benign"] if any(s["text"].rstrip().endswith(":") for s in nt(r) if s["sentence_id"] not in cue_ids(r["family_id"]))]
colbatch = Counter((int(f[-4:])-1)//10+1 for f in cuecol)
L["a"]["twin_cue_sentences"] = {"twins_with_located_cue_sentence":cuetot,"twins_cue_ending_colon":len(cuecol),"families":cuecol,"by_cue_position":dict(colpos),"by_role":dict(colrole),"by_batch":dict(sorted(colbatch.items())),"twins_with_colon_outside_cue_sentence":twin_noncue_colon}
md.append(f"Twin cue sentences (located with selfcheck._cue_sentence_ids; the 40 query-position twins have none): {len(cuecol)} of {cuetot} have one ending in a colon; by cue position {dict(colpos)}; by role {dict(colrole)}; by batch {dict(sorted(colbatch.items()))}. Twins with a colon-ended non-target sentence outside the located cue: {len(twin_noncue_colon)} ({', '.join(twin_noncue_colon)}).\n")
OPEN = ["That","Under the","After","This","Please"]
def opens(t, o): return re.match(r"\s*"+re.escape(o)+r"\b", t) is not None
rows=[]; L["b"]={}
for k in KINDS:
    ss = [s["text"] for r in bykind[k] for s in nt(r)]
    L["b"][k] = {o: [sum(opens(t,o) for t in ss), len(ss)] for o in OPEN}
    rows.append([SH[k]]+[f"{L['b'][k][o][0]} ({pct(*L['b'][k][o])}%)" for o in OPEN]+[len(ss)])
cs_all = [s["text"] for fid in fams for s in fams[fid]["semantic_benign"]["sentences"] if s["sentence_id"] in cue_ids(fid) and not s["is_target"]]
L["b"]["twin_cue_sentences"] = {o:[sum(opens(t,o) for t in cs_all), len(cs_all)] for o in OPEN}
rows.append(["twin cue sentences"]+[f"{L['b']['twin_cue_sentences'][o][0]} ({pct(*L['b']['twin_cue_sentences'][o])}%)" for o in OPEN]+[len(cs_all)])
qopen = {k:{o: sum(opens(r["query"],o) for r in bykind[k]) for o in OPEN} for k in KINDS}
recshare = {k: {o: sum(1 for r in bykind[k] if any(opens(s["text"],o) for s in nt(r))) for o in OPEN} for k in KINDS}
L["b"]["records_with_opener"] = recshare
that_f = sorted({fid for fid in fams for s in fams[fid]["semantic_benign"]["sentences"] if s["sentence_id"] in cue_ids(fid) and not s["is_target"] and opens(s["text"],"That")})
L["b"]["twin_cue_that_families"] = that_f; L["b"]["that_and_colon_overlap"] = sorted(set(that_f)&set(cuecol))
L["b"]["either_that_or_colon"] = len(set(that_f)|set(cuecol)); L["b"]["queries_with_opener"] = qopen
md.append("(b) Non-target sentences opening with each word (count, share of non-target sentences).\n"); table(["kind"]+OPEN+["n sentences"], rows)
md.append(f"Twin cue sentences opening with That: {len(that_f)} families; overlap with the colon-ended cues: {len(set(that_f)&set(cuecol))}; twins carrying either tell: {len(set(that_f)|set(cuecol))} of 200. That-cue families by batch {dict(sorted(Counter((int(f[-4:])-1)//10+1 for f in that_f).items()))}; by cue position {dict(Counter(manifest[f]['cue_position'] for f in that_f))}; by role {dict(Counter(manifest[f]['semantic_role'] for f in that_f))}.\n")
md.append("Records with at least one such sentence (of 200): " + "; ".join(f"{SH[k]} " + ", ".join(f"{o} {v}" for o,v in recshare[k].items()) for k in KINDS) + "\n")
L["c"]={}
def qw(q,n): return " ".join(normalise(q).split()[:n])
rows=[]
for n_ in (1,2):
    dist = {k: Counter(qw(r["query"],n_) for r in bykind[k]) for k in KINDS}
    L["c"][f"first_{n_}"] = {k: dict(dist[k].most_common()) for k in KINDS}
    keys = set(dist["semantic_benign"])|set(dist["shared_malicious"])
    for w in sorted(keys, key=lambda w: -abs(dist["semantic_benign"][w]-dist["shared_malicious"][w])):
        d = (dist["semantic_benign"][w]-dist["shared_malicious"][w])/2
        if abs(d) > 10: rows.append([n_, w, dist["shared_malicious"][w], dist["semantic_benign"][w], dist["random_benign"][w], dist["keyword_benign"][w], f"{d:+.1f}"])
md.append("(c) Query openers. Top first words by kind: " + "; ".join(f"{SH[k]}: " + ", ".join(f"{w} {c}" for w,c in Counter(L['c']['first_1'][k]).most_common(6)) for k in KINDS) + "\n")
md.append("Top first two words: " + "; ".join(f"{SH[k]}: " + ", ".join(f"{w} {c}" for w,c in Counter(L['c']['first_2'][k]).most_common(5)) for k in KINDS) + "\n")
md.append("Openers whose share differs by more than ten points between twin and malicious (counts of 200):\n")
table(["words","opener","mal","twin","rand","kw","twin-mal pts"], rows or [["-","none","","","","",""]])
L["d"]={}; rows=[]
for k in KINDS:
    c = [sc.chars(r) for r in bykind[k]]; s_ = [len(r["sentences"]) for r in bykind[k]]; q = [len(r["query"]) for r in bykind[k]]
    L["d"][k] = {"mean_chars":round(st.mean(c),1),"median_chars":st.median(c),"mean_sentences":round(st.mean(s_),2),"median_sentences":st.median(s_),"mean_query_chars":round(st.mean(q),1)}
    rows.append([SH[k]]+list(L["d"][k].values()))
md.append("(d) Length (characters over sentences; query separately).\n"); table(["kind","mean chars","median chars","mean sentences","median sentences","mean query chars"], rows)
tl = {}
for fid,m in fams.items():
    b = m["shared_malicious"]["_batch"]; tl.setdefault(b,[]).append(sc.chars(m["semantic_benign"])>sc.chars(m["shared_malicious"]))
tot = sum(sum(v) for v in tl.values())
diffs = [sc.chars(m["semantic_benign"])-sc.chars(m["shared_malicious"]) for m in fams.values()]
L["d"]["twin_longer"] = {"overall":[tot,200], "per_batch":{b:sum(v) for b,v in sorted(tl.items())}, "twin_minus_mal_mean":round(st.mean(diffs),1), "twin_minus_mal_median":st.median(diffs)}
md.append(f"Twin longer than malicious: {tot}/200 ({pct(tot,200)}%); twin minus malicious characters mean {L['d']['twin_longer']['twin_minus_mal_mean']}, median {L['d']['twin_longer']['twin_minus_mal_median']}. Per batch (of 10): " + ", ".join(f"{b:02d}:{sum(v)}" for b,v in sorted(tl.items())) + "\n")
def toks(r): return normalise(" ".join([r["query"]]+[s["text"] for s in nt(r)])).split()
def tok_alpha(r): return [t for t in toks(r) if re.fullmatch(r"[a-z]+", t)]
def logodds(A, B, top=20, mindf=10):
    ca, cb = Counter(), Counter(); df = Counter()
    for r in A: t = tok_alpha(r); ca.update(t); df.update(set(t))
    for r in B: t = tok_alpha(r); cb.update(t); df.update(set(t))
    V = len(set(ca)|set(cb)); na, nb = sum(ca.values()), sum(cb.values())
    s_ = {w: math.log((ca[w]+1)/(na+V)) - math.log((cb[w]+1)/(nb+V)) for w in df if df[w] >= mindf}
    o = sorted(s_, key=lambda w: -s_[w])
    f = lambda w: {"word":w,"log_odds":round(s_[w],2),"count_a":ca[w],"count_b":cb[w],"records":df[w]}
    return [f(w) for w in o[:top]], [f(w) for w in o[::-1][:top]]
L["e"]={}
for name, A, B in [("twin_vs_mal", bykind["semantic_benign"], bykind["shared_malicious"]), ("twin_vs_controls", bykind["semantic_benign"], bykind["random_benign"]+bykind["keyword_benign"])]:
    a,b = logodds(A,B); L["e"][name] = {"a_over_b":a,"b_over_a":b}
    md.append(f"(e) Log-odds {name.replace('_',' ')} (add-one, words in >=10 records; non-target sentences plus query). word log-odds (count A/count B).\n")
    table(["#", "favours twin", "favours "+("malicious" if "mal" in name else "controls")],
          [[i+1, f"{x['word']} {x['log_odds']} ({x['count_a']}/{x['count_b']})", f"{y['word']} {y['log_odds']} ({y['count_a']}/{y['count_b']})"] for i,(x,y) in enumerate(zip(a,b))])
L["f"]={}; rows=[]
for k in KINDS:
    hits=[]
    for r in bykind[k]:
        tgt = sc.target_text(fams[r["family_id"]]["shared_malicious"]) or ""
        ids = {d for d in sc.DIGITS_RE.findall(tgt) if len(d)>=4}
        others = " ".join([r["query"]]+[s["text"] for s in nt(r)])
        shd = sorted(ids & set(sc.DIGITS_RE.findall(others)))
        if shd: hits.append({"family_id":r["family_id"],"digits":shd})
    L["f"][k]=hits; rows.append([SH[k], len(hits), ", ".join(h["family_id"][-4:] for h in hits)])
ntgt = sum(1 for fid in fams if any(len(d)>=4 for d in sc.DIGITS_RE.findall(sc.target_text(fams[fid]['shared_malicious']) or "")))
md.append(f"(f) Digit strings (>=4 digits) of the family's target echoed in the record's query or non-target sentences ({ntgt} targets carry such a string; controls compared with the family target).\n")
table(["kind","records","families"], rows)
L["g"]={}
words = list(sc.WATCH_TOKENS)+list(sc.POLICY_WORDS)+list(sc.POLICY_LEXICON)
rows=[]
for w in words:
    row = {k: sum(1 for r in bykind[k] if w in toks(r)) for k in KINDS}; L["g"][w]=row
    rows.append([w]+[row[k] for k in KINDS])
md.append("(g) Records whose query or non-target sentences contain each word (selfcheck.WATCH_TOKENS, POLICY_WORDS, POLICY_LEXICON).\n")
table(["word","mal","twin","rand","kw"], rows)
wj("lexical_tells.json", L)

# ---------------- 3 shortcut probe
md.append("## 3. Shortcut probe\n")
md.append("scikit-learn is not importable in the repository interpreter (ModuleNotFoundError), so the probe is a multinomial naive Bayes written here (Laplace alpha 1, unigrams plus bigrams over selfcheck.normalise tokens, which drop punctuation), five folds grouped by family_id (families shuffled with seed 764; each family's records in one fold). A second variant adds punctuation tokens, a colon-ended-sentence token and the first word of each sentence and of the query. Classes are balanced (200 each); chance is 50%.\n")
fids = sorted(fams); random.Random(764).shuffle(fids); fold = {f:i%5 for i,f in enumerate(fids)}
PUN = re.compile("[:;\"“”'’()—–-]")
def feats(r, with_target, punct):
    parts = [("Q", r["query"])] + [("S", s["text"]) for s in r["sentences"] if with_target or not s["is_target"]]
    out=[]
    for tag,t in parts:
        tk = normalise(t).split()
        out += tk + [a+"_"+b for a,b in zip(tk,tk[1:])]
        if punct:
            out += ["P:"+c for c in PUN.findall(t)]
            if t.rstrip().endswith(":"): out.append("P:END_COLON")
            out.append(f"{tag}:FIRST_{tk[0] if tk else ''}")
    return out
def nb_train(X, y):
    cnt = {0:Counter(),1:Counter()}; prior=Counter(y)
    for x,l in zip(X,y): cnt[l].update(x)
    V = set(cnt[0])|set(cnt[1]); tot={l:sum(cnt[l].values()) for l in (0,1)}
    return cnt, prior, V, tot
def nb_logp(model, x, l):
    cnt, prior, V, tot = model
    return math.log(prior[l]/sum(prior.values())) + sum(math.log((cnt[l][w]+1)/(tot[l]+len(V))) for w in x if w in V)
def probe(kA, kB, with_target, punct=False):
    data = [(feats(r,with_target,punct), 1 if r["condition_source"]==kA else 0, r["family_id"]) for r in bykind[kA]+bykind[kB]]
    correct=0; tp=Counter(); per=[]; pair_ok=0; pair_n=0
    for f in range(5):
        tr = [d for d in data if fold[d[2]]!=f]; te=[d for d in data if fold[d[2]]==f]
        m = nb_train([d[0] for d in tr],[d[1] for d in tr]); c=0
        mg = {}
        for x,l,fid_ in te: mg.setdefault(fid_,{})[l] = nb_logp(m,x,1)-nb_logp(m,x,0)
        for v in mg.values():
            if 0 in v and 1 in v: pair_n+=1; pair_ok += v[1]>v[0]
        for x,l,_ in te:
            p = 1 if nb_logp(m,x,1)>nb_logp(m,x,0) else 0
            c += p==l; tp[(l,p==l)]+=1
        per.append(round(c/len(te),3)); correct+=c
    acc = correct/len(data); bal = (tp[(1,True)]/(tp[(1,True)]+tp[(1,False)]) + tp[(0,True)]/(tp[(0,True)]+tp[(0,False)]))/2
    cnt,prior,V,tot = nb_train([d[0] for d in data],[d[1] for d in data])
    df = Counter()
    for d in data: df.update(set(d[0]))
    s_ = {w: math.log((cnt[1][w]+1)/(tot[1]+len(V))) - math.log((cnt[0][w]+1)/(tot[0]+len(V))) for w in V if df[w]>=5}
    o = sorted(s_, key=lambda w:-s_[w])
    return {"A":kA,"B":kB,"with_target":with_target,"punct_features":punct,"accuracy":round(acc,3),"paired_accuracy":round(pair_ok/pair_n,3),"balanced_accuracy":round(bal,3),"fold_acc":per,
            "top_A":[(w,round(s_[w],2),cnt[1][w],cnt[0][w]) for w in o[:20]],"top_B":[(w,round(s_[w],2),cnt[1][w],cnt[0][w]) for w in o[::-1][:20]]}
P=[]
for kA,kB in [("semantic_benign","shared_malicious"),("semantic_benign","random_benign"),("semantic_benign","keyword_benign")]:
    for wt in (False, True):
        for pu in (False, True):
            P.append(probe(kA,kB,wt,pu))
wj("shortcut_probe.json", P)
table(["A vs B","target included","punctuation/opener features","accuracy","balanced acc","paired acc (A scored above B within family)","fold acc"],
      [[f"{SH[p['A']]} vs {SH[p['B']]}", p["with_target"], p["punct_features"], p["accuracy"], p["balanced_accuracy"], p["paired_accuracy"], p["fold_acc"]] for p in P])
for p in P:
    if p["B"]=="shared_malicious" or (not p["with_target"] and not p["punct_features"]):
        md.append(f"Top features (min 5 records), {SH[p['A']]} vs {SH[p['B']]}, target {'in' if p['with_target'] else 'out'}, punctuation features {'on' if p['punct_features'] else 'off'} (feature count A/count B).\n")
        table(["#","favours "+SH[p["A"]],"favours "+SH[p["B"]]], [[i+1, f"{a[0]} ({a[2]}/{a[3]})", f"{b[0]} ({b[2]}/{b[3]})"] for i,(a,b) in enumerate(zip(p["top_A"],p["top_B"]))])
pm = {(p["B"],p["with_target"],p["punct_features"]):p["accuracy"] for p in P}
md.append(f"Reading: the twin and its malicious partner carry the same target sentence, so including it adds no signal for that pair; anything above 50% comes from the query and context. Twin against malicious: {pm[('shared_malicious',False,False)]:.1%} without the target, {pm[('shared_malicious',True,False)]:.1%} with it, {pm[('shared_malicious',False,True)]:.1%} with punctuation and opener features. That share of labels is guessable from framing words alone, without reading the target against the cue; a scorer trained on this set can reach it by learning the twin register. Twin against controls: high with the target is expected (controls have no target sentence); without the target it measures how far the twin register differs from the controls.\n")

# ---------------- 4 register
md.append("## 4. Register at 200\n")
G={}
mal = {fid:fams[fid]["shared_malicious"] for fid in fams}
role = {fid:manifest[fid]["semantic_role"] for fid in fams}; pos={fid:manifest[fid]["cue_position"] for fid in fams}
G["role"]=Counter(role.values()); G["cue_position"]=Counter(pos.values())
G["role_by_position"]={r_:dict(Counter(pos[f] for f in fams if role[f]==r_)) for r_ in sorted(G["role"])}
G["domain"]=Counter(mal[f]["domain"] for f in fams)
G["domain_by_role"]={d:dict(Counter(role[f] for f in fams if mal[f]["domain"]==d)) for d in sorted(G["domain"])}
G["source_dataset"]=Counter(mal[f]["provenance"]["source_dataset"] for f in fams)
asb = [json.loads(l) for l in open(R.parent/"handover_2026-10-13/sources/asb_all_attack_tools.jsonl", encoding="utf-8")]
RANGES=[(200,"system_admin"),(220,"financial"),(240,"legal"),(260,"medical"),(280,"education"),(300,"psychological"),(320,"ecommerce"),(340,"academic"),(360,"aerospace"),(380,"autonomous_driving")]
agent={}; mism=[]
for f in fams:
    sid = mal[f]["provenance"]["source_record_id"]
    if sid.startswith("asb:"):
        i = int(sid.split(":")[-1]); a = asb[i]["Corresponding Agent"]; agent[f]=a
        stated = [n for lo,n in RANGES if lo<=i<lo+20]
        if not stated or not a.startswith(stated[0]): mism.append({"family_id":f,"row":i,"stated":stated[0] if stated else None,"file":a})
G["asb_agent_from_file"]=Counter(agent.values()); G["asb_range_mismatches"]=mism
G["asb_rows"]=sorted(int(mal[f]["provenance"]["source_record_id"].split(":")[-1]) for f in agent)
G["bipia_subsets"]=Counter(":".join(mal[f]["provenance"]["source_record_id"].split(":")[1:3]) for f in fams if mal[f]["provenance"]["source_record_id"].startswith("bipia:"))
G["attack_goal"]=Counter(mal[f].get("attack_goal") for f in fams)
G["sentence_count_mal"]=Counter(len(mal[f]["sentences"]) for f in fams)
G["sentence_count_twin"]=Counter(len(fams[f]["semantic_benign"]["sentences"]) for f in fams)
hn = {f: sorted(t for t in sc.SECURITY_TOPIC if t in normalise(sc.context_text(mal[f])).split()) for f in fams}
G["hard_negatives"]={f:v for f,v in hn.items() if v}
G["weak_cue"]=[f for f in fams if sc.WEAK_CUE_MARKER in manifest[f].get("justification","")]
dev = {f: sc.DEVICE_MARKER.findall(manifest[f].get("justification","")) for f in fams}
gen = {f: sc.MECHANISM_MARKER.findall(manifest[f].get("justification","")) for f in fams}
G["untagged_device"]=[f for f in fams if not dev[f]]; G["untagged_genus"]=[f for f in fams if not gen[f]]
G["genus_per_role"]={r_:dict(Counter(g for f in fams if role[f]==r_ for g in gen[f]).most_common()) for r_ in sorted(G["role"])}
G["device_per_role"]={r_:dict(Counter(d for f in fams if role[f]==r_ for d in dev[f]).most_common()) for r_ in sorted(G["role"])}
G["genus_overall"]=dict(Counter(g for f in fams for g in gen[f]).most_common())
G["s12_window_fail"]=[f for f in fams if not sc.s12_window_ok(f, str(answers.get(f,{}).get("S12","")))]
G["s12_names_no_family"]=[f for f in fams if not sc.FAMILY_NUMBER.findall(str(answers.get(f,{}).get("S12","")))]
G["boundary"]={f:manifest[f]["justification"][:400] for f in fams if f=="pilot_0153" or re.search(r"boundar", manifest[f].get("justification",""), re.I)}
G["boundary_in_answers"]=[f for f in fams if re.search(r"boundar", json.dumps(answers.get(f,{})), re.I)]
for k in ("role","cue_position","domain","source_dataset","asb_agent_from_file","bipia_subsets","attack_goal","sentence_count_mal","sentence_count_twin"):
    G[k]=dict(sorted(Counter(G[k]).items(), key=lambda kv:str(kv[0])))
wj("register.json", G)
for k in ("role","cue_position","domain","source_dataset","asb_agent_from_file","bipia_subsets","attack_goal","sentence_count_mal","sentence_count_twin"):
    md.append(f"- {k}: " + ", ".join(f"{a} {b}" for a,b in G[k].items()))
md.append(f"- ASB rows used: {G['asb_rows'][0]} to {G['asb_rows'][-1]} ({len(set(G['asb_rows']))} distinct of {len(G['asb_rows'])}); the stated row ranges disagree with the file's 'Corresponding Agent' for {len(mism)} of {len(agent)} ASB families, so the counts use the file.\n")
P_ = sorted(G["cue_position"]); md.append("Role by cue position:\n")
table(["role"]+P_, [[r_]+[G["role_by_position"][r_].get(p,0) for p in P_] for r_ in sorted(G["role"])])
D_ = sorted(G["role"]); md.append("Domain by role:\n")
table(["domain"]+D_, [[d]+[G["domain_by_role"][d].get(r_,0) for r_ in D_] for d in sorted(G["domain"])])
hk = Counter("planted text" if set(v)&sc.PLANTED_TEXT_TOKENS else "security in general" for v in G["hard_negatives"].values())
md.append(f"Hard negatives (malicious query or context with an M16 SECURITY_TOPIC token): {len(G['hard_negatives'])} of 200 ({dict(hk)}). Weak-cue families: {len(G['weak_cue'])} ({', '.join(G['weak_cue'])}).\n")
ub = lambda L_: dict(sorted(Counter((int(f[-4:])-1)//10+1 for f in L_).items()))
md.append(f"Untagged device: {len(G['untagged_device'])} families, by batch {ub(G['untagged_device'])}; untagged genus: {len(G['untagged_genus'])}, by batch {ub(G['untagged_genus'])}.\n")
md.append("Genus register per role:\n")
table(["role","tagged","genera at >=2","singletons"], [[r_, sum(v.values()), ", ".join(f"{g} {c}" for g,c in v.items() if c>=2), sum(1 for c in v.values() if c==1)] for r_,v in G["genus_per_role"].items()])
md.append("Genera at two or more over the whole set: " + ", ".join(f"{g} {c}" for g,c in G["genus_overall"].items() if c>=2) + f"; {sum(1 for c in G['genus_overall'].values() if c==1)} singleton genera.\n")
md.append("Device slugs per role (distinct/tagged): " + "; ".join(f"{r_} {len(v)}/{sum(v.values())}" + (" (repeats: " + ", ".join(f"{d} {c}" for d,c in v.items() if c>=2) + ")" if any(c>=2 for c in v.values()) else "") for r_,v in G["device_per_role"].items()) + "\n")
md.append(f"S12 window (selfcheck.s12_window_ok over all answers files): {len(G['s12_window_fail'])} twins name only families from the same or the previous batch: {', '.join(G['s12_window_fail']) or 'none'}. Twins whose S12 names no family id: {len(G['s12_names_no_family'])}.\n")
md.append("Role-boundary cases (pilot_0153 and manifest justifications mentioning a boundary): " + "; ".join(f"{f} [{role[f]}, {pos[f]}]" for f in G["boundary"]) + f". Answers mentioning a boundary: {', '.join(G['boundary_in_answers']) or 'none'}.\n")

# ---------------- 5 duplicates
md.append("## 5. Duplicates and near-duplicates\n")
qd = defaultdict(list); sd = defaultdict(list)
for r in recs:
    qd[normalise(r["query"])].append(r["record_id"])
    for s in r["sentences"]: sd[normalise(s["text"])].append((r["record_id"], r["family_id"], s["is_target"]))
dq = {q:v for q,v in qd.items() if len(v)>1}
dq_x = {q:v for q,v in dq.items() if len({x[:10] for x in v})>1}
ds_x = {t:v for t,v in sd.items() if len({x[1] for x in v})>1}
ds_in = {t:v for t,v in sd.items() if len(v)>1 and len({x[1] for x in v})==1 and not any(x[2] for x in v)}
pool = [(r["family_id"], r["record_id"], s["text"], set(normalise(s["text"]).split())) for r in recs for s in nt(r)]
seen=set(); uniq=[]
for p in pool:
    key=(p[0], normalise(p[2]))
    if key not in seen: seen.add(key); uniq.append(p)
pairs=[]
for i in range(len(uniq)):
    fi, ri, ti, si = uniq[i]
    for j in range(i+1, len(uniq)):
        fj, rj, tj, sj = uniq[j]
        if fi==fj: continue
        inter = len(si & sj)
        if inter < 4: continue
        jac = inter/len(si|sj)
        if jac >= 0.3: pairs.append((round(jac,3), ri, rj, ti, tj))
pairs.sort(key=lambda x:-x[0]); top = pairs[:50]
wj("duplicates.json", {"duplicate_queries_any":dq, "duplicate_queries_across_families":dq_x, "duplicate_sentences_across_families":ds_x,
                       "duplicate_nontarget_sentences_within_family_count":len(ds_in), "top50_jaccard":top, "pairs_jaccard_ge_0_5":sum(1 for p in pairs if p[0]>=0.5)})
md.append(f"Exact duplicate queries (normalised): {len(dq)} strings shared by more than one record, {len(dq_x)} across families. Exact duplicate sentences across families: {len(ds_x)}. Within families, {len(ds_in)} non-target sentence strings repeat across records (twin and malicious otherwise use different context sentences).\n")
md.append(f"Closest non-target sentence pairs across families by token Jaccard ({len(uniq)} distinct sentences per family; {sum(1 for p in pairs if p[0]>=0.5)} pairs at >=0.5). Top ten (texts in duplicates.json):\n")
table(["#","Jaccard","record A","record B"], [[i+1,p[0],p[1],p[2]] for i,p in enumerate(top[:10])])
(O/"audit200_report.md").write_text("\n".join(md), encoding="utf-8")
print("ok", len(retro), len(nonm12))
