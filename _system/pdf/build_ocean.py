"""The Deep Dive edition of a day's field guide: an original underwater look inspired by the event (see _system/ocean_art.py).

Steps: swap the stylesheet for ocean.css, replace the cover with a full-bleed underwater cover, put a glossy number bubble in
every section head, recolour the modern palette of the SVG figures and inline colours to the ocean palette (stopping on a
colour it cannot map), paginate, then lay every content page over an underlay page rendered by Chromium: the water, the
white card behind the text, the seabed and footer band, the running header (with the current section's title) and footer.
"""
import html as htmllib, math, random, re, shutil, sys
from html import escape
from pathlib import Path
import pdfplumber
from pypdf import PdfReader, PdfWriter
from common import BUILD, OUT, HERE, BuildError, config, day_data, paginate, check_fonts, find_pages, render

sys.path.insert(0, str(HERE.parent))
import ocean_art as art  # noqa: E402
from ocean_art import PALETTE as P, fmt  # noqa: E402

SYM = "'Noto Symbols'"
e = lambda v: escape(str(v), quote=False)

# ---------------------------------------------------------------- fonts (the underlay page uses the same files as ocean.css)
_RANGES = {
    'latin': 'U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, '
             'U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD',
    'ext': 'U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, '
           'U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF',
}


def font_faces(prefix='fonts/'):
    out = []
    for w in (400, 500, 600, 700, 800):
        for sub, r in (('latin', 'latin'), ('latin-ext', 'ext')):
            out.append(f"@font-face {{ font-family: 'Figtree'; font-weight: {w}; src: url('{prefix}figtree-{sub}-{w}-normal.woff2') "
                       f"format('woff2'); unicode-range: {_RANGES[r]}; }}")
    return '\n'.join(out)


# ---------------------------------------------------------------- cover
COVER = '''<div class="cover">
  <div class="art">{scene}</div>
  <div class="deep"></div>
  <div class="inner">
    <div class="eyebrow">Search Central Live &nbsp;·&nbsp; Deep Dive Europe 2026</div>
    <div class="ed">{ed}</div>
    <div class="t1">{t1}</div>
    <div class="t2">{t2}</div>
    <div class="t3">{t3}</div>
    <div class="sub">{sub}</div>
  </div>
  <div class="meta">
    <div class="k">Notes &amp; guide by</div>
    <div class="name">{author}</div>
    <div class="v">{date}</div>
    <div class="ind">Deep Dive edition &nbsp;·&nbsp; an independent attendee guide</div>
  </div>
</div>
'''
COVER_BAND = '#0c1a3f'      # the deep footer band of the cover; it continues in the .deep block below the art

# Per-day cover: scene seed, whether the reef corners are mirrored, the fish (x, y as fractions of the art, heading right?)
# and the diver bot (pose, centre x, y and size in px on the 794 x 1006 art, i.e. 210 x 266 mm at 96 dpi; y None = seated on
# the near hill). Day 1 swims down the title's diagonal towards the reef; Day 2 sits on the seabed beside the anemone,
# reading the field guide; Day 3 stands on the seabed, pointing at the reef. A day without an entry uses the Day 1 layout.
COVERS = {
    '1': dict(seed=4, mirror=False, school=(0.8, 0.49, False), yellow=(0.22, 0.585, True), red=(0.36, 0.675, True),
              bot=('swim', 520, 668, 268)),
    '2': dict(seed=11, mirror=True, school=(0.6, 0.535, False), yellow=(0.8, 0.645, False), red=(0.2, 0.6, True),
              bot=('read', 345, None, 236)),
    '3': dict(seed=7, mirror=False, school=(0.3, 0.5, True), yellow=(0.66, 0.6, False), red=(0.5, 0.69, False),
              bot=('point', 455, None, 250)),
}
COVER_W, COVER_H = 794, 1006


