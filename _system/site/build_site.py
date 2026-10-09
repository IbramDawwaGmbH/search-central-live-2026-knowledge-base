"""Build the web edition of the knowledge base: a static, offline, self-contained site in 60-outputs/site/.

Input (public only): 60-outputs/agent-pack/claims.jsonl, topics.json, sessions.json, sources.json, dev-requirements.json and
content-library.json (the developer and content kits), plus CHANGELOG.md for the version. Copies 50-maps/mindmap.html, the
PDFs of 60-outputs/pdf/, 60-outputs/dev/requirements.csv and the two kit files (into downloads/) when they exist, so the
site folder works when it is shared on its own. Open 60-outputs/site/index.html by double-clicking it: no server, no
network, no CDN.

One style per build: Deep Dive, the default of _system/theme.yaml, written into every page as <html data-style="...">.
Nothing on the page changes it and the browser keeps no style choice; the Art Deco look is still in site.css, so setting
`default: art-deco` in _system/theme.yaml and rebuilding gives the whole site in Art Deco. The Deep Dive artwork (water
surface, seabed, hero scene, reef accents) is drawn by _system/ocean_art.py into assets/ocean/ at build time.

Links (v2.8.0): every claim card says what rests on it ("Used by": the requirements, facts, myths, quotes, story angles and
glossary terms whose `claims` cite it, counted from the kits); every source lists the claims it backs by grade; every topic
lists the requirements and facts built on its claims. The search index (assets/search-data.js) covers the kits and the
glossary too, with a vocabulary for typo tolerance, aliases seeded from the glossary, and a speaker filter that offers only
names proven by _system/kits.py proven() (never the session-speaker fallback).

Things (v2.9.0): entities.json (the things of 20-claims/entities.yaml) and the `mentions` of claims.jsonl give an index page
(entities.html, by kind) and one short card per thing (entities/<id>.html): kind, other names, summary, the home topic for the
narrative, the claims that name it split into Google's documentation and what was only said at the event (with grades, the
undocumented first), the kit items resting on those claims, its typed relations with the claims behind them, and the things most
often named with it. Claim cards show the things they name; topic and session pages show the things their claims name most; search
lists Things first and expands each thing's other names (GSC finds Search Console).

The Reef map (v2.10.0; "Graph" in the Art Deco style): graph.html, from _system/templates/graph.template.html, explores graph.json
one neighbourhood at a time (graph.html#ent:googlebot; the back button returns). Its data is assets/graph-data.js (window.KB_GRAPH),
checked against the cards: a thing's neighbours on the map are the ones its card lists. The same page with the data inline is written
to 50-maps/graph.html, next to the mindmap. The menu, every thing's card and every topic page link to it.
Since v2.12.0 it pans, zooms, drags bubbles, grows a bubble's neighbours in place, and has a preview card, a right-click menu (pin,
hide), a trail of visited centres and an optional living layout, by mouse, touch and keyboard. The default layout stays deterministic.

The ledgers (v2.11.0): numbers.json, differences.json and question-bank.json of the agent pack (written by _system/kits.py) give
three kit pages: dev/differences.html (where the event and Google's documentation differ, and what to follow), content/numbers.html
(every stat fact with its figures, scope and credit, and the figures no fact cites yet) and content/questions.html (the audience
questions with their answers, and "What did Google say about X?" per thing). Every claim on them is checked against claims.jsonl
like the kits', the registry must hold every stat fact, the kit pages link them, and a thing's card links its rows and its question.

Two editions (v2.13.0, _system/edition.yaml read through _system/edition.py): without the file, or with `edition: full`, the build makes
the full edition exactly as before. With `edition: community` the media kit is not in the site: content/index.html becomes a short
page on what the full kit holds (the counts of edition.yaml full_kit), with the preview items of the agent pack's reduced
content-library.json as normal kit cards, a soft note on working together and the open glossary. The facts, myths, angles, quotes,
numbers and questions pages are not written, every link to a preview item points to its card on the Content page, search leaves
the media kit out, and numbers.json and question-bank.json are not read. The developer kit stays whole, with one note near its end;
the masthead names the edition, About says who made it, and every page's footer carries one quiet line with the two links of
edition.yaml (the company and LinkedIn), the only links the edition adds.

The published community edition (the web addresses of edition.yaml; the full edition has none and is built exactly as before):
- site_url: every page gets an absolute <link rel="canonical"> (not search.html, which is "noindex, follow", nor 404.html), Open
  Graph and Twitter tags, and the home page WebSite and Organization JSON-LD; pages with crumbs get a BreadcrumbList. The share image
  is _system/brand/social/og-image.png (1200 x 630, made once by make_og_image.py next to it, never per build), copied to
  assets/social/. sitemap.xml lists every indexable page (lastmod: the date of the version heading of CHANGELOG.md), and 404.html,
  which GitHub Pages serves for any missing path, has a plain <base href="{site_url}"> before anything with an address, so its
  style sheet, scripts and links work at any depth (a page of the published site only: opened from the folder, it loads them
  from the web). The graph and the mindmap keep their own frame: in the sitemap only.
- repo_url, impressum_url, privacy_url: one footer line with the licences (linking LICENSE-CONTENT.md in the repository), Impressum
  and Privacy. Links to these addresses carry class "ext own"; the offline guard allows exactly the configured addresses (and the
  schema.org context of the JSON-LD), and nothing may be loaded from the web.
- The home page shows the 1-minute tour (_system/brand/video/tour.mp4 and tour-poster.jpg, copied to assets/video/; only when
  both exist) in a section with id "tour", and quick links. method.html renders METHOD.md of the repository root (a short
  placeholder when it is missing), linked from About, the quick links and the footer.

Usage:  python _system/site/build_site.py
"""
import html, json, math, re, shutil, sys, unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PACK = ROOT / '60-outputs' / 'agent-pack'
OUT = ROOT / '60-outputs' / 'site'
LABELS = {'slide': ('Slide', 'Shown on screen'), 'stage': ('Stage', 'Said on stage'), 'docs': ('Docs', "Google's documentation"),
          'press': ('Press', 'Reported by the press'), 'analysis': ('Analysis', "The author's interpretation")}
GROUPS = {'slide': 'Shown on screen', 'stage': 'Said on stage', 'docs': "What Google's documentation says", 'press': 'What the press reported',
          'analysis': 'Analysis by the author'}
VER = {'confirmed': ('Confirmed by docs', "Google's documentation states the same thing."),
       'consistent': ('Consistent with docs', "Google's documentation supports it without stating it directly."),
       'undocumented': ('Not in docs', "Said or shown at the event, but not in Google's documentation. Quote it as said at Search Central Live, not as documented policy."),
       'source': ('Source', 'The claim is the cited document itself: a page of Google documentation or a press report.'),
       'n/a': ('', 'Nothing to verify: a quotation, framing, agenda fact, audience question, opinion or analysis.')}
REL = {'contradicts': ('Contradicts', 'Contradicted by', 'A claim that disagrees with an earlier one.'),
       'updates': ('Updates', 'Updated by', 'A claim that replaces or revises an earlier one.'),
       'extends': ('Extends', 'Extended by', 'A claim that adds detail to an earlier one.'),
       'repeats': ('Repeats', 'Repeated by', 'The same point made again, often on a later day.'),
       'answers': ('Answers', 'Answered by', 'An answer to a question from the audience.')}
KINDS = {'talk': 'Talk', 'lightning': 'Lightning talk', 'panel': 'Panel', 'qa': 'Q&A', 'poster': 'Poster', 'break': 'Break', 'unrecorded': 'Not recorded'}
EXCLUDED = ('IMG_4692',)  # same list as EXCLUDED in _system/build_kb.py: never in any page
COVERAGE = {'slides': 'Slides', 'notes': 'Notes', 'transcript': 'Transcript', 'one-slide': 'One slide', 'video': 'Video', 'none': 'Not covered'}
NUMS = dict(enumerate('zero one two three four five six seven eight nine'.split()))
MONTHS = 'January February March April May June July August September October November December'.split()
WEEKDAYS = 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()
WORD = re.compile(r"[^\W_][\w'’-]*")
S, L = (str, None), list
SPEC = {
    'claim': dict(id=str, day=int, session_id=str, session=str, speaker=S, who=S, author=S, label=str, label_meaning=str, text=str, quote=str,
                  quote_checked=bool, verification=str, topics=L, sources=L, evidence=L, relations=L, related_from=L, used_by=L, mentions=L),
    'csource': dict(key=str, title=str, url=str, publisher=str, kind=str, checked=str),
    'source': dict(title=str, url=str, publisher=str, kind=str, checked=str),
    'topics': dict(version=str, data_through=str, areas=L), 'area': dict(id=str, title=str, blurb=str, topics=L),
    'topic': dict(id=str, title=str, summary=str, cites=L, do=L, related=L, claim_ids=L, sessions=L, days=L, event_sessions=L, event_days=L),
    'sessions': dict(version=str, data_through=str, event=dict, days=L), 'event': dict(name=str, city=str, dates=str),
    'day': dict(day=int, date=str, theme=str, sessions=L),
    'session': dict(id=str, time=str, title=str, speakers=L, role=S, kind=str, coverage=L, note=S, claim_count=int, topics=L),
    'rel': dict(type=str, to=str), 'relf': dict(type=str, **{'from': str}),
    'devkit': dict(version=str, data_through=str, event=str, levels=dict, statuses=dict, areas=L, snippets=L),
    'devarea': dict(id=str, title=str, intro=str, requirements=L),
    'req': dict(id=str, level=str, title=str, why=str, how=str, test=str, status=str, status_label=str, snippet=S, claims=L, docs=L, topics=L, entities=L),
    'kref': dict(id=str, day=int, session_id=str, session=str, label=str, label_meaning=str, verification=str, verification_meaning=str, text=str,
                 quote=str, quote_checked=bool, credit=str, speaker=S, sources=L),
    'snippet': dict(key=str, title=str, text=str, code=L, used_by=L), 'code': dict(lang=str, code=str, note=str),
    'lib': dict(version=str, data_through=str, event=str, wording_rules=L, statuses=dict, facts=L, myths=L, quotes=L, angles=L, glossary=L),
    'fact': dict(id=str, statement=str, status=str, status_label=str, use=str, claims=L, topics=L, entities=L),
    'myth': dict(id=str, myth=str, fact=str, status=str, status_label=str, claims=L, topics=L, entities=L),
    'quote': dict(id=str, quote=str, day=int, session_id=str, session=str, label=str, label_meaning=str, verification=str, verification_meaning=str,
                  text=str, quote_checked=bool, credit=str, speaker=S, sources=L, claim=str, topics=L, entities=L),
    'angle': dict(id=str, title=str, audience=L, formats=L, hook=str, points=L, caution=str, cta=str, topics=L, entities=L),
    'point': dict(text=str, status=str, claims=L), 'term': dict(id=str, term=str, definition=str, claims=L, topics=L, entities=L, defines=L),
    'ent': dict(id=str, kind=str, name=str, aliases=L, match=L, summary=str, glossary=S, definition=S, docs=L, topics=L, rel=L, rel_from=L, claims=L,
                tally=dict, cite=dict, co_mentioned=L, featured_in=L, items=L),
    'mention': dict(entity=str, via=S, field=str), 'erel': dict(type=str, to=str, claims=L), 'erelf': dict(type=str, claims=L, **{'from': str}),
    'eco': dict(id=str, count=int, claims=L), 'ecount': dict(id=str, count=int), 'eitem': dict(id=str, count=int, own=bool),
    # the ledgers of knowledge graph phase 3 (numbers.json, differences.json, question-bank.json): every claim is a kit claim record plus by and cite
    'lref': dict(id=str, day=int, session_id=str, session=str, label=str, label_meaning=str, verification=str, verification_meaning=str, text=str,
                 quote=str, quote_checked=bool, credit=str, speaker=S, sources=L, by=str, cite=str),
    'numbers': dict(version=str, data_through=str, about=str, rule=str, facts=L, candidates=L),
    'nfact': dict(id=str, figures=L, statement=str, status=str, status_label=str, credit=L, claims=L, topics=L, entities=L),
    'ncand': dict(id=str, day=int, session_id=str, session=str, label=str, label_meaning=str, verification=str, verification_meaning=str, text=str,
                  quote=str, quote_checked=bool, credit=str, speaker=S, sources=L, by=str, cite=str, figures=L),
    'lent': dict(id=str, name=str, count=int), 'lento': dict(id=str, name=str, count=int, own=bool),
    'diffs': dict(version=str, data_through=str, about=str, rule=str, rows=L, pairs=L, hedged=L),
    'drow': dict(id=str, title=str, follow=str, event=L, docs=L, pages=L, analysis=L, topics=L, entities=L),
    'dpage': dict(key=str, title=str, url=str, publisher=str, checked=str), 'dpair': dict(type=str, to=dict, rows=L, **{'from': dict}),
    'qbank': dict(version=str, data_through=str, about=str, rules=L, audience=L, things=L),
    'qaud': dict(question=dict, answers=L, grade=S, grade_label=str, topics=L, entities=L),
    'qthing': dict(id=str, name=str, kind=str, question=str, claims=int, card=str, documented=dict, event_only=dict), 'qtop': dict(count=int, top=L)}
LIST_OF = {'claim': dict(topics=str, evidence=str, used_by=str), 'ent': dict(aliases=str, docs=str, topics=str, claims=str), 'erel': dict(claims=str),
           'erelf': dict(claims=str), 'eco': dict(claims=str), 'session': dict(speakers=str, coverage=str, topics=str),
           'topic': dict(cites=str, do=str, related=str, claim_ids=str, sessions=str, days=int, event_sessions=str, event_days=int),
           'snippet': dict(used_by=str), 'lib': dict(wording_rules=str), 'angle': dict(audience=str, formats=str, topics=str),
           'nfact': dict(figures=str, credit=str, topics=str), 'ncand': dict(figures=str), 'drow': dict(topics=str), 'dpair': dict(rows=str),
           'qbank': dict(rules=str), 'qaud': dict(topics=str),
           **{k: dict(topics=str) for k in ('req', 'fact', 'myth', 'quote', 'term')}}
LEVELS = {'MUST': ('Must', 'Required: the site is not ready to launch without it.'), 'SHOULD': ('Should', 'Recommended: skip it only for a reason you can name.'),
          'MAY': ('May', 'Optional: worth doing where it fits.'), 'AVOID': ('Avoid', 'Must not: the site is not ready to launch while it does this.')}
KSTATUS = {'documented': ('Documented', 'A cited Google page states or supports it.'),
           'event-only': ('Said at Search Central Live', 'Said or shown at the event, not in Google’s documentation. Present it as said at Search Central Live, never as documented policy.'),
           'mixed': ('Partly documented', 'Some of its claims are in Google’s documentation and some were only said or shown at the event: check each claim.'),
           'press': ('Press report', 'A third-party report of what Google said, not Google’s documentation.'),
           'analysis': ('Author’s analysis', 'The author’s interpretation. Never attribute it to Google.')}
USES = {'stat': 'Stats', 'headline': 'Headlines', 'context': 'Context'}
FORMATS = {'linkedin': 'LinkedIn post', 'article': 'Article', 'newsletter': 'Newsletter', 'video': 'Video', 'carousel': 'Carousel', 'talk': 'Talk',
           'podcast': 'Podcast', 'infographic': 'Infographic'}
# The PDF editions that rebuild.bat no longer rebuilds (frozen since v2.5.0): their download names say so, and the log of what
# they lack (60-outputs/pdf/classic-editions-log.md) is listed and copied next to them.
CLASSIC_STYLES, CLASSIC_NOTE, CLASSIC_LOG = ('art-deco', 'modern'), 'classic edition, content as of v2.4.0', 'classic-editions-log.md'
STYLES = {'deep-dive': 'Deep Dive', 'art-deco': 'Art Deco'}  # the site's two looks (data-style value -> name); theme.yaml picks one per build
STYLE = 'art-deco'  # the default of this build, from _system/theme.yaml (set in main)
# The edition of this build, from _system/edition.yaml (set in main, before the pack is read): 'full', or 'community' (see the top)
URLS = ('site_url', 'repo_url', 'contact_url', 'impressum_url', 'privacy_url')  # where the community edition is published (edition.yaml)
ED = {'edition': 'full', 'author': '', 'linkedin': '', 'company': {'name': '', 'url': ''}, 'full_kit': {}, **{k: '' for k in URLS}}
MEDIA = ('facts', 'myths', 'quotes', 'angles')  # the media kit lists of content-library.json: a short preview of each in the community edition
LIB_EXTRA = ('edition', 'note', 'about')  # keys content-library.json may add to the kit (its edition and a one-line note), strings
CONTACT = re.compile(r'https?://[^\s"\'<>`\\]+')  # the links of edition.yaml: plain web addresses only
# The published community edition: the tour video and its poster (copied to assets/video/ when both exist), the share image of the
# social previews (made once by _system/brand/social/make_og_image.py, copied to assets/social/), and the method write-up.
TOUR = {'assets/video/tour.mp4': ROOT / '_system' / 'brand' / 'video' / 'tour.mp4',
        'assets/video/tour-poster.jpg': ROOT / '_system' / 'brand' / 'video' / 'tour-poster.jpg'}
OG_IMAGE, OG_SIZE = ('assets/social/og-image.png', ROOT / '_system' / 'brand' / 'social' / 'og-image.png'), (1200, 630)
OG_ALT = 'The Knowledge Base of Search Central Live Deep Dive Europe 2026: the Diver bot in sunlit water beside the title'
METHOD_MD = ROOT / 'METHOD.md'
SCHEMA_ORG = 'https://schema.org'


# ------------------------------------------------------------------ style: theme.yaml and the Deep Dive artwork
def default_style():
    """The default style from _system/theme.yaml. A bad theme.yaml stops the build; a copy of the site code without
    _system/theme.py (an older checkout) builds in Art Deco."""
    if not (HERE.parent / 'theme.py').exists():
        print('WARNING: _system/theme.py not found: the site defaults to Art Deco', file=sys.stderr)
        return 'art-deco'
    sys.path.insert(0, str(HERE.parent))
    import theme
    try: s = theme.default_style()
    except theme.ThemeError as x: sys.exit(f'ERROR: {x}')
    if s not in STYLES: sys.exit(f'ERROR: _system/theme.yaml names style {s!r}, which the web edition does not know')
    return s


def edition_settings():
    """The edition from _system/edition.py (it reads _system/edition.yaml). A checkout without edition.py (the main branch before
    v2.13.0, a test fixture) builds the full edition. In the community edition the company and LinkedIn links must be plain web
    addresses: they are written into every page."""
    if not (HERE.parent / 'edition.py').exists(): return ED
    sys.path.insert(0, str(HERE.parent))
    import edition
    d = edition.load()
    d = dict(d, **{k: d.get(k) or '' for k in URLS})  # an older edition.py without the web addresses: none set
    if d['edition'] == 'community':
        for k, v in (('linkedin', d['linkedin']), ('company url', d['company']['url'])) + tuple((k.replace('_', ' '), d[k]) for k in URLS):
            if v and not CONTACT.fullmatch(v): sys.exit(f'ERROR: _system/edition.yaml: the {k} must be an http(s) address, not {v!r}')
        if d['site_url'] and not d['site_url'].endswith('/'): d['site_url'] += '/'
        d['repo_url'] = d['repo_url'].rstrip('/')
    return d


def community(): return ED['edition'] == 'community'
EDITION_BLOCK = re.compile(r'/\* edition: community \*/.*?/\* edition: end \*/\n', re.S)
def edition_blocks(text):
    """site.css and site.js as the edition needs them: a block from "/* edition: community */" to the line "/* edition: end */"
    is only for the community edition, so the full edition's copy is byte for byte what it was before the block was added."""
    return text if community() else EDITION_BLOCK.sub('', text)
def site_url(): return ED['site_url'] if community() else ''  # the published web edition, ending in '/'; '' in the full edition
def abs_url(path): return site_url() + ('' if path == 'index.html' else path)  # a page's absolute (canonical) address
def ed_url(k): return ED[k] if community() else ''  # repo_url, contact_url, impressum_url, privacy_url: '' when not set or full
def repo_file(path): return f'{ed_url("repo_url")}/blob/HEAD/{path}' if ed_url('repo_url') else ''  # a file of the repository on its host
def own_link(url, text, cls='ext own'):
    """A link to an address of edition.yaml other than the company and LinkedIn (the repository, Impressum, Privacy, contact),
    opened in a new tab like the contact links. The offline guard checks every one of them."""
    return f'<a class="{cls}" href="{e(url)}" rel="noopener external" target="_blank">{e(text)}</a>'


# The diver bot of the site: (pose, height in CSS px it is drawn for). Each is written light and dark (night water) as
# assets/ocean/bot-<name>.svg; the CSS shows them as backgrounds of decorative, aria-hidden boxes in Deep Dive only.
BOTS = {'head': ('head', 40), 'hero': ('swim', 230), 'peek': ('peek', 66), 'read': ('read', 190), 'point': ('point', 150), 'wave': ('wave', 190)}


def bot_file(oa, pose, px, uid, dark=False, blink=False):
    """A diver bot as a stand-alone SVG file: its viewBox and intrinsic size, no inline style (CSS sizes it).
    blink (seconds) gives the -anim variant: the same bot with a short blink inside the SVG."""
    svg = oa.diver_bot_svg(pose, f'{px}px', uid, dark=dark, blink=blink)
    w = re.search(r'width:([0-9.]+)px', svg).group(1)
    return re.sub(r' class="bot" style="[^"]*"', f' width="{w}" height="{px}"', svg, count=1)


# Motion (Deep Dive, prefers-reduced-motion: no-preference only; site.css picks the files): the bots that blink, with
# their blink period in seconds (different, so two bots on one page never blink together). 'head' stays still.
BLINK = {'hero': 5.6, 'read': 4.7, 'point': 5.2, 'wave': 4.4, 'peek': 4.9}
ACCENT = '<svg viewBox="0 0 300 150" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{}</svg>'


def accent_parts(oa, dark, wag=False):
    """The page-head reef accent in its four parts, in drawing order: a small mono school (swims left), a bubble trail,
    the yellow fish (swims left) and the red fish (flip=True: swims right), all in the accent's 300 x 150 box.
    accent.svg draws all four; fish-school.svg, trail.svg, fish-yellow.svg and fish-red.svg one each (same calls).
    wag=True gives the two big fish a tail group for ocean_art.TAIL_CSS (the -anim files)."""
    pal = oa.DARK if dark else oa.PALETTE
    tail = {'tail': 'tail'} if wag else {}
    return {'school': oa.fish_school(246, 30, 15, '#b3bfec' if not dark else '#3b5aa8', n=3, seed='head', mono=True),
            'trail': oa.bubble_trail(112, 64, 54, 6.5, n=4, seed='head', pal=pal, fill_op=.5 if not dark else .18),
            'yellow': oa.fish(172, 86, 84, 'yellow', pal=pal, **tail),
            'red': oa.fish(66, 122, 38, 'red', flip=True, pal=pal, **({'tail': 'tail t1'} if wag else {}))}


def _path_box(d):
    """Box (x0, y0, x1, y1) of SVG path data with absolute M/L/Q/C/Z commands; curves are sampled finely."""
    toks = re.findall(r'[A-Za-z]|-?\d*\.?\d+', d)
    pts, cur, i, cmd = [], (0.0, 0.0), 0, ''
    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in 'Zz':
                continue
        n = {'M': 1, 'L': 1, 'Q': 2, 'C': 3}[cmd]
        ctl = [(float(toks[i + 2 * k]), float(toks[i + 2 * k + 1])) for k in range(n)]
        i += 2 * n
        seg = [cur] + ctl
        for s in range(65 if n > 1 else 1):
            t = s / 64 if n > 1 else 1.0
            p = seg
            while len(p) > 1:                        # de Casteljau
                p = [((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1]) for a, b in zip(p, p[1:])]
            pts.append(p[0])
        cur = ctl[-1]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def fish_box(oa, svg):
    """Box (x, y, w, h) of the fish in an SVG fragment drawn by ocean_art.fish / mono_fish / fish_school, in the fragment's
    user units: the outline of the base-100 fish (tail, dorsal fin, body), placed by each fish's translate/scale."""
    local = [_path_box(d) for d in re.findall(r'<path d="([^"]+)"', oa.mono_fish(0, 0, 100, '#000000'))]
    lx0, ly0 = min(b[0] for b in local), min(b[1] for b in local)
    lx1, ly1 = max(b[2] for b in local), max(b[3] for b in local)
    xs, ys = [], []
    for tx, ty, sx, sy in re.findall(r'<g transform="translate\(([-\d.]+),([-\d.]+)\) scale\(([-\d.]+),([-\d.]+)\)"', svg):
        tx, ty, sx, sy = map(float, (tx, ty, sx, sy))
        xs += [tx + sx * lx0, tx + sx * lx1]
        ys += [ty + sy * ly0, ty + sy * ly1]
    x0, y0 = math.floor(min(xs) * 10) / 10, math.floor(min(ys) * 10) / 10
    return x0, y0, math.ceil((max(xs) - x0) * 10) / 10, math.ceil((max(ys) - y0) * 10) / 10


_REEF = []


def reef_markup():
    """The page-head reef of heads without the bot: the accent's four parts as aria-hidden layers (site.css draws each one
    with its SVG, site.js makes the fish clickable). data-box is each fish's box in the accent's 300 x 150 units."""
    if not _REEF:
        box = {}
        if (HERE.parent / 'ocean_art.py').exists():
            sys.path.insert(0, str(HERE.parent))
            import ocean_art as oa
            parts = accent_parts(oa, False)
            box = {k: ' data-box="' + ' '.join(fmt_n(v) for v in fish_box(oa, parts[k])) + '"' for k in ('school', 'yellow', 'red')}
        _REEF.append(f'<span class="dd-reef" aria-hidden="true"><i class="dd-fish dd-f-school"{box.get("school", "")}></i><i class="dd-trail"></i>'
                     f'<i class="dd-fish dd-f-yellow"{box.get("yellow", "")}></i><i class="dd-fish dd-f-red"{box.get("red", "")}></i></span>')
    return _REEF[0]


def fmt_n(v):
    """A number for an attribute: at most one decimal, no trailing zero."""
    s = f'{v:.1f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


DD_PLANKTON = '<span class="dd-plankton" aria-hidden="true"><i></i><i></i></span>'
DD_HEAD = '<span class="dd-rays" aria-hidden="true"></span>' + DD_PLANKTON + '<span class="dd-crossing" aria-hidden="true"><i></i></span>'


def ocean_assets():
    """Deep Dive artwork as SVG files for assets/ocean/, light and night-water versions. They are CSS backgrounds, so a
    browser only fetches them when Deep Dive is showing. Deterministic: fixed seeds, no clock."""
    if not (HERE.parent / 'ocean_art.py').exists():
        print('WARNING: _system/ocean_art.py not found: the Deep Dive style is built without its artwork', file=sys.stderr)
        return {}
    sys.path.insert(0, str(HERE.parent))
    import ocean_art as oa
    out = {}
    for dark, sfx in ((False, ''), (True, '-dark')):
        pal = oa.DARK if dark else oa.PALETTE
        # water surface under the masthead: a seamless tile (its width is a whole number of wavelengths)
        # (its front wave takes the masthead's lower blue, a shade deeper than the print blue so white text on it reads well)
        out[f'wave{sfx}.svg'] = oa.top_wave(width=600, height=44, dark=dark, wl=200).replace(pal['wave_front'], '#2862d2')
        # seabed above the footer band: wide, centred, cropped on narrow screens
        out[f'seabed{sfx}.svg'] = oa.seabed(width=2400, height=230, variant='slim', seed=31, dark=dark)
        # the overview hero: a full underwater banner, the title card sits in its safe area
        out[f'hero{sfx}.svg'] = oa.underwater_scene(1440, 720, seed=4, mood='deep' if dark else 'light', uid='hero' + sfx)
        # a small reef accent for the head of every other page: two fish and a bubble trail
        parts = accent_parts(oa, dark)
        out[f'accent{sfx}.svg'] = ACCENT.format(''.join(parts.values()))
        # the diver bot (the masthead mark sits on blue water in both colour schemes: one light version)
        for name, (pose, px) in BOTS.items():
            if not (name == 'head' and dark):
                out[f'bot-{name}{sfx}.svg'] = bot_file(oa, pose, px, f'bot-{name}{sfx}', dark)
        # --- motion (Deep Dive; site.css uses these only under prefers-reduced-motion: no-preference) ---
        # the accent in four layers (each in the full 300 x 150 box: stacked, they are accent.svg)
        for k, name in (('school', 'fish-school'), ('trail', 'trail'), ('yellow', 'fish-yellow'), ('red', 'fish-red')):
            out[f'{name}{sfx}.svg'] = ACCENT.format(parts[k])
        # the yellow and red fish with a gently wagging tail (CSS keyframes inside the SVG); otherwise as fish-yellow / fish-red
        wag = accent_parts(oa, dark, wag=True)
        for k in ('yellow', 'red'):
            out[f'fish-{k}-anim{sfx}.svg'] = ACCENT.format(oa.TAIL_CSS + wag[k])
        # a small, faint school that now and then crosses a page head from right to left (the fish face left)
        cross = '#b3bfec' if not dark else '#3b5aa8'
        out[f'fish-cross{sfx}.svg'] = ('<svg viewBox="0 0 140 40" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
                                       + oa.fish_school(17, 23, 14, cross, n=4, seed='cross', mono=True)
                                       + oa.fish_school(104, 20, 12, cross, n=3, seed='cross-b', mono=True) + '</svg>')
        # the footer seabed with its ferns and fan corals swaying
        out[f'seabed-anim{sfx}.svg'] = oa.seabed(width=2400, height=230, variant='slim', seed=31, dark=dark, sway=True)
        # the bots with a blink (same size and viewBox as the still files)
        for name, period in BLINK.items():
            pose, px = BOTS[name]
            out[f'bot-{name}-anim{sfx}.svg'] = bot_file(oa, pose, px, f'bot-{name}{sfx}', dark, blink=period)
        # the bot's reactions on the search page and in empty states: a question bubble and one blown bubble
        # (light water: a pale blue fill, so the white highlight arc shows and the bubble looks glossy)
        bkw = dict(stroke='#9cc0ff', fill='#cfe0ff', fill_op=.18) if dark else dict(fill=oa.mix(pal['bubble_stroke'], '#ffffff', .55), fill_op=.75)
        # the question mark of the quiz chip (ocean_art.icon_question, 64-unit box), in amber, inside a round bubble
        q = re.search(r'<path .*/>', oa.icon_question()).group(0).replace('#ffffff', pal['quiz_amber'])
        out[f'q-bubble{sfx}.svg'] = ('<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
                                     + oa.bubble(20, 20, 18, pal=pal, **(dict(bkw, fill_op=.3) if dark else dict(fill=pal['blue_wash'], fill_op=.96)))
                                     + f'<g transform="translate(19.2,20.2) scale(.5) translate(-32,-32)">{q}</g></svg>')
        out[f'blow-bubble{sfx}.svg'] = ('<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
                                        + oa.bubble(12, 12, 10.5, pal=pal, **bkw) + '</svg>')
    return {k: v + '\n' for k, v in out.items()}


