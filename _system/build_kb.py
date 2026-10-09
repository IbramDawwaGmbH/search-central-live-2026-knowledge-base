"""Rebuild every generated part of the knowledge base from the source data (schema v2).

Source of truth (edit these):   20-claims/day*.yaml, topics.yaml, sessions.yaml, sources.yaml; 25-kits/ (the developer and content kits)
Generated (never edit by hand): 30-topics/, 40-sessions/, 50-maps/, 60-outputs/agent-pack/, 60-outputs/dev/, 60-outputs/content/,
                                60-outputs/badges/ (drawn by _system/badges.py), 60-outputs/README.md, 70-private/private-claims.md

Usage:  python _system/build_kb.py               validate everything, then rebuild
        python _system/build_kb.py --check       validate only, write nothing
        python _system/build_kb.py --root DIR    work on another copy of the repository
        python _system/build_kb.py --check --stoplist   also print the stop list of 20-claims/entities.yaml (the most frequent words)
Needs:  pyyaml. Field rules: _system/schema/claim.md; kits: _system/kits.py; default style (mindmap, badges): _system/theme.yaml
        read by _system/theme.py (art-deco when the file is absent). Every check runs before any file is deleted or
written; a key repeated in one YAML entry is an error. After writing, every shared output is scanned for the excluded photos (EXCLUDED).
No output depends on the clock: the version comes from CHANGELOG.md, dates from the data.
Edition: _system/edition.yaml (read by _system/edition.py, edition_settings()). Without it, or with "edition: full", the build makes the
full edition exactly as before; "edition: community" makes the open community edition: the media kit is the short preview kept in
25-kits/content.yaml, the numbers registry and the question bank are not written (kits.py), and the READMEs, INDEX.md, AGENTS.md (its
<!-- edition: ... --> blocks) and the media-kit badge say so.
The agent pack's graph.json and links.json (pack_graph) hold only links that already exist (claim fields, topics.yaml, sessions.yaml,
the kits' cited claims and docs); `used_by` on every claim and the topic pages' "Built on these claims" come from the same links.
The things (knowledge graph phase 1) come from 20-claims/entities.yaml, the one hand-written file of the graph: load_entities() checks it and
matches each thing's name and aliases against the public claims (never the other way round: a claim's record is never changed); everything
else about a thing (mentions on claims.jsonl, entities.json, the cards in agent-pack/entities/, graph.json, the kit items' `entities`, the
"Things" sections and 50-maps/entity-index.md) is derived from those matches by entity_model().
Folder READMEs follow one pattern (breadcrumb, title, lead, header illustration, divider, "What's here", generated note, pipeline
navigation). Their HTML (the illustration's <picture>, the divider, the centred navigation in <sub>, the badge row of 60-outputs/README.md)
is fixed strings in this file, never built from data.
"""
import csv, datetime, difflib, hashlib, importlib.util, inspect, io, json, re, shutil, sys, time, types, unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
AUTHOR = 'Ibrahim Anjro'
LABELS = {'slide': 'Slide', 'stage': 'Stage', 'docs': 'Docs', 'press': 'Press', 'analysis': 'Analysis'}
LABEL_HELP = {'slide': 'shown on screen', 'stage': 'said on stage', 'docs': "Google's documentation",
              'press': 'reported by third-party press', 'analysis': "the author's interpretation"}
VER = {'confirmed': 'confirmed by Google docs', 'consistent': 'consistent with Google docs', 'undocumented': 'not in Google docs',
       'source': 'is the documentation', 'n/a': ''}
EVENT = ('slide', 'stage')
REL = {'repeats': ('Repeats', 'Repeated by'), 'extends': ('Extends', 'Extended by'), 'contradicts': ('Contradicts', 'Contradicted by'),
       'updates': ('Updates', 'Updated by'), 'answers': ('Answers', 'Answered by')}
COVERAGE = ('slides', 'notes', 'transcript', 'one-slide', 'video', 'none')
KINDS = ('talk', 'lightning', 'panel', 'qa', 'poster', 'break')
EXCLUDED = ('IMG_4692',)  # never cited, never in a shared output (Day 2: another attendee's badge). Same list in site/build_site.py.
EXCLUDED_RE = re.compile(r'(?<![A-Za-z0-9])(' + '|'.join(EXCLUDED) + r')(?!\d)', re.I)
SHARED_OUT = ('30-topics', '40-sessions', '50-maps', '60-outputs')
TEXT_EXT = {'.md', '.json', '.jsonl', '.html', '.htm', '.js', '.css', '.csv', '.txt', '.yaml', '.yml', '.svg', '.xml'}
CLAIM_KEYS = ('id', 's', 'label', 'ev', 'ver', 'src', 'topics', 'text', 'quote', 'private', 'who', 'rel', 'quote_checked')
SESSION_KEYS = ('id', 'time', 'title', 'speaker', 'coverage', 'note', 'role', 'kind')
AREA_KEYS, TOPIC_KEYS = ('id', 'title', 'blurb', 'topics'), ('id', 'title', 'summary', 'do', 'related', 'cites')
SOURCE_KEYS = ('title', 'url', 'publisher', 'checked', 'kind')
KEBAB = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
CID = re.compile(r'\bD\d+-C\d+\b')
CRANGE = re.compile(r'\b(D(\d+)-C(\d+))\s*(?:to|–|—)\s*(D(\d+)-C(\d+))\b')
WORD = re.compile(r"[^\W_][\w'’-]*")
TAG = re.compile(r'<[A-Za-z!/?][^<>`\n]*>')  # a tag-like fragment with no backtick inside: shown as a code span
PHOTO = re.compile(r'[A-Za-z]+_?\d[\w-]*')
EV_FORMS = [re.compile(p) for p in (r'notes', r'agenda', r'T:([\w.-]+):\d+', r'T \d{1,2}:\d{2}:\d{2}(?:-\d{1,2}:\d{2}:\d{2})?', r'video:([\w.-]+)')]
GEN = '<!-- GENERATED by _system/build_kb.py. Do not edit; change 20-claims/ and rebuild. -->\n'
BADGES = ('version', 'days', 'claims', 'docs-backed', 'topics', 'sources', 'dev-kit', 'media-kit', 'privacy')  # 60-outputs/badges/<name>.svg

# ---------------------------------------------------------------- folder README chrome. Fixed HTML strings only: data never goes into
# HTML; every piece of data in a README is Markdown that went through md() or cell(). The test whitelist in _system/tests/run_tests.py
# allows exactly these lines.
PIPELINE = ('00-raw', '10-sources', '20-claims', '25-kits', '30-topics', '40-sessions', '50-maps', '60-outputs', '70-private')
DIVIDER = {1: '<p align="center"><img src="../_system/brand/divider.svg" width="600" alt="Section divider"></p>',
           2: '<p align="center"><img src="../../_system/brand/divider.svg" width="600" alt="Section divider"></p>'}
# The header illustration of each generated README, drawn by _system/brand/make_illustrations.py as <slug>-light.svg (sunlit
# water) and <slug>-dark.svg (night water) in _system/brand/illustrations/. The slug is the README's folder with "/" turned into
# "-"; the alt text says what the picture shows and how it relates to the README's title. A README whose slug is missing here
# (a new topic area) gets no picture until a scene is drawn for it and a line is added.
ILLUSTRATION_ALT = {
    '30-topics': 'The Diver bot glides over a terraced reef of thirteen different corals, one for each topic area of the knowledge base.',
    '30-topics-ai-features': 'A large glowing jellyfish, its bell patterned like a network, reaches its tentacles down to pages and a book on '
                             'the seabed as the Diver bot waves: AI features and how they use web content.',
    '30-topics-community': 'The Diver bot sits with a turtle, a crab, an octopus and fish around a glowing campfire of bubbles on the seabed: '
                           'the Search team and the community working together.',
    '30-topics-content-and-media': 'The Diver bot works an underwater camera on a tripod, beside floating photo, video and image cards tied '
                                   'together by a branching string of pearls: structured data and media.',
    '30-topics-crawling': 'The Diver bot follows a glowing cable from page to page across the seabed, while one branch dips to a fallen rock '
                          'with a no-entry marker: how Google discovers and fetches URLs, and what gets in the way.',
    '30-topics-how-search-works': 'A pipeline runs across the seabed, from an intake funnel through a processing chamber and an index tank to '
                                  'an outlet of result bubbles, with the Diver bot swimming above it: how Search works.',
    '30-topics-index-and-signals': 'A beacon tower on the seabed sends out rings of light to signal buoys around it, while the Diver bot '
                                   'reads them in its guide: the signals Google calculates while indexing.',
    '30-topics-indexing': 'The Diver bot files a card into an open drawer of a coral filing cabinet, with two matching shells on top and one '
                          'marked as the original: how Google processes and stores a page.',
    '30-topics-international': 'The Diver bot waves beside a globe on the seabed, surrounded by speech bubbles in different colours linked to '
                               'it: one site in many languages.',
    '30-topics-publisher-controls': 'The Diver bot works the lever on a control panel whose sliders and switches open and close two streams '
                                    'of bubbles: the controls site owners have over how they appear in Search.',
    '30-topics-rendering-javascript': 'Under a hanging lamp, the Diver bot guides floating blocks (a header, an image, a button) into an '
                                      'empty page frame on an easel: how Google renders JavaScript into a page.',
    '30-topics-search-console': 'The Diver bot points at a sonar screen on a seabed console with gauges, switches and a small chart: Search '
                                'Console and its data.',
    '30-topics-search-landscape': 'From a rocky outcrop, the Diver bot points out over a wide underwater valley towards a bright horizon: the '
                                  'state of Search and where it is heading.',
    '30-topics-search-trends': 'Columns of bubbles rise across the seabed like a bar chart, traced by a climbing strand of kelp, as the Diver '
                               'bot studies them: search trends and search interest.',
    '30-topics-serving-ranking': 'Three fish wearing award rosettes stand on a three-step podium while more fish queue and the Diver bot '
                                 'referees: how Google ranks results and serves the results page.',
    '40-sessions': 'The Diver bot waves from a lectern on a seabed stage framed by kelp curtains, under a spotlight and beside a slide, with '
                   'a row of fish watching: the sessions of the event.',
    '50-maps': 'The Diver bot sits beside a large map unrolled on the seabed, with a branching tree of routes, a compass rose and a marked '
               'spot: the maps of the knowledge base.',
    '60-outputs': 'The Diver bot points a cargo net up to a boat at the surface; the net holds a globe, a field guide, a toolbox, a conch and '
                  'a chip, with badges hanging off its sides: everything the knowledge base produces.',
    '60-outputs-content': 'The Diver bot points at a conch megaphone on a coral stand that sends out rings of sound and cards of facts, myths '
                          'and quotes, with a camera and a microphone drifting nearby: the media kit.',
    '60-outputs-dev': 'The Diver bot peeks out of the hatch of a small submarine in a seabed workshop, with tools on a board and a checklist '
                      'of green ticks: the developer kit.',
}
CENTER = ('<div align="center">', '</div>')  # around the navigation, which is Markdown in <sub> (small type)
SMALL = ('<sub>', '</sub>')
BADGE_ALT = {'version': 'Version and the date the data runs to', 'days': 'Event days covered so far', 'claims': 'Number of public claims',
             'docs-backed': "Share of graded slide and stage claims that Google's documentation confirms or supports", 'topics': 'Number of topics',
             'sources': 'Number of sources', 'dev-kit': 'Developer kit: number of requirements', 'media-kit': 'Media kit: number of facts',
             'privacy': 'Privacy: private material excluded'}
BADGE_ALT_COMMUNITY = dict(BADGE_ALT, **{'media-kit': 'Media kit: full edition on request'})  # the community edition's badge counts nothing
# how a generated README describes the default style of _system/theme.yaml (fixed Markdown, picked by the style key)
STYLE_TEXT = {
    'deep-dive': {'badges': 'the Deep Dive pills (an indigo label, an ocean-blue value and a small bubble on the seam)',
                  'mindmap': 'It is in the Deep Dive style and follows the light or dark setting of the computer (dark is night water). '
                             'It has no switch: for Art Deco, set `default: art-deco` in `_system/theme.yaml` and rebuild.'},
    'art-deco': {'badges': 'the Art Deco pills (an onyx label, a gold value and a small diamond on the seam)',
                 'mindmap': 'It is in the Art Deco style and follows the light or dark setting of the computer. '
                            'It has no switch: for Deep Dive, set `default: deep-dive` in `_system/theme.yaml` and rebuild.'}}
BADGE_DIRS = ('badges/',)  # only 60-outputs/README.md shows a badge row (the root README is hand-written)


# ---------------------------------------------------------------- helpers
def nt(s):  # one line, single spaces
    return ' '.join(str(s).split())


def md(s):
    """Markdown-safe inline text, read the way CommonMark reads it: a backtick run opens a code span only if a run of the
    same length follows. Real code spans stay as they are and every other backtick is escaped, so nothing can pair with a
    backtick written around this text. Outside code spans a simple tag such as <a href> becomes a code span (when no
    backtick touches it) and every other '<' becomes &lt;, so no HTML tag, comment or autolink can form."""
    s, out, i = nt(s), [], 0
    while i < len(s):
        ch = s[i]
        if ch == '\\':  # an escape pair stays as it is; a lone backslash at the end is doubled
            out.append(s[i:i + 2] if i + 1 < len(s) else '\\\\'); i += 2
        elif ch == '<':
            m = TAG.match(s, i)
            if m and not (out and out[-1].endswith('`')) and not s.startswith('`', m.end()): out.append(f'`{m[0]}`'); i = m.end()
            else: out.append('&lt;'); i += 1
        elif ch != '`': out.append(ch); i += 1
        else:
            j = i
            while j < len(s) and s[j] == '`': j += 1
            m = re.compile(rf'(?<!`){"`" * (j - i)}(?!`)').search(s, j)
            if m: out.append(s[i:m.end()]); i = m.end()
            else: out.append('\\`' * (j - i)); i = j
    return ''.join(out)


def cell(s):
    return md(s).replace('|', '\\|')


# The web edition's fold() in _system/site/site.js, letter for letter: lower case, NFD, combining marks dropped, then the few
# letters with no decomposition spelled out. norm_key() is site.js norm() without its padding spaces: the key of an alias in
# links.json. node_slug() turns a name into the id part of a node (a glossary term: term:<slug>).
SPELL = {'ł': 'l', 'đ': 'd', 'ð': 'd', 'ø': 'o', 'ı': 'i', 'ß': 'ss', 'æ': 'ae', 'œ': 'oe', 'þ': 'th', 'ς': 'σ'}


def fold(s):
    s = unicodedata.normalize('NFD', str(s or '').lower())
    return ''.join(SPELL.get(ch, ch) for ch in s if not unicodedata.category(ch).startswith('M'))


def norm_key(s):
    return ' '.join(re.findall(r'[^\W_]+', fold(s)))


def node_slug(s):
    return re.sub(r'[^a-z0-9]+', '-', fold(s)).strip('-')


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def anchor(s):  # the id GitHub gives a Markdown heading (the same rule as kits.anchor)
    return re.sub(r'[^\w\- ]', '', s.strip().lower()).replace(' ', '-')


def badge_row(where, *rows, alt=BADGE_ALT):
    """Centred badges: one row per list of names, built only from the fixed names, folders and alt texts above (alt: BADGE_ALT, or
    BADGE_ALT_COMMUNITY in the community edition)."""
    if where not in BADGE_DIRS or alt not in (BADGE_ALT, BADGE_ALT_COMMUNITY) or any(n not in alt for r in rows for n in r):
        raise ValueError(f'not a README badge: {where} {rows}')
    return '<p align="center">' + '<br>'.join(' '.join(f'<img src="{where}{n}.svg" alt="{alt[n]}">' for n in r) for r in rows) + '</p>'


def nav(*links):
    """'← previous · up · next →' from [(text, link)]; a side with nothing to link is (text, None) and is left out."""
    return ('← ' if links[0][1] else '') + ' · '.join(f'[{t}]({h})' for t, h in links if h) + (' →' if links[-1][1] else '')


def pipeline_nav(folder, up):  # the folders before and after this one, in pipeline order
    i = PIPELINE.index(folder)
    return nav(*[(f, f'{up}{f}/README.md') if f else ('', None) for f in (PIPELINE[i - 1] if i else None, PIPELINE[i + 1] if i + 1 < len(PIPELINE) else None)])


def picture(depth, art):
    """The header illustration of a README depth folders below the root: a <picture> that GitHub shows as the night-water card in dark
    mode and the sunlit one otherwise. art is a key of ILLUSTRATION_ALT; the path and the alt text come from that key and its fixed
    line only. None when art has no illustration."""
    key = next((k for k in ILLUSTRATION_ALT if k == art), None)
    if key is None: return None
    base = '../' * depth + '_system/brand/illustrations/' + key
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{base}-dark.svg">'
            f'<img src="{base}-light.svg" width="100%" alt="{ILLUSTRATION_ALT[key]}"></picture>')


def readme(depth, trail, gen, title, lead, body, foot, art=None):
    """A folder README in the shared pattern: breadcrumb (line 1), generated-file comment, title, lead, header illustration (art, a key
    of ILLUSTRATION_ALT), divider, body, divider and the navigation in small type. trail is [(text, link or None)]; trail, title, lead,
    body and foot are Markdown whose data already went through md(). The only HTML is the fixed strings above."""
    pic = picture(depth, art)
    out = [' / '.join(f'[{t}]({h})' if h else f'**{t}**' for t, h in trail), '', gen.strip(), '', f'# {title}', '', lead, '']
    out += ([pic, ''] if pic else []) + [DIVIDER[depth], '']
    out += list(body)
    while out[-1] == '': out.pop()
    return '\n'.join(out + ['', DIVIDER[depth], '', CENTER[0], '', SMALL[0] + foot + SMALL[1], '', CENTER[1], ''])


def generated_note(what, change):
    return ['> [!NOTE]', f'> **Generated** by {what}. Do not edit; change {change} and run `rebuild.bat`.']


def words(q):
    return len(WORD.findall(q or ''))


