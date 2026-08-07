"""One-time fix: nine entries where a sub-place ended up in the Title column.

The article writes a heading as `Type: Title, Location`, but a few locations are themselves
comma-separated (`Julius Caesar, Shanklin, Isle of Wight`), and the extractor kept only the final
segment as the location, leaving the rest attached to the title. Moving the place across sharpens
four of the vaguest map points — Cupar rather than the Fife centroid, Shanklin rather than the
Isle of Wight centroid — and independently confirms that #428's "Briston" is Bristol, since its
venue is Clifton College.
"""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV = ROOT / 'macdonald_timeline.csv'

# entry no. -> (expected current Title, new Title, new Location)
FIXES = {
    184: ('unknown, Fitchburg',                'unknown',              'Fitchburg, MA'),
    185: ('unknown, Charlestown',              'unknown',              'Charlestown, Boston, MA'),
    186: ('unknown, Westboro',                 'unknown',              'Westboro, MA'),
    404: ('Pilgrim’s Progress 2, Bedford Park', 'Pilgrim’s Progress 2', 'Bedford Park, Chiswick'),
    428: ('Pilgrim’s Progress 2, Clifton',      'Pilgrim’s Progress 2', 'Clifton, Bristol'),
    503: ('Julius Caesar, Shanklin',            'Julius Caesar',        'Shanklin, Isle of Wight'),
    583: ('Pilgrim’s Progress 2, Cupar',        'Pilgrim’s Progress 2', 'Cupar, Fife, SCT'),
    584: ('Pilgrim’s Progress 1, Cupar',        'Pilgrim’s Progress 1', 'Cupar, Fife, SCT'),
    650: ('Macbeth, Sale',                      'Macbeth',              'Sale'),
}


def main():
    rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
    assert len(rows) == 700, len(rows)
    done = 0
    for r in rows:
        fix = FIXES.get(int(r['No.']))
        if not fix:
            continue
        expect, title, loc = fix
        if r['Title'] != expect:
            print('#%s already fixed or changed (Title is %r) — skipping' % (r['No.'], r['Title']))
            continue
        print('#%-4s %-38r -> %r  |  %r -> %r'
              % (r['No.'], r['Title'], title, r['Location'], loc))
        r['Title'], r['Location'] = title, loc
        done += 1

    with open(CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print('fixed %d of %d' % (done, len(FIXES)))


if __name__ == '__main__':
    main()
