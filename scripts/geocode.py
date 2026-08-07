"""Build macdonald_places.csv, the gazetteer joining location strings to coordinates.

Queries go to Nominatim at 1 req/sec and are cached to scripts/geocode_cache.json, so a rebuild
costs nothing. QUERIES overrides the query for anything a literal lookup gets wrong — source
misspellings, bare district names, historic forms. Where the reading is a judgement call the
gazetteer carries a `note` saying so.

macdonald_places.csv is the source of truth on rebuild: edit lat/lon there and the edit sticks.
"""
import csv, json, pathlib, sys, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / 'scripts/geocode_cache.json'
PLACES = ROOT / 'macdonald_places.csv'
UA = 'macdonald-timeline-research/1.0 (kaylendwyer@gmail.com)'

# Location string -> (Nominatim query, note). Everything else is resolved by SUFFIXES below.
QUERIES = {
    # source misspellings and shorthand, resolved from each entry's own citations
    'Briston': ('Bristol, England, UK', 'source reads "Briston"; entry #428 names Clifton College, which is in Bristol'),
    'Harbourne': ('Harborne, Birmingham, England, UK', 'source spelling of Harborne'),
    'Farmingham': ('Farningham, Kent, England, UK', 'probable source spelling of Farningham'),
    'Ben Rhydding': ('Ben Rhydding, Ilkley, England, UK', 'sources also have "Ben Rydding"'),
    'MA [source has “Fitchbury”]': ('Fitchburg, Massachusetts, USA', 'source reads "Fitchbury"; no such place — Fitchburg assumed'),
    'Plainfield [Scotch Plains], NJ': ('Plainfield, New Jersey, USA', 'source gives Scotch Plains as an alternative'),
    'East Saginaw, MI.': ('Saginaw, Michigan, USA', 'East Saginaw merged into Saginaw in 1889'),
    'Flint, MI.': ('Flint, Michigan, USA', ''),
    'Bishop Auckland, SCT': ('Bishop Auckland, County Durham, England, UK',
                             'the article marks this SCT, but Bishop Auckland is in County Durham, England'),
    'Newton': ('Newton-le-Willows, England, UK', 'entry #108 names Crow Lane and cites the Wigan Observer'),
    'Shields': ('South Shields, England, UK', 'ambiguous: the article lists North Shields separately, but #656 cites the Shields Daily Gazette of South Shields'),
    'Brampton': ('Brampton, Cumberland, United Kingdom', 'follows Carlisle by one day on the 1885 tour'),
    'Barrow': ('Barrow-in-Furness, England, UK', ''),
    'Sale': ('Sale, Greater Manchester, England, UK', ''),
    'Southam': ('Southam, Warwickshire, England, UK', 'entries name Ladbroke Hall, near Southam'),
    'Mealsgate': ('Mealsgate, United Kingdom', ''),
    'Clifton': ('Clifton, Bristol, England, UK', 'entry #467 names the Victoria Rooms and cites the Western Daily Press'),
    'Clifton, Bristol': ('Clifton, Bristol, England, UK',
                         'the article gives "Briston"; #428 was performed at Clifton College, in Bristol'),
    'Westboro, MA': ('Westborough, Massachusetts, USA', 'source spelling of Westborough'),
    'Charlestown, Boston, MA': ('Charlestown, Boston, Massachusetts, USA', ''),
    'Bedford Park, Chiswick': ('Bedford Park, London, United Kingdom',
                              'the garden suburb in Chiswick; OSM holds it as a residential area, not a settlement'),
    'Shanklin, Isle of Wight': ('Shanklin, Isle of Wight, England, UK', ''),
    'Cupar, Fife, SCT': ('Cupar, Fife, Scotland, UK',
                         'the article gives only "Fife"; #583 cites the Fife Herald, published at Cupar'),
    'Hanley': ('Hanley, Stoke-on-Trent, England, UK', ''),
    'Christchurch': ('Christchurch, Dorset, England, UK', ''),
    'Newcastle': ('Newcastle upon Tyne, England, UK', ''),
    'Stockton': ('Stockton-on-Tees, England, UK', ''),
    'Reading': ('Reading, Berkshire, England, UK', ''),
    'Cambridge': ('Cambridge, England, UK', ''),
    'Lancaster': ('Lancaster, England, UK', ''),
    'Boston, MA': ('Boston, Massachusetts, USA', ''),
    'Bedford': ('Bedford, England, UK', ''),
    'Bath': ('Bath, England, UK', ''),
    'Chester': ('Chester, England, UK', ''),
    'Derby': ('Derby, England, UK', ''),
    'Hull': ('Kingston upon Hull, England, UK', ''),
    'York': ('York, England, UK', ''),
    'Norwich': ('Norwich, England, UK', ''),
    'Exeter': ('Exeter, England, UK', ''),
    'Taunton': ('Taunton, England, UK', ''),
    'Winchester': ('Winchester, England, UK', ''),
    'Southampton': ('Southampton, England, UK', ''),
    'Guildford': ('Guildford, England, UK', ''),
    'Maidstone': ('Maidstone, England, UK', ''),
    'Woodford': ('Woodford, London, England, UK', ''),
    'Bedwell Park': ('Essendon, Hertfordshire, England, UK', 'Bedwell Park is the estate at Essendon'),
    'Weybridge Heath': ('Weybridge, Surrey, England, UK', ''),
    'St. Leonards': ('St Leonards, Hastings, United Kingdom', ''),
    'St. Leonards, Hastings': ('St Leonards, Hastings, United Kingdom', ''),
    'Menai, Wales': ('Menai Bridge, Anglesey, Wales, UK', ''),
    'Wigston Magna': ('Wigston, Leicestershire, England, UK', ''),
    'Southborough': ('Southborough, Kent, England, UK', ''),
    'Weston-Super-Mare': ('Weston-super-Mare, England, UK', ''),
    'Tunbridge Wells': ('Royal Tunbridge Wells, England, UK', ''),
    'Edinburgh': ('Edinburgh, Scotland, UK', 'the article lists both "Edinburgh" and "Edinburgh, SCT"'),
    'Wrexham': ('Wrexham, Wales, UK', ''),
    'Cheshunt, London': ('Cheshunt, Hertfordshire, England, UK',
                         'the article gives London; Cheshunt is in Hertfordshire'),

    # continental Europe
    'Mentone, ITL': ('Menton, France', 'the article marks this ITL; "Mentone" is the historic name of Menton, on the French side of the Riviera'),
    'Genova, ITL': ('Genoa, Italy', ''),
    'Nervi, ITL': ('Nervi, Genoa, Italy', ''),
    'San Remo, ITL': ('Sanremo, Italy', ''),

    # bracketed = the editors inferred the place
    '[London]': ('London, England, UK', 'place inferred by the editors'),
    '[Bordighera, ITL]': ('Bordighera, Italy', 'place inferred by the editors'),
    '[Camden], London': ('Camden, London, England, UK', 'place inferred by the editors'),
    'London.': ('London, England, UK', ''),

    # regions rather than points; plotted at the region centroid
    'Fife, SCT': ('Fife, Scotland, UK', 'region, not a town; #583 cites the Fife Herald of Cupar'),
    'Upper Perthshire, SCT': ('Perth and Kinross, Scotland, UK', 'region, not a town'),
    'Isle of Wight': ('Isle of Wight, England, UK', 'region, not a town'),
    'Derbyshire': ('Derbyshire, England, UK', 'region, not a town'),

    # unmappable
    'unknown': (None, 'location not recorded'),
    'S. S. Malta': (None, 'a reading given aboard ship in passage; no fixed point'),
}

