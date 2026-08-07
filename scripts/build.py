import json, re, csv

d=json.load(open('grouped.json'))

REGION = {'SCT','IRL','ITL','NY','MA','PA','NJ','OH','MI','IL','DE','DC','VT','RI','CT','MD','IA','WI','IN','NH','ME','VA','KY','MO','CA','MN','KS','NE',
          'Ontario','Quebec','France','Wales','Canada','Italy','Scotland','Ireland','England'}
LONDON_DISTRICTS = {'Islington','Hampstead','Croydon','Bloomsbury','Hammersmith','Poplar','Lewisham','Camden','Clapham','Surbiton','Cheshunt','Norwood',
    'Highgate','Anerley','Wood Green','Enfield','Hendon','Blackheath','Streatham Hill','Whitechapel','Holborn','Bow','Westminster','Woolwich','Peckham',
    'Southwark','Belgravia','Brixton','New Barnet','Charlton','Canonbury','Wimbledon','Stoke Newington','Chiswick','Kensington','Greenwich','Dulwich',
    'Sydenham','Forest Hill','Tottenham','Ealing','Barnet','Finchley','Hackney','Shoreditch','Battersea','Fulham','Putney','Balham','Lambeth','Bermondsey',
    'Deptford','Stratford','Walthamstow','Leyton','Ilford','Bexley','Eltham','Catford','Clerkenwell','Marylebone','Paddington','Pimlico','Chelsea','Mayfair'}

# single-part bodies that are a place, not a title
LOC_ONLY = {355}

def core(s):
    return s.strip().strip('[]').strip(' .,;:”“"’').strip()

def join_lines(lines):
    out=''
    for i,l in enumerate(lines):
        if i==0: out=l
        elif out.endswith('-'): out+=l
        else: out+=' '+l
    return re.sub(r'\s+',' ',out).strip()

TYPE_RE = re.compile(r'^(\[?)(Lectures?|Performances?|Dramatic Reading|Reading|Lecture/Sermon|Lecture-sermon|Sermon|Speaker)(\]?)\s*[:,]\s*(.*)$')

rows=[]
for e in d['entries']:
    head = re.sub(r'^\d+\.\s*','', join_lines(e['head']))
    m = re.match(r'^(.*?)\s*–\s*(.*)$', head)
    date, rest = (m.group(1).strip(), m.group(2).strip()) if m else (head, '')

    # an opening bracket in the date whose close falls at the end of the entry
    if date.count('[')>date.count(']') and rest.endswith(']'):
        rest=rest[:-1].strip(); date=date+']'

    # whole-entry bracket, e.g. "[Lecture: unknown, Northampton, MA]"
    trailing_bracket = rest.startswith('[') and rest.endswith(']') and rest.count('[')==1
    if trailing_bracket:
        rest = rest[1:-1]
        if not date.startswith('['): date = '[' + date + ']'

    tm = TYPE_RE.match(rest)
    if tm:
        typ = ('[%s]' % tm.group(2)) if tm.group(1) else tm.group(2)
        body = tm.group(4)
    else:
        typ, body = '', rest
    body = body.strip().rstrip(',').strip()

    parts=[p.strip() for p in body.split(',')]
    # source uses ';' instead of ',' before the location in a couple of entries
    if ';' in parts[-1]:
        a,b = parts[-1].rsplit(';',1)
        parts = parts[:-1] + [a.strip()+';', b.strip()]

    if len(parts)==1:
        if e['num'] in LOC_ONLY: title, loc = '', parts[0]
        else: title, loc = parts[0], ''
    else:
        loc_parts=[parts[-1]]; idx=len(parts)-1
        floor = 0 if typ=='' else 1     # no type marker => there may be no title at all
        while idx-1 >= floor:
            prev=parts[idx-1]; h=core(loc_parts[0])
            if h in REGION or (h.rstrip('.')=='London' and core(prev) in LONDON_DISTRICTS):
                loc_parts.insert(0, prev); idx-=1
            else:
                break
        title=', '.join(parts[:idx]).strip()
        loc=', '.join(loc_parts).strip()

    # a stray closing quote at the head of the location belongs to the title
    mq=re.match(r'^([”“"]+)', loc)
    if mq: title += mq.group(1)
    loc=re.sub(r'^[”“"\s,]+','',loc).strip()
    title=title.strip().strip(',;').strip()

    # source omits the comma between a London district and "London"
    if core(loc).rstrip('.')=='London':
        mm=re.search(r'\s([A-Z][a-z]+)$', title)
        if mm and mm.group(1) in LONDON_DISTRICTS:
            title=title[:mm.start()].strip(); loc=mm.group(1)+', '+loc

    # "St. Leonards, Hastings" is a single place
    if core(loc)=='Hastings' and title.endswith('St. Leonards'):
        title=title[:-len('St. Leonards')].strip().strip(','); loc='St. Leonards, '+loc

    rows.append({'No.':e['num'],'Year':e['year'],'Date':date,'Type':typ,
                 'Title':title,'Location':loc,'Details':join_lines(e['det'])})

with open('macdonald_timeline.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['No.','Year','Date','Type','Title','Location','Details'])
    w.writeheader(); [w.writerow(r) for r in rows]

with open('macdonald_timeline_notes.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['Year','Note'])
    w.writeheader(); [w.writerow({'Year':n['year'],'Note':join_lines([n['note']])}) for n in d['notes']]

json.dump(rows, open('rows.json','w'), ensure_ascii=False, indent=1)
import collections
print(len(rows), collections.Counter(r['Type'] for r in rows).most_common())
print('empty loc:', [r['No.'] for r in rows if not r['Location']])
print('empty title:', [r['No.'] for r in rows if not r['Title']])