def cover_scene(dayn):
    """Night-water scene for the top of the cover (210 x 266 mm), composed from ocean_art's pieces so each day gets its own
    layout: water with a soft sun glow and rays, a calm distant school, the seabed, an organic band whose top edge the reef
    overlaps, two reef fish and the diver bot. Deterministic per day."""
    lay = COVERS.get(str(dayn), COVERS['1'])
    W, H, seed, mir = COVER_W, COVER_H, lay['seed'], lay['mirror']
    X = (lambda x: W - x) if mir else (lambda x: x)
    u = W / 1000.0
    pal = dict(art.DARK)
    pal.update(far='#1d3a86', far_dk='#2a4a9a', mid='#183175', mid_dk='#22408b', near='#132863', dot_mid='#22408a',
               dot_near='#1d3878', star='#2c4a9a', band=COVER_BAND, wave_back='#5d92ee', wave_front='#2f6fe0')
    bub = dict(stroke='#9cc0ff', fill='#cfe0ff', fill_op=0.16, pal=pal)
    # a slightly deeper surface and a softer sun glow than ocean_art's 'deep' scene keep the white type above AA contrast
    water = (('0', '#2a60d2'), ('.16', '#2356c6'), ('.42', '#1f4bb4'), ('.7', '#173983'), ('1', '#0e2357'))
    uid = f'cover{dayn}'
    defs = (f'<linearGradient id="{uid}-water" x1="0" y1="0" x2="0" y2="1">'
            + ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in water) + '</linearGradient>'
            f'<radialGradient id="{uid}-glow" cx="50%" cy="0%" r="70%"><stop offset="0" stop-color="#bcd6ff" stop-opacity=".26"/>'
            f'<stop offset="1" stop-color="#bcd6ff" stop-opacity="0"/></radialGradient>')
    out = [f'<rect width="{W}" height="{H}" fill="url(#{uid}-water)"/>',
           f'<ellipse cx="{fmt(X(W * 0.58))}" cy="0" rx="{fmt(W * 0.75)}" ry="{fmt(H * 0.42)}" fill="url(#{uid}-glow)"/>']
    rdefs, rays = art._rays(W, H, uid, f'{seed}:deep', 8, 0.2, '#ffffff', reach=0.8)
    defs += rdefs
    out.append(rays)
    # the distant school: one mono colour, small and faint, so the bot and the title lead
    sx, sy, sf = lay['school']
    out.append(f'<g opacity=".5">{art.fish_school(W * sx, H * sy, 26 * u, "#5d86d8", n=6, flip=sf, seed=f"{seed}s", mono=True)}</g>')
    bed_top = H * 0.70
    bed_h = H - bed_top
    bed, layers = art._bed(W, H, bed_top, bed_h, pal, art._rng(f'scene:{seed}:deep:0'), 'tall', scale=u * 0.8)
    out.append(bed)
    # the band: an organic top edge (two summed swells), the reef planted over it
    bt = bed_top + 0.86 * bed_h
    ph = 0.6 + seed * 0.37
    edge = [(x, bt + 7.5 * u * math.sin(2 * math.pi * x / (W / 1.6) + ph) + 3.2 * u * math.sin(2 * math.pi * x / (W / 4.6) + ph * 2.1))
            for x in [-30 + i * (W + 60) / 48 for i in range(49)]]
    out.append(f'<path d="{art.catmull(edge)} L{fmt(W + 30)},{fmt(H + 10)} L-30,{fmt(H + 10)} Z" fill="{COVER_BAND}"/>')
    foot = bt
    lx, rx = W * 0.045, W * 0.875
    reef = [art.seaweed(X(lx), foot + 10 * u, bed_h * 0.98, pal['weed'], width=13 * u, amp=12 * u, wl=125 * u, phase=0.3),
            art.seaweed(X(lx + 30 * u), foot + 10 * u, bed_h * 0.66, pal['weed_light'], width=10 * u, amp=10 * u, wl=100 * u, phase=2.2),
            art.branch_coral(X(rx), foot + 9 * u, 1.0 * u, pal['coral'], width=11.5 * u, flip=mir),
            art.anemone(X(rx - 128 * u), foot + 8 * u, 46 * u, pal=pal),
            art.seaweed(X(rx + 78 * u), foot + 10 * u, bed_h * 0.52, pal['weed_light'], width=9 * u, amp=8 * u, wl=90 * u, phase=1.4)]
    out.append(''.join(reef))
    out.append(art.bubble_trail(X(W * 0.09), foot - bed_h * 0.98, H * 0.16, 11 * u, n=5, seed=f'{seed}a', **bub))
    out.append(art.bubble_trail(X(W * 0.86), foot - bed_h * 0.9, H * 0.1, 12 * u, n=4, seed=f'{seed}b', **bub))
    # two reef companions, heading towards each other
    for name, ln in (('yellow', 96), ('red', 58)):
        fx, fy, right = lay[name]
        out.append(art.fish(W * fx, H * fy, ln * u, name, flip=right, pal=pal))
    # the diver bot, in the scene (behind the surface, in front of the reef)
    pose, bx, by, size = lay['bot']
    bw, bh = art.diver_bot_box(pose, size)
    if by is None:                       # seated: the bottom of its box rests in the near hill, above the band
        by = min(layers['near'](bx) + 40 * u, bt - 14 * u) - bh / 2
    out.append(art.diver_bot(pose, bx, by, size, f'{uid}-bot', dark=True))
    sh = H * 0.04
    out.append(art._surface(W, sh, pal, True, wl=sh * 1.7))
    return art._svg(W, H, ''.join(out), 'scene', ' preserveAspectRatio="xMidYMid slice"', defs)


