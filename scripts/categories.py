"""Collapse the article's twelve Type labels into four categories.

`Lecture-sermon` and `Lecture/Sermon` are genuinely both things and stay multi-valued, so an
entry can appear under two filters. Labels the editors bracketed or left blank are still
assigned a category, but flagged `type_inferred` so an inference is never mistaken for a
statement of the source.
"""
import re

CATEGORIES = {
    'Lecture': (['lecture'], False),
    'Lectures': (['lecture'], False),
    '[Lecture]': (['lecture'], True),      # editors' own inference
    'Speaker': (['lecture'], True),        # #207, the Burns Society dinner address
    '': (['lecture'], True),               # 7 entries with no label; all read as lectures
    'Performance': (['performance'], False),
    'Performances': (['performance'], False),
    'Reading': (['reading'], False),
    'Dramatic Reading': (['reading'], False),
    'Sermon': (['sermon'], False),
    'Lecture-sermon': (['lecture', 'sermon'], False),
    'Lecture/Sermon': (['lecture', 'sermon'], False),
}

CANCELLED = re.compile(r'^cancell?ed\b', re.I)


def classify(type_label, details):
    cats, inferred = CATEGORIES[type_label]
    return {
        'categories': cats,
        'type_inferred': inferred,
        'cancelled': bool(CANCELLED.match(details.strip())),
    }