def isdate(v):  # a real calendar date: YAML date or "YYYY-MM-DD"; never a date with a time
    if type(v) is datetime.date: return True
    try: return isinstance(v, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', v) is not None and bool(datetime.date.fromisoformat(v))
    except ValueError: return False


def as_list(v):
    return v if isinstance(v, list) else [] if v in (None, '') else [v]


def speakers(s):
    return [x for x in as_list(s.get('speaker')) if x]


def ev_list(c):
    return [x.strip() for e in as_list(c.get('ev')) for x in str(e).split(',') if x.strip()]


def cited_ids(txt, where, E):
    """Claim IDs mentioned in free text. 'D1-C010 to D1-C014' counts as the inclusive range."""
    txt, out = str(txt), []
    for m in CRANGE.finditer(txt):
        if m[2] != m[5] or int(m[3]) > int(m[6]) or int(m[6]) - int(m[3]) > 99:
            E.append(f'{where}: cannot read the range "{m[0]}"'); continue
        out += [f'D{m[2]}-C{i:03d}' for i in range(int(m[3]), int(m[6]) + 1)]
    return out + CID.findall(txt)


def dups(items, where, E):  # a value listed twice would be counted and rendered twice
    for x, k in Counter(items).items():
        if k > 1: E.append(f'{where} lists {x} {k} times; keep one')


def hint(k, allowed):
    m = difflib.get_close_matches(str(k), allowed, 1, 0.6)
    return f' (did you mean "{m[0]}"?)' if m else ''


class StrictYAMLError(yaml.YAMLError):
    pass


class StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses a key repeated in one mapping (PyYAML would keep the last value without a word, so a
    second 'private: false' could publish a private claim) and a date that is not on the calendar."""
    def construct_mapping(self, node, deep=False):
        seen = {}
        cid = next((v.value for k, v in node.value if isinstance(k, yaml.ScalarNode) and k.value == 'id' and isinstance(v, yaml.ScalarNode)), None)
        for k, _ in node.value:
            if not isinstance(k, yaml.ScalarNode) or k.tag == 'tag:yaml.org,2002:merge': continue
            key = self.construct_object(k)
            if key in seen:
                raise StrictYAMLError(f'line {k.start_mark.line + 1}: ' + (f'{cid}: ' if cid else '') +
                                      f'key "{key}" appears twice in one entry (first on line {seen[key] + 1}); keep one')
            seen[key] = k.start_mark.line
        return super().construct_mapping(node, deep)

    def construct_yaml_timestamp(self, node):
        try: return super().construct_yaml_timestamp(node)
        except ValueError as e: raise StrictYAMLError(f'line {node.start_mark.line + 1}: {node.value} is not a real date ({e})') from None


StrictLoader.add_constructor('tag:yaml.org,2002:timestamp', StrictLoader.construct_yaml_timestamp)


def load_yaml(text):  # used by every script that reads the knowledge base's YAML (ingest.py, eval_check.py)
    return yaml.load(text, Loader=StrictLoader)


def read_yaml(p, E):
    where = f'{p.parent.name}/{p.name}'
    try:
        return load_yaml(p.read_text(encoding='utf-8'))
    except FileNotFoundError: E.append(f'{where}: file missing')
    except UnicodeDecodeError: E.append(f'{where}: not UTF-8 text; save it as UTF-8')
    except StrictYAMLError as e: E.append(f'{where}: {e}')
    except yaml.YAMLError as e: E.append(f'{where}: YAML error: {nt(e)}')
    except (ValueError, TypeError) as e: E.append(f'{where}: a value cannot be read: {nt(e)}')
    return None


def kits():  # _system/kits.py, loaded only by the build: ingest.py, eval_check.py and make_pdf.py import this file without it
    if 'KITS' not in globals():
        spec = importlib.util.spec_from_file_location('kb_kits', Path(__file__).resolve().with_name('kits.py'))
        globals()['KITS'] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(KITS)
    return KITS, types.SimpleNamespace(**globals())


def badges_module():  # _system/badges.py, loaded like kits.py from the folder of this script; None when the file is missing
    if 'BADGE_MOD' not in globals():
        p = Path(__file__).resolve().with_name('badges.py')
        if not p.exists(): return None
        spec = importlib.util.spec_from_file_location('kb_badges', p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        globals()['BADGE_MOD'] = m
    return BADGE_MOD


def edition_module():  # _system/edition.py, loaded like badges.py from the folder of this script; None when the file is missing
    if 'EDITION_MOD' not in globals():
        p = Path(__file__).resolve().with_name('edition.py')
        if not p.exists(): return None
        spec = importlib.util.spec_from_file_location('kb_edition', p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        globals()['EDITION_MOD'] = m
    return EDITION_MOD


FULL_EDITION = {'edition': 'full', 'author': '', 'linkedin': '', 'company': {'name': '', 'url': ''}, 'full_kit': {}}
FULL_KIT_KEYS = ('facts', 'myths', 'angles', 'quotes', 'stat_facts', 'audience_questions')
EDITION_MARK = re.compile(r'<!-- edition: (full|community|end) -->')
LINK_URL = re.compile(r'https://[^\s<>()\[\]"\'`]+')


def edition_settings(root, E):
    """Which edition the build makes, from _system/edition.yaml (read by _system/edition.py): the full edition when the file is
    absent or says `edition: full`, so the main branch builds exactly as before; `edition: community` makes the community edition
    (the media kit is a short preview, see kits.py). The community edition needs the author, the LinkedIn and company links it
    shows and the counts of the full kit."""
    f = root / '_system' / 'edition.yaml'
    try:
        m = edition_module()
    except Exception as x:
        E.append(f'_system/edition.py cannot be loaded: {type(x).__name__}: {nt(x)}'); return dict(FULL_EDITION)
    if m is None:
        if f.exists(): E.append('_system/edition.py: file missing (it reads _system/edition.yaml)')
        return dict(FULL_EDITION)
    try:
        ed = m.load(root)
    except SystemExit as x:
        E.append(nt(str(x)).removeprefix('ERROR: ')); return dict(FULL_EDITION)
    except (yaml.YAMLError, OSError, ValueError, TypeError, AttributeError) as x:
        E.append(f'_system/edition.yaml cannot be read: {nt(x)}'); return dict(FULL_EDITION)
    if ed.get('edition') != 'community': return ed
    for k, v in (('author', ed.get('author')), ('company name', ed['company'].get('name'))):
        if not isinstance(v, str) or not v.strip(): E.append(f'_system/edition.yaml: the community edition needs {k}')
    for k, v in (('linkedin', ed.get('linkedin')), ('company url', ed['company'].get('url'))):
        if not isinstance(v, str) or not LINK_URL.fullmatch(v): E.append(f'_system/edition.yaml: {k} must be a full https:// link with no spaces, found {v!r}')
    fk = ed.get('full_kit') if isinstance(ed.get('full_kit'), dict) else {}
    for k in FULL_KIT_KEYS:
        if isinstance(fk.get(k), bool) or not isinstance(fk.get(k), int) or fk[k] < 0: E.append(f'_system/edition.yaml: full_kit needs {k}, a whole number')
    return ed


def community(kb):
    return (kb.get('edition') or {}).get('edition') == 'community'


def edition_text(text, edition):
    """A template with edition blocks: the lines between '<!-- edition: full -->' (or '<!-- edition: community -->') and
    '<!-- edition: end -->' are kept only in that edition, and the marker lines go. Everything else is kept as it is, line endings
    included, so a template without markers comes out byte for byte."""
    out, cur = [], None
    for ln in text.splitlines(keepends=True):
        m = EDITION_MARK.fullmatch(ln.strip())
        if m: cur = None if m[1] == 'end' else m[1]; continue
        if cur is None or cur == edition: out.append(ln)
    return ''.join(out)


def edition_marks_ok(text, where, E):
    """The edition blocks of a template: a block opens with <!-- edition: full --> or <!-- edition: community -->, may switch once to the
    other edition (the text for the other edition in its place) and closes with <!-- edition: end -->."""
    cur, seen = None, set()
    for i, ln in enumerate(text.splitlines(), 1):
        m = EDITION_MARK.fullmatch(ln.strip())
        if not m: continue
        if m[1] == 'end':
            if cur is None: E.append(f'{where}: line {i}: <!-- edition: end --> closes no edition block')
            cur, seen = None, set()
            continue
        if m[1] in seen: E.append(f'{where}: line {i}: <!-- edition: {m[1]} --> twice in one block; close it with <!-- edition: end --> first')
        cur = m[1]; seen.add(m[1])
    if cur is not None: E.append(f'{where}: an edition block is never closed with <!-- edition: end -->')


def theme_module():  # _system/theme.py, loaded like badges.py from the folder of this script; None when the file is missing
    if 'THEME_MOD' not in globals():
        p = Path(__file__).resolve().with_name('theme.py')
        if not p.exists(): return None
        spec = importlib.util.spec_from_file_location('kb_theme', p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        globals()['THEME_MOD'] = m
    return THEME_MOD


def default_style(root, E):
    """The default visual style ('art-deco' or 'deep-dive') from _system/theme.yaml, read and checked by _system/theme.py. It sets
    the mindmap's style and the badges' style. A copy without theme.yaml keeps the original look, art-deco; a bad value
    is an error."""
    f = root / '_system' / 'theme.yaml'
    if not f.exists(): return 'art-deco'
    try:
        m = theme_module()
    except Exception as x:
        E.append(f'_system/theme.py cannot be loaded: {type(x).__name__}: {nt(x)}'); return 'art-deco'
    if m is None: E.append('_system/theme.py: file missing (it reads _system/theme.yaml)'); return 'art-deco'
    try:
        return m.default_style(f)
    except ValueError as x:  # theme.ThemeError names the file, the bad value and the allowed values
        E.append(nt(x)); return 'art-deco'


def badge_stats(kb):
    """The numbers the README badges show, counted by the same rules as the outputs that print them (public claims only)."""
    S, public = kb['sessions'], [c for c in kb['claims'] if c.get('private') is not True]
    used = sorted({S[c['s']]['day'] for c in public})
    dates = {d['day']: d['date'] for d in kb['days']}
    ev = Counter(c['ver'] for c in public if c['label'] in EVENT)
    backed, graded = ev['confirmed'] + ev['consistent'], ev['confirmed'] + ev['consistent'] + ev['undocumented']
    cited = lambda cs: {k for c in cs for k in c.get('src', [])}
    kit = kb.get('kits') or {}
    kit_docs = {x for a in kit.get('areas', []) for r in a['requirements'] for x in r.get('docs') or []}  # shared through the developer kit
    private_only = cited(c for c in kb['claims'] if c.get('private') is True) - cited(public) - kit_docs - ent_docs(kb)  # left out of sources.json too
    st = {'version': kb['version'], 'data_through': dates[used[-1]] if used else '', 'days_done': len(used), 'days_total': len(kb['days']),
          'claims': len(public), 'docs_backed_pct': (200 * backed + graded) // (2 * graded) if graded else 0,  # rounded half up, no floats
          'topics': len(kb['topics']), 'sources': len(kb['sources']) - len(private_only),
          'requirements': sum(len(a['requirements']) for a in kit.get('areas', [])), 'facts': len((kit.get('content') or {}).get('facts', []))}
    if community(kb): st['edition'] = 'community'  # the media-kit badge says the full kit is on request instead of counting the preview
    return st


SVG_UNSAFE = re.compile(r'<script|<foreignObject|<!ENTITY|\son[a-z]+\s*=|(?:href|src)\s*=\s*(?:"(?!#)|\'(?!#)|(?![\s"\'#]))', re.I)


def make_badges(kb, E):
    """Draw the README badges in memory with _system/badges.py (nothing is written here) and check what comes back: the nine
    expected files, each well-formed SVG with an <svg> root and no script, event handler or link to another file."""
    where = '_system/badges.py'
    try:
        m = badges_module()
    except Exception as x:
        E.append(f'{where} cannot be loaded: {type(x).__name__}: {nt(x)}'); return {}
    if m is None: E.append(f'{where}: file missing (it draws the README badges in 60-outputs/badges/)'); return {}
    style = kb.get('style', 'art-deco')
    try:
        if 'style' in inspect.signature(m.render).parameters: out = m.render(dict(kb['badge_stats']), style=style)
        elif style != 'art-deco': E.append(f'{where}: render() takes no style, so it cannot draw the {style} badges set in _system/theme.yaml'); return {}
        else: out = m.render(dict(kb['badge_stats']))  # a render(stats) without styles draws the original Art Deco badges
    except Exception as x:
        E.append(f'{where}: render() failed: {type(x).__name__}: {nt(x)}'); return {}
    if not isinstance(out, dict): E.append(f'{where}: render() must return a mapping of file name to SVG text'); return {}
    for k in sorted({f'{n}.svg' for n in BADGES} - set(out)): E.append(f'{where}: render() returned no {k}')
    for k, v in out.items():
        if not isinstance(k, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*\.svg', k): E.append(f'{where}: {k!r} is not a badge file name like claims.svg'); continue
        if not isinstance(v, str): E.append(f'{where}: {k} must be SVG text'); continue
        try:
            el = ET.fromstring(v.encode('utf-8'))
        except ET.ParseError as x:
            E.append(f'{where}: {k} is not well-formed SVG ({x})'); continue
        if el.tag not in ('svg', '{http://www.w3.org/2000/svg}svg'): E.append(f'{where}: {k} does not start with an <svg> element')
        if SVG_UNSAFE.search(v): E.append(f'{where}: {k} holds a script, an event handler or a link to another file')
    return out


def excluded_in(obj):  # excluded photo stems named anywhere in a (nested) value
    return sorted({m.upper() for m in EXCLUDED_RE.findall(json.dumps(obj, ensure_ascii=False, default=str))})


def scan_shared(root):  # every shared output file that names an excluded photo
    hits = []
    for d in SHARED_OUT:
        for p in sorted((root / d).rglob('*')) if (root / d).is_dir() else []:
            if p.is_file() and p.suffix.lower() in TEXT_EXT and EXCLUDED_RE.search(p.read_text(encoding='utf-8', errors='replace')):
                hits.append(p.relative_to(root).as_posix())
    return hits


# ---------------------------------------------------------------- load + validate (nothing is written here)
def load(root):
    E, W = [], []
    C = root / '20-claims'
    topics_doc = read_yaml(C / 'topics.yaml', E)
    sessions_doc = read_yaml(C / 'sessions.yaml', E)
    sources = read_yaml(C / 'sources.yaml', E)
    files = []
    for f in C.glob('day*.yaml'):
        m = re.fullmatch(r'day(\d+)\.yaml', f.name)
        if not m: E.append(f'20-claims/{f.name}: claim files must be named dayN.yaml'); continue
        files.append((int(m[1]), f, read_yaml(f, E)))
    files.sort(key=lambda x: x[0])
    if E: return {}, E, W  # a file that cannot be read: report that alone, not every claim that depends on it
    kb = validate(root, topics_doc, sessions_doc, sources, files, E, W)
    kb['edition'] = edition_settings(root, E)  # full (main) or community: _system/edition.yaml
    k, ns = kits()
    k.validate(root, kb, E, W, ns)  # 25-kits/: ids, levels, statuses, cited claims (existing, public), docs keys, snippets
    if not E: load_entities(root, kb, E, W)  # 20-claims/entities.yaml: needs valid claims, topics, sources and the glossary
    tpl = root / '_system' / 'templates'
    for n in ('mindmap.template.html', 'AGENTS.md'):
        if not (tpl / n).exists(): E.append(f'_system/templates/{n}: file missing')
    if (tpl / 'AGENTS.md').exists(): edition_marks_ok((tpl / 'AGENTS.md').read_text(encoding='utf-8'), '_system/templates/AGENTS.md', E)
    if (tpl / 'mindmap.template.html').exists() and (tpl / 'mindmap.template.html').read_text(encoding='utf-8').count('/*DATA*/null') != 1:
        E.append('_system/templates/mindmap.template.html: must contain /*DATA*/null exactly once')
    if (tpl / 'mindmap.template.html').exists() and (tpl / 'mindmap.template.html').read_text(encoding='utf-8').count('/*STYLE*/') != 1:
        E.append('_system/templates/mindmap.template.html: must contain /*STYLE*/ exactly once (the default style from _system/theme.yaml)')
    kb['style'] = default_style(root, E)
    m = re.search(r'^## (v\d+\.\d+\.\d+)\b', (root / 'CHANGELOG.md').read_text(encoding='utf-8'), re.M) if (root / 'CHANGELOG.md').exists() else None
    if not m: W.append('CHANGELOG.md has no "## vX.Y.Z" heading; the version is shown as "unversioned"')
    kb['version'] = m[1] if m else 'unversioned'
    if not E:  # the badges need valid data and kits
        kb['badge_stats'] = badge_stats(kb)
        kb['badges'] = make_badges(kb, E)
    return kb, E, W


def validate(root, topics_doc, sessions_doc, sources, files, E, W):
    # sources
    if not isinstance(sources, dict):
        if sources is not None: E.append('sources.yaml: must be a mapping of key: {title, url, publisher, checked}')
        sources = {}
    for k, s in sources.items():
        if not isinstance(s, dict): E.append(f'source {k}: must be a mapping'); continue
        for x in s:
            if x not in SOURCE_KEYS: E.append(f'source {k}: unknown key "{x}"{hint(x, SOURCE_KEYS)}')
        for x in ('title', 'url', 'publisher', 'checked'):
            if not s.get(x): E.append(f'source {k}: missing {x}')
            elif x != 'checked' and not isinstance(s[x], str): E.append(f'source {k}: {x} must be a string')
        if isinstance(s.get('url'), str) and s['url'] and not re.fullmatch(r'https?://[^\s<>"]+', s['url']):
            E.append(f'source {k}: url must start with http:// or https:// (found {s["url"]!r:.60})')
        if s.get('checked') and not isdate(s['checked']): E.append(f'source {k}: checked must be a real date written YYYY-MM-DD (found {s["checked"]!r})')
        if s.get('kind', 'google') not in ('google', 'press'): E.append(f'source {k}: kind must be google or press')
        for x in excluded_in(s): E.append(f'source {k}: names {x}, which must never appear in a shared output')
    kind = {k: (s.get('kind') or 'google') if isinstance(s, dict) else 'google' for k, s in sources.items()}

    # sessions
    sessions, days = {}, []
    if not isinstance(sessions_doc, dict):
        if sessions_doc is not None: E.append('sessions.yaml: must be a mapping with event and days')
        sessions_doc = {}
    ev = sessions_doc.get('event')
    if not isinstance(ev, dict) or any(not ev.get(k) for k in ('name', 'city', 'dates')): E.append('sessions.yaml: event needs name, city and dates')
    if not isinstance(sessions_doc.get('days'), list): E.append('sessions.yaml: days must be a list')
    for d in sessions_doc.get('days') or []:
        n = d.get('day') if isinstance(d, dict) else None
        if not isinstance(n, int) or isinstance(n, bool): E.append(f'sessions.yaml: every entry of days needs day: <number> (found {d!r:.60})'); continue
        if any(x['day'] == n for x in days): E.append(f'sessions.yaml: day {n} is listed twice')
        for x in d:
            if x not in ('day', 'date', 'theme', 'sessions'): E.append(f'sessions.yaml day {n}: unknown key "{x}"')
        if not isdate(d.get('date')): E.append(f'sessions.yaml day {n}: date must be a real date written YYYY-MM-DD (found {d.get("date")!r})')
        if not isinstance(d.get('theme'), str) or not d['theme'].strip(): E.append(f'sessions.yaml day {n}: theme missing')
        ss = d.get('sessions')
        if not isinstance(ss, list): E.append(f'sessions.yaml day {n}: sessions must be a list (write "sessions: []" for a day with none)'); ss = []
        days.append({'day': n, 'date': str(d.get('date')), 'theme': str(d.get('theme') or ''), 'sessions': []})
        for s in ss:
            if not isinstance(s, dict): E.append(f'sessions.yaml day {n}: every session must be a mapping'); continue
            sid = s.get('id')
            tag = f'session {sid} (day {n})'
            m = re.fullmatch(r'D(\d+)-S(\d{2})', sid) if isinstance(sid, str) else None
            if not m: E.append(f'{tag}: id must look like D{n}-S01')
            elif int(m[1]) != n: E.append(f'{tag}: the id says day {m[1]} but the session is listed under day {n}')
            if isinstance(sid, str) and sid in sessions: E.append(f'{tag}: duplicate session id (already used on day {sessions[sid]["day"]})')
            for x in s:
                if x not in SESSION_KEYS: E.append(f'{tag}: unknown key "{x}"{hint(x, SESSION_KEYS)}')
            for x in ('id', 'time', 'title', 'speaker', 'coverage'):
                if x not in s: E.append(f'{tag}: missing key "{x}"' + (' (use "" when not known)' if x in ('time', 'speaker') else ''))
            t = s.get('time', '')
            if isinstance(t, int) and not isinstance(t, bool):
                E.append(f'{tag}: time must be quoted, e.g. time: "{t // 60:02d}:{t % 60:02d}" (unquoted, YAML reads it as the number {t})')
            elif not isinstance(t, str) or not re.fullmatch(r'(([01]\d|2[0-3]):[0-5]\d)?', t):
                E.append(f'{tag}: time must be "HH:MM" in quotes, or ""')
            if not isinstance(s.get('title'), str) or not s.get('title', '').strip(): E.append(f'{tag}: title missing')
            sp = s.get('speaker', '')
            if not (isinstance(sp, str) or (isinstance(sp, list) and sp and all(isinstance(x, str) and x.strip() for x in sp))):
                E.append(f'{tag}: speaker must be a string or a list of names')
            if 'coverage' in s:
                cv = as_list(s['coverage'])
                if not cv or any(x not in COVERAGE for x in cv): E.append(f'{tag}: coverage must be one of {", ".join(COVERAGE)}, or a list of them')
            if s.get('kind', 'talk') not in KINDS: E.append(f'{tag}: kind must be one of {", ".join(KINDS)}')
            for x in ('note', 'role'):
                if x in s and not isinstance(s[x], str): E.append(f'{tag}: {x} must be a string')
            for x in excluded_in(s): E.append(f'{tag}: names {x}, which must never appear in a shared output')
            if isinstance(sid, str) and sid not in sessions:
                rec = dict(s, day=n, date=str(d.get('date')), theme=str(d.get('theme') or ''))
                rec['time'] = t if isinstance(t, str) else ''
                rec['speaker'] = sp if isinstance(sp, (str, list)) else ''
                rec['coverage'] = [x for x in as_list(s.get('coverage')) if isinstance(x, str)]
                sessions[sid] = rec
                days[-1]['sessions'].append(rec)

    # topics
    areas, topics, ids = [], {}, Counter()
    if not isinstance(topics_doc, dict) or not isinstance(topics_doc.get('areas'), list): E.append('topics.yaml: needs areas: [...]')
    else: areas = topics_doc['areas']
    good_areas = []
    for a in areas:
        if not isinstance(a, dict): E.append('topics.yaml: every area must be a mapping'); continue
        aid = a.get('id')
        for x in a:
            if x not in AREA_KEYS: E.append(f'area {aid}: unknown key "{x}"{hint(x, AREA_KEYS)}')
        for x in ('id', 'title', 'blurb'):
            if not isinstance(a.get(x), str) or not a[x].strip(): E.append(f'area {aid}: {x} missing')
        if not isinstance(aid, str) or not KEBAB.fullmatch(aid): E.append(f'area {aid}: id must be lowercase kebab-case, e.g. crawling-basics')
        for x in excluded_in({k: v for k, v in a.items() if k != 'topics'}): E.append(f'area {aid}: names {x}, which must never appear in a shared output')
        ids[str(aid)] += 1
        if not isinstance(a.get('topics'), list): E.append(f'area {aid}: topics must be a list'); continue
        good = []
        for t in a['topics']:
            if not isinstance(t, dict): E.append(f'area {aid}: every topic must be a mapping'); continue
            tid = t.get('id')
            for x in t:
                if x not in TOPIC_KEYS: E.append(f'topic {tid}: unknown key "{x}"{hint(x, TOPIC_KEYS)}')
            for x in ('id', 'title', 'summary'):
                if not isinstance(t.get(x), str) or not t[x].strip(): E.append(f'topic {tid}: {x} missing')
            if not isinstance(tid, str) or not KEBAB.fullmatch(tid): E.append(f'topic {tid}: id must be lowercase kebab-case, e.g. crawl-budget')
            for x in ('do', 'related', 'cites'):
                if x in t and not isinstance(t[x], list): E.append(f'topic {tid}: {x} must be a list')
                elif any(not isinstance(y, str) for y in as_list(t.get(x))): E.append(f'topic {tid}: every {x} item must be a string')
                else: dups(as_list(t.get(x)), f'topic {tid}: {x}', E)
            for x in excluded_in(t): E.append(f'topic {tid}: names {x}, which must never appear in a shared output')
            ids[str(tid)] += 1
            if isinstance(tid, str) and tid not in topics: topics[tid] = t; good.append(t)
        good_areas.append(dict(a, topics=good))
    for k, n in ids.items():
        if n > 1: E.append(f'topics.yaml: id "{k}" is used {n} times (area and topic ids must be unique across the file)')
    for t in topics.values():
        for r in as_list(t.get('related')):
            if not isinstance(r, str): continue
            if r not in topics: E.append(f'topic {t["id"]}: unknown related topic {r}')
            elif r == t['id']: E.append(f'topic {t["id"]}: related to itself')

    # claims
    claims, by_id = [], {}
    for n, f, data in files:
        if data is None: continue
        if not isinstance(data, list): E.append(f'20-claims/{f.name}: must be a YAML list of claims (each claim starting with "- {{id: ...}}")'); continue
        for c in data:
            if not isinstance(c, dict): E.append(f'20-claims/{f.name}: every entry must be a mapping, found {c!r:.60}'); continue
            claims.append((n, f.name, c))
    for n, fname, c in claims:
        cid = c.get('id')
        cid = cid if isinstance(cid, str) else f'{fname}:?'
        for x in c:
            if x not in CLAIM_KEYS: E.append(f'{cid}: unknown key "{x}"{hint(x, CLAIM_KEYS)}')
        for x in ('id', 's', 'label', 'ver', 'topics', 'text'):
            if x not in c: E.append(f'{cid}: missing key "{x}"')
        m = re.fullmatch(r'D(\d+)-C(\d{3})', cid)
        if not m: E.append(f'{cid}: bad id format (D<day>-C<3 digits>, e.g. D{n}-C001)')
        elif int(m[1]) != n: E.append(f'{cid}: the id says day {m[1]} but the claim is in {fname}')
        if cid in by_id: E.append(f'{cid}: duplicate id')
        by_id.setdefault(cid, c)
        ses = sessions.get(c.get('s')) if isinstance(c.get('s'), str) else None
        if not ses: E.append(f'{cid}: unknown session {c.get("s")}')
        elif m and int(m[1]) != ses['day']: E.append(f'{cid}: the id says day {m[1]} but session {c["s"]} is on day {ses["day"]}')
        label, ver = c.get('label'), c.get('ver')
        if not isinstance(label, str): E.append(f'{cid}: label must be one word ({" | ".join(LABELS)}), found {label!r:.60}'); label = None
        elif label not in LABELS: E.append(f'{cid}: bad label {label} (use {" | ".join(LABELS)})')
        if not isinstance(ver, str): E.append(f'{cid}: ver must be one word ({" | ".join(VER)}), found {ver!r:.60}'); ver = None
        elif ver not in VER: E.append(f'{cid}: bad ver {ver} (use {" | ".join(VER)})')
        src = c.get('src', [])
        if not isinstance(src, list): E.append(f'{cid}: src must be a list, e.g. [robots-spec]'); src = []
        elif any(not isinstance(k, str) for k in src): E.append(f'{cid}: every src item must be a source key (a string), e.g. [robots-spec]'); src = []
        dups(src, f'{cid}: src', E)
        for k in src:
            if k not in sources: E.append(f'{cid}: unknown source {k}')
        tps = c.get('topics')
        if 'topics' in c and not isinstance(tps, list): E.append(f'{cid}: topics must be a list, e.g. [robots-txt]')
        elif 'topics' in c and not tps: E.append(f'{cid}: no topics')
        elif 'topics' in c and any(not isinstance(t, str) for t in tps): E.append(f'{cid}: every topics item must be a topic id (a string), e.g. [robots-txt]')
        else:
            dups(as_list(tps), f'{cid}: topics', E)
            for t in as_list(tps):
                if t not in topics: E.append(f'{cid}: unknown topic {t}')
        txt = c.get('text')
        if 'text' in c and (not isinstance(txt, str) or not txt.strip()): E.append(f'{cid}: text must be a non-empty string')
        q = c.get('quote')
        if q is not None and not isinstance(q, str): E.append(f'{cid}: quote must be a string')
        elif words(q) > 25: E.append(f'{cid}: quote has {words(q)} words; at most 25 (paraphrase the rest in text)')
        for x in ('text', 'quote'):
            if isinstance(c.get(x), str) and '\n' in c[x].strip(): W.append(f'{cid}: {x} spans several lines; outputs join it into one')
        for x in ('private', 'quote_checked'):
            if x in c and not isinstance(c[x], bool): E.append(f'{cid}: {x} must be true or false (YAML boolean), found {c[x]!r}')
        if c.get('quote_checked') and not q: W.append(f'{cid}: quote_checked is set but there is no quote')
        kinds = [kind[k] for k in src if k in kind]
        if ver in ('confirmed', 'consistent') and 'google' not in kinds: E.append(f'{cid}: ver {ver} needs at least one Google source in src (kind: google)')
        if label == 'docs':
            if ver != 'source': E.append(f'{cid}: docs claims use ver: source')
            if not src: E.append(f'{cid}: docs claim without src')
            if any(k != 'google' for k in kinds): E.append(f'{cid}: docs claims cite only Google sources; label a third-party report press')
        if label == 'press':
            if ver != 'source': E.append(f'{cid}: press claims use ver: source')
            if 'press' not in kinds: E.append(f'{cid}: press claims cite at least one source with kind: press')
        if ver == 'source' and label in LABELS and label not in ('docs', 'press'): E.append(f'{cid}: ver source is only for docs and press claims')
        if label == 'analysis' and ver in VER and ver != 'n/a': E.append(f'{cid}: analysis claims use ver: n/a')
        who = c.get('who')
        if 'who' in c:  # in D<day>-S00 (session not recorded) who may be any name: there is no speaker list to check against
            if label not in EVENT: E.append(f'{cid}: who is only for slide and stage claims')
            elif not isinstance(who, str) or not who.strip(): E.append(f'{cid}: who must be a name, audience or unknown')
            elif ses and not ses['id'].endswith('-S00') and who not in speakers(ses) + ['audience', 'unknown']:
                E.append(f'{cid}: who "{who}" is not a speaker of {c["s"]} ({", ".join(speakers(ses)) or "none listed"}); use one of them, audience or unknown')
        elif label == 'stage' and ses and len(speakers(ses)) > 1:
            E.append(f'{cid}: stage claim in a session with several speakers needs who: <name>, audience or unknown')
        e = c.get('ev')
        if e is not None and not (isinstance(e, str) or (isinstance(e, list) and all(isinstance(x, str) for x in e))):
            E.append(f'{cid}: ev must be a string or a list of strings')
        elif label in EVENT and not ev_list(c): W.append(f'{cid}: {label} claim has no evidence (ev)')
        else: check_ev(root, cid, n, ev_list(c), W)
        for x in ev_list(c) if isinstance(e, (str, list)) else []:
            if EXCLUDED_RE.search(x): E.append(f'{cid}: evidence {x} is an excluded photo (another attendee\'s badge): never cite it')
        if c.get('private') is not True:
            for x in excluded_in({k: v for k, v in c.items() if k != 'ev'}): E.append(f'{cid}: names {x}, which must never appear in a shared output')

    public = {cid for cid, c in by_id.items() if c.get('private') is not True}
    for cid, c in by_id.items():
        rel = c.get('rel')
        if rel is None: continue
        if not isinstance(rel, list): E.append(f'{cid}: rel must be a list, e.g. [{{type: repeats, to: D1-C111}}]'); continue
        for r in rel:
            if not isinstance(r, dict) or set(r) != {'to', 'type'}: E.append(f'{cid}: every rel entry needs exactly type and to, e.g. {{type: repeats, to: D1-C111}}'); continue
            if not isinstance(r['type'], str) or not isinstance(r['to'], str): E.append(f'{cid}: rel type and to must be single words, e.g. {{type: repeats, to: D1-C111}}'); continue
            if r['type'] not in REL: E.append(f'{cid}: rel type {r["type"]} must be one of {", ".join(REL)}')
            if r['to'] == cid: E.append(f'{cid}: rel points to itself')
            elif r['to'] not in by_id: E.append(f'{cid}: rel points to {r["to"]}, which does not exist')
            elif r['to'] not in public: E.append(f'{cid}: rel points to {r["to"]}, which is private')
        dups([f'{{type: {r["type"]}, to: {r["to"]}}}' for r in rel if isinstance(r, dict) and set(r) == {'to', 'type'}], f'{cid}: rel', E)

    def refs(txt, where, pub=True):
        for x in cited_ids(txt, where, E):
            if x not in by_id: E.append(f'{where}: mentions {x}, which does not exist')
            elif pub and x not in public: E.append(f'{where}: mentions {x}, which is private')
    for cid, c in by_id.items():
        for x in ('text', 'quote'):
            if isinstance(c.get(x), str): refs(c[x], f'{cid} {x}', cid in public)
    for t in topics.values():
        refs(t.get('summary', ''), f'topic {t["id"]} summary')
        for i, d in enumerate(as_list(t.get('do'))): refs(d, f'topic {t["id"]} do item {i + 1}')
        for x in as_list(t.get('cites')):
            if not isinstance(x, str): continue  # reported above
            if not re.fullmatch(r'D\d+-C\d{3}', x): E.append(f'topic {t["id"]}: cites must list claim ids, found {x!r}')
            elif x not in by_id: E.append(f'topic {t["id"]}: cites {x}, which does not exist')
            elif x not in public: E.append(f'topic {t["id"]}: cites {x}, which is private')
    ev_path = root / '_system' / 'eval' / 'questions.yaml'
    if ev_path.exists():
        n_err, qs = len(E), read_yaml(ev_path, E)
        if len(E) > n_err: pass
        elif not isinstance(qs, list): E.append('_system/eval/questions.yaml: must be a list of questions')
        else:
            seen = set()
            for q in qs:
                qid = q.get('id') if isinstance(q, dict) else None
                if not isinstance(qid, str) or not re.fullmatch(r'q\d{2,}', qid) or qid in seen: E.append(f'eval question {qid}: needs a unique id like q01'); continue
                seen.add(qid)
                if not isinstance(q.get('claims', []), list): E.append(f'eval {qid}: claims must be a list')
                refs(yaml.safe_dump(q, allow_unicode=True), f'eval {qid}')
    return {'sessions': sessions, 'days': days, 'event': ev if isinstance(ev, dict) else {}, 'areas': good_areas, 'topics': topics,
            'sources': sources, 'claims': [c for _, _, c in claims]}


RAW = {}


def check_ev(root, cid, n, evs, W):
    for e in evs:
        m = next((f.fullmatch(e) for f in EV_FORMS if f.fullmatch(e)), None)
        stem = m[1] if m and m.lastindex else (e if PHOTO.fullmatch(e) and not m else None)
        if not m and not stem: W.append(f'{cid}: unrecognised evidence "{e}" (photo stem, notes, agenda, T:<stem>:<paragraph>, T hh:mm:ss, video:<stem>)'); continue
        if e.startswith('T:'):
            d = root / '10-sources' / f'day{n}'
            if d.is_dir() and not (d / 'clean' / f'{stem}.md').exists(): W.append(f'{cid}: evidence {e}: no 10-sources/day{n}/clean/{stem}.md')
        elif stem:
            if n not in RAW:
                d = root / '00-raw' / f'day{n}'
                RAW[n] = {p.stem.lower() for p in d.rglob('*') if p.is_file()} if d.is_dir() else None
            if RAW[n] is not None and stem.lower() not in RAW[n]: W.append(f'{cid}: evidence {e}: no file named {stem}.* under 00-raw/day{n}/')


# ---------------------------------------------------------------- things (entities; knowledge graph phase 1): 20-claims/entities.yaml
# A thing is matched to the public claims by its name and aliases, never written on a claim: the claims and their schema stay as
# they are. The rules (B2.2 and B2.3 of the plan, and _system/schema/claim.md "Things"): a plain alias matches case-insensitively
# after fold() on word boundaries; {s, in: [topic ids]} only in claims filed under one of those topics; {s, exact: true}
# case-sensitively. The name is matched as a plain alias unless an alias spells it (after fold), which then sets its mode.
# Boundaries (?<![\w-]) and (?![\w-]): "noindex" is not found in "noindexing", "Googlebot" not in "Googlebot-Image". A match that
# lies inside a longer match of another alias does not count ("Rich Results Test" is not a mention of rich results).
ENTITY_KINDS = {  # kind: (label, meaning), in the order the outputs list them
    'product': ('Product', 'A Google product or service: Search Console, Merchant Center, Discover.'),
    'feature': ('Feature', 'A feature of Google Search: AI Mode, AI Overviews, rich results.'),
    'crawler': ('Crawler', 'A crawler or fetcher, named by its user agent: Googlebot, Google-Extended.'),
    'report': ('Report', 'A report or view of a Google tool: Crawl stats, Page indexing, URL Inspection.'),
    'directive': ('Directive', 'A rule a site writes for crawlers or indexing: noindex, rel=canonical, hreflang, Disallow.'),
    'status-code': ('Status code', 'An HTTP status code or class: 404, 429, 5xx.'),
    'standard': ('Standard', 'A standard, protocol or format: RFC 9309, HTTP/2, schema.org, JSON-LD.'),
    'metric': ('Metric', 'Something measured or budgeted: crawl budget, Core Web Vitals, PageRank.'),
    'concept': ('Concept', 'An idea or process: canonicalisation, soft 404, query fan-out, E-E-A-T.'),
    'update': ('Update', 'A named change to Search: core updates, spam updates, the helpful content update.'),
    'tool': ('Tool', 'A testing or research tool: Rich Results Test, Lighthouse, Trends Explore.')}
ENT_REL = {  # type: (reverse, structural, meaning). Structural: no claims needed. Factual: claims that mention both ends, validated.
    'is-a': ('has-kind', True, 'The first thing is a kind of the second (404 is-a client error).'),
    'part-of': ('has-part', True, 'The first thing is part of the second (Crawl stats part-of Search Console).'),
    'uses': ('used-by', False, 'The first thing uses the second (AI Mode uses query fan-out).'),
    'affects': ('affected-by', False, 'The first thing affects the second (5xx affects the crawl rate).'),
    'measured-by': ('measures', False, 'The first thing is measured by the second (crawl budget measured-by Crawl stats).'),
    'applies-to': ('subject-of', False, 'The first thing applies to the second (hreflang applies-to multilingual sites).')}
ENTITY_KEYS = ('id', 'kind', 'name', 'aliases', 'summary', 'glossary', 'docs', 'topics', 'rel', 'pin', 'unpin')
ALIAS_KEYS = ('s', 'in', 'exact')
STOP_N = 200  # the stop list: the most frequent words of the public claims
DRIFT = 20    # an alias that newly matches more claims than this is printed after the build
SAMPLE_N = 100  # the precision sample of 50-maps/entity-index.md
_FOLD_CH = {}


def fold_map(s):
    """fold(s), and for each of its characters the index of the character of s it comes from. fold() works character by character
    (lower case, NFD, marks dropped, SPELL), so folding each character gives the same string as folding the whole."""
    out, idx = [], []
    for i, ch in enumerate(s):
        f = _FOLD_CH.get(ch)
        if f is None: f = _FOLD_CH[ch] = fold(ch)
        out.append(f)
        idx += [i] * len(f)
    return ''.join(out), idx


def stop_words(public):
    """The STOP_N most frequent folded words ([^\\W_]+ runs) of the public claims' text and quote, most frequent first, ties by spelling."""
    n = Counter(w for c in public for x in (c.get('text'), c.get('quote')) if isinstance(x, str) for w in re.findall(r'[^\W_]+', fold(nt(x))))
    return [w for w, _ in sorted(n.items(), key=lambda x: (-x[1], x[0]))[:STOP_N]]


def ent_rule(eid, i, s, exact, scope, is_name=False):
    f = s if exact else fold(s)
    return {'ent': eid, 'i': i, 's': s, 'exact': exact, 'in': scope, 'name': is_name, 'needle': f,
            're': re.compile(r'(?<![\w-])' + re.escape(f) + r'(?![\w-])')}


def rule_mode(r):  # how an alias is matched, in words: plain, exact, in <topics>, exact, in <topics>
    return ', '.join(p for p in ('exact' if r['exact'] else '', 'in ' + ', '.join(sorted(r['in'])) if r['in'] else '') if p) or 'plain'


def ent_match(rules, raw, topics):
    """[(start, end, entity id, rule index)] of the aliases found in raw (a claim's text or quote, or a kit item's own text, as
    exported: one line). Scoped rules run only when topics meets their `in`; a span strictly inside a longer span is dropped."""
    if not raw: return []
    folded, idx = fold_map(raw)
    spans = []
    for r in rules:
        if r['in'] is not None and not (r['in'] & topics): continue
        hay = raw if r['exact'] else folded
        if r['needle'] not in hay: continue
        for m in r['re'].finditer(hay):
            a, b = m.span()
            if not r['exact']: a, b = idx[a], idx[b - 1] + 1
            spans.append((a, b, r['ent'], r['i']))
    return [s for s in spans if not any(t[0] <= s[0] and s[1] <= t[1] and t[1] - t[0] > s[1] - s[0] for t in spans)]


def load_entities(root, kb, E, W):
    """Check 20-claims/entities.yaml, match its things against the public claims and check what needs the matches (every claim of a
    factual rel mentions both ends; pins and unpins). Sets kb['entities'] (valid things, by id), kb['ent_rules'], kb['mentions']
    ({claim id: {entity id: {via, field}}}, in claim order) and kb['alias_hits']. Writes nothing. No file: no things yet."""
    public = [c for c in kb['claims'] if c.get('private') is not True]
    kb['stop_words'] = stop_words(public)
    kb.update(entities=[], ent_rules=[], mentions={}, alias_hits={})
    p, where = root / '20-claims' / 'entities.yaml', '20-claims/entities.yaml'
    if not p.exists(): return
    n0 = len(E)
    doc = read_yaml(p, E)
    if len(E) > n0: return
    if not isinstance(doc, dict) or set(doc) != {'entities'} or not isinstance(doc['entities'], (list, type(None))):
        E.append(f'{where}: must be a mapping with the one key entities, holding a list of things'); return
    topics, areas = kb['topics'], {a['id'] for a in kb['areas']}
    by_id = {c['id']: c for c in kb['claims']}
    pub = {c['id'] for c in public}
    sources = kb['sources']
    K, _ = kits()
    people, _ = K.people(kb['sessions'])
    people |= {c['who'] for c in kb['claims'] if K.person(c.get('who'))}
    terms = {nt(t['term']): t['term'] for t in kb['kits']['content'].get('glossary', []) if isinstance(t.get('term'), str)}
    ids, good = Counter(), []
    declared = {x.get('id') for x in doc['entities'] or [] if isinstance(x, dict) and isinstance(x.get('id'), str)}
    for x in doc['entities'] or []:
        eid = x.get('id') if isinstance(x, dict) else None
        w = f'entity {eid}'
        if not isinstance(x, dict): E.append(f'{where}: every entry must be a mapping with id, kind, name and summary, found {x!r:.60}'); continue
        n1 = len(E)
        for k in x:
            if k not in ENTITY_KEYS: E.append(f'{w}: unknown key "{k}"{hint(k, ENTITY_KEYS)}')
        for k in ('id', 'kind', 'name', 'summary'):
            if not isinstance(x.get(k), str) or not x[k].strip(): E.append(f'{w}: {k} must be a non-empty string')
        if isinstance(eid, str):
            ids[eid] += 1
            if not KEBAB.fullmatch(eid): E.append(f'{w}: id must be lowercase kebab-case, e.g. search-console')
            elif eid in topics or eid in areas:
                E.append(f'{w}: id {eid} is already a{" topic" if eid in topics else "n area"} id; ids are unique across things, topics and areas '
                         f'(link the {"topic with topics: [" + eid + "]" if eid in topics else "area"} and give the thing its own id)')
        if isinstance(x.get('kind'), str) and x['kind'] not in ENTITY_KINDS: E.append(f'{w}: kind {x["kind"]!r} must be one of {", ".join(ENTITY_KINDS)}{hint(x["kind"], ENTITY_KINDS)}')
        if isinstance(x.get('summary'), str) and '\n' in x['summary'].strip(): W.append(f'{w}: summary spans several lines; outputs join it into one')

        def lst(k, item=str, what='a string'):
            v = x.get(k)
            if v is None: return []
            if not isinstance(v, list) or any(not isinstance(y, item) for y in v): E.append(f'{w}: {k} must be a list, each item {what}'); return []
            return v
        aliases = []
        for a in lst('aliases', (str, dict), 'a string or {s, in, exact}'):
            if isinstance(a, str):
                if not a.strip(): E.append(f'{w}: an alias is empty'); continue
                aliases.append({'s': nt(a), 'exact': False, 'in': None}); continue
            bad = [k for k in a if k not in ALIAS_KEYS]
            if bad: E.append(f'{w}: alias {a!r:.60}: unknown key "{bad[0]}" (an alias is a string, {{s, in: [topic ids]}} or {{s, exact: true}})'); continue
            if not isinstance(a.get('s'), str) or not a['s'].strip(): E.append(f'{w}: alias {a!r:.60}: s must be a non-empty string'); continue
            if 'exact' in a and not isinstance(a['exact'], bool): E.append(f'{w}: alias "{a["s"]}": exact must be true or false'); continue
            scope = None
            if 'in' in a:
                if not isinstance(a['in'], list) or not a['in'] or any(not isinstance(t, str) for t in a['in']):
                    E.append(f'{w}: alias "{a["s"]}": in must be a non-empty list of topic ids'); continue
                unknown = [t for t in a['in'] if t not in topics]
                if unknown: E.append(f'{w}: alias "{a["s"]}": unknown topic {unknown[0]}{hint(unknown[0], list(topics))}'); continue
                dups(a['in'], f'{w}: alias "{a["s"]}" in', E)
                scope = frozenset(a['in'])
            aliases.append({'s': nt(a['s']), 'exact': a.get('exact') is True, 'in': scope})
        gl = x.get('glossary')
        if gl is not None and (not isinstance(gl, str) or nt(gl) not in terms):
            E.append(f'{w}: glossary {gl!r} is not a term of 25-kits/content.yaml' + (hint(nt(gl), list(terms)) if isinstance(gl, str) else '') + ' (write the term exactly)')
        docs = lst('docs', what='a key of sources.yaml')
        dups(docs, f'{w}: docs', E)
        for k in docs:
            if k not in sources: E.append(f'{w}: unknown docs key {k}{hint(k, list(sources))} (add it to 20-claims/sources.yaml first)')
            elif (sources[k].get('kind') or 'google') != 'google': E.append(f'{w}: docs key {k} is a press source; docs lists Google pages only')
        home = lst('topics', what='a topic id')
        dups(home, f'{w}: topics', E)
        for t in home:
            if t not in topics: E.append(f'{w}: unknown topic {t}{hint(t, list(topics))}')
        rels = []
        for r in lst('rel', dict, '{type, to} or {type, to, claims}'):
            bad = [k for k in r if k not in ('type', 'to', 'claims')]
            t, to = r.get('type'), r.get('to')
            if bad or not isinstance(t, str) or not isinstance(to, str):
                E.append(f'{w}: every rel entry is {{type, to}} or {{type, to, claims: [claim ids]}}, found {r!r:.80}'); continue
            if t == 'documented-in': E.append(f'{w}: rel documented-in: list the Google pages under docs instead'); continue
            if t not in ENT_REL: E.append(f'{w}: rel type {t} must be one of {", ".join(ENT_REL)}{hint(t, ENT_REL)}'); continue
            if to == eid: E.append(f'{w}: rel {t} points to itself'); continue
            if to not in declared:
                E.append(f'{w}: rel {t} points to {to}, which is not a thing of {where}' + (' (it is a topic: list it under topics)' if to in topics else hint(to, sorted(declared)))); continue
            cl = r.get('claims')
            if cl is not None and (not isinstance(cl, list) or any(not isinstance(c, str) for c in cl)):
                E.append(f'{w}: rel {t} {to}: claims must be a list of claim ids'); continue
            cl = cl or []
            if not ENT_REL[t][1] and not cl:
                E.append(f'{w}: rel {t} {to} is a factual relation: cite the public claims that say it, claims: [D1-C001, ...] (each must mention both things)'); continue
            dups(cl, f'{w}: rel {t} {to} claims', E)
            for c in cl:
                if c not in by_id: E.append(f'{w}: rel {t} {to} cites {c}, which does not exist')
                elif c not in pub: E.append(f'{w}: rel {t} {to} cites {c}, which is private')
            rels.append({'type': t, 'to': to, 'claims': list(dict.fromkeys(cl))})
        dups([f'{r["type"]} {r["to"]}' for r in rels], f'{w}: rel', E)
        pins = {}
        for k in ('pin', 'unpin'):
            pins[k] = lst(k, what='a claim id')
            dups(pins[k], f'{w}: {k}', E)
            for c in pins[k]:
                if c not in by_id: E.append(f'{w}: {k} lists {c}, which does not exist')
                elif c not in pub: E.append(f'{w}: {k} lists {c}, which is private (only public claims are matched)')
        for c in sorted(set(pins['pin']) & set(pins['unpin'])): E.append(f'{w}: {c} is both pinned and unpinned; keep one')
        for y in excluded_in(x): E.append(f'{w}: names {y}, which must never appear in a shared output')
        blob = ' '.join([str(x.get('name') or ''), str(x.get('summary') or '')] + [a['s'] for a in aliases])
        for n in sorted(people):
            if re.search(r'(?<!\w)' + re.escape(n) + r'(?!\w)', blob):
                E.append(f'{w}: names {n}; things are never people (use the speaker filter for who said what), so leave the name out')
        if isinstance(x.get('summary'), str):
            for c in cited_ids(x['summary'], f'{w} summary', E):
                if c not in by_id: E.append(f'{w} summary: mentions {c}, which does not exist')
                elif c not in pub: E.append(f'{w} summary: mentions {c}, which is private')
        if len(E) == n1:
            good.append({'id': eid, 'kind': x['kind'], 'name': nt(x['name']), 'summary': nt(x['summary']), 'aliases': aliases,
                         'glossary': node_slug(terms[nt(gl)]) if gl is not None else None, 'docs': docs, 'topics': home, 'rel': rels,
                         'pin': pins['pin'], 'unpin': pins['unpin']})
    for k, n in ids.items():
        if n > 1: E.append(f'{where}: id {k} is used {n} times')
    good.sort(key=lambda x: x['id'])

    # the alias rules: the name (unless an alias spells it), then the aliases as written; one owner per folded spelling
    stop, owner, rules = set(kb['stop_words']), {}, []
    for x in good:
        w = f"entity {x['id']}"
        fn = fold(x['name'])
        items = ([] if any(fold(a['s']) == fn for a in x['aliases']) else [dict(s=x['name'], exact=False, **{'in': None}, name=True)]) + x['aliases']
        seen = set()
        x['rules'] = []
        for a in items:  # one spelling may be listed in two modes (exact everywhere, plain in some topics), never twice in one
            f = fold(a['s'])
            what = 'the name' if a.get('name') else f'alias "{a["s"]}"'
            if (f, a['exact'], a['in']) in seen: W.append(f'{w}: {what} is listed twice in the same mode (after folding: "{f}"); keep one'); continue
            seen.add((f, a['exact'], a['in']))
            if owner.get(f, x['id']) != x['id']: E.append(f'{w}: {what} is also a name or alias of {owner[f]} (after folding: "{f}"); one thing per spelling')
            owner.setdefault(f, x['id'])
            if len(f) < 3 and not a['exact']: E.append(f'{w}: {what} has fewer than 3 characters: write it as {{s: {a["s"]}, exact: true}}')
            elif f in stop and not a['exact'] and a['in'] is None:
                E.append(f'{w}: {what} is a common word ("{f}" is among the {STOP_N} most frequent words of the claims; see --check --stoplist): '
                         f'use a phrase such as "Performance report", scope it to topics: {{s: {a["s"]}, in: [topic ids]}}, or, when the claims '
                         f'always write it this way, match it exactly: {{s: {a["s"]}, exact: true}}')
            r = ent_rule(x['id'], len(rules), a['s'], a['exact'], a['in'], a.get('name', False) or f == fn)
            rules.append(r)
            x['rules'].append(r)
    kb['entities'], kb['ent_rules'] = good, rules

    # match every public claim (text first, then quote; the leftmost, longest span gives `via`), then unpin and pin
    unpin = {(c, x['id']) for x in good for c in x['unpin']}
    used_unpin, mentions, hits = set(), {}, defaultdict(set)
    for c in public:
        tps = set(c['topics'])
        for field, raw in (('text', nt(c['text'])), ('quote', nt(c.get('quote') or ''))):
            for a, b, eid, i in sorted(ent_match(rules, raw, tps), key=lambda s: (s[0], s[0] - s[1], s[2])):
                if (c['id'], eid) in unpin: used_unpin.add((c['id'], eid)); continue
                hits[i].add(c['id'])
                m = mentions.setdefault(c['id'], {})
                if eid not in m: m[eid] = {'via': raw[a:b], 'field': field}
    for c, eid in sorted(unpin - used_unpin): W.append(f'entity {eid}: unpin {c} changes nothing: no alias of {eid} matches that claim')
    for x in good:
        for c in x['pin']:
            m = mentions.setdefault(c, {})
            if x['id'] in m: W.append(f"entity {x['id']}: pin {c} is not needed: the claim already names it (\"{m[x['id']]['via']}\")")
            else: m[x['id']] = {'via': None, 'field': 'pin'}
    order = {c['id']: i for i, c in enumerate(public)}
    kb['mentions'] = {c: dict(sorted(mentions[c].items())) for c in sorted(mentions, key=order.get) if mentions[c]}
    kb['alias_hits'] = {i: len(hits[i]) for i in range(len(rules))}
    for x in good:
        for r in x['rel']:
            if r['to'] not in {y['id'] for y in good}: continue  # its own errors are reported above
            for c in r['claims']:
                got = set(kb['mentions'].get(c, {}))
                if c in pub and not {x['id'], r['to']} <= got:
                    E.append(f"entity {x['id']}: rel {r['type']} {r['to']} cites {c}, which does not mention both things (it mentions: "
                             f"{', '.join(sorted(got)) or 'none'}); add an alias or a pin, or cite another claim")
    n = Counter(e for m in kb['mentions'].values() for e in m)
    for x in good:
        if not n[x['id']]: W.append(f"entity {x['id']}: no public claim mentions it; add an alias, a scope or a pin, or remove the thing")


def ent_docs(kb):  # the Google pages the things are documented in: shared through entities.json like the developer kit's docs
    return {k for x in kb.get('entities', []) for k in x['docs']}


# ---------------------------------------------------------------- build
def long_paths(root, kb, limit=260):
    """Output files whose full path would reach the Windows path limit: on a machine without long path support the build
    would fail halfway, after deleting part of the outputs, so main() stops before anything is deleted."""
    S, area_of = kb['sessions'], {t['id']: a['id'] for a in kb['areas'] for t in a['topics']}
    fname = {sid: f"{sid}-{slug(s['title'])}.md" for sid, s in S.items()}
    paths = ([root / '40-sessions' / f"day{S[sid]['day']}" / f for sid, f in fname.items()] + [root / '60-outputs' / 'agent-pack' / 'sessions' / f for f in fname.values()]
             + [root / '30-topics' / a / f'{t}.md' for t, a in area_of.items()] + [root / '60-outputs' / 'agent-pack' / 'topics' / f'{t}.md' for t in area_of]
             + [root / '60-outputs' / 'agent-pack' / 'entities' / f"{x['id']}.md" for x in kb.get('entities', [])])
    return sorted({str(p) for p in paths if len(str(p)) >= limit}, key=lambda p: (-len(p), p))


def windows_long_paths_enabled():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\FileSystem') as k:
            return winreg.QueryValueEx(k, 'LongPathsEnabled')[0] == 1
    except (ImportError, OSError):
        return False


def fresh(p):
    for i in range(6):
        try:
            if p.exists(): shutil.rmtree(p)
            p.mkdir(parents=True)
            return
        except PermissionError:
            if i == 5: raise
            time.sleep(0.5)


def write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8', newline='\n')


def js_json(o):  # safe to inline inside <script>
    s = json.dumps(o, ensure_ascii=False)
    for a, b in (('<', '\\u003c'), ('>', '\\u003e'), ('&', '\\u0026'), ('\u2028', '\\u2028'), ('\u2029', '\\u2029')):
        s = s.replace(a, b)
    return s


def claim_schema():
    rel = lambda k: {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'required': ['type', k],
                     'properties': {'type': {'enum': list(REL)}, k: {'type': 'string', 'pattern': r'^D\d+-C\d{3}$'}}}}
    props = {
        'id': {'type': 'string', 'pattern': r'^D\d+-C\d{3}$', 'description': 'Stable claim id; cite it.'},
        'day': {'type': 'integer', 'minimum': 1, 'description': 'Event day. For docs, press and analysis claims: the day this claim annotates.'},
        'session_id': {'type': 'string', 'pattern': r'^D\d+-S\d{2}$', 'description': 'D<day>-S00 means the session was not recorded.'},
        'session': {'type': 'string', 'minLength': 1},
        'speaker': {'type': ['string', 'null'], 'description': 'Slide and stage claims only: who, or the session speaker(s).'},
        'who': {'type': ['string', 'null'], 'description': 'Per-claim speaker: a name, "audience" or "unknown".'},
        'author': {'type': ['string', 'null'], 'description': 'Analysis: the author. Docs and press: the publisher(s) of the sources. Slide and stage: null.'},
        'label': {'enum': list(LABELS)},
        'label_meaning': {'enum': list(LABEL_HELP.values())},
        'text': {'type': 'string', 'minLength': 1},
        'quote': {'type': 'string', 'description': 'Exact words, at most 25; "" when there is none.'},
        'quote_checked': {'type': 'boolean'},
        'verification': {'enum': list(VER)},
        'topics': {'type': 'array', 'minItems': 1, 'items': {'type': 'string', 'pattern': r'^[a-z0-9]+(-[a-z0-9]+)*$'}},
        'sources': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'required': ['key', 'title', 'url', 'publisher', 'kind', 'checked'],
                    'properties': {'key': {'type': 'string'}, 'title': {'type': 'string'}, 'url': {'type': 'string'}, 'publisher': {'type': 'string'},
                                   'kind': {'enum': ['google', 'press']}, 'checked': {'type': 'string', 'pattern': r'^\d{4}-\d{2}-\d{2}$'}}}},
        'evidence': {'type': 'array', 'items': {'type': 'string', 'minLength': 1}},
        'relations': rel('to'), 'related_from': rel('from'),
        'used_by': {'type': 'array', 'items': {'type': 'string', 'pattern': r'^(req|fact|myth|quote|angle|term):[A-Za-z0-9-]+$'},
                    'description': 'Derived: the kit items that rest on this claim (req:DEV-SRV-01, fact:F-012, myth:, quote:, angle:, '
                                   'term:<glossary term id>), as graph.json node ids. Never written by hand.'},
        'mentions': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['entity', 'via', 'field'],
            'properties': {'entity': {'type': 'string', 'pattern': r'^[a-z0-9]+(-[a-z0-9]+)*$'}, 'via': {'type': ['string', 'null'], 'minLength': 1},
                           'field': {'enum': ['text', 'quote', 'pin']}},
            'if': {'properties': {'field': {'const': 'pin'}}}, 'then': {'properties': {'via': {'type': 'null'}}}, 'else': {'properties': {'via': {'type': 'string'}}}},
            'description': 'Derived: the things (entities.json ids) this claim names, by entity id. via: the words as written in text or quote (field); '
                           'field pin, via null: pinned to the thing by hand in 20-claims/entities.yaml. Never written by hand.'}}
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'claims.schema.json', 'title': 'One line of claims.jsonl',
            'type': 'object', 'additionalProperties': False, 'required': list(props), 'properties': props,
            'allOf': [
                {'if': {'properties': {'label': {'enum': ['docs', 'press', 'analysis']}}}, 'then': {'properties': {'speaker': {'const': None}, 'who': {'const': None}}}},
                {'if': {'properties': {'label': {'const': 'analysis'}}}, 'then': {'properties': {'author': {'const': AUTHOR}}}},
                {'if': {'properties': {'label': {'enum': ['docs', 'press']}}}, 'then': {'properties': {'author': {'type': 'string', 'minLength': 1}}}},
                {'if': {'properties': {'label': {'enum': list(EVENT)}}}, 'then': {'properties': {'author': {'const': None}}}},
                {'if': {'properties': {'label': {'enum': ['docs', 'press']}}}, 'then': {'properties': {'verification': {'const': 'source'}}}}]}