def cover(d, author, dayn):
    t = d['title'] if isinstance(d['title'], list) and len(d['title']) == 3 else None
    if not t:
        raise BuildError('days.yaml title must be a list of three cover lines, e.g. [How Google Crawls, in the Age of, AI SEARCH]')
    return COVER.format(scene=cover_scene(dayn), ed=e(d['edition']), t1=e(t[0]), t2=e(t[1]), t3=e(t[2]), sub=e(d['subtitle']),
                        author=e(author), date=e(d['cover_date']).replace(' · ', ' &nbsp;·&nbsp; '))


def replace_cover(html, new):
    """Swap the template's <div class="cover"> block (matched by counting nested divs) for the Deep Dive cover."""
    i, depth = html.find('<div class="cover">'), 0
    for m in re.finditer(r'<div\b|</div>', html[max(i, 0):]) if i >= 0 else []:
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            j = i + m.end() + (html[i + m.end():i + m.end() + 1] == '\n')
            return html[:i] + new + html[j:]
    raise BuildError('the template has no complete <div class="cover"> ... </div> block for the Deep Dive cover')


# ---------------------------------------------------------------- SVG and inline recolour (modern palette -> ocean palette)
TEXT_MAP = {'#2457e6': '#2152c4', '#0f1d33': '#262d3b', '#2a3446': '#3b4354', '#667085': '#687185', '#98a2b3': '#717b90',
            '#0b8a5f': '#15784b', '#c8372d': '#c2412f', '#6d3fd6': '#6a45cf', '#b86e00': '#8f5200',
            '#bcd0ff': '#d4e3ff', '#dbe5ff': '#e6efff', '#e3eaff': '#eef4ff'}
FILL_MAP = {'#2457e6': '#2f6fe0', '#e8eefd': '#e6effd', '#0f1d33': '#262d3b', '#0b1a33': '#16306b', '#f5f7fb': '#f4f8ff',
            '#e3f4ec': '#e0f3e8', '#fbe7e5': '#fde6e1', '#667085': '#687185', '#98a2b3': '#a3b0c8',
            '#c8372d': '#c2412f', '#0b8a5f': '#1f9a74', '#b86e00': '#d48712'}
STROKE_MAP = {'#2457e6': '#2f6fe0', '#c7cdd8': '#c3d3ee', '#e4e7ec': '#dde7f6', '#98a2b3': '#9fb0cc', '#667085': '#7a87a3',
              '#0b8a5f': '#1f9a74', '#c8372d': '#c2412f', '#6d3fd6': '#6a45cf', '#bcd0ff': '#a9c6ff', '#b86e00': '#d48712'}
INLINE_MAP = {'#2457e6': '#2152c4', '#0b8a5f': '#15784b', '#6d3fd6': '#6a45cf', '#b86e00': '#8f5200', '#667085': '#687185',
              '#c8372d': '#c2412f'}
RECOLORED = ('rect', 'text', 'tspan', 'path', 'circle', 'line', 'polygon', 'g', 'svg', 'marker')
WHITE = ('#fff', '#ffffff')
FONT_MAP = {'Inter': 'Figtree', 'Fraunces': 'Figtree'}


def unmapped_colours(html):
    """Every colour the Deep Dive recolouring would leave in its modern value: an SVG fill or stroke missing from TEXT_MAP,
    FILL_MAP or STROKE_MAP (white excepted), a colour on an SVG element the recolouring skips, or an inline style="color:..."
    missing from INLINE_MAP."""
    bad = set()
    for svg in re.findall(r'<svg viewBox.*?</svg>', html, flags=re.S):
        for m in re.finditer(r'<([a-zA-Z][\w-]*)\b[^>]*>', svg):
            name = m.group(1)
            for attr, v in re.findall(r'\s((?:stop-)?color|fill|stroke)="(#[0-9a-fA-F]{3,6})"', m.group(0)):
                table = (TEXT_MAP if name in ('text', 'tspan', 'g') else FILL_MAP) if attr == 'fill' else STROKE_MAP if attr == 'stroke' else {}
                if name not in RECOLORED or (v.lower() not in table and v.lower() not in WHITE):
                    bad.add(f'<{name} {attr}="{v}">')
    bad |= {f'style="color:{v}"' for v in re.findall(r'style="color:(#[0-9a-fA-F]{3,6})"', html) if v.lower() not in INLINE_MAP}
    return sorted(bad)