def dd_icon():
    """The browser-tab icon in Deep Dive: the diver bot's head, drawn for 16 px (high contrast, square). Without
    ocean_art.py (an older checkout): a glossy blue bubble with a small fish."""
    if not (HERE.parent / 'ocean_art.py').exists():
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="10" fill="#2f6fe0"/>'
                '<path d="M11 23c4-7 13-7 16 0-3 6-12 6-16 0z" fill="#fff"/><path d="M26 23l6-4.5v9z" fill="#fff"/>'
                '<circle cx="15.2" cy="21.8" r="1.4" fill="#2152c4"/></svg>\n')
    sys.path.insert(0, str(HERE.parent))
    import ocean_art as oa
    svg = oa.diver_bot_svg('head', '16px', 'fav', square=True)
    return re.sub(r' class="bot" style="[^"]*"', ' width="32" height="32"', svg, count=1) + '\n'


def empty_note(pose, inner, cls='empty-note'):
    """An empty state. Deep Dive shows the diver bot (an aria-hidden box, its pose from data-pose) beside the message;
    Art Deco hides the box, so the message looks as it always did (a plain paragraph or callout)."""
    return (f'<div class="{cls}" data-pose="{pose}"><span class="bot-art" aria-hidden="true"></span><span class="dd-q" aria-hidden="true"></span>'
            f'<div class="note-t">{inner}</div></div>')


# ------------------------------------------------------------------ load and validate
def is_type(v, t):
    if isinstance(t, tuple): return v is None or isinstance(v, t[0])
    if t is int: return isinstance(v, int) and not isinstance(v, bool)
    return isinstance(v, t)


def shape(obj, kind, where, errs):
    spec = SPEC[kind]
    if not isinstance(obj, dict): errs.append(f'{where}: expected an object'); return False
    bad = [f'missing "{k}"' for k in spec if k not in obj] + [f'unexpected key "{k}"' for k in obj if k not in spec]
    bad += [f'"{k}" must be {getattr(t, "__name__", "string or null")}' for k, t in spec.items() if k in obj and not is_type(obj[k], t)]
    lists = LIST_OF.get(kind, {})
    bad += [f'"{k}" must be a list of {t.__name__}' for k, t in lists.items() if isinstance(obj.get(k), list) and not all(is_type(x, t) for x in obj[k])]
    errs += [f'{where}: {b}' for b in bad]
    return not bad


def load():
    errs, warns = [], []
    def read(name):
        p = PACK / name
        if not p.exists(): sys.exit(f'ERROR: {p} is missing. Run python _system/build_kb.py first.')
        return p.read_text(encoding='utf-8')
    def parse(name):
        try: return json.loads(read(name))
        except json.JSONDecodeError as x: sys.exit(f'ERROR: {name}: {x}')
    claims = []
    for n, line in enumerate(read('claims.jsonl').splitlines(), 1):
        if not line.strip(): continue
        try: claims.append(json.loads(line))
        except json.JSONDecodeError as x: errs.append(f'claims.jsonl line {n}: {x}')
    tdoc, sdoc, sources = parse('topics.json'), parse('sessions.json'), parse('sources.json')
    dev, lib, links, edoc = parse('dev-requirements.json'), parse('content-library.json'), parse('links.json'), parse('entities.json')
    if community():  # the media kit's ledgers (numbers.json, question-bank.json) are not in the community edition: never read
        nums, difs, qbank = None, parse('differences.json'), None
        if isinstance(lib, dict):
            for k in MEDIA: lib.setdefault(k, [])
    else: nums, difs, qbank = parse('numbers.json'), parse('differences.json'), parse('question-bank.json')
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8') if (ROOT / 'CHANGELOG.md').exists() else ''
    m = re.search(r'^## (v\d+\.\d+\.\d+)([^\n]*)\n(.*?)(?=^## |\Z)', log, re.M | re.S)
    if not m: sys.exit('ERROR: CHANGELOG.md has no "## vX.Y.Z" heading')
    version, notes = m.group(1), [x[2:].strip() for x in m.group(3).splitlines() if x.startswith('- ')]
    vdate = re.search(r'\b(\d{4}-\d\d-\d\d)\b', m.group(2))  # "## v2.13.0 — 2026-10-08": the lastmod of sitemap.xml
    vdate = vdate.group(1) if vdate and isodate(vdate.group(1)) else ''

    if not shape(tdoc, 'topics', 'topics.json', errs) or not shape(sdoc, 'sessions', 'sessions.json', errs) or not isinstance(sources, dict):
        fail(errs + ([] if isinstance(sources, dict) else ['sources.json: expected an object']))
    shape(sdoc['event'], 'event', 'sessions.json event', errs)
    for k, v in sources.items():
        if shape(v, 'source', f'sources.json {k}', errs):
            if v['kind'] not in ('google', 'press'): errs.append(f'sources.json {k}: kind must be google or press')
            if not re.match(r'https?://', v['url']): errs.append(f'sources.json {k}: url must be http(s)')
            if not isodate(v['checked']): errs.append(f'sources.json {k}: checked must be a real date, YYYY-MM-DD')
    sess, days = {}, []
    for d in sdoc['days']:
        if not shape(d, 'day', f'sessions.json day {d.get("day", "?") if isinstance(d, dict) else "?"}', errs): continue
        if not isodate(d['date']): errs.append(f'sessions.json day {d["day"]}: bad date {d["date"]}')
        days.append(d)
        for s in d['sessions']:
            w = f'sessions.json {s.get("id", "?") if isinstance(s, dict) else "?"}'
            if not shape(s, 'session', w, errs): continue
            if not re.fullmatch(rf'D{d["day"]}-S\d\d', s['id']): errs.append(f'{w}: id must be D{d["day"]}-Snn')
            if s['id'] in sess: errs.append(f'{w}: duplicate session id')
            if s['time'] and not re.fullmatch(r'\d\d:\d\d', s['time']): errs.append(f'{w}: time must be "HH:MM" or ""')
            if s['kind'] not in KINDS: errs.append(f'{w}: unknown kind {s["kind"]}')
            if s['id'].endswith('-S00') and s['kind'] != 'unrecorded': errs.append(f'{w}: S00 must have kind "unrecorded"')
            errs += [f'{w}: unknown coverage {c}' for c in s['coverage'] if c not in COVERAGE]
            sess[s['id']] = dict(s, day=d['day'], date=d['date'], theme=d['theme'])
        d['sessions'] = [sess[s['id']] for s in d['sessions'] if isinstance(s, dict) and s.get('id') in sess]
    areas, topics, ids = [], {}, set()
    for a in tdoc['areas']:
        if not shape(a, 'area', f'topics.json area {a.get("id", "?") if isinstance(a, dict) else "?"}', errs): continue
        areas.append(a)
        for x in [a] + [t for t in a['topics'] if shape(t, 'topic', f'topics.json topic {t.get("id", "?") if isinstance(t, dict) else "?"}', errs)]:
            if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', x['id']): errs.append(f'topics.json: id "{x["id"]}" is not kebab-case')
            if x['id'] in ids: errs.append(f'topics.json: duplicate id {x["id"]}')
            ids.add(x['id'])
            if x is not a: topics[x['id']] = dict(x, area=a)
        a['topics'] = [t for t in a['topics'] if isinstance(t, dict) and t.get('id') in topics]
    if errs: fail(errs)

    byid = {}
    for n, c in enumerate(claims, 1):
        w = f'claims.jsonl {c.get("id", f"line {n}") if isinstance(c, dict) else f"line {n}"}'
        if not shape(c, 'claim', w, errs): continue
        m = re.fullmatch(r'D(\d)-C\d{3}', c['id'])
        if not m: errs.append(f'{w}: bad id'); continue
        if c['id'] in byid: errs.append(f'{w}: duplicate id')
        byid[c['id']] = c
        s = sess.get(c['session_id'])
        if not s: errs.append(f'{w}: unknown session {c["session_id"]}'); continue
        if not (int(m.group(1)) == c['day'] == s['day']): errs.append(f'{w}: day {c["day"]} does not match its id and session {c["session_id"]}')
        if c['session'] != s['title']: errs.append(f'{w}: session title differs from sessions.json')
        if c['label'] not in LABELS: errs.append(f'{w}: unknown label {c["label"]}')
        if c['verification'] not in VER: errs.append(f'{w}: unknown verification {c["verification"]}')
        if not c['text'].strip() or '\n' in c['text']: errs.append(f'{w}: text must be one non-empty line')
        if len(WORD.findall(c['quote'])) > 25: errs.append(f'{w}: quote longer than 25 words')
        if not c['topics']: errs.append(f'{w}: no topics')
        errs += [f'{w}: unknown topic {t}' for t in c['topics'] if t not in topics]
        stage = c['label'] in ('slide', 'stage')
        if c['who'] is not None and not stage: errs.append(f'{w}: "who" is only allowed on slide/stage claims')
        if c['who'] is not None and not c['who'].strip(): errs.append(f'{w}: who is empty')
        elif c['who'] is not None and not s['id'].endswith('-S00') and c['who'] not in s['speakers'] + ['audience', 'unknown']:
            errs.append(f'{w}: who "{c["who"]}" is not a speaker of {s["id"]}')  # S00 (not recorded) has no speaker list: any name
        if stage and c['speaker'] != (c['who'] or ', '.join(s['speakers']) or None): errs.append(f'{w}: speaker must be who, or else the session speakers')
        if c['label'] == 'stage' and len(s['speakers']) > 1 and not c['who']: errs.append(f'{w}: stage claim in a multi-speaker session needs "who"')
        if not stage and not c['author']: errs.append(f'{w}: {c["label"]} claim needs an author')
        kinds = []
        for x in c['sources']:
            if not shape(x, 'csource', f'{w} source', errs): continue
            kinds.append(x['kind'])
            ref = sources.get(x['key'])
            if not ref: errs.append(f'{w}: unknown source {x["key"]}')
            elif {k: x[k] for k in ref} != ref: errs.append(f'{w}: source {x["key"]} differs from sources.json')
        v = c['verification']
        if v in ('confirmed', 'consistent') and 'google' not in kinds: errs.append(f'{w}: {v} needs a Google source')
        if c['label'] == 'docs' and (v != 'source' or not kinds or set(kinds) != {'google'}): errs.append(f'{w}: docs claims cite only Google sources and use verification "source"')
        if c['label'] == 'press' and (v != 'source' or 'press' not in kinds): errs.append(f'{w}: press claims cite a press source and use verification "source"')
        for r in c['relations']:
            if shape(r, 'rel', f'{w} relation', errs) and r['type'] not in REL: errs.append(f'{w}: unknown relation type {r["type"]}')
        for r in c['related_from']:
            if shape(r, 'relf', f'{w} related_from', errs) and r['type'] not in REL: errs.append(f'{w}: unknown relation type {r["type"]}')
    if errs: fail(errs)
    fwd = {(c['id'], r['type'], r['to']) for c in claims for r in c['relations']}
    back = {(r['from'], r['type'], c['id']) for c in claims for r in c['related_from']}
    errs += [f'claims.jsonl {a}: relation {t} to unknown claim {b}' for a, t, b in sorted(fwd) if b not in byid or a == b]
    errs += [f'claims.jsonl {b}: related_from {t} names unknown claim {a}' for a, t, b in sorted(back) if a not in byid]
    errs += [f'claims.jsonl: relation {a} {t} {b} has no matching related_from' for a, t, b in sorted(fwd - back)]
    errs += [f'claims.jsonl: related_from {a} {t} {b} has no matching relation' for a, t, b in sorted(back - fwd)]
    for t in topics.values():
        w, mine = f'topics.json {t["id"]}', [c for c in claims if t['id'] in c['topics']]
        ev = [c for c in mine if c['label'] in ('slide', 'stage') and not c['session_id'].endswith('-S00')]
        errs += [f'{w}: cites unknown claim {x}' for x in t['cites'] if x not in byid]
        errs += [f'{w}: related to unknown topic {x}' for x in t['related'] if x not in topics]
        errs += [f'{w}: unknown session {x}' for x in t['sessions'] + t['event_sessions'] if x not in sess]
        if set(t['claim_ids']) != {c['id'] for c in mine}: errs.append(f'{w}: claim_ids do not match the claims tagged with it')
        said = {c['day'] for c in mine if c['label'] in ('slide', 'stage')}  # S00 counts here: its day is known
        if set(t['event_sessions']) != {c['session_id'] for c in ev}:
            errs.append(f'{w}: event_sessions must list the sessions of its slide and stage claims, without S00')
        if set(t['event_days']) != said:
            errs.append(f'{w}: event_days must list the days of its slide and stage claims, S00 included')
    for s in sess.values():
        n = sum(c['session_id'] == s['id'] for c in claims)
        if s['claim_count'] != n: errs.append(f'sessions.json {s["id"]}: claim_count {s["claim_count"]} but {n} claims')
        errs += [f'sessions.json {s["id"]}: unknown topic {x}' for x in s['topics'] if x not in topics]
    with_claims = [d for d in days if any(c['day'] == d['day'] for c in claims)]
    through = with_claims[-1]['date'] if with_claims else ''
    for doc, name in ((tdoc, 'topics.json'), (sdoc, 'sessions.json')):
        if doc['data_through'] != through: errs.append(f'{name}: data_through {doc["data_through"]} but the latest day with claims is {through}')
    if tdoc['version'] != sdoc['version']: errs.append('topics.json and sessions.json carry different versions')
    check_kits(dev, lib, byid, tdoc['version'], errs)
    if errs: fail(errs)
    L = check_links(links, claims, byid, topics, sess, sources, dev, lib, tdoc['version'], errs)
    if errs: fail(errs)
    L.update(check_entities(edoc, claims, byid, topics, ids, sources, sess, L, tdoc['version'], errs))
    if not errs: check_ledgers(nums, difs, qbank, byid, topics, L['ents'], lib, tdoc['version'], errs)
    if tdoc['version'].lstrip('v') != version.lstrip('v'):
        warns.append(f'agent pack is {tdoc["version"]} but CHANGELOG.md says {version}: run build_kb.py to refresh it')
    if community() and lib.get('edition') != 'community':  # a pack of before the community edition: built, its kit shown as the preview
        warns.append('content-library.json does not say it is the community edition, so its whole media kit shows as the preview: run build_kb.py')
    if errs: fail(errs)
    for w in warns: print('WARNING:', w, file=sys.stderr)
    short = re.sub(r'^Search Central Live\s+', '', sdoc['event']['name'])
    return dict(claims=claims, byid=byid, order={c['id']: i for i, c in enumerate(claims)}, short=short, sess=sess, days=days, areas=areas, topics=topics, sources=sources, event=sdoc['event'],
                version=version, vdate=vdate, notes=notes, through=through, dev=dev, lib=lib, nums=nums, difs=difs, qbank=qbank, **L)


def check_kits(dev, lib, byid, version, errs):
    """The developer and content kits of the agent pack: shapes, values, and every cited claim public and identical to claims.jsonl."""
    def refs(rs, w):
        for r in rs:
            if not shape(r, 'kref', f'{w} claim', errs): continue
            c = byid.get(r['id'])
            if not c: errs.append(f'{w}: claim {r["id"]} is not a public claim of claims.jsonl')
            elif any(r[k] != c[k] for k in ('text', 'label', 'verification', 'day', 'session_id')): errs.append(f'{w}: claim {r["id"]} differs from claims.jsonl')
            for x in r['sources']: shape(x, 'csource', f'{w} {r["id"]} source', errs)
        if not rs: errs.append(f'{w}: cites no claim')
    if shape(dev, 'devkit', 'dev-requirements.json', errs):
        snips = {s['key'] for s in dev['snippets'] if shape(s, 'snippet', 'dev-requirements.json snippet', errs) and all(shape(b, 'code', f'snippet {s["key"]} code', errs) for b in s['code'])}
        ids = set()
        for a in dev['areas']:
            if not shape(a, 'devarea', 'dev-requirements.json area', errs): continue
            for r in a['requirements']:
                w = f'dev-requirements.json {r.get("id", "?") if isinstance(r, dict) else "?"}'
                if not shape(r, 'req', w, errs): continue
                if not re.fullmatch(r'DEV-[A-Z]{2,6}-\d\d', r['id']) or r['id'] in ids: errs.append(f'{w}: bad or duplicate id')
                ids.add(r['id'])
                if r['level'] not in LEVELS: errs.append(f'{w}: unknown level {r["level"]}')
                if r['status'] not in ('documented', 'event-only'): errs.append(f'{w}: unknown status {r["status"]}')
                if r['snippet'] is not None and r['snippet'] not in snips: errs.append(f'{w}: unknown snippet {r["snippet"]}')
                for x in r['docs']:
                    if shape(x, 'csource', f'{w} docs', errs) and x['kind'] != 'google': errs.append(f'{w}: docs must be Google pages')
                refs(r['claims'], w)
        if dev['version'] != version: errs.append(f'dev-requirements.json is {dev["version"]} but topics.json is {version}: run build_kb.py')
    if isinstance(lib, dict):  # its edition, when it names one, is the edition of this build (a pack of the other edition is stale)
        errs += [f'content-library.json: "{k}" must be a string' for k in LIB_EXTRA if k in lib and not isinstance(lib[k], str)]
        if lib.get('edition', ED['edition']) != ED['edition']:
            errs.append(f'content-library.json is the {lib["edition"]} edition but _system/edition.yaml makes the {ED["edition"]} edition: run build_kb.py')
    if shape({k: v for k, v in lib.items() if k not in LIB_EXTRA} if isinstance(lib, dict) else lib, 'lib', 'content-library.json', errs):
        for kind, items in (('fact', lib['facts']), ('myth', lib['myths']), ('quote', lib['quotes']), ('angle', lib['angles']), ('term', lib['glossary'])):
            for x in items:
                w = f'content-library.json {kind} {x.get("id", x.get("term", "?")) if isinstance(x, dict) else "?"}'
                if not shape(x, kind, w, errs): continue
                if kind in ('fact', 'myth') and x['status'] not in ('documented', 'event-only'): errs.append(f'{w}: unknown status {x["status"]}')
                if kind == 'fact' and x['use'] not in USES: errs.append(f'{w}: unknown use {x["use"]}')
                if kind == 'quote':
                    refs([{k: v for k, v in x.items() if k not in ('claim', 'topics', 'entities')} | {'id': x['claim'], 'quote': x['quote']}], w)
                    if not x['quote'] or len(WORD.findall(x['quote'])) > 25: errs.append(f'{w}: quote empty or longer than 25 words')
                elif kind == 'angle':
                    errs += [f'{w}: unknown format {f}' for f in x['formats'] if f not in FORMATS]
                    for pt in x['points']:
                        if shape(pt, 'point', f'{w} point', errs):
                            if pt['status'] not in KSTATUS: errs.append(f'{w}: unknown point status {pt["status"]}')
                            refs(pt['claims'], f'{w} point')
                else: refs(x['claims'], w)
        if lib['version'] != version: errs.append(f'content-library.json is {lib["version"]} but topics.json is {version}: run build_kb.py')


def check_ledgers(nums, difs, qb, byid, topics, ents, lib, version, errs):
    """The ledgers of knowledge graph phase 3 (v2.11.0): numbers.json, differences.json and question-bank.json. Shapes, values, every
    claim public and identical to claims.jsonl, every stat fact of the content kit in the registry, every topic and thing known.
    The community edition has no numbers.json and question-bank.json (None): differences.json is checked alone."""
    def refs(rs, w, kind='lref', labels=None):
        for r in rs:
            if not shape(r, kind, f'{w} claim', errs): continue
            c = byid.get(r['id'])
            if not c: errs.append(f'{w}: claim {r["id"]} is not a public claim of claims.jsonl'); continue
            if any(r[k] != c[k] for k in ('text', 'label', 'verification', 'day', 'session_id')): errs.append(f'{w}: claim {r["id"]} differs from claims.jsonl')
            if not r['cite'].startswith(f'[{r["id"]}, {r["label"]}, '): errs.append(f'{w}: claim {r["id"]} has a bad cite')
            if labels and r['label'] not in labels: errs.append(f'{w}: claim {r["id"]} is a {r["label"]} claim, not {" or ".join(labels)}')
            for x in r['sources']: shape(x, 'csource', f'{w} {r["id"]} source', errs)
    def known(x, w):
        errs.extend(f'{w}: unknown topic {t}' for t in x['topics'] if t not in topics)
        for y in x['entities']:
            if shape(y, 'lento' if 'own' in y else 'lent', f'{w} thing', errs) and y['id'] not in ents: errs.append(f'{w}: unknown thing {y["id"]}')
    if nums is not None and shape(nums, 'numbers', 'numbers.json', errs):
        stat = [f['id'] for f in lib['facts'] if f['use'] == 'stat']
        got = [f.get('id') for f in nums['facts'] if isinstance(f, dict)]
        if got != stat: errs.append(f'numbers.json: the registry must list every stat fact of content-library.json, in order (missing: {sorted(set(stat) - set(got))})')
        for f in nums['facts']:
            w = f'numbers.json {f.get("id", "?") if isinstance(f, dict) else "?"}'
            if not shape(f, 'nfact', w, errs): continue
            if f['status'] not in ('documented', 'event-only'): errs.append(f'{w}: unknown status {f["status"]}')
            if not f['claims']: errs.append(f'{w}: cites no claim')
            refs(f['claims'], w)
            known(f, w)
        refs(nums['candidates'], 'numbers.json candidates', 'ncand')
        errs.extend(f'numbers.json candidate {c["id"]}: no figure' for c in nums['candidates'] if isinstance(c, dict) and not c.get('figures'))
        if nums['version'] != version: errs.append(f'numbers.json is {nums["version"]} but topics.json is {version}: run build_kb.py')
    if shape(difs, 'diffs', 'differences.json', errs):
        seen = set()
        for r in difs['rows']:
            w = f'differences.json {r.get("id", "?") if isinstance(r, dict) else "?"}'
            if not shape(r, 'drow', w, errs): continue
            if not re.fullmatch(r'DIF-\d\d', r['id']) or r['id'] in seen: errs.append(f'{w}: bad or duplicate id')
            seen.add(r['id'])
            if not r['event'] or not (r['docs'] or r['pages']): errs.append(f'{w}: a row needs event claims and docs claims or Google pages')
            refs(r['event'], w, labels=('slide', 'stage'))
            refs(r['docs'], w, labels=('docs',))
            refs(r['analysis'], w, labels=('analysis',))
            for p in r['pages']:
                if shape(p, 'dpage', f'{w} page', errs) and not re.match(r'https://', p['url']): errs.append(f'{w}: page {p["key"]} must be an https URL')
            known(r, w)
        for p in difs['pairs']:
            if not shape(p, 'dpair', 'differences.json pair', errs): continue
            if p['type'] not in ('contradicts', 'updates'): errs.append(f'differences.json pair: type {p["type"]} is not contradicts or updates')
            refs([p['from'], p['to']], 'differences.json pair')
            errs.extend(f'differences.json pair: unknown row {x}' for x in p['rows'] if x not in seen)
        refs(difs['hedged'], 'differences.json hedged')
        if difs['version'] != version: errs.append(f'differences.json is {difs["version"]} but topics.json is {version}: run build_kb.py')
    if qb is not None and shape(qb, 'qbank', 'question-bank.json', errs):
        for q in qb['audience']:
            if not shape(q, 'qaud', 'question-bank.json question', errs): continue
            w = f'question-bank.json question {q["question"].get("id", "?")}'
            refs([q['question']], w)
            refs(q['answers'], w)
            if q['grade'] is not None and q['grade'] not in KSTATUS: errs.append(f'{w}: unknown grade {q["grade"]}')
            known(q, w)
        for t in qb['things']:
            w = f'question-bank.json {t.get("id", "?") if isinstance(t, dict) else "?"}'
            if not shape(t, 'qthing', w, errs): continue
            if t['id'] not in ents: errs.append(f'{w}: unknown thing')
            for k in ('documented', 'event_only'):
                if shape(t[k], 'qtop', f'{w} {k}', errs): refs(t[k]['top'], f'{w} {k}')
        if qb['version'] != version: errs.append(f'question-bank.json is {qb["version"]} but topics.json is {version}: run build_kb.py')


# ------------------------------------------------------------------ links between records (links.json, since v2.8.0)
KIT_ORDER = ('req', 'fact', 'myth', 'quote', 'angle', 'term')  # node id prefixes, in the kind order of every list of kit items
KIT_KIND = {'req': 'requirement', 'fact': 'fact', 'myth': 'myth', 'quote': 'quote', 'angle': 'angle', 'term': 'term'}  # links.json "kind"
KIT_NOUN = {'req': ('requirement', 'requirements'), 'fact': ('fact', 'facts'), 'myth': ('myth', 'myths'), 'quote': ('quote', 'quotes'),
            'angle': ('story angle', 'story angles'), 'term': ('glossary term', 'glossary terms')}
GRADE_ORDER = ('source', 'confirmed', 'consistent', 'undocumented', 'n/a')  # links.json sources.<key>.claims
SPEAKER_GROUPS = ('google', 'community', 'unattributed', 'audience')
SPELL = {'ł': 'l', 'đ': 'd', 'ð': 'd', 'ø': 'o', 'ı': 'i', 'ß': 'ss', 'æ': 'ae', 'œ': 'oe', 'þ': 'th', 'ς': 'σ'}


def fold(s):
    """site.js fold(): lower case, accents and other combining marks removed, a few letters with no decomposition spelled out."""
    s = ''.join(ch for ch in unicodedata.normalize('NFD', str(s).lower()) if not unicodedata.category(ch).startswith('M'))
    return re.sub('[łđðøıßæœþς]', lambda m: SPELL[m[0]], s)


def words(s): return [w for w in re.split(r'[\W_]+', fold(s)) if w]  # site.js norm(): every run of non letter/digit separates words
def term_id(t): return re.sub(r'[^a-z0-9]+', '-', fold(t)).strip('-')
def md_plain(s):
    """A kit text without its Markdown: code spans, bold, links and list or fence markers become plain text."""
    s = re.sub(r'\[([^\]]+)\]\([^)\s]+\)', r'\1', str(s))
    s = re.sub(r'^\s*(?:[-*+]|\d+[.)]|`{3,}\S*|~{3,}\S*)[ \t]*', '', s, flags=re.M)
    return re.sub(r'\s+', ' ', s.replace('**', '').replace('`', '')).strip()
def node_key(n):
    k, i = n.split(':', 1)
    return (KIT_ORDER.index(k), i)


def kit_records(dev, lib):
    """Every kit item, from the kits themselves: node id -> (prefix, record, cited claim ids, page of the site). In the community
    edition a fact, myth, quote or story angle is a preview item: its card is on the Content page."""
    out = {}
    url = (lambda name, i: f'content/index.html#{i}') if community() else (lambda name, i: f'content/{name}.html#{i}')
    for a in dev['areas']:
        for r in a['requirements']: out[f'req:{r["id"]}'] = ('req', r, [x['id'] for x in r['claims']], f'dev/index.html#{r["id"]}')
    for f in lib['facts']: out[f'fact:{f["id"]}'] = ('fact', f, [x['id'] for x in f['claims']], url('facts', f['id']))
    for m in lib['myths']: out[f'myth:{m["id"]}'] = ('myth', m, [x['id'] for x in m['claims']], url('myths', m['id']))
    for q in lib['quotes']: out[f'quote:{q["id"]}'] = ('quote', q, [q['claim']], url('quotes', q['id']))
    for x in lib['angles']: out[f'angle:{x["id"]}'] = ('angle', x, [c['id'] for p in x['points'] for c in p['claims']], url('angles', x['id']))
    for g in lib['glossary']: out[f'term:{g["id"]}'] = ('term', g, [c['id'] for c in g['claims']], f'content/glossary.html#term-{g["id"]}')
    return out


def proven_names(claims, sess, errs):
    """claim id -> the speaker's name where _system/kits.py proven() proves it, for slide and stage claims. The one rule for naming a
    person: never the session-speaker fallback of the `speaker` field."""
    if not (HERE.parent / 'kits.py').exists():
        errs.append('_system/kits.py not found: the speaker filter needs its proven() rule'); return {}
    sys.path.insert(0, str(HERE.parent))
    import kits
    S = {k: {'speaker': s['speakers'], 'role': s['role'], 'note': s['note'], 'kind': s['kind']} for k, s in sess.items()}
    return {c['id']: kits.proven({'label': c['label'], 's': c['session_id'], 'who': c['who']}, S) for c in claims if c['label'] in ('slide', 'stage')}


def check_links(links, claims, byid, topics, sess, sources, dev, lib, version, errs):
    """links.json (written by build_kb.py) against the kits, claims.jsonl and sessions.json: every backlink, topic list, source list
    and speaker name is recomputed here and must match. Returns what the pages and the search index use."""
    w = 'links.json'
    keys = ('version', 'data_through', 'items', 'used_by', 'topic_items', 'sources', 'aliases', 'speakers')
    if not isinstance(links, dict) or set(links) - {'about'} != set(keys) or not all(isinstance(links[k], dict) for k in keys[2:]):
        fail([f'{w}: expected an object with {", ".join(keys)} ({", ".join(keys[2:])} objects) and an optional "about"'])
    if links['version'] != version: errs.append(f'{w} is {links["version"]} but topics.json is {version}: run build_kb.py')
    kit = kit_records(dev, lib)
    for g in lib['glossary']:
        if g['id'] != term_id(g['term']): errs.append(f'content-library.json term {g["term"]!r}: id must be {term_id(g["term"])!r}')
    if len(kit) != sum(len(a['requirements']) for a in dev['areas']) + sum(len(lib[k]) for k in ('facts', 'myths', 'quotes', 'angles', 'glossary')):
        errs.append('dev-requirements.json / content-library.json: two kit items share an id')
    order = sorted(kit, key=node_key)
    items = links['items']
    if list(items) != order: errs.append(f'{w}: items must hold every kit item once, in kind order')
    used = {}
    for n in order:
        kind, x, cids, _ = kit[n]
        for c in dict.fromkeys(cids): used.setdefault(c, []).append(n)
        tps = {t for c in cids if c in byid for t in byid[c]['topics']}
        it = items.get(n)
        if not isinstance(it, dict) or it.get('kind') != KIT_KIND[kind] or set(it.get('claims') or ()) != set(cids):
            errs.append(f'{w} {n}: kind or claims differ from the kits'); continue
        if set(x['topics']) != tps or len(x['topics']) != len(tps) or it.get('topics') != x['topics']:
            errs.append(f'{w} {n}: topics must be the topics of its claims, as in the kit file')
    for c in claims:
        if c['used_by'] != used.get(c['id'], []): errs.append(f'claims.jsonl {c["id"]}: used_by {c["used_by"]} but the kits cite it from {used.get(c["id"], [])}')
    if links['used_by'] != used: errs.append(f'{w}: used_by differs from what the kits cite')
    ti = links['topic_items']
    if set(ti) != set(topics): errs.append(f'{w}: topic_items must have one entry per topic')
    for t in topics:
        want = [n for n in order if t in kit[n][1]['topics']]
        if ti.get(t) != want: errs.append(f'{w}: topic_items {t} must list the kit items with that topic, in kind order')
    cited = {}
    for c in claims:
        for x in c['sources']: cited.setdefault(x['key'], []).append(c['id'])
    if set(links['sources']) != set(sources): errs.append(f'{w}: sources must have one entry per key of sources.json')
    for k in sources:
        v = links['sources'].get(k)
        want = {g: [i for i in cited.get(k, []) if byid[i]['verification'] == g] for g in GRADE_ORDER}
        reqs = [f'req:{r["id"]}' for a in dev['areas'] for r in a['requirements'] if any(d['key'] == k for d in r['docs'])]
        if not isinstance(v, dict) or v.get('claims') != {g: x for g, x in want.items() if x} or sorted(v.get('requirements') or ()) != sorted(reqs):
            errs.append(f'{w}: sources {k} differs from the claims that cite it or the requirements documented in it')
    for a, ns in links['aliases'].items():
        if a != ' '.join(words(a)) or not isinstance(ns, list) or not ns or any(n not in kit and not str(n).startswith('ent:') for n in ns): errs.append(f'{w}: bad alias {a!r}')
    sp = links['speakers']
    proven = proven_names(claims, sess, errs)
    if set(sp) != {'names', 'groups', 'claims'} or not isinstance(sp.get('claims'), dict):
        errs.append(f'{w}: speakers must hold names, groups and claims')
    else:
        if set(sp['claims']) != set(proven): errs.append(f'{w}: speakers.claims must list every slide and stage claim')
        for i, v in sp['claims'].items():
            if not isinstance(v, dict) or v.get('group') not in SPEAKER_GROUPS or v.get('name') != proven.get(i):
                errs.append(f'{w}: speakers.claims {i}: a name is given only where kits.proven() proves it, and the group must be one of {", ".join(SPEAKER_GROUPS)}')
        n = Counter(x for x in proven.values() if x)
        if sp['names'] != [{'name': k, 'claims': v} for k, v in sorted(n.items(), key=lambda x: (-x[1], x[0]))]:
            errs.append(f'{w}: speakers.names must be the proven names, most claims first')
        g = Counter(v.get('group') for v in sp['claims'].values() if isinstance(v, dict))
        if not isinstance(sp['groups'], list) or [x.get('id') for x in sp['groups'] if isinstance(x, dict)] != [k for k in SPEAKER_GROUPS if g[k]] or any(
                x.get('claims') != g[x.get('id')] or not isinstance(x.get('label'), str) for x in sp['groups'] if isinstance(x, dict)):
            errs.append(f'{w}: speakers.groups must count the claims of each group, in the order {", ".join(SPEAKER_GROUPS)}')
    return dict(links=links, kit=kit, kit_order=order, used=used)


