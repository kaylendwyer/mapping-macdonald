"""Map the article's 103 title strings onto a two-level subject taxonomy.

`group` is the author or corpus, `work` the specific text or `(unspecified)`. That shape lets the
individual plays stay separate while still totalling under Shakespeare, and it treats every author
the same way — Coleridge's Rime of the Ancient Mariner nests under Coleridge exactly as Hamlet
nests under Shakespeare.

A title that names two subjects gets two entries and is counted under both, the same way #145 and
#612 are both a lecture and a sermon. The entry itself is still one row and is never
double-counted in the 700.

DEFAULT below is the starting point. `main()` writes it to macdonald_subjects.csv, which is
hand-editable and wins on every rebuild — so a revised grouping survives.
"""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUBJECTS = ROOT / 'macdonald_subjects.csv'
UNSPEC = '(unspecified)'

# title (verbatim, as transcribed) -> [(group, work), …]
DEFAULT = {
    # ── Shakespeare ────────────────────────────────────────────────────────
    'Hamlet': [('Shakespeare', 'Hamlet')],
    'Macbeth': [('Shakespeare', 'Macbeth')],
    '[Macbeth]': [('Shakespeare', 'Macbeth')],
    'King Lear': [('Shakespeare', 'King Lear')],
    'Merchant of Venice': [('Shakespeare', 'The Merchant of Venice')],
    'Julius Caesar': [('Shakespeare', 'Julius Caesar')],
    'As You Like It': [('Shakespeare', 'As You Like It')],
    'Twelfth Night': [('Shakespeare', 'Twelfth Night')],
    'Othello': [('Shakespeare', 'Othello')],
    'Timon of Athens': [('Shakespeare', 'Timon of Athens')],
    'The Tempest': [('Shakespeare', 'The Tempest')],
    'Much Ado About Nothing': [('Shakespeare', 'Much Ado About Nothing')],
    'Rape of Lucrece': [('Shakespeare', 'The Rape of Lucrece')],
    'Midsummer Night’s Dream': [('Shakespeare', 'A Midsummer Night’s Dream')],
    'A Midsummer Night’s Dream': [('Shakespeare', 'A Midsummer Night’s Dream')],
    'King Henry IV': [('Shakespeare', 'Henry IV')],
    'Henry the Fourth': [('Shakespeare', 'Henry IV')],
    'Romeo and Juliet': [('Shakespeare', 'Romeo and Juliet')],
    'Shakespeare’s Sonnet 110': [('Shakespeare', 'Sonnet 110')],
    'Shakespeare': [('Shakespeare', UNSPEC)],
    'Shakespeare’s Plays': [('Shakespeare', UNSPEC)],
    'Hamlet and Brutus': [('Shakespeare', 'Hamlet'), ('Shakespeare', 'Julius Caesar')],

    # ── Bunyan ─────────────────────────────────────────────────────────────
    'Pilgrim’s Progress 2': [('Bunyan', 'Pilgrim’s Progress, Part 2')],
    'Pilgrim’s Progress [2]': [('Bunyan', 'Pilgrim’s Progress, Part 2')],
    '[Pilgrim’s Progress 2]': [('Bunyan', 'Pilgrim’s Progress, Part 2')],
    'Pilgrim’s Progress 1': [('Bunyan', 'Pilgrim’s Progress, Part 1')],
    'Pilgrim’s Progress 1 and 2': [('Bunyan', 'Pilgrim’s Progress, Part 1'),
                                   ('Bunyan', 'Pilgrim’s Progress, Part 2')],
    'Pilgrim’s Progress': [('Bunyan', UNSPEC)],

    # ── individual authors ─────────────────────────────────────────────────
    'Tennyson': [('Tennyson', UNSPEC)],
    'Tennyson’s “In Memoriam”': [('Tennyson', 'In Memoriam')],
    'Wordsworth': [('Wordsworth', UNSPEC)],
    'William Wordsworth': [('Wordsworth', UNSPEC)],
    'Burns': [('Burns', UNSPEC)],
    '[Burns]': [('Burns', UNSPEC)],
    'Milton': [('Milton', UNSPEC)],
    'Hood': [('Hood', UNSPEC)],
    '[Hood]': [('Hood', UNSPEC)],
    'Shelley': [('Shelley', UNSPEC)],
    'Percy Bysshe Shelley': [('Shelley', UNSPEC)],
    'Scott': [('Scott', UNSPEC)],
    'Sir Walter Scott': [('Scott', UNSPEC)],
    'Browning': [('Browning', UNSPEC)],
    'Coleridge': [('Coleridge', UNSPEC)],
    'Samuel Taylor Coleridge': [('Coleridge', UNSPEC)],
    'Rime of the Ancient Mariner': [('Coleridge', 'The Rime of the Ancient Mariner')],
    'Coleridge’s Rime of the Ancient Mariner': [('Coleridge', 'The Rime of the Ancient Mariner')],
    'Byron': [('Byron', UNSPEC)],
    'Lord Byron': [('Byron', UNSPEC)],
    'Keats': [('Keats', UNSPEC)],
    'John Keats': [('Keats', UNSPEC)],
    'Dante': [('Dante', UNSPEC)],
    'Spenser': [('Spenser', UNSPEC)],
    'Works of Spenser': [('Spenser', UNSPEC)],
    'Elizabethan Poets [Edmund Spenser]': [('Spenser', UNSPEC)],
    'Sidney': [('Sidney', UNSPEC)],
    'Sir Philip Sidney': [('Sidney', UNSPEC)],
    'John Donne': [('Donne', UNSPEC)],
    'Geoffrey Chaucer': [('Chaucer', UNSPEC)],
    'Elizabeth Barrett Browning': [('E. B. Browning', UNSPEC)],
    'Polyeuctus': [('Corneille', 'Polyeuctus')],

    # paired authors — counted under both
    'Scott and Byron': [('Scott', UNSPEC), ('Byron', UNSPEC)],
    'Shelley and Keats': [('Shelley', UNSPEC), ('Keats', UNSPEC)],
    'Wordsworth and Coleridge': [('Wordsworth', UNSPEC), ('Coleridge', UNSPEC)],
    'Robert Burns and Thomas Hood': [('Burns', UNSPEC), ('Hood', UNSPEC)],
    'Polyeuctus and Macbeth': [('Corneille', 'Polyeuctus'), ('Shakespeare', 'Macbeth')],
    'Shelley and Cymbeline': [('Shelley', UNSPEC), ('Shakespeare', 'Cymbeline')],

    # ── scripture ──────────────────────────────────────────────────────────
    'Zaccheus': [('Scripture', 'Zacchaeus (Luke 19)')],
    'Luke 12': [('Scripture', 'Luke 12')],
    'On Justice': [('Scripture', 'On Justice')],

    # ── the family's entertainments ────────────────────────────────────────
    'The Tetterby’s': [('Dickens', 'The Tetterbys')],
    'The Tetterby’s and Obstinacy': [('Dickens', 'The Tetterbys'),
                                     ('Family entertainments', 'Obstinacy')],
    'Illustrated Proverbs': [('Family entertainments', 'Illustrated Proverbs')],
    'Tableaux Vivante': [('Family entertainments', 'Tableaux Vivants')],
    'Cinderella, Beauty and the Beast': [('Family entertainments', 'Cinderella'),
                                         ('Family entertainments', 'Beauty and the Beast')],

    # ── survey lectures and occasional addresses ───────────────────────────
    'Sixteenth-Century Poetry': [('Survey lectures', 'Sixteenth-century poetry')],
    'Sixteenth-Century Drama': [('Survey lectures', 'Sixteenth-century drama')],
    'Drama before Shakespeare': [('Survey lectures', 'Sixteenth-century drama')],
    'Elizabethan Literature': [('Survey lectures', 'Elizabethan literature')],
    'English Literature': [('Survey lectures', 'English literature')],
    'English Literature and Language': [('Survey lectures', 'English literature')],
    'Contemporary Poets': [('Survey lectures', 'Contemporary poets')],
    'Contemporary Authors': [('Survey lectures', 'Contemporary poets')],
    'Lake Poets': [('Survey lectures', 'The Lake poets')],
    'Imagination': [('Survey lectures', 'Imagination')],
    'Individual Development': [('Survey lectures', 'Individual development')],
    'Inaugural Address': [('Occasional addresses', 'Inaugural address')],
    'Opening Academic Address': [('Occasional addresses', 'Opening academic address')],
    'Burns Society Dinner': [('Occasional addresses', 'Burns Society dinner')],

    # ── science ────────────────────────────────────────────────────────────
    'Natural Philosophy': [('Science & mathematics', 'Natural philosophy')],
    'Natural Philosophy and Mathematics': [('Science & mathematics', 'Natural philosophy'),
                                           ('Science & mathematics', 'Mathematics')],
    'English Literature, Physical Science, Natural Philosophy, Mathematics': [
        ('Survey lectures', 'English literature'),
        ('Science & mathematics', 'Physical science'),
        ('Science & mathematics', 'Natural philosophy'),
        ('Science & mathematics', 'Mathematics')],

    # ── no subject recorded ────────────────────────────────────────────────
    'unknown': [('Unknown', '(unknown)')],
    '': [('Unknown', '(unknown)')],
    '[Uncertain]': [('Unknown', '(unknown)')],
}