def recolor_tag(m):
    tag, name = m.group(0), m.group(1)

    def sub(attr, table):
        nonlocal tag
        tag = re.sub(rf'\s{attr}="(#[0-9a-fA-F]{{3,6}})"', lambda mm: f' {attr}="{table.get(mm.group(1).lower(), mm.group(1))}"', tag)
    sub('fill', TEXT_MAP if name in ('text', 'tspan', 'g') else FILL_MAP)
    sub('stroke', STROKE_MAP)

    def font(f):
        fam = FONT_MAP[f.group(1)]
        return f'font-family="{fam}, {SYM}"'
    display = re.search(r'font-family="Fraunces\b', tag) and 'font-weight=' not in tag
    tag = re.sub(rf'font-family="(Inter|Fraunces)(?:, {SYM})?"', font, tag)
    if display:                                   # Fraunces display words become Figtree Bold
        tag = tag.replace('font-family="Figtree', 'font-weight="700" font-family="Figtree', 1)
    return tag


def recolor_svgs(html):
    return re.sub(r'<svg viewBox.*?</svg>',
                  lambda s: re.sub(r'<(rect|text|tspan|path|circle|line|polygon|g|svg|marker)\b[^>]*>', recolor_tag, s.group(0)),
                  html, flags=re.S)


def recolor_inline(html):
    for a, b in INLINE_MAP.items():
        html = html.replace(f'style="color:{a}"', f'style="color:{b}"')
    return html


# ---------------------------------------------------------------- build-time HTML touches (the template is never edited)
def section_bubbles(html):
    """Each section head's number becomes a glossy bubble (the number stays real text, so it can be found and copied)."""
    return re.sub(r'<div class="num">(\d{1,3})</div>',
                  lambda m: f'<div class="num">{art.section_bubble(m.group(1), uid=f"sec{m.group(1)}", size=14.5)}</div>', html)


def touches(html, d):
    html = html.replace('href="style.css"', 'href="../ocean.css"').replace(' style="border-left-color: var(--blue)"', '')
    html = html.replace('<h2 class="title">Contents</h2>',
                        f'<div class="kicker">Dive log &nbsp;·&nbsp; {e(d["edition"])}</div>\n  <h2 class="title">Contents</h2>')
    # "(not in docs)" markers get their own quiet italic style
    html = re.sub(r'<span class="muted">(\((?:[^()<]*?)not&nbsp;in&nbsp;docs\))</span>', r'<span class="muted nid">\1</span>', html)
    # a date in a section lead ("2 October 2026") stays on one line
    return re.sub(r'<div class="lead"[^>]*>.*?</div>', lambda m: DATE.sub(lambda d: '\u00a0'.join(d.groups()), m.group(0)), html, flags=re.S)


MONTHS = 'January|February|March|April|May|June|July|August|September|October|November|December'
DATE = re.compile(rf'\b(\d{{1,2}}) ({MONTHS}) (\d{{4}})\b')


# ---------------------------------------------------------------- running header: which section each page belongs to
def strip(s):
    return htmllib.unescape(re.sub(r'<[^>]+>', '', s)).replace('\u00a0', ' ').strip()


def sections(html, d):
    """[(needle, label)] for every <section class="s"> in order: needle finds its first page, label is printed in the header."""
    out = []
    marks = [v for v in (d.get('pages') or {}).values() if v]
    for m in re.finditer(r'<section class="s"[^>]*>(.*?)</section>', html, flags=re.S):
        body = m.group(1)
        h2 = re.search(r'<h2[^>]*>(.*?)</h2>', body, flags=re.S)
        kick = re.search(r'<div class="kicker">(.*?)</div>', body, flags=re.S)
        title = strip(h2.group(1)) if h2 else ''
        num = re.match(r'Section (\d+)', strip(kick.group(1))) if kick else None
        if num:
            out.append((f'Section {num.group(1)}', num.group(1), title))
        else:
            text = strip(body)
            needle = next((mk for mk in marks if mk in text), title)
            out.append((needle, '', title))
    return out


