import json,re
rows=json.load(open('lines.json'))
entries=[]; notes=[]
year=None; cur=None; mode=None
ENTRY=re.compile(r'^(\d{1,3})\.\s')
YEAR=re.compile(r'^1[89]\d\d$')
for bold,text in rows:
    if bold and YEAR.match(text):
        year=text; cur=None; mode=None; continue
    if bold and text.startswith('NB'):
        notes.append({'year':year,'note':text}); mode='nb'; continue
    m=ENTRY.match(text) if bold else None
    if m:
        cur={'num':int(m.group(1)),'year':year,'head':[text],'det':[]}
        entries.append(cur); mode='head'; continue
    if cur is None:
        if mode=='nb' and bold: notes[-1]['note']+=' '+text
        continue
    if bold:
        if mode=='nb': notes[-1]['note']+=' '+text
        elif mode=='head' and not text.startswith('('): cur['head'].append(text)
        else: cur['det'].append(text); mode='det'
    else:
        cur['det'].append(text); mode='det'
json.dump({'entries':entries,'notes':notes},open('grouped.json','w'))
print('entries',len(entries),'notes',len(notes))
nums=[e['num'] for e in entries]
print('first',nums[:3],'last',nums[-3:])
# check sequence
exp=1; bad=[]
for n in nums:
    if n!=exp: bad.append((exp,n))
    exp=n+1
print('seq issues',bad[:20])
