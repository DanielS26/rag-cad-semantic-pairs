"""Shortcut probe from audit.py section 3 (copied: audit.py runs its whole audit at import and needs argv).
Twin vs malicious, target out, punctuation features off; NB Laplace 1; uni+bigrams; 5 folds grouped by family (seed 764)."""
import json, re, sys, math, random
from collections import Counter
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
bykind = {k:[r for r in recs if r["condition_source"]==k] for k in ["shared_malicious","semantic_benign"]}
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
data = [(feats(r), 1 if r["condition_source"]=="semantic_benign" else 0, r["family_id"]) for r in bykind["semantic_benign"]+bykind["shared_malicious"]]
correct=0; tp=Counter(); per=[]; margins={}
for f in range(5):
    tr=[d for d in data if fold[d[2]]!=f]; te=[d for d in data if fold[d[2]]==f]
    m = nb_train([d[0] for d in tr],[d[1] for d in tr]); c=0
    for x,l,fid in te:
        mg = nb_logp(m,x,1)-nb_logp(m,x,0); margins.setdefault(fid,{})[l]=mg
        p = 1 if mg>0 else 0; c += p==l; tp[(l,p==l)]+=1
    per.append(round(c/len(te),3)); correct+=c
acc = correct/len(data); bal = (tp[(1,True)]/(tp[(1,True)]+tp[(1,False)]) + tp[(0,True)]/(tp[(0,True)]+tp[(0,False)]))/2
def sig(z): return 1/(1+math.exp(-z)) if z>-700 else 0.0
fam = {fid:{"batch": int(fid[-4:]) and (int(fid[-4:])-1)//10+1, "p_mal_is_twin": sig(v[0]), "p_twin_is_twin": sig(v[1]), "margin_mal": round(v[0],3), "margin_twin": round(v[1],3), "twin_above_mal": v[1]>v[0]} for fid,v in sorted(margins.items())}
pair = sum(v["twin_above_mal"] for v in fam.values())/len(fam)
cnt,prior,V,tot = nb_train([d[0] for d in data],[d[1] for d in data]); df=Counter()
for d in data: df.update(set(d[0]))
s_ = {w: math.log((cnt[1][w]+1)/(tot[1]+len(V))) - math.log((cnt[0][w]+1)/(tot[0]+len(V))) for w in V if df[w]>=5}
o = sorted(s_, key=lambda w:-s_[w])
res = {"setting":"twin (semantic_benign) vs malicious (shared_malicious), target out, punctuation features off, min df 5 for features",
       "accuracy":round(acc,4),"balanced_accuracy":round(bal,4),"within_family_ranking_share":round(pair,4),"fold_acc":per,
       "top_twin":[(w,round(s_[w],2),cnt[1][w],cnt[0][w]) for w in o[:20]],"top_mal":[(w,round(s_[w],2),cnt[1][w],cnt[0][w]) for w in o[::-1][:20]],
       "families":fam}
OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
print(res["accuracy"], res["balanced_accuracy"], res["within_family_ranking_share"], per)