def page_labels(pdf, html, d):
    """{page number: (number, title)} for every page after the cover, from the section starts found in the paginated PDF."""
    secs = sections(html, d)
    found, n = find_pages(pdf, {i: s[0] for i, s in enumerate(secs)})
    starts = sorted((p, i) for i, p in found.items())
    first = {sp for sp, _ in starts} | {2}
    labels = {}
    for p in range(2, n + 1):
        cur = [i for sp, i in starts if sp <= p]
        labels[p] = (secs[cur[-1]][1], secs[cur[-1]][2], p in first) if cur else ('', 'Contents', p in first)
    return labels, n


# ---------------------------------------------------------------- underlay (pages 2..N), drawn in 0.1 mm units
W, H = 2100, 2970
CARD = (110, 170, 1990, 2730)            # x0, y0, x1, y1 of the white card (11 mm side margins)
CARD_R = 50
SEABED_TOP, SEABED_H = 2520, 450         # seabed strip at the bottom (band from about 285.6 mm)
SLIM = dict(far=0.27, mid=0.43, near=0.58, band=0.72)
BAND_Y = SEABED_TOP + SLIM['band'] * SEABED_H


def card_svg(n, texture=True):
    """The white card behind the text: two faint offset layers for depth, a thin frame and, on a page that opens a section,
    a faint line texture behind the heading that fades out (as on the event's screens)."""
    x0, y0, x1, y1 = CARD
    g = f'p{n}-tex'
    lines = []
    y = y0 + 26
    while texture and y < y0 + 330:
        op = 0.075 * (1 - (y - y0) / 330) ** 1.4
        lines.append(f'<line x1="{x0 + 40}" y1="{fmt(y)}" x2="{x1 - 40}" y2="{fmt(y)}" stroke-opacity="{fmt(op, 3)}"/>')
        y += 14.5
    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="layer" aria-hidden="true">'
            f'<defs><linearGradient id="{g}" gradientUnits="userSpaceOnUse" x1="{x0}" y1="0" x2="{x1}" y2="0">'
            f'<stop offset="0" stop-color="#2f6fe0" stop-opacity="0"/><stop offset=".08" stop-color="#2f6fe0"/>'
            f'<stop offset=".92" stop-color="#2f6fe0"/><stop offset="1" stop-color="#2f6fe0" stop-opacity="0"/></linearGradient></defs>'
            f'<rect x="{x0}" y="{y0 + 9}" width="{x1 - x0}" height="{y1 - y0}" rx="{CARD_R}" fill="#2a5bc4" fill-opacity=".05"/>'
            f'<rect x="{x0}" y="{y0 + 4}" width="{x1 - x0}" height="{y1 - y0}" rx="{CARD_R}" fill="#2a5bc4" fill-opacity=".05"/>'
            f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="{CARD_R}" fill="#ffffff" stroke="{P["frame"]}" stroke-width="3"/>'
            f'<g stroke="url(#{g})" stroke-width="2">{"".join(lines)}</g></svg>')


def accents_svg(n):
    """Reef colour in the margins and the seabed strip, never under the card's text area. Deterministic per page number."""
    rnd = random.Random(f'deep-dive-page:{n}')
    a = []
    band = BAND_Y
    # bottom left: two seaweed ribbons rising from the band through the margin
    a.append(art.seaweed(58, band + 30, rnd.uniform(250, 330), P['weed'], width=11, amp=10, wl=118, phase=rnd.uniform(0, 6)))
    a.append(art.seaweed(88, band + 30, rnd.uniform(150, 210), P['weed_light'], width=9, amp=8, wl=96, phase=rnd.uniform(0, 6)))
    # bottom right: coral in the margin, an anemone below the card
    a.append(art.branch_coral(2040, band + 26, 0.46, P['coral'], width=9.5, flip=rnd.random() < 0.5))
    ax = rnd.uniform(1800, 1880) if n % 2 else rnd.uniform(1560, 1700)
    a.append(art.anemone(ax, band + 10, 36, seed=n, pal=P))
    # one small fish in a margin, alternating sides, with a few bubbles above it
    left = n % 2 == 0
    fx = 55 if left else 2045
    fy = rnd.uniform(700, 2050)
    color = ('blue', 'yellow', 'red', 'green')[n % 4]
    a.append(art.fish(fx, fy, 64, color, flip=left))
    bx = fx + (8 if left else -8)
    a.append(art.bubble(bx, fy - 62, 8.5))
    a.append(art.bubble(bx + (10 if left else -10), fy - 98, 5.5))
    a.append(art.bubble(bx - 2, fy - 126, 3.6))
    # every third page a far, faint pair of mono fish in the other margin
    if n % 3 == 0:
        ox = 2045 if left else 55
        oy = rnd.uniform(500, 1700)
        a.append(art.mono_fish(ox, oy, 34, '#9fb3e6', flip=not left))
        a.append(art.mono_fish(ox + (16 if left else -16), oy + 38, 26, '#9fb3e6', flip=not left))
    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="layer" aria-hidden="true">' + ''.join(a) + '</svg>')


