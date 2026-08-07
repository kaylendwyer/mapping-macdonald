import pdfplumber, re, json
PDF='/Users/k337d578/Projects/Misfits/macdonald/George MacDonald_ A Timeline of Lectures and Performance 1855-18.pdf'
pdf=pdfplumber.open(PDF)
rows=[]; started=False
for pi in range(8,73):
    p=pdf.pages[pi]
    words=[w for w in p.extract_words(extra_attrs=['fontname']) if w['top']>=60]
    words.sort(key=lambda w:(w['top'], w['x0']))
    clusters=[]
    for w in words:
        if clusters and abs(w['top']-clusters[-1][0])<=4:
            clusters[-1][1].append(w)
        else:
            clusters.append([w['top'],[w]])
    for top,ws in clusters:
        ws=sorted(ws,key=lambda x:x['x0'])
        buf=ws[0]['text']
        for a,b in zip(ws,ws[1:]):
            buf += ('' if b['x0']-a['x1'] < 1.2 else ' ') + b['text']
        text=re.sub(r'\s+',' ',buf).strip()
        bold=sum(1 for x in ws if 'Bold' in x['fontname'])/len(ws)>0.5
        if not started:
            if text.startswith('Timeline of George MacDonald Lectures'): started=True
            continue
        if text=='Endnotes': started=False; break
        rows.append((bold,text))
    if not started and rows: break
json.dump(rows,open('lines.json','w'))
print(len(rows))
for b,t in rows[:8]: print(int(b),t)