# ---------------------------------------------------------------- graph.json and links.json (knowledge graph, phase 0: the links that exist)
NODE_KINDS = {
    'claim': 'A public claim of claims.jsonl. name: its text, cut at 100 characters; label, ver (its verification) and day as in claims.jsonl.',
    'topic': 'A topic of topics.json; url: its page in topics/.', 'area': 'An area of topics.json: a group of topics.',
    'session': 'A session of sessions.json; D<day>-S00 collects the points whose session was not recorded. url: its page in sessions/.',
    'day': 'An event day of sessions.json.', 'source': 'A document of sources.json; url: the document itself.',
    'requirement': 'A requirement of the developer kit (dev-requirements.json).', 'fact': 'A fact of the content kit (content-library.json).',
    'myth': 'A myth of the content kit, with the fact that answers it.', 'quote': 'A quotation of the content kit; name: the quotation.',
    'angle': 'A story angle of the content kit.', 'term': 'A glossary term of the content kit; its id is the id in content-library.json.',
    'entity': 'A thing the event talked about, from 20-claims/entities.yaml: entity_kind says which kind (product, feature, crawler, report, '
              'directive, status-code, standard, metric, concept, update, tool); url: its card in entities/; the full card is in entities.json.'}
EDGE_TYPES = {
    'about': 'Claim to topic: the claim is filed under the topic. Kit item to thing: the item is about the thing; count: how many of its claims '
             'mention the thing; own: its own words name it.',
    'in': 'Claim to session: where it was shown or said, or the session a docs, press or analysis claim annotates. Topic to area: its area.',
    'on': 'The session is on that day.',
    'cites': "Claim to source: a document the claim cites. Topic to claim: a claim its summary is based on (\"Based on\").",
    'related': 'A related topic, as listed in topics.yaml.',
    **{t: f'The first claim {v[0].lower()} the second ({v[0]} / {v[1]} in claims.jsonl).' for t, v in REL.items()},
    'rests-on': 'The kit item cites the claim: what a requirement, fact, myth, quote, story angle or glossary term rests on.',
    'documented-in': "A Google page in the requirement's or the thing's docs.",
    'mentions': 'Claim to thing: the claim names the thing. via: the words as written in the claim; field: text or quote. '
                'field pin (no via): the claim was pinned to the thing by hand because it names it without an alias.',
    'defines': 'Glossary term to thing: the term of the content kit that defines it.',
    'features': "Topic to thing: count of the topic's claims that mention the thing.",
    'co-mentioned': 'Thing to thing, written once, from the smaller id: count of the public claims that mention both, and their ids (claims). '
                    'The main link between two things.',
    **{t: f'Thing to thing, written by hand: {v[2]} Reverse: {v[0]}. ' + ('Structural: no claims needed.' if v[1] else 'claims: the public claims '
          'that say it, each mentioning both things; cite them, not the edge.') for t, v in ENT_REL.items()}}