# ---------------------------------------------------------------- end vignettes (quiet art in a card's empty bottom)
VIG_MIN = 450                  # draw one only when the card leaves at least 45 mm free below the last content
VIG_GAP = 110                  # never closer than 11 mm to the content above
VIG_LINE = CARD[3] - 55        # the wavy hairline the silhouettes stand on (5.5 mm above the card's bottom edge)
VIG_X = (230, 1870)            # inside the text column
VIG_PALE, VIG_SOFT, VIG_LINEC = '#dfe5f8', '#cdd6f3', '#c3d0ef'
BOT_UNIT_PX = 96 / 254         # CSS px per 0.1 mm: tells the bot its rendered size


BOT_FIT = {'wave': (420, 440), 'read': (250, 265), 'swim': (290, 330)}   # pose: (size, room it needs above the line)


def content_bottoms(pdf):
    """{page: lowest point of the content in 0.1 mm} for every page after the cover, and the set of contact pages.
    The content pages have a transparent background, so every char, rule, box and image is content."""
    bottoms, contact = {}, set()
    with pdfplumber.open(pdf) as doc:
        for i, pg in enumerate(doc.pages[1:], start=2):
            objs = pg.chars + pg.rects + pg.curves + pg.lines + pg.images
            bottoms[i] = max((o['bottom'] for o in objs), default=0) * 254 / 72
            if 'keep in contact' in re.sub(r'\s+', ' ', pg.extract_text() or '').lower():
                contact.add(i)
    return bottoms, contact


