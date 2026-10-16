"""Minimal-pair probe: same NB code path and folds as pilot40_probe.py; twin vs baseline malicious, vs variant A (cue removed), vs variant C (cue swapped)."""
import json, sys, math, random, copy
from collections import Counter, defaultdict
from pathlib import Path
from rag_cad.data import selfcheck as sc
from rag_cad.data.similarity import normalise
R = Path(sys.argv[1]); OUT = Path(sys.argv[2])
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
def feats(r):
    parts = [r["query"]] + [s["text"] for s in r["sentences"] if not s["is_target"]]
    out=[]
    for t in parts:
        tk = normalise(t).split(); out += tk + [a+"_"+b for a,b in zip(tk,tk[1:])]
    return out
def nb_train(X, y):
    cnt = {0:Counter(),1:Counter()}; prior=Counter(y)
    for x,l in zip(X,y): cnt[l].update(x)
    V = set(cnt[0])|set(cnt[1]); tot={l:sum(cnt[l].values()) for l in (0,1)}
    return cnt, prior, V, tot
def nb_logp(model, x, l):
    cnt, prior, V, tot = model
    return math.log(prior[l]/sum(prior.values())) + sum(math.log((cnt[l][w]+1)/(tot[l]+len(V))) for w in x if w in V)
pairs = {}  # fid -> (twin, mal)
for fid, m in fams.items():
    t, mal = m.get("semantic_benign"), m.get("shared_malicious")
    if t and mal: pairs[fid] = (t, mal)
def variant(t, mal, e, kind):
    v = copy.deepcopy(t); pos = e.get("cue_position")
    if pos == "query":
        v["query"] = mal["query"]; return v
    ids = sc._cue_sentence_ids(e, t)
    if kind == "A":
        v["sentences"] = [s for s in v["sentences"] if s["sentence_id"] not in ids or s["is_target"]]
    else:
        mby = {s["sentence_id"]: s for s in mal["sentences"]}
        last = [s for s in mal["sentences"] if not s["is_target"]][-1]
        for s in v["sentences"]:
            if s["sentence_id"] in ids and not s["is_target"]:
                s["text"] = (mby.get(s["sentence_id"]) or last)["text"]
    return v
def run(name, other):
    data = []
    for fid,(t,mal) in pairs.items():
        data.append((feats(t),1,fid)); data.append((feats(other(fid,t,mal)),0,fid))
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
    br = {}
    for key in ("cue_position","semantic_role"):
        g = defaultdict(lambda:[0,0,0])
        for fid,v in margins.items():
            k = man.get(fid,{}).get(key,"?")
            g[k][0] += (v[1]>0) + (v[0]<=0); g[k][1] += 2; g[k][2] += v[1]>v[0]
        br[key] = {k:{"n_families":c[1]//2,"accuracy":round(c[0]/c[1],4),"within_family_share":round(c[2]/(c[1]//2),4)} for k,c in sorted(g.items())}
    return {"variant":name,"n_families":len(pairs),"accuracy":round(acc,4),"balanced_accuracy":round(bal,4),
            "within_family_ranking_share":round(pair,4),
            "top_twin":[(w,round(s_[w],2),cnt[1][w],cnt[0][w]) for w in o[:15]],
            "top_other":[(w,round(s_[w],2),cnt[1][w],cnt[0][w]) for w in o[::-1][:15]],"breakdown":br}
res = {"baseline": run("baseline: twin vs current shared_malicious", lambda fid,t,mal: mal),
       "A": run("A: twin with cue removed", lambda fid,t,mal: variant(t,mal,man[fid],"A")),
       "C": run("C: twin with cue swapped for malicious sentence", lambda fid,t,mal: variant(t,mal,man[fid],"C"))}
shares = []; byp = defaultdict(list)
for fid,(t,mal) in pairs.items():
    e = man[fid]; tot = len(normalise(t["query"]).split()) + sum(len(normalise(s["text"]).split()) for s in t["sentences"] if not s["is_target"])
    if e["cue_position"] == "query": rem = len(normalise(t["query"]).split())
    else:
        ids = sc._cue_sentence_ids(e, t); rem = sum(len(normalise(s["text"]).split()) for s in t["sentences"] if s["sentence_id"] in ids and not s["is_target"])
    shares.append(rem/tot); byp[e["cue_position"]].append(rem/tot)
res["A"]["cue_token_share"] = {"mean_all": round(sum(shares)/len(shares),4), "by_cue_position": {k:round(sum(v)/len(v),4) for k,v in sorted(byp.items())}}
OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
for k,v in res.items(): print(k, v["accuracy"], v["balanced_accuracy"], v["within_family_ranking_share"])
print(res["A"]["cue_token_share"])
for k,v in res.items(): print(k, json.dumps(v["breakdown"]))
print("A top_twin", [x[0] for x in res["A"]["top_twin"]]); print("A top_other", [x[0] for x in res["A"]["top_other"]])