REGIONS = {'Fife, SCT', 'Upper Perthshire, SCT', 'Isle of Wight', 'Derbyshire'}
INFERRED = {'[London]', '[Bordighera, ITL]', '[Camden], London'}

SUFFIXES = [
    (', SCT', ', Scotland, UK'), (', IRL', ', Ireland'), (', ITL', ', Italy'),
    (', Wales', ', Wales, UK'), (', London', ', London, England, UK'),
    (', Ontario', ', Ontario, Canada'), (', Quebec', ', Quebec, Canada'),
    (', France', ', France'),
]
US_STATES = {
    'NY': 'New York', 'MA': 'Massachusetts', 'PA': 'Pennsylvania', 'NJ': 'New Jersey',
    'OH': 'Ohio', 'MI': 'Michigan', 'IL': 'Illinois', 'DE': 'Delaware', 'DC': 'District of Columbia',
    'VT': 'Vermont', 'RI': 'Rhode Island', 'CT': 'Connecticut', 'MD': 'Maryland',
    'IA': 'Iowa', 'WI': 'Wisconsin',
}


def to_query(loc):
    if loc in QUERIES:
        return QUERIES[loc]
    for suffix, repl in SUFFIXES:
        if loc.endswith(suffix):
            return loc[: -len(suffix)] + repl, ''
    head, _, tail = loc.rpartition(', ')
    if tail in US_STATES:
        return '%s, %s, USA' % (head, US_STATES[tail]), ''
    return loc + ', England, UK', ''