def vignette_plan(bottoms, contact):
    """{page: (top, robot pose or None)} for the pages that get an end vignette. The contact page always gets the bot waving;
    of the other vignette pages with room for it, every second gets it (a small swim, then reading on the line). Deterministic."""
    plan, k = {}, 0
    for p in sorted(bottoms):
        if CARD[3] - bottoms[p] < VIG_MIN:
            continue
        top = bottoms[p] + VIG_GAP
        if p in contact:
            plan[p] = (top, 'wave')
            continue
        if VIG_LINE - top >= max(BOT_FIT['swim'][1], BOT_FIT['read'][1]):     # room for the bot at full vignette size
            plan[p] = (top, ('swim', 'read')[(k // 2) % 2] if k % 2 == 1 else None)
            k += 1
        else:
            plan[p] = (top, None)
    return plan


def vignette_svg(n, top, pose):
    """A calm end vignette between `top` and the card's bottom: pale mono reef silhouettes on a wavy hairline, two far fish,
    and on some pages the diver bot. Nothing reaches above `top`, so it never sits under text."""
    rnd = random.Random(f'deep-dive-vignette:{n}')
    x0, x1 = VIG_X
    y = VIG_LINE
    room = y - top                                   # height available above the line
    s = min(1.0, room / 330)                         # silhouettes shrink on a tighter page
    g = f'p{n}-vig'
    ph = rnd.uniform(0, 6)
    wy = lambda x: y + 5 * math.sin(2 * math.pi * x / 260 + ph)
    line = [(x0 + (x1 - x0) * i / 60, wy(x0 + (x1 - x0) * i / 60)) for i in range(61)]
    out = [f'<defs><linearGradient id="{g}" gradientUnits="userSpaceOnUse" x1="{x0}" y1="0" x2="{x1}" y2="0">'
           f'<stop offset="0" stop-color="{VIG_LINEC}" stop-opacity="0"/><stop offset=".14" stop-color="{VIG_LINEC}"/>'
           f'<stop offset=".86" stop-color="{VIG_LINEC}"/><stop offset="1" stop-color="{VIG_LINEC}" stop-opacity="0"/></linearGradient></defs>',
           f'<path d="{art.catmull(line)}" fill="none" stroke="url(#{g})" stroke-width="3" stroke-linecap="round"/>']
    # the bot's place first, so the reef leaves room for it
    bot, bot_x = '', None
    if pose:
        size = BOT_FIT[pose][0] * min(1.0, room / BOT_FIT[pose][1])
        bw, bh = art.diver_bot_box(pose, size)
        right = pose == 'wave' or n % 2 == 1
        bot_x = (x1 - 300 - bw / 2) if right else (x0 + 300 + bw / 2)
        by = (y - 80 - bh / 2) if pose == 'swim' else (wy(bot_x) + 3 - bh / 2)   # gliding above the reef, or on the line
        if by - bh / 2 >= top - 0.5 and size >= 170:
            bot = art.diver_bot(pose, bot_x, by, size, f'p{n}-bot', flip=(pose == 'swim' and right), unit_px=BOT_UNIT_PX)
        else:
            bot_x = None
    avoid = (bot_x - 200, bot_x + 200) if bot_x is not None else (0, 0)
    slots = [x0 + 130 + rnd.uniform(0, 80), x1 - 130 - rnd.uniform(0, 80)]
    slots += [x0 + (x1 - x0) * t + rnd.uniform(-60, 60) for t in (0.3, 0.5, 0.7)]
    reef = []
    for i, x in enumerate(slots):
        if avoid[0] <= x <= avoid[1]:
            continue
        base = wy(x) + 2
        kind = ('fan', 'coral')[(i + n) % 2] if i < 2 else ('fern', 'star', 'fern', 'star')[(i + n) % 4]
        if kind == 'fan':
            reef.append(art.fan_coral(x, base, rnd.uniform(150, 190) * s, VIG_PALE, n=9, width=6 * s))
            reef.append(art.fern(x + 75 * s, base, rnd.uniform(105, 135) * s, VIG_SOFT, leaves=6, lean=0.12, size=0.9 * s))
        elif kind == 'coral':
            reef.append(art.branch_coral(x, base, 0.76 * s, VIG_PALE, width=11 * s, flip=rnd.random() < 0.5))
            reef.append(art.fern(x - 85 * s, base, rnd.uniform(90, 120) * s, VIG_SOFT, leaves=5, lean=-0.14, size=0.8 * s))
        elif kind == 'fern':
            reef.append(art.fern(x, base, rnd.uniform(90, 125) * s, VIG_PALE, leaves=6, lean=rnd.uniform(-0.15, 0.15), size=0.85 * s))
        else:
            reef.append(art.starfish(x, base - 16 * s, 22 * s, VIG_SOFT, rot=rnd.uniform(0, 40)))
    out.append(''.join(reef))
    # two far fish high in the free space, on the side away from the bot
    if room > 260:
        far_side = 0.36 if bot_x is not None and bot_x > (x0 + x1) / 2 else 0.64
        fx = x0 + (x1 - x0) * far_side + rnd.uniform(-80, 80)
        fy = max(top + 40, y - min(room * 0.7, 300))
        left = rnd.random() < 0.5
        out.append(art.mono_fish(fx, fy, 46, VIG_SOFT, flip=not left))
        out.append(art.mono_fish(fx + (56 if left else -56), fy + 32, 34, VIG_PALE, flip=not left))
    out.append(bot)
    return f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="layer" aria-hidden="true">' + ''.join(out) + '</svg>'


UNDER_CSS = '''
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #ffffff; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'Figtree', sans-serif; font-kerning: normal; }
.pg { position: relative; width: 210mm; height: 297mm; overflow: hidden; break-after: page;
      background: linear-gradient(180deg, #ffffff 0%, #f2f7fe 14%, #e2edfb 46%, #d2e2f8 74%, #c7d9f5 100%); }
.pg:last-child { break-after: auto; }
.pg svg { position: absolute; display: block; }
.pg .light, .pg .layer { left: 0; top: 0; width: 210mm; height: 297mm; }
.pg .topwave { left: 0; top: 0; width: 210mm; height: 9.5mm; }
.pg .seabed { left: 0; top: @SBT@mm; width: 210mm; height: @SBH@mm; }
.rh { position: absolute; left: 13mm; right: 13mm; top: 10.6mm; height: 5mm; display: flex; justify-content: space-between;
      align-items: baseline; gap: 6mm; font-size: 7.4pt; color: #687185; letter-spacing: 0.01em; white-space: nowrap; }
.rh b { color: #262d3b; font-weight: 700; }
.rh .dot { color: #2f6fe0; margin: 0 1.5mm; }
.rh .sec { overflow: hidden; text-overflow: ellipsis; color: #4a5366; }
.rh .sec i { font-style: normal; font-weight: 800; color: #2152c4; margin-right: 1.6mm; letter-spacing: 0.02em; }
.rf { position: absolute; left: 13mm; right: 13mm; top: @FTY@mm; height: 8mm; display: grid; grid-template-columns: 1fr 9mm 1fr;
      align-items: center; font-size: 7.1pt; color: #e3e7fa; letter-spacing: 0.01em; white-space: nowrap; }
.rf .l { overflow: hidden; text-overflow: ellipsis; }
.rf .l b { color: #ffffff; font-weight: 700; }
.rf .r { text-align: right; color: #ffffff; font-weight: 600; letter-spacing: 0.04em; }
.rf .pnb { display: block; margin: 0 auto; position: static; }
'''


def underlay_html(labels, n_pages, dayn, d, author, vignettes=None):
    sbed = art.seabed(W, SEABED_H, variant='slim', seed=26, band=True, cls='seabed')
    light = art.light_blobs(W, H, opacity=0.9)
    wave = art.top_wave(W, 95, wl=300)
    css = (UNDER_CSS.replace('@SBT@', fmt(SEABED_TOP / 10)).replace('@SBH@', fmt(SEABED_H / 10))
           .replace('@FTY@', fmt((BAND_Y + (H - BAND_Y) / 2) / 10 - 4 + 0.15)))
    pages = []
    for p in range(2, n_pages + 1):
        num, title, start = labels[p]
        sec = (f'<i>{e(num)}</i>' if num else '') + e(title)
        pages.append(f'''<div class="pg">
{light}{sbed}{wave}{card_svg(p, start)}{accents_svg(p)}{vignette_svg(p, *vignettes[p]) if p in (vignettes or {}) else ''}
<div class="rh"><div><b>{e(author)}</b><span class="dot">&#8226;</span>Day {dayn} Field Guide</div><div class="sec">{sec}</div></div>
<div class="rf"><div class="l">{e(d["footer"])} <span class="dot">&nbsp;·&nbsp;</span> <b>Deep Dive edition</b></div>{art.page_bubble(str(p), uid=f"pg{p}", size=7.4)}<div class="r">Barcelona &nbsp;·&nbsp; 2026</div></div>
</div>''')
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>underlay</title><style>\n{font_faces("../fonts/")}\n{css}</style>'
            f'</head><body>\n' + '\n'.join(pages) + '\n</body></html>\n')


def finish(src, html, dst, dayn, d, author):
    labels, n = page_labels(src, html, d)
    plan = vignette_plan(*content_bottoms(src))
    print('end vignettes:', ', '.join(f'p{p}' + (f' ({v[1]})' if v[1] else '') for p, v in sorted(plan.items())) or 'none')
    under = BUILD / '_ocean_under.html'
    under.write_text(underlay_html(labels, n, dayn, d, author, plan), encoding='utf-8', newline='\n')
    render(under, BUILD / '_ocean_under.pdf')
    r, u = PdfReader(src), PdfReader(BUILD / '_ocean_under.pdf')
    if len(u.pages) != len(r.pages) - 1:
        raise BuildError(f'the underlay has {len(u.pages)} pages for {len(r.pages) - 1} content pages')
    w = PdfWriter()
    for i, page in enumerate(r.pages):
        if i == 0:
            w.add_page(page); continue
        bg = u.pages[i - 1]
        bg.merge_page(page)
        w.add_page(bg).compress_content_streams()   # merge_page leaves the combined stream uncompressed
    w.add_metadata({'/Title': d['pdf']['ocean']['title'], '/Author': author, '/Subject': d['pdf']['ocean']['subject']})
    with open(dst, 'wb') as f:
        w.write(f)
    return labels


def build(day):
    d, author = day_data(day), config()['author']
    html = (BUILD / f'{day}.html').read_text(encoding='utf-8')
    html = touches(html, d)
    bad = unmapped_colours(html)
    if bad:
        raise BuildError('colours the Deep Dive style cannot recolour: ' + ', '.join(bad) + '. Use the modern palette listed in '
                         '_system/pdf/README.md, or add the colour to TEXT_MAP, FILL_MAP, STROKE_MAP or INLINE_MAP in build_ocean.py.')
    html = recolor_inline(recolor_svgs(html))
    html = replace_cover(section_bubbles(html), cover(d, author, day.replace('day', '')))     # the art is drawn in the ocean palette already
    pdf = paginate(html, d, BUILD / '_ocean1.html', '_ocean')
    tmp, out = BUILD / f'{day}-field-guide-deep-dive.pdf', OUT / f'{day}-field-guide-deep-dive.pdf'
    final_html = (BUILD / '_ocean1.html').read_text(encoding='utf-8')
    finish(pdf, final_html, tmp, day.replace('day', ''), d, author)
    check_fonts(tmp)
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tmp, out)
    print('wrote', out)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'day1')
