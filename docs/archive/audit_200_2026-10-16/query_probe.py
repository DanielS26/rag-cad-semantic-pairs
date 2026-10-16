"""Query probe: same NB code and folds as minpair_probe.py; queries only, sentences only, query-cue families left out, query swap what-if."""
import json, sys, math, random
from collections import Counter, defaultdict
from pathlib import Path
from rag_cad.data import selfcheck as sc
from rag_cad.data.similarity import normalise
R = Path(sys.argv[1]); OUTD = Path(sys.argv[2])
AUG = R/"datasets/raw/augmentation"; FAM = AUG/"families"
recs = []
for n in range(1,21):
    for r in sc.read_jsonl(FAM/f"pilot_batch_{n:02d}.jsonl"):
        r["_batch"] = n; recs.append(r)
fams = sc.group_families(recs)
for r in recs:
    if not r.get("family_id"): r["family_id"] = r["group_id"].replace("unit_", "")
man = {e["family_id"]: e for e in sc.read_jsonl(AUG/"family_manifest.jsonl")}
fids = sorted(fams); random.Random(764).shuffle(fids); fold = {f:i%5 for i,f in enumerate(fids)}
def tok(t):
    tk = normalise(t).split(); return tk + [a+"_"+b for a,b in zip(tk,tk[1:])]
def F_full(r): return tok(r["query"]) + [w for s in r["sentences"] if not s["is_target"] for w in tok(s["text"])]
def F_q(r): return tok(r["query"])
def F_s(r): return [w for s in r["sentences"] if not s["is_target"] for w in tok(s["text"])]
def nb_train(X, y):
    cnt = {0:Counter(),1:Counter()}; prior=Counter(y)
    for x,l in zip(X,y): cnt[l].update(x)
    V = set(cnt[0])|set(cnt[1]); tot={l:sum(cnt[l].values()) for l in (0,1)}
    return cnt, prior, V, tot
def nb_logp(model, x, l):
    cnt, prior, V, tot = model
    return math.log(prior[l]/sum(prior.values())) + sum(math.log((cnt[l][w]+1)/(tot[l]+len(V))) for w in x if w in V)
pairs = {fid:(m["semantic_benign"], m["shared_malicious"]) for fid,m in fams.items() if m.get("semantic_benign") and m.get("shared_malicious")}
nonq = {f for f in pairs if man[f]["cue_position"] != "query"}
def run(name, feat, keep=None, swap=False):
    data = []
    for fid,(t,mal) in pairs.items():
        if keep is not None and fid not in keep: continue
        tt, mm = t, mal
        if swap: tt = dict(t, query=mal["query"]); mm = dict(mal, query=t["query"])
        data.append((feat(tt),1,fid)); data.append((feat(mm),0,fid))
    correct=0; tp=Counter(); margins={}
    for f in range(5):
        tr=[d for d in data if fold[d[2]]!=f]; te=[d for d in data if fold[d[2]]==f]
        m = nb_train([d[0] for d in tr],[d[1] for d in tr])
        for x,l,fid in te:
            mg = nb_logp(m,x,1)-nb_logp(m,x,0); margins.setdefault(fid,{})[l]=mg
            p = 1 if mg>0 else 0; correct += p==l; tp[(l,p==l)]+=1
    acc = correct/len(data); bal = (tp[(1,True)]/(tp[(1,True)]+tp[(1,False)]) + tp[(0,True)]/(tp[(0,True)]+tp[(0,False)]))/2
    pair = sum(v[1]>v[0] for v in margins.values())/len(margins)
    cnt,prior,V,tot = nb_train([d[0] for d in data],[d[1] for d in data]); df=Counter()
    for d in data: df.update(set(d[0]))
    s_ = {w: math.log((cnt[1][w]+1)/(tot[1]+len(V))) - math.log((cnt[0][w]+1)/(tot[0]+len(V))) for w in V if df[w]>=5}
    o = sorted(s_, key=lambda w:-s_[w])
    return {"variant":name,"n_families":len(margins),"accuracy":round(acc,4),"balanced_accuracy":round(bal,4),
            "within_family_ranking_share":round(pair,4),
            "top_twin":[(w,round(s_[w],2),cnt[1][w],cnt[0][w]) for w in o[:15]],
            "top_malicious":[(w,round(s_[w],2),cnt[1][w],cnt[0][w]) for w in o[::-1][:15]]}