KIT_PREFIX = {'requirement': 'req', 'fact': 'fact', 'myth': 'myth', 'quote': 'quote', 'angle': 'angle', 'term': 'term'}
SPEAKER_GROUPS = {'google': 'Google', 'community': 'a community speaker',
                  'unattributed': 'a speaker (the knowledge base does not record whether Google or a community speaker)', 'audience': 'audience'}
GRADE_ORDER = ('source', 'confirmed', 'consistent', 'undocumented', 'n/a')


def claim_cite(c, kb, google):
    """The citation of one public claim in the form of AGENTS.md "How to cite". A person is named only where kits.proven() proves
    it; otherwise the kits' credit: Google, a community speaker, a speaker, an audience member."""
    K_, _ = kits()
    S, sources = kb['sessions'], kb['sources']
    if c['label'] == 'analysis': return f"[{c['id']}, analysis, {AUTHOR}]"
    if c['label'] in ('docs', 'press'):
        return f"[{c['id']}, {c['label']}, {', '.join(dict.fromkeys(sources[k]['publisher'] for k in c['src']))}, {sources[c['src'][0]]['url']}]"
    return f"[{c['id']}, {c['label']}, {K_.proven(c, S) or K_.who_short(c, S, google, sources)}, Day {S[c['s']]['day']}]"


