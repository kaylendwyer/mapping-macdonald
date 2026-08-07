"""Parse the published date strings of the North Wind timeline into machine-readable form.

The article's convention: a firm date is written plainly (`November 10`); anything estimated
is bracketed, and brackets may wrap the whole date (`[June 28]`) or just the uncertain part
(`March [21]`). Alternatives are separated by `/` or `or` with the *most likely* first;
ranges use `-`. Coarser estimates give a month, a season, or a year.

Per the project's convention the timeline marker sits at the EARLIEST possible date
(`date_start`), while `date_likely` preserves the editors' first-listed alternative where the
two disagree (entries 241 and 242).
"""
import calendar
import re

MONTHS = {m: i for i, m in enumerate(calendar.month_name) if m}
SEASONS = {'Spring': 3, 'Summer': 6, 'Fall': 9, 'Autumn': 9, 'Winter': 12}
MON = '|'.join(MONTHS)


def _eom(year, month):
    return calendar.monthrange(year, month)[1]


def _iso(y, m, d):
    return '%04d-%02d-%02d' % (y, m, d)


def parse(raw, year):
    """-> dict(start, end, likely, precision, certain, note)."""
    year = int(year)
    note = ''
    s = raw.replace('’', "'").strip()
    bracketed = '[' in s
    s = s.replace('[', '').replace(']', '')
    # a prose annotation trailing the date, e.g. "September 20-29, during ship's passage"
    if ',' in s:
        s, note = (p.strip() for p in s.split(',', 1))
    s = re.sub(r'\s+', ' ', s).strip()

    def out(start, end, precision, likely=''):
        return {
            'start': start, 'end': end, 'likely': likely, 'precision': precision,
            'certain': not bracketed and precision == 'day', 'note': note,
        }

    if s.lower() == 'unknown':
        return out(_iso(year, 1, 1), _iso(year, 12, 31), 'unknown')

    # 1864 | 1865-1866 | 1873-74
    m = re.fullmatch(r'(\d{4})(?:-(\d{2,4}))?', s)
    if m:
        y0 = int(m.group(1))
        if m.group(2) is None:
            return out(_iso(y0, 1, 1), _iso(y0, 12, 31), 'year')
        tail = m.group(2)
        y1 = int(tail) if len(tail) == 4 else y0 - y0 % 100 + int(tail)
        return out(_iso(y0, 1, 1), _iso(y1, 12, 31), 'year_range')

    # April 28/23 | October 20 or 27 | February 1-3
    m = re.fullmatch(r'(%s) (\d{1,2})\s*(/|-| or )\s*(\d{1,2})' % MON, s)
    if m:
        mo = MONTHS[m.group(1)]
        a, b = int(m.group(2)), int(m.group(4))
        precision = 'day_range' if m.group(3) == '-' else 'day_choice'
        likely = _iso(year, mo, a) if precision == 'day_choice' else ''
        return out(_iso(year, mo, min(a, b)), _iso(year, mo, max(a, b)), precision, likely)

    # November 10
    m = re.fullmatch(r'(%s) (\d{1,2})' % MON, s)
    if m:
        mo = MONTHS[m.group(1)]
        return out(_iso(year, mo, int(m.group(2))), _iso(year, mo, int(m.group(2))), 'day')

    # January-March | April/May | February - March | June-July
    m = re.fullmatch(r'(%s)\s*[-/]\s*(%s)' % (MON, MON), s)
    if m:
        a, b = MONTHS[m.group(1)], MONTHS[m.group(2)]
        return out(_iso(year, a, 1), _iso(year, b, _eom(year, b)), 'month_range')

    # February
    if s in MONTHS:
        mo = MONTHS[s]
        return out(_iso(year, mo, 1), _iso(year, mo, _eom(year, mo)), 'month')

    # Fall | Spring | Summer | Autumn | Winter
    if s in SEASONS:
        mo = SEASONS[s]
        end_y, end_m = (year + 1, 2) if s == 'Winter' else (year, mo + 2)
        return out(_iso(year, mo, 1), _iso(end_y, end_m, _eom(end_y, end_m)), 'season')

    raise ValueError('unparsed date %r (year %s)' % (raw, year))
