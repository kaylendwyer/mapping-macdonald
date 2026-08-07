"""Clip and simplify Natural Earth 50m countries into an inlineable basemap.

The events fall in three clusters — Britain & Ireland, the NE United States and Canada, and the
Ligurian/Riviera coast — so the map only ever needs the North Atlantic. Everything outside that
window is dropped, the rest is simplified and rounded to 3 decimal places (~110 m), which is far
finer than a town-level dot needs and keeps the file small enough to inline.
"""
import json, pathlib

from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'scripts/ne_50m_countries.geojson'
OUT = ROOT / 'basemap.geojson'

WINDOW = box(-98, 22, 22, 64)          # North Atlantic: lon -98..22, lat 22..64
TOLERANCE = 0.02                        # degrees; ~2 km, invisible at these zooms


def round_coords(obj, nd=3):
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(float(c), nd) for c in obj]
        return [round_coords(o, nd) for o in obj]
    return obj


NE_URL = ('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/'
          'geojson/ne_50m_admin_0_countries.geojson')


def main():
    if not SRC.exists():
        import urllib.request
        print('downloading Natural Earth 50m countries…')
        urllib.request.urlretrieve(NE_URL, SRC)
    src = json.loads(SRC.read_text())
    features = []
    for feat in src['features']:
        geom = shape(feat['geometry'])
        if not geom.intersects(WINDOW):
            continue
        clipped = geom.intersection(WINDOW).simplify(TOLERANCE, preserve_topology=True)
        if clipped.is_empty or clipped.area < 0.01:
            continue
        props = feat['properties']
        features.append({
            'type': 'Feature',
            'properties': {'name': props.get('NAME') or props.get('name')},
            'geometry': _round_geom(mapping(clipped)),
        })

    out = {'type': 'FeatureCollection', 'features': features}
    OUT.write_text(json.dumps(out, separators=(',', ':')))
    kb = OUT.stat().st_size / 1024
    print('%d features, %.0f KB' % (len(features), kb))


def _round_geom(g):
    g['coordinates'] = round_coords(g['coordinates'])
    return g


if __name__ == '__main__':
    main()