NOTES = {
    'Drama before Shakespeare': 'filed under survey lectures, not Shakespeare — it is about what came before him',
    'Shakespeare': 'the article names no play',
    'Shakespeare’s Plays': 'the article names no play',
    'Pilgrim’s Progress': 'the article does not say which part',
    '[Uncertain]': 'the published PDF prints the title as a bare "s"',
    'The Tetterby’s and Obstinacy': 'the Tetterbys are from Dickens’s The Haunted Man',
    'Polyeuctus': 'Louisa MacDonald’s adaptation of Corneille',
}


def write_default():
    rows = []
    for title in sorted(DEFAULT, key=lambda t: (t == '', t.lower())):
        for group, work in DEFAULT[title]:
            rows.append({'title': title, 'group': group, 'work': work,
                         'note': NOTES.get(title, '')})
    with open(SUBJECTS, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['title', 'group', 'work', 'note'])
        w.writeheader()
        w.writerows(rows)
    return rows


def load():
    """title -> [(group, work), …], from the CSV if it exists, else the default."""
    if not SUBJECTS.exists():
        write_default()
    out = {}
    for r in csv.DictReader(open(SUBJECTS, encoding='utf-8')):
        out.setdefault(r['title'], []).append((r['group'], r['work']))
    return out


if __name__ == '__main__':
    rows = write_default()
    print('wrote %s: %d rows, %d titles, %d groups'
          % (SUBJECTS.name, len(rows), len(DEFAULT), len({r['group'] for r in rows})))