# ------------------------------------------------------------------ things (entities.json and claims.jsonl mentions, since v2.9.0)
ENT_KINDS = {'product': ('Product', 'Products'), 'feature': ('Feature', 'Features'), 'crawler': ('Crawler', 'Crawlers'), 'report': ('Report', 'Reports'),
             'directive': ('Directive', 'Directives'), 'status-code': ('Status code', 'Status codes'), 'standard': ('Standard', 'Standards'),
             'metric': ('Metric', 'Metrics'), 'concept': ('Concept', 'Concepts'), 'update': ('Update', 'Updates'), 'tool': ('Tool', 'Tools')}
# hand-written relation types of entities.yaml: (as read from the entity that has it, as read from the other end, needs claims)
ENT_REL = {'is-a': ('Is a', 'Includes', False), 'part-of': ('Part of', 'Has part', False), 'uses': ('Uses', 'Used by', True),
           'affects': ('Affects', 'Affected by', True), 'measured-by': ('Measured by', 'Measures', True), 'applies-to': ('Applies to', 'Subject of', True)}
MENTION_FIELDS = ('text', 'quote', 'pin')
GRADE_SAID = ('undocumented', 'consistent', 'confirmed', 'n/a')  # the order of an entity card: what only the event says comes first


def documented(c): return c['label'] == 'docs' or c['verification'] in ('confirmed', 'consistent')


def check_entities(edoc, claims, byid, topics, taken, sources, sess, L, version, errs):
    """entities.json and the `mentions` of claims.jsonl (both written by build_kb.py from 20-claims/entities.yaml) against the rest of
    the pack: every reference resolves; every mention's `via` is written in the claim; every factual relation cites public claims that
    mention both ends; and what build_kb derives from the mentions (an entity's claims, tally, co-mentions, topics, reverse relations,
    kit items, the things of each topic and session) is recomputed here and must match. Returns what the pages and the search use."""
    w = 'entities.json'
    keys = ('version', 'data_through', 'kinds', 'relation_types', 'entities', 'topic_entities', 'session_entities')
    if not isinstance(edoc, dict) or set(edoc) - {'about'} != set(keys) or not isinstance(edoc['entities'], list) or not all(
            isinstance(edoc[k], dict) for k in ('kinds', 'relation_types', 'topic_entities', 'session_entities')):
        fail([f'{w}: expected an object with {", ".join(keys)} and an optional "about"'])
    if edoc['version'] != version: errs.append(f'{w} is {edoc["version"]} but topics.json is {version}: run build_kb.py')
    if set(edoc['kinds']) != set(ENT_KINDS): errs.append(f'{w}: kinds must be {", ".join(ENT_KINDS)}')
    if set(edoc['relation_types']) != set(ENT_REL): errs.append(f'{w}: relation_types must be {", ".join(ENT_REL)}')
    ents = {}
    for x in edoc['entities']:
        ww = f'{w} {x.get("id", "?") if isinstance(x, dict) else "?"}'
        if not shape(x, 'ent', ww, errs): continue
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', x['id']): errs.append(f'{ww}: id is not kebab-case')
        if x['id'] in ents or x['id'] in taken: errs.append(f'{ww}: id is used twice, or by a topic or an area')
        if x['kind'] not in ENT_KINDS: errs.append(f'{ww}: unknown kind {x["kind"]}')
        if not x['name'].strip() or not x['summary'].strip() or '\n' in x['summary']: errs.append(f'{ww}: name and summary must be non-empty, the summary one line')
        if (x['glossary'] is None) != (x['definition'] is None): errs.append(f'{ww}: glossary and definition go together')
        elif x['glossary'] is not None:
            t = L['kit'].get(f'term:{x["glossary"]}')
            if not t: errs.append(f'{ww}: unknown glossary term {x["glossary"]}')
            elif t[1]['definition'] != x['definition']: errs.append(f'{ww}: definition differs from the glossary term {x["glossary"]}')
        errs += [f'{ww}: unknown source {k}' for k in x['docs'] if k not in sources]
        errs += [f'{ww}: unknown topic {t}' for t in x['topics'] if t not in topics]
        errs += [f'{ww}: unknown claim {i}' for i in x['claims'] if i not in byid]
        for r in x['rel']:
            if not shape(r, 'erel', f'{ww} rel', errs): continue
            if r['type'] not in ENT_REL: errs.append(f'{ww}: unknown relation type {r["type"]}')
            elif ENT_REL[r['type']][2] != bool(r['claims']): errs.append(f'{ww}: a {r["type"]} relation {"needs" if ENT_REL[r["type"]][2] else "takes no"} claims')
        for k, kind in (('rel_from', 'erelf'), ('co_mentioned', 'eco'), ('featured_in', 'ecount'), ('items', 'eitem')):
            for y in x[k]: shape(y, kind, f'{ww} {k}', errs)
        if not isinstance(x['tally'], dict) or not isinstance(x['tally'].get('event'), dict): errs.append(f'{ww}: tally must hold docs, event, press, analysis')
        if not isinstance(x['cite'], dict) or list(x['cite']) != x['claims'] or not all(isinstance(v, str) and v for v in x['cite'].values()):
            errs.append(f'{ww}: cite must hold one citation per claim, in the order of claims')
        ents[x['id']] = x
    if errs: fail(errs)
    ment = {}
    for c in claims:
        ww, ms = f'claims.jsonl {c["id"]}', []
        for m in c['mentions']:
            if not shape(m, 'mention', f'{ww} mention', errs): continue
            if m['entity'] not in ents: errs.append(f'{ww}: mentions unknown entity {m["entity"]}')
            elif m['field'] not in MENTION_FIELDS: errs.append(f'{ww}: mention field must be one of {", ".join(MENTION_FIELDS)}')
            elif m['field'] == 'pin' and m['via'] is not None: errs.append(f'{ww}: a pinned mention of {m["entity"]} has no via')
            elif m['field'] != 'pin' and (not m['via'] or m['via'] not in c[m['field']]): errs.append(f'{ww}: mention of {m["entity"]} via {m["via"]!r} is not written in its {m["field"]}')
            ms.append(m['entity'])
        if ms != sorted(set(ms)): errs.append(f'{ww}: mentions must name each entity once, sorted by id')
        if ms: ment[c['id']] = ms
    if errs: fail(errs)
    # derived, never hand-written: recomputed from the mentions and the kits, and compared with what build_kb wrote
    co, feat, sfeat, rests, rel = {k: {} for k in ents}, {t: Counter() for t in topics}, {s: Counter() for s in sess}, {k: Counter() for k in ents}, {k: [] for k in ents}
    for c in claims:
        es = ment.get(c['id'], ())
        for a in es:
            for b in es:
                if a != b: co[a].setdefault(b, []).append(c['id'])
            for t in c['topics']: feat[t][a] += 1
            sfeat[c['session_id']][a] += 1
            for n in c['used_by']: rests[a][n] += 1
    rank = lambda cnt, key: sorted(cnt, key=lambda k: (-cnt[k], key(k)))
    torder = {t: i for i, t in enumerate(topics)}
    for k in sorted(ents):
        for r in ents[k]['rel']:
            rel[k].append((r['type'], 0, r['to'], r['claims']))
            if r['to'] in rel: rel[r['to']].append((r['type'], 1, k, r['claims']))
    for k, x in ents.items():
        ww = f'{w} {k}'
        cs = [c['id'] for c in claims if k in ment.get(c['id'], ())]
        if x['claims'] != cs: errs.append(f'{ww}: claims must be the claims that mention it, in claims.jsonl order')
        for r in x['rel']:
            if r['to'] not in ents or r['to'] == k: errs.append(f'{ww}: relation {r["type"]} to unknown entity {r["to"]}'); continue
            for i in r['claims']:
                if i not in byid: errs.append(f'{ww}: relation {r["type"]} {r["to"]} cites {i}, not a public claim')
                elif not {k, r['to']} <= set(ment.get(i, ())): errs.append(f'{ww}: relation {r["type"]} {r["to"]} cites {i}, which does not mention both')
        want = sorted(({'type': t, 'from': o, 'claims': cl} for t, back, o, cl in rel[k] if back), key=lambda r: (r['type'], r['from']))
        if x['rel_from'] != want: errs.append(f'{ww}: rel_from must be the relations other things have to it')
        if x['co_mentioned'] != [{'id': o, 'count': len(co[k][o]), 'claims': co[k][o]} for o in sorted(co[k], key=lambda o: (-len(co[k][o]), o))]:
            errs.append(f'{ww}: co_mentioned differs from the claims that name it with another thing')
        ft = Counter({t: feat[t][k] for t in topics if feat[t][k]})
        if x['featured_in'] != [{'id': t, 'count': ft[t]} for t in rank(ft, torder.get)]: errs.append(f'{ww}: featured_in differs from the topics of its claims')
        cl = [byid[i] for i in cs]
        ev = Counter(c['verification'] for c in cl if c['label'] in ('slide', 'stage'))
        lab = Counter(c['label'] for c in cl)
        if x['tally'] != {'docs': lab['docs'], 'event': {g: ev[g] for g in ('undocumented', 'confirmed', 'consistent', 'n/a')}, 'press': lab['press'], 'analysis': lab['analysis']}:
            errs.append(f'{ww}: tally differs from its claims')
        for y in x['items']:
            if y['id'] not in L['kit']: errs.append(f'{ww}: unknown kit item {y["id"]}')
            elif y['count'] != rests[k][y['id']]: errs.append(f'{ww}: kit item {y["id"]} rests on {rests[k][y["id"]]} of its claims, not {y["count"]}')
    for name, got, cnt, ks in (('topic_entities', edoc['topic_entities'], feat, topics), ('session_entities', edoc['session_entities'], sfeat, sess)):
        if set(got) != set(ks): errs.append(f'{w}: {name} must have one entry per {name.split("_")[0]}')
        for t in ks:
            if got.get(t) != [{'id': e, 'count': cnt[t][e]} for e in rank(cnt[t], lambda e: e)]: errs.append(f'{w}: {name} {t} differs from the mentions of its claims')
    about = {}
    for k in sorted(ents):
        for y in ents[k]['items']: about.setdefault(y['id'], []).append({'id': k, 'count': y['count'], 'own': y['own']})
    for a, ns in L['links']['aliases'].items():  # links.json aliases of things (checked against the kits in check_links)
        errs += [f'links.json: alias {a!r} names unknown thing {n}' for n in ns if n.startswith('ent:') and n[4:] not in ents]
    for k, x in ents.items():
        errs += [f'links.json: aliases must map {y!r} to ent:{k}' for y in [x['name']] + x['aliases'] if f'ent:{k}' not in L['links']['aliases'].get(' '.join(words(y)), ())]
    defines = {}
    for k in sorted(ents):
        if ents[k]['glossary']: defines.setdefault(ents[k]['glossary'], []).append(k)
    for n, (kind, x, _, _) in L['kit'].items():  # a kit item's `entities`: the same links seen from the item
        if not all(isinstance(y, dict) for y in x['entities']) or sorted(x['entities'], key=lambda y: str(y.get('id'))) != about.get(n, []):
            errs.append(f'{n}: entities differ from the kit items listed on the things in entities.json')
        if kind == 'term' and x['defines'] != defines.get(x['id'], []): errs.append(f'{n}: defines must list the things whose glossary term it is')
    order = sorted(ents, key=lambda k: (fold(ents[k]['name']), k))
    return dict(ents=ents, ent_order=order, ment=ment, co=co, feat=feat, sfeat=sfeat, erel=rel)


def fail(errs):
    print('\n'.join(f'ERROR: {x}' for x in errs), file=sys.stderr)
    sys.exit(f'{len(errs)} contract violation(s) in the agent pack: site not built')


# ------------------------------------------------------------------ helpers
R = ''  # relative prefix from the page being rendered to the site root


def at(path):
    global R
    R = '../' * path.count('/')


def e(s): return html.escape(str(s), quote=True)
def isodate(s):
    try: return bool(re.fullmatch(r'\d{4}-\d\d-\d\d', s)) and bool(date.fromisoformat(s))
    except ValueError: return False
def u(path): return e(R + path)
def plural(n, word, many=None): return f'{n} {word if n == 1 else many or word + "s"}'
def fdate(iso, weekday=False):
    d = date.fromisoformat(iso)
    return (WEEKDAYS[d.weekday()] + ' ' if weekday else '') + f'{d.day} {MONTHS[d.month - 1]} {d.year}'
