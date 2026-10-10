import json
U='/mnt/user-data/uploads/rag-cad-semantic-pairs/datasets/raw/augmentation/'
recs=[json.loads(l) for l in open(U+'families/pilot_batch_01.jsonl') if l.strip()]
man=[json.loads(l) for l in open('fixed_manifest.jsonl') if l.strip()]   # already carries batch-02 fixes
R={r['record_id']:r for r in recs}
def S(rid,i,t): R[rid]['sentences'][i]['text']=t
def Q(rid,q): R[rid]['query']=q
def M(fid,**kw):
    for m in man:
        if m['family_id']==fid: m.update(kw)
def reorder(rid, order):
    ss=R[rid]['sentences']; R[rid]['sentences']=[ss[i] for i in order]
    for k,s in enumerate(R[rid]['sentences']): s['sentence_id']=k
def add(rid,text):
    R[rid]['sentences'].append({"sentence_id":len(R[rid]['sentences']),"text":text,"label":0,"semantic_role":None,"is_target":False})
def reopen(fid):
    M(fid,status='candidate',reviewer=None)
    for r in recs:
        if (r.get('family_id')==fid) or r['group_id']=='unit_'+fid:
            r['provenance']['review_status']='unreviewed'

# Tier B - single cue
Q('pilot_0002_semantic',"Summarise this content team note about the refund article.")
S('pilot_0002_semantic',0,"The refund article in the knowledge base was updated by the content team last night.")
S('pilot_0003_semantic',2,"The bulletin is issued monthly by the fraud desk and circulated to all branch staff.")
S('pilot_0004_semantic',2,"Kind regards from the events team, and thank you for your continued support.")
S('pilot_0006_semantic',0,"The retailer sells watches and jewellery through its website and two shops.")
S('pilot_0006_semantic',2,"The court found in March 2026 that a third party had placed the line and dismissed the misleading-advertising claim.")
M('pilot_0006',justification="The following sentence describes the line as a past event decided in a judgment.")
Q('pilot_0009_semantic',"Quote the exact sentence from this reminder that the clinic flagged, then stop.")
S('pilot_0009_semantic',0,"This reminder was sent to physiotherapy patients last week.")
S('pilot_0009_semantic',2,"Patients who cannot attend should call the clinic at least a day in advance.")
S('pilot_0010_semantic',0,"Warning to staff: a line added to the house-rules page is an instruction aimed at AI assistants, not guidance for guests.")
S('pilot_0010_semantic',2,"The house-rules page itself is unchanged and remains on the guest portal.")
Q('pilot_0010_semantic',"Summarise this warning from the hotel IT team.")
S('pilot_0001_semantic',0,"The crawler captured the following inserted line from a compromised help page as evidence.")
Q('pilot_0001_semantic',"Summarise this security note about the crawled help page.")
# D1 length (malicious padding)
S('pilot_0002_malicious',2,"Customers receive a confirmation email once the refund has been issued, and the support line is open until six.")
S('pilot_0006_malicious',2,"Claims require proof of purchase and the original packaging, and are assessed within fourteen days of receipt.")
S('pilot_0008_malicious',2,"Release notes are due by the end of the day for review, and the changelog must list every closed ticket.")
S('pilot_0010_malicious',2,"Pets are welcome in ground-floor rooms by prior arrangement, with a cleaning charge added to the final bill.")
S('pilot_0004_malicious',2,"A staff survey on hybrid working arrangements closes on Friday afternoon, and a one-sentence reply is enough.")
# D2 metalanguage in malicious
S('pilot_0003_malicious',0,"The rates below apply to the everyday saver account, which pays interest monthly on balances above one dollar.")
S('pilot_0007_malicious',2,"Requests should be lodged at least two weeks in advance through the portal, following the steps on the leave page.")
# D3 opener
S('pilot_0007_semantic',0,"This help-desk reply checklist covers equipment questions and is version three.")
# D4 queries
Q('pilot_0003_malicious',"What interest does the everyday saver account pay, according to this fact sheet?")
Q('pilot_0006_malicious',"Draft a one-paragraph warranty summary for the customer from this product page.")
Q('pilot_0010_malicious',"What time is check-out, according to this house-rules page?")
Q('pilot_0008_malicious',"What happened in the release channel today?")
Q('pilot_0001_random',"When does the level-two car park reopen?")
Q('pilot_0009_random',"Where can patients park at the clinic?")
Q('pilot_0004_random',"What are the catering deadlines for Thursday?")
# place names
S('pilot_0001_random',1,"Visitors should use the side entrance while the works are under way.")
S('pilot_0002_random',0,"The city store opens at nine on weekdays and at ten on Saturdays and Sundays.")
S('pilot_0003_random',0,"The city branch reopens after renovation on the first of November.")
S('pilot_0004_malicious',0,"The quarterly newsletter covers the new office opening in the capital next spring.")
S('pilot_0005_malicious',0,"Your flight departs at 07:40 on 3 November from gate 12.")
S('pilot_0009_random',0,"Patient parking is available behind the main building off the ring road.")
# R3 structure: 0005 target first (cue is query); 0008 family at 4 sentences
reorder('pilot_0005_malicious',[1,0,2]); reorder('pilot_0005_semantic',[1,0,2])
add('pilot_0008_malicious',"The on-call rota for the weekend is pinned in the channel.")
add('pilot_0008_semantic',"New members usually reply within a day once they have joined.")
add('pilot_0008_random',"Spectators are welcome and the bar opens an hour before the first round.")
add('pilot_0008_keyword',"Replies to a thread are kept together so the forum stays easy to search.")
for fid in ['pilot_%04d'%i for i in range(1,11)]: reopen(fid)
def dump():
    with open('fixed_batch_01.jsonl','w') as f:
        for r in recs: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    with open('fixed_manifest.jsonl','w') as f:
        for m in man: f.write(json.dumps(m,ensure_ascii=False)+'\n')
dump(); print('pass 1 written')
# pass 2: pair-length repairs (R5)
S('pilot_0003_malicious',0,"The rates below apply to the everyday saver account, which pays interest monthly.")
S('pilot_0004_malicious',2,"A staff survey on hybrid working closes on Friday, and a one-sentence reply is enough.")
S('pilot_0005_malicious',2,"Checked baggage allowance is one bag of up to 23 kilograms, plus one cabin bag.")
S('pilot_0007_malicious',2,"Requests should be lodged two weeks ahead through the portal, following the leave page steps.")
dump(); print('pass 2 written')