res = {"n_pairs":len(pairs),"n_nonquery_cue":len(nonq),"probes":{
 "baseline_full": run("full (query + non-target sentences), all families", F_full),
 "1_query_only": run("query only, all families", F_q),
 "2_sentences_only": run("non-target sentences only, all families", F_s),
 "3a_query_only_nonq": run("query only, non-query-cue families", F_q, nonq),
 "3b_sentences_only_nonq": run("sentences only, non-query-cue families", F_s, nonq),
 "baseline_full_nonq": run("full, non-query-cue families", F_full, nonq),
 "5_swap_full_nonq": run("full with twin/malicious queries swapped, non-query-cue families", F_full, nonq, swap=True)}}
def fw(q): t = normalise(q).split(); return t[0] if t else ""
tw = [fw(pairs[f][0]["query"]) for f in nonq]; ml = [fw(pairs[f][1]["query"]) for f in nonq]
top_t = [w for w,_ in Counter(tw).most_common(10)]; top_m = [w for w,_ in Counter(ml).most_common(10)]
res["first_word"] = {"top10_twin":top_t,"top10_malicious":top_m,
 "twin_in_twin_top10":round(sum(w in top_t for w in tw)/len(tw),4),"twin_in_mal_top10":round(sum(w in top_m for w in tw)/len(tw),4),
 "mal_in_mal_top10":round(sum(w in top_m for w in ml)/len(ml),4),"mal_in_twin_top10":round(sum(w in top_t for w in ml)/len(ml),4)}
byk = defaultdict(Counter); allc = Counter()
for f in nonq:
    for k,r in fams[f].items():
        if isinstance(r, dict) and "query" in r: w=fw(r["query"]); byk[k][w]+=1; allc[w]+=1
kinds = sorted(byk); top20 = [w for w,_ in allc.most_common(20)]
res["first_word_table"] = {"kinds":kinds,"rows":[[w]+[byk[k][w] for k in kinds] for w in top20],"n_by_kind":{k:sum(byk[k].values()) for k in kinds}}
(OUTD/"query_probe.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
P = res["probes"]
L = ["# Query probe","",f"Naive Bayes probe, same code and five family-grouped folds as minpair_probe.py; twin (semantic_benign) against current shared_malicious. {len(pairs)} families; {len(nonq)} without query cue.","",
     "| probe | families | accuracy | balanced | within-family share |","|---|---|---|---|---|"]
for k,v in P.items(): L.append(f"| {v['variant']} | {v['n_families']} | {v['accuracy']} | {v['balanced_accuracy']} | {v['within_family_ranking_share']} |")
q = P["3a_query_only_nonq"]
L += ["","## Query-only probe, non-query-cue families: top 15 features","","| towards twin | score | twin n | mal n | towards malicious | score | twin n | mal n |","|---|---|---|---|---|---|---|---|"]
for a,b in zip(q["top_twin"], q["top_malicious"]): L.append(f"| {a[0]} | {a[1]} | {a[2]} | {a[3]} | {b[0]} | {b[1]} | {b[2]} | {b[3]} |")
fwr = res["first_word"]
L += ["","## First words (non-query-cue families)","",f"Ten most frequent twin first words: {', '.join(fwr['top10_twin'])}.",f"Ten most frequent malicious first words: {', '.join(fwr['top10_malicious'])}.","",
 "| queries | in twin top 10 | in malicious top 10 |","|---|---|---|",
 f"| twin | {fwr['twin_in_twin_top10']} | {fwr['twin_in_mal_top10']} |", f"| malicious | {fwr['mal_in_twin_top10']} | {fwr['mal_in_mal_top10']} |","",
 "| first word | "+" | ".join(kinds)+" |","|"+"---|"*(len(kinds)+1)]
for row in res["first_word_table"]["rows"]: L.append("| "+" | ".join(map(str,row))+" |")
L.append("| (n records) | "+" | ".join(str(res["first_word_table"]["n_by_kind"][k]) for k in kinds)+" |")
(OUTD/"query_probe.md").write_text("\n".join(L)+"\n", encoding="utf-8")
for k,v in P.items(): print(k, v["n_families"], v["accuracy"], v["balanced_accuracy"], v["within_family_ranking_share"])
print("q top twin", [x[0] for x in q["top_twin"]]); print("q top mal", [x[0] for x in q["top_malicious"]])
print(json.dumps(fwr)); print(json.dumps(res["first_word_table"]))