def entity_model(kb, KI):
    """What the outputs say about the things, all derived from kb['mentions'] (B2.3 of the plan): per thing its claims, tally,
    citations, relations both ways, co-mentions, topics and kit items; per claim its mentions; per topic and session its things;
    per kit item its things (its own words name it, or at least two of its claims do; half of them when it has fewer than four)."""
    K_, ns_ = kits()
    S = kb['sessions']
    public = [c for c in kb['claims'] if c.get('private') is not True]
    CL = {c['id']: c for c in public}
    M, ents = kb.get('mentions', {}), kb.get('entities', [])
    _, google = K_.people(S)
    trank = {t: i for i, t in enumerate(kb['topics'])}
    by_claim = {cid: [{'entity': e, 'via': v['via'], 'field': v['field']} for e, v in m.items()] for cid, m in M.items()}
    claims_of, co, feat, sess = defaultdict(list), defaultdict(dict), defaultdict(Counter), defaultdict(Counter)
    for c in public:
        es = sorted(M.get(c['id'], {}))
        for e in es:
            claims_of[e].append(c['id'])
            for t in c['topics']: feat[t][e] += 1
            sess[c['s']][e] += 1
            for o in es:
                if o != e: co[e].setdefault(o, []).append(c['id'])
    texts = K_.item_texts(kb, ns_) if ents else {}
    item_ents, items_of = {}, defaultdict(list)
    for nid, it in KI.items():
        n = Counter(e for x in it['claims'] for e in M.get(x, {}))
        own = {s[2] for s in ent_match(kb.get('ent_rules', []), texts.get(nid, ''), set(it['topics']))}
        k = len(it['claims'])
        keep = sorted((e for e in set(n) | own if e in own or (n[e] >= 2 if k >= 4 else 2 * n[e] >= k)), key=lambda e: (-n[e], e))
        item_ents[nid] = [{'id': e, 'count': n[e], 'own': e in own} for e in keep]
        for e in keep: items_of[e].append({'id': nid, 'count': n[e], 'own': e in own})
    rel_from = defaultdict(list)
    for x in ents:
        for r in x['rel']: rel_from[r['to']].append({'type': r['type'], 'from': x['id'], 'claims': r['claims']})
    defs = {node_slug(t['term']): (nt(t['term']), nt(t['definition'])) for t in kb['kits']['content']['glossary']}
    rank = lambda cnt, key=lambda k: k: sorted(cnt, key=lambda k: (-cnt[k], key(k)))
    out = []
    for x in ents:
        cs, others = claims_of[x['id']], co[x['id']]
        ev = Counter(CL[c]['ver'] for c in cs if CL[c]['label'] in EVENT)
        lab = Counter(CL[c]['label'] for c in cs)
        ft = Counter({t: n[x['id']] for t, n in feat.items() if n[x['id']]})
        out.append({'id': x['id'], 'kind': x['kind'], 'name': x['name'],
                    'aliases': [a['s'] for a in x['aliases'] if fold(a['s']) != fold(x['name'])],
                    'match': [{'s': r['s'], 'exact': r['exact'], 'in': sorted(r['in']) if r['in'] else None, 'claims': kb['alias_hits'][r['i']]} for r in x['rules']],
                    'summary': x['summary'], 'glossary': x['glossary'], 'definition': defs[x['glossary']][1] if x['glossary'] else None,
                    'docs': x['docs'], 'topics': x['topics'],
                    'rel': [dict(r) for r in x['rel']], 'rel_from': sorted(rel_from[x['id']], key=lambda r: (r['type'], r['from'])),
                    'claims': cs,
                    'tally': {'docs': lab['docs'], 'event': {g: ev[g] for g in ('undocumented', 'confirmed', 'consistent', 'n/a')},
                              'press': lab['press'], 'analysis': lab['analysis']},
                    'cite': {c: claim_cite(CL[c], kb, google) for c in cs},
                    'co_mentioned': [{'id': o, 'count': len(others[o]), 'claims': others[o]} for o in sorted(others, key=lambda o: (-len(others[o]), o))],
                    'featured_in': [{'id': t, 'count': ft[t]} for t in rank(ft, trank.get)],
                    'items': items_of[x['id']]})
    return {'list': out, 'by_id': {x['id']: x for x in out}, 'by_claim': by_claim, 'item_entities': item_ents, 'defs': defs,
            'topic_entities': {t: [{'id': e, 'count': feat[t][e]} for e in rank(feat[t])] for t in kb['topics']},
            'session_entities': {s: [{'id': e, 'count': sess[s][e]} for e in rank(sess[s])] for s in S}}


def pack_graph(kb, KI, fname, private_only, EN):
    """graph.json and links.json of the agent pack, from links that already exist: claim fields (topics, session, src, rel), topics.yaml
    (area, related, cites), sessions.yaml (day), the kits' cited claims and docs. Public claims only; every edge end is a node (checked
    here: a broken end stops the build); nodes sorted by id, edges by (from, type, to). No clock, no hand-written data."""
    S, sources = kb['sessions'], kb['sources']
    public = [c for c in kb['claims'] if c.get('private') is not True]
    snip = lambda x: x if len(x) <= 100 else x[:100].rsplit(' ', 1)[0].rstrip(',;:') + '…'
    nodes, edges = {}, {}  # edges: (from, type, to) -> extra fields (via, field, count, own, claims)

    def node(nid, kind, name, url, **kw):
        nodes[nid] = {'id': nid, 'kind': kind, 'name': name, 'url': url, **kw}

    def edge(f, t, to, **kw):
        edges[(f, t, to)] = kw
    for d in kb['days']: node(f"day:{d['day']}", 'day', f"Day {d['day']}: {nt(d['theme'])}", None)
    for sid, s in S.items():
        node(f'session:{sid}', 'session', nt(s['title']), f'sessions/{fname[sid]}')
        edge(f'session:{sid}', 'on', f"day:{s['day']}")
    for a in kb['areas']:
        node(f"area:{a['id']}", 'area', nt(a['title']), None)
        for t in a['topics']:
            tn = f"topic:{t['id']}"
            node(tn, 'topic', nt(t['title']), f"topics/{t['id']}.md")
            edge(tn, 'in', f"area:{a['id']}")
            for r in as_list(t.get('related')): edge(tn, 'related', f'topic:{r}')
            for x in as_list(t.get('cites')): edge(tn, 'cites', f'claim:{x}')
    for k in sources:
        if k not in private_only: node(f'source:{k}', 'source', nt(sources[k]['title']), sources[k]['url'])
    for c in public:
        cn = f"claim:{c['id']}"
        node(cn, 'claim', snip(nt(c['text'])), f"sessions/{fname[c['s']]}", label=c['label'], ver=c['ver'], day=S[c['s']]['day'])
        for t in c['topics']: edge(cn, 'about', f'topic:{t}')
        edge(cn, 'in', f"session:{c['s']}")
        for k in c.get('src', []): edge(cn, 'cites', f'source:{k}')
        for r in c.get('rel', []): edge(cn, r['type'], f"claim:{r['to']}")
    for nid, it in KI.items():
        node(nid, it['kind'], it['name'], it['file'])
        for x in it['claims']: edge(nid, 'rests-on', f'claim:{x}')
    for a in kb['kits']['areas']:
        for r in a['requirements']:
            for k in r.get('docs') or []: edge(f"req:{r['id']}", 'documented-in', f'source:{k}')
    for x in EN['list']:  # things (phase 1): every edge below is derived from the claims' words, or carries the claim ids behind it
        en = f"ent:{x['id']}"
        node(en, 'entity', x['name'], f"entities/{x['id']}.md", entity_kind=x['kind'])
        for k in x['docs']: edge(en, 'documented-in', f'source:{k}')
        for r in x['rel']: edge(en, r['type'], f"ent:{r['to']}", **({'claims': r['claims']} if r['claims'] else {}))
        if x['glossary']: edge(f"term:{x['glossary']}", 'defines', en)
        for y in x['featured_in']: edge(f"topic:{y['id']}", 'features', en, count=y['count'])
        for y in x['co_mentioned']:
            if x['id'] < y['id']: edge(en, 'co-mentioned', f"ent:{y['id']}", count=y['count'], claims=y['claims'])
    for cid, ms in EN['by_claim'].items():
        for m in ms: edge(f'claim:{cid}', 'mentions', f"ent:{m['entity']}", **({'field': 'pin'} if m['field'] == 'pin' else {'via': m['via'], 'field': m['field']}))
    for nid, es in EN['item_entities'].items():
        for y in es: edge(nid, 'about', f"ent:{y['id']}", count=y['count'], own=y['own'])
    bad = sorted(e for e in edges if e[0] not in nodes or e[2] not in nodes)
    if bad: raise SystemExit(f'graph.json: {len(bad)} edge(s) end at no node, e.g. {bad[0]}. Nothing after the agent pack was written.')
    order = sorted(edges)
    kind_rank = {k: i for i, k in enumerate(NODE_KINDS)}
    ends = defaultdict(Counter)
    for f, t, to in order: ends[t][(nodes[f]['kind'], nodes[to]['kind'])] += 1
    graph = {'version': kb['version'], 'data_through': kb['badge_stats']['data_through'],
             'about': 'The links that exist in the knowledge base, and the things (entities) its claims name, as nodes and edges. '
                      'A node or an edge is a map, not a source: cite the claim ids behind it.',
             'node_kinds': {k: {'count': sum(1 for n in nodes.values() if n['kind'] == k), 'about': v} for k, v in NODE_KINDS.items()},
             'edge_types': {t: {'ends': sorted(ends[t], key=lambda p: (kind_rank[p[0]], kind_rank[p[1]])), 'count': sum(ends[t].values()), 'about': v}
                            for t, v in EDGE_TYPES.items() if ends[t]},
             'nodes': [nodes[k] for k in sorted(nodes)],
             'edges': [{'from': f, 'to': to, 'type': t, **edges[(f, t, to)]} for f, t, to in order]}

    # links.json: the same links as lookup tables for the web edition and for agents
    K_, ns_ = kits()
    _, google = K_.people(S)
    used_by = defaultdict(list)
    for nid, it in KI.items():
        for x in it['claims']: used_by[x].append(nid)
    by_src = defaultdict(lambda: defaultdict(list))
    for c in public:
        for k in c.get('src', []): by_src[k][c['ver']].append(c['id'])
    reqs_of = defaultdict(list)
    for a in kb['kits']['areas']:
        for r in a['requirements']:
            for k in r.get('docs') or []: reqs_of[k].append(f"req:{r['id']}")
    aliases = defaultdict(set)
    spellings = [(nid, x) for nid, it in KI.items() for x in it.get('aliases', [])]
    spellings += [(f"ent:{x['id']}", s) for x in EN['list'] for s in [x['name']] + [r['s'] for r in x['match']]]  # a thing: its name and every alias
    for nid, x in spellings:  # each spelling, and the same with its hyphens closed up: "query fanout", "eeat"
        if not norm_key(x): continue
        aliases[norm_key(x)].add(nid)
        if '-' in x: aliases[norm_key(x.replace('-', ''))].add(nid)
    group = {'Google': 'google', 'a community speaker': 'community', 'a speaker': 'unattributed', 'an audience member': 'audience'}
    spk = {}
    for c in public:
        if c['label'] in EVENT: spk[c['id']] = {'group': group[K_.who_short(c, S, google, sources)], 'name': K_.proven(c, S)}
    names = Counter(v['name'] for v in spk.values() if v['name'])
    gcount = Counter(v['group'] for v in spk.values())
    links = {'version': graph['version'], 'data_through': graph['data_through'],
             'about': 'Lookup tables built from the links in graph.json. Node ids as in graph.json. A link is a map, not a source: cite the claim ids.',
             'items': KI,
             'used_by': {c['id']: used_by[c['id']] for c in public if used_by.get(c['id'])},
             'topic_items': {t: [n for n in KI if t in KI[n]['topics']] for t in kb['topics']},
             'sources': {k: {'claims': {g: by_src[k][g] for g in GRADE_ORDER if by_src[k].get(g)}, 'requirements': reqs_of.get(k, [])}
                         for k in sources if k not in private_only},
             'aliases': {k: sorted(aliases[k]) for k in sorted(aliases)},
             'speakers': {'names': [{'name': n, 'claims': names[n]} for n in sorted(names, key=lambda n: (-names[n], n))],
                          'groups': [{'id': g, 'label': SPEAKER_GROUPS[g], 'claims': gcount[g]} for g in SPEAKER_GROUPS if gcount[g]],
                          'claims': spk}}
    return graph, links


THINGS_TOP = 12  # things listed on a topic or session page
VER_SHORT = {'confirmed': 'confirmed by Google docs', 'consistent': 'consistent with Google docs', 'undocumented': 'not in Google docs',
             'n/a': 'nothing to verify', 'source': ''}
REL_WORDS = {'is-a': ('Is a', 'Includes'), 'part-of': ('Part of', 'Has part'), 'uses': ('Uses', 'Used by'), 'affects': ('Affects', 'Affected by'),
             'measured-by': ('Measured by', 'Measures'), 'applies-to': ('Applies to', 'Subject of')}
KIT_WORD = {'requirement': 'Requirement', 'fact': 'Fact', 'myth': 'Myth', 'quote': 'Quote', 'angle': 'Story angle', 'term': 'Glossary term'}
ALIAS_ROW = re.compile(r'^\| (.*) \| `([a-z0-9-]+)` \| (.*?) \| (\d+) \|$')  # a row of "Alias hits" in 50-maps/entity-index.md


def things_line(EN, ents, link):
    """'[Googlebot](link) (34) · [robots.txt](link) (20)': the things of a topic or session page, most mentioned first."""
    return ' · '.join(f"[{md(EN['by_id'][y['id']]['name'])}]({link(y['id'])}) ({y['count']})" for y in ents[:THINGS_TOP])


def code_or_md(s):  # a citation as a code span (it holds no backtick), so Markdown leaves its brackets alone
    return f'`{s}`' if '`' not in s else md(s)


def tally_text(t, n):
    ev = sum(t['event'].values())
    parts = [f"{t['docs']} from Google's documentation"] if t['docs'] else []
    if ev: parts.append(f'{ev} shown or said at the event (' + ', '.join(f"{t['event'][g]} {VER_SHORT[g]}" for g in t['event'] if t['event'][g]) + ')')
    parts += [f"{t[k]} {w}" for k, w in (('press', 'press report' + 's' * (t['press'] != 1)), ('analysis', "the author's analysis")) if t[k]]
    return f"{n} claim{'s' * (n != 1)} mention it" + (': ' + ', '.join(parts) if parts else '') + '.'


def entities_json(EN, meta):
    return {'version': meta['version'], 'data_through': meta['through'],
            'about': 'The things the event talked about (20-claims/entities.yaml), each with everything the knowledge base links to it. A card is a '
                     'map, not a source: cite the claim ids it lists; cite holds the citation of each claim.',
            'kinds': {k: {'label': v[0], 'about': v[1], 'count': sum(1 for x in EN['list'] if x['kind'] == k)} for k, v in ENTITY_KINDS.items()},
            'relation_types': {t: {'reverse': v[0], 'structural': v[1], 'about': v[2]} for t, v in ENT_REL.items()},
            'entities': EN['list'], 'topic_entities': EN['topic_entities'], 'session_entities': EN['session_entities']}


def entity_card(x, kb, EN, KI, fname):
    """The Markdown card of one thing in the agent pack (entities/<id>.md): short, linking to its home topics for the narrative."""
    S, sources, topics = kb['sessions'], kb['sources'], kb['topics']
    CL = {c['id']: c for c in kb['claims'] if c.get('private') is not True}
    reqs = {r['id']: r for a in kb['kits']['areas'] for r in a['requirements']}
    K_, _ = kits()
    link = lambda e: f"[{md(EN['by_id'][e]['name'])}]({e}.md)"

    def line(cid):
        c = CL[cid]
        meta = [LABELS[c['label']]] + ([f"Day {S[c['s']]['day']}", VER_SHORT[c['ver']]] if c['label'] in EVENT else [])
        return f"- [`{cid}`](../sessions/{fname[c['s']]}) {', '.join(m for m in meta if m)}: {md(c['text'])} {code_or_md(x['cite'][cid])}"
    head = {'id': x['id'], 'kind': x['kind'], 'name': x['name'], 'aliases': x['aliases'], 'claims': len(x['claims']), 'topics': x['topics'], 'docs': x['docs']}
    out = ['---', yaml.safe_dump(head, sort_keys=False, allow_unicode=True).strip(), '---', GEN.strip(), '', f"# {md(x['name'])}", '',
           f"*{ENTITY_KINDS[x['kind']][0]}*" + (' · also written ' + ' · '.join(md(a) for a in x['aliases']) if x['aliases'] else ''), '', md(x['summary']), '']
    if x['definition']: out += [f"**Glossary** (*{md(EN['defs'][x['glossary']][0])}*): {md(x['definition'])}", '']
    if x['topics']:
        out += ['Narrative: the topic' + 's' * (len(x['topics']) > 1) + ' ' + ', '.join(f"[{md(topics[t]['title'])}](../topics/{t}.md)" for t in x['topics'])
                + ' tell' + 's' * (len(x['topics']) == 1) + ' the story; this card lists what links to it.', '']
    out += [tally_text(x['tally'], len(x['claims'])) + ' A card is a map: cite the claim ids, with the citation given after each claim.', '']
    by_label = defaultdict(list)
    for c in x['claims']: by_label[CL[c]['label']].append(c)
    if x['docs'] or by_label['docs']:
        out += ["## Google's documentation", '']
        if x['docs']: out += ['Documented in: ' + ', '.join(f"[{md(sources[k]['title'])}]({sources[k]['url']})" for k in x['docs']) + '.', '']
        out += [line(c) for c in by_label['docs']] + ([''] if by_label['docs'] else [])
    ev = by_label['slide'] + by_label['stage']
    if ev:
        out += ['## Shown or said at the event', '', 'Not in Google\'s documentation first: present those as said at Search Central Live, never as documented policy.', '']
        out += [line(c) for g in ('undocumented', 'confirmed', 'consistent', 'n/a') for c in x['claims'] if c in ev and CL[c]['ver'] == g] + ['']
    for lab, title in (('press', 'Press reports'), ('analysis', "The author's analysis")):
        if by_label[lab]: out += [f'## {title}', ''] + [line(c) for c in by_label[lab]] + ['']
    dev = [y for y in x['items'] if KI[y['id']]['kind'] == 'requirement']
    why = lambda y: ' (' + '; '.join(p for p in (f"{y['count']} of its claims mention{'s' * (y['count'] == 1)} it" if y['count'] else '',
                                                 'its own text names it' if y['own'] else '') if p) + ')'
    if dev:
        out += ['## For developers', '']
        for y in dev:
            r = reqs[KI[y['id']]['key']]
            out.append(f"- `{r['id']}` **{r['level']}** · {K_.STATUS[r['status']][0]}: {md(r['title'])}{why(y)}")
        out.append('')
    content = [y for y in x['items'] if KI[y['id']]['kind'] != 'requirement']
    if content:
        out += ['## For content', '']
        for y in content:
            it = KI[y['id']]
            label = f"*{md(it['name'])}*" if it['kind'] == 'term' else f"`{it['key']}`: {md(it['name'])}"
            out.append(f"- {KIT_WORD[it['kind']]} {label}{why(y)}")
        out.append('')
    con = []
    for r in x['rel']:
        con.append(f"- {REL_WORDS[r['type']][0]} {link(r['to'])}" + (f" ({len(r['claims'])} claim{'s' * (len(r['claims']) > 1)}: "
                   + ', '.join(f'`{c}`' for c in r['claims']) + ')' if r['claims'] else ''))
    for r in x['rel_from']:
        con.append(f"- {REL_WORDS[r['type']][1]} {link(r['from'])}" + (f" ({len(r['claims'])} claim{'s' * (len(r['claims']) > 1)}: "
                   + ', '.join(f'`{c}`' for c in r['claims']) + ')' if r['claims'] else ''))
    if x['co_mentioned']: con.append('- Mentioned together with: ' + ' · '.join(f"{link(y['id'])} ({y['count']})" for y in x['co_mentioned'][:15]))
    if x['featured_in']: con.append('- Topics whose claims mention it: ' + ' · '.join(f"[{md(topics[y['id']]['title'])}](../topics/{y['id']}.md) ({y['count']})" for y in x['featured_in'][:15]))
    if con: out += ['## Connected things', ''] + con + ['']
    return '\n'.join(out)


