"""One-time fix: restore the Date column to the form published in North Wind 37.

A round trip through Excel reformatted every plain date (`November 10` -> `10-Nov`) and
silently dropped the editors' brackets from 11 estimated dates (`March [21]` -> `21-Mar`),
losing the uncertainty markers. This rewrites Date from the verified PDF parse in
pdf_parse.json, keyed on entry number. No other column is touched.
"""
import csv, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV = ROOT / 'macdonald_timeline.csv'

published = {r['No.']: r['Date'] for r in json.load(open(ROOT / 'scripts/pdf_parse.json'))}

rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
assert len(rows) == 700, len(rows)

changed = []
for r in rows:
    want = published[int(r['No.'])]
    if r['Date'] != want:
        changed.append((r['No.'], r['Date'], want))
        r['Date'] = want

with open(CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f'restored {len(changed)} Date cells')
for no, old, new in changed:
    if '[' in new:
        print(f'  #{no}: {old!r} -> {new!r}')