def country_of(loc):
    """Expected country, for the sanity check in build_data.py."""
    q = to_query(loc)[0]
    if q is None:
        return ''
    for name in ('USA', 'Canada', 'Italy', 'France', 'Ireland'):
        if q.endswith(name):
            return name
    return 'UK'


def _search(query, limit):
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(
        {'q': query, 'format': 'json', 'limit': limit})
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as fh:
        data = json.load(fh)
    time.sleep(1.1)
    return data


def nominatim(query, cache):
    """Top hit, preferring a settlement.

    Free-text search happily returns a commercial building in Reading or an allotment in
    Walsall for `Wrexham`, so when the best match isn't a populated place or an administrative
    boundary, look further down the result list for one that is.
    """
    if query in cache:
        return cache[query]
    data = _search(query, 1)
    if data and data[0]['class'] not in ('place', 'boundary'):
        better = [d for d in _search(query, 10) if d['class'] in ('place', 'boundary')]
        if better:
            data = better
    cache[query] = data[0] if data else None
    CACHE.write_text(json.dumps(cache, indent=1))
    return cache[query]


def main():
    rows = list(csv.DictReader(open(ROOT / 'macdonald_timeline.csv', encoding='utf-8')))
    counts = {}
    for r in rows:
        counts[r['Location']] = counts.get(r['Location'], 0) + 1

    existing = {}
    if PLACES.exists():
        existing = {r['location']: r for r in csv.DictReader(open(PLACES, encoding='utf-8'))}

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    out = []
    for loc in sorted(counts):
        prev = existing.get(loc)
        if prev and prev.get('lat') and prev.get('manual') == 'TRUE':
            out.append(prev)                      # never overwrite a hand-corrected row
            continue
        query, note = to_query(loc)
        lat = lon = display = ''
        if query is None:
            precision = 'unmappable'
        else:
            hit = nominatim(query, cache)
            if not hit:
                print('NO RESULT: %r -> %r' % (loc, query), file=sys.stderr)
                precision = 'unresolved'
            else:
                lat, lon, display = hit['lat'], hit['lon'], hit['display_name']
                precision = ('region' if loc in REGIONS else
                             'inferred' if loc in INFERRED else 'town')
        out.append({
            'location': loc, 'events': counts[loc], 'query': query or '',
            'lat': lat, 'lon': lon, 'geo_precision': precision,
            'country': country_of(loc), 'display_name': display,
            'note': note, 'manual': 'FALSE',
        })

    with open(PLACES, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['location', 'events', 'query', 'lat', 'lon',
                                          'geo_precision', 'country', 'display_name',
                                          'note', 'manual'])
        w.writeheader()
        w.writerows(out)
    print('wrote %d places (%d events)' % (len(out), sum(counts.values())))


if __name__ == '__main__':
    main()
