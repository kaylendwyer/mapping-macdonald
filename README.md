# George MacDonald: lectures and performances, 1854–1891

A machine-readable dataset and an interactive timeline + map built from Joe Ricke, Ashley Chu,
Kendra Smalley, Kaylen Dwyer and Caleb Hoelscher, "George MacDonald: A Timeline of Lectures and
Performances, 1855–1891," *North Wind: A Journal of George MacDonald Studies* 37 (2018): 107–179.

## Files

| File | What it is |
|---|---|
| `macdonald_timeline.html` | The visualization. Self-contained — open it straight from disk. |
| `macdonald_timeline.csv` | 700 entries. Columns 1–7 are transcribed and curated; the rest are derived. |
| `macdonald_places.csv` | Gazetteer: one row per distinct location string, with coordinates. **Hand-editable.** |
| `macdonald_subjects.csv` | Subject taxonomy: title → author/corpus → work. **Hand-editable.** |
| `macdonald_timeline_notes.csv` | The nine `NB:` notes the editors placed between entries to explain gaps. |
| `basemap.geojson` | Natural Earth coastlines, clipped to the North Atlantic. |

### Columns

`No., Year, Date, Type, Title, Location, Details` are the article's own fields, transcribed
verbatim — `Date` reads as published, brackets and all. Everything after them is derived and
regenerated on every build, so **edit only the first seven**:

- `date_start` / `date_end` — the earliest and latest dates the published string allows.
  Estimated entries are placed at `date_start`.
- `date_likely` — where the editors listed alternatives (most likely first), their first choice.
  Differs from `date_start` only at #241 and #242.
- `date_precision` — `day` · `day_choice` · `day_range` · `month` · `month_range` · `season` ·
  `year` · `year_range` · `unknown`
- `date_certain` — `FALSE` for anything the editors bracketed or gave coarser than a day (76 of 700)
- `date_note` — prose the editors folded into the date, e.g. *during ship's passage* (#168)
- `categories` — pipe-separated: `lecture` (453) · `performance` (244) · `sermon` (3) ·
  `reading` (2). #145 and #612 are `lecture|sermon`.
- `type_inferred` — `TRUE` where the source bracketed the type or gave none (20)
- `cancelled` — `TRUE` for the seven engagements the sources say did not happen
- `subject_groups` / `subjects` — pipe-separated and positionally parallel, so
  `Corneille|Shakespeare` lines up with `Polyeuctus|Macbeth`
- `lat` / `lon` / `geo_precision` — from the gazetteer; `town` · `region` · `inferred` · `unmappable`

Six entries have no recorded location (#62, 168, 212, 325, 329, 635) and carry no coordinates.

## Rebuilding

```bash
python3 scripts/build_site.py
```

That runs `build_data.py` (dates + categories + gazetteer join) and inlines the result into
`scripts/template.html`. Editing the template and re-running is the way to change the page.

Two steps are separate because they hit the network and rarely need re-running:

```bash
python3 scripts/geocode.py    # gazetteer; Nominatim at 1 req/sec, cached
python3 scripts/basemap.py    # clip + simplify Natural Earth (downloads it if absent)
python3 scripts/subjects.py   # rewrite macdonald_subjects.csv from the defaults in the script
```

Note that `subjects.py` **overwrites** your edits — the CSV is the source of truth on a normal
build, so only run it to start over.

`geocode.py` never overwrites a gazetteer row whose `manual` column is `TRUE` — set it after
correcting a `lat`/`lon` by hand and the correction survives every rebuild.

Requires `shapely` (basemap only). Leaflet 1.9.4 is vendored at `scripts/leaflet.{js,css}` and
inlined at build time — the three CSS rules referencing bundled PNGs are stripped, since the page
uses neither the layers control nor the default marker icon.

`scripts/extract.py`, `group.py` and `build.py` are the original PDF extraction, kept for
provenance. `restore_dates.py` repaired a Date column mangled by a round trip through Excel, and
`fix_place_leaks.py` moved nine sub-places out of Title into Location; both were one-time and are
idempotent if re-run.

## The subject taxonomy

`macdonald_subjects.csv` maps each transcribed title to one or more `(group, work)` pairs, where
the group is the author or corpus and the work is the specific text or `(unspecified)`. That lets
the individual plays stay separate while still totalling under Shakespeare — 187 engagements, of
which Hamlet 59, Macbeth 43, King Lear 21, and 8 where the article names no play at all.

A title naming two subjects gets two rows and is counted under both, the same way an entry can be
both a lecture and a sermon; the entry is still one row and is never double-counted in the 700.
`Polyeuctus and Macbeth` therefore appears under Corneille and under Shakespeare.

Spelling variants are absorbed here (`Sir Walter Scott` → Scott, `[Macbeth]` → Macbeth,
`Coleridge's Rime of the Ancient Mariner` → The Rime of the Ancient Mariner). `Drama before
Shakespeare` is filed under survey lectures rather than Shakespeare — it is about what came
before him.

Edit the CSV freely: it wins over the defaults in `scripts/subjects.py` on every build, and
`build_data.py` fails loudly if a title has no row, so the mapping can never silently go stale.

## Editorial decisions

Places where the source is ambiguous or wrong are resolved in the `note` column of
`macdonald_places.csv` rather than silently — `Briston` is Bristol (entry #428 names Clifton
College), `Bishop Auckland` is in County Durham though the article marks it SCT, `Mentone` is
Menton in France, `Shields` is read as South Shields. Entry #311's title is literally `s` in the
published PDF; it is recorded here as `[Uncertain]`.