def entity_index(kb, EN, meta, fname):
    """50-maps/entity-index.md: every thing with its counts, the alias hits, the precision sample and every mention with the words that
    matched, so `git diff` after a rebuild shows exactly which mentions came and went (step 3 and 4 of B3 in the plan)."""
    public = [c for c in kb['claims'] if c.get('private') is not True]
    CL, order = {c['id']: c for c in public}, {c['id']: i for i, c in enumerate(public)}
    sl = lambda cid: f"../40-sessions/day{kb['sessions'][CL[cid]['s']]['day']}/{fname[CL[cid]['s']]}"
    ms = [(cid, m) for cid, x in EN['by_claim'].items() for m in x]
    pins = sum(1 for _, m in ms if m['field'] == 'pin')
    out = [GEN, '# Entity index\n',
           'The things of `20-claims/entities.yaml` and every public claim each one is matched in, with the words that matched. '
           'It is the review list for the things: the web edition and the agent pack show the same matches as cards.\n',
           f"Version {meta['version']}, data through {meta['through_txt']}.\n"]
    if not EN['list']:
        return '\n'.join(out + ['No things yet: `20-claims/entities.yaml` is missing or lists none.', ''])
    out += [f"**{len(EN['list'])} things, {len(ms)} mentions in {len(EN['by_claim'])} of {len(public)} public claims** "
            f"({pins} pinned by hand). How a claim is matched: `_system/schema/claim.md`, section *Things*.\n",
            '**How to review.** Read the precision sample below and mark every row where the matched words do not mean the thing (another sense of '
            'the word, or a different thing with a similar name): fewer than 5 wrong in 100 '
            'is the bar. After each rebuild, `git diff 50-maps/entity-index.md` shows exactly the mentions that came and went. A wrong mention: '
            'make the alias a phrase, scope it to topics or `unpin` the claim. A missed one: add an alias or `pin` the claim.\n',
            '## Things by kind\n', '| Thing | Id | Claims | Docs | Event | Not in docs | Home topics |', '| --- | --- | ---: | ---: | ---: | ---: | --- |']
    for k, (label, _) in ENTITY_KINDS.items():
        for x in (x for x in EN['list'] if x['kind'] == k):
            out.append(f"| {cell(x['name'])} ({label.lower()}) | `{x['id']}` | {len(x['claims'])} | {x['tally']['docs']} | {sum(x['tally']['event'].values())} | "
                       f"{x['tally']['event']['undocumented']} | {', '.join(x['topics']) or '—'} |")
    zero = [x['id'] for x in EN['list'] if not x['claims']]
    out += ['', '*Docs*: Google documentation claims. *Event*: slide and stage claims; *Not in docs*: those of them Google\'s documentation does not back.', '']
    if zero: out += ['## Things no claim mentions', '', 'Add an alias, a scope or a pin, or remove the thing: ' + ', '.join(f'`{z}`' for z in zero) + '.', '']
    out += ['## Alias hits', '', 'Every spelling a thing is matched by, and in how many public claims it matched. The build prints a note when a spelling '
            f'newly matches more than {DRIFT} claims.', '', '| Alias | Thing | Matched | Claims |', '| --- | --- | --- | ---: |']
    for x in EN['list']:
        out += [f"| {cell(r['s'])} | `{x['id']}` | {rule_mode({'exact': r['exact'], 'in': r['in']})} | {r['claims']} |" for r in x['match']]
    pool = sorted((hashlib.sha1(f"{cid} {m['entity']}".encode()).hexdigest(), cid, m) for cid, m in ms if m['field'] != 'pin')[:SAMPLE_N]
    out += ['', '## Precision sample', '', f'{len(pool)} mentions picked by a hash of the claim id and the thing id, so every build picks the same ones '
            'while the data stays the same. For each row: do the matched words mean this thing here? Mark a wrong row with an x.', '',
            '| # | Claim | Thing | Matched words | Claim text or quote | Wrong? |', '| ---: | --- | --- | --- | --- | --- |']
    for i, (_, cid, m) in enumerate(sorted(pool, key=lambda p: (order[p[1]], p[2]['entity'])), 1):
        txt = nt(CL[cid]['text'] if m['field'] == 'text' else CL[cid].get('quote') or '')
        out.append(f"| {i} | [`{cid}`]({sl(cid)}) | `{m['entity']}` | {cell(m['via'])} | {cell(txt)} | |")
    out += ['', '## Every mention', '']
    for x in EN['list']:
        out += [f"### {md(x['name'])} (`{x['id']}`): {len(x['claims'])}", '']
        for cid in x['claims']:
            m = next(y for y in EN['by_claim'][cid] if y['entity'] == x['id'])
            if m['field'] == 'pin': out.append(f"- [`{cid}`]({sl(cid)}) pinned: {md(CL[cid]['text'])}")
            else: out.append(f"- [`{cid}`]({sl(cid)}) **{md(m['via'])}**{' (in the quote)' if m['field'] == 'quote' else ''}: {md(CL[cid]['text'])}")
        out.append('')
    return '\n'.join(out)


def drift(old, EN):
    """Spellings that match more than DRIFT claims now and did not before: read from the previous 50-maps/entity-index.md."""
    was = {}
    for ln in old.splitlines():
        m = ALIAS_ROW.match(ln)
        if m: was[(m[2], m[1])] = int(m[4])
    return [(x['id'], r['s'], was.get((x['id'], cell(r['s']))), r['claims']) for x in EN['list'] for r in x['match']
            if r['claims'] > DRIFT and was.get((x['id'], cell(r['s'])), 0) <= DRIFT]


def graph_json(g):
    """graph.json as valid JSON with the header indented and one node or edge per line, so a diff shows exactly what changed."""
    line = lambda o: '    ' + json.dumps(o, ensure_ascii=False)
    head = json.dumps({k: v for k, v in g.items() if k not in ('nodes', 'edges')}, indent=2, ensure_ascii=False)
    return (head[:-2] + ',\n  "nodes": [\n' + ',\n'.join(map(line, g['nodes'])) + '\n  ],\n  "edges": [\n'
            + ',\n'.join(map(line, g['edges'])) + '\n  ]\n}\n')


