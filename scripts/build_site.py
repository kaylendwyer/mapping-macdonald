"""Inline the data into the page template to produce macdonald_timeline.html.

The page makes no external requests — data, basemap and all — so it works offline, straight
from the repo, and unchanged as a published artifact.
"""
import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HERE = ROOT / 'scripts'
OUT = ROOT / 'macdonald_timeline.html'

subprocess.run([sys.executable, str(HERE / 'build_data.py')], check=True)

template = (HERE / 'template.html').read_text()
data = (HERE / 'site_data.json').read_text()
for token in ('__DATA__', '__LEAFLET_JS__', '__LEAFLET_CSS__'):
    assert token in template, token
# the JSON sits in a <script type="application/json">, so only `</` needs escaping
body = (template
        .replace('__LEAFLET_CSS__', (HERE / 'leaflet.css').read_text())
        .replace('__LEAFLET_JS__', (HERE / 'leaflet.js').read_text())
        .replace('__DATA__', data.replace('</', '<\\/')))

# The template is written bare because the artifact host supplies its own document
# skeleton; the local file needs a real one, or the browser lands in quirks mode.
DOC = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
       '%s\n</head>\n<body>\n%s\n</body>\n</html>\n')
head, _, rest = body.partition('\n')          # the <title> line
OUT.write_text(DOC % (head, rest))
(HERE / 'artifact.html').write_text(body)     # bare variant, for publishing
print('wrote %s (%.0f KB)' % (OUT.name, OUT.stat().st_size / 1024))
