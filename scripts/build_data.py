"""Join the timeline, the parsed dates, the collapsed categories and the gazetteer.

Rewrites the derived columns of macdonald_timeline.csv in place (idempotent — the seven
curated columns are never touched) and emits scripts/site_data.json for the visualization.
"""
import collections, csv, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import dates as dates_mod
import subjects as subjects_mod
from categories import classify

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV = ROOT / 'macdonald_timeline.csv'
PLACES = ROOT / 'macdonald_places.csv'
OUT_JSON = ROOT / 'scripts/site_data.json'

SOURCE_COLUMNS = ['No.', 'Year', 'Date', 'Type', 'Title', 'Location', 'Details']
DERIVED_COLUMNS = ['date_start', 'date_end', 'date_likely', 'date_precision', 'date_certain',
                   'date_note', 'categories', 'type_inferred', 'cancelled',
                   'subject_groups', 'subjects', 'lat', 'lon', 'geo_precision']


def main():
    rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
    assert len(rows) == 700, 'expected 700 entries, got %d' % len(rows)
    places = {r['location']: r for r in csv.DictReader(open(PLACES, encoding='utf-8'))}
    taxonomy = subjects_mod.load()

    unmapped_titles = sorted({r['Title'] for r in rows if r['Title'] not in taxonomy})
    if unmapped_titles:
        raise SystemExit('macdonald_subjects.csv has no row for: '
                         + ', '.join(repr(t) for t in unmapped_titles))

    out, events, warnings = [], [], []
    for r in rows:
        rec = {k: r[k] for k in SOURCE_COLUMNS}
        d = dates_mod.parse(r['Date'], r['Year'])
        c = classify(r['Type'], r['Details'])
        p = places[r['Location']]
        subs = taxonomy[r['Title']]

        if d['start'][:4] != r['Year']:
            warnings.append('#%s date %r starts in %s but sits under the %s heading'
                            % (r['No.'], r['Date'], d['start'][:4], r['Year']))

        rec.update({
            'date_start': d['start'], 'date_end': d['end'], 'date_likely': d['likely'],
            'date_precision': d['precision'], 'date_certain': str(d['certain']).upper(),
            'date_note': d['note'],
            'categories': '|'.join(c['categories']),
            'type_inferred': str(c['type_inferred']).upper(),
            'cancelled': str(c['cancelled']).upper(),
            'subject_groups': '|'.join(g for g, _ in subs),
            'subjects': '|'.join(w for _, w in subs),
            'lat': p['lat'], 'lon': p['lon'], 'geo_precision': p['geo_precision'],
        })
        out.append(rec)

        events.append({
            'n': int(r['No.']), 'd': d['start'], 'e': d['end'],
            'p': d['precision'], 'c': d['certain'],
            'cat': c['categories'], 'inf': c['type_inferred'], 'x': c['cancelled'],
            'sub': [list(s) for s in subs],
            'ti': r['Title'], 'lo': r['Location'], 'de': r['Details'], 'raw': r['Date'],
            'lat': float(p['lat']) if p['lat'] else None,
            'lon': float(p['lon']) if p['lon'] else None,
            'gp': p['geo_precision'],
        })

    with open(CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=SOURCE_COLUMNS + DERIVED_COLUMNS)
        w.writeheader()
        w.writerows(out)

    place_list = [{
        'lo': p['location'], 'lat': float(p['lat']), 'lon': float(p['lon']),
        'gp': p['geo_precision'], 'nm': p['display_name'].split(',')[0], 'note': p['note'],
    } for p in places.values() if p['lat']]

    OUT_JSON.write_text(json.dumps({
        'events': events, 'places': place_list,
        'basemap': json.loads((ROOT / 'basemap.geojson').read_text()),
    }, separators=(',', ':')))

    # --- report -------------------------------------------------------------
    print('%d entries -> %d rows' % (len(rows), len(out)))
    print('categories: ', dict(collections.Counter(c for r in out for c in r['categories'].split('|'))))
    print('precision:  ', dict(collections.Counter(r['date_precision'] for r in out)))
    print('estimated dates: %d of %d'
          % (sum(1 for r in out if r['date_certain'] == 'FALSE'), len(out)))
    print('inferred type:   %d   cancelled: %d'
          % (sum(1 for r in out if r['type_inferred'] == 'TRUE'),
             sum(1 for r in out if r['cancelled'] == 'TRUE')))
    unmapped = [r['No.'] for r in out if not r['lat']]
    print('unmapped entries (%d): %s' % (len(unmapped), ', '.join('#' + n for n in unmapped)))
    print('mapped places: %d' % len(place_list))

    # subjects: an entry counts once per group it touches, never twice within one group
    per_group = collections.defaultdict(set)
    per_work = collections.Counter()
    for r, ev in zip(out, events):
        for g, w in ev['sub']:
            per_group[g].add(r['No.'])
            per_work[(g, w)] += 1
    covered = {n for ns in per_group.values() for n in ns}
    assert covered == {r['No.'] for r in out}, 'every entry must carry at least one subject'
    print('subjects: %d groups, %d works, %d entries covered'
          % (len(per_group), len(per_work), len(covered)))
    for g, ns in sorted(per_group.items(), key=lambda kv: -len(kv[1]))[:6]:
        works = sorted(((w, n) for (g2, w), n in per_work.items() if g2 == g),
                       key=lambda kv: -kv[1])[:4]
        print('  %-22s %4d   %s' % (g, len(ns), ', '.join('%s %d' % x for x in works)))
    for w_ in warnings:
        print('NOTE:', w_)
    print('site_data.json: %.0f KB' % (OUT_JSON.stat().st_size / 1024))


if __name__ == '__main__':
    main()