def build(root, kb):
    S, sources, areas, topics = kb['sessions'], kb['sources'], kb['areas'], kb['topics']
    DAYS = {d['day']: d for d in kb['days']}
    claims = kb['claims']
    public = [c for c in claims if c.get('private') is not True]
    private = [c for c in claims if c.get('private') is True]
    CL = {c['id']: c for c in public}
    area_of = {t['id']: a for a in areas for t in a['topics']}
    by_topic = defaultdict(list)
    for c in public:
        for t in c['topics']: by_topic[t].append(c)
    rfrom = defaultdict(list)
    for c in public:
        for r in c.get('rel', []): rfrom[r['to']].append({'type': r['type'], 'from': c['id']})
    day = lambda c: S[c['s']]['day']
    is_ev = lambda c: c['label'] in EVENT
    real = lambda sid: not sid.endswith('-S00')
    order = {sid: i for i, sid in enumerate(S)}
    fname = {sid: f"{sid}-{slug(s['title'])}.md" for sid, s in S.items()}
    used_days = sorted({day(c) for c in public})
    version, through = kb['version'], (DAYS[used_days[-1]]['date'] if used_days else '')
    through_txt = f"{through} (Day {used_days[-1]})" if through else 'no claims yet'
    K_, ns_ = kits()
    KI = K_.kit_items(kb, ns_)  # every kit item as a graph node: req:DEV-SRV-01, fact:F-012, ..., term:crawl-budget
    EN = entity_model(kb, KI)  # the things (20-claims/entities.yaml) and everything derived from their mentions
    kb['item_entities'] = EN['item_entities']  # kits.build() writes them on the kit items
    kb['entity_model'] = EN  # kits.build() also asks each thing "What did Google say about it?" for the question bank (phase 3)
    el_up = lambda e: f'../../60-outputs/agent-pack/entities/{e}.md'  # a thing's card, from 30-topics/<area>/ and 40-sessions/day<N>/
    el_pack = lambda e: f'../entities/{e}.md'  # the same from the agent pack's topics/ and sessions/
    used_by = defaultdict(list)  # claim id -> the kit items that rest on it, in KIND_ORDER then key
    for nid, it in KI.items():
        for x in it['claims']: used_by[x].append(nid)
    kit_docs = {x for a in kb['kits']['areas'] for r in a['requirements'] for x in r.get('docs') or []}  # shared through dev-requirements.json
    private_only = {k for c in private for k in c.get('src', [])} - {k for c in public for k in c.get('src', [])} - kit_docs - ent_docs(kb)
    KIND_WORD = {'requirement': 'Requirement', 'fact': 'Fact', 'myth': 'Myth', 'quote': 'Quote', 'angle': 'Story angle', 'term': 'Glossary term'}

    def used_md(cid):  # "Used by `DEV-SRV-01`, `F-012`, the glossary term *Crawl stats*"
        ids = used_by.get(cid, [])
        if not ids: return None
        return 'Used by ' + ', '.join([f"`{KI[n]['key']}`" for n in ids if KI[n]['kind'] != 'term'] +
                                      [f"the glossary term *{md(KI[n]['name'])}*" for n in ids if KI[n]['kind'] == 'term'])

    def item_md(nid):  # one line of a topic page's "Built on these claims"
        it = KI[nid]
        if it['kind'] == 'term': return f"- {KIND_WORD['term']} *{md(it['name'])}*"
        return f"- {KIND_WORD[it['kind']]} `{it['key']}`: {md(it['name'])}"

    def spk_text(s):
        sp = ', '.join(speakers(s))
        return sp + (f", {s['role']}" if sp and s.get('role') else '')

    def speaker(c):  # claims.jsonl
        if not is_ev(c): return None
        return c.get('who') or ', '.join(speakers(S[c['s']])) or None

    def by(c):  # display
        if c['label'] == 'analysis': return f'{AUTHOR} (author)'
        if c['label'] in ('docs', 'press'): return ', '.join(dict.fromkeys(sources[k]['publisher'] for k in c.get('src', [])))
        w = c.get('who')
        return {'audience': 'audience member', 'unknown': 'speaker not identified'}.get(w, w) if w else spk_text(S[c['s']])

    def where(c, f=md):
        s = S[c['s']]
        return ('' if is_ev(c) else 'annotates ') + f"Day {s['day']}, " + (f(s['title']) if real(s['id']) else 'session not recorded')

    def ver_text(c):
        return 'is the press report' if c['ver'] == 'source' and c['label'] == 'press' else VER[c['ver']]

    def claim_md(c, sl, indent=''):
        meta = [f"`{c['id']}`"]
        if is_ev(c): meta.append(where(c) + (f' ({md(by(c))})' if by(c) else ''))
        else: meta += [md(by(c)), where(c)] if by(c) else [where(c)]
        if ver_text(c): meta.append(ver_text(c))
        if c.get('src'): meta.append(', '.join(f"[{md(sources[k]['title'])}]({sources[k]['url']})" for k in c['src']))
        meta += [f"{REL[r['type']][0]} [{r['to']}]({sl(CL[r['to']]['s'])})" for r in c.get('rel', []) if r['to'] in CL]
        meta += [f"{REL[r['type']][1]} [{r['from']}]({sl(CL[r['from']]['s'])})" for r in rfrom.get(c['id'], [])]
        if used_md(c['id']): meta.append(used_md(c['id']))
        out = f"- **[{LABELS[c['label']]}]** {md(c['text'])}\n"
        if c.get('quote'): out += f"  > \"{md(c['quote']).strip(chr(34))}\"\n"
        out += f"  <br><sub>{' · '.join(meta)}</sub>\n"
        return ''.join(indent + l for l in out.splitlines(True))

    def fm(d):
        return ['---', yaml.safe_dump(d, sort_keys=False, allow_unicode=True).strip(), '---', GEN.strip(), '']

    def tstats(cs):
        ev = [c for c in cs if is_ev(c)]
        return {'days': sorted({day(c) for c in cs}), 'sessions': sorted({c['s'] for c in cs}),
                'event_days': sorted({day(c) for c in ev}), 'event_sessions': sorted({c['s'] for c in ev if real(c['s'])})}

    def topic_page(a, t, tl, sl, el):
        cs = by_topic.get(t['id'], [])
        st = tstats(cs)
        last = max((DAYS[x]['date'] for x in st['event_days']), default=None)
        out = fm({'id': t['id'], 'title': t['title'], 'area': a['id'], **st, 'claims': len(cs), 'last_discussed': last})
        out += [f"# {md(t['title'])}", '', md(t['summary']), '']
        if t.get('cites'): out += ['Based on: ' + ', '.join(f'`{x}`' for x in t['cites']) + '.', '']
        if t.get('do'): out += ['## What to do', ''] + [f'- {md(x)}' for x in t['do']] + ['']
        if cs:
            out += ['## Where it was discussed', '']
            for dn in st['days']:
                dc = [c for c in cs if day(c) == dn]
                n_ev = Counter(c['s'] for c in dc if is_ev(c))
                parts = [f"[{md(S[sid]['title'])}]({sl(sid)}) ({k} claim{'s' * (k > 1)})" for sid, k in sorted(n_ev.items(), key=lambda x: order[x[0]])]
                other = sum(1 for c in dc if not is_ev(c))
                line = f"- **Day {dn}** ({DAYS[dn]['date']}, {md(DAYS[dn]['theme'])}): " + ('; '.join(parts) if parts else 'not raised on a slide or on stage')
                out.append(line + (f"; plus {other} documentation, press or analysis note{'s' * (other > 1)}" if other else ''))
            out.append('')
        for title, labs in [('Shown and said at the event', EVENT), ("What Google's documentation says", ('docs',)),
                            ('What the press reported', ('press',)), ('Analysis', ('analysis',))]:
            g = [c for c in cs if c['label'] in labs]
            if g: out += [f'## {title}', ''] + [claim_md(c, sl) for c in g]
        built = [n for n in KI if t['id'] in KI[n]['topics']]
        if built:
            out += ['## Built on these claims', '', "The items of the developer and content kits that rest on this topic's claims.", ''] + [item_md(n) for n in built] + ['']
        th = EN['topic_entities'].get(t['id'], [])
        if th: out += ['## Things in this topic', '', 'The things its claims mention most, with the number of claims: ' + things_line(EN, th, el) + '.', '']
        if t.get('related'):
            out += ['## Related topics', ''] + [f"- [{md(topics[r]['title'])}]({tl(r)})" for r in t['related']] + ['']
        srcs = sorted({k for c in cs for k in c.get('src', [])})
        if srcs:
            out += ['## Sources', ''] + [f"- [{md(sources[k]['title'])}]({sources[k]['url']}) — {md(sources[k]['publisher'])}, checked {sources[k]['checked']}"
                                         + (' (third-party press)' if sources[k].get('kind') == 'press' else '') for k in srcs] + ['']
        return '\n'.join(out)

    def session_page(d, s, tl, sl, el):
        cs = [c for c in public if c['s'] == s['id']]
        tset = list(dict.fromkeys(t for c in cs for t in c['topics']))
        meta = {'id': s['id'], 'title': s['title'], 'day': d['day'], 'time': s['time'], 'speaker': s['speaker'],
                'coverage': s['coverage'][0] if len(s['coverage']) == 1 else s['coverage']}
        meta.update({k: s[k] for k in ('role', 'kind') if s.get(k)})
        out = fm({**meta, 'claims': len(cs), 'topics': tset})
        kind = f" · {s['kind']}" if s.get('kind', 'talk') != 'talk' else ''
        out += [f"# {md(s['title'])}", '', f"Day {d['day']}, {s['time'] or 'time not recorded'} · {md(spk_text(s)) or 'speaker not recorded'}{kind} · coverage: {', '.join(s['coverage'])}", '']
        if s.get('note'): out += [md(s['note']), '']
        if not cs:
            out += ['No claims captured from this session yet. Additions are welcome.', '']
            return '\n'.join(out)
        pos = {c['id']: i for i, c in enumerate(cs)}
        parent = {}
        for c in cs:  # an answer is shown under the earliest earlier question of this session it answers
            qs = [r['to'] for r in c.get('rel', []) if r['type'] == 'answers' and pos.get(r['to'], 1e9) < pos[c['id']]]
            if qs: parent[c['id']] = min(qs, key=pos.get)
        kids = defaultdict(list)
        for k, p in parent.items(): kids[p].append(k)

        def emit(c, ind):
            yield claim_md(c, sl, ind)
            for k in sorted(kids[c['id']], key=pos.get): yield from emit(CL[k], ind + '  ')
        out += ['## Claims', ''] + [x for c in cs if c['id'] not in parent for x in emit(c, '')]
        out += ['## Topics covered', ''] + [f"- [{md(topics[t]['title'])}]({tl(t)})" for t in tset] + ['']
        th = EN['session_entities'].get(s['id'], [])
        if th: out += ['## Things in this session', '', 'The things its claims mention most, with the number of claims: ' + things_line(EN, th, el) + '.', '']
        return '\n'.join(out)

    # ---------------- 30-topics
    T = root / '30-topics'
    fresh(T)
    tl_t = lambda r: f"../{area_of[r]['id']}/{r}.md"
    sl_t = lambda sid: f"../../40-sessions/day{S[sid]['day']}/{fname[sid]}"
    days_txt = lambda ds: ' · '.join(str(n) for n in ds) or '—'
    root_link = lambda up: [('Knowledge base', f'{up}README.md')]
    labels_txt = ', '.join(f"**[{LABELS[k]}]** {LABEL_HELP[k]}" for k in LABELS)

    def topic_table(a, link):
        rows = ['| Topic | Claims | Days | Sessions |', '| --- | ---: | --- | ---: |']
        for t in a['topics']:
            cs = by_topic.get(t['id'], [])
            st = tstats(cs)
            rows.append(f"| [{cell(t['title'])}]({link(t['id'])}) | {len(cs)} | {days_txt(st['event_days'])} | {len(st['event_sessions'])} |")
        return rows
    key = ('*Claims* counts every public claim on the topic. *Days* and *Sessions* say where it was raised on a slide or on stage; '
           'a point from a session that was not recorded counts for its day, never as a session.')
    topic_use = ('Open a topic for its summary and the claims it is based on, what to do, where it was discussed on each day, every claim '
                 "(what was shown and said at the event, Google's documentation, press reports, analysis), related topics and sources.")
    topic_gen = generated_note('`_system/build_kb.py`', '`20-claims/topics.yaml` or the claims in `20-claims/`')
    for i, a in enumerate(areas):
        for t in a['topics']: write(T / a['id'] / f"{t['id']}.md", topic_page(a, t, tl_t, sl_t, el_up))
        prev, nxt = areas[i - 1] if i else None, areas[i + 1] if i + 1 < len(areas) else None
        summ = ['## In brief', ''] + [f"- **[{md(t['title'])}]({t['id']}.md)**: {md(t['summary'])}" for t in a['topics']] + ['']
        body = ["## What's here", ''] + topic_table(a, lambda t: f'{t}.md') + ['', key, ''] + summ + ['## How to use it', '', topic_use, ''] + topic_gen
        foot = nav((md(prev['title']), f"../{prev['id']}/README.md") if prev else ('', None), ('All topics', '../README.md'),
                   (md(nxt['title']), f"../{nxt['id']}/README.md") if nxt else ('', None))
        write(T / a['id'] / 'README.md', readme(2, root_link('../../') + [('30-topics', '../README.md'), (a['id'], None)], GEN, md(a['title']),
                                                f"**{md(a['blurb'])}**", body, foot, art=f"30-topics-{a['id']}"))
    body = ["## What's here", '', '| Area | Topics | Claims | Days | About |', '| --- | ---: | ---: | --- | --- |']
    for a in areas:
        acs = {c['id'] for t in a['topics'] for c in by_topic.get(t['id'], [])}
        ads = sorted({n for t in a['topics'] for n in tstats(by_topic.get(t['id'], []))['event_days']})
        body.append(f"| [{cell(a['title'])}]({a['id']}/README.md) | {len(a['topics'])} | {len(acs)} | {days_txt(ads)} | {cell(a['blurb'])} |")
    body += ['', '*Claims* counts each public claim once per area, though a claim can belong to several topics. '
             '*Days*: the days the area was raised on a slide or on stage.', '', '## Topics by area', '', key, '']
    for a in areas:
        body += [f"### [{md(a['title'])}]({a['id']}/README.md)", ''] + topic_table(a, lambda t, a=a: f"{a['id']}/{t}.md") + ['']
    body += ['## How to use it', '', f'- {topic_use}', f'- Every claim carries a label: {labels_txt}.',
             '- A sentence that starts with "Author\'s view:" is the author\'s interpretation, never Google\'s.', ''] + topic_gen
    write(T / 'README.md', readme(1, root_link('../') + [('30-topics', None)], GEN, 'Topics',
                                  '**One page per topic, grouped by area, each built from the claims in [`20-claims/`](../20-claims/README.md).**',
                                  body, pipeline_nav('30-topics', '../'), art='30-topics'))

    # ---------------- 40-sessions
    SD = root / '40-sessions'
    fresh(SD)
    tl_s = lambda t: f"../../30-topics/{area_of[t]['id']}/{t}.md"
    sl_s = lambda sid: f"../day{S[sid]['day']}/{fname[sid]}"
    n_cl = Counter(c['s'] for c in public)
    kinds = {'talk': 'Talk', 'lightning': 'Lightning', 'panel': 'Panel', 'qa': 'Q&A', 'poster': 'Poster', 'break': 'Break'}
    cover = {'slides': 'Slides', 'notes': 'Notes', 'transcript': 'Transcript', 'one-slide': 'One slide', 'video': 'Video', 'none': 'None'}
    day_head = lambda d: f"Day {d['day']} · {nt(d['theme'])}"
    over = ["## What's here", '', '| Day | Date | Theme | Sessions | With claims | Claims |', '| --- | --- | --- | ---: | ---: | ---: |']
    days_md = []
    for d in kb['days']:
        (SD / f"day{d['day']}").mkdir()
        agenda = [s for s in d['sessions'] if real(s['id'])]
        n_with, n_day = sum(1 for s in agenda if n_cl[s['id']]), sum(n_cl[s['id']] for s in d['sessions'])
        over.append(f"| [Day {d['day']}](#{anchor(day_head(d))}) | {d['date']} | {cell(d['theme'])} | {len(agenda)} | {n_with} | {n_day} |")
        days_md += [f"## Day {d['day']} · {md(d['theme'])}", '']
        if not d['sessions']: days_md += [f"{d['date']} · Not added yet.", '']; continue
        days_md += [f"{d['date']} · {len(agenda)} session{'s' * (len(agenda) != 1)} on the agenda · {n_with} with claims · {n_day} claims", '',
                    '| Time | Session | Speaker | Kind | Coverage | Claims |', '| --- | --- | --- | --- | --- | ---: |']
        for s in d['sessions']:
            write(SD / f"day{d['day']}" / fname[s['id']], session_page(d, s, tl_s, sl_s, el_up))
            kind = kinds[s.get('kind', 'talk')] if real(s['id']) else 'Not recorded'
            days_md.append(f"| {s['time'] or '—'} | [{cell(s['title'])}](day{d['day']}/{fname[s['id']]}) | {cell(spk_text(s)) or '—'} | {kind} | "
                           f"{', '.join(cover[x] for x in s['coverage'])} | {n_cl[s['id']]} |")
        days_md.append('')
    body = over + ['', '*Sessions*: the slots on the agenda. *Claims*: every public claim filed under the day, including documentation, press and analysis '
                   'notes on its sessions and the points from sessions that were not recorded.', ''] + days_md + [
        '## How to use it', '',
        '- Each session page lists the claims captured from it in running order, with every audience question followed by its answer, and the topics it covered.',
        "- *Coverage* says what was captured: slide photos (*Slides*, *One slide*), the author's *Notes*, a *Transcript* or a *Video* clip. "
        '*None* means nothing was captured, so the knowledge base cannot say what was said there.',
        '- *Day N, session not recorded* collects the points whose session is not known.', '',
        'The material behind these pages (slide photos, recordings, transcripts and notes) is private and never enters git. '
        'The pages hold paraphrased claims and short quotations only. See [PRIVACY.md](../PRIVACY.md).', ''] + generated_note(
        '`_system/build_kb.py`', '`20-claims/sessions.yaml` or the claims in `20-claims/`')
    write(SD / 'README.md', readme(1, root_link('../') + [('40-sessions', None)], GEN, 'Sessions',
                                   '**Every session of the event in running order, with the claims captured from it.**',
                                   body, pipeline_nav('40-sessions', '../'), art='40-sessions'))

    # ---------------- 50-maps
    M = root / '50-maps'
    M.mkdir(exist_ok=True)
    tl_m = lambda t: f"../30-topics/{area_of[t]['id']}/{t}.md"
    sl_m = lambda sid: f"../40-sessions/day{S[sid]['day']}/{fname[sid]}"
    tree = [GEN, '# Topic tree\n']
    mm = ['---', 'title: Search Central Live Deep Dive Europe 2026', 'markmap:', '  colorFreezeLevel: 2', '  initialExpandLevel: 2', '---', '',
          '# Search Central Live Deep Dive Europe 2026', '']
    for a in areas:
        tree.append(f"- **{md(a['title'])}** ({sum(len(by_topic.get(t['id'], [])) for t in a['topics'])} claims)")
        mm.append(f"## {md(a['title'])}")
        for t in a['topics']:
            cs = by_topic.get(t['id'], [])
            es = tstats(cs)['event_sessions']
            tree.append(f"  - [{md(t['title'])}](../30-topics/{a['id']}/{t['id']}.md) — {len(cs)} claims, event sessions: {', '.join(es) or 'none'}")
            mm.append(f"### {md(t['title'])} ({len(cs)})")
            for c in cs:
                if is_ev(c):
                    x = nt(c['text'])
                    mm.append(f"- {md(x[:110] + ('…' if len(x) > 110 else ''))}")
        mm.append('')
    write(M / 'topic-tree.md', '\n'.join(tree) + '\n')
    write(M / 'mindmap.markmap.md', '\n'.join(mm) + '\n')

    # mention matrix: event claims (slide/stage) per topic and session; S00 shown, never counted as a session
    short = lambda sid: re.sub(r'^D(\d+)-', r'\1·', sid)
    ev_sess = sorted({c['s'] for c in public if is_ev(c)}, key=order.get)
    rows = []
    for a in areas:
        for t in a['topics']:
            cs = by_topic.get(t['id'], [])
            st = tstats(cs)
            rows.append({'a': a, 't': t, 'cnt': Counter(c['s'] for c in cs if is_ev(c)), 'all': len(cs), 'allc': Counter(day(c) for c in cs),
                         'ev': sum(1 for c in cs if is_ev(c)), 'es': st['event_sessions'], 'ed': st['event_days']})
    buf = io.StringIO(newline='')
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['area', 'topic', 'topic_id'] + ev_sess + ['event_claims', 'all_claims', 'event_sessions', 'event_days'])
    for r in rows: w.writerow([r['a']['title'], r['t']['title'], r['t']['id']] + [r['cnt'].get(s, 0) for s in ev_sess] + [r['ev'], r['all'], len(r['es']), len(r['ed'])])
    write(M / 'mention-matrix.csv', buf.getvalue())
    mx = [GEN, '# Mention matrix\n',
          'How often each topic was raised at the event, by Google or a community speaker: counts of slide and stage claims only. Documentation, press and analysis '
          'notes appear only in the "All claims" column. A topic raised in several sessions is one the event kept returning to. `S00` collects points whose session was not recorded: it is shown, but never counted as a session.\n',
          '## Across days\n',
          '| Topic | ' + ' | '.join(f'Day {n}' for n in used_days) + ' | Days | Sessions | Event claims | All claims |',
          '| --- | ' + ' | '.join('---:' for _ in used_days) + ' | ---: | ---: | ---: | ---: |']
    for r in sorted(rows, key=lambda r: (-len(r['ed']), -len(r['es']), -r['ev'], -r['all'])):
        dn = Counter(day(c) for c in by_topic.get(r['t']['id'], []) if is_ev(c))
        mx.append(f"| {cell(r['t']['title'])} | " + ' | '.join(str(dn[n]) if dn[n] else '' for n in used_days) + f" | {len(r['ed'])} | {len(r['es'])} | {r['ev']} | {r['all']} |")
    for n in used_days:
        cols = [s for s in ev_sess if S[s]['day'] == n]
        mx += ['', f"## Day {n} — {md(DAYS[n]['theme'])} ({DAYS[n]['date']})", '',
               '| Topic | ' + ' | '.join(short(s) for s in cols) + ' | Event claims | Sessions | All claims |',
               '| --- | ' + ' | '.join('---:' for _ in cols) + ' | ---: | ---: | ---: |']
        drows = []
        for r in rows:
            if not r['allc'].get(n): continue
            k = [r['cnt'].get(s, 0) for s in cols]
            drows.append((-sum(1 for s, x in zip(cols, k) if x and real(s)), -sum(k), -r['allc'][n], r, k))
        for ns, ne, na, r, k in sorted(drows, key=lambda x: x[:3]):
            mx.append(f"| {cell(r['t']['title'])} | " + ' | '.join(str(x) if x else '' for x in k) + f" | {-ne} | {-ns} | {-na} |")
        mx += ['', 'Session key:', ''] + [f"- `{s}` {md(S[s]['title'])} ({md(spk_text(S[s])) or 'n/a'})" for s in cols]
    write(M / 'mention-matrix.md', '\n'.join(mx) + '\n')

    # verification report, grouped by day
    def vtable(cs):
        vc = Counter(c['ver'] for c in cs)
        return ['| Status | Claims | Meaning |', '| --- | ---: | --- |',
                f"| Confirmed | {vc.get('confirmed', 0)} | The documentation says the same thing |",
                f"| Consistent | {vc.get('consistent', 0)} | The documentation supports it without stating it directly |",
                f"| Not in docs | {vc.get('undocumented', 0)} | Said or shown at the event, by Google or a community speaker, but not in Google's documentation |",
                f"| Not checkable | {vc.get('n/a', 0)} | Nothing to verify: quotations, framing, agenda facts, audience questions, opinions |", '']
    lab = Counter(c['label'] for c in public)
    stage = [c for c in public if is_ev(c)]
    vr = [GEN, '# Verification report\n',
          f"{len(public)} public claims: " + ', '.join(f"{lab[k]} {LABELS[k]}" for k in LABELS if lab[k]) + '.\n',
          f"Version {version}, data through {through_txt}. Docs claims are Google's documentation itself; press claims are third-party reports of what Google said, not documentation.\n"]
    if len(used_days) > 1: vr += ["## All days: how the event claims stand against Google's documentation\n"] + vtable(stage)
    for n in used_days:
        ds = [c for c in stage if day(c) == n]
        vr += [f"## Day {n} — {md(DAYS[n]['theme'])} ({DAYS[n]['date']})", ''] + vtable(ds)
        und = [c for c in ds if c['ver'] == 'undocumented']
        if und:
            vr += ["### Said at the event but not in Google's documentation", '',
                   'These are the most valuable and the most fragile claims: quote them as "said at Search Central Live", not as documented policy.', '']
            vr += [claim_md(c, sl_m) for c in und]
    write(M / 'verification-report.md', '\n'.join(vr) + '\n')

    # links between claims (rel), by type
    links = [(c, r) for c in public for r in c.get('rel', [])]
    ad = [GEN, '# Links between claims\n',
          'How claims relate across sessions and days: a later claim that repeats, extends, contradicts or updates an earlier one, and answers to audience questions. '
          'Each link is set with `rel` on the later claim in `20-claims/`.\n']
    if not links: ad.append('No links yet.\n')
    for typ, (verb, _) in REL.items():
        g = [(c, r) for c, r in links if r['type'] == typ]
        if not g: continue
        ad += [f'## {verb} ({len(g)})', '']
        for c, r in g:
            o = CL[r['to']]
            ad += [f"- [`{c['id']}`]({sl_m(c['s'])}) ({where(c)}) {verb.lower()} [`{o['id']}`]({sl_m(o['s'])}) ({where(o)})",
                   f"  - `{c['id']}` **[{LABELS[c['label']]}]** {md(c['text'])}", f"  - `{o['id']}` **[{LABELS[o['label']]}]** {md(o['text'])}"]
        ad.append('')
    write(M / 'across-days.md', '\n'.join(ad) + '\n')

    # interactive mindmap
    data = {'title': kb['event'].get('name', ''), 'version': version, 'data_through': through_txt,
            'days': [{'day': d['day'], 'date': d['date'], 'theme': d['theme'], 'claims': sum(1 for c in public if day(c) == d['day'])} for d in kb['days']],
            'areas': []}
    for a in areas:
        A = {'id': a['id'], 'title': a['title'], 'blurb': nt(a['blurb']), 'topics': []}
        for t in a['topics']:
            cs = by_topic.get(t['id'], [])
            A['topics'].append({'id': t['id'], 'title': t['title'], 'summary': nt(t['summary']), 'cites': t.get('cites', []), 'do': [nt(x) for x in t.get('do', [])],
                                # its top things, each a link into the Reef map (graph.html#ent:<id>)
                                'things': [{'id': x['id'], 'name': EN['by_id'][x['id']]['name'], 'n': x['count']} for x in EN['topic_entities'].get(t['id'], [])[:8]],
                                'claims': [{'id': c['id'], 'label': c['label'], 'text': nt(c['text']), 'quote': nt(c.get('quote') or ''), 'ver': ver_text(c),
                                            'sid': c['s'], 'session': S[c['s']]['title'], 'day': day(c), 'where': where(c, str), 'by': by(c),
                                            'rel': [f"{REL[r['type']][0]} {r['to']}" for r in c.get('rel', [])] + [f"{REL[r['type']][1]} {r['from']}" for r in rfrom.get(c['id'], [])],
                                            'src': [{'t': sources[k]['title'], 'u': sources[k]['url']} for k in c.get('src', [])]} for c in cs]})
        data['areas'].append(A)
    tpl = (root / '_system' / 'templates' / 'mindmap.template.html').read_text(encoding='utf-8')
    style = kb.get('style', 'art-deco')
    # the tab icon of the style: the template has the Deep Dive one in href and the Art Deco one in data-deco; the page keeps one
    tpl = re.sub(r'<link rel="icon" type="image/svg\+xml" href="([^"]*)" data-deco="([^"]*)">',
                 lambda m: f'<link rel="icon" type="image/svg+xml" href="{m[2] if style == "art-deco" else m[1]}">', tpl, count=1)
    write(M / 'mindmap.html', tpl.replace('/*STYLE*/', style, 1).replace('/*DATA*/null', js_json(data)))  # style first: the data may hold any text

    # the entity index: the review list of the things (read the previous one first for the drift note)
    old = (M / 'entity-index.md').read_text(encoding='utf-8') if (M / 'entity-index.md').exists() else ''
    write(M / 'entity-index.md', entity_index(kb, EN, {'version': version, 'through_txt': through_txt}, fname) + '\n')
    drifted = drift(old, EN)

    # 50-maps/README.md
    vc, pct = Counter(c['ver'] for c in stage), kb['badge_stats']['docs_backed_pct']
    body = ["## What's here", '', '| Map | What it shows |', '| --- | --- |',
            '| [Topic tree](topic-tree.md) | Every area and topic with its claim count and the sessions that raised it on a slide or on stage. |',
            '| [Mindmap](mindmap.html) | The interactive map of every area and topic: pick a day, filter, and open a topic to read its summary, what to do '
            'and every claim with its label, verification and sources. |',
            '| Reef map (`graph.html`) | The things, topics, kit items, documents and claims as a map of links, one neighbourhood at a time ("Graph" in the Art Deco style): '
            'click a bubble to put it in the centre, the back button returns; drag to pan or move bubbles, scroll to zoom, right-click for more. Written by the web edition build (`_system/site/build_site.py`), with its data inline. |',
            '| [Mindmap as Markdown](mindmap.markmap.md) | The same tree for markmap tools, with the slide and stage claims under each topic, each cut to at most 110 characters. |',
            '| [Mention matrix](mention-matrix.md) · [CSV](mention-matrix.csv) | How often each topic was raised at the event: slide and stage claims per topic, '
            'across days and per session. The CSV holds the per-session counts for a spreadsheet. |',
            "| [Verification report](verification-report.md) | How the slide and stage claims stand against Google's documentation, day by day, and every claim "
            'that was said at the event but is not in the documentation. |',
            '| [Links between claims](across-days.md) | Where a later claim repeats, extends, contradicts or updates an earlier one, and the answers to audience questions. |',
            f"| [Entity index](entity-index.md) | The review list of the things (`20-claims/entities.yaml`): {len(EN['list'])} things, how often each is mentioned, "
            'the words that matched, and a fixed sample of 100 mentions to check that the matching is right. |',
            "| [Differences ledger](differences.md) | Where the event and Google's documentation differ and what to follow (the rows of "
            '`25-kits/differences.yaml`), then the claims linked as contradicting or updating and the claims that say they are uncertain. '
            'Written by `_system/kits.py`, like the copy in the developer kit. |'] + ([] if community(kb) else [
            '| [Numbers registry](numbers.md) | Every figure of the media kit (the facts marked `use: stat`) with its scope, claims, status and credit, then the '
            'figures in the claims that no fact cites yet: candidates for the kit. Written by `_system/kits.py`. |']) + ['',
            '## At a glance', '', f'Version {version}, data through {through_txt}.', '', '| Public claims | Count |', '| --- | ---: |',
            f'| All public claims | {len(public)} |', f'| Shown or said at the event (slide and stage) | {len(stage)} |',
            f"| … confirmed by Google's documentation | {vc['confirmed']} |", f"| … consistent with the documentation | {vc['consistent']} |",
            f"| … not in Google's documentation | {vc['undocumented']} |", f"| … with nothing to verify | {vc['n/a']} |",
            f'| Links between claims | {len(links)} |', '',
            f"The *docs-backed* badge shows {pct}%: the share of confirmed and consistent claims among the event claims graded confirmed, consistent "
            'or not in the documentation.', '',
            '## Opening the mindmap', '',
            '> [!TIP]', '> GitHub shows `.html` files as source code. Download or clone the repository and double-click `50-maps/mindmap.html`: it opens in any '
            'browser, with no server and no internet connection. The web edition carries the same map as `60-outputs/site/mindmap.html`.', '',
            '- **Day chips** show one day or all of them; the **filter box** keeps the topics whose title, summary or claims match.',
            '- **Click an area** to fold it, or use **Collapse all**. **Click a topic**, or tab to it and press Enter, to read it in the side panel; the arrow keys move between nodes.',
            '- A bigger circle means more claims; a filled circle means the topic was raised on a slide or on stage in more than one session.',
            '- A topic\'s panel lists its top things under **Things in this topic**; each one, like the **Reef map** link in the header, opens `graph.html`, '
            'the map of links that the web edition build writes next to this file. The Reef map\'s topic nodes link back here.',
            '- ' + STYLE_TEXT[kb.get('style', 'art-deco')]['mindmap'] + ' It links back to the web edition.', ''] + generated_note(
            '`_system/build_kb.py`', 'the claims in `20-claims/` (the mindmap page itself: `_system/templates/mindmap.template.html`)')
    maps_lead = ('**Eight views across the days covered so far: the topic tree, the interactive mindmap, the Reef map of links, the mention matrix, the verification '
                 'report, the links between claims, the entity index (the review list of the things the event talked about) and the differences ledger.**'
                 if community(kb) else
                 '**Nine views across the days covered so far: the topic tree, the interactive mindmap, the Reef map of links, the mention matrix, the verification report, '
                 'the links between claims, the entity index (the review list of the things the event talked about), the differences ledger and the numbers registry.**')
    write(M / 'README.md', readme(1, root_link('../') + [('50-maps', None)], GEN, 'Maps', maps_lead, body, pipeline_nav('50-maps', '../'), art='50-maps'))

    # ---------------- 60-outputs/agent-pack (public claims only)
    P = root / '60-outputs' / 'agent-pack'
    fresh(P)
    src_rec = lambda k: {'title': sources[k]['title'], 'url': sources[k]['url'], 'publisher': sources[k]['publisher'],
                         'kind': sources[k].get('kind') or 'google', 'checked': str(sources[k]['checked'])}
    with open(P / 'claims.jsonl', 'w', encoding='utf-8', newline='\n') as f:
        for c in public:
            s = S[c['s']]
            f.write(json.dumps({'id': c['id'], 'day': s['day'], 'session_id': c['s'], 'session': s['title'], 'speaker': speaker(c),
                                'who': c.get('who'), 'author': None if is_ev(c) else AUTHOR if c['label'] == 'analysis' else by(c),
                                'label': c['label'], 'label_meaning': LABEL_HELP[c['label']], 'text': nt(c['text']), 'quote': nt(c.get('quote') or ''),
                                'quote_checked': c.get('quote_checked') is True, 'verification': c['ver'], 'topics': c['topics'],
                                'sources': [{'key': k, **src_rec(k)} for k in c.get('src', [])], 'evidence': ev_list(c),
                                'relations': [{'type': r['type'], 'to': r['to']} for r in c.get('rel', [])], 'related_from': rfrom.get(c['id'], []),
                                'used_by': used_by.get(c['id'], []), 'mentions': EN['by_claim'].get(c['id'], [])},
                               ensure_ascii=False) + '\n')
    write(P / 'claims.schema.json', json.dumps(claim_schema(), indent=2, ensure_ascii=False) + '\n')
    tj = {'version': version, 'data_through': through, 'areas': []}
    for a in areas:
        tj['areas'].append({'id': a['id'], 'title': a['title'], 'blurb': nt(a['blurb']), 'topics': [
            {'id': t['id'], 'title': t['title'], 'summary': nt(t['summary']), 'cites': t.get('cites', []), 'do': [nt(x) for x in t.get('do', [])],
             'related': t.get('related', []), 'claim_ids': [c['id'] for c in by_topic.get(t['id'], [])],
             **{k: tstats(by_topic.get(t['id'], []))[k] for k in ('sessions', 'days', 'event_sessions', 'event_days')}}
            for t in a['topics']]})
    write(P / 'topics.json', json.dumps(tj, indent=2, ensure_ascii=False) + '\n')
    sj = {'version': version, 'data_through': through, 'event': {k: str(kb['event'].get(k, '')) for k in ('name', 'city', 'dates')}, 'days': [
        {'day': d['day'], 'date': d['date'], 'theme': d['theme'], 'sessions': [
            {'id': s['id'], 'time': s['time'], 'title': s['title'], 'speakers': speakers(s), 'role': s.get('role'),
             'kind': 'unrecorded' if not real(s['id']) else s.get('kind', 'talk'), 'coverage': s['coverage'], 'note': s.get('note'),
             'claim_count': sum(1 for c in public if c['s'] == s['id']), 'topics': list(dict.fromkeys(t for c in public if c['s'] == s['id'] for t in c['topics']))}
            for s in d['sessions']]} for d in kb['days']]}
    write(P / 'sessions.json', json.dumps(sj, indent=2, ensure_ascii=False) + '\n')
    write(P / 'sources.json', json.dumps({k: src_rec(k) for k in sources if k not in private_only}, indent=2, ensure_ascii=False))
    graph, links = pack_graph(kb, KI, fname, private_only, EN)
    meta = {'version': version, 'through': through, 'through_txt': through_txt}
    write(P / 'entities.json', json.dumps(entities_json(EN, meta), indent=1, ensure_ascii=False) + '\n')
    for x in EN['list']: write(P / 'entities' / f"{x['id']}.md", entity_card(x, kb, EN, KI, fname))
    write(P / 'graph.json', graph_json(graph))
    write(P / 'links.json', json.dumps(links, indent=1, ensure_ascii=False) + '\n')
    for a in areas:
        for t in a['topics']: write(P / 'topics' / f"{t['id']}.md", topic_page(a, t, lambda r: f'{r}.md', lambda sid: f'../sessions/{fname[sid]}', el_pack))
    for d in kb['days']:
        for s in d['sessions']: write(P / 'sessions' / fname[s['id']], session_page(d, s, lambda t: f'../topics/{t}.md', lambda sid: fname[sid], el_pack))
    n_top = sum(1 for t in topics if by_topic.get(t))
    n_ses = sum(1 for s in S if any(c['s'] == s for c in public))
    nocov = [s for d in kb['days'] for s in d['sessions'] if 'none' in s['coverage'] and real(s['id']) and s.get('kind') != 'break']
    ix = ['# Search Central Live Deep Dive Europe 2026 — knowledge base index', '',
          f"Version {version} · data through {through_txt}. {len(public)} claims across {n_top} topics in {len(areas)} areas; "
          f"{n_ses} of {len(S)} sessions have claims, on {len(used_days)} of {len(kb['days'])} days. Read [`AGENTS.md`](AGENTS.md) first.", '',
          'In the knowledge base folder, `python _system/kb_query.py search "your question"` answers from this pack alone, with a citation for every '
          'claim (`about`, `entity`, `neighbours`, `claims`, `evidence` and `cite` too; see "Ask it from the command line" in `AGENTS.md`). People double-click `ask.bat`.', '',
          '## Files', '', '| File | What it holds |', '| --- | --- |',
          '| [`AGENTS.md`](AGENTS.md) | How to answer from this pack. Read it first. |',
          '| [`INDEX.md`](INDEX.md) | This file: every topic with its summary. |',
          f'| [`claims.jsonl`](claims.jsonl) | Every public claim, one JSON object per line ({len(public)}). |',
          '| [`claims.schema.json`](claims.schema.json) | JSON Schema (2020-12) for one line of `claims.jsonl`. |',
          '| [`topics.json`](topics.json) | Areas and topics: summary, cited claims, actions, related topics, claim ids, sessions and days. |',
          '| [`sessions.json`](sessions.json) | Days and sessions: time, speakers, kind, coverage, claim count, topics. |',
          '| [`sources.json`](sources.json) | The documents cited, with publisher, kind (google or press) and the date each was checked. |',
          '| [`dev-requirements.json`](dev-requirements.json) | The developer kit: requirements by area (level, why, how, test, status), code snippets, cited claims and Google pages. |',
          ('| [`content-library.json`](content-library.json) | The open part of the content kit: the wording rules, the glossary and a short preview of the '
           'media kit (facts, myths, a story angle and quotes), with claim texts and source URLs. The full media kit is not part of this community edition. |'
           if community(kb) else
           '| [`content-library.json`](content-library.json) | The content kit: wording rules, facts, myths, story angles, quotes and glossary, with claim texts and source URLs. |'),
          f"| [`topics/<topic-id>.md`](topics/) | One page per topic ({len(topics)}). |",
          f"| [`sessions/<session-id>-*.md`](sessions/) | One page per session ({len(S)}). |",
          f"| [`graph.json`](graph.json) | Every link that exists between claims, topics, areas, sessions, days, sources and kit items, as one graph: "
          f"{len(graph['nodes'])} nodes and {len(graph['edges'])} edges (see \"The graph\" below). |",
          '| [`links.json`](links.json) | Lookup tables built from the same links: what rests on each claim, the kit items per topic, the claims per '
          'source by grade, the spellings of the glossary terms and things, and the speaker each claim is proven to be by. |',
          "| [`differences.json`](differences.json) | The differences ledger: where the event and Google's documentation differ, with the event, docs and "
          'analysis claims of each row and what to follow; then the claims linked by `contradicts` or `updates`, and the claims whose text says they are uncertain. |']
    if not community(kb):  # the numbers registry and the question bank belong to the full media kit
        ix += ['| [`numbers.json`](numbers.json) | The numbers registry: every stat fact of the content kit with its figures, wording (its scope), status, credit, '
               'claims and things; then the claims with a figure that no stat fact cites. |',
               '| [`question-bank.json`](question-bank.json) | The question bank: the audience questions with their answers and grades, and per thing "What did '
               'Google say about it?" with its top documented and event-only claims. Every claim carries its `cite`. |']
    if EN['list']:
        ix += [f"| [`entities.json`](entities.json) | The things the event talked about ({len(EN['list'])}), each with its aliases, summary, the claims that "
               'mention it (with a citation each), its Google pages, relations, the things mentioned with it, its topics and kit items. |',
               f"| [`entities/<id>.md`](entities/) | One short card per thing ({len(EN['list'])}), the same as Markdown (see \"Things\" below). |"]
    ix += ['',
          '## The graph', '',
          '`graph.json` holds `nodes` (`{id, kind, name, url}`; a claim also carries `label`, `ver` and `day`) and `edges` (`{from, to, type}`), '
          'sorted, every end a node. An id is `<kind>:<id>`: `claim:D1-C108`, `topic:robots-txt`, `area:crawling`, `session:D1-S07`, `day:1`, '
          '`source:<key>`, `req:DEV-SRV-01`, `fact:F-012`, `myth:M-003`, `quote:Q-088`, `angle:A-007` and `term:<id>` (a glossary term, its `id` in '
          '`content-library.json`) and `ent:<id>` (a thing of `entities.json`, with its `entity_kind`). `url` is the pack file that holds the node; '
          'for a source, its own URL. An edge may carry more fields: `via` and `field` (`mentions`), `count` (`about`, `features`, `co-mentioned`), '
          '`own` (`about`) and `claims` (`co-mentioned` and the factual relations between things: the claim ids to cite). A node or an edge is a map, not a '
          'source: cite the claim ids behind it.', '',
          '| Edge type | From → to | Count | Meaning |', '| --- | --- | ---: | --- |']
    ix += [f"| `{t}` | {', '.join(f'{a} → {b}' for a, b in e['ends'])} | {e['count']} | {md(e['about'])} |" for t, e in graph['edge_types'].items()]
    ix += ['', 'What rests on a claim: its `used_by` in `claims.jsonl`, or the `rests-on` edges that end at it. The requirements and facts of a topic: '
           "`topic_items` in `links.json`, or the kit items whose `rests-on` edges end at the topic's claims. Everything about a thing: its card, "
           'or the `mentions` edges that end at it, then the `rests-on` edges that end at those claims.', '']
    if EN['list']:
        n_m = sum(len(m) for m in EN['by_claim'].values())
        ix += ['## Things', '', f"{len(EN['list'])} things the event talked about, matched in the claims by name and alias ({n_m} mentions in "
               f"{len(EN['by_claim'])} claims; `mentions` in `claims.jsonl`). Each has a card in [`entities/`](entities/) and in `entities.json`. A card is a map, "
               'not a source: cite the claim ids it lists.', '']
        for k, (label, _) in ENTITY_KINDS.items():
            xs = [x for x in EN['list'] if x['kind'] == k]
            if xs: ix += [f'### {label}s ({len(xs)})', ''] + [f"- [{md(x['name'])}](entities/{x['id']}.md) ({len(x['claims'])}): {md(x['summary'])}" for x in xs] + ['']
    ix += ['## Sessions with no coverage', '']
    ix += ([f"- `{s['id']}` Day {s['day']}, {s['time'] or 'time not recorded'}: {md(s['title'])} ({md(spk_text(s)) or 'speaker not recorded'}). Nothing was captured, so this pack cannot say what was said there."
            for s in nocov] or ['Every session has some coverage.']) + ['']
    for a in areas:
        ix += [f"## {md(a['title'])}", '', md(a['blurb']), '']
        ix += [f"- [{md(t['title'])}](topics/{t['id']}.md): {md(t['summary'])}" + (f" Based on: {', '.join(t['cites'])}." if t.get('cites') else '') for t in a['topics']] + ['']
    write(P / 'INDEX.md', '\n'.join(ix))
    # AGENTS.md: the template, with the blocks of the other edition left out (bytes in, bytes out: a template without markers is a plain copy)
    agents = (root / '_system' / 'templates' / 'AGENTS.md').read_bytes().decode('utf-8')
    (P / 'AGENTS.md').write_bytes(edition_text(agents, kb['edition']['edition']).encode('utf-8'))

    # ---------------- 25-kits -> 60-outputs/dev, 60-outputs/content and the kit files of the agent pack
    k, ns = kits()
    k.build(root, kb, ns, {'version': version, 'through': through, 'through_txt': through_txt})

    # ---------------- 60-outputs/badges (drawn and checked in load()) and 60-outputs/README.md
    O = root / '60-outputs'
    fresh(O / 'badges')
    for name, svg in sorted(kb.get('badges', {}).items()): write(O / 'badges' / name, svg)
    st = kb['badge_stats']
    shows = {'version': f"{st['version']}, data through {st['data_through'] or 'no claims yet'}: the top `CHANGELOG.md` entry and the last day with claims",
             'days': f"{st['days_done']} of {st['days_total']} event days have claims",
             'claims': f"{st['claims']} public claims; private claims never count",
             'docs-backed': f"{st['docs_backed_pct']}% of the slide and stage claims graded against the docs are confirmed or consistent",
             'topics': f"{st['topics']} topics", 'sources': f"{st['sources']} sources: the Google pages and press reports in `agent-pack/sources.json`",
             'dev-kit': f"{st['requirements']} requirements in the developer kit", 'media-kit': f"{st['facts']} facts in the media kit",
             'privacy': 'Private material is left out of every shared output: see [PRIVACY.md](../PRIVACY.md)'}
    if community(kb): shows['media-kit'] = 'Media kit: full edition on request; this community edition holds the wording rules, the glossary and a short preview'
    body = ["## What's here", '', '| Folder | What it is | For |', '| --- | --- | --- |',
            '| [`site/`](site/index.html) | **Web edition**: every day, topic, thing and claim, with search | Anyone reading |',
            '| [`pdf/`](pdf/README.md) | **Field guides**: a PDF per day in Deep Dive, the main edition, kept current; the classic Art Deco and modern editions are frozen at v2.4.0' + (' ([what they lack](pdf/classic-editions-log.md))' if (root / '60-outputs' / 'pdf' / 'classic-editions-log.md').exists() else '') + ' | Reading and printing |',
            f"| [`dev/`](dev/README.md) | **Developer kit**: {st['requirements']} requirements, a ticket CSV, snippets, the differences ledger | Developers |",
            ('| [`content/`](content/README.md) | **Media kit**: the wording rules, the glossary and a short preview; the full kit is not part of this '
             'community edition | Content and media teams |' if community(kb) else
             f"| [`content/`](content/README.md) | **Media kit**: {st['facts']} facts, myths, angles, quotes, glossary, the question bank | Content and media teams |"),
            '| [`agent-pack/`](agent-pack/INDEX.md) | **Agent pack**: the claims, topics, things and kits as JSON, and the links between them as a graph | AI agents |',
            '| [`badges/`](badges/) | **Badges**: the status badges the README pages show | The README pages |', '']
    if community(kb):
        body += ['The web edition holds every area, session and claim too, a card for each thing the event talked about, the developer kit, the glossary and the field guides. '
                 'It works offline and carries its own copy of the PDFs, so `site/` can be shared on its own. The developer kit adds a pre-launch checklist and the '
                 "differences ledger (`dev/differences.md`: where the event and Google's documentation differ, and what to follow), also a page of the web edition. "
                 'The media kit keeps its wording rules and glossary open, with a short preview of the full kit, which is not part of this community edition. '
                 'The agent pack holds claims, topics, sessions, sources, the developer kit and the open part of the content kit as JSON and Markdown, '
                 'the links between them as one graph (`graph.json`, with lookup tables in `links.json`), a card for each thing the event talked about '
                 '(`entities.json`), the differences ledger (`differences.json`) and instructions in `AGENTS.md`: '
                 'hand the folder over as it is. In the knowledge base folder, `ask.bat` (for people) and `python _system/kb_query.py` (for AI agents) '
                 'answer questions from the pack alone, with a citation for every claim.', '']
    else:
        body += ['The web edition holds every area, session and claim too, a card for each thing the event talked about, both kits and the field guides. It works offline and carries its own copy '
                 'of the PDFs, so `site/` can be shared on its own. The developer kit adds a pre-launch checklist and the media kit its wording rules '
                 'and a JSON library for AI writing tools. Three ledgers sit with them: the differences ledger (`dev/differences.md`: where the event and '
                 "Google's documentation differ, and what to follow), the question bank (`content/questions.md`) and the numbers registry "
                 '([`50-maps/numbers.md`](../50-maps/numbers.md)), each also a page of the web edition. The agent pack holds claims, topics, sessions, sources and both kits as JSON and Markdown, '
                 'the links between them as one graph (`graph.json`, with lookup tables in `links.json`), a card for each thing the event talked about '
                 '(`entities.json`), the three ledgers (`differences.json`, `numbers.json`, `question-bank.json`) and instructions in `AGENTS.md`: '
                 'hand the folder over as it is. In the knowledge base folder, `ask.bat` (for people) and `python _system/kb_query.py` (for AI agents) '
                 'answer questions from the pack alone, with a citation for every claim.', '']
    body += [
            '> [!TIP]', '> GitHub shows `.html` files as source code. To read the web edition, download or clone the repository and double-click '
            '`60-outputs/site/index.html`.', '',
            '## How it is made', '', '| Folder | Built by | From |', '| --- | --- | --- |',
            '| `site/` | `_system/site/build_site.py` | The agent pack, the field guides and the mindmap |',
            "| `pdf/` | `_system/pdf/make_pdf.py` | The day's template in `_system/pdf/` and the agent pack |",
            '| `dev/`, `content/` | `_system/kits.py`, run by `_system/build_kb.py` | `25-kits/` and the claims |',
            '| `agent-pack/` | `_system/build_kb.py` | `20-claims/`, `25-kits/` and `_system/templates/AGENTS.md` |',
            '| `badges/` | `_system/badges.py`, run by `_system/build_kb.py` | The claims, the kits and `CHANGELOG.md` |', '',
            '`rebuild.bat` runs them in order: the knowledge base, then the field guides, then the web edition.', '',
            '## Badges', '', badge_row('badges/', ['version', 'days', 'claims'], ['docs-backed', 'topics', 'sources'], ['dev-kit', 'media-kit', 'privacy'],
                                       alt=BADGE_ALT_COMMUNITY if community(kb) else BADGE_ALT), '',
            'The build draws these badges, which also head the [knowledge base README](../README.md), from the data every time it runs, so they '
            'always match the pages. They take the default style of `_system/theme.yaml`: ' + STYLE_TEXT[kb.get('style', 'art-deco')]['badges'] + '.', '', '| Badge | Shows |', '| --- | --- |'] + [f'| `{n}.svg` | {shows[n]} |' for n in BADGES] + ['',
            '*Graded against the docs* means graded confirmed, consistent or undocumented; a claim with nothing to verify (n/a) does not count.', '',
            'Everything here is built from public claims only: a claim marked `private: true` never reaches this folder, and no slide '
            'photo, recording or transcript is ever included. See [PRIVACY.md](../PRIVACY.md).', ''] + generated_note(
            'the scripts above', '`20-claims/`, `25-kits/` or the day templates in `_system/pdf/`')
    write(O / 'README.md', readme(1, root_link('../') + [('60-outputs', None)], GEN, 'Outputs',
                                  ('**Everything the knowledge base produces: the web edition, the field guides, a kit for developers, the glossary and a preview of the '
                                   'media kit for content teams, a pack for AI agents and the status badges.**\n\n' if community(kb) else
                                   '**Everything the knowledge base produces: the web edition, the field guides, a kit for developers, a kit for content teams, '
                                   'a pack for AI agents and the status badges.**\n\n') + f'Version {version} · data through {through_txt}.',
                                  body, pipeline_nav('60-outputs', '../'), art='60-outputs'))

    # ---------------- 70-private
    pm = [GEN, '# Private claims\n', 'Claims marked `private: true`. They are left out of every shared output.\n']
    CL.update({c['id']: c for c in private})
    pm += [claim_md(c, lambda sid: f"../40-sessions/day{S[sid]['day']}/{fname[sid]}") for c in private]
    write(root / '70-private' / 'private-claims.md', '\n'.join(pm) + '\n')

    print(f"OK: {len(claims)} claims ({len(private)} private), {len(topics)} topics, {len(S)} sessions. Version {version}, data through {through_txt}.")
    bare = [a['id'] for a in areas if f"30-topics-{a['id']}" not in ILLUSTRATION_ALT]
    if bare: print('Topic areas without a README illustration (draw one in _system/brand/illus_*.py, add it to ILLUSTRATION_ALT):', ', '.join(bare))
    empty = [t for t in topics if not by_topic.get(t)]
    if empty: print('Topics with no claims:', ', '.join(empty))
    if EN['list']:
        n_m = sum(len(m) for m in EN['by_claim'].values())
        pins = sum(1 for m in EN['by_claim'].values() for y in m if y['field'] == 'pin')
        print(f"OK: things: {len(EN['list'])} things, {n_m} mentions in {len(EN['by_claim'])} of {len(public)} public claims ({pins} pinned); "
              f"review 50-maps/entity-index.md (git diff shows the new mentions).")
        print('Mentions per thing: ' + ', '.join(f"{x['id']} {len(x['claims'])}" for x in sorted(EN['list'], key=lambda x: (-len(x['claims']), x['id']))))
        for eid, s, was, now in drifted:
            print(f'NOTE: the spelling "{s}" of {eid} now matches {now} claims (before: {"new" if was is None else was}); check its mentions in 50-maps/entity-index.md')