def snippet(s, n=120): return s if len(s) <= n else s[:n].rsplit(' ', 1)[0].rstrip(',;:') + '…'
def day_url(n, frag=''): return f'days/day-{n}.html' + (f'#{frag}' if frag else '')
def day_sec(d, count): return sec(f'Day {d["day"]}: {d["theme"]}', f'day-{d["day"]}', count)
def has_page(s): return s['claim_count'] > 0 or s['kind'] not in ('break', 'unrecorded')
def stitle(s): return 'session not recorded' if s['kind'] == 'unrecorded' else s['title']  # after "Day N ·", S00's title would repeat the day
def session_url(s): return f'sessions/{s["id"]}.html' if has_page(s) else f'days/day-{s["day"]}.html#{s["id"]}'
def summary_html(s): return re.sub(r'Author(?:&#x27;|’)s view:', '<strong class="aview">Author’s view:</strong>', e(s))
def inline_md(s):
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', e(s))
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', re.sub(r'`([^`]+)`', r'<code>\1</code>', s))
def ornament(cls='orn'):
    return (f'<svg class="{cls}" viewBox="0 0 240 20" aria-hidden="true" focusable="false"><path d="M0 10H99M141 10H240" stroke="currentColor"/>'
            '<path d="M20 14.5H95M145 14.5H220" stroke="currentColor" stroke-width=".5"/><path d="M120 1l9 9-9 9-9-9z" fill="currentColor"/>'
            '<path d="M104 10l4-4 4 4-4 4zM128 10l4-4 4 4-4 4z" fill="none" stroke="currentColor" stroke-width=".8"/></svg>')
def fan(cls='fan'):
    rays = ''.join(f'<path d="M20 20L{20 - math.cos(math.pi * i / 8) * 19:.1f} {20 - math.sin(math.pi * i / 8) * 19:.1f}"/>' for i in range(1, 8))
    return (f'<svg class="{cls}" viewBox="0 0 40 21" aria-hidden="true" focusable="false"><g stroke="currentColor" stroke-width="1.1">{rays}</g>'
            '<path d="M13 20a7 7 0 0 1 14 0z" fill="currentColor"/><path d="M0 20.5h40" stroke="currentColor"/></svg>')
def sunburst():
    cx, cy = 600, 660
    p = ['<svg class="burst" viewBox="0 0 1200 620" preserveAspectRatio="xMidYMax slice" aria-hidden="true" focusable="false">']
    p += [f'<path class="{"r1" if i % 2 == 0 else "r2"}" d="M{cx} {cy}L{cx - math.cos(math.pi * i / 40) * 1400:.1f} {cy - math.sin(math.pi * i / 40) * 1400:.1f}"/>' for i in range(1, 40)]
    p += [f'<path class="{"a1" if k in (0, 3) else "a2"}" d="M{cx - r} {cy}A{r} {r} 0 0 1 {cx + r} {cy}"/>' for k, r in enumerate((130, 175, 220, 300, 390, 500))]
    return ''.join(p) + f'<path class="sun" d="M{cx - 130} {cy}A130 130 0 0 1 {cx + 130} {cy}z"/></svg>'


def badge_label(lab): return f'<span class="badge lab lab-{lab}" title="{e(LABELS[lab][1])}">{LABELS[lab][0]}</span>'
def badge_ver(v): return f'<span class="badge ver ver-{v.replace("/", "")}" title="{e(VER[v][1])}">{VER[v][0]}</span>' if VER[v][0] else ''
def cid_link(cid, anchor=False): return f'<a class="cid" href="{"#" + cid if anchor else u("claims.html#" + cid)}">{cid}</a>'


def evidence(ev):
    k = Counter()
    for x in ev:
        k['slide photo' if re.fullmatch(r'IMG_\d+', x) else 'video' if x.startswith('video:') else 'transcript' if re.match(r'T[: ]', x)
          else x if x in ('notes', 'agenda') else 'other record'] += 1
    return ', '.join(f'{n} {w}s' if n > 1 and w in ('slide photo', 'video') else w for w, n in k.items())


def who_line(c, K, show_session=True):
    s = K['sess'][c['session_id']]
    bits = []
    if c['label'] in ('slide', 'stage'):
        w = {'audience': 'From the audience', 'unknown': 'Speaker not identified'}.get(c['who']) or c['speaker']
        if w: bits.append(f'<span class="by">{e(w)}</span>' if c['who'] in ('audience', 'unknown') else f'<span class="by"><span class="k">Speaker</span> {e(w)}</span>')
    else:
        k = {'docs': 'Publisher', 'press': 'Reported by', 'analysis': 'Author'}[c['label']]
        bits.append(f'<span class="by"><span class="k">{k}</span> {e(c["author"])}</span>')
    if show_session:
        k = 'Annotates' if c['label'] in ('docs', 'press', 'analysis') else 'In'
        bits.append(f'<span class="in"><span class="k">{k}</span> <a href="{u(session_url(s))}">Day {s["day"]}{", " + s["time"] if s["time"] else ""} · {e(stitle(s))}</a></span>')
    if c['label'] in ('slide', 'stage') and c['evidence']:
        bits.append(f'<span class="ev"><span class="k">Evidence</span> {e(evidence(c["evidence"]))}</span>')
    return f'<p class="claim-by">{"".join(bits)}</p>'


def rel_items(c, K, skip=()):
    """skip: claim ids whose 'answers' link is not listed, because the question and its answer are shown together."""
    out = []
    for r in c['relations']:
        if not (r['type'] == 'answers' and r['to'] in skip): out.append((REL[r['type']][0], r['type'], r['to']))
    for r in c['related_from']:
        if not (r['type'] == 'answers' and r['from'] in skip): out.append((REL[r['type']][1], r['type'], r['from']))
    if not out: return ''
    li = ''.join(f'<li><span class="rel rel-{t}">{v}</span> {cid_link(o)} <span class="rel-text">Day {K["byid"][o]["day"]}: {e(snippet(K["byid"][o]["text"], 110))}</span></li>' for v, t, o in out)
    return f'<ul class="rels" aria-label="Links to other claims">{li}</ul>'


def claim_card(c, K, show_session=True, anchor=True, show_topics=True, skip_rel=()):
    lab = c['label']
    head = f'<div class="claim-head">{badge_label(lab)}{badge_ver(c["verification"])}<span class="sp"></span>{cid_link(c["id"])}</div>'
    body = f'<p class="claim-text">{e(c["text"])}</p>'
    if c['quote']:
        chk = '<p class="q-check">Wording checked against the slide or recording</p>' if c['quote_checked'] else ''
        q = c['quote'].strip('"')
        body += f'<blockquote class="quote"><p>“{e(q)}”</p>{chk}</blockquote>'
    body += who_line(c, K, show_session)
    if show_topics:
        body += '<ul class="chips small" aria-label="Topics">' + ''.join(f'<li><a href="{u("topics/" + t + ".html")}">{e(K["topics"][t]["title"])}</a></li>' for t in c['topics']) + '</ul>'
    body += ent_chips(c, K) + used_by(c, K)
    if c['sources']:
        body += '<ul class="srcs" aria-label="Sources">' + ''.join(source_li(x) for x in c['sources']) + '</ul>'
    body += rel_items(c, K, skip_rel)
    idattr = f' id="{c["id"]}"' if anchor else ''
    return f'<article class="claim c-{lab}"{idattr} data-label="{lab}" data-grade="{c["verification"].replace("/", "")}" data-day="{c["day"]}">{head}{body}</article>'


def kit_name(n, K):
    """How a kit item is named in a list: its id (DEV-SRV-01, F-012), or a glossary term by the term itself."""
    kind, x, _, _ = K['kit'][n]
    return x['term'] if kind == 'term' else x['id']


def kit_title(n, K):
    kind, x, _, _ = K['kit'][n]
    return {'req': lambda: md_plain(x['title']), 'fact': lambda: x['statement'], 'myth': lambda: 'Myth: ' + x['myth'], 'quote': lambda: f'“{x["quote"]}”',
            'angle': lambda: x['title'], 'term': lambda: x['definition']}[kind]()


def kit_links(ns, K):
    """Kit items grouped by kind: 'requirements DEV-SRV-01, DEV-SRV-02 · fact F-012 · glossary term Crawl stats'."""
    out = []
    for kind in KIT_ORDER:
        g = [n for n in ns if n.startswith(kind + ':')]
        if not g: continue
        a = ', '.join(f'<a class="{"ub-term" if kind == "term" else "cid"}" href="{u(K["kit"][n][3])}" title="{e(snippet(kit_title(n, K), 160))}">{e(kit_name(n, K))}</a>' for n in g)
        out.append(f'<span class="ub-g"><span class="ub-k">{KIT_NOUN[kind][len(g) > 1]}</span> {a}</span>')
    return ''.join(out)


def used_by(c, K):
    """What rests on a claim: the kit items whose claims cite it (claims.jsonl used_by, checked against the kits)."""
    return f'<p class="used-by"><span class="k">Used by</span>{kit_links(c["used_by"], K)}</p>' if c['used_by'] else ''


def source_li(x):
    press = ' <span class="badge lab lab-press">Press</span>' if x['kind'] == 'press' else ''
    return (f'<li><a class="ext" href="{e(x["url"])}" rel="noopener external">{e(x["title"])}</a>{press} '
            f'<span class="src-meta">{e(x["publisher"])} · checked {fdate(x["checked"])}</span></li>')


def sec(title, sid='', count=None, level=2):
    n = f' <span class="count">{count}</span>' if count is not None else ''
    idattr = f' id="{sid}"' if sid else ''
    return f'<h{level} class="sec-h"{idattr}>{e(title)}{n}</h{level}>'


def pairs(rels, K):
    """rels: list of (from_id, type, to_id). One row per relation: later claim, verb, earlier claim."""
    rows = []
    for a, t, b in rels:
        side = lambda c: (f'<div class="pair-c">{badge_label(c["label"])} {cid_link(c["id"])} <span class="pair-day">Day {c["day"]} · '
                          f'<a href="{u(session_url(K["sess"][c["session_id"]]))}">{e(stitle(K["sess"][c["session_id"]]))}</a></span>'
                          f'<p>{e(c["text"])}</p></div>')
        rows.append(f'<li class="pair">{side(K["byid"][a])}<div class="pair-v"><span class="rel rel-{t}">{REL[t][0].lower()}</span></div>{side(K["byid"][b])}</li>')
    return f'<ol class="pairs">{"".join(rows)}</ol>' if rows else ''


def all_rels(K, ids=None, answers=False):
    out = []
    for c in K['claims']:
        for r in c['relations']:
            if ids is not None and c['id'] not in ids and r['to'] not in ids: continue
            if not answers and r['type'] == 'answers': continue
            out.append((c['id'], r['type'], r['to']))
    order = list(REL)
    return sorted(out, key=lambda x: (order.index(x[1]), x[0], x[2]))


def stats(items):
    return '<dl class="stats">' + ''.join(f'<div><dt>{e(k)}</dt><dd>{v}</dd></div>' for k, v in items) + '</dl>'


def label_mix(cs):
    n = Counter(c['label'] for c in cs)
    return ' '.join(f'<span class="mix">{badge_label(k)} {n[k]}</span>' for k in LABELS if n[k])


# ------------------------------------------------------------------ page shell
NAV = [('days/day-{n}.html', 'Day {n}'), ('topics.html', 'Topics'), ('entities.html', 'Things'), ('graph.html', '{map}'), ('verification.html', 'Verification'), ('across-days.html', 'Across days'),
       ('sources.html', 'Sources'), ('claims.html', 'All claims'), ('dev/index.html', 'Developers'), ('content/index.html', 'Content'), ('about.html', 'How to read')]


def contact(name, url):
    """A link of edition.yaml (the company or LinkedIn), opened in a new tab; the name alone when no address is set."""
    if not name: return ''
    return f'<a class="ext contact" href="{e(url)}" rel="noopener external" target="_blank">{e(name)}</a>' if url else e(name)


def contacts():
    """The company and LinkedIn as links, '[Company name] · LinkedIn' (each left out when edition.yaml does not give it)."""
    return ' · '.join(x for x in (contact(ED['company']['name'], ED['company']['url']), contact('LinkedIn', ED['linkedin']) if ED['linkedin'] else '') if x)


def foot_edition():
    """The community edition's one quiet line under the footer of every page."""
    who = f'Community edition by {e(ED["author"])}' if ED['author'] else 'Community edition'
    return f'<p class="foot-ed">{" · ".join(x for x in (who, contacts(), "Open for collaboration on this community version") if x)}</p>'


LICENCE_LINE = 'Content CC BY-NC 4.0 · Developer kit CC BY 4.0 · Code MIT'


def foot_legal():
    """The published community edition's line under it: the licences (linking LICENSE-CONTENT.md of the repository), Impressum
    and Privacy, each only when its address is in edition.yaml."""
    if not community(): return ''
    bits = [own_link(repo_file('LICENSE-CONTENT.md'), LICENCE_LINE) if ed_url('repo_url') else '',
            own_link(ed_url('impressum_url'), 'Impressum') if ed_url('impressum_url') else '',
            own_link(ed_url('privacy_url'), 'Privacy') if ed_url('privacy_url') else '']
    bits = [x for x in bits if x]
    return f'<p class="foot-legal">{" · ".join(bits)}</p>' if bits else ''


# ------------------------------------------------------------------ the published community edition: head tags, JSON-LD, 404 base
def base_tag():
    """404.html's <base>: a plain tag before anything with an address, so the browser (its preload scanner included, and without
    JavaScript) resolves the style sheet, the scripts, the icon and the links from the site root at any depth."""
    return f'<base href="{e(site_url())}">'


def ld_script(obj):
    """One JSON-LD block; '<' is escaped, so no text in it can close the script."""
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + '</script>'


def breadcrumb_ld(path, title, crumbs):
    """The BreadcrumbList of a page's visible crumbs: Overview, the crumbs, the page itself, all as absolute addresses."""
    items = [('index.html', 'Overview')] + list(crumbs) + [(path, title)]
    return {'@context': SCHEMA_ORG, '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i, 'name': t, 'item': abs_url(p)} for i, (p, t) in enumerate(items, 1)]}


def home_ld(K):
    """The home page's JSON-LD: the WebSite (its name as the page title shows it) and the Organization named in every footer."""
    out = [{'@context': SCHEMA_ORG, '@type': 'WebSite', 'name': site_name(K), 'url': site_url(), 'inLanguage': 'en'}]
    if ED['company']['name'] and ED['company']['url']:
        org = {'@context': SCHEMA_ORG, '@type': 'Organization', 'name': ED['company']['name'], 'url': ED['company']['url']}
        if ED['linkedin']: org['sameAs'] = [ED['linkedin']]
        out.append(org)
    return out


def site_name(K): return f'{K["event"]["name"]} · Knowledge base'


def og_image():
    """The share image (site path, source), or None when _system/brand/social/og-image.png is not there."""
    return OG_IMAGE if site_url() and OG_IMAGE[1].exists() else None


def share_desc(desc, n=300):
    """A page description as a share preview shows it: whole sentences up to about n characters, else words and an ellipsis
    (a topic page's description is its whole summary). desc is escaped, and so is the result."""
    t = html.unescape(desc)
    if len(t) <= n: return desc
    cut = t[:n + 1]
    end = max(cut.rfind('. '), cut.rfind('? '))
    return e(cut[:end + 1]) if end > n // 2 else e(cut.rsplit(' ', 1)[0].rstrip(',;:') + '…')


def seo_head(path, full, desc, K, robots):
    """The head lines of the published community edition (none without site_url): robots, canonical (indexable pages only),
    Open Graph and Twitter (not on 404.html). full and desc are escaped already."""
    if not site_url(): return ''
    desc = share_desc(desc)
    out = [f'<meta name="robots" content="{robots}">'] if robots else []
    if not robots: out.append(f'<link rel="canonical" href="{e(abs_url(path))}">')
    if path != '404.html':
        img = og_image()
        out += [f'<meta property="og:type" content="website">', f'<meta property="og:site_name" content="{e(site_name(K))}">',
                f'<meta property="og:title" content="{full}">', f'<meta property="og:description" content="{desc}">',
                f'<meta property="og:url" content="{e(abs_url(path))}">', '<meta property="og:locale" content="en_GB">']
        if img:
            out += [f'<meta property="og:image" content="{e(abs_url(img[0]))}">', '<meta property="og:image:type" content="image/png">',
                    f'<meta property="og:image:width" content="{OG_SIZE[0]}">', f'<meta property="og:image:height" content="{OG_SIZE[1]}">',
                    f'<meta property="og:image:alt" content="{e(OG_ALT)}">']
        out += [f'<meta name="twitter:card" content="{"summary_large_image" if img else "summary"}">', f'<meta name="twitter:title" content="{full}">',
                f'<meta name="twitter:description" content="{desc}">']
        if img: out += [f'<meta name="twitter:image" content="{e(abs_url(img[0]))}">', f'<meta name="twitter:image:alt" content="{e(OG_ALT)}">']
    return ''.join(x + '\n' for x in out)


MAP_DESC = {'graph.html': 'The Reef map: start from any thing or topic, see its neighbourhood and follow the links.',
            'mindmap.html': 'The interactive topic map: every area and topic as a tree you can expand and search.'}


def map_seo(t, path, K):
    """The Reef map and the topic map keep their own frame; in the published community edition (site_url) their head gets the
    same canonical link and social tags as every other page, after the color-scheme line (the web edition's copies only)."""
    anchor = '<meta name="color-scheme" content="light dark">\n'
    m = re.search(r'<title>(.*?)</title>', t, re.S)
    if not site_url() or anchor not in t or not m: return t
    return t.replace(anchor, anchor + seo_head(path, m[1].strip(), e(MAP_DESC[path]), K, ''), 1)


def map_name(deep, deco):
    """The explorer's name in each style (decision D5): "Reef map" in Deep Dive, "Graph" in Art Deco; site.css shows one."""
    return f'<span class="nm-dd">{deep}</span><span class="nm-deco">{deco}</span>'


def page(path, title, main, K, desc='', crumbs=(), head=None, scripts=(), section='', bot='', robots='', ld=()):
    """bot: a diver bot pose ('read', 'point', 'wave') shown beside the page head in Deep Dive (decorative).
    robots, ld: the published community edition only (site_url): a robots meta value (such a page gets no canonical link) and
    JSON-LD objects for the head (a page with crumbs also gets its BreadcrumbList)."""
    at(path)
    nav = []
    for p, label in NAV:
        for n in ([d['day'] for d in K['days']] if '{n}' in p else [None]):
            q, lab = p.format(n=n), label.format(n=n, map=map_name('Reef map', 'Graph'))
            cur = ' aria-current="page"' if q == path else ' class="on"' if q == section else ''
            nav.append(f'<li><a href="{u(q)}"{cur}>{lab}</a></li>')
    cr = ''
    if crumbs:
        cr = '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + ''.join(
            f'<li><a href="{u(p)}">{e(t)}</a></li>' for p, t in [('index.html', 'Overview')] + list(crumbs)) + f'<li><span aria-current="page">{e(title)}</span></li></ol></nav>'
    hd = ''
    if head:
        eyebrow, h1, lead, meta = head
        # Deep Dive motion layers first (decorative, aria-hidden): light rays, night plankton, the occasional crossing school,
        # and on heads without the bot the reef accent as separate fish (the bot keeps its place on .page-head.has-bot::after)
        hd = (f'<header class="page-head{" has-bot bot-" + bot if bot else ""}">{DD_HEAD}{"" if bot else reef_markup()}<div class="wrap">'
              f'{cr}<p class="eyebrow">{eyebrow}</p><h1>{e(h1)}</h1>{ornament()}'
              + (f'<p class="lead">{lead}</p>' if lead else '') + (f'<div class="head-meta">{meta}</div>' if meta else '') + '</div></header>')
    sc = ''.join(f'<script src="{u(s)}" defer></script>' for s in scripts)
    full = e(title) if path == 'index.html' else f'{e(title)} · {e(K["short"])}'
    # before the first paint: mark JavaScript as on (the page's style is the build's, from theme.yaml; nothing in the browser changes it)
    boot = "<script>document.documentElement.classList.add('js')</script>"
    icon = u('assets/icon-deep-dive.svg' if STYLE == 'deep-dive' else 'assets/icon.svg')  # the diver bot's head in Deep Dive, the gold fan in Art Deco
    # the published community edition (site_url): 404.html is served for missing paths at any depth, so it resolves its links
    # from the site root (a plain <base>); robots, canonical, social tags and JSON-LD (all empty in the full edition)
    base = base_tag() + '\n' if path == '404.html' and site_url() else ''
    seo = seo_head(path, full, e(desc or title), K, robots)
    lds = list(ld) + ([breadcrumb_ld(path, title, crumbs)] if crumbs and site_url() else [])
    ldh = ''.join(ld_script(x) + '\n' for x in lds) if site_url() else ''
    return f'''<!doctype html>
<html lang="en" data-style="{STYLE}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{base}<title>{full}</title>
<meta name="description" content="{e(desc or title)}">
{seo}<meta name="color-scheme" content="light dark">
<link rel="icon" href="{icon}" type="image/svg+xml">
<link rel="stylesheet" href="{u('assets/site.css')}">
{ldh}{boot}
{sc}<script src="{u('assets/site.js')}" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="mast">
<div class="wrap mast-row">
<a class="brand" href="{u('index.html')}">{fan('brand-fan')}<span class="brand-mark" aria-hidden="true"></span><span class="brand-text"><span class="brand-k">Search Central Live</span><span class="brand-t">{e(K['short'])}</span></span></a>
<p class="mast-ver">Knowledge base {e(K['version'])}{' · Community edition' if community() else ''}<span> · data through {fdate(K['through']) if K['through'] else 'none yet'}</span></p>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-nav" hidden><span class="bars" aria-hidden="true"></span>Menu</button>
</div>
<nav id="site-nav" class="site-nav" aria-label="Main"><div class="wrap nav-row"><ul>{''.join(nav)}</ul>
<form class="nav-search" role="search" action="{u('search.html')}" method="get"><label class="vh" for="q-nav">Search the knowledge base</label><input id="q-nav" name="q" type="search" placeholder="Keywords" autocomplete="off"><button type="submit">Search</button></form>
</div></nav>
<div class="surface" aria-hidden="true"></div>
</header>
<main id="main" tabindex="-1">
{hd}
{main}
</main>
<footer class="foot">{DD_PLANKTON}
<div class="wrap"><span class="foot-bot" aria-hidden="true"></span>{ornament('orn foot-orn')}
<div class="foot-grid">
<div><p class="foot-k">This edition</p><p>Knowledge base {e(K['version'])}, data through {fdate(K['through']) if K['through'] else 'none yet'}. Built from the public agent pack: {plural(len(K['claims']), 'claim')}, {plural(len(K['topics']), 'topic')}, {plural(len(K['sources']), 'source')}.</p></div>
<div><p class="foot-k">About</p><p>An independent attendee resource by Ibrahim Anjro, not an official Google publication. Paraphrases and short quotations only; no slide photos or transcripts.</p></div>
<div><p class="foot-k">Find your way</p><ul class="foot-links"><li><a href="{u('index.html')}">Overview</a></li><li><a href="{u('about.html')}">How to read this site</a></li><li><a href="{u('search.html')}">Search</a></li><li><a href="{u('sources.html')}">Sources</a></li><li><a href="{u('dev/index.html')}">For developers</a></li><li><a href="{u('content/index.html')}">For content teams</a></li>{method_li()}</ul></div>
</div>{foot_edition() + foot_legal() if community() else ''}</div>
</footer>
</body>
</html>
'''


# ------------------------------------------------------------------ pages
def index_page(K, pdfs, mindmap, log=None):
    ev, claims = K['event'], K['claims']
    real = [s for s in K['sess'].values() if s['kind'] not in ('break', 'unrecorded')]
    d0, d1 = K['days'][0]['date'], K['days'][-1]['date']
    name, year = re.fullmatch(r'(.*?)\s*(\d{4})?', K['short']).groups()
    at('index.html')
    hero = (f'<section class="hero" aria-labelledby="hero-t">{sunburst()}<span class="drift" aria-hidden="true"><i></i><i></i><i></i><i></i></span>{DD_PLANKTON}<span class="hero-bot" aria-hidden="true"></span><div class="wrap"><div class="step hero-frame"><div class="in">'
            f'<p class="hero-k">Search Central Live · {e(ev["city"])}</p><h1 id="hero-t" class="hero-t"><span>{e(name)}</span> '
            f'<span class="hero-y">{e(year or "")}</span></h1>{ornament("orn hero-orn")}'
            f'<p class="hero-sub">{fdate(d0)} to {fdate(d1)} · {plural(len(K["days"]), "day")}</p>'
            f'<p class="hero-lead">The knowledge base, web edition: every public claim from the event, labelled by who said it and checked against '
            f'Google’s own documentation.</p><p class="hero-meta">Version {e(K["version"])} · data through {fdate(K["through"]) if K["through"] else "none yet"}</p>'
            '</div></div></div></section>')
    st = stats([('Claims', len(claims)), ('Sessions', len(real)), ('Topics', len(K['topics'])), ('Sources', len(K['sources'])),
                ('Days covered', f'{sum(1 for d in K["days"] if any(c["day"] == d["day"] for c in claims))}<small>/{len(K["days"])}</small>')])
    top = sorted(K['topics'].values(), key=lambda t: (-len(t['event_sessions']), -len(t['claim_ids']), t['title']))[:8]
    und = [c for c in claims if c['label'] in ('slide', 'stage') and c['verification'] == 'undocumented']
    start = [
        ('How to read', 'Labels and grades', 'about.html', 'Every claim carries a label for who is speaking and a grade for how it stands against Google’s documentation. Two minutes here makes the rest easy.'),
        ('Fragile and valuable', f'{plural(len(und), "claim")} not in the docs', 'verification.html', 'What was said or shown at the event, by Google or a community speaker, that Google’s documentation does not say. Quote these as said at Search Central Live.'),
        ('Find anything', 'Search the knowledge base', 'search.html', 'Search every thing, claim, topic, session, kit item and glossary term as you type, typos and abbreviations included. Works offline, straight from this folder.'),
    ]
    tiles = ''.join(f'<li class="step tile"><div class="in"><p class="tile-k">{k}</p><h3><a class="stretch" href="{u(p)}">{e(t)}</a></h3><p>{d}</p></div></li>' for k, t, p, d in start)
    reqs, lib = dev_reqs(K), K['lib']
    kits = kit_tiles([('Developer kit', 'For developers', 'dev/index.html', f'{plural(len(reqs), "requirement")} by area, with why, how, test and code, '
                       f'a pre-launch checklist and {plural(len(K["dev"]["snippets"]), "snippet")}, for sites Google can crawl, render, index and show well.'),
                      ('Content kit', 'For content teams', 'content/index.html', f'A glossary of {plural(len(lib["glossary"]), "term")} in plain English, open to everyone, '
                       'and a small taste of the media kit for posts, articles and newsletters.') if community() else
                      ('Content kit', 'For content teams', 'content/index.html', f'{plural(len(lib["facts"]), "fact")}, {plural(len(lib["myths"]), "myth")}, '
                       f'{plural(len(lib["angles"]), "story angle")}, {plural(len(lib["quotes"]), "quote")} and a glossary, each tied to its evidence.')])
    raised = ''.join(f'<li><a href="{u("topics/" + t["id"] + ".html")}">{e(t["title"])}</a><span>{plural(len(t["event_sessions"]), "session")}</span></li>' for t in top)
    raised = (f'<section aria-labelledby="raised">{sec("Raised most often", "raised")}<p class="blurb">Topics the event returned to in the most sessions.</p>'
              f'<ol class="toplist">{raised}</ol><p class="more"><a href="{u("topics.html")}">All topics</a></p></section>')
    daycards = ''
    for d in K['days']:
        cs = [c for c in claims if c['day'] == d['day']]
        n = sum(1 for s in d['sessions'] if s['kind'] not in ('break', 'unrecorded'))
        state = (f'<p class="tile-stats">{plural(n, "session")} · {plural(len(cs), "claim")}</p><p class="mixes">{label_mix(cs)}</p>' if cs
                 else '<p class="tile-stats soon">Not yet available</p>')
        daycards += (f'<li class="step tile day-tile{"" if cs else " is-soon"}"><div class="in"><p class="day-n" aria-hidden="true">{d["day"]}</p>'
                     f'<p class="tile-k">Day {d["day"]} · {fdate(d["date"], True)}</p><h3><a class="stretch" href="{u(day_url(d["day"]))}">{e(d["theme"])}</a></h3>{state}</div></li>')
    rels = [x for x in all_rels(K) if K['byid'][x[0]]['day'] != K['byid'][x[2]]['day']]
    cnt = Counter(t for _, t, _ in rels)
    new = ''
    if rels:
        new = ('<p class="rel-sum">' + ' '.join(f'<span class="mix"><span class="rel rel-{t}">{REL[t][0]}</span> {cnt[t]}</span>' for t in REL if cnt[t]) + '</p>'
               + pairs(rels[:4], K) + f'<p class="more"><a href="{u("across-days.html")}">All {plural(len(rels), "link")} between days</a></p>')
    else:
        new = '<p>Links between days appear here once a later day repeats, extends, contradicts or updates an earlier one.</p>'
    latest = [d for d in K['days'] if d['date'] == K['through']]
    if latest:
        d = latest[0]
        n = sum(c['day'] == d['day'] for c in claims)
        new = f'<p class="lead-s">Newest: <a href="{u(day_url(d["day"]))}">Day {d["day"]}, {e(d["theme"])}</a>, with {plural(n, "claim")}.</p>' + new
    notes = ''.join(f'<li>{inline_md(x)}</li>' for x in K['notes'])
    changes = f'<div class="callout"><p class="callout-k">In version {e(K["version"])}</p><ul>{notes}</ul></div>' if notes else ''
    areas = ''
    for a in K['areas']:
        n = len({i for t in a['topics'] for i in t['claim_ids']})
        areas += (f'<li class="step tile area-tile"><div class="in"><p class="tile-k">{plural(len(a["topics"]), "topic")} · {plural(n, "claim")}</p>'
                  f'<h3><a class="stretch" href="{u("areas/" + a["id"] + ".html")}">{e(a["title"])}</a></h3><p>{e(a["blurb"])}</p></div></li>')
    dl = ''.join(f'<li><a href="{u("downloads/" + p.name)}"><span class="dl-t">{e(t)}</span><span class="dl-m">PDF · {size}</span></a></li>' for p, t, size in pdfs)
    if mindmap: dl = f'<li><a href="{u("mindmap.html")}"><span class="dl-t">Interactive topic map</span><span class="dl-m">Opens in this browser</span></a></li>' + dl
    if log and pdfs: dl += (f'<li><a href="{u("downloads/" + log.name)}"><span class="dl-t">Classic editions log: what the Art Deco and modern guides lack</span>'
                          f'<span class="dl-m">Markdown · plain text</span></a></li>')
    downloads = f'<section class="band"><div class="wrap">{sec("Take it with you", "downloads")}<ul class="downloads">{dl}</ul></div></section>' if dl else ''
    days_title = f'The {NUMS.get(len(K["days"]), len(K["days"]))} days'
    main = (f'{hero}<div class="wrap">{st}{tour_section()}'
            f'<section aria-labelledby="start">{sec("Start here", "start")}<ul class="tiles start">{tiles}</ul>{quick_links(bool(pdfs))}</section>'
            f'<section aria-labelledby="kits">{sec("Put it to work", "kits")}{kits}</section>'
            f'<section aria-labelledby="days">{sec(days_title, "days")}<ul class="tiles days">{daycards}</ul></section>'
            f'<div class="two"><section aria-labelledby="new">{sec("What’s new across days", "new")}{new}</section><div>{changes}{raised}</div></div>'
            f'<section aria-labelledby="areas">{sec("Areas", "areas")}<ul class="tiles areas">{areas}</ul><p class="more"><a href="{u("topics.html")}">Every topic on one page</a></p></section>'
            f'</div>{downloads}')
    return page('index.html', f'{K["event"]["name"]} · Knowledge base', main, K, desc=f'Knowledge base for {K["event"]["name"]}, {K["event"]["city"]}: claims, topics, sessions and verification.',
                ld=home_ld(K) if site_url() else ())


def tour_ok():
    """The tour is on the home page of the community edition when its video and poster are both in _system/brand/video/."""
    return community() and all(p.exists() for p in TOUR.values())


def tour_section():
    """The home page's 1-minute tour (community edition): a plain video player, nothing loads before the reader presses play."""
    if not tour_ok(): return ''
    size = TOUR['assets/video/tour.mp4'].stat().st_size
    mb = f'{size / 1048576:.1f} MB'
    mp4, poster = u('assets/video/tour.mp4'), u('assets/video/tour-poster.jpg')
    return (f'<section class="tour" id="tour" aria-labelledby="tour-h">{sec("Watch the 1-minute tour", "tour-h")}'
            '<p class="blurb">The Diver bot swims through the knowledge base: how every point is labelled and checked against Google’s documentation, '
            'the field guides, this web edition, the Reef map and the kits.</p>'
            f'<figure class="tour-fig"><div class="tour-frame"><video controls preload="none" playsinline poster="{poster}" width="1920" height="1080" aria-describedby="tour-cap">'
            f'<source src="{mp4}" type="video/mp4"><p>This browser cannot play the video here. <a href="{mp4}">Download the tour</a> (MP4, {mb}).</p></video></div>'
            f'<figcaption id="tour-cap">About a minute, with sound; it plays only when you press play. <a href="{mp4}">Download the video</a> (MP4, {mb}).</figcaption>'
            '</figure></section>')


def quick_links(pdfs):
    """The home page's quick links (community edition): the method write-up, the developer kit, the agent pack and the code in
    the repository, the field guides."""
    if not community(): return ''
    items = [f'<a href="{u("method.html")}">How the claims were graded</a>', f'<a href="{u("dev/index.html")}">Developer kit</a>']
    if ed_url('repo_url'):
        items.append(own_link(f'{ed_url("repo_url")}/tree/HEAD/60-outputs/agent-pack', 'Agent pack for AI agents'))
    if pdfs: items.append(f'<a href="#downloads">Field guides (PDF)</a>')
    if ed_url('repo_url'): items.append(own_link(ed_url('repo_url'), 'The repository on GitHub'))
    return '<nav class="quick" aria-label="Quick links"><p class="quick-k">Quick links</p><ul>' + ''.join(f'<li>{x}</li>' for x in items) + '</ul></nav>'


def day_page(d, K):
    path = f'days/day-{d["day"]}.html'
    at(path)
    cs = [c for c in K['claims'] if c['day'] == d['day']]
    rows = ''
    for s in d['sessions']:
        title = f'<a href="{u(session_url(s))}">{e(s["title"])}</a>' if has_page(s) else e(s['title'])
        who, role = ', '.join(s['speakers']), f'<span class="role">, {e(s["role"])}</span>' if s['role'] else ''
        who = f'<p class="ag-who">{e(who)}{role}</p>' if who else ''
        note = f'<p class="ag-note">{e(s["note"])}</p>' if s['note'] else ''
        cov = ''.join(f'<li class="cov cov-{c}">{COVERAGE[c]}</li>' for c in s['coverage'])
        cnt = f'<span class="ag-count"><b>{s["claim_count"]}</b> {"claim" if s["claim_count"] == 1 else "claims"}</span>' if s['kind'] != 'break' else ''
        time = e(s['time']) if s['time'] else '<span aria-hidden="true">·</span><span class="vh">Time not recorded</span>'
        rows += (f'<li class="ag-row k-{s["kind"]}" id="{s["id"]}"><div class="ag-time">{time}</div><div class="ag-main"><h3 class="ag-title">{title}</h3>{who}{note}</div>'
                 f'<div class="ag-meta"><span class="kind kind-{s["kind"]}">{KINDS[s["kind"]]}</span><ul class="covs" aria-label="Coverage">{cov}</ul>{cnt}</div></li>')
    if not d['sessions']:
        note = empty_note('wave', f'<p class="callout-k">Not yet available</p><p>Day {d["day"]} has not been added yet. This edition covers data '
                          f'through {fdate(K["through"]) if K["through"] else "no day yet"}.</p>', cls='callout empty-note')
        main = f'<div class="wrap narrow">{note}{day_nav(d, K)}</div>'
        return page(path, f'Day {d["day"]}: {d["theme"]}', main, K, crumbs=(), head=(f'Day {d["day"]} · {fdate(d["date"], True)}', d['theme'], '', ''))
    ev = [c for c in cs if c['label'] in ('slide', 'stage') and not c['session_id'].endswith('-S00')]  # what was raised, as in topics.json
    tc, ts = Counter(t for c in ev for t in c['topics']), {}
    for c in ev:
        for t in c['topics']: ts.setdefault(t, set()).add(c['session_id'])
    tops = ''.join(f'<li><a href="{u("topics/" + t + ".html")}">{e(K["topics"][t]["title"])}</a> <span class="n">{plural(len(ts[t]), "session")} · {plural(n, "claim")}</span></li>'
                   for t, n in sorted(tc.items(), key=lambda x: (-len(ts[x[0]]), -x[1], K['topics'][x[0]]['title']))[:16])
    stage = [c for c in cs if c['label'] in ('slide', 'stage')]
    vc = Counter(c['verification'] for c in stage)
    n_real = sum(1 for s in d['sessions'] if s['kind'] not in ('break', 'unrecorded'))
    st = stats([('Sessions', n_real), ('Claims', len(cs)), ('Confirmed or consistent', vc['confirmed'] + vc['consistent']), ('Not in docs', vc['undocumented'])])
    nav = day_nav(d, K)
    main = (f'<div class="wrap">{st}<div class="layout"><div class="main-col">'
            f'<section aria-labelledby="agenda">{sec("Agenda", "agenda")}<ol class="agenda">{rows}</ol></section>{nav}</div>'
            f'<aside class="side" aria-label="About this day"><div class="side-box"><p class="side-k">Claims by label</p><p class="mixes">{label_mix(cs) or "None yet"}</p></div>'
            f'<div class="side-box"><p class="side-k">Topics raised most</p><ul class="toplist n">{tops}</ul></div>'
            f'<div class="side-box"><p class="side-k">Fragile claims</p><p><a href="{u("verification.html#day-" + str(d["day"]))}">{plural(vc["undocumented"], "claim")} from Day {d["day"]} not in Google’s docs</a></p></div></aside></div></div>')
    lead = f'{plural(n_real, "session")} and {plural(len(cs), "claim")} from {fdate(d["date"], True)}.'
    return page(path, f'Day {d["day"]}: {d["theme"]}', main, K, desc=lead, head=(f'Day {d["day"]} · {fdate(d["date"], True)}', d['theme'], e(lead), ''))


def day_nav(d, K):
    i, ds = K['days'].index(d), K['days']
    pn = lambda x, k, cls: f'<a class="pn {cls}" href="{u(day_url(x["day"]))}"><span>{k}</span>Day {x["day"]}: {e(x["theme"])}</a>'
    return (f'<nav class="prevnext" aria-label="Other days">{pn(ds[i - 1], "Previous day", "prev") if i else "<span></span>"}'
            f'{pn(ds[i + 1], "Next day", "next") if i + 1 < len(ds) else "<span></span>"}</nav>')


def session_claims(cs, K):
    """Claims of one session grouped by label; an audience question is followed by its answers. As in build_kb, an answer
    is shown once, under the earliest question of this session that comes before it and that it answers."""
    pos = {c['id']: i for i, c in enumerate(cs)}
    parent = {}
    for c in cs:
        qs = [r['to'] for r in c['relations'] if r['type'] == 'answers' and pos.get(r['to'], len(cs)) < pos[c['id']]]
        if qs: parent[c['id']] = min(qs, key=pos.get)
    kids = {c['id']: [a for a in cs if parent.get(a['id']) == c['id']] for c in cs}

    def block(c, up=()):  # (html, number of cards)
        ans = kids[c['id']]
        skip = set(up) | {a['id'] for a in ans}
        if not ans: return claim_card(c, K, show_session=False, skip_rel=skip), 1
        inner = [block(a, (c['id'],)) for a in ans]
        return (f'<div class="qa"><p class="qa-k"><span>Q</span>Question and answer{"s" if len(ans) > 1 else ""}</p>'
                + claim_card(c, K, show_session=False, skip_rel=skip) + '<div class="qa-a">' + ''.join(h for h, _ in inner) + '</div></div>',
                1 + sum(n for _, n in inner))
    out = ''
    for lab in LABELS:
        parts = [block(c) for c in cs if c['label'] == lab and c['id'] not in parent]
        if parts: out += f'<section class="group" aria-labelledby="g-{lab}">{sec(GROUPS[lab], "g-" + lab, sum(n for _, n in parts))}{"".join(h for h, _ in parts)}</section>'
    return out


def session_page(s, K):
    path = f'sessions/{s["id"]}.html'
    at(path)
    cs = [c for c in K['claims'] if c['session_id'] == s['id']]
    d = next(x for x in K['days'] if x['day'] == s['day'])
    order = [x for x in d['sessions'] if has_page(x)]
    i = order.index(s)
    pn = lambda x, k, cls: f'<a class="pn {cls}" href="{u(session_url(x))}"><span>{k}</span>{e(x["time"] + " · " if x["time"] else "")}{e(x["title"])}</a>'
    nav = (f'<nav class="prevnext" aria-label="Other sessions">{pn(order[i - 1], "Previous session", "prev") if i else "<span></span>"}'
           f'{pn(order[i + 1], "Next session", "next") if i + 1 < len(order) else "<span></span>"}</nav>')
    who = ', '.join(s['speakers'])
    meta = ''
    if who: meta += f'<p class="speakers"><span class="k">{"Speakers" if len(s["speakers"]) > 1 else "Speaker"}</span> {e(who)}{", " + e(s["role"]) if s["role"] else ""}</p>'
    meta += f'<p class="covline"><span class="kind kind-{s["kind"]}">{KINDS[s["kind"]]}</span><span class="k">Coverage</span><span class="covs">' + ''.join(f'<span class="cov cov-{c}">{COVERAGE[c]}</span>' for c in s['coverage']) + '</span></p>'
    rels = all_rels(K, {c['id'] for c in cs})
    rels = [x for x in rels if K['byid'][x[0]]['session_id'] != K['byid'][x[2]]['session_id']]
    rel = f'<section aria-labelledby="links">{sec("Links to other sessions", "links", len(rels))}{pairs(rels, K)}</section>' if rels else ''
    tc = list(dict.fromkeys(s['topics']))
    side = (f'<aside class="side" aria-label="About this session"><div class="side-box"><p class="side-k">Claims by label</p><p class="mixes">{label_mix(cs) or "None"}</p></div>'
            + (f'<div class="side-box"><p class="side-k">Topics</p><ul class="chips">' + ''.join(f'<li><a href="{u("topics/" + t + ".html")}">{e(K["topics"][t]["title"])}</a></li>' for t in tc) + '</ul></div>' if tc else '')
            + (f'<div class="side-box">{things_strip(K["sfeat"][s["id"]], K, "Things named", "things-side", 10)}</div>' if K['sfeat'][s['id']] else '')
            + f'<div class="side-box back"><p class="side-k">Day {s["day"]}</p><p><a href="{u(day_url(s["day"], s["id"]))}">Back to the Day {s["day"]} agenda</a></p></div></aside>')
    body = session_claims(cs, K) if cs else empty_note('read', '<p class="empty">No claims were captured from this session.</p>')
    note = f'<p class="note">{e(s["note"])}</p>' if s['note'] else ''
    main = f'<div class="wrap"><div class="layout"><div class="main-col">{note}{body}{rel}{nav}</div>{side}</div></div>'
    eyebrow = f'Day {s["day"]} · {fdate(s["date"], True)}{" · " + e(s["time"]) if s["time"] else ""}'
    return page(path, s['title'], main, K, desc=f'Day {s["day"]} session: {s["title"]}, {plural(len(cs), "claim")}.',
                crumbs=((day_url(s['day']), f'Day {s["day"]}'),), head=(eyebrow, s['title'], '', meta), section=day_url(s['day']))


def topic_page(t, K):
    path = f'topics/{t["id"]}.html'
    at(path)
    cs = [K['byid'][i] for i in t['claim_ids']]
    cs.sort(key=lambda c: K['order'][c['id']])
    on = {c['id'] for c in cs}
    cites = ''
    if t['cites']:
        cites = '<p class="based">Based on ' + ', '.join(cid_link(x, anchor=x in on) for x in t['cites']) + '</p>'
    ev = len(t['event_sessions'])
    facts = [plural(len(cs), 'claim')] + ([f'raised in {plural(ev, "session")}'] if ev else [])
    if t['event_days']: facts.append('said or shown on ' + ' and '.join(f'Day {x}' for x in t['event_days']))
    meta = f'<p class="facts">{" · ".join(facts)}</p>' + map_link(f'topic:{t["id"]}', 'Open in Reef map', 'Open in Graph')
    body = things_strip(K['feat'][t['id']], K, 'Things in this topic')
    if t['do']:
        body += f'<div class="callout"><p class="callout-k">What to do</p><ul>' + ''.join(f'<li>{e(x)}</li>' for x in t['do']) + '</ul></div>'
    toc = []
    for d in K['days']:
        dc = [c for c in cs if c['day'] == d['day']]
        if not dc: continue
        toc.append((f'day-{d["day"]}', f'Day {d["day"]}: {d["theme"]}', len(dc)))
        body += f'<section aria-labelledby="day-{d["day"]}">{day_sec(d, len(dc))}'
        for lab in LABELS:
            g = [c for c in dc if c['label'] == lab]
            if g: body += f'<h3 class="lab-h">{GROUPS[lab]} <span class="count">{len(g)}</span></h3>' + ''.join(claim_card(c, K) for c in g)
        body += '</section>'
    if not cs: body += empty_note('peek', '<p class="empty">No claims carry this topic yet.</p>')
    rels = all_rels(K, on)
    if rels:
        toc.append(('across', 'Across days and sessions', len(rels)))
        body += f'<section aria-labelledby="across">{sec("Across days and sessions", "across", len(rels))}{pairs(rels, K)}</section>'
    built, side_terms = built_on(t, on, K)
    if built:
        n = sum(1 for x in K['links']['topic_items'][t['id']] if not x.startswith('term:'))
        toc.append(('built', 'Built on these claims', n))
        body += f'<section aria-labelledby="built">{sec("Built on these claims", "built", n)}{built}</section>'
    srcs = list({x['key']: x for c in cs for x in c['sources']}.values())
    if srcs:
        toc.append(('sources', 'Sources', len(srcs)))
        body += f'<section aria-labelledby="sources">{sec("Sources", "sources", len(srcs))}<ul class="srcs big">' + ''.join(source_li(x) for x in srcs) + '</ul></section>'
    rel_t = [K['topics'][x] for x in t['related']]
    side = '<aside class="side" aria-label="About this topic">'
    if toc: side += '<div class="side-box"><p class="side-k">On this page</p><ul class="toc">' + ''.join(f'<li><a href="#{i}">{e(n)}</a> <span class="n">{c}</span></li>' for i, n, c in toc) + '</ul></div>'
    if t['event_sessions']:
        side += '<div class="side-box"><p class="side-k">Raised in</p><ul class="toc">' + ''.join(
            f'<li><a href="{u(session_url(K["sess"][x]))}">Day {K["sess"][x]["day"]} · {e(K["sess"][x]["title"])}</a></li>' for x in t['event_sessions']) + '</ul></div>'
    if side_terms: side += f'<div class="side-box"><p class="side-k">Glossary</p><ul class="chips">{side_terms}</ul></div>'
    if rel_t: side += '<div class="side-box"><p class="side-k">Related topics</p><ul class="chips">' + ''.join(f'<li><a href="{u("topics/" + x["id"] + ".html")}">{e(x["title"])}</a></li>' for x in rel_t) + '</ul></div>'
    side += f'<div class="side-box"><p class="side-k">Area</p><p><a href="{u("areas/" + t["area"]["id"] + ".html")}">{e(t["area"]["title"])}</a></p></div></aside>'
    main = f'<div class="wrap"><div class="layout"><div class="main-col">{body}</div>{side}</div></div>'
    return page(path, t['title'], main, K, desc=t['summary'], crumbs=(('topics.html', 'Topics'), (f'areas/{t["area"]["id"]}.html', t['area']['title'])),
                head=(f'Topic · {e(t["area"]["title"])}', t['title'], summary_html(t['summary']), cites + meta), section='topics.html')


def built_on(t, on, K):
    """The kit items that rest on a topic's claims (links.json topic_items): requirements, facts and myths as rows, most of their
    claims in this topic first; quotes and story angles as one line of links; glossary terms as chips for the side column."""
    ns = K['links']['topic_items'][t['id']]
    here = {n: sum(1 for c in dict.fromkeys(K['kit'][n][2]) if c in on) for n in ns}
    rows = ''
    for kind, title in (('req', 'Developer requirements'), ('fact', 'Facts'), ('myth', 'Myths')):
        g = sorted((n for n in ns if n.startswith(kind + ':')), key=lambda n: -here[n])  # stable: ties keep the kind order of links.json
        if not g: continue
        li = ''
        for n in g:
            _, x, cids, url = K['kit'][n]
            badges = (lv_badge(x['level']) if kind == 'req' else '') + st_badge(x['status'])
            text = inline(x['title']) if kind == 'req' else e(x['statement'] if kind == 'fact' else x['myth'])
            li += (f'<li><div class="bt-head">{badges}<span class="sp"></span><a class="cid" href="{u(url)}">{e(x["id"])}</a></div>'
                   f'<p class="bt-t"><a href="{u(url)}">{"Myth: " if kind == "myth" else ""}{text}</a></p>'
                   f'<p class="bt-n">Rests on {plural(len(dict.fromkeys(cids)), "claim")}, {here[n]} of them in this topic</p></li>')
        rows += f'<h3 class="lab-h">{title} <span class="count">{len(g)}</span></h3><ul class="built">{li}</ul>'
    more = [n for n in ns if n.startswith(('quote:', 'angle:'))]
    if more: rows += f'<p class="src-by used-by"><span class="k">Also in</span>{kit_links(more, K)}</p>'
    terms = ''.join(f'<li><a href="{u(K["kit"][n][3])}" title="{e(snippet(kit_title(n, K), 160))}">{e(kit_name(n, K))}</a></li>' for n in ns if n.startswith('term:'))
    return rows, terms


def ent_url(k): return f'entities/{k}.html'
def map_link(node, deep, deco):
    """A button to the explorer, centred on a node of graph.json (graph.html#ent:googlebot): the back button returns here."""
    return f'<p class="map-go"><a class="map-btn" href="{u("graph.html")}#{e(node)}"><span class="map-i" aria-hidden="true"></span>{map_name(deep, deco)}</a></p>'
def ent_kind(kind): return f'<span class="ekind ek-{kind}">{ENT_KINDS[kind][0]}</span>'


def ent_link(k, K, n=None):
    """A thing as a chip: its name (its kind as a coloured mark and a tooltip) and, when given, a count."""
    x = K['ents'][k]
    cnt = f' <span class="n">{n}</span>' if n is not None else ''
    return f'<a class="ent ek-{x["kind"]}" href="{u(ent_url(k))}" title="{ENT_KINDS[x["kind"]][0]}">{e(x["name"])}{cnt}</a>'


def ent_chips(c, K):
    """Under a claim: the things it mentions (claims.jsonl `mentions`)."""
    es = K['ment'].get(c['id'])
    if not es: return ''
    return '<div class="ents"><span class="k">Things</span><ul class="ent-chips" aria-label="Things mentioned">' + ''.join(f'<li>{ent_link(k, K)}</li>' for k in es) + '</ul></div>'


def ranked(counter, K):
    """Entities by count, then by name."""
    return sorted(counter.items(), key=lambda x: (-x[1], fold(K['ents'][x[0]]['name']), x[0]))


def things_strip(counter, K, title, cls='things-strip', top=12):
    """The things mentioned most by a set of claims, with counts: the first `top` as chips, the rest behind a toggle."""
    r = ranked(counter, K)
    if not r: return ''
    chips = lambda xs: '<ul class="ent-chips big">' + ''.join(f'<li>{ent_link(k, K, n)}</li>' for k, n in xs) + '</ul>'
    more = f'<details class="kd more-ents"><summary>{plural(len(r) - top, "more thing")}</summary>{chips(r[top:])}</details>' if len(r) > top else ''
    return (f'<div class="{cls}"><p class="side-k">{e(title)} <span class="count">{len(r)}</span></p>{chips(r[:top])}{more}'
            f'<p class="ts-n">Counts are claims that name the thing. <a href="{u("entities.html")}">All things</a></p></div>')


def claim_row(c, K, here):
    """A claim on a thing's card, short: label, grade, ID (to its full card on All claims), text, where it was said, the other things
    it names. The card stays short; the full claim card (sources, quote, what rests on it) is one click away."""
    s = K['sess'][c['session_id']]
    others = [k for k in K['ment'].get(c['id'], ()) if k != here]
    ents = ('<ul class="ent-chips" aria-label="Also names">' + ''.join(f'<li>{ent_link(k, K)}</li>' for k in others) + '</ul>') if others else ''
    sp = K['links']['speakers']['claims'].get(c['id'])  # a person is named only where kits.proven() proves it
    who = f'{e(sp["name"])} · ' if sp and sp['name'] else 'From the audience · ' if c['who'] == 'audience' else '' if sp else f'{e(c["author"])} · '
    return (f'<article class="claim crow c-{c["label"]}" data-label="{c["label"]}" data-grade="{c["verification"].replace("/", "")}" data-day="{c["day"]}">'
            f'<div class="claim-head">{badge_label(c["label"])}{badge_ver(c["verification"])}<span class="sp"></span>{cid_link(c["id"])}</div>'
            f'<p class="claim-text">{e(c["text"])}</p><p class="crow-by">{who}<a href="{u(session_url(s))}">Day {s["day"]} · {e(stitle(s))}</a></p>{ents}</article>')


def tally(cs):
    """Said at the event (slide and stage claims) against Google's documentation: a bar and its legend."""
    st = [c for c in cs if c['label'] in ('slide', 'stage')]
    n = Counter(c['verification'] for c in st)
    if not st: return ''
    names = {'undocumented': 'Not in docs', 'consistent': 'Consistent with docs', 'confirmed': 'Confirmed by docs', 'n/a': 'Nothing to verify'}
    seg = ''.join(f'<span class="t-seg t-{g.replace("/", "")}" style="flex-grow:{n[g]}"></span>' for g in GRADE_SAID if n[g])
    leg = ''.join(f'<li><span class="t-dot t-{g.replace("/", "")}" aria-hidden="true"></span>{names[g]} <b>{n[g]}</b></li>' for g in GRADE_SAID if n[g])
    label = ', '.join(f'{names[g]} {n[g]}' for g in GRADE_SAID if n[g])
    return (f'<div class="tally"><p class="side-k">Said at the event, against the docs <span class="count">{len(st)}</span></p>'
            f'<div class="t-bar" role="img" aria-label="{e(label)}">{seg}</div><ul class="t-leg">{leg}</ul></div>')


def ent_rows(ns, counts, K, total, top=5):
    """Kit items resting on an entity's claims: requirements, facts and myths as rows (most of its claims first; after `top` of a kind,
    behind a toggle), the rest as links."""
    out = ''
    for kind, title in (('req', 'Developer requirements'), ('fact', 'Facts'), ('myth', 'Myths')):
        g = [n for n in ns if n.startswith(kind + ':')]
        if not g: continue
        li = []
        for n in g:
            _, x, cids, url = K['kit'][n]
            badges = (lv_badge(x['level']) if kind == 'req' else '') + st_badge(x['status'])
            text = inline(x['title']) if kind == 'req' else e(x['statement'] if kind == 'fact' else x['myth'])
            li.append(f'<li><div class="bt-head">{badges}<span class="sp"></span><a class="cid" href="{u(url)}">{e(x["id"])}</a></div>'
                      f'<p class="bt-t"><a href="{u(url)}">{"Myth: " if kind == "myth" else ""}{text}</a></p>'
                      f'<p class="bt-n">Rests on {plural(len(dict.fromkeys(cids)), "claim")}, {counts[n]["count"]} of them naming {e(total)}'
                   + (f'; its own words name {e(total)}' if counts[n]['own'] else '') + '</p></li>')
        out += f'<h3 class="lab-h">{title} <span class="count">{len(g)}</span></h3><ul class="built">{"".join(li[:top])}</ul>'
        if len(li) > top: out += f'<details class="kd more-ents"><summary>{len(li) - top} more</summary><ul class="built">{"".join(li[top:])}</ul></details>'
    more = [n for n in ns if n.startswith(('quote:', 'angle:', 'term:'))]
    if more: out += f'<p class="src-by used-by"><span class="k">Also in</span>{kit_links(more, K)}</p>'
    return out


def ent_rel_list(k, K):
    """Typed relations of entities.yaml, both ways, each with the claims behind it (structural ones need none)."""
    li = ''
    for t, back, o, cids in sorted(K['erel'][k], key=lambda r: (list(ENT_REL).index(r[0]), r[1], fold(K['ents'][r[2]]['name']))):
        verb = ENT_REL[t][back]
        ev = ''
        if cids:
            cs = [K['byid'][i] for i in cids]
            ev = (f'<details class="kd rel-ev"><summary>{plural(len(cs), "claim")}, {sum(documented(c) for c in cs)} documented</summary><ul class="ev-list">'
                  + ''.join(f'<li><div class="ev-head">{badge_label(c["label"])}{badge_ver(c["verification"])}<span class="sp"></span>{cid_link(c["id"])}</div>'
                            f'<p>{e(c["text"])}</p></li>' for c in cs) + '</ul></details>')
        else: ev = '<span class="rel-s">structure, no claim needed</span>'
        li += f'<li><span class="rel-v">{verb}</span> {ent_link(o, K)} {ev}</li>'
    return f'<ul class="ent-rels">{li}</ul>' if li else ''


def entity_page(k, K):
    x = K['ents'][k]
    path = ent_url(k)
    at(path)
    cs = [K['byid'][i] for i in x['claims']]
    docs = [c for c in cs if c['label'] == 'docs']
    said = [c for c in cs if c['label'] in ('slide', 'stage')]
    other = [c for c in cs if c['label'] in ('press', 'analysis')]
    meta = f'<p class="ent-meta">{ent_kind(x["kind"])}'
    if x['aliases']: meta += '<span class="k">Also called</span><span class="aka">' + ', '.join(f'<span>{e(a)}</span>' for a in x['aliases']) + '</span>'
    meta += '</p>' + map_link(f'ent:{k}', 'Open in Reef map', 'Open in Graph')
    if x['topics']:
        meta += ('<p class="ent-home"><span class="k">Narrative</span> see the topic' + ('s ' if len(x['topics']) > 1 else ' ')
                 + ', '.join(f'<a href="{u("topics/" + t + ".html")}">{e(K["topics"][t]["title"])}</a>' for t in x['topics']) + '</p>')
    st = stats([('Claims', len(cs)), ('In Google’s docs', len(docs)), ('Said at the event', len(said)),
                ('Not in docs', sum(c['verification'] == 'undocumented' for c in said)), ('Kit items', len(x['items']))])
    body, toc = '', []
    if x['glossary']:
        _, g, _, gurl = K['kit'][f'term:{x["glossary"]}']
        body += f'<div class="callout slim gloss-c"><p class="callout-k">Glossary · <a href="{u(gurl)}">{e(g["term"])}</a></p><p>{e(g["definition"])}</p></div>'
    srcs = [dict(K['sources'][s], key=s) for s in x['docs']]
    if srcs or docs:
        toc.append(('docs', 'Google’s documentation', len(docs)))
        body += f'<section aria-labelledby="docs">{sec("Google’s documentation", "docs", len(docs))}'
        if srcs: body += f'<p class="src-by"><span class="k">Documented in</span></p><ul class="srcs big">{"".join(source_li(s) for s in srcs)}</ul>'
        body += ''.join(claim_row(c, K, k) for c in docs) + '</section>'
    if said:
        toc.append(('said', 'Said at the event', len(said)))
        body += (f'<section aria-labelledby="said" class="ent-said">{sec("Said at the event", "said", len(said))}'
                 '<p class="blurb">Slide and stage claims that name it, the ones Google’s documentation does not cover first.</p>')
        if len(said) > 6:
            days = sorted({c['day'] for c in said})
            groups = [('label', 'Label', [(l, badge_label(l)) for l in ('slide', 'stage') if any(c['label'] == l for c in said)])]
            groups.append(('grade', 'Grade', [(g.replace('/', ''), badge_ver(g) or '<span class="badge-none">Nothing to verify</span>') for g in GRADE_SAID if any(c['verification'] == g for c in said)]))
            if len(days) > 1: groups.append(('day', 'Day', [(str(d), f'<span class="uchip">Day {d}</span>') for d in days]))
            body += kit_filter('.ent-said .claim', 'claim', groups)
        for g in GRADE_SAID:
            gs = [c for c in said if c['verification'] == g]
            if gs: body += (f'<div data-group><h3 class="lab-h">{badge_ver(g) or "<span class=badge-none>Nothing to verify</span>"} <span class="count">{len(gs)}</span></h3>'
                            + ''.join(claim_row(c, K, k) for c in gs) + '</div>')
        body += '</section>'
    if other:
        toc.append(('other', 'Press and analysis', len(other)))
        body += f'<section aria-labelledby="other">{sec("Press and analysis", "other", len(other))}' + ''.join(claim_row(c, K, k) for c in other) + '</section>'
    if not cs: body += empty_note('peek', '<p class="empty">No public claim names this thing yet.</p>')
    its = {y['id']: y for y in x['items']}
    ns = sorted(its, key=lambda n: (-its[n]['count'], node_key(n)))
    if ns:
        toc.append(('built', 'Built on these claims', len(ns)))
        body += (f'<section aria-labelledby="built">{sec("Built on these claims", "built", len(ns))}<p class="blurb">Kit items about {e(x["name"])}: their own words name it, '
                 f'or several of the claims they rest on do.</p>{ent_rows(ns, its, K, x["name"])}</section>')
    rels, co = ent_rel_list(k, K), sorted(((o, len(v)) for o, v in K['co'][k].items()), key=lambda y: (-y[1], fold(K['ents'][y[0]]['name']), y[0]))
    feat = sorted(((t, K['feat'][t][k]) for t in K['topics'] if K['feat'][t][k]), key=lambda y: (-y[1], K['topics'][y[0]]['title']))
    if rels or co or feat:
        n = len(K['erel'][k]) + len(co)
        toc.append(('connected', 'Connected things', n))
        body += f'<section aria-labelledby="connected">{sec("Connected things", "connected", n)}'
        if rels: body += f'<h3 class="lab-h">Relations</h3>{rels}'
        if co: body += ('<h3 class="lab-h">Most often named with it</h3><p class="blurb">Things named in the same claim, with the number of claims they share.</p>'
                        '<ul class="ent-chips big">' + ''.join(f'<li>{ent_link(o, K, n)}</li>' for o, n in co[:16]) + '</ul>')
        if len(co) > 16: body += f'<details class="kd more-ents"><summary>{plural(len(co) - 16, "more thing")}</summary><ul class="ent-chips big">' + ''.join(f'<li>{ent_link(o, K, n)}</li>' for o, n in co[16:]) + '</ul></details>'
        if feat: body += ('<h3 class="lab-h">Topics that feature it</h3><ul class="chips">' + ''.join(
            f'<li><a href="{u("topics/" + t + ".html")}">{e(K["topics"][t]["title"])} <span class="n">{n}</span></a></li>' for t, n in feat) + '</ul>')
        body += '</section>'
    side = '<aside class="side" aria-label="About this thing">'
    side += '<div class="side-box">' + tally(cs) + '</div>' if tally(cs) else ''
    if toc: side += '<div class="side-box"><p class="side-k">On this page</p><ul class="toc">' + ''.join(f'<li><a href="#{i}">{e(t)}</a> <span class="n">{c}</span></li>' for i, t, c in toc) + '</ul></div>'
    drows, asked = K['ledger_links']
    if k in asked or drows.get(k):
        side += ('<div class="side-box"><p class="side-k">Ledgers</p><ul class="toc">'
                 + (f'<li><a href="{u("content/questions.html#t-" + k)}">What did Google say about it?</a></li>' if k in asked else '')
                 + ''.join(f'<li><a href="{u("dev/differences.html#" + r)}">{e(r)}</a> where the event and the docs differ</li>' for r in drows.get(k, ())) + '</ul></div>')
    side += f'<div class="side-box"><p class="side-k">{ENT_KINDS[x["kind"]][1]}</p><p><a href="{u("entities.html#k-" + x["kind"])}">All {ENT_KINDS[x["kind"]][1].lower()} in the base</a></p></div></aside>'
    main = f'<div class="wrap">{st}<div class="layout"><div class="main-col">{body}</div>{side}</div></div>'
    return page(path, x['name'], main, K, desc=x['summary'], crumbs=(('entities.html', 'Things'),),
                head=(f'Thing · {ENT_KINDS[x["kind"]][0]}', x['name'], e(x['summary']), meta), section='entities.html')


def entities_index(K):
    at('entities.html')
    by = {kind: [k for k in K['ent_order'] if K['ents'][k]['kind'] == kind] for kind in ENT_KINDS}
    jump = '<nav class="jump" aria-label="Kinds"><ul>' + ''.join(f'<li><a href="#k-{kind}">{ENT_KINDS[kind][1]}</a> <span class="n">{len(v)}</span></li>' for kind, v in by.items() if v) + '</ul></nav>'
    body = ''
    for kind, ks in by.items():
        if not ks: continue
        rows = ''
        for k in ks:
            x = K['ents'][k]
            cs = [K['byid'][i] for i in x['claims']]
            und = sum(c['label'] in ('slide', 'stage') and c['verification'] == 'undocumented' for c in cs)
            aka = f'<span class="ei-aka">{e(", ".join(x["aliases"]))}</span>' if x['aliases'] else ''
            facts = [plural(len(cs), 'claim'), f'{sum(c["label"] == "docs" for c in cs)} in the docs'] + ([f'{und} not in docs'] if und else [])
            rows += (f'<li class="ei ek-{x["kind"]}" id="{e(k)}"><p class="ei-t"><a href="{u(ent_url(k))}">{e(x["name"])}</a>{aka}</p>'
                     f'<p class="ei-s">{e(x["summary"])}</p><p class="ei-n">{" · ".join(facts)}</p></li>')
        body += f'<section aria-labelledby="k-{kind}">{sec(ENT_KINDS[kind][1], "k-" + kind, len(ks))}<ul class="ent-index">{rows}</ul></section>'
    if not K['ents']: body = empty_note('peek', '<p class="empty">No things have been listed yet.</p>')
    n = sum(1 for v in K['ment'].values() if v)
    how = ('<div class="callout slim"><p class="callout-k">How things are found</p><p>Each thing is a name the event used, with its other names. A claim names it '
           'when one of those names is written in the claim, word for word; a few are scoped to the topics where a common word means this thing. '
           'A card is a map, not a source: cite the claim IDs on it.</p></div>')
    if K['ents']: how += f'<p class="callout slim"><a href="{u("graph.html")}">Open the {map_name("Reef map", "Graph")}</a>: the things as a map of links, one neighbourhood at a time.</p>'
    main = f'<div class="wrap narrow">{how}{jump}{body}</div>'
    return page('entities.html', 'Things', main, K, desc='Every product, feature, crawler, report, directive, status code, standard, metric, concept, update and tool the event talked about.',
                head=('Index', 'Things', f'{plural(len(K["ents"]), "thing")} the event talked about, by kind: products, crawlers, reports, directives, status codes and more. '
                      f'{plural(n, "claim")} name at least one. Each card gathers the claims, the documentation, the kit items and the things named with it.', ''))


def topic_tiles(ts, K):
    out = ''
    for t in ts:
        days = ''.join(f'<span class="dchip">Day {x}</span>' for x in t['days'])
        out += (f'<li class="step tile topic-tile"><div class="in"><p class="tile-k">{plural(len(t["claim_ids"]), "claim")} · {plural(len(t["event_sessions"]), "session")}</p>'
                f'<h3><a class="stretch" href="{u("topics/" + t["id"] + ".html")}">{e(t["title"])}</a></h3><p>{summary_html(t["summary"])}</p><p class="dchips">{days}</p></div></li>')
    return f'<ul class="tiles">{out}</ul>'


def area_page(a, K):
    path = f'areas/{a["id"]}.html'
    at(path)
    ids = {i for t in a['topics'] for i in t['claim_ids']}
    rels = [x for x in all_rels(K, ids) if K['byid'][x[0]]['day'] != K['byid'][x[2]]['day']]
    main = f'<div class="wrap">{sec("Topics in this area", "topics", len(a["topics"]))}{topic_tiles(a["topics"], K)}'
    if rels: main += f'<section aria-labelledby="across">{sec("Across days", "across", len(rels))}{pairs(rels, K)}</section>'
    main += '</div>'
    meta = f'<p class="facts">{plural(len(a["topics"]), "topic")} · {plural(len(ids), "claim")}</p>'
    return page(path, a['title'], main, K, desc=a['blurb'], crumbs=(('topics.html', 'Topics'),), head=('Area', a['title'], e(a['blurb']), meta), section='topics.html')


def topics_index(K, mindmap):
    at('topics.html')
    main = '<div class="wrap">'
    if mindmap: main += f'<p class="callout slim"><a href="{u("mindmap.html")}">Open the interactive topic map</a>: every area and topic as a tree you can expand and search.</p>'
    main += f'<p class="callout slim"><a href="{u("graph.html")}">Open the {map_name("Reef map", "Graph")}</a>: start from any thing or topic, see its neighbourhood and follow the links.</p>'
    if K['ents']: main += f'<p class="callout slim"><a href="{u("entities.html")}">Browse the {plural(len(K["ents"]), "thing")}</a>: products, crawlers, reports, directives, status codes and more, each with every claim that names it.</p>'
    for a in K['areas']:
        rows = ''.join(f'<li><a href="{u("topics/" + t["id"] + ".html")}">{e(t["title"])}</a><span class="tl-m">{plural(len(t["claim_ids"]), "claim")}'
                       + ''.join(f'<span class="dchip">Day {x}</span>' for x in t['days']) + '</span></li>' for t in a['topics'])
        main += (f'<section class="area-block" aria-labelledby="a-{a["id"]}"><h2 class="sec-h" id="a-{a["id"]}"><a href="{u("areas/" + a["id"] + ".html")}">{e(a["title"])}</a></h2>'
                 f'<p class="blurb">{e(a["blurb"])}</p><ul class="topic-list">{rows}</ul></section>')
    main += '</div>'
    return page('topics.html', 'Topics', main, K, desc='Every area and topic of the knowledge base.',
                head=('Index', 'Topics', f'{plural(len(K["topics"]), "topic")} in {plural(len(K["areas"]), "area")}. Each topic page gathers every claim on it, from every day.', ''))


def verification_page(K):
    at('verification.html')
    secs, cols = '', []
    for d in K['days']:
        st = [c for c in K['claims'] if c['day'] == d['day'] and c['label'] in ('slide', 'stage')]
        if not st: continue
        cols.append((d, Counter(c['verification'] for c in st), len(st)))
        und = [c for c in st if c['verification'] == 'undocumented']
        body = ''
        for sid in dict.fromkeys(c['session_id'] for c in und):
            s = K['sess'][sid]
            g = [c for c in und if c['session_id'] == sid]
            body += f'<h3 class="lab-h"><a href="{u(session_url(s))}">{e(s["title"])}</a> <span class="count">{len(g)}</span></h3>' + ''.join(claim_card(c, K, show_session=False, anchor=False) for c in g)
        secs += f'<section aria-labelledby="day-{d["day"]}">{day_sec(d, len(und))}{body or empty_note("wave", "<p class=empty>Nothing undocumented on this day.</p>")}</section>'
    head = ''.join(f'<th scope="col"><a href="#day-{d["day"]}">Day {d["day"]}</a></th>' for d, _, _ in cols)
    rows = ''.join(f'<tr><th scope="row">{badge_ver(k) or "<span class=badge-none>Nothing to verify</span>"}</th>' + ''.join(f'<td>{v[k]}</td>' for _, v, _ in cols) + '</tr>'
                   for k in ('confirmed', 'consistent', 'undocumented', 'n/a'))
    table = ('<div class="table-wrap"><table><caption>Slide and stage claims by verification grade</caption>'
             f'<thead><tr><th scope="col">Grade</th>{head}</tr></thead><tbody>{rows}</tbody>'
             '<tfoot><tr><th scope="row">Total</th>' + ''.join(f'<td>{n}</td>' for _, _, n in cols) + '</tr></tfoot></table></div>')
    grades = ''.join(f'<li>{badge_ver(k)} {e(VER[k][1])}</li>' for k in ('confirmed', 'consistent', 'undocumented'))
    main = (f'<div class="wrap"><div class="two"><div>{table}</div><div class="callout"><p class="callout-k">How to quote these</p>'
            '<p>A claim marked <strong>Not in docs</strong> was said or shown at the event, by Google or a community speaker, but is not in Google’s published documentation. '
            'Quote it as “said at Search Central Live Deep Dive 2026”, never as documented policy.</p>'
            f'<p>Where the event and the documentation say different things, the <a href="{u("dev/differences.html")}">differences ledger</a> puts both side by side '
            'and says what to follow.</p></div></div>'
            f'<ul class="legend">{grades}</ul>{secs}</div>')
    return page('verification.html', 'Said at the event, not in the docs', main, K, desc='Event claims that Google’s documentation does not state, per day.',
                head=('Verification', 'Said at the event, not in the docs', 'Every slide and stage claim was checked against Google’s documentation. These are the ones the documentation does not cover: the most valuable claims, and the most fragile.', ''))


def across_page(K):
    at('across-days.html')
    rels = all_rels(K, answers=True)
    cnt = Counter(t for _, t, _ in rels)
    main = '<div class="wrap">'
    if not rels: main += empty_note('peek', '<p class="empty">No links between claims yet.</p>')
    main += '<p class="rel-sum">' + ' '.join(f'<a class="mix" href="#{t}"><span class="rel rel-{t}">{REL[t][0]}</span> {cnt[t]}</a>' for t in REL if cnt[t]) + '</p>'
    for t in REL:
        g = [x for x in rels if x[1] == t]
        if g: main += f'<section aria-labelledby="{t}">{sec(REL[t][0], t, len(g))}<p class="blurb">{e(REL[t][2])} The later claim is on the left.</p>{pairs(g, K)}</section>'
    main += '</div>'
    return page('across-days.html', 'Across days', main, K, desc='How claims repeat, extend, contradict, update and answer each other.',
                head=('Connections', 'Across days', 'When a later talk repeats, extends, contradicts or updates an earlier one, the two claims are linked. Questions from the audience are linked to their answers.', ''))


def sources_page(K):
    at('sources.html')
    L = K['links']['sources']
    main = '<div class="wrap narrow">'
    for kind, title, blurb in (('google', 'Google documentation', 'Google’s own pages, used to verify what was said at the event.'),
                               ('press', 'Press reports', 'Third-party publications reporting what Google or a Googler said. Not Google’s own documentation.')):
        ks = sorted((k for k, v in K['sources'].items() if v['kind'] == kind), key=lambda k: K['sources'][k]['title'].lower())
        if not ks: continue
        main += f'<section aria-labelledby="{kind}">{sec(title, kind, len(ks))}<p class="blurb">{blurb}</p>'
        for k in ks:
            v, ln = K['sources'][k], L[k]
            n = sum(len(x) for x in ln['claims'].values())
            by = (f'<p class="src-by"><span class="k">Backs</span> {plural(n, "claim")}, by grade</p><ul class="by-grade">' + ''.join(
                f'<li><span class="bg-k">{badge_ver(g) or "<span class=badge-none>Nothing to verify</span>"}<span class="count">{len(ids)}</span></span>'
                f'<span class="bg-ids">{" ".join(cid_link(i) for i in ids)}</span></li>' for g, ids in ln['claims'].items()) + '</ul>') if n else '<p class="src-by">Not cited by a claim yet</p>'
            if ln['requirements']: by += f'<p class="src-by used-by"><span class="k">Documents</span>{kit_links(ln["requirements"], K)}</p>'
            main += (f'<article class="src-card" id="src-{e(k)}"><h3><a class="ext" href="{e(v["url"])}" rel="noopener external">{e(v["title"])}</a></h3>'
                     f'<p class="src-meta">{e(v["publisher"])} · checked {fdate(v["checked"])}</p><p class="src-url">{e(v["url"])}</p>{by}</article>')
        main += '</section>'
    main += '</div>'
    return page('sources.html', 'Sources', main, K, desc='Every document used to verify the claims, with the date it was checked.',
                head=('References', 'Sources', 'Every document used to check the claims, with the date it was last read, the claims it backs by grade and the '
                      'developer requirements it documents. Documentation changes: re-check the live page before relying on it.', ''))


def claims_page(K):
    at('claims.html')
    jump, body = '', ''
    for d in K['days']:
        dc = [c for c in K['claims'] if c['day'] == d['day']]
        if not dc: continue
        jump += f'<li><a href="#day-{d["day"]}">Day {d["day"]}</a> <span class="n">{len(dc)}</span></li>'
        body += f'<section aria-labelledby="day-{d["day"]}">{day_sec(d, len(dc))}'
        for s in d['sessions']:
            g = [c for c in dc if c['session_id'] == s['id']]
            if g: body += (f'<div class="claim-group"><h3 class="lab-h"><a href="{u(session_url(s))}">{e(s["time"] + " · " if s["time"] else "")}{e(s["title"])}</a> <span class="count">{len(g)}</span></h3>'
                           + ''.join(claim_card(c, K, show_session=False) for c in g) + '</div>')
        body += '</section>'
    filt = ('<fieldset id="claim-filter" class="filter" hidden><legend>Show labels</legend>' + ''.join(
        f'<label><input type="checkbox" value="{k}" checked> {badge_label(k)}</label>' for k in LABELS) + '<p class="filter-n" aria-live="polite"></p></fieldset>')
    main = f'<div class="wrap narrow"><nav class="jump" aria-label="Days"><ul>{jump}</ul></nav>{filt}{body}</div>'
    return page('claims.html', 'All claims', main, K, desc='Every public claim with a permanent link.',
                head=('Every claim', 'All claims', f'{plural(len(K["claims"]), "claim")} in event order. Each one has a permanent link: use its ID, such as {K["claims"][0]["id"] if K["claims"] else "D1-C001"}, to cite it.', ''))


def search_page(K):
    at('search.html')
    main = ('<div class="wrap narrow"><form id="search-form" class="search-big" role="search" action="search.html" method="get">'
            f'<label for="q">Search things, claims, topics, sessions, {"the developer kit" if community() else "the kits"} and the glossary</label><div class="sb-row"><input id="q" name="q" type="search" autocomplete="off" spellcheck="false" '
            'placeholder="Try: crawl budget, GSC, canonical"><button type="submit">Search</button></div>'
            '<p class="hint">All words must match; whole words rank first. Small typos and other names (GSC for Search Console) are understood. '
            'Search runs in your browser; nothing leaves this computer.</p></form>'
            '<div id="search-filters" class="filter" hidden></div><p id="search-status" class="status" role="status" aria-live="polite"></p>'
            '<div id="search-note" class="res-note" hidden></div>'
            '<div id="search-guide" class="bot-note" hidden><span class="bot-art" aria-hidden="true"></span><span class="dd-q" aria-hidden="true"></span>'
            '<span class="dd-blow" aria-hidden="true"></span><p class="bot-say"></p></div><div id="results"></div>'
            f'<noscript><p class="callout slim">Search needs JavaScript. Without it, browse <a href="{u("topics.html")}">all topics</a> or <a href="{u("claims.html")}">all claims</a>.</p></noscript></div>')
    return page('search.html', 'Search', main, K, desc='Search every thing, claim, topic, session, kit item and glossary term.', scripts=('assets/search-data.js',),
                head=('Find', 'Search', '', ''), robots='noindex, follow')


def not_found_page(K):
    """404.html of the published community edition (GitHub Pages serves it for any missing path): a friendly way back."""
    at('404.html')
    ways = [('index.html', 'Overview', 'The event at a glance, the three days and where to start.'),
            ('search.html', 'Search', 'Every thing, claim, topic, session, kit item and glossary term.'),
            ('topics.html', 'Topics', 'Everything the event covered, by area.'),
            ('claims.html', 'All claims', 'Every claim with its permanent ID, in event order.')]
    li = ''.join(f'<li class="step tile"><div class="in"><h3><a class="stretch" href="{u(p)}">{e(t)}</a></h3><p>{e(d)}</p></div></li>' for p, t, d in ways)
    form = (f'<form class="search-big nf-search" role="search" action="{u("search.html")}" method="get"><label for="q404">Search the knowledge base</label>'
            '<div class="sb-row"><input id="q404" name="q" type="search" autocomplete="off" spellcheck="false" placeholder="Try: crawl budget, GSC, canonical">'
            '<button type="submit">Search</button></div></form>')
    note = empty_note('point', '<p><strong>Nothing lives at this address.</strong> The link may be old or mistyped, or the page moved when the '
                               'knowledge base grew. Claim IDs never change: search for one, such as D1-C094, to find it again.</p>')
    main = f'<div class="wrap narrow nf">{note}{form}{sec("Ways back to the reef", "ways")}<ul class="tiles nf-ways">{li}</ul></div>'
    return page('404.html', 'Page not found', main, K, desc='This page is not in the knowledge base.', robots='noindex',
                head=('Lost at sea', 'Page not found', 'Sorry, the page you were looking for is not here.', ''))


def sitemap_xml(pages, K):
    """sitemap.xml of the published community edition: every indexable page (not search.html, not 404.html) as an absolute
    address, in path order with the home page first; lastmod is the date of the version heading of CHANGELOG.md."""
    urls = sorted((p for p in pages if p.endswith('.html') and p not in ('search.html', '404.html')), key=lambda p: (p != 'index.html', p))
    lm = f'<lastmod>{K["vdate"]}</lastmod>' if K['vdate'] else ''
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + ''.join(f'<url><loc>{html.escape(abs_url(p), quote=False)}</loc>{lm}</url>\n' for p in urls) + '</urlset>\n')


def about_page(K):
    at('about.html')
    labs = ''.join(f'<li>{badge_label(k)}<div><strong>{e(LABELS[k][1])}.</strong> {e(t)}</div></li>' for k, t in (
        ('slide', 'Shown on a slide at the event, by Google or a community speaker, taken from a photo of the slide.'),
        ('stage', 'Taken from the author’s notes, a transcript or a recording. The speaker is named when known; audience questions say so.'),
        ('docs', 'Google’s own published pages, with a link. Placed next to the session it explains; it was not said there.'),
        ('press', 'A third-party publication, such as a search industry news site, reporting what Google or a Googler said. Useful context, but not Google’s own words on record.'),
        ('analysis', 'Advice and interpretation by Ibrahim Anjro. Never attribute it to Google.')))
    vers = ''.join(f'<li>{badge_ver(k) or "<span class=badge-none>No badge</span>"}<div>{e(VER[k][1])}</div></li>' for k in VER)
    rels = ''.join(f'<li><span class="rel rel-{k}">{v[0]}</span><div>{e(v[2])} The other claim shows “{e(v[1])}”.</div></li>' for k, v in REL.items())
    covs = ''.join(f'<li><span class="cov cov-{k}">{v}</span></li>' for k, v in COVERAGE.items())
    sample = next((c for c in K['claims'] if c['quote'] and c['label'] == 'slide' and c['verification'] != 'n/a'), None) or (K['claims'][0] if K['claims'] else None)
    demo = f'<div class="demo"><p class="demo-k">A claim as it appears on every page</p>{claim_card(sample, K, anchor=False)}</div>' if sample else ''
    main = (f'<div class="wrap narrow prose">'
            f'<p>{e(K["event"]["name"])} ran for {NUMS.get(len(K["days"]), len(K["days"]))} days in {e(K["event"]["city"])}. This site turns what was shown and said there into <strong>claims</strong>: '
            'short, self-contained statements, each with an ID, a label for who is speaking and a grade for how it stands against Google’s documentation.</p>'
            f'{demo}{sec("Labels: who is speaking", "labels")}<ul class="legend big">{labs}</ul>'
            f'{sec("Verification: is it in Google’s documentation?", "grades")}<p>Every technical claim made at the event was checked against Google’s public documentation.</p><ul class="legend big">{vers}</ul>'
            f'{sec("Links between claims", "links")}<p>Claims point to each other when a later talk returns to an earlier point, and answers point to the audience question they answer. '
            f'The <a href="{u("across-days.html")}">Across days</a> page lists every link.</p><ul class="legend big">{rels}</ul>'
            '<p>Under a claim, <strong>Used by</strong> lists what rests on it: the developer requirements, facts, myths, quotes, story angles and glossary terms '
            'of the two kits that cite it. Each topic page lists the requirements and facts built on its claims, and each source lists the claims it backs, by grade.</p>'
            f'{sec("Things", "things")}<p>A <strong>thing</strong> is a product, feature, crawler, report, directive, status code, standard, metric, concept, update or tool '
            f'the event talked about, such as Search Console, Googlebot, hreflang or 429. Under a claim, <strong>Things</strong> lists the ones it names, matched word for word '
            f'by name or other name. Each thing has a short card: what Google’s documentation says, what was only said at the event, the kit items built on those claims and '
            f'the things named with it most often. A card is a map, not a source: cite the claim IDs on it. <a href="{u("entities.html")}">All things</a>.</p>'
            f'<p>The <a href="{u("graph.html")}">{map_name("Reef map", "Graph")}</a> shows the same links as a map, one neighbourhood at a time: a thing, topic, '
            'kit item, document or claim in the centre and everything linked to it around it, with the full list beside the map. Click a neighbour, or tab to it and '
            'press Enter, to put it in the centre; the browser’s back button returns. Every thing’s card and every topic page has an “Open in” button that starts it there. '
            'Drag the background to pan, scroll or pinch to zoom, and drag a bubble to move it. Point at a bubble for a preview; its <strong>+</strong> grows its neighbours '
            'where it sits, and a right-click (a long press on a phone) opens a menu to open, pin or hide it. A trail along the top lists the centres you visited.</p>'
            f'{sec("Coverage of a session", "coverage")}<p>The agenda shows what the claims of each session were taken from.</p><ul class="covs wide">{covs}</ul>'
            f'{sec("Citing a claim", "cite")}<p>Every claim has a permanent ID such as <code>D1-C094</code>: Day 1, claim 94. IDs never change or get reused. '
            f'Link to <code>claims.html#D1-C094</code> on the <a href="{u("claims.html")}">All claims</a> page.</p>'
            f'{sec("What is deliberately not here", "privacy")}<p>No slide photographs, no transcripts, no private notes and nothing about other attendees. '
            'Claims are paraphrased, with quotations of 25 words or fewer only where the wording matters. Companies shown on stage as examples of broken sites are not named.</p>'
            f'{sec("Using this site offline", "offline")}<p>The whole site is a folder of plain files. Open <code>index.html</code> by double-clicking it: no server, no account, no network. '
            f'Search works offline too. Version {e(K["version"])}; data through {fdate(K["through"]) if K["through"] else "no day yet"}.</p>{who_made_it()}</div>')
    return page('about.html', 'How to read this site', main, K, desc='Labels, verification grades, links between claims and how to cite.',
                head=('Guide', 'How to read this site', 'Two things on every claim tell you how far to trust it: the label says who is speaking, the grade says whether Google’s documentation backs it.', ''), bot='read')


def who_made_it():
    """About, community edition: who made it, with the two links of edition.yaml."""
    if not community(): return ''
    by = f'<strong>{e(ED["author"])}</strong>, who attended the event,' if ED['author'] else 'an attendee of the event'
    links = f'<p class="who-links">{contacts()}</p>' if contacts() else ''
    how = (f'<p>How the claims were captured, labelled and checked against Google’s documentation, and where the method stops: '
           f'<a href="{u("method.html")}">{e(method_doc()["title"])}</a>.</p>')
    return (f'{sec("Who made this", "who")}<p>This community edition was made by {by} and is free to use and to share.</p>{links}{how}'
            '<p>Open for collaboration on this community version: corrections, ideas and contributions are welcome.</p>')


# ------------------------------------------------------------------ method.html: METHOD.md of the repository root (community edition)
METHOD_FALLBACK = 'How the claims were graded'
_METHOD = {}


def method_li():
    """The footer's "Find your way" link to the method write-up (community edition only)."""
    return f'<li><a href="{u("method.html")}">How the claims were graded</a></li>' if community() else ''


def md_link(text, url):
    """A Markdown link of METHOD.md on the site: an address of edition.yaml as its own link, another web address as an external
    link, a page of this site (method.html, about.html ...) as is, a file of the repository on the repository's host, else the text."""
    url = url.strip().strip('<>')
    if re.match(r'https?://', url):
        if url in (ED['company']['url'], ED['linkedin']) and community():
            return f'<a class="ext contact" href="{e(url)}" rel="noopener external" target="_blank">{text}</a>'
        if own_ok(url): return f'<a class="ext own" href="{e(url)}" rel="noopener external" target="_blank">{text}</a>'
        return f'<a class="ext" href="{e(url)}" rel="noopener external">{text}</a>'
    if url.startswith('#'): return f'<a href="{e(url)}">{text}</a>'
    path, _, frag = url.partition('#')
    path = re.sub(r'^(\./)+', '', path)
    if path.startswith('60-outputs/site/') and path.endswith('.html'): return f'<a href="{u(path[len("60-outputs/site/"):] + ("#" + frag if frag else ""))}">{text}</a>'
    if path and not path.startswith('../') and repo_file(path):
        return f'<a class="ext own" href="{e(repo_file(path) + ("#" + frag if frag else ""))}" rel="noopener external" target="_blank">{text}</a>'
    return text


def md_inline(s):
    """Inline Markdown of METHOD.md: `code`, **bold**, *italic* or _italic_, [text](link) and <https://...>; all else escaped."""
    kept = []
    def keep(html_):  # finished markup (a code span, a link), kept out of the formatting below as \0n\0
        kept.append(html_)
        return f'\0{len(kept) - 1}\0'
    def fmt(x):
        x = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', e(x))
        x = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', x)
        return re.sub(r'(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)', r'<em>\1</em>', x)
    s = re.sub(r'`([^`\n]+)`', lambda m: keep(f'<code>{e(m.group(1))}</code>'), s.replace('\0', ''))
    s = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', s)                            # an image: its alt text only
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)', lambda m: keep(md_link(fmt(m.group(1)), m.group(2))), s)
    s = re.sub(r'<(https?://[^>\s]+)>', lambda m: keep(md_link(e(m.group(1)), m.group(1))), s)
    s = fmt(s)
    while '\0' in s: s = re.sub('\0(\\d+)\0', lambda m: kept[int(m.group(1))], s)
    return s


def md_blocks(text, ids):
    """Block Markdown of METHOD.md: ## and ### headings (with ids), paragraphs, - and 1. lists, > quotes, tables, fenced code and
    --- rules. Raw HTML lines (a banner or divider image of the repository) are left out."""
    out, para, items, kind, quote = [], [], [], None, []
    lines = text.split('\n') + ['']
    def flush():
        nonlocal para, items, kind, quote
        if para: out.append('<p>' + md_inline(' '.join(para)) + '</p>'); para = []
        if items: out.append(f'<{kind}>' + ''.join(f'<li>{md_inline(x)}</li>' for x in items) + f'</{kind}>'); items, kind = [], None
        if quote: out.append('<blockquote class="md-quote">' + md_blocks('\n'.join(quote), ids) + '</blockquote>'); quote = []
    i = 0
    while i < len(lines):
        ln = lines[i]; i += 1
        st = ln.strip()
        m = re.match(r'\s*(`{3,}|~{3,})', ln)
        if m:
            flush(); code = []
            while i < len(lines) and not (lines[i].strip() and set(lines[i].strip()) == {m[1][0]} and len(lines[i].strip()) >= len(m[1])):
                code.append(lines[i]); i += 1
            i += 1
            out.append(code_block('', '\n'.join(code))); continue
        if st.startswith('>'):
            if para or items: flush()
            quote.append(re.sub(r'^\s*> ?', '', ln)); continue
        if quote: flush()
        h = re.match(r'(#{2,4})\s+(.+?)\s*#*\s*$', ln)
        if h:
            flush()
            t = md_plain(h[2]); sid = term_id(t) or 'section'
            n, base = 2, sid
            while sid in ids: sid, n = f'{base}-{n}', n + 1
            ids.add(sid)
            out.append(sec(t, sid) if len(h[1]) == 2 else f'<h{len(h[1])} class="md-h" id="{sid}">{md_inline(h[2])}</h{len(h[1])}>'); continue
        if re.fullmatch(r'(-{3,}|\*{3,}|_{3,})', st): flush(); out.append('<hr class="md-rule">'); continue
        if st.startswith('<') and st.endswith('>'): flush(); continue           # raw HTML of the repository page (images, dividers)
        if st.startswith('|') and i < len(lines) and re.fullmatch(r'\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?', lines[i].strip()):
            flush()
            cells = lambda r: [c.strip() for c in r.strip().strip('|').split('|')]
            head, rows = cells(ln), []
            num = [' class="num"' if c.endswith(':') and not c.startswith(':') else '' for c in cells(lines[i])]  # ---: right-aligned
            al = lambda k: num[k] if k < len(num) else ''
            i += 1
            while i < len(lines) and lines[i].strip().startswith('|'): rows.append(cells(lines[i])); i += 1
            out.append('<div class="md-table"><table><thead><tr>' + ''.join(f'<th scope="col"{al(k)}>{md_inline(c)}</th>' for k, c in enumerate(head)) + '</tr></thead><tbody>'
                       + ''.join('<tr>' + ''.join(f'<td{al(k)}>{md_inline(c)}</td>' for k, c in enumerate(r)) + '</tr>' for r in rows) + '</tbody></table></div>'); continue
        m = re.match(r'\s*([-*+]|\d+[.)])\s+(.*)', ln)
        if m:
            k = 'ol' if m[1][0].isdigit() else 'ul'
            if para or (kind and kind != k): flush()
            kind = k; items.append(m[2]); continue
        if not st: flush(); continue
        if items and ln[:1] in ' \t': items[-1] += ' ' + st; continue
        if items: flush()
        para.append(st)
    flush()
    return ''.join(out)


def method_doc():
    """METHOD.md split for its page: title (its # heading), lead (the first paragraph, when it comes before any other block),
    body (the rest as HTML), words, and whether the file was there. Read once per build."""
    if not _METHOD:
        t = METHOD_MD.read_text(encoding='utf-8').replace('\r\n', '\n') if METHOD_MD.exists() else ''
        m = re.search(r'^# (.+?)\s*#*\s*$', t, re.M)
        title = md_plain(m.group(1)).strip() if m else METHOD_FALLBACK
        rest = t[m.end():] if m else t
        lead, body = '', rest.strip('\n')
        first = re.match(r'((?:[^\n#>|<`\-*+\d\s][^\n]*\n?)+)(?:\n|$)', body)
        if first and len(first.group(1)) < 700:
            lead, body = ' '.join(x.strip() for x in first.group(1).strip().split('\n')), body[first.end():]
        _METHOD.update(title=title, lead=lead, body=body, found=bool(t.strip()), words=len(WORD.findall(md_plain(t))))
    return _METHOD


def method_page(K):
    """method.html: METHOD.md rendered in the site's look, or a short placeholder when the file is missing."""
    at('method.html')
    d = method_doc()
    desc = f'How {len(K["claims"]):,} claims from {K["event"]["name"]} were captured, labelled and graded against Google’s documentation, and where the method stops.'
    if d['found']:
        body = md_blocks(d['body'], set())
        mins = max(1, round(d['words'] / 220))
        meta = f'<p class="facts">{"By " + e(ED["author"]) + " · " if ED["author"] else ""}about {plural(mins, "minute")} to read</p>'
        lead = md_inline(d['lead']) if d['lead'] else ''
    else:
        src = repo_file('METHOD.md')
        body = (f'<div class="callout slim"><p>The method write-up is not in this copy of the site yet. It lives in <code>METHOD.md</code> at the root of the '
                f'repository{" (" + own_link(src, "open it on GitHub") + ")" if src else ""}. Until then, <a href="{u("about.html")}">How to read this site</a> '
                'explains the labels, the grades and how every claim was checked against Google’s documentation.</p></div>')
        meta, lead = '', 'How the claims were captured, labelled and checked against Google’s documentation.'
    main = f'<div class="wrap narrow prose method">{body}</div>'
    return page('method.html', d['title'], main, K, desc=desc, crumbs=(('about.html', 'How to read this site'),),
                head=('Method', d['title'], lead, meta), bot='read')


# Abbreviations and other names that neither the glossary nor 20-claims/entities.yaml spells out (plan B5.1): searching either side also
# finds the other. Since v2.9.0 most names come from the things of entities.yaml; this short list stays for the rest.
HAND_ALIASES = (('GSC', 'Search Console'), ('Google Search Console', 'Search Console'), ('SD', 'structured data'), ('CWV', 'Core Web Vitals'),
                ('LCP', 'Largest Contentful Paint'), ('INP', 'Interaction to Next Paint'), ('AIO', 'AI Overviews'), ('GMC', 'Merchant Center'),
                ('Google Merchant Center', 'Merchant Center'), ('JS', 'JavaScript'), ('SSR', 'server-side rendering'), ('CSR', 'client-side rendering'),
                ('LLM', 'large language model'), ('EEAT', 'E-E-A-T'), ('REP', 'Robots Exclusion Protocol'))
# What site.js searches in each kind of record: the fields of its title line (a match there ranks higher) and of the rest. The
# vocabulary for typo tolerance is built from exactly these fields, so a suggested word is always one that a search finds.
SEARCH_FIELDS = {'things': ('n al', 'k s id'), 'glossary': ('n', 'df'), 'topics': ('n', 'a s id'), 'reqs': ('n', 'id ar w h'), 'facts': ('t', 'id us'), 'myths': ('m', 'f id'),
                 'angles': ('n', 'h pt au id'), 'quotes': ('q', 'cr id c'), 'sessions': ('n', 'w k id dy'), 'claims': ('t', 'q w s tp id')}


def alias_groups(K):
    """alias -> the other names of the same thing, every name normalised as site.js norm() does. From the glossary (links.json
    aliases): a term written 'Name (other name)' makes the two names synonyms ('Crawl rate limit (hostload)', 'Cumulative Layout
    Shift (CLS)'); the parts of 'A and B' name different things and are not expanded. Plus HAND_ALIASES, and each thing's name
    with its other names from entities.json (GSC, Google Search Console, Search Console)."""
    key = lambda s: ' '.join(words(s))
    parent = {}
    def find(x):
        while parent.setdefault(x, x) != x: x = parent[x]
        return x
    def join(x, y): parent[find(x)] = find(y)
    items = K['links']['items']
    for n, it in items.items():
        if not n.startswith('term:'): continue
        m = re.fullmatch(r'(.+?)\s*\(([^()]+)\)', it['name'])
        if not m or ',' in m[2] or re.search(r'\sand\s', m[1]): continue
        names = [key(m[1]), key(m[2])]
        if not all(x in K['links']['aliases'] and n in K['links']['aliases'][x] for x in names): continue  # the same seed as build_kb.py
        join(*names)
    for x, y in HAND_ALIASES: join(key(x), key(y))
    for x in K['ents'].values():  # a thing's name and its other names (20-claims/entities.yaml)
        for a in x['aliases']:
            if key(a) and key(a) != key(x['name']): join(key(a), key(x['name']))
    groups = {}
    for x in parent: groups.setdefault(find(x), []).append(x)
    return {x: sorted(y for y in groups[find(x)] if y != x) for x in sorted(parent) if len(groups[find(x)]) > 1}


def alias_names(K, groups):
    """How to print each alias key in the search note ("GSC = Google Search Console, Search Console"): the glossary's spelling
    first, then HAND_ALIASES'; a key with no spelling is printed as it is."""
    key, out = (lambda s: ' '.join(words(s))), {}
    for n, it in K['links']['items'].items():
        m = re.fullmatch(r'(.+?)\s*\(([^()]+)\)', it['name']) if n.startswith('term:') else None
        for s in (m[1], m[2]) if m else ():
            out.setdefault(key(s), s.strip())
    for pair in HAND_ALIASES:
        for s in pair: out.setdefault(key(s), s)
    for x in K['ents'].values():
        for s in [x['name']] + x['aliases']: out.setdefault(key(s), s)
    return {k: out[k] for k in sorted(groups) if k in out}


def search_data(K):
    """window.KB_SEARCH: every claim, topic, session, requirement, fact, myth, quote, story angle and glossary term, with the
    aliases, the vocabulary (every word of the searched fields, most frequent first) and the proven speakers."""
    sp = K['links']['speakers']
    who = sp['claims']
    data = {'things': [], 'claims': [], 'topics': [], 'sessions': [], 'glossary': [], 'reqs': [], 'facts': [], 'myths': [], 'quotes': [], 'angles': [],
            'labels': {k: v[0] for k, v in LABELS.items()}, 'grades': {k: v[0] for k, v in VER.items()},
            'levels': {k: v[0] for k, v in LEVELS.items()}, 'statuses': {k: v[0] for k, v in KSTATUS.items()}}
    for c in K['claims']:
        s = K['sess'][c['session_id']]
        w = c['speaker'] if c['label'] in ('slide', 'stage') else c['author']
        x = {'id': c['id'], 'd': c['day'], 'l': c['label'], 'v': c['verification'], 't': c['text'], 'q': c['quote'], 'w': w or '',
             's': s['title'], 'tp': ' '.join(K['topics'][t]['title'] for t in c['topics']), 'u': 'claims.html#' + c['id']}
        if c['id'] in who:
            x['g'] = who[c['id']]['group']
            if who[c['id']]['name']: x['p'] = who[c['id']]['name']
        data['claims'].append(x)
    for k in sorted(K['ents'], key=lambda k: (-len(K['ents'][k]['claims']), K['ent_order'].index(k))):  # most named first: ties rank the bigger thing first
        x = K['ents'][k]
        data['things'].append({'id': k, 'n': x['name'], 'al': ' · '.join(x['aliases']), 'k': ENT_KINDS[x['kind']][0], 'ki': x['kind'], 's': x['summary'],
                               'c': len(x['claims']), 'u': ent_url(k)})
    for t in K['topics'].values():
        data['topics'].append({'id': t['id'], 'n': t['title'], 'a': t['area']['title'], 's': t['summary'], 'c': len(t['claim_ids']), 'u': f'topics/{t["id"]}.html'})
    for s in K['sess'].values():
        data['sessions'].append({'id': s['id'], 'n': s['title'], 'd': s['day'], 'dy': f'day {s["day"]}', 'tm': s['time'], 'w': ', '.join(s['speakers']),
                                 'k': KINDS[s['kind']], 'c': s['claim_count'], 'u': session_url(s)})
    area = {r['id']: a['title'] for a in K['dev']['areas'] for r in a['requirements']}
    for n in K['kit_order']:
        kind, x, cids, url = K['kit'][n]
        if community() and kind in ('fact', 'myth', 'quote', 'angle'): continue  # the media kit is not searched in the community edition
        if kind == 'req':
            data['reqs'].append({'id': x['id'], 'n': md_plain(x['title']), 'lv': x['level'], 'st': x['status'], 'ar': area[x['id']], 'w': md_plain(x['why']),
                                 'h': md_plain(x['how'] + '\n' + x['test']), 'u': url})
        elif kind == 'fact': data['facts'].append({'id': x['id'], 't': x['statement'], 'st': x['status'], 'us': USES[x['use']], 'u': url})
        elif kind == 'myth': data['myths'].append({'id': x['id'], 'm': x['myth'], 'f': x['fact'], 'st': x['status'], 'u': url})
        elif kind == 'quote':
            q = {'id': x['id'], 'q': x['quote'], 'cr': x['credit'], 'c': x['claim'], 'd': x['day'], 'u': url}
            if x['claim'] in who: q['g'] = who[x['claim']]['group']
            if x['speaker']: q['p'] = x['speaker']
            data['quotes'].append(q)
        elif kind == 'angle':
            data['angles'].append({'id': x['id'], 'n': x['title'], 'h': x['hook'], 'pt': ' '.join(p['text'] for p in x['points']), 'au': ', '.join(x['audience']), 'u': url})
        else: data['glossary'].append({'id': x['id'], 'n': x['term'], 'df': x['definition'], 'u': url})
    voc = Counter()
    for k, (fa, fb) in SEARCH_FIELDS.items():
        for x in data[k]: voc.update(dict.fromkeys(words(' '.join('' if x.get(f) is None else str(x[f]) for f in (fa + ' ' + fb).split())), 1))
    groups = alias_groups(K)
    data.update(fields=SEARCH_FIELDS, aliases=groups, alias_names=alias_names(K, groups), vocab=' '.join(sorted(voc, key=lambda w: (-voc[w], w))),
                speakers={'names': sp['names'], 'groups': sp['groups']})
    return 'window.KB_SEARCH = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n'


# ------------------------------------------------------------------ the Reef map (knowledge graph phase 2, since v2.10.0)
# The explorer page (_system/templates/graph.template.html) reads window.KB_GRAPH: the nodes and edges of the agent pack's
# graph.json that a neighbourhood shows (things, topics, kit items, sources and claims; sessions, days and areas stay out), with
# what the side panel prints about each. graph.json is checked against what the cards print: a thing's neighbours on the map are
# exactly the claims, documentation, kit items, relations, co-mentions and topics of its card.
GRAPH_KINDS = ('entity', 'topic', 'requirement', 'fact', 'myth', 'quote', 'angle', 'term', 'source', 'claim')
GRAPH_TYPES = ('is-a', 'part-of', 'uses', 'affects', 'measured-by', 'applies-to', 'co-mentioned', 'mentions', 'features', 'related', 'about', 'defines',
               'rests-on', 'documented-in', 'cites', 'repeats', 'extends', 'contradicts', 'updates', 'answers')
GRAPH_TPL = HERE.parent / 'templates' / 'graph.template.html'
GRAPH_SLOTS = ('/*STYLE*/', '<!--GRAPH-DATA-->')  # each exactly once in the template
# the template's tab icon: the Deep Dive one in href, the Art Deco one in data-deco; the page keeps the one of the build's style
ICON_LINK = re.compile(r'<link rel="icon" type="image/svg\+xml" href="([^"]*)" data-deco="([^"]*)">')


def js_safe(s):
    """JSON text that is safe inside a <script> element (no </script>, no line separators that end a JS string)."""
    for a, b in (('<', '\\u003c'), ('>', '\\u003e'), ('&', '\\u0026'), (' ', '\\u2028'), (' ', '\\u2029')):
        s = s.replace(a, b)
    return s


def graph_data(K):
    """window.KB_GRAPH from the agent pack's graph.json, enriched with what the pages print (a claim's full text and session, a
    topic's summary, a thing's other names and home topics). Errors: an edge that ends at no node, or a thing whose neighbours in
    graph.json differ from its card."""
    p = PACK / 'graph.json'
    if not p.exists(): sys.exit(f'ERROR: {p} is missing. Run python _system/build_kb.py first.')
    try: g = json.loads(p.read_text(encoding='utf-8'))
    except json.JSONDecodeError as x: sys.exit(f'ERROR: graph.json: {x}')
    errs, w = [], 'graph.json'
    if not isinstance(g, dict) or not isinstance(g.get('nodes'), list) or not isinstance(g.get('edges'), list): fail([f'{w}: expected an object with nodes and edges'])
    if g.get('version') != K['links']['version']: errs.append(f'{w} is {g.get("version")} but links.json is {K["links"]["version"]}: run build_kb.py')
    byid = {}
    for n in g['nodes']:
        if not isinstance(n, dict) or not isinstance(n.get('id'), str) or n['id'] in byid: errs.append(f'{w}: bad or duplicate node {n!r:.80}'); continue
        byid[n['id']] = n
    adj = {}
    for x in g['edges']:
        if not isinstance(x, dict) or x.get('from') not in byid or x.get('to') not in byid: errs.append(f'{w}: edge {x!r:.120} ends at no node'); continue
        adj.setdefault(x['from'], []).append((x['type'], 0, x['to'], x))
        adj.setdefault(x['to'], []).append((x['type'], 1, x['from'], x))
    if errs: fail(errs)
    # the contract with the cards: the same neighbours, from the same derived links
    for k, x in sorted(K['ents'].items()):
        nid, ww = f'ent:{k}', f'{w} ent:{k}'
        if nid not in byid: errs.append(f'{ww}: missing, but entities.json has it'); continue
        got = lambda t, back, pre: sorted(o for tt, b, o, _ in adj.get(nid, ()) if tt == t and (back is None or b == back) and o.startswith(pre))
        want = (('mentions', 1, 'claim:', [f'claim:{i}' for i in x['claims']]), ('features', 1, 'topic:', [f'topic:{t}' for t in K['topics'] if K['feat'][t][k]]),
                ('co-mentioned', None, 'ent:', [f'ent:{o}' for o in K['co'][k]]), ('documented-in', 0, 'source:', [f'source:{s}' for s in x['docs']]),
                ('about', 1, '', [y['id'] for y in x['items']]))
        for t, back, pre, ids in want:
            if got(t, back, pre) != sorted(ids): errs.append(f'{ww}: its {t} neighbours differ from its card')
        rel = sorted((t, b, o[4:]) for t, b, o, _ in adj.get(nid, ()) if t in ENT_REL)
        if rel != sorted((t, b, o) for t, b, o, _ in K['erel'][k]): errs.append(f'{ww}: its typed relations differ from its card')
    if errs: fail(errs)
    kit_url = {n: v[3] for n, v in K['kit'].items()}
    sess = sorted(K['sess'])
    si = {s: i for i, s in enumerate(sess)}
    nodes, index = [], {}
    for n in g['nodes']:
        if n['kind'] not in GRAPH_KINDS: continue
        i, kind = n['id'], n['kind']
        x = {'i': i, 'k': kind, 'n': n['name']}
        if kind == 'entity':
            en = K['ents'][i[4:]]
            x.update(n=en['name'], ek=en['kind'], s=en['summary'], u=ent_url(i[4:]))
            if en['aliases']: x['al'] = en['aliases']
            if en['topics']: x['home'] = [f'topic:{t}' for t in en['topics']]
        elif kind == 'topic':
            t = K['topics'][i[6:]]
            x.update(n=t['title'], s=snippet(' '.join(t['summary'].split()), 300), a=t['area']['title'], u=f'topics/{t["id"]}.html')
        elif kind == 'claim':
            c = K['byid'][i[6:]]
            x.update(n=c['text'], l=c['label'], v=c['verification'], d=c['day'], ss=si[c['session_id']], u=f'claims.html#{c["id"]}')
        elif kind == 'source':
            s = K['sources'][i[7:]]
            x.update(n=s['title'], pk=s['kind'], pb=s['publisher'], u=s['url'])
        else:
            pre, rec, _, url = K['kit'][i]
            if pre == 'term': x.update(n=rec['term'], s=rec['definition'], u=url)
            else: x.update(n=kit_title(i, K), id=rec['id'], u=url)
            if pre in ('req', 'fact', 'myth'): x['st'] = rec['status']
            if pre == 'req': x['lv'] = rec['level']
        index[i] = len(nodes)
        nodes.append(x)
    edges = []
    for x in g['edges']:
        if x['type'] not in GRAPH_TYPES or x['from'] not in index or x['to'] not in index: continue
        r = [index[x['from']], index[x['to']], GRAPH_TYPES.index(x['type']), x.get('count') or 0]
        if x.get('claims') and x['type'] in ENT_REL: r.append([index[f'claim:{c}'] for c in x['claims']])
        edges.append(r)
    start = 'ent:googlebot' if 'ent:googlebot' in index else (f'ent:{max(K["ents"], key=lambda k: (len(K["ents"][k]["claims"]), k))}' if K['ents'] else nodes[0]['i'] if nodes else '')
    data = {'version': K['links']['version'], 'through': K['through'], 'start': start, 'types': GRAPH_TYPES,
            'ekinds': {k: v[0] for k, v in ENT_KINDS.items()}, 'erel': {k: v[:2] for k, v in ENT_REL.items()}, 'rel': {k: v[:2] for k, v in REL.items()},
            'labels': {k: v[0] for k, v in LABELS.items()}, 'grades': {k: v[0] for k, v in VER.items()}, 'levels': {k: v[0] for k, v in LEVELS.items()},
            'statuses': {k: v[0] for k, v in KSTATUS.items()}, 'sessions': [f'Day {K["sess"][s]["day"]} · {stitle(K["sess"][s])}' for s in sess],
            'aliases': alias_groups(K), 'nodes': nodes, 'edges': edges}
    return 'window.KB_GRAPH = ' + js_safe(json.dumps(data, ensure_ascii=False, separators=(',', ':'))) + ';\n'


def graph_pages(data_js):
    """The Reef map twice from one template: the web edition's graph.html loads assets/graph-data.js; 50-maps/graph.html, next to
    the mindmap, carries the same data inline so it works on its own."""
    if not GRAPH_TPL.exists(): sys.exit(f'ERROR: {GRAPH_TPL.relative_to(ROOT)} is missing: the Reef map cannot be built')
    tpl = GRAPH_TPL.read_text(encoding='utf-8')
    bad = [s for s in GRAPH_SLOTS if tpl.count(s) != 1]
    if bad: sys.exit(f'ERROR: {GRAPH_TPL.relative_to(ROOT)} must contain {" and ".join(bad)} exactly once')
    tpl = tpl.replace('/*STYLE*/', STYLE, 1)
    tpl = ICON_LINK.sub(lambda m: f'<link rel="icon" type="image/svg+xml" href="{m[2] if STYLE == "art-deco" else m[1]}">', tpl, count=1)
    return (tpl.replace('<!--GRAPH-DATA-->', '<script src="assets/graph-data.js"></script>', 1),
            tpl.replace('<!--GRAPH-DATA-->', '<script>' + data_js.rstrip('\n') + '</script>', 1))


# ------------------------------------------------------------------ kits: for developers, for content teams
def inline(s):
    """Escaped text with `code`, **bold** and [text](https://...) links; nothing else becomes markup."""
    def fmt(x):
        x = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', e(x))
        return re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a class="ext" href="\2" rel="noopener external">\1</a>', x)
    return ''.join(f'<code>{e(p[1:-1])}</code>' if len(p) > 1 and p[0] == p[-1] == '`' else fmt(p) for p in re.split(r'(`[^`\n]+`)', s))


def rich(s):
    """A kit text of several lines: paragraphs, - and 1. lists, fenced code."""
    out, para, items, kind, code = [], [], [], None, None
    def flush():
        nonlocal para, items, kind
        if para: out.append('<p>' + ' '.join(inline(x) for x in para) + '</p>'); para = []
        if items: out.append(f'<{kind}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{kind}>'); items, kind = [], None
    for ln in str(s).strip().split('\n'):
        if code is not None:
            if ln.strip() and set(ln.strip()) == {code[0][0]} and len(ln.strip()) >= len(code[0]):
                out.append(code_block('', '\n'.join(code[1]))); code = None
            else: code[1].append(ln)
            continue
        m = re.match(r'\s*(`{3,}|~{3,})', ln)
        if m: flush(); code = (m[1], []); continue
        m = re.match(r'\s*([-*+]|\d+[.)])\s+(.*)', ln)
        if m:
            k = 'ol' if m[1][0].isdigit() else 'ul'
            if para or (kind and kind != k): flush()
            kind = k; items.append(m[2]); continue
        if not ln.strip(): flush(); continue
        if items and ln[:1] in ' \t': items[-1] += ' ' + ln.strip(); continue
        if items: flush()
        para.append(ln.strip())
    if code is not None: out.append(code_block('', '\n'.join(code[1])))
    flush()
    return ''.join(out)


LANGS = {'html': 'HTML', 'json': 'JSON', 'jsonld': 'JSON-LD', 'json-ld': 'JSON-LD', 'javascript': 'JavaScript', 'js': 'JavaScript', 'xml': 'XML', 'http': 'HTTP',
         'robots.txt': 'robots.txt', 'robots': 'robots.txt', 'text': 'Text', 'apache': 'Apache', 'nginx': 'nginx', 'bash': 'Shell', 'sh': 'Shell', 'shell': 'Shell'}


def code_block(lang, code):
    name = LANGS.get(lang.lower(), lang) or 'Code'
    return (f'<div class="code-wrap copyable"><div class="code-bar"><span class="code-lang">{e(name)}</span><button class="copy" type="button" hidden>Copy</button></div>'
            f'<pre class="code" tabindex="0"><code class="copy-src">{e(code)}</code></pre></div>')


def snippet_html(s, head=True):
    body = (f'<p>{inline(s["text"])}</p>' if s['text'] else '') + ''.join((f'<p class="code-note">{inline(b["note"])}</p>' if b['note'] else '') + code_block(b['lang'], b['code']) for b in s['code'])
    if not head: return body
    return f'<details class="kd snip"><summary>Code · {e(s["title"])}</summary><div class="kd-in">{body}</div></details>'


def lv_badge(lv): return f'<span class="lv lv-{lv}" title="{e(LEVELS[lv][1])}">{LEVELS[lv][0]}</span>'
def st_badge(st): return f'<span class="badge ver st-{st}" title="{e(KSTATUS[st][1])}">{e(KSTATUS[st][0])}</span>'


def kit_evidence(refs, docs=(), label='Evidence'):
    """Cited claims with their label, grade and credit, then the Google pages (given, or else the Google sources of the claims)."""
    docs = list({x['url']: x for x in (list(docs) or [s for r in refs for s in r['sources'] if s['kind'] == 'google'])}.values())
    press = list({x['url']: x for r in refs for x in r['sources'] if x['kind'] == 'press'}.values())
    li = ''.join(f'<li><div class="ev-head">{badge_label(r["label"])}{badge_ver(r["verification"])}<span class="sp"></span>{cid_link(r["id"])}</div>'
                 f'<p>{e(r["text"])}</p><p class="ev-by">{e(r["credit"])}</p></li>' for r in refs)
    n = plural(len(refs), 'claim') + (f' · {plural(len(docs), "Google page")}' if docs else '')
    srcs = ''.join(source_li(x) for x in docs + press)
    return (f'<details class="kd evid"><summary>{e(label)} · {n}</summary><div class="kd-in"><ul class="ev-list">{li}</ul>'
            + (f'<ul class="srcs">{srcs}</ul>' if srcs else '') + '</div></details>')


def topic_chips(x, K):
    """The topics of a kit item's claims (its `topics`, most frequent first), as links."""
    return ('<ul class="chips small kit-topics" aria-label="Topics">' + ''.join(f'<li><a href="{u("topics/" + t + ".html")}">{e(K["topics"][t]["title"])}</a></li>'
                                                                         for t in x['topics']) + '</ul>') if x['topics'] else ''


def kit_filter(items, noun, groups):
    """groups: [(name, title, [(value, label_html)])]; site.js shows the items whose data-<name> holds a ticked value."""
    g = ''.join(f'<div class="fgroup" role="group" aria-label="{e(t)}"><span class="k">{e(t)}</span>'
                + ''.join(f'<label><input type="checkbox" name="{n}" value="{e(v)}" checked> {lab}</label>' for v, lab in opts) + '</div>' for n, t, opts in groups)
    return f'<div class="filter kit-filter" data-items="{items}" data-noun="{noun}" role="group" aria-label="Filter" hidden>{g}<p class="filter-n" aria-live="polite"></p></div>'


def kit_tiles(items):
    return '<ul class="tiles start kit-tiles">' + ''.join(f'<li class="step tile"><div class="in"><p class="tile-k">{k}</p><h3><a class="stretch" href="{u(p)}">{e(t)}</a></h3><p>{d}</p></div></li>'
                                                          for k, t, p, d in items) + '</ul>'


def dl_list(items):
    return '<ul class="downloads">' + ''.join(f'<li><a href="{u(p)}" download><span class="dl-t">{e(t)}</span><span class="dl-m">{e(m)}</span></a></li>' for p, t, m in items) + '</ul>'


def dev_reqs(K):
    return [(a, r) for a in K['dev']['areas'] for r in a['requirements']]


def reach(hid, title, text, line):
    """The community edition's one note on working together (the Content page, the Developers page): a callout with its heading,
    a short text and the two links of edition.yaml after `line`."""
    links = f'<p class="reach-ln">{e(line)} {contacts()}</p>' if contacts() else ''
    return (f'<section class="callout reach" id="{hid}" aria-labelledby="{hid}-h"><p class="callout-k">Working together</p>'
            f'<h2 class="reach-h" id="{hid}-h">{e(title)}</h2><p>{e(text)}</p>{links}</section>')


def dev_reach():
    """Developers page, community edition: the kit stays open; a team with many sites can have it built into an agent."""
    if not community(): return ''
    return reach('with-us', 'From checklist to an agent that guards every site',
                 'This developer kit is free and stays open. If you manage many websites, we can build it into your workflow: an agentic system that checks '
                 'every site against these requirements on each release, flags what breaks with the claim and the Google page behind it, and keeps launches clean.',
                 'Open for collaboration on this community version:')


def dev_reach_line():
    """The end of a developer kit subpage, community edition: one quiet line to the note on the Developers page."""
    if not community(): return ''
    return f'<p class="reach-line">Looking after many sites? <a href="{u("dev/index.html")}#with-us">This kit can run as an agent on every release</a>.</p>'


def dev_page(K, dls):
    at('dev/index.html')
    dev, reqs = K['dev'], dev_reqs(K)
    snips = {s['key']: s for s in dev['snippets']}
    lv = Counter(r['level'] for _, r in reqs)
    st = stats([('Requirements', len(reqs))] + [(LEVELS[k][0], lv[k]) for k in LEVELS])
    tiles = kit_tiles([('One page', 'Pre-launch checklist', 'dev/checklist.html', f'The {lv["MUST"] + lv["AVOID"]} MUST and AVOID items to tick off before a launch or a migration.'),
                       ('Copy and paste', 'Code snippets', 'dev/snippets.html', f'{plural(len(snips), "snippet")}: HTML, JSON-LD, robots.txt, HTTP headers and more, each with a copy button.'),
                       ('Before you build', 'Differences ledger', 'dev/differences.html', f'{plural(len(K["difs"]["rows"]), "place")} where the event and Google’s documentation differ, '
                        'and what to follow.')])
    legend = ('<div class="callout"><p class="callout-k">How to read a requirement</p><ul class="kit-legend">'
              + ''.join(f'<li>{lv_badge(k)} {e(v[1])}</li>' for k, v in LEVELS.items())
              + ''.join(f'<li>{st_badge(k)} {e(KSTATUS[k][1])}</li>' for k in ('documented', 'event-only')) + '</ul></div>')
    jump = '<nav class="jump" aria-label="Areas"><ul>' + ''.join(f'<li><a href="#{e(a["id"])}">{e(a["title"])}</a></li>' for a in dev['areas']) + '</ul></nav>'
    filt = kit_filter('.req', 'requirement', [('level', 'Level', [(k, lv_badge(k)) for k in LEVELS]), ('status', 'Status', [(k, st_badge(k)) for k in ('documented', 'event-only')])])
    body = ''
    for a in dev['areas']:
        cards = ''
        for r in a['requirements']:
            cards += (f'<article class="req" id="{e(r["id"])}" data-level="{r["level"]}" data-status="{r["status"]}">'
                      f'<div class="claim-head">{lv_badge(r["level"])}{st_badge(r["status"])}<span class="sp"></span><a class="cid" href="#{e(r["id"])}">{e(r["id"])}</a></div>'
                      f'<h3 class="req-t">{inline(r["title"])}</h3><dl class="req-grid"><dt>Why</dt><dd class="rich">{rich(r["why"])}</dd>'
                      f'<dt>How</dt><dd class="rich">{rich(r["how"])}</dd><dt>Test</dt><dd class="rich">{rich(r["test"])}</dd></dl>'
                      + topic_chips(r, K) + (snippet_html(snips[r['snippet']]) if r['snippet'] else '') + kit_evidence(r['claims'], r['docs']) + '</article>')
        body += f'<section class="req-area" data-group aria-labelledby="{e(a["id"])}">{sec(a["title"], a["id"], len(a["requirements"]))}<div class="blurb rich">{rich(a["intro"])}</div>{cards}</section>'
    downloads = f'<section aria-labelledby="dl">{sec("Take it with you", "dl")}{dl_list(dls)}</section>' if dls else ''
    main = (f'<div class="wrap">{st}{tiles}<div class="two">{legend}<div class="callout slim"><p class="callout-k">Use it in your tracker</p>'
            '<p>Import the CSV into Jira, Linear, GitHub Issues or a spreadsheet: one ticket per requirement, with the test as the acceptance criterion and the level as the priority. '
            'Each requirement cites the claims it rests on: follow an ID to see exactly what was said and how it stands against Google’s documentation.</p></div></div>'
            f'{sec("Requirements by area", "reqs", len(reqs))}{jump}{filt}{body}{dev_reach()}{downloads}</div>')
    lead = (f'{plural(len(reqs), "requirement")} for sites that Google can crawl, render, index and show well, drawn from {K["short"]} and checked against Google’s '
            'documentation. Each one says why it matters, how to build it, how to test it, and what it rests on.')
    return page('dev/index.html', 'For developers', main, K, desc='Requirements, a pre-launch checklist and code snippets for developers building SEO-friendly sites.',
                head=('Developer kit', 'For developers', e(lead), ''), section='dev/index.html', bot='point')


def checklist_page(K):
    at('dev/checklist.html')
    body, n = '', 0
    for a in K['dev']['areas']:
        items = [r for r in a['requirements'] if r['level'] in ('MUST', 'AVOID')]
        if not items: continue
        n += len(items)
        li = ''.join(f'<li><label><input type="checkbox" value="{e(r["id"])}"><span class="cl-t">{lv_badge(r["level"])} <span class="cl-id">{e(r["id"])}</span> <span class="cl-title">{inline(r["title"])}</span>'
                     + (' <em class="cl-ev">said at Search Central Live</em>' if r['status'] == 'event-only' else '') + '</span></label>'
                     f'<div class="cl-test"><span class="k">Test</span><div class="rich">{rich(r["test"])}</div></div><a class="cl-more" href="{u("dev/index.html#" + r["id"])}">Why and how</a></li>' for r in items)
        body += f'<section aria-labelledby="c-{e(a["id"])}">{sec(a["title"], "c-" + a["id"], len(items))}<ul class="checklist">{li}</ul></section>'
    tools = '<div class="cl-bar"><p id="cl-progress" class="cl-progress" aria-live="polite"></p><button id="cl-reset" class="show-all" type="button" hidden>Clear all ticks</button></div>'
    main = f'<div class="wrap narrow"><div id="checklist" class="cl">{tools}{body}</div><p class="hint">Ticks are kept in this browser only. Print the page for a paper copy.</p>{dev_reach_line()}</div>'
    return page('dev/checklist.html', 'Pre-launch checklist', main, K, desc='Every MUST and AVOID requirement of the developer kit, to tick off before a launch.',
                crumbs=(('dev/index.html', 'For developers'),),
                head=('Developer kit', 'Pre-launch checklist', f'{plural(n, "item")} for the release review. Tick a MUST item when it is in place and an AVOID item when you have confirmed the site does not do it.', ''),
                section='dev/index.html')


def snippets_page(K):
    at('dev/snippets.html')
    title = {r['id']: r['title'] for _, r in dev_reqs(K)}
    body = ''
    for s in K['dev']['snippets']:
        used = ', '.join(f'<a href="{u("dev/index.html#" + x)}">{e(x)}</a> {inline(title.get(x, ""))}' for x in s['used_by']) or 'No requirement yet'
        body += (f'<section class="snip-card" aria-labelledby="s-{e(s["key"])}"><h2 class="sec-h" id="s-{e(s["key"])}">{e(s["title"])}</h2>'
                 f'{snippet_html(s, head=False)}<p class="src-by"><span class="k">Used by</span> {used}</p></section>')
    main = f'<div class="wrap narrow">{body}{dev_reach_line()}</div>'
    return page('dev/snippets.html', 'Code snippets', main, K, desc='Copy-paste code for SEO-friendly sites: HTML, JSON-LD, robots.txt, HTTP headers.',
                crumbs=(('dev/index.html', 'For developers'),),
                head=('Developer kit', 'Code snippets', f'{plural(len(K["dev"]["snippets"]), "snippet")} to copy into templates and server configuration. Replace example.com and the sample values with your own.', ''),
                section='dev/index.html')


CONTENT_PAGES = [('facts', 'Fact sheet', 'Headline-ready facts, each with its status and evidence.'), ('myths', 'Myths and facts', 'Common beliefs, answered from the event and the documentation.'),
                 ('angles', 'Story angles', 'Ready-made angles: audience, formats, hook, points, cautions and a call to action.'),
                 ('quotes', 'Quotes', 'Short quotations with the credit line to use.'), ('glossary', 'Glossary', 'The terms, in plain English.'),
                 ('numbers', 'Numbers registry', 'Every figure of the kit with its scope and credit, and the figures no fact cites yet.'),
                 ('questions', 'Question bank', 'Audience questions with their answers, and what Google said about each thing.')]
NOUNS = {'facts': 'fact', 'myths': 'myth', 'angles': 'angle', 'quotes': 'quote', 'glossary': 'term'}


def content_page(K, dls):
    if community(): return wall_page(K)
    at('content/index.html')
    lib = K['lib']
    n = {'numbers': plural(len(K['nums']['facts']), 'stat fact'), 'questions': plural(len(K['qbank']['audience']), 'question')}
    tiles = kit_tiles([(n.get(k) or plural(len(lib[k]), NOUNS[k]), t, f'content/{k}.html', e(d)) for k, t, d in CONTENT_PAGES])
    rules = '<div class="callout"><p class="callout-k">Wording rules</p><ol>' + ''.join(f'<li>{inline(x)}</li>' for x in lib['wording_rules']) + '</ol></div>'
    labels = '<ul class="kit-legend lab-l">' + ''.join(f'<li>{st_badge(k)}<span>{e(v[1])}</span></li>' for k, v in KSTATUS.items()) + '</ul>'
    credit = (f'<ul class="credit-l"><li>What Google said or showed: “Google at {e(lib["event"])} (Day N)”.</li><li>What a community speaker said: “a community speaker at {e(lib["event"])} (Day N)”. '
              'Never present it as Google’s position.</li><li>Google’s documentation: name the page and link it.</li>'
              '<li>Name a speaker only where the kit gives one. Who said it matters less than what was said and how well it is documented.</li></ul>')
    downloads = (f'<section aria-labelledby="dl">{sec("For AI content tools", "dl")}<p class="blurb">The whole kit as one JSON file, with the claim texts, labels, verification '
                 f'and source URLs resolved.</p>{dl_list(dls)}</section>') if dls else ''
    main = (f'<div class="wrap">{tiles}<div class="two"><div>{rules}<section aria-labelledby="credit">{sec("Credit lines", "credit")}{credit}</section></div>'
            f'<section aria-labelledby="labels">{sec("Labels", "labels")}{labels}</section></div>{downloads}</div>')
    lead = (f'Facts, myths, story angles, quotes and a glossary from {K["short"]}, ready for posts, articles, newsletters, videos and talks. '
            'Every item is tied to the claims it rests on and labelled by how far Google’s documentation backs it.')
    return page('content/index.html', 'For content teams', main, K, desc='Facts, myths, story angles, quotes and a glossary for media and content teams.',
                head=('Content kit', 'For content teams', e(lead), ''), section='content/index.html', bot='wave')


def content_sub(K, key, main, lead):
    title = dict((k, t) for k, t, _ in CONTENT_PAGES)[key]
    return page(f'content/{key}.html', title, main, K, desc=lead, crumbs=(('content/index.html', 'Media kit' if community() else 'For content teams'),),
                head=('Content kit', title, e(lead), ''), section='content/index.html')


def count_words(n, one, many=None):
    """'three facts', 'one story angle': a number in words up to nine, else in figures."""
    return f'{NUMS.get(n, n)} {one if n == 1 else many or one + "s"}'


def and_list(xs):
    xs = [x for x in xs if x]
    return ', '.join(xs[:-1]) + (', and ' if len(xs) > 2 else ' and ') + xs[-1] if len(xs) > 1 else ''.join(xs)


def wall_page(K):
    """The Content page of the community edition. The media kit is not in this edition: what the full kit holds (the counts of
    edition.yaml full_kit; a count it does not give is left out), a small taste (the preview items of content-library.json as the
    full kit's own cards, so every link to a preview item lands on its card here), one soft note on working together, the
    glossary (open) and the wording rules the kit follows."""
    at('content/index.html')
    lib, fk = K['lib'], ED['full_kit']
    held = and_list([f'{fk["facts"]} facts with safe wording' if fk.get('facts') else '',
                     f'{fk["myths"]} myths with the facts that answer them' if fk.get('myths') else '',
                     f'{fk["angles"]} story angles' if fk.get('angles') else '', f'{fk["quotes"]} short quotations with their credit lines' if fk.get('quotes') else '',
                     f'every figure with its scope ({fk["stat_facts"]})' if fk.get('stat_facts') else '',
                     f'the audience’s questions with Google’s answers ({fk["audience_questions"]})' if fk.get('audience_questions') else ''])
    intro = (f'<p class="mk-intro">Behind this page sits a complete kit for content teams{": " + e(held) if held else ""}. Each item is tied to its claims, '
             'labelled, and graded against Google’s documentation, so writers know what can be said as Google’s position and what was only said on stage.</p>')
    groups = [('Facts', [fact_card(f, K) for f in lib['facts']]), ('Myths', [myth_card(m, K) for m in lib['myths']]),
              ('Story angle' if len(lib['angles']) == 1 else 'Story angles', [angle_card(x, 'h4') for x in lib['angles']]),
              ('Quotes', [quote_card(q) for q in lib['quotes']])]
    taste = ''
    if any(cs for _, cs in groups):
        what = and_list([count_words(len(lib[k]), noun) for k, noun in (('facts', 'fact'), ('myths', 'myth'), ('angles', 'story angle'), ('quotes', 'quote')) if lib[k]])
        taste = (f'<section class="taste" aria-labelledby="taste">{sec("A small taste", "taste")}<p class="blurb">{e(what[:1].upper() + what[1:])} from the full kit, as it '
                 'presents them: the status, the claims behind each item and the credit line to use.</p>'
                 + ''.join(f'<h3 class="lab-h">{t} <span class="count">{len(cs)}</span></h3>{"".join(cs)}' for t, cs in groups if cs) + '</section>')
    note = reach('with-us', 'Want to create content from it, at scale?',
                 'We help companies turn this knowledge base into a content engine: briefs, articles, social posts and newsletters, generated with the wording rules, '
                 'credit lines and verification built in, reviewed for quality and written in your brand’s voice.', 'Get in touch:')
    gloss = (f'<p class="callout slim mk-gloss">The glossary stays open for everyone: <a href="{u("content/glossary.html")}">{plural(len(lib["glossary"]), "term")} in plain English</a>, '
             'each tied to the claims that explain it.</p>')
    rules = (f'<details class="kd mk-rules" id="wording-rules"><summary>The wording rules the kit follows · {len(lib["wording_rules"])}</summary><div class="kd-in"><ol>'
             + ''.join(f'<li>{inline(x)}</li>' for x in lib['wording_rules']) + '</ol></div></details>') if lib['wording_rules'] else ''
    main = f'<div class="wrap narrow mk">{intro}{taste}{note}{gloss}{rules}</div>'
    return page('content/index.html', 'Media kit', main, K, desc='The media kit is not part of this community edition: a small taste of it, and the glossary, which stays open.',
                head=('Content kit', 'Media kit', 'The full media kit is not part of this community edition.', ''), section='content/index.html', bot='wave')


def fact_card(f, K):
    return (f'<article class="kcard copyable" id="{e(f["id"])}" data-status="{f["status"]}" data-use="{f["use"]}"><div class="claim-head">{st_badge(f["status"])}'
            f'<span class="sp"></span><button class="copy" type="button" hidden>Copy</button><a class="cid" href="#{e(f["id"])}">{e(f["id"])}</a></div>'
            f'<p class="fact-t copy-src">{e(f["statement"])}</p>{topic_chips(f, K)}{kit_evidence(f["claims"])}</article>')


def myth_card(m, K):
    return (f'<article class="kcard" id="{e(m["id"])}" data-status="{m["status"]}"><div class="claim-head">{st_badge(m["status"])}<span class="sp"></span>'
            f'<a class="cid" href="#{e(m["id"])}">{e(m["id"])}</a></div><div class="mf"><div class="mf-myth"><p class="mf-k">Myth</p><p>{e(m["myth"])}</p></div>'
            f'<div class="mf-fact"><p class="mf-k">Fact</p><p>{e(m["fact"])}</p></div></div>{topic_chips(m, K)}{kit_evidence(m["claims"])}</article>')


def angle_card(x, h='h2'):
    """h: the level of the angle's title (h2 on the angles page, under the page title)."""
    pts = ''.join(f'<li><p>{e(p["text"])}</p><p class="pt-m">{st_badge(p["status"])} ' + ' '.join(cid_link(r['id']) for r in p['claims']) + '</p></li>' for p in x['points'])
    refs = list({r['id']: r for p in x['points'] for r in p['claims']}.values())
    return (f'<article class="kcard angle" id="{e(x["id"])}" data-formats="{" ".join(x["formats"])}"><div class="claim-head"><span class="fchips">'
            + ''.join(f'<span class="uchip">{FORMATS[f]}</span>' for f in x['formats']) + f'</span><span class="sp"></span><a class="cid" href="#{e(x["id"])}">{e(x["id"])}</a></div>'
            f'<{h} class="angle-t">{e(x["title"])}</{h}><p class="aud"><span class="k">For</span> {e(", ".join(x["audience"]))}</p>'
            f'<blockquote class="hook"><p>{e(x["hook"])}</p></blockquote><p class="kk">Points</p><ol class="points">{pts}</ol>'
            + (f'<div class="caution"><p class="kk">Caution</p><p>{e(x["caution"])}</p></div>' if x['caution'] else '')
            + f'<p class="cta"><span class="k">Call to action</span> {e(x["cta"])}</p>{kit_evidence(refs)}</article>')


def quote_card(q):
    line = f'“{q["quote"]}” — {q["credit"]}'
    return (f'<article class="kcard qcard copyable" id="{e(q["id"])}"><div class="claim-head">{badge_label(q["label"])}{badge_ver(q["verification"])}<span class="sp"></span>'
            f'<button class="copy" type="button" hidden>Copy with credit</button><a class="cid" href="#{e(q["id"])}">{e(q["id"])}</a></div>'
            f'<blockquote class="bigq"><p class="copy-src" data-copy="{e(line)}">“{e(q["quote"])}”</p></blockquote>'
            f'<p class="credit">{e(q["credit"])}' + (f' <span class="named"><span class="k">Speaker</span> {e(q["speaker"])}</span>' if q['speaker'] else '') + '</p>'
            f'<p class="q-meta">{cid_link(q["claim"])} · ' + ('<span class="q-ok">Wording checked against the slide or recording</span>' if q['quote_checked'] else 'Wording not yet checked against the slide or recording')
            + f'</p><p class="q-ctx"><span class="k">Context</span> {e(q["text"])}</p>'
            + (f'<ul class="srcs">{"".join(source_li(x) for x in q["sources"])}</ul>' if q['sources'] else '') + '</article>')


def facts_page(K):
    at('content/facts.html')
    facts = K['lib']['facts']
    filt = kit_filter('.kcard', 'fact', [('status', 'Status', [(k, st_badge(k)) for k in ('documented', 'event-only')]),
                                         ('use', 'Use', [(k, f'<span class="uchip">{v}</span>') for k, v in USES.items() if any(f['use'] == k for f in facts)])])
    body = ''
    for k, title in USES.items():
        g = [f for f in facts if f['use'] == k]
        if not g: continue
        cards = ''.join(fact_card(f, K) for f in g)
        body += f'<section data-group aria-labelledby="u-{k}">{sec(title, "u-" + k, len(g))}{cards}</section>'
    return content_sub(K, 'facts', f'<div class="wrap narrow">{filt}{body}</div>',
                       f'{plural(len(facts), "fact")}. Documented facts can be written as Google’s position; the others as said at Search Central Live.')


def myths_page(K):
    at('content/myths.html')
    ms = K['lib']['myths']
    filt = kit_filter('.kcard', 'myth', [('status', 'Status', [(k, st_badge(k)) for k in ('documented', 'event-only')])])
    cards = ''.join(myth_card(m, K) for m in ms)
    return content_sub(K, 'myths', f'<div class="wrap narrow">{filt}<div data-group>{cards}</div></div>', f'{plural(len(ms), "myth")} heard in the industry, each with the fact that answers it.')


def angles_page(K):
    at('content/angles.html')
    an = K['lib']['angles']
    filt = kit_filter('.kcard', 'angle', [('formats', 'Format', [(f, f'<span class="uchip">{v}</span>') for f, v in FORMATS.items() if any(f in x['formats'] for x in an)])])
    cards = ''.join(angle_card(x) for x in an)
    return content_sub(K, 'angles', f'<div class="wrap narrow">{filt}<div data-group>{cards}</div></div>',
                       f'{plural(len(an), "angle")} that can become a post, an article, a newsletter, a video or a talk. Follow the caution where there is one.')


def quotes_page(K):
    at('content/quotes.html')
    qs = K['lib']['quotes']
    cards = ''.join(quote_card(q) for q in qs)
    return content_sub(K, 'quotes', f'<div class="wrap narrow">{cards}</div>', f'{plural(len(qs), "quotation")} of 25 words or fewer. Quote them exactly, with the credit line given.')


def glossary_page(K):
    at('content/glossary.html')
    gl = K['lib']['glossary']
    first = lambda t: t['term'][:1].upper() if t['term'][:1].isalpha() else '#'
    letters = list(dict.fromkeys(first(t) for t in gl))
    jump = '<nav class="jump" aria-label="Letters"><ul>' + ''.join(f'<li><a href="#l-{ord(x)}">{e(x)}</a></li>' for x in letters) + '</ul></nav>'
    body = ''
    for x in letters:
        body += (f'<section aria-labelledby="l-{ord(x)}">{sec(x, f"l-{ord(x)}")}<dl class="gloss">' + ''.join(
            f'<div class="g-row" id="term-{e(t["id"])}"><dt>{e(t["term"])}</dt><dd><p>{e(t["definition"])}</p><p class="g-cites">' + ' '.join(cid_link(r['id']) for r in t['claims']) + '</p>'
            + (f'<p class="g-ent"><span class="k">{"Things" if len(t["defines"]) > 1 else "Thing"}</span>' + ' '.join(ent_link(k, K) for k in t['defines']) + '</p>' if t['defines'] else '') + '</dd></div>'
            for t in gl if first(t) == x) + '</dl></section>')
    return content_sub(K, 'glossary', f'<div class="wrap narrow">{jump}{body}</div>', f'{plural(len(gl), "term")} in plain English, each tied to the claims that explain it.')


# ------------------------------------------------------------------ the ledgers (knowledge graph phase 3, v2.11.0)
# Three pages from the agent pack's numbers.json, differences.json and question-bank.json (written by _system/kits.py from 25-kits/ and
# the claims): the differences ledger in the developer kit, the numbers registry and the question bank in the content kit.
LEDGER_DL = [('differences.json', 'Differences ledger (JSON)', 'Every row with its claims and citations'),
             ('numbers.json', 'Numbers registry (JSON)', 'Every stat fact with its figures and claims'),
             ('question-bank.json', 'Question bank (JSON)', 'Questions and answers, with a citation per claim')]


def ref_list(refs, cls='ev-list'):
    """Kit claim records as a list: label, grade, ID (to its card on All claims), text, credit line."""
    li = ''.join(f'<li><div class="ev-head">{badge_label(r["label"])}{badge_ver(r["verification"])}<span class="sp"></span>{cid_link(r["id"])}</div>'
                 f'<p>{e(r["text"])}</p><p class="ev-by">{e(r["credit"])}</p></li>' for r in refs)
    return f'<ul class="{cls}">{li}</ul>' if li else ''


def thing_chips(ents, K, top=8, label='Things'):
    xs = [x for x in ents if x['id'] in K['ents']][:top]
    return (f'<div class="ents"><span class="k">{e(label)}</span><ul class="ent-chips" aria-label="{e(label)}">' + ''.join(f'<li>{ent_link(x["id"], K)}</li>' for x in xs)
            + '</ul></div>') if xs else ''


def figs(fs, cls='figs'):
    return f'<p class="{cls}">' + (''.join(f'<span class="fig">{e(f)}</span>' for f in fs) or '<span class="fig in-words">In words</span>') + '</p>'


def ledger_links(K):
    """For the things' cards: thing id -> the differences rows that name it, and the things the question bank asks about (none in
    the community edition, which has no question bank)."""
    rows = {}
    for r in K['difs']['rows']:
        for x in r['entities']: rows.setdefault(x['id'], []).append(r['id'])
    return rows, {t['id'] for t in K['qbank']['things']} if K['qbank'] else set()


def differences_page(K, dls):
    at('dev/differences.html')
    D = K['difs']
    rows = D['rows']
    st = stats([('Differences', len(rows)), ('Event claims', sum(len(r['event']) for r in rows)), ('Docs claims and pages', sum(len(r['docs']) + len(r['pages']) for r in rows)),
                ('Linked pairs', len(D['pairs'])), ('Say they are uncertain', len(D['hedged']))])
    rule = (f'<div class="callout"><p class="callout-k">The rule</p><p>{e(D["rule"])}</p><p>Media kit wording rule 13. A requirement rests on what Google documents: '
            'read the row before you build on what was said on stage.</p></div>') if D['rule'] else ''
    how = ('<div class="callout slim"><p class="callout-k">How to read a row</p><ul><li><strong>What to follow</strong> is the author’s guidance, written from the claims below it.</li>'
           '<li><strong>At the event</strong>: what was shown on a slide or said on stage. <strong>Google’s documentation</strong>: the docs claims and the Google pages.</li>'
           '<li><strong>The author’s analysis</strong> explains the gap. It is the author’s view, never Google’s.</li><li>Cite the claim IDs, not the row.</li></ul></div>')
    glance = ''
    if rows:
        glance = ('<div class="table-wrap glance"><table><caption>At a glance</caption><thead><tr><th scope="col">Row</th><th scope="col">Difference</th>'
                  '<th scope="col">What to follow</th></tr></thead><tbody>'
                  + ''.join(f'<tr><th scope="row"><a href="#{e(r["id"])}">{e(r["id"])}</a></th><td class="g-title">{e(r["title"])}</td><td>{e(r["follow"])}</td></tr>' for r in rows)
                  + '</tbody></table></div>')
    cards = ''
    for r in rows:
        pages = ''.join(source_li(dict(p, kind='google')) for p in r['pages'])
        docs = ref_list(r['docs']) + (f'<p class="kk vs-pages">Google pages</p><ul class="srcs">{pages}</ul>' if pages else '')
        topics = ('<ul class="chips small kit-topics" aria-label="Topics">' + ''.join(f'<li><a href="{u("topics/" + t + ".html")}">{e(K["topics"][t]["title"])}</a></li>'
                                                                               for t in r['topics'][:4]) + '</ul>') if r['topics'] else ''
        cards += (f'<article class="kcard dif" id="{e(r["id"])}"><div class="claim-head"><span class="uchip">Event and docs differ</span><span class="sp"></span>'
                  f'<a class="cid" href="#{e(r["id"])}">{e(r["id"])}</a></div><h3 class="dif-t">{e(r["title"])}</h3>'
                  f'<div class="follow"><p class="kk">What to follow</p><p>{e(r["follow"])}</p></div>'
                  f'<div class="vs"><div class="vs-ev"><p class="mf-k">At the event</p>{ref_list(r["event"])}</div>'
                  f'<div class="vs-doc"><p class="mf-k">Google’s documentation</p>{docs}</div></div>'
                  + (f'<details class="kd"><summary>The author’s analysis · {plural(len(r["analysis"]), "claim")}</summary><div class="kd-in">{ref_list(r["analysis"])}</div></details>'
                     if r['analysis'] else '')
                  + f'{thing_chips(r["entities"], K)}{topics}</article>')
    covered = [f'<a href="#{e(x)}">{e(x)}</a> covers {cid_link(p["from"]["id"])} {p["type"]} {cid_link(p["to"]["id"])}' for p in D['pairs'] for x in p['rows']]
    prs = (f'<section aria-labelledby="pairs">{sec("Claims linked as contradicting or updating", "pairs", len(D["pairs"]))}'
           '<p class="blurb">Set with a relation on the later claim. A pair that no row covers is usually two views at the event (Google and a community speaker, or two talks) '
           'or a later page of Google’s documentation, not a difference between the event and the documentation.'
           + (f' {"; ".join(covered)}.' if covered else '') + f'</p>{pairs([(p["from"]["id"], p["type"], p["to"]["id"]) for p in D["pairs"]], K)}</section>') if D['pairs'] else ''
    hedged = ''
    if D['hedged']:
        hedged = (f'<section aria-labelledby="hedged">{sec("Claims that say they are uncertain", "hedged", len(D["hedged"]))}'
                  '<p class="blurb">Their text states the uncertainty: an unclear recording, an uncertain word, a best reading. Keep the hedge in your wording or leave the point out '
                  '(media kit wording rule 10).</p>')
        for d in sorted({c['day'] for c in D['hedged']}):
            g = [c for c in D['hedged'] if c['day'] == d]
            hedged += f'<h3 class="lab-h">Day {d} <span class="count">{len(g)}</span></h3>' + ''.join(claim_row(K['byid'][c['id']], K, None) for c in g)
        hedged += '</section>'
    body = (f'<section aria-labelledby="rows">{sec("The differences", "rows", len(rows))}{cards}</section>' if rows
            else empty_note('peek', '<p class="empty">No differences have been written yet: add rows to <code>25-kits/differences.yaml</code>.</p>'))
    downloads = f'<section aria-labelledby="dl">{sec("Take it with you", "dl")}{dl_list(dls)}</section>' if dls else ''
    main = f'<div class="wrap">{st}<div class="two">{rule}{how}</div>{glance}{body}{prs}{hedged}{downloads}{dev_reach_line()}</div>'
    lead = (f'{plural(len(rows), "place")} where what was shown or said at {K["short"]} differs from Google’s documentation, and what to follow. '
            'Each row puts the event’s version next to the documented one, with the claims behind both.')
    return page('dev/differences.html', 'Differences ledger', main, K, desc='Where the event and Google’s documentation differ, and what to follow.',
                crumbs=(('dev/index.html', 'For developers'),), head=('Developer kit', 'Differences ledger', e(lead), ''), section='dev/index.html')


def numbers_page(K, dls):
    at('content/numbers.html')
    N = K['nums']
    fs, cand = N['facts'], N['candidates']
    sc = Counter(f['status'] for f in fs)
    st = stats([('Stat facts', len(fs)), (KSTATUS['documented'][0], sc['documented']), ('Said at the event', sc['event-only']), ('Figures no fact cites', len(cand))])
    rule = (f'<div class="callout"><p class="callout-k">The rule</p><p>{e(N["rule"])}</p><p>Media kit wording rule 9.</p></div>') if N['rule'] else ''
    how = ('<div class="callout slim"><p class="callout-k">How to use a figure</p><ul><li>Quote the whole wording, never the figure alone: it keeps the market, the period, '
           'the basis and the comparison.</li><li>Use the credit line given. Documented figures can be written as Google’s; the others as said at Search Central Live.</li>'
           '<li>The figures are read from the wording by the build; a figure written in words (doubled, one in six) shows as <em>In words</em>.</li></ul></div>')
    filt = kit_filter('.kcard', 'figure', [('status', 'Status', [(k, st_badge(k)) for k in ('documented', 'event-only') if sc[k]])])
    cards = ''.join(f'<article class="kcard copyable num" id="{e(f["id"])}" data-status="{f["status"]}"><div class="claim-head">{st_badge(f["status"])}<span class="sp"></span>'
                    f'<button class="copy" type="button" hidden>Copy</button><a class="cid" href="{u("content/facts.html#" + f["id"])}">{e(f["id"])}</a></div>'
                    f'{figs(f["figures"])}<p class="fact-t copy-src">{e(f["statement"])}</p>'
                    f'<p class="credit-ln"><span class="k">Credit</span> {e("; ".join(f["credit"]))}</p>{thing_chips(f["entities"], K)}{topic_chips(f, K)}{kit_evidence(f["claims"])}</article>'
                    for f in fs)
    cl = ''
    for d in sorted({c['day'] for c in cand}):
        g = [c for c in cand if c['day'] == d]
        cl += (f'<h3 class="lab-h">Day {d} <span class="count">{len(g)}</span></h3><ul class="ev-list cand-list">'
               + ''.join(f'<li><div class="ev-head">{badge_label(c["label"])}{badge_ver(c["verification"])}<span class="sp"></span>{cid_link(c["id"])}</div>'
                         f'{figs(c["figures"], "figs sm")}<p>{e(c["text"])}</p><p class="ev-by">{e(c["credit"])}</p></li>' for c in g) + '</ul>')
    cands = (f'<section aria-labelledby="cand">{sec("Figures no stat fact cites yet", "cand", len(cand))}<p class="blurb">Slide, stage, documentation and press claims that state a figure '
             'and that no stat fact cites: candidates for the kit. When one is worth quoting, add a fact with <code>use: stat</code> to <code>25-kits/content.yaml</code>, with its scope. '
             f'Audience questions and analysis claims are left out.</p><div class="cand-box">{cl}</div></section>') if cand else ''
    downloads = f'<section aria-labelledby="dl">{sec("For AI content tools", "dl")}{dl_list(dls)}</section>' if dls else ''
    body = (f'<section aria-labelledby="reg">{sec("The registry", "reg", len(fs))}{filt}<div data-group>{cards}</div></section>' if fs
            else empty_note('peek', '<p class="empty">No fact is marked <code>use: stat</code> yet.</p>'))
    main = f'<div class="wrap narrow">{st}{rule}{how}{body}{cands}{downloads}</div>'
    return content_sub(K, 'numbers', main, f'{plural(len(fs), "stat fact")}: every figure of the media kit with its scope, status, credit and the claims behind it.')


def questions_page(K, dls):
    at('content/questions.html')
    Q = K['qbank']
    aq, th = Q['audience'], Q['things']
    shown = {c['id'] for q in aq for c in q['answers']} | {c['id'] for t in th for k in ('documented', 'event_only') for c in t[k]['top']}
    st = stats([('Audience questions', len(aq)), ('Answered', sum(1 for q in aq if q['answers'])), ('Things asked about', len(th)), ('Claims in the answers', len(shown))])
    rules = ('<div class="callout"><p class="callout-k">Before you publish</p><ul>' + ''.join(f'<li>{e(x)}</li>' for x in Q['rules'] if x)
             + '<li>Keep the claim IDs in drafts and use the credit lines of the content kit in the published text.</li></ul></div>')
    jump = ('<nav class="jump qb-jump" aria-label="Sections"><ul><li><a href="#aud">Audience questions</a></li><li><a href="#things">What did Google say about it?</a></li></ul></nav>')
    aud = ''
    for d in sorted({q['question']['day'] for q in aq}):
        g = [q for q in aq if q['question']['day'] == d]
        aud += f'<h3 class="lab-h">Day {d} <span class="count">{len(g)}</span></h3>'
        for q in g:
            c, s = q['question'], K['sess'][q['question']['session_id']]
            grade = st_badge(q['grade']) if q['grade'] else f'<span class="badge-none">{e(q["grade_label"])}</span>'
            ans = ref_list(q['answers']) if q['answers'] else '<p class="blurb">No answer was recorded.</p>'
            aud += (f'<article class="kcard qb" id="q-{e(c["id"])}" data-status="{q["grade"] or "none"}"><div class="claim-head">{grade}<span class="sp"></span>{cid_link(c["id"])}</div>'
                    f'<div class="qb-q"><span class="qb-m" aria-hidden="true">Q</span><div><p class="qb-t">{e(c["text"])}</p>'
                    f'<p class="ev-by"><a href="{u(session_url(s))}">Day {s["day"]} · {e(stitle(s))}</a></p></div></div>'
                    f'<div class="qb-a"><span class="qb-m" aria-hidden="true">A</span><div>{ans}</div></div>{thing_chips(q["entities"], K, 6)}</article>')
    kinds = [k for k in ENT_KINDS if any(t['kind'] == k for t in th)]
    filt = kit_filter('.qt', 'thing', [('kind', 'Kind', [(k, ent_kind(k)) for k in kinds])]) if th else ''
    tc = ''
    for t in th:
        dn, en = t['documented'], t['event_only']
        inner = ((f'<p class="mf-k vs-k">Documented · {dn["count"]}</p>{ref_list(dn["top"])}' if dn['top'] else '')
                 + (f'<p class="mf-k vs-k ev">Said at the event only · {en["count"]}</p>{ref_list(en["top"])}' if en['top'] else ''))
        tc += (f'<li class="qt kcard ek-{t["kind"]}" id="t-{e(t["id"])}" data-kind="{t["kind"]}"><div class="claim-head">{ent_kind(t["kind"])}<span class="sp"></span>'
               f'<span class="qt-n">{plural(t["claims"], "claim")}</span></div><h3 class="qt-t"><a href="{u(ent_url(t["id"]))}">{e(t["question"])}</a></h3>'
               f'<p class="qt-c">{dn["count"]} documented · {en["count"]} said at the event only</p>'
               f'<details class="kd"><summary>Google’s answers</summary><div class="kd-in">{inner}</div></details></li>')
    things = (f'<section aria-labelledby="things">{sec("What did Google say about it?", "things", len(th))}<p class="blurb">For each thing the event talked about: up to three claims '
              'that Google’s documentation backs and up to three said only at the event, in Google’s words only (community speakers and audience questions are left out), '
              f'the claims the kits rest on first. The card holds everything else.</p>{filt}<ul class="qt-grid" data-group>{tc}</ul></section>') if th else ''
    downloads = f'<section aria-labelledby="dl">{sec("For AI tools and agents", "dl")}{dl_list(dls)}</section>' if dls else ''
    none = empty_note('peek', '<p class="empty">No audience question has been recorded yet.</p>')
    grades = ('<div class="callout slim"><p class="callout-k">How far the documentation backs an answer</p><ul class="kit-legend">'
              + ''.join(f'<li>{st_badge(k)} {e(KSTATUS[k][1])}</li>' for k in ('documented', 'event-only'))
              + '<li><span class="badge-none">No answer recorded</span> The recordings hold the question but not an answer: never guess one.</li></ul></div>')
    main = (f'<div class="wrap">{st}<div class="two">{rules}{grades}</div>{jump}<section aria-labelledby="aud">{sec("Audience questions", "aud", len(aq))}'
            '<p class="blurb">What people in the room asked, with the answers given. A question is a question, not Google’s position: only the answer can be credited to Google.</p>'
            f'{aud or none}</section>{things}{downloads}</div>')
    return content_sub(K, 'questions', main, f'{plural(len(aq), "audience question")} with the answers given, and what Google said about each of {plural(len(th), "thing")}: '
                       'ready for a Q&A post, an FAQ or an AI agent.')


def standalone_md(t):
    """A repository Markdown page as a plain download: without its images and divider lines, and with relative links turned into
    their text (they would not resolve from downloads/); web links stay."""
    t = re.sub(r'^<p align="center"><img [^>]*></p>\n\n?', '', t, flags=re.M)
    t = re.sub(r'<img [^>]*>\s?', '', t)
    t = re.sub(r'<a href="(?![a-z]+:)[^"]*">(.*?)</a>', r'\1', t)
    t = re.sub(r'\[([^\]]+)\]\((?![a-z]+:)[^)\s]+\)', r'\1', t)
    return t


LOADS = re.compile(r'''<(script|link|img|iframe|source)\b[^>]*\b(src|href)\s*=\s*["']?(https?:)?//''')


CANON = re.compile(r'<link rel="canonical" href="([^"]*)">')
SOCIAL = re.compile(r'<meta (?:property="og:[a-z:_]+"|name="twitter:[a-z:_]+") content="(https?://[^"]*)">')
LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def own_ok(url):
    """An address the edition may link with class "ext own": contact, Impressum, Privacy, the repository (any file in it) or a
    page of the published site. None in the full edition."""
    if not community(): return False
    exact = {ed_url(k) for k in ('contact_url', 'impressum_url', 'privacy_url', 'repo_url')} - {''}
    return url in exact or bool(ed_url('repo_url') and url.startswith(ed_url('repo_url') + '/')) or bool(site_url() and url.startswith(site_url()))


def offline_guard(files):
    """The site works offline: no page and no style sheet loads anything from the web (the links to Google's pages and the press,
    class "ext", are links, not loads; a canonical link to the published site names the page, it loads nothing). The edition's own
    links go to the addresses of edition.yaml and nowhere else: class "contact" to the company and LinkedIn, class "own" to the
    repository, contact, Impressum, Privacy or the published site; canonical, Open Graph and Twitter addresses lie under site_url,
    the JSON-LD names only those, the company, LinkedIn and the schema.org context, and only 404.html has a <base> (site_url;
    that page is a page of the published site only). The full edition has none of them."""
    su = site_url()
    canon_ok = lambda h: bool(su) and html.unescape(h).startswith(su)
    loads = [p for p, t in files.items() if p.endswith('.html') and LOADS.search(CANON.sub(lambda m: '' if canon_ok(m[1]) else m[0], t))]
    loads += [p for p in ('assets/site.css',) if re.search(r'''@import|url\(\s*["']?(https?:)?//''', files[p])]
    if loads: sys.exit(f'ERROR: {", ".join(sorted(loads))} load external resources: site not built')
    allowed = {x for x in (ED['company']['url'], ED['linkedin']) if x} if community() else set()
    pages = [(p, t) for p, t in files.items() if p.endswith('.html')]
    wrong = sorted({f'{p} ({html.unescape(h)})' for p, t in pages
                    for h in re.findall(r'<a class="ext contact" href="([^"]*)"', t) if html.unescape(h) not in allowed})
    if wrong: sys.exit(f'ERROR: a contact link that is not one of the two of _system/edition.yaml: {", ".join(wrong[:5])}: site not built')
    wrong = ({f'{p} ({html.unescape(h)})' for p, t in pages for h in re.findall(r'<a class="ext own" href="([^"]*)"', t) if not own_ok(html.unescape(h))}
             | {f'{p} (canonical {h})' for p, t in pages for h in CANON.findall(t) if not canon_ok(h)}
             | {f'{p} ({h})' for p, t in pages for h in SOCIAL.findall(t) if not canon_ok(h)})
    ld_ok = (allowed | {SCHEMA_ORG}) if su else set()
    def urls(v):  # every string of a JSON value
        if isinstance(v, dict): return [x for y in v.values() for x in urls(y)]
        if isinstance(v, list): return [x for y in v for x in urls(y)]
        return [v] if isinstance(v, str) else []
    for p, t in pages:
        for block in LD.findall(t):
            try: data = json.loads(block)
            except ValueError as x: sys.exit(f'ERROR: {p}: its JSON-LD does not parse ({x}): site not built')
            wrong |= {f'{p} (JSON-LD {v})' for v in urls(data) if re.match(r'https?://', v) and not (v in ld_ok or canon_ok(v))}
            if not su: wrong.add(f'{p} (JSON-LD without site_url)')
    base_ok = base_tag() if su else None
    for p, t in pages:
        n = t.count("createElement('base')") + len(re.findall(r'<base\b', t))
        if n and not (p == '404.html' and n == 1 and base_ok and base_ok in t): wrong.add(f'{p} (a <base> that is not site_url on 404.html)')
    if wrong: sys.exit(f'ERROR: a web address that is not in _system/edition.yaml: {", ".join(sorted(wrong)[:5])}: site not built')


# ------------------------------------------------------------------ main
def main():
    global STYLE, ED
    STYLE = default_style()
    ED = edition_settings()
    K = load()
    K['ledger_links'] = ledger_links(K)
    pdf_dir, mm = ROOT / '60-outputs' / 'pdf', ROOT / '50-maps' / 'mindmap.html'
    log = pdf_dir / CLASSIC_LOG
    log = log if log.exists() else None
    pdfs = []
    def pdf_key(p):  # by day, the default edition first
        m = re.fullmatch(r'day(\d+)-field-guide-(.+)', p.stem)
        return (int(m.group(1)), m.group(2) != STYLE, m.group(2)) if m else (1 << 30, False, p.stem)
    for p in sorted(pdf_dir.glob('*.pdf'), key=pdf_key) if pdf_dir.exists() else []:
        m = re.fullmatch(r'day(\d+)-field-guide-(.+)', p.stem)
        name = f'Day {m.group(1)} field guide · {m.group(2).replace("-", " ").title()}' if m else p.stem.replace('-', ' ').capitalize()
        if m and m.group(2) in CLASSIC_STYLES: name += f' ({CLASSIC_NOTE})'
        size = p.stat().st_size
        pdfs.append((p, name, f'{size / 1048576:.1f} MB' if size >= 1048576 else f'{max(1, round(size / 1024))} KB'))
    files = {'index.html': index_page(K, pdfs, mm.exists(), log), 'topics.html': topics_index(K, mm.exists()), 'verification.html': verification_page(K),
             'across-days.html': across_page(K), 'sources.html': sources_page(K), 'claims.html': claims_page(K), 'search.html': search_page(K),
             'about.html': about_page(K), 'assets/search-data.js': search_data(K), 'entities.html': entities_index(K)}
    files.update({ent_url(k): entity_page(k, K) for k in sorted(K['ents'])})
    for d in K['days']:
        files[f'days/day-{d["day"]}.html'] = day_page(d, K)
        for s in d['sessions']:
            if has_page(s): files[f'sessions/{s["id"]}.html'] = session_page(s, K)
    for a in K['areas']:
        files[f'areas/{a["id"]}.html'] = area_page(a, K)
        for t in a['topics']: files[f'topics/{t["id"]}.html'] = topic_page(K['topics'][t['id']], K)
    kit_dl = [(PACK / 'dev-requirements.json', 'Developer kit (JSON)', 'For scripts and AI agents'), (PACK / 'content-library.json', 'Content library (JSON)', 'For AI content tools')]
    csv_p = ROOT / '60-outputs' / 'dev' / 'requirements.csv'
    if csv_p.exists(): kit_dl.insert(0, (csv_p, 'Requirements (CSV)', 'For Jira, Linear, GitHub Issues'))
    kit_dl += [(PACK / n, t, m) for n, t, m in LEDGER_DL]
    if community():  # no media kit files in the community edition's downloads (the agent pack keeps its reduced content library)
        kit_dl = [x for x in kit_dl if x[0].name not in ('content-library.json', 'numbers.json', 'question-bank.json')]
    copies = {f'downloads/{p.name}': p for p, _, _ in kit_dl}
    if log and pdfs: files[f'downloads/{log.name}'] = standalone_md(log.read_text(encoding='utf-8'))
    dl = lambda names: [(f'downloads/{p.name}', t, m) for p, t, m in kit_dl if p.name in names]
    files.update({'dev/index.html': dev_page(K, dl(('requirements.csv', 'dev-requirements.json', 'differences.json'))), 'dev/checklist.html': checklist_page(K),
                  'dev/snippets.html': snippets_page(K), 'dev/differences.html': differences_page(K, dl(('differences.json',))),
                  'content/index.html': content_page(K, dl(('content-library.json', 'numbers.json', 'question-bank.json')))})
    if not community():  # the media kit's pages: the full edition only
        files.update({'content/facts.html': facts_page(K), 'content/myths.html': myths_page(K), 'content/angles.html': angles_page(K), 'content/quotes.html': quotes_page(K)})
    files['content/glossary.html'] = glossary_page(K)
    if not community():
        files.update({'content/numbers.html': numbers_page(K, dl(('numbers.json',))), 'content/questions.html': questions_page(K, dl(('question-bank.json',)))})
    # the community edition: the method write-up; published (site_url): 404.html and, below, sitemap.xml
    binaries = {}  # site path -> a file copied byte for byte (the tour video and its poster, the share image)
    if community():
        files['method.html'] = method_page(K)
        if not method_doc()['found']: print(f'WARNING: {METHOD_MD.name} not found: method.html is a short placeholder', file=sys.stderr)
        if tour_ok(): binaries.update(TOUR)
        else: print('WARNING: _system/brand/video/tour.mp4 or tour-poster.jpg not found: the home page has no tour', file=sys.stderr)
    if site_url():
        files['404.html'] = not_found_page(K)
        if og_image(): binaries[og_image()[0]] = og_image()[1]
        else: print(f'WARNING: {OG_IMAGE[1].relative_to(ROOT).as_posix()} not found: the social previews have no image', file=sys.stderr)
    for n in ('site.css', 'site.js'): files[f'assets/{n}'] = edition_blocks((HERE / n).read_text(encoding='utf-8'))
    files['assets/icon.svg'] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="4" fill="#1a1712"/>'
                                + fan().replace('class="fan" viewBox="0 0 40 21" aria-hidden="true" focusable="false"', 'x="3" y="9" width="34" height="18" viewBox="0 0 40 21"')
                                .replace('currentColor', '#b08d3a').replace('stroke-width="1.1"', 'stroke-width="2.4"') + '</svg>\n')
    files['assets/icon-deep-dive.svg'] = dd_icon()
    files.update({f'assets/ocean/{k}': v for k, v in ocean_assets().items()})
    files['assets/graph-data.js'] = graph_data(K)
    files['graph.html'], maps_graph = graph_pages(files['assets/graph-data.js'])
    mind = mm.read_text(encoding='utf-8') if mm.exists() else None
    bad = re.compile(r'(?<![A-Za-z0-9])(' + '|'.join(EXCLUDED) + r')(?!\d)', re.I)
    leaks = [p for p, t in list(files.items()) + [('mindmap.html', mind or ''), ('50-maps/graph.html', maps_graph)] + [(k, v.read_text(encoding='utf-8')) for k, v in copies.items()] if bad.search(t)]
    if leaks: sys.exit(f'ERROR: an excluded photo ({", ".join(EXCLUDED)}) is referenced in {", ".join(leaks)}: site not built')
    if mind and re.search(r'''<(script|link|img|iframe|source)\b[^>]*\b(src|href)\s*=\s*["']?(https?:)?//|@import|url\(\s*["']?(https?:)?//''', mind):
        sys.exit('ERROR: 50-maps/mindmap.html loads external resources: site not built')
    if re.search(r'''<(script|link|img|iframe|source)\b[^>]*\b(src|href)\s*=\s*["']?(https?:)?//|@import|url\(\s*["']?(https?:)?//|\bfetch\(|\bimport\(''', files['graph.html']):
        sys.exit(f'ERROR: {GRAPH_TPL.relative_to(ROOT)} loads external resources or fetches: site not built')
    if site_url():  # the published community edition: the two maps name their address and share like every page (50-maps/ keeps its copies as they are)
        files['graph.html'] = map_seo(files['graph.html'], 'graph.html', K)
        if mind: mind = map_seo(mind, 'mindmap.html', K)
    offline_guard({**files, 'mindmap.html': mind} if mind else files)
    if site_url(): files['sitemap.xml'] = sitemap_xml(list(files) + (['mindmap.html'] if mind else []), K)
    if OUT.exists(): shutil.rmtree(OUT)
    for p, t in files.items():
        f = OUT / p
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, 'w', encoding='utf-8', newline='\n') as fh: fh.write(t)
    if mind:
        with open(OUT / 'mindmap.html', 'w', encoding='utf-8', newline='\n') as fh: fh.write(mind)
    (ROOT / '50-maps').mkdir(exist_ok=True)  # the Reef map next to the mindmap, with its data inline
    with open(ROOT / '50-maps' / 'graph.html', 'w', encoding='utf-8', newline='\n') as fh: fh.write(maps_graph)
    shutil.copytree(HERE / 'fonts', OUT / 'assets' / 'fonts')
    for p in [p for p, _, _ in pdfs] + list(copies.values()):  # the site links its own copies, so the folder works when it is shared alone
        (OUT / 'downloads').mkdir(exist_ok=True)
        shutil.copyfile(p, OUT / 'downloads' / p.name)
    for dst, src in binaries.items():
        (OUT / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, OUT / dst)
    print(f'OK: site {K["version"]} -> {OUT.relative_to(ROOT)} ({len(files) + bool(mind) + len(pdfs) + len(copies) + len(binaries)} files, {len(K["claims"])} claims, {len(K["topics"])} topics, '
          f'{sum(has_page(s) for s in K["sess"].values())} session pages, {len(dev_reqs(K))} requirements, '
          + (f'community edition: a preview of {plural(sum(len(K["lib"][k]) for k in MEDIA), "media kit item")})' if community() else f'{len(K["lib"]["facts"])} facts)'))


if __name__ == '__main__':
    main()