def main(argv):
    for f in (sys.stdout, sys.stderr): f.reconfigure(errors='backslashreplace')
    root = Path(argv[argv.index('--root') + 1]).resolve() if '--root' in argv else ROOT
    kb, E, W = load(root)
    for w in W: print('WARNING:', w)
    if '--stoplist' in argv and kb.get('stop_words'):
        print(f'Stop list: the {STOP_N} most frequent words of the public claims, most frequent first. An alias of 20-claims/entities.yaml that is one '
              'of these words must be scoped ({s, in: [topics]}) or exact ({s, exact: true}):\n' + ', '.join(kb['stop_words']))
    lp = long_paths(root, kb) if not E and sys.platform == 'win32' and not windows_long_paths_enabled() else []
    if lp:
        E.append(f'{len(lp)} output path(s) would reach the Windows limit of 260 characters, the longest {len(lp[0])}: {lp[0]}. '
                 'Move the repository to a shorter folder path (or enable Windows long paths) and run again.')
    if E:
        print('\n'.join('ERROR: ' + e for e in E))
        sys.exit(f'{len(E)} validation error(s). Nothing was written.')
    if '--check' in argv:
        print(f"OK: validation passed ({len(kb['claims'])} claims, {len(W)} warnings). Nothing was written (--check).")
        return
    build(root, kb)
    leaks = scan_shared(root)
    if leaks:
        print('\n'.join(f'ERROR: {p} names an excluded photo ({", ".join(EXCLUDED)})' for p in leaks))
        sys.exit(f'{len(leaks)} shared file(s) name an excluded photo. Remove the mention from the source and rebuild; do not share or save this version.')


if __name__ == '__main__':
    main(sys.argv[1:])
