"""README illustrations, group B: topic areas about how pages get in: the topics overview, crawling, indexing, rendering, the pipeline, index signals, structured data and media, international.

Build every scene with illus_common.Scene; see illus_a.scene_claims (20-claims) for the reference scene.
"""
import math

from illus_common import oa
from illus_common import (FLOOR, H, W, Scene, catmull, fmt, mix, stroke)   # noqa: F401

# the saturated label inks, used in both waters (as illus_a.claim_card does)
INK = {k: oa.PALETTE['label_' + k][0] for k in ('slide', 'stage', 'docs', 'analysis', 'press')}


# ------------------------------------------------------------------------------------------------------------ helpers
def _pt(x, y):
    return f'{fmt(x)},{fmt(y)}'


def _quad(p0, c, p1, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1])


def _rock_tones(p):
    """(body, shade, highlight) of a seabed boulder: lighter than the near hill so it reads in front of it."""
    if p['dark']:
        return '#3a56a6', '#2c458f', '#5673c4'
    return '#d0d8f5', '#aab5e9', '#eef1fc'


def rock(p, cx, base, w, h, seed=0, tone=None):
    """A smooth boulder with a flat bottom on `base`: one shade (lower right), one highlight, the shared outline."""
    rnd = oa._rng(f'b-rock:{seed}')
    body, shade, hi = tone or _rock_tones(p)
    pts = []
    for i in range(8):
        a = math.pi * (1 - i / 7)
        k = 1 + (rnd.uniform(-.07, .07) if 0 < i < 7 else 0)
        pts.append((cx + math.cos(a) * w / 2 * k, base - math.sin(a) ** .8 * h * k))
    inner = [(cx - w * .07 + (x - cx) * .86, base - (base - y) * .86) for x, y in pts]
    hl = [pts[2], pts[3]]
    return (f'<path d="{catmull(pts)} Z" fill="{shade}"/>'
            f'<path d="{catmull(inner)} Z" fill="{body}"/>'
            f'<path d="M{_pt(*mix_pt(hl[0], pts[1], .3))} Q{_pt(*hl[0])} {_pt(*mix_pt(hl[0], hl[1], .6))}" fill="none" '
            f'stroke="{hi}" stroke-width="2.4" stroke-linecap="round" transform="translate(2,4)"/>'
            f'<path d="{catmull(pts)} Z" fill="none" {stroke(p)}/>')


def mix_pt(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def scallop(p, cx, base, w, color, rib=None, dashed=False, op=1.0):
    """An upright scallop shell, hinge at (cx, base), fanning upwards with a scalloped rim and ribs."""
    r = w / 2
    rib = rib or mix(color, p['line'], .28)
    n = 6
    angs = [math.radians(200 + 140 * i / n) for i in range(n + 1)]
    cy = base - 3
    pts = [(cx + math.cos(a) * r, cy + math.sin(a) * r * 1.02) for a in angs]
    d = [f'M{_pt(cx - 5, base)} L{_pt(*pts[0])}']
    for i in range(n):
        am = (angs[i] + angs[i + 1]) / 2
        d.append(f'Q{_pt(cx + math.cos(am) * r * 1.16, cy + math.sin(am) * r * 1.18)} {_pt(*pts[i + 1])}')
    d.append(f'L{_pt(cx + 5, base)} Z')
    d = ' '.join(d)
    ribs = ' '.join(f'M{_pt(cx, cy)} L{_pt(cx + math.cos(a) * r * .86, cy + math.sin(a) * r * .88)}' for a in angs[1:-1])
    o = f' fill-opacity="{fmt(op, 2)}"' if op < 1 else ''
    line = (f'stroke="{p["line"]}" stroke-width="1.4" stroke-dasharray="3 3" stroke-linecap="round" stroke-opacity=".8"'
            if dashed else stroke(p))
    return (f'<path d="{d}" fill="{color}"{o}/>'
            f'<path d="{ribs}" stroke="{rib}" stroke-width="1.5" stroke-linecap="round" stroke-opacity="{fmt(.8 * op, 2)}"/>'
            f'<path d="M{_pt(cx - 8, base)} L{_pt(cx - 6, base - 6)} L{_pt(cx + 6, base - 6)} L{_pt(cx + 8, base)} Z" '
            f'fill="{rib}"{o}/>'
            f'<path d="{d}" fill="none" {line}/>')


def page(p, x, y, w, h, lines=2, fold=7, rot=0.0, ink=None, op=1.0):
    """A small document: paper with a folded top-right corner and a couple of text strokes; (x, y) is its centre."""
    x0, y0 = -w / 2, -h / 2
    body = (f'M{_pt(x0, y0)} L{_pt(-x0 - fold, y0)} L{_pt(-x0, y0 + fold)} L{_pt(-x0, -y0)} L{_pt(x0, -y0)} Z')
    ls = ' '.join(f'M{_pt(x0 + 4, y0 + fold + 4 + i * 5)} L{_pt(-x0 - (4 if i % 2 == 0 else 8), y0 + fold + 4 + i * 5)}'
                  for i in range(lines))
    head = (f'<path d="M{_pt(x0 + 4, y0 + 4)} L{_pt(x0 + w * .45, y0 + 4)}" stroke="{ink}" stroke-width="2.4" '
            f'stroke-linecap="round"/>' if ink else '')
    o = f' opacity="{fmt(op, 2)}"' if op < 1 else ''
    return (f'<g transform="translate({_pt(x, y)}) rotate({fmt(rot)})"{o}>'
            f'<path d="{body}" fill="{p["paper"]}" {stroke(p)}/>'
            f'<path d="M{_pt(-x0 - fold, y0)} L{_pt(-x0 - fold, y0 + fold)} L{_pt(-x0, y0 + fold)} Z" fill="{p["paper_sh"]}" '
            f'{stroke(p, .7)}/>' + head +
            f'<path d="{ls}" stroke="{p["paper_line"]}" stroke-width="1.8" stroke-linecap="round"/></g>')


def star5(x, y, r, color, line=None):
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr = r if i % 2 == 0 else r * .46
        pts.append(_pt(x + rr * math.cos(a), y + rr * math.sin(a)))
    st = f' stroke="{line}" stroke-width="1.2" stroke-linejoin="round"' if line else ''
    return f'<path d="M{" L".join(pts)} Z" fill="{color}"{st}/>'


def pearl(p, x, y, r, tint=None):
    """A glossy pearl (same drawing as group A's): shade crescent lower right, highlight upper left, thin outline."""
    body = tint or p['pearl']
    shade = mix(body, p['pearl_sh'] if tint is None else p['line'], .25 if tint else 1.0)
    return (f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{shade}"/>'
            f'<circle cx="{fmt(x - r * .17)}" cy="{fmt(y - r * .17)}" r="{fmt(r * .8)}" fill="{body}"/>'
            f'<circle cx="{fmt(x - r * .36)}" cy="{fmt(y - r * .36)}" r="{fmt(r * .27)}" fill="{p["pearl_hi"]}"/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="none" {stroke(p, .8)}/>')


def glow_dot(sc, name, x, y, r, color, op=.8):
    return f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{sc.radial(name, color, op, .3)}"/>'


def gear(cx, cy, r, teeth, color, hole):
    """A small gear: a toothed ring and a hub."""
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        rr = r if i % 4 in (1, 2) else r * .78
        pts.append(_pt(cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return (f'<path d="M{" L".join(pts)} Z" fill="{color}" stroke-linejoin="round"/>'
            f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r * .32)}" fill="{hole}"/>')


def _edge_dressing(sc, left=True, right=True, weed_h=(118, 82), coral_x=820):
    p = sc.p
    if left:
        sc.over.append(sc.seaweed(30, weed_h[0], phase=.4) + sc.seaweed(50, weed_h[1], p['weed_light'], width=4, phase=1.9))
    if right:
        sc.over.append(sc.coral(coral_x, .38))
        sc.over.append(sc.seaweed(856, 92, p['weed_light'], width=4, phase=2.6))


# ------------------------------------------------------------------------------------------------------------ 30-topics
def coral_head(p, kind, x, base, h, color):
    """One small coral head of the reef district (13 kinds, one per topic area)."""
    if kind == 'anemone':
        return oa.anemone(x, base, h * .6, pal=p)
    dk = mix(color, p['line'], .3)
    st = stroke(p, .85)
    if kind == 'fan':
        return oa.fan_coral(x, base, h, color, n=9, spread=56, width=2.6)
    if kind == 'branch':
        s = h / 215
        return oa.branch_coral(x, base, s, color, width=5.4)
    if kind == 'brain':
        r = h * .62
        d = f'M{_pt(x - r, base)} A{fmt(r)},{fmt(h)} 0 0 1 {_pt(x + r, base)} Z'
        mz = ' '.join(f'M{_pt(x - r * k, base - 1)} A{fmt(r * k)},{fmt(h * k)} 0 0 1 {_pt(x + r * k, base - 1)}' for k in (.68, .38))
        return (f'<path d="{d}" fill="{color}"/>'
                f'<path d="{mz}" fill="none" stroke="{dk}" stroke-width="1.7" stroke-linecap="round"/>'
                f'<path d="{d}" fill="none" {st}/>')
    if kind == 'table':
        y = base - h * .62
        return (f'<path d="M{_pt(x - 3, base)} L{_pt(x - 2, y)} L{_pt(x + 2, y)} L{_pt(x + 3, base)} Z" fill="{dk}"/>'
                f'<path d="M{_pt(x - 24, y + 2)} Q{_pt(x, y - 12)} {_pt(x + 24, y + 2)} Q{_pt(x, y + 6)} {_pt(x - 24, y + 2)} Z" '
                f'fill="{color}" {st}/>'
                f'<path d="M{_pt(x - 18, y + 4)} l0,4 M{_pt(x - 6, y + 5)} l0,5 M{_pt(x + 9, y + 5)} l0,4 M{_pt(x + 19, y + 4)} l0,3" '
                f'stroke="{color}" stroke-width="2.6" stroke-linecap="round"/>')
    if kind == 'seapen':
        return oa.fern(x, base, h * .78, color, leaves=6, lean=.12, size=.36)
    if kind == 'tube':
        out = ''
        for dx, hh, ww in ((-8, .74, 8), (6, .58, 8), (-1, 1.0, 9)):
            t = base - h * hh
            out += (f'<path d="M{_pt(x + dx - ww / 2, base)} L{_pt(x + dx - ww / 2 - 1, t)} L{_pt(x + dx + ww / 2 + 1, t)} '
                    f'L{_pt(x + dx + ww / 2, base)} Z" fill="{color}" {st}/>'
                    f'<ellipse cx="{fmt(x + dx)}" cy="{fmt(t)}" rx="{fmt(ww / 2 + 1)}" ry="2.4" fill="{dk}" {st}/>')
        return out
    if kind == 'mushroom':
        y = base - h * .5
        return (f'<path d="M{_pt(x - 4, base)} L{_pt(x - 3, y)} L{_pt(x + 3, y)} L{_pt(x + 4, base)} Z" fill="{p["pearl_sh"]}" {st}/>'
                f'<path d="M{_pt(x - 17, y + 2)} Q{_pt(x - 16, base - h)} {_pt(x, base - h)} Q{_pt(x + 16, base - h)} {_pt(x + 17, y + 2)} Z" '
                f'fill="{color}" {st}/>'
                f'<path d="M{_pt(x - 10, y - 4)} Q{_pt(x - 6, base - h + 5)} {_pt(x - 1, base - h + 4)}" fill="none" stroke="{dk}" '
                f'stroke-width="1.5" stroke-linecap="round" stroke-opacity=".6"/>'
                f'<circle cx="{fmt(x + 6)}" cy="{fmt(base - h * .8)}" r="2" fill="{dk}" fill-opacity=".5"/>')
    if kind == 'softtree':
        tips = [(-12, -.72), (0, -1.0), (12, -.78), (-5, -.5), (8, -.52)]
        stem = ' '.join(f'M{_pt(x, base)} Q{_pt(x + dx * .2, base - h * .45)} {_pt(x + dx, base + dy * h * .9)}' for dx, dy in tips[:3])
        puffs = ''.join(f'<circle cx="{fmt(x + dx)}" cy="{fmt(base + dy * h)}" r="{fmt(6.4 if i < 3 else 5)}" fill="{color}" {st}/>'
                        for i, (dx, dy) in enumerate(tips))
        return f'<path d="{stem}" fill="none" stroke="{dk}" stroke-width="3" stroke-linecap="round"/>' + puffs
    if kind == 'kelp':
        return (oa.seaweed(x - 3, base, h, color, width=4, amp=3.5, wl=34, phase=.3)
                + oa.seaweed(x + 4, base, h * .72, mix(color, '#ffffff', .25), width=3.4, amp=3, wl=30, phase=2.1))
    if kind == 'anemone':
        return oa.anemone(x, base, h * .6, pal=p)
    if kind == 'cup':
        out = ''
        for dx, hh in ((-9, .66), (1, 1.0), (10, .74)):
            t = base - h * hh
            out += (f'<path d="M{_pt(x + dx, base)} L{_pt(x + dx, t + 7)}" stroke="{dk}" stroke-width="2.4" stroke-linecap="round"/>'
                    f'<path d="M{_pt(x + dx - 6, t)} Q{_pt(x + dx - 2, t + 3)} {_pt(x + dx - 1.5, t + 9)} L{_pt(x + dx + 1.5, t + 9)} '
                    f'Q{_pt(x + dx + 2, t + 3)} {_pt(x + dx + 6, t)} Z" fill="{color}" {st}/>'
                    f'<ellipse cx="{fmt(x + dx)}" cy="{fmt(t)}" rx="6" ry="2" fill="{dk}" {st}/>')
        return out
    if kind == 'staghorn':
        segs = [((0, 0), (-2, -.55)), ((-2, -.55), (-12, -1.0)), ((-2, -.55), (6, -.92)), ((0, -.2), (12, -.62)),
                ((12, -.62), (16, -.82)), ((-1, -.35), (-13, -.6)), ((6, -.92), (3, -1.08))]
        d = ' '.join(f'M{_pt(x + a[0], base + a[1] * h)} L{_pt(x + b[0], base + b[1] * h)}' for a, b in segs)
        return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round"/>'
    if kind == 'barrel':
        t = base - h
        d = (f'M{_pt(x - 9, base)} Q{_pt(x - 17, base - h * .5)} {_pt(x - 12, t)} L{_pt(x + 12, t)} '
             f'Q{_pt(x + 17, base - h * .5)} {_pt(x + 9, base)} Z')
        return (f'<path d="{d}" fill="{color}"/>'
                f'<path d="M{_pt(x - 5, base - 2)} Q{_pt(x - 9, base - h * .5)} {_pt(x - 6, t + 2)} M{_pt(x + 5, base - 2)} '
                f'Q{_pt(x + 9, base - h * .5)} {_pt(x + 6, t + 2)} M{_pt(x, base - 2)} L{_pt(x, t + 3)}" fill="none" stroke="{dk}" '
                f'stroke-width="1.6" stroke-linecap="round" stroke-opacity=".7"/>'
                f'<path d="{d}" fill="none" {st}/>'
                f'<ellipse cx="{fmt(x)}" cy="{fmt(t)}" rx="12" ry="3.2" fill="{dk}" {st}/>')
    raise ValueError(kind)


def _slab(p, x0, x1, top, bot):
    body, shade, hi = _rock_tones(p)
    d = (f'M{_pt(x0, bot)} L{_pt(x0 + 5, top + 8)} Q{_pt(x0 + 7, top)} {_pt(x0 + 16, top)} L{_pt(x1 - 16, top)} '
         f'Q{_pt(x1 - 7, top)} {_pt(x1 - 5, top + 8)} L{_pt(x1, bot)} Z')
    mid = (top + bot) / 2 + 2
    return (f'<path d="{d}" fill="{body}"/>'
            f'<path d="M{_pt(x0 + 2, mid)} L{_pt(x1 - 2, mid)} L{_pt(x1, bot)} L{_pt(x0, bot)} Z" fill="{shade}"/>'
            f'<path d="M{_pt(x0 + 14, top + 3.5)} L{_pt(x1 - 40, top + 3.5)}" stroke="{hi}" stroke-width="2.2" stroke-linecap="round"/>'
            + ''.join(f'<ellipse cx="{fmt(x0 + (x1 - x0) * k)}" cy="{fmt(top + (bot - top) * (.45 + .25 * (i % 2)))}" rx="3" ry="1.8" '
                      f'fill="{mix(shade, p["line"], .25)}" fill-opacity=".5"/>' for i, k in enumerate((.12, .27, .55, .7, .88)))
            + f'<path d="{d}" fill="none" {stroke(p)}/>')


def scene_topics(dark=False):
    """30-topics, "Topics": a terraced reef district of thirteen different coral heads, one per topic area, with the
    Diver bot gliding over it."""
    sc = Scene('30-topics', dark, seed=30, avoid=[(300, 810)], rays=6, glow=(560, -30, 400))
    p = sc.p
    tiers = [(452, 668, 142, 172), (382, 738, 170, 200), (318, 802, 198, 226)]
    heads = [
        [('fan', 478, 30, p['violet_lt']), ('brain', 518, 22, p['gold']), ('branch', 562, 44, p['coral']),
         ('table', 606, 30, p['fish_green']), ('seapen', 644, 34, p['violet'])],
        [('tube', 400, 30, p['fish_blue']), ('mushroom', 436, 24, p['pearl']),
         ('softtree', 690, 32, p['fish_red']), ('kelp', 722, 34, p['weed'])],
        [('anemone', 340, 26, None), ('cup', 374, 24, p['violet_lt']),
         ('staghorn', 752, 30, p['fish_blue']), ('barrel', 786, 26, p['gold'])],
    ]
    sc.under.append(sc.far_school(720, 70, 13, n=5, flip=False, seed=1))
    sc.body.append(sc.shadow(560, FLOOR + 1, 250, 6))
    sc.body.append(sc.radial('reefglow', p['glow'], .5 if not dark else .2, .3).join(
        ('<ellipse cx="560" cy="150" rx="260" ry="90" fill="', '"/>')))
    for (x0, x1, top, bot), row in zip(tiers, heads):
        sc.body.append(_slab(p, x0, x1, top, bot))
        for kind, x, h, col in row:
            sc.body.append(coral_head(p, kind, x, top + 2, h * 1.15, col))
    sc.body.append(sc.bubbles(516, 104, 40, 3.4, n=4, seed=4))
    sc.body.append(sc.bot('swim', 232, base=120, height=88))
    sc.body.append(sc.fish(352, 96, 20, 'yellow', flip=True))
    sc.body.append(sc.school(790, 112, 14, 'red', n=3, seed=2))
    sc.over.append(sc.seaweed(30, 118, phase=.4) + sc.seaweed(50, 82, p['weed_light'], width=4, phase=1.9))
    sc.over.append(sc.seaweed(862, 70, p['weed_light'], width=4, phase=2.6))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ crawling
def scene_crawling(dark=False):
    """30-topics-crawling, "Crawling": the Diver bot follows a glowing cable from page to page across the seabed; one
    branch is blocked by a fallen rock with a no-entry marker, and its beads stop."""
    sc = Scene('30-topics-crawling', dark, seed=31, avoid=[(220, 800)], rays=6, glow=(470, -40, 380))
    p = sc.p
    glow_c = '#9cc0ff' if not dark else '#6fa3ff'
    core = p['blue']
    bead = p['gold'] if not dark else p['gold_hi']
    # nodes: (x, rock height, rock width, seed)
    A, B, C, D, E = (292, 16, 46, 1), (424, 44, 54, 2), (600, 66, 60, 3), (756, 24, 48, 4), (530, 8, 36, 5)

    def top(n):
        return FLOOR - n[1]
    start = (26, 212)
    segs = [(start, (A[0], top(A) - 2)), ((A[0], top(A) - 2), (B[0], top(B) - 2)), ((B[0], top(B) - 2), (C[0], top(C) - 2)),
            ((C[0], top(C) - 2), (D[0], top(D) - 2))]
    blocked = ((B[0], top(B) - 2), (E[0], top(E) - 2))

    def ctrl(a, b, sag=14):
        return ((a[0] + b[0]) / 2, max(a[1], b[1]) + sag)
    # shadows and rocks first
    for n in (A, B, C, D):
        sc.body.append(sc.shadow(n[0], FLOOR, n[2] * .62))
    sc.body.append(sc.shadow(150, FLOOR, 36, op=.6))
    for n in (A, B, C, D, E):
        sc.body.append(rock(p, n[0], FLOOR + 2, n[2], n[1] + 2, seed=n[3]))
    # the blocked branch: cable glows up to the fallen rock, then goes dim and dashed
    a, b = blocked
    c = ctrl(a, b, 10)
    cut = .5
    m = _quad(a, c, b, cut)
    c1 = mix_pt(a, c, cut)
    c2 = mix_pt(c, b, cut)
    sc.body.append(f'<path d="M{_pt(*m)} Q{_pt(*c2)} {_pt(*b)}" fill="none" stroke="{p["muted"]}" stroke-width="2.4" '
                   f'stroke-dasharray="2 5" stroke-linecap="round" stroke-opacity=".9"/>')
    sc.body.append(f'<path d="M{_pt(*a)} Q{_pt(*c1)} {_pt(*m)}" fill="none" stroke="{glow_c}" stroke-width="8" '
                   f'stroke-opacity=".35" stroke-linecap="round"/>'
                   f'<path d="M{_pt(*a)} Q{_pt(*c1)} {_pt(*m)}" fill="none" stroke="{core}" stroke-width="2.6" stroke-linecap="round"/>')
    for t in (.14, .3, .4, .47):
        bx, by = _quad(a, c, b, t)
        sc.body.append(f'<circle cx="{fmt(bx)}" cy="{fmt(by)}" r="2.8" fill="{bead}" {stroke(p, .5)}/>')
    # the main trail
    for i, (a, b) in enumerate(segs):
        c = ctrl(a, b, -26 if i == 2 else 14)    # B to C arches up, clear of the blocked branch that dips beneath it
        sc.body.append(f'<path d="M{_pt(*a)} Q{_pt(*c)} {_pt(*b)}" fill="none" stroke="{glow_c}" stroke-width="8" '
                       f'stroke-opacity=".35" stroke-linecap="round"/>'
                       f'<path d="M{_pt(*a)} Q{_pt(*c)} {_pt(*b)}" fill="none" stroke="{core}" stroke-width="2.6" stroke-linecap="round"/>')
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(2, int(L // 34))
        for i in range(1, k):
            bx, by = _quad(a, c, b, i / k)
            sc.body.append(f'<circle cx="{fmt(bx)}" cy="{fmt(by)}" r="2.8" fill="{bead}" {stroke(p, .5)}/>')
    # the fallen rock across the blocked branch
    bm = _quad(blocked[0], ctrl(*blocked, 10), blocked[1], .56)
    sc.body.append(sc.shadow(bm[0], FLOOR, 28, op=.8))
    body, shade, hi = _rock_tones(p)
    fall = (shade, mix(shade, p['line'], .25), body)
    base = min(FLOOR + 1, bm[1] + 13)
    sc.body.append(rock(p, bm[0], base, 60, 32, seed=9, tone=fall))
    sc.body.append(''.join(f'<circle cx="{fmt(bm[0] + dx)}" cy="{fmt(FLOOR + dy)}" r="{fmt(r)}" fill="{fall[1]}" {stroke(p, .6)}/>'
                           for dx, dy, r in ((-35, -2, 3.6), (34, -1, 3), (42, -3, 2))))
    # a no-entry marker wedged in the fallen rock, so the blocked branch reads at README width
    nx, ny = bm[0] + 6, base - 40
    no = oa.PALETTE['verdict_no']
    sc.body.append(f'<path d="M{fmt(nx)},{fmt(ny + 10)} L{fmt(nx + 2)},{fmt(base - 22)}" stroke="{p["metal_dk"]}" stroke-width="2.6" stroke-linecap="round"/>'
                   f'<circle cx="{fmt(nx)}" cy="{fmt(ny)}" r="11" fill="{no}" {stroke(p, .8)}/>'
                   f'<rect x="{fmt(nx - 6.5)}" y="{fmt(ny - 2)}" width="13" height="4" rx="1.5" fill="#ffffff"/>')
    # page-shells on the rocks, the blocked one faded
    shells = [(A, p['pearl'], 0), (B, mix(p['fish_red'], '#ffffff', .62), 1), (C, p['pearl'], 2), (D, mix(p['gold'], '#ffffff', .45), 3)]
    for n, col, i in shells:
        x, t = n[0], top(n)
        sc.body.append(scallop(p, x - 7, t + 1, 34, col))
        sc.body.append(page(p, x + 6, t - 12, 18, 23, lines=2, fold=6, rot=4 - i * 3, ink=INK[('slide', 'docs', 'stage', 'slide')[i]]))
        sc.body.append(f'<circle cx="{fmt(x)}" cy="{fmt(t - 2)}" r="4.2" fill="{p["gold_hi"]}" {stroke(p, .7)}/>')
    x, t = E[0], top(E)
    sc.body.append(page(p, x + 4, t - 11, 18, 22, lines=2, fold=6, rot=-8, op=.6))
    # the bot, its antenna lighting the way
    sc.body.append(glow_dot(sc, 'lamp', 176, 146, 34, p['gold'], .6))
    sc.body.append(sc.bot('swim', 150, base=196, height=84))
    sc.body.append(sc.school(520, 70, 15, 'blue', n=4, seed=2, flip=True))
    sc.body.append(sc.fish(706, 112, 22, 'yellow'))
    sc.over.append(sc.seaweed(28, 112, phase=.8) + sc.seaweed(46, 76, p['weed_light'], width=4, phase=2.2))
    sc.over.append(sc.anemone(836, 15))
    sc.over.append(sc.seaweed(862, 96, p['weed_light'], width=4, phase=2.6))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ indexing
def index_card(p, x, y, w, h, ink, rot=0.0):
    """An index card standing in a drawer: paper with a coloured tab on top."""
    return (f'<g transform="translate({_pt(x, y)}) rotate({fmt(rot)})">'
            f'<rect x="{fmt(-w / 2 + 2)}" y="{fmt(-h / 2 - 5)}" width="{fmt(w * .42)}" height="8" rx="2" fill="{ink}" {stroke(p, .7)}/>'
            f'<rect x="{fmt(-w / 2)}" y="{fmt(-h / 2)}" width="{fmt(w)}" height="{fmt(h)}" rx="2" fill="{p["paper"]}" {stroke(p, .8)}/>'
            f'<path d="M{_pt(-w / 2 + 4, -h / 2 + 6)} L{_pt(w / 2 - 4, -h / 2 + 6)} M{_pt(-w / 2 + 4, -h / 2 + 11)} '
            f'L{_pt(w / 2 - 9, -h / 2 + 11)}" stroke="{p["paper_line"]}" stroke-width="1.6" stroke-linecap="round"/></g>')


def scene_indexing(dark=False):
    """30-topics-indexing, "Indexing": the Diver bot files a card into the open drawer of a coral filing cabinet; two
    matching shells on top, one starred as the original, the other a faint duplicate."""
    sc = Scene('30-topics-indexing', dark, seed=32, avoid=[(420, 640)], rays=6, glow=(540, -30, 380))
    p = sc.p
    cx, x0, x1, top = 522, 458, 586, 86
    if dark:
        body, side, dots, inner = mix(p['coral'], p['pearl'], .5), mix(p['coral'], p['pearl'], .26), mix(p['coral'], p['line'], .25), '#3a2a52'
    else:
        body, side, dots, inner = mix(p['coral'], p['pearl'], .62), mix(p['coral'], p['pearl'], .4), mix(p['coral'], p['line'], .12), '#5b3a5e'
    st = stroke(p)
    sc.under.append(sc.far_school(170, 62, 14, n=5, flip=True, seed=1))
    sc.body.append(sc.shadow(cx, FLOOR, 92))
    sc.body.append(sc.shadow(300, FLOOR, 40))
    sc.body.append(f'<ellipse cx="{cx}" cy="110" rx="150" ry="90" fill="{sc.radial("glow2", p["glow"], .6 if not dark else .18)}"/>')
    shape = (f'M{_pt(x0, FLOOR)} L{_pt(x0, top + 16)} Q{_pt(x0, top)} {_pt(x0 + 16, top)} L{_pt(x1 - 16, top)} '
             f'Q{_pt(x1, top)} {_pt(x1, top + 16)} L{_pt(x1, FLOOR)} Z')
    sc.body.append(f'<path d="{shape}" fill="{body}"/>')
    sc.body.append(f'<path d="M{_pt(x1 - 20, top + 1)} L{_pt(x1 - 16, top)} Q{_pt(x1, top)} {_pt(x1, top + 16)} L{_pt(x1, FLOOR)} '
                   f'L{_pt(x1 - 20, FLOOR)} Z" fill="{side}"/>')
    rnd = oa._rng('b-cab')
    pol = ''.join(f'<circle cx="{fmt(x0 + 6 + rnd.random() * (x1 - x0 - 12))}" cy="{fmt(top + 8 + rnd.random() * (FLOOR - top - 14))}" '
                  f'r="{fmt(1 + rnd.random() * 1.2)}"/>' for _ in range(26))
    sc.body.append(f'<g fill="{dots}" fill-opacity=".6">{pol}</g>')
    sc.body.append(f'<path d="M{_pt(x0 + 10, top + 5)} L{_pt(x0 + 46, top + 5)}" stroke="#ffffff" stroke-opacity=".6" stroke-width="2.4" '
                   f'stroke-linecap="round"/>')
    # closed drawers
    for y0, y1 in ((146, 170), (174, 198), (202, 220)):
        sc.body.append(f'<rect x="{x0 + 9}" y="{y0}" width="{x1 - x0 - 18}" height="{y1 - y0}" rx="4" fill="{body}" {st}/>'
                       f'<rect x="{cx - 11}" y="{fmt(y0 + 5)}" width="22" height="6" rx="1.5" fill="{p["paper"]}" {stroke(p, .6)}/>'
                       f'<rect x="{cx - 9}" y="{fmt(y1 - 9)}" width="18" height="4.6" rx="2.3" fill="{p["gold"]}" {stroke(p, .7)}/>')
    # the open top drawer: dark inside, index cards with tabs, the front pulled forward
    sc.body.append(f'<rect x="{x0 + 9}" y="102" width="{x1 - x0 - 18}" height="26" rx="3" fill="{inner}" {st}/>')
    for i, (lab, h, r) in enumerate((('slide', 22, -3), ('docs', 25, -1), ('stage', 21, 2), ('press', 24, 0), ('analysis', 22, 3))):
        sc.body.append(index_card(p, x0 + 26 + i * 19, 116 - h / 2 + 8, 22, h, INK[lab], r))
    sc.body.append(f'<rect x="{x0 + 3}" y="118" width="{x1 - x0 - 6}" height="24" rx="4" fill="{body}" {st}/>'
                   f'<path d="M{_pt(x0 + 8, 122)} L{_pt(x1 - 8, 122)}" stroke="#ffffff" stroke-opacity=".55" stroke-width="2" stroke-linecap="round"/>'
                   f'<rect x="{cx - 11}" y="124" width="22" height="6" rx="1.5" fill="{p["paper"]}" {stroke(p, .6)}/>'
                   f'<rect x="{cx - 10}" y="133" width="20" height="5" rx="2.5" fill="{p["gold"]}" {stroke(p, .7)}/>')
    sc.body.append(f'<path d="{shape}" fill="none" {st}/>')
    # two matching shells on top: the original wears a gold star, the duplicate is a faint dashed outline
    sc.body.append(scallop(p, 500, top + 1, 34, mix(p['fish_red'], '#ffffff', .6)))
    sc.body.append(scallop(p, 552, top + 1, 34, mix(p['fish_red'], '#ffffff', .6), dashed=True, op=.42))
    sc.body.append(glow_dot(sc, 'starglow', 500, 66, 18, p['gold'], .55))
    sc.body.append(star5(500, 66, 9, p['gold'], p['line']))
    # the card being filed: from the bot's glove, along a dotted arc, into the drawer
    arc = f'M{_pt(332, 172)} Q{_pt(372, 92)} {_pt(452, 104)}'
    sc.body.append(f'<path d="{arc}" fill="none" stroke="{p["blue"]}" stroke-width="2" stroke-dasharray="1 6" stroke-linecap="round" '
                   f'stroke-opacity=".7"/>')
    sc.body.append(index_card(p, 404, 108, 24, 26, INK['slide'], -18))
    sc.body.append(sc.bot('point', 300, FLOOR))
    sc.body.append(sc.bubbles(612, 96, 44, 3.6, n=4, seed=3))
    sc.body.append(sc.school(714, 66, 18, 'yellow', n=4, seed=2))
    sc.body.append(sc.fish(178, 108, 24, 'green', flip=True))
    _edge_dressing(sc)
    sc.over.append(sc.anemone(746, 15))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ rendering
def brace(x, y, h, color, right=False, w=3.4):
    """A curly brace drawn as a stroke (not a glyph), centred at (x, y), h tall."""
    m = -1 if right else 1
    k = h / 2

    def X(dx):
        return x + m * dx
    d = (f'M{_pt(X(6), y - k)} Q{_pt(X(-1), y - k)} {_pt(X(-1), y - k * .55)} L{_pt(X(-1), y - k * .22)} '
         f'Q{_pt(X(-1), y)} {_pt(X(-7), y)} Q{_pt(X(-1), y)} {_pt(X(-1), y + k * .22)} L{_pt(X(-1), y + k * .55)} '
         f'Q{_pt(X(-1), y + k)} {_pt(X(6), y + k)}')
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{fmt(w)}" stroke-linecap="round" stroke-linejoin="round"/>'


def scene_rendering(dark=False):
    """30-topics-rendering-javascript, "Rendering and JavaScript": under a hanging lamp, the Diver bot guides floating
    blocks into an empty page frame on a stand; two brace shapes drift by like little jellyfish."""
    sc = Scene('30-topics-rendering-javascript', dark, seed=33, avoid=[(430, 690)], rays=5, glow=(560, -40, 360))
    p = sc.p
    st = stroke(p)
    fx0, fx1, fy0, fy1 = 474, 650, 64, 184
    lamp = (562, 40)
    slot = (f'fill="none" stroke="{p["paper_line"]}" stroke-width="1.5" stroke-dasharray="3 3"')
    # lamp: a curved angler rod from the surface, a glowing bulb, a soft cone of light over the frame
    sc.defs.append(f'<linearGradient id="{sc.id("conef")}" x1="0" y1="0" x2="0" y2="1">'
                   f'<stop offset="0" stop-color="{p["gold_hi"]}" stop-opacity="{".6" if not dark else ".32"}"/>'
                   f'<stop offset="1" stop-color="{p["gold_hi"]}" stop-opacity="0"/></linearGradient>')
    sc.body.append(f'<path d="M{_pt(lamp[0] - 8, lamp[1] + 4)} L{_pt(lamp[0] + 8, lamp[1] + 4)} L{_pt(694, 212)} L{_pt(430, 212)} Z" '
                   f'fill="url(#{sc.id("conef")})"/>')
    sc.body.append(sc.shadow((fx0 + fx1) / 2, FLOOR, 100))
    sc.body.append(sc.shadow(300, FLOOR, 40))
    # easel stand
    leg = mix(p['wood'], p['wood_dk'], .3)
    sc.body.append(f'<path d="M{_pt(522, fy1 - 4)} L{_pt(500, FLOOR)} M{_pt(602, fy1 - 4)} L{_pt(624, FLOOR)}" stroke="{p["line"]}" '
                   f'stroke-width="8.6" stroke-linecap="round"/>'
                   f'<path d="M{_pt(522, fy1 - 4)} L{_pt(500, FLOOR)} M{_pt(602, fy1 - 4)} L{_pt(624, FLOOR)}" stroke="{leg}" '
                   f'stroke-width="5.4" stroke-linecap="round"/>'
                   f'<rect x="504" y="204" width="116" height="6" rx="3" fill="{p["wood"]}" {st}/>')
    # the page frame
    sc.body.append(f'<rect x="{fx0}" y="{fy0}" width="{fx1 - fx0}" height="{fy1 - fy0}" rx="8" fill="{p["paper"]}" {st}/>'
                   f'<path d="M{_pt(fx0, fy0 + 15)} L{_pt(fx0, fy0 + 8)} Q{_pt(fx0, fy0)} {_pt(fx0 + 8, fy0)} L{_pt(fx1 - 8, fy0)} '
                   f'Q{_pt(fx1, fy0)} {_pt(fx1, fy0 + 8)} L{_pt(fx1, fy0 + 15)} Z" fill="{p["paper_sh"]}"/>'
                   + ''.join(f'<circle cx="{fx0 + 11 + i * 9}" cy="{fy0 + 7.5}" r="2.6" fill="{p["blue"]}" fill-opacity="{fmt(1 - i * .25, 2)}"/>'
                             for i in range(3))
                   + f'<path d="M{_pt(fx0, fy0 + 15)} L{_pt(fx1, fy0 + 15)}" {stroke(p, .8)}/>')
    # blocks already in place: header bar and three text lines
    sc.body.append(f'<rect x="{fx0 + 12}" y="{fy0 + 24}" width="{fx1 - fx0 - 24}" height="12" rx="3" fill="{INK["slide"]}"/>'
                   f'<path d="M{_pt(fx0 + 20, fy0 + 30)} L{_pt(fx0 + 64, fy0 + 30)}" stroke="#ffffff" stroke-opacity=".75" stroke-width="2.4" '
                   f'stroke-linecap="round"/>')
    for i, w in enumerate((76, 70, 52)):
        y = fy0 + 48 + i * 11
        sc.body.append(f'<path d="M{_pt(fx0 + 14, y)} L{_pt(fx0 + 14 + w, y)}" stroke="{p["paper_line"]}" stroke-width="5" stroke-linecap="round"/>')
    # empty slots: one text line, a button, the image
    sc.body.append(f'<rect x="{fx0 + 11}" y="{fy0 + 78}" width="76" height="8" rx="4" {slot}/>'
                   f'<rect x="{fx0 + 11}" y="{fy0 + 96}" width="48" height="16" rx="8" {slot}/>'
                   f'<rect x="{fx0 + 100}" y="{fy0 + 44}" width="64" height="64" rx="5" {slot}/>')
    # image block drifting in from the right
    ix, iy = 690, 110
    sc.body.append(f'<g transform="translate({_pt(ix, iy)}) rotate(9)">'
                   f'<rect x="-32" y="-30" width="64" height="60" rx="5" fill="{p["glass"]}" {st}/>'
                   f'<circle cx="12" cy="-12" r="7" fill="{p["gold"]}"/>'
                   f'<path d="M-28,26 L-10,0 L2,14 L12,4 L28,26 Z" fill="{p["fish_blue"]}"/>'
                   f'<path d="M-28,26 L-10,0 L2,14" fill="none" stroke="{mix(p["fish_blue"], p["line"], .35)}" stroke-width="1.6" '
                   f'stroke-linejoin="round"/>'
                   f'<rect x="-32" y="-30" width="64" height="60" rx="5" fill="none" {st}/></g>')
    sc.body.append(''.join(f'<circle cx="{fmt(ix + 42 + i * 11)}" cy="{fmt(iy + 10 + i * 3)}" r="{fmt(2.4 - i * .6)}" fill="{p["blue"]}" '
                           f'fill-opacity=".45"/>' for i in range(3)))
    # the button block guided by the bot
    bx, by = 362, 162
    sc.body.append(f'<path d="M{_pt(bx + 30, by - 8)} Q{_pt(430, 140)} {_pt(fx0 + 10, fy0 + 108)}" fill="none" stroke="{p["violet"]}" '
                   f'stroke-width="2" stroke-dasharray="1 6" stroke-linecap="round" stroke-opacity=".75"/>')
    sc.body.append(f'<g transform="translate({_pt(bx, by)}) rotate(-8)">'
                   f'<rect x="-25" y="-9" width="50" height="18" rx="9" fill="{INK["stage"]}" {st}/>'
                   f'<path d="M-12,0 L12,0" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round"/></g>')
    # floating text-line block
    sc.body.append(f'<g transform="translate({_pt(424, 96)}) rotate(6)">'
                   f'<rect x="-30" y="-7" width="60" height="14" rx="7" fill="{p["paper"]}" {st}/>'
                   f'<path d="M-22,0 L18,0" stroke="{p["paper_line"]}" stroke-width="4" stroke-linecap="round"/></g>')
    # braces drifting like small jellyfish
    bcol = p['violet']
    for x, y, h, right, rot in ((406, 50, 34, False, -10), (722, 52, 30, True, 12)):
        sc.body.append(f'<g transform="rotate({rot} {_pt(x, y)})">' + glow_dot(sc, f'jg{x}', x, y, 22, p['violet_lt'], .4)
                       + brace(x, y, h, bcol, right) + '</g>')
    # the angler lamp
    sc.body.append(f'<path d="M{_pt(470, 8)} Q{_pt(540, 6)} {_pt(lamp[0], lamp[1] - 7)}" fill="none" stroke="{p["line"]}" '
                   f'stroke-width="3" stroke-linecap="round"/>')
    sc.body.append(glow_dot(sc, 'lampglow', lamp[0], lamp[1], 34, p['gold'], .75))
    sc.body.append(f'<circle cx="{fmt(lamp[0])}" cy="{fmt(lamp[1])}" r="8" fill="{p["gold"]}" {st}/>'
                   f'<circle cx="{fmt(lamp[0] - 2)}" cy="{fmt(lamp[1] - 2)}" r="3.6" fill="#fff6d6"/>')
    sc.body.append(sc.bot('point', 300, FLOOR))
    sc.body.append(sc.school(200, 66, 16, 'blue', n=4, seed=2, flip=True))
    _edge_dressing(sc, coral_x=812)
    sc.over.append(sc.anemone(760, 15))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ how search works
def _pipe(p, x0, x1, y, r=7):
    """A horizontal metal pipe from x0 to x1 centred on y."""
    return (f'<rect x="{fmt(x0)}" y="{fmt(y - r)}" width="{fmt(x1 - x0)}" height="{fmt(2 * r)}" fill="{p["metal"]}"/>'
            f'<rect x="{fmt(x0)}" y="{fmt(y + r * .25)}" width="{fmt(x1 - x0)}" height="{fmt(r * .75)}" fill="{p["metal_dk"]}"/>'
            f'<path d="M{_pt(x0 + 2, y - r * .45)} L{_pt(x1 - 2, y - r * .45)}" stroke="{p["metal_hi"]}" stroke-width="2" stroke-linecap="round"/>'
            f'<path d="M{_pt(x0, y - r)} L{_pt(x1, y - r)} M{_pt(x0, y + r)} L{_pt(x1, y + r)}" {stroke(p)}/>')


def _collar(p, x, y, r=7):
    return (f'<rect x="{fmt(x - 4)}" y="{fmt(y - r - 3)}" width="8" height="{fmt(2 * r + 6)}" rx="2" fill="{p["gold"]}" {stroke(p)}/>'
            f'<path d="M{_pt(x - 1.5, y - r - 1)} L{_pt(x - 1.5, y + r + 1)}" stroke="{p["gold_hi"]}" stroke-width="1.6"/>')


def _flow(p, x, y):
    """A flow arrow made of bubble dots on a pipe (a chevron pointing right)."""
    return ''.join(f'<circle cx="{fmt(x + dx)}" cy="{fmt(y + dy)}" r="1.6" fill="#ffffff" fill-opacity=".9"/>'
                   for dx, dy in ((-4, -4), (0, 0), (-4, 4), (-9, -4), (-5, 0), (-9, 4))[:3])


def scene_pipeline(dark=False):
    """30-topics-how-search-works, "How Search works": one pipeline across the seabed: an intake funnel swallowing small
    URL fish, a processing chamber with a turning gear, a tall index tank of stacked cards, an outlet releasing result
    bubbles; the Diver bot rides along above."""
    sc = Scene('30-topics-how-search-works', dark, seed=34, avoid=[(60, 800)], rays=6, glow=(500, -40, 400))
    p = sc.p
    st = stroke(p)
    py = 198
    sc.under.append(sc.far_school(400, 58, 13, n=4, flip=True, seed=1))
    for x, r in ((100, 40), (290, 52), (496, 64), (650, 26)):
        sc.body.append(sc.shadow(x, FLOOR, r))
    # pipes and joints
    for x0, x1 in ((124, 248), (332, 446), (546, 640)):
        sc.body.append(_pipe(p, x0, x1, py))
    # intake funnel, mouth to the left
    sc.body.append(f'<path d="M{_pt(70, 150)} Q{_pt(84, 186)} {_pt(124, py - 7)} L{_pt(124, py + 7)} Q{_pt(84, 210)} {_pt(70, 224)} Z" '
                   f'fill="{p["metal"]}" {st}/>'
                   f'<path d="M{_pt(76, 196)} Q{_pt(92, 206)} {_pt(122, py + 5)} L{_pt(76, 220)} Z" fill="{p["metal_dk"]}" fill-opacity=".6"/>'
                   f'<ellipse cx="70" cy="187" rx="9" ry="37" fill="{mix(p["metal_dk"], p["line"], .45)}" {st}/>'
                   f'<path d="M73,156 Q78,170 77,184" stroke="{p["metal_hi"]}" stroke-width="2" stroke-linecap="round" fill="none"/>'
                   + _collar(p, 126, py))
    for x, y, c in ((44, 160, 'red'), (36, 186, 'yellow'), (48, 210, 'red')):
        sc.body.append(sc.fish(x, y, 15, c, flip=True))
    # processing chamber with a porthole and a gear
    cx, cy, r = 290, 176, 42
    sc.body.append(f'<path d="M{_pt(262, 210)} L{_pt(256, FLOOR)} M{_pt(318, 210)} L{_pt(324, FLOOR)}" stroke="{p["line"]}" '
                   f'stroke-width="7.6" stroke-linecap="round"/>'
                   f'<path d="M{_pt(262, 210)} L{_pt(256, FLOOR)} M{_pt(318, 210)} L{_pt(324, FLOOR)}" stroke="{p["metal_dk"]}" '
                   f'stroke-width="4.4" stroke-linecap="round"/>')
    sc.body.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{p["metal_dk"]}"/>'
                   f'<circle cx="{cx - 5}" cy="{cy - 5}" r="{r - 6}" fill="{p["metal"]}"/>'
                   f'<path d="M{_pt(cx - 30, cy - 18)} Q{_pt(cx - 22, cy - 32)} {_pt(cx - 6, cy - 36)}" stroke="{p["metal_hi"]}" '
                   f'stroke-width="3" stroke-linecap="round" fill="none"/>'
                   f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" {st}/>'
                   + ''.join(f'<circle cx="{fmt(cx + math.cos(a) * (r - 5))}" cy="{fmt(cy + math.sin(a) * (r - 5))}" r="1.8" fill="{p["metal_dk"]}"/>'
                             for a in [math.radians(20 + 45 * i) for i in range(8)])
                   + f'<circle cx="{cx}" cy="{cy}" r="23" fill="{p["gold"]}" {st}/>'
                   f'<circle cx="{cx}" cy="{cy}" r="18" fill="{p["glass_dk"] if not dark else "#1a3a7a"}" {st}/>'
                   + gear(cx, cy, 13, 8, p['gold_dk'] if not dark else p['gold'], p['glass_dk'] if not dark else '#1a3a7a')
                   + f'<path d="M{_pt(cx - 11, cy - 4)} A12,12 0 0 1 {_pt(cx - 2, cy - 12)}" stroke="#ffffff" stroke-opacity=".7" '
                   f'stroke-width="2" fill="none" stroke-linecap="round"/>')
    sc.body.append(_collar(p, 250, py) + _collar(p, 330, py))
    # index tank: glass with stacked cards
    tx0, tx1, ty0 = 448, 546, 84
    sc.body.append(f'<rect x="{tx0}" y="{ty0}" width="{tx1 - tx0}" height="{FLOOR - 6 - ty0}" rx="6" fill="{p["glass"]}" '
                   f'fill-opacity="{".9" if not dark else ".85"}"/>'
                   f'<rect x="{tx0 + 4}" y="{ty0 + 18}" width="{tx1 - tx0 - 8}" height="{FLOOR - 28 - ty0}" fill="{p["glass_dk"]}" fill-opacity=".45"/>'
                   f'<path d="M{_pt(tx0 + 4, ty0 + 18)} q12,-3 22,0 t22,0 t22,0 t22,0" stroke="{p["blue"]}" stroke-width="1.6" '
                   f'fill="none" stroke-opacity=".6"/>')
    # one cool family of tab colours (blue, violet, pale blue): a grid of mixed red / green / blue / yellow tabs would read as a
    # four-colour logo set, which the brand rules forbid
    tabs = (INK['slide'], INK['stage'], mix(INK['slide'], '#ffffff', .45))
    for col in range(3):
        for row in range(6):
            x = tx0 + 10 + col * 28
            y = FLOOR - 22 - row * 15
            if col == 1 and row == 5:
                continue
            ink = tabs[(row + col) % 3]
            sc.body.append(f'<rect x="{x}" y="{y}" width="24" height="12" rx="2" fill="{p["paper"]}" {stroke(p, .7)}/>'
                           f'<rect x="{x + 2}" y="{y + 2}" width="5" height="8" rx="1" fill="{ink}"/>'
                           f'<path d="M{_pt(x + 10, y + 6)} L{_pt(x + 20, y + 6)}" stroke="{p["paper_line"]}" stroke-width="1.6" stroke-linecap="round"/>')
    sc.body.append(f'<path d="M{_pt(tx0 + 8, ty0 + 24)} L{_pt(tx0 + 8, FLOOR - 16)}" stroke="#ffffff" stroke-opacity=".7" stroke-width="3" '
                   f'stroke-linecap="round"/>'
                   f'<rect x="{tx0}" y="{ty0}" width="{tx1 - tx0}" height="{FLOOR - 6 - ty0}" rx="6" fill="none" {st}/>'
                   f'<rect x="{tx0 - 6}" y="{ty0 - 8}" width="{tx1 - tx0 + 12}" height="12" rx="4" fill="{p["metal"]}" {st}/>'
                   f'<path d="M{_pt(tx0 + 36, ty0 - 8)} q0,-8 7,-8 h14 q7,0 7,8" fill="none" stroke="{p["gold"]}" stroke-width="4" stroke-linecap="round"/>'
                   f'<rect x="{tx0 - 6}" y="{FLOOR - 10}" width="{tx1 - tx0 + 12}" height="10" rx="3" fill="{p["metal_dk"]}" {st}/>')
    sc.body.append(_collar(p, 444, py) + _collar(p, 550, py))
    # outlet: elbow up and a nozzle, releasing result bubbles in a neat line
    sc.body.append(f'<path d="M{_pt(632, py - 7)} Q{_pt(652, py - 7)} {_pt(652, py - 27)} L{_pt(666, py - 27)} Q{_pt(666, py + 7)} {_pt(632, py + 7)} Z" '
                   f'fill="{p["metal"]}" {st}/>'
                   f'<path d="M{_pt(648, py - 27)} L{_pt(644, py - 44)} L{_pt(674, py - 44)} L{_pt(670, py - 27)} Z" fill="{p["metal_dk"]}" {st}/>'
                   f'<rect x="642" y="{py - 48}" width="34" height="6" rx="2" fill="{p["gold"]}" {st}/>')
    for i in range(4):
        bx, by = 668 + i * 30, 132 - i * 28
        r = 12
        sc.body.append(sc.bubble(bx, by, r)
                       + f'<circle cx="{fmt(bx - 5.5)}" cy="{fmt(by)}" r="2.6" fill="{(INK["stage"], INK["slide"])[i % 2]}"/>'
                       f'<path d="M{_pt(bx - 1, by - 2.5)} L{_pt(bx + 7, by - 2.5)}" stroke="{INK["slide"]}" stroke-width="2.2" stroke-linecap="round"/>'
                       f'<path d="M{_pt(bx - 1, by + 3)} L{_pt(bx + 4, by + 3)}" stroke="{p["paper_line"]}" stroke-width="2" stroke-linecap="round"/>')
    sc.body.append(sc.bubble(660, 140, 3) + sc.bubble(652, 128, 2))
    for x in (192, 400, 600):
        sc.body.append(_flow(p, x, py))
    sc.body.append(sc.bot('swim', 214, base=128, height=80))
    sc.body.append(sc.school(380, 92, 14, 'yellow', n=3, seed=3, flip=True))
    sc.over.append(sc.coral(834, .34))
    sc.over.append(sc.seaweed(862, 96, p['weed_light'], width=4, phase=2.6))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ index and signals
def buoy(p, x, y, r, color, tether_to=None):
    """A round signal buoy with a band and a little light on top, on a short tether to the seabed."""
    dk = mix(color, p['line'], .3)
    out = ''
    if tether_to is not None:
        out += (f'<path d="M{_pt(x, y + r)} Q{_pt(x + 4, (y + tether_to) / 2)} {_pt(x, tether_to)}" fill="none" stroke="{p["line"]}" '
                f'stroke-width="1.3" stroke-opacity=".7"/>'
                f'<rect x="{fmt(x - 5)}" y="{fmt(tether_to - 3)}" width="10" height="5" rx="1.5" fill="{p["metal_dk"]}" {stroke(p, .7)}/>')
    out += (f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{color}" {stroke(p)}/>'
            f'<path d="M{_pt(x - r, y + 1)} Q{_pt(x, y + r * .45)} {_pt(x + r, y + 1)}" fill="none" stroke="{p["pearl"]}" stroke-width="3.2"/>'
            f'<path d="M{_pt(x + r * .2, y + r * .9)} A{fmt(r)},{fmt(r)} 0 0 0 {_pt(x + r * .95, y + r * .2)}" fill="none" stroke="{dk}" '
            f'stroke-width="2.4" stroke-opacity=".6"/>'
            f'<circle cx="{fmt(x - r * .38)}" cy="{fmt(y - r * .4)}" r="{fmt(r * .22)}" fill="#ffffff" fill-opacity=".85"/>'
            f'<rect x="{fmt(x - 2)}" y="{fmt(y - r - 5)}" width="4" height="6" fill="{p["metal_dk"]}"/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y - r - 6.5)}" r="2.8" fill="{p["gold_hi"]}" {stroke(p, .6)}/>')
    return out


def scene_signals(dark=False):
    """30-topics-index-and-signals, "The index and its signals": a beacon tower of stacked rock with white and blue bands
    rises from behind the hills and sends rings of light to signal buoys; the Diver bot sits at the right reading them."""
    sc = Scene('30-topics-index-and-signals', dark, seed=35, avoid=[(330, 470)], rays=5, glow=(400, -20, 360))
    p = sc.p
    st = stroke(p)
    tx, lamp_y = 400, 74
    # beams and rings first, behind the tower
    sc.defs.append(f'<linearGradient id="{sc.id("beamL")}" x1="1" y1="0" x2="0" y2="0">'
                   f'<stop offset="0" stop-color="{p["gold_hi"]}" stop-opacity="{".75" if not dark else ".45"}"/>'
                   f'<stop offset="1" stop-color="{p["gold_hi"]}" stop-opacity="0"/></linearGradient>'
                   f'<linearGradient id="{sc.id("beamR")}" x1="0" y1="0" x2="1" y2="0">'
                   f'<stop offset="0" stop-color="{p["gold_hi"]}" stop-opacity="{".75" if not dark else ".45"}"/>'
                   f'<stop offset="1" stop-color="{p["gold_hi"]}" stop-opacity="0"/></linearGradient>')
    sc.under.append(f'<path d="M{_pt(tx, lamp_y - 5)} L{_pt(tx - 260, lamp_y - 38)} L{_pt(tx - 260, lamp_y + 30)} L{_pt(tx, lamp_y + 5)} Z" '
                    f'fill="url(#{sc.id("beamL")})"/>'
                    f'<path d="M{_pt(tx, lamp_y - 5)} L{_pt(tx + 280, lamp_y - 30)} L{_pt(tx + 280, lamp_y + 40)} L{_pt(tx, lamp_y + 5)} Z" '
                    f'fill="url(#{sc.id("beamR")})"/>')
    ring = p['gold'] if not dark else p['gold_hi']
    for i, rr in enumerate((44, 72, 100, 128)):
        op = .85 - i * .18
        for a0, a1 in ((-38, 38), (142, 218)):
            x0, y0 = tx + rr * math.cos(math.radians(a0)), lamp_y + rr * math.sin(math.radians(a0))
            x1, y1 = tx + rr * math.cos(math.radians(a1)), lamp_y + rr * math.sin(math.radians(a1))
            sc.under.append(f'<path d="M{_pt(x0, y0)} A{rr},{rr} 0 0 1 {_pt(x1, y1)}" fill="none" stroke="{ring}" '
                            f'stroke-width="{fmt(2.6 - i * .35)}" stroke-opacity="{fmt(op, 2)}" stroke-linecap="round"/>')
    sc.under.append(glow_dot(sc, 'lampglow', tx, lamp_y, 64, p['gold'], .7 if not dark else .55))
    # the tower: tapered, stacked rock courses in white and blue bands
    base_y, top_y = 200, 92
    hb, ht = 34, 22

    def half(y):
        return ht + (hb - ht) * (y - top_y) / (base_y - top_y)
    bands = 5
    for i in range(bands):
        y0 = top_y + (base_y - top_y) * i / bands
        y1 = top_y + (base_y - top_y) * (i + 1) / bands
        col = p['pearl'] if i % 2 == 0 else (p['blue'] if not dark else '#3f7fe8')
        sh = p['pearl_sh'] if i % 2 == 0 else mix(col, p['line'], .3)
        sc.under.append(f'<path d="M{_pt(tx - half(y0), y0)} L{_pt(tx + half(y0), y0)} L{_pt(tx + half(y1), y1)} L{_pt(tx - half(y1), y1)} Z" '
                        f'fill="{col}"/>'
                        f'<path d="M{_pt(tx + half(y0) * .45, y0)} L{_pt(tx + half(y0), y0)} L{_pt(tx + half(y1), y1)} L{_pt(tx + half(y1) * .45, y1)} Z" '
                        f'fill="{sh}"/>')
        # stone joints
        ym = (y0 + y1) / 2
        jx = [-.5, .1, .6] if i % 2 == 0 else [-.2, .35]
        sc.under.append(f'<path d="M{_pt(tx - half(ym), ym)} L{_pt(tx + half(ym), ym)} '
                        + ' '.join(f'M{_pt(tx + k * half(y0), y0 + 1)} L{_pt(tx + k * half(ym), ym)}' for k in jx)
                        + ' '.join(f' M{_pt(tx + (k + .25) * half(ym), ym)} L{_pt(tx + (k + .25) * half(y1), y1 - 1)}' for k in jx[:-1])
                        + f'" stroke="{mix(col, p["line"], .25)}" stroke-width="1.1" stroke-opacity=".55"/>')
    sc.under.append(f'<path d="M{_pt(tx - ht, top_y)} L{_pt(tx + ht, top_y)} L{_pt(tx + hb, base_y)} L{_pt(tx - hb, base_y)} Z" fill="none" {st}/>')
    # door and window
    sc.under.append(f'<path d="M{_pt(tx - 7, 170)} Q{_pt(tx, 160)} {_pt(tx + 7, 170)} L{_pt(tx + 7, 182)} L{_pt(tx - 7, 182)} Z" '
                    f'fill="{mix(p["line"], p["blue"], .2)}" {stroke(p, .8)}/>'
                    f'<rect x="{tx - 4}" y="120" width="8" height="11" rx="4" fill="{p["gold_hi"]}" {stroke(p, .8)}/>')
    # gallery, lamp room, roof
    sc.under.append(f'<rect x="{tx - 32}" y="{top_y - 6}" width="64" height="8" rx="3" fill="{p["metal"]}" {st}/>'
                    f'<path d="M{_pt(tx - 30, top_y - 6)} L{_pt(tx - 30, top_y - 13)} L{_pt(tx + 30, top_y - 13)} L{_pt(tx + 30, top_y - 6)}'
                    + ''.join(f' M{_pt(tx - 30 + k * 10, top_y - 13)} L{_pt(tx - 30 + k * 10, top_y - 6)}' for k in range(1, 6))
                    + f'" fill="none" stroke="{p["line"]}" stroke-width="1.4"/>'
                    f'<rect x="{tx - 16}" y="{lamp_y - 12}" width="32" height="22" rx="3" fill="{p["gold"]}" {st}/>'
                    f'<rect x="{tx - 11}" y="{lamp_y - 8}" width="22" height="14" rx="2" fill="#fff4c8"/>'
                    f'<path d="M{_pt(tx - 4, lamp_y - 12)} L{_pt(tx - 4, lamp_y + 10)} M{_pt(tx + 4, lamp_y - 12)} L{_pt(tx + 4, lamp_y + 10)}" '
                    f'stroke="{p["gold_dk"]}" stroke-width="1.6"/>'
                    f'<path d="M{_pt(tx - 22, lamp_y - 11)} Q{_pt(tx - 18, lamp_y - 34)} {_pt(tx, lamp_y - 36)} Q{_pt(tx + 18, lamp_y - 34)} '
                    f'{_pt(tx + 22, lamp_y - 11)} Z" fill="{INK["slide"]}" {st}/>'
                    f'<path d="M{_pt(tx - 10, lamp_y - 20)} Q{_pt(tx - 7, lamp_y - 29)} {_pt(tx, lamp_y - 30)}" stroke="#ffffff" stroke-opacity=".5" '
                    f'stroke-width="2" fill="none" stroke-linecap="round"/>'
                    f'<circle cx="{tx}" cy="{lamp_y - 39}" r="3.6" fill="{p["gold"]}" {st}/>')
    # buoys on tethers, each catching the signal
    for x, y, r, col in ((236, 110, 12, p['fish_blue']), (290, 160, 10, p['violet_lt']), (526, 118, 12, p['weed_light']),
                         (580, 166, 10, p['coral'])):
        sc.body.append(sc.shadow(x, FLOOR, 8, op=.6))
        sc.body.append(buoy(p, x, y, r, col, tether_to=FLOOR - 2))
    # the bot, reading the signals on a rock at the right
    sc.body.append(sc.shadow(690, FLOOR, 56))
    sc.body.append(rock(p, 690, FLOOR + 2, 96, 30, seed=3))
    sc.body.append(sc.bot('read', 688, base=FLOOR - 24, height=100, flip=True))
    sc.body.append(sc.school(160, 70, 15, 'yellow', n=4, seed=2, flip=True))
    sc.over.append(sc.seaweed(30, 116, phase=.4) + sc.seaweed(50, 80, p['weed_light'], width=4, phase=1.9))
    sc.over.append(sc.anemone(800, 16))
    sc.over.append(sc.coral(842, .36))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ content and media
def frame(p, x, y, w, h, rot, inner):
    """A floating picture frame: paper border, `inner` drawn in a local box (-w/2..w/2, -h/2..h/2) inset by 4."""
    return (f'<g transform="translate({_pt(x, y)}) rotate({fmt(rot)})">'
            f'<rect x="{fmt(-w / 2)}" y="{fmt(-h / 2)}" width="{fmt(w)}" height="{fmt(h)}" rx="4" fill="{p["paper"]}" {stroke(p)}/>'
            + inner +
            f'<rect x="{fmt(-w / 2 + 4)}" y="{fmt(-h / 2 + 4)}" width="{fmt(w - 8)}" height="{fmt(h - 8)}" rx="2" fill="none" {stroke(p, .6)}/>'
            '</g>')


def _photo(p, w, h, sun=True):
    x0, y0, x1, y1 = -w / 2 + 4, -h / 2 + 4, w / 2 - 4, h / 2 - 4
    hill = mix(p['fish_blue'], p['line'], .15)
    return (f'<rect x="{fmt(x0)}" y="{fmt(y0)}" width="{fmt(x1 - x0)}" height="{fmt(y1 - y0)}" rx="2" fill="{p["glass_dk"]}"/>'
            + (f'<circle cx="{fmt(x1 - (x1 - x0) * .28)}" cy="{fmt(y0 + (y1 - y0) * .3)}" r="{fmt((y1 - y0) * .14)}" fill="{p["gold"]}"/>' if sun else '')
            + f'<path d="M{_pt(x0, y1)} L{_pt(x0 + (x1 - x0) * .3, y0 + (y1 - y0) * .42)} L{_pt(x0 + (x1 - x0) * .5, y0 + (y1 - y0) * .7)} '
            f'L{_pt(x0 + (x1 - x0) * .68, y0 + (y1 - y0) * .5)} L{_pt(x1, y1)} Z" fill="{hill}"/>')


def scene_media(dark=False):
    """30-topics-content-and-media, "Structured data and media": the Diver bot works an underwater camera on a tripod,
    beside floating photo and video frames tied together by a lattice of pearls."""
    sc = Scene('30-topics-content-and-media', dark, seed=36, avoid=[(330, 700)], rays=6, glow=(580, -40, 380))
    p = sc.p
    st = stroke(p)
    sc.under.append(sc.far_school(200, 62, 14, n=4, flip=True, seed=1))
    # camera viewing cone towards the frames
    sc.defs.append(f'<linearGradient id="{sc.id("view")}" x1="0" y1="0" x2="1" y2="0">'
                   f'<stop offset="0" stop-color="{p["glow"]}" stop-opacity="{".9" if not dark else ".35"}"/>'
                   f'<stop offset="1" stop-color="{p["glow"]}" stop-opacity="0"/></linearGradient>')
    sc.body.append(f'<path d="M{_pt(420, 162)} L{_pt(640, 70)} L{_pt(660, 190)} L{_pt(420, 172)} Z" fill="url(#{sc.id("view")})"/>')
    sc.body.append(sc.shadow(362, FLOOR, 46))
    sc.body.append(sc.shadow(300, FLOOR, 36))
    # lattice: a small tree of pearls joining the frames
    root = (580, 42)
    pins = [(486, 72), (580, 84), (668, 50), (680, 108)]
    lc = p['blue'] if not dark else p['blue_deep']
    sc.body.append(f'<path d="' + ' '.join(f'M{_pt(*root)} L{_pt(*q)}' for q in pins) + f' M{_pt(*pins[2])} L{_pt(*pins[3])}" '
                   f'stroke="{lc}" stroke-width="1.6" stroke-opacity=".75" stroke-linecap="round"/>')
    # frames
    sc.body.append(frame(p, 486, 100, 60, 48, -8, _photo(p, 60, 48)))
    vw, vh = 96, 64
    screen = mix(INK['slide'], p['line'], .35)
    sc.body.append(frame(p, 580, 118, vw, vh, 0,
                         f'<rect x="{fmt(-vw / 2 + 4)}" y="{fmt(-vh / 2 + 4)}" width="{vw - 8}" height="{vh - 8}" rx="2" fill="{screen}"/>'
                         f'<circle cx="0" cy="-4" r="15" fill="#ffffff" fill-opacity=".16"/>'
                         f'<path d="M-6,-13 L10,-4 L-6,5 Z" fill="#ffffff" stroke="#ffffff" stroke-width="2" stroke-linejoin="round"/>'
                         f'<path d="M-36,19 L36,19" stroke="#ffffff" stroke-opacity=".35" stroke-width="3" stroke-linecap="round"/>'
                         f'<path d="M-36,19 L-8,19" stroke="{p["gold"]}" stroke-width="3" stroke-linecap="round"/>'
                         f'<circle cx="-8" cy="19" r="3.4" fill="#ffffff"/>'))
    sc.body.append(frame(p, 668, 66, 40, 32, 7, _photo(p, 40, 32, sun=False)))
    cw, ch = 44, 54
    sc.body.append(f'<g transform="translate({_pt(682, 134)}) rotate(8)">'
                   f'<rect x="{-cw / 2}" y="{-ch / 2}" width="{cw}" height="{ch}" rx="4" fill="{p["paper"]}" {st}/>'
                   f'<g transform="translate(0,-8)">{_photo(p, cw, 30)}</g>'
                   f'<path d="M-15,14 L15,14 M-15,20 L7,20" stroke="{p["paper_line"]}" stroke-width="2" stroke-linecap="round"/></g>')
    # pearls on the nodes
    tints = ('slide', 'stage', 'docs', 'press')
    sc.body.append(pearl(p, root[0], root[1], 7.5, tint=mix(INK['analysis'], '#ffffff', .55)))
    for q, t in zip(pins, tints):
        sc.body.append(pearl(p, q[0], q[1], 5.2, tint=mix(INK[t], '#ffffff', .6)))
    # the camera on its tripod, the bot holding its side grip
    leg = p['metal_dk']
    sc.body.append(f'<path d="M{_pt(362, 192)} L{_pt(334, FLOOR)} M{_pt(362, 192)} L{_pt(392, FLOOR)} M{_pt(362, 192)} L{_pt(364, FLOOR - 4)}" '
                   f'stroke="{p["line"]}" stroke-width="5.6" stroke-linecap="round"/>'
                   f'<path d="M{_pt(362, 192)} L{_pt(334, FLOOR)} M{_pt(362, 192)} L{_pt(392, FLOOR)} M{_pt(362, 192)} L{_pt(364, FLOOR - 4)}" '
                   f'stroke="{leg}" stroke-width="2.8" stroke-linecap="round"/>'
                   f'<rect x="352" y="186" width="20" height="8" rx="2" fill="{p["metal"]}" {st}/>')
    hb = INK['slide']
    sc.body.append(f'<path d="M{_pt(388, 150)} Q{_pt(392, 120)} {_pt(414, 114)}" fill="none" stroke="{p["line"]}" stroke-width="4.6" stroke-linecap="round"/>'
                   f'<path d="M{_pt(388, 150)} Q{_pt(392, 120)} {_pt(414, 114)}" fill="none" stroke="{p["metal"]}" stroke-width="2.2" stroke-linecap="round"/>'
                   f'<rect x="410" y="104" width="16" height="18" rx="4" fill="{p["metal"]}" {st}/>'
                   f'<rect x="424" y="106" width="5" height="14" rx="1.5" fill="{p["gold_hi"]}" {stroke(p, .7)}/>')
    sc.body.append(glow_dot(sc, 'strobe', 430, 113, 20, p['gold'], .6))
    sc.body.append(f'<rect x="326" y="146" width="76" height="46" rx="11" fill="{p["pearl_sh"]}" {st}/>'
                   f'<rect x="326" y="146" width="66" height="40" rx="10" fill="{p["pearl"]}"/>'
                   f'<rect x="326" y="146" width="76" height="46" rx="11" fill="none" {st}/>'
                   f'<rect x="340" y="139" width="16" height="9" rx="2" fill="{hb}" {stroke(p, .8)}/>'
                   f'<rect x="370" y="141" width="10" height="6" rx="2" fill="{p["metal"]}" {stroke(p, .8)}/>'
                   f'<path d="M332,154 L384,154" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>'
                   f'<path d="M{_pt(400, 150)} L{_pt(412, 152)} L{_pt(412, 186)} L{_pt(400, 188)} Z" fill="{hb}" {st}/>'
                   f'<path d="M{_pt(412, 154)} A16,16 0 0 1 {_pt(412, 184)} Z" fill="{p["glass_dk"]}" {st}/>'
                   f'<path d="M{_pt(415, 160)} A10,10 0 0 1 {_pt(420, 167)}" stroke="#ffffff" stroke-width="2" fill="none" stroke-linecap="round"/>'
                   f'<rect x="312" y="156" width="12" height="34" rx="5" fill="{hb}" {st}/>'
                   f'<path d="M318,162 L318,184" stroke="#ffffff" stroke-opacity=".35" stroke-width="2" stroke-linecap="round"/>')
    sc.body.append(sc.bot('point', 296, FLOOR))
    sc.body.append(sc.bubbles(530, 66, 40, 3.2, n=3, seed=4))
    sc.body.append(sc.school(770, 60, 16, 'red', n=3, seed=2))
    _edge_dressing(sc, coral_x=816)
    sc.over.append(sc.anemone(754, 15))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ international
def speech(p, x, y, w, h, ink, tail, pattern):
    """A speech bubble centred at (x, y) with a tail pointing to `tail`, holding an abstract (never letter-like) pattern."""
    fill = mix(ink, '#ffffff', .82 if not p['dark'] else .74)
    tx, ty = tail
    dx, dy = tx - x, ty - y
    k = min((w / 2 - 2) / abs(dx) if dx else 9e9, (h / 2 - 2) / abs(dy) if dy else 9e9)
    bx, by = x + dx * k, y + dy * k                      # where the tail leaves the bubble edge
    n = math.hypot(dx, dy)
    ux, uy = -dy / n * 6, dx / n * 6                     # half the tail base, across the tail
    ix, iy = -dx / n * 4, -dy / n * 4                    # a little way inside the bubble
    tri = f'M{_pt(bx + ux, by + uy)} L{_pt(tx, ty)} L{_pt(bx - ux, by - uy)} Z'
    tri_in = f'M{_pt(bx + ux * .78 + ix, by + uy * .78 + iy)} L{_pt(tx - dx / n * 2.4, ty - dy / n * 2.4)} L{_pt(bx - ux * .78 + ix, by - uy * .78 + iy)} Z'
    if pattern == 'dots':
        g = ''.join(f'<circle cx="{fmt(x - 14 + i * 9.3)}" cy="{fmt(y)}" r="3" fill="{ink}" fill-opacity="{fmt(1 - i * .18, 2)}"/>'
                    for i in range(4))
    elif pattern == 'bars':
        g = (f'<path d="M{_pt(x - 15, y - 5)} L{_pt(x + 15, y - 5)}" stroke="{ink}" stroke-width="4.4" stroke-linecap="round"/>'
             f'<path d="M{_pt(x - 15, y + 5)} L{_pt(x + 3, y + 5)}" stroke="{ink}" stroke-width="4.4" stroke-linecap="round" stroke-opacity=".55"/>')
    elif pattern == 'wave':
        g = (f'<path d="M{_pt(x - 17, y + 1)} q4.25,-8 8.5,0 t8.5,0 t8.5,0 t8.5,0" fill="none" stroke="{ink}" stroke-width="2.6" '
             f'stroke-linecap="round"/>')
    else:   # dots and a bar
        g = (f'<circle cx="{fmt(x - 14)}" cy="{fmt(y)}" r="3" fill="{ink}"/>'
             f'<path d="M{_pt(x - 6, y)} L{_pt(x + 6, y)}" stroke="{ink}" stroke-width="4.4" stroke-linecap="round"/>'
             f'<circle cx="{fmt(x + 14)}" cy="{fmt(y)}" r="3" fill="{ink}" fill-opacity=".6"/>')
    return (f'<path d="{tri}" fill="{fill}" {stroke(p)}/>'
            f'<rect x="{fmt(x - w / 2)}" y="{fmt(y - h / 2)}" width="{fmt(w)}" height="{fmt(h)}" rx="11" fill="{fill}" {stroke(p)}/>'
            f'<path d="{tri_in}" fill="{fill}"/>' + g)


def scene_international(dark=False):
    """30-topics-international, "International and multilingual sites": a pearl-and-blue globe in a coral cradle, ringed by
    speech bubbles in different colours (abstract patterns, no letters) linked to it by dotted lines; the Diver bot waves."""
    sc = Scene('30-topics-international', dark, seed=37, avoid=[(470, 670)], rays=6, glow=(570, -40, 380))
    p = sc.p
    st = stroke(p)
    gx, gy, r = 572, 122, 52
    sc.under.append(sc.far_school(170, 60, 14, n=4, flip=True, seed=1))
    sc.body.append(f'<circle cx="{gx}" cy="{gy}" r="{r + 50}" fill="{sc.radial("halo", p["glow"], .7 if not dark else .22)}"/>')
    sc.body.append(sc.shadow(gx, FLOOR, 58))
    sc.body.append(sc.shadow(290, FLOOR, 40))
    bubbles = [(452, 62, 58, 34, INK['slide'], 'dots'), (700, 50, 58, 34, INK['stage'], 'bars'),
               (722, 142, 56, 34, INK['docs'], 'wave'), (446, 150, 54, 32, INK['analysis'], 'mixed')]
    # dotted links from each bubble to the globe
    tails = []
    for bx, by, w, h, ink, pat in bubbles:
        ang = math.atan2(by - gy, bx - gx)
        edge = (gx + math.cos(ang) * (r + 4), gy + math.sin(ang) * (r + 4))
        tail = (bx + (edge[0] - bx) * .42, by + (edge[1] - by) * .42 + (h * .25 if by < gy else -h * .1))
        tails.append(tail)
        sc.body.append(f'<path d="M{_pt(*tail)} L{_pt(*edge)}" stroke="{ink}" stroke-width="2" stroke-dasharray="1 5" '
                       f'stroke-linecap="round" stroke-opacity=".8"/>'
                       f'<circle cx="{fmt(edge[0])}" cy="{fmt(edge[1])}" r="2.6" fill="{ink}"/>')
    # coral cradle: a stem now, the bowl after the globe
    cc = p['coral']
    sc.body.append(f'<path d="M{_pt(gx - 28, FLOOR)} Q{_pt(gx - 10, 204)} {_pt(gx - 9, 182)} L{_pt(gx + 9, 182)} '
                   f'Q{_pt(gx + 10, 204)} {_pt(gx + 28, FLOOR)} Z" fill="{cc}" {st}/>'
                   f'<path d="M{_pt(gx + 4, 188)} Q{_pt(gx + 7, 204)} {_pt(gx + 18, 218)}" stroke="{mix(cc, p["line"], .25)}" stroke-width="2" '
                   f'fill="none" stroke-linecap="round" stroke-opacity=".7"/>')
    # globe
    ocean = p['glass_dk'] if not dark else '#9cc0ff'
    land = p['pearl']
    sc.defs.append(f'<clipPath id="{sc.id("g")}"><circle cx="{gx}" cy="{gy}" r="{r}"/></clipPath>')
    meridians = ''.join(f'<ellipse cx="{gx}" cy="{gy}" rx="{fmt(r * k)}" ry="{r}" fill="none"/>' for k in (.36, .74))
    parallels = ' '.join(f'M{_pt(gx - r, gy + dy)} L{_pt(gx + r, gy + dy)}' for dy in (-34, -17, 0, 17, 34))
    sc.body.append(f'<circle cx="{gx}" cy="{gy}" r="{r}" fill="{ocean}"/>'
                   f'<g clip-path="url(#{sc.id("g")})">'
                   f'<path d="M{_pt(gx - 44, gy - 26)} Q{_pt(gx - 30, gy - 44)} {_pt(gx - 10, gy - 36)} Q{_pt(gx - 2, gy - 20)} {_pt(gx - 16, gy - 10)} '
                   f'Q{_pt(gx - 22, gy + 8)} {_pt(gx - 34, gy + 4)} Q{_pt(gx - 50, gy - 6)} {_pt(gx - 44, gy - 26)} Z" fill="{land}"/>'
                   f'<path d="M{_pt(gx + 8, gy - 30)} Q{_pt(gx + 30, gy - 40)} {_pt(gx + 42, gy - 18)} Q{_pt(gx + 30, gy - 4)} {_pt(gx + 34, gy + 12)} '
                   f'Q{_pt(gx + 20, gy + 30)} {_pt(gx + 8, gy + 16)} Q{_pt(gx + 14, gy - 6)} {_pt(gx + 8, gy - 30)} Z" fill="{land}"/>'
                   f'<path d="M{_pt(gx - 20, gy + 26)} Q{_pt(gx - 6, gy + 20)} {_pt(gx - 2, gy + 36)} Q{_pt(gx - 14, gy + 46)} {_pt(gx - 24, gy + 38)} Z" '
                   f'fill="{land}"/>'
                   f'<g stroke="{INK["slide"]}" stroke-width="1.3" stroke-opacity=".45">{meridians}<path d="{parallels} M{_pt(gx, gy - r)} '
                   f'L{_pt(gx, gy + r)}"/></g>'
                   f'<path d="M{_pt(gx + r * .2, gy + r * 1.05)} A{r},{r} 0 0 0 {_pt(gx + r * 1.02, gy - r * .2)} L{_pt(gx + r * 1.2, gy + r * 1.2)} Z" '
                   f'fill="{p["line"]}" fill-opacity=".14"/></g>'
                   f'<path d="M{_pt(gx - 36, gy - 22)} A{r - 10},{r - 10} 0 0 1 {_pt(gx - 14, gy - 40)}" stroke="#ffffff" stroke-width="4" '
                   f'stroke-opacity=".85" fill="none" stroke-linecap="round"/>'
                   f'<circle cx="{gx}" cy="{gy}" r="{r}" fill="none" {st}/>')
    # the coral bowl the globe rests in, with a knobbly rim and polyp dots
    rim_y = gy + 32
    bowl = (f'M{_pt(gx - 46, rim_y - 2)} Q{_pt(gx, rim_y + 14)} {_pt(gx + 46, rim_y - 2)} Q{_pt(gx + 42, rim_y + 30)} {_pt(gx, rim_y + 32)} '
            f'Q{_pt(gx - 42, rim_y + 30)} {_pt(gx - 46, rim_y - 2)} Z')
    cdk = mix(cc, p['line'], .22)
    sc.body.append(f'<path d="{bowl}" fill="{cc}"/>'
                   f'<path d="M{_pt(gx + 14, rim_y + 10)} Q{_pt(gx + 38, rim_y + 6)} {_pt(gx + 44, rim_y + 2)} Q{_pt(gx + 40, rim_y + 28)} {_pt(gx + 6, rim_y + 31)} Z" '
                   f'fill="{cdk}" fill-opacity=".45"/>'
                   f'<path d="{bowl}" fill="none" {st}/>'
                   + ''.join(f'<circle cx="{fmt(gx + dx)}" cy="{fmt(rim_y + 4 + (1 - (dx / 46) ** 2) * 2 - 2)}" r="4.4" fill="{mix(cc, "#ffffff", .28)}" {stroke(p, .75)}/>'
                             for dx in (-42, -28, -14, 0, 14, 28, 42))
                   + ''.join(f'<circle cx="{fmt(gx + dx)}" cy="{fmt(rim_y + dy)}" r="1.6" fill="{cdk}"/>'
                             for dx, dy in ((-26, 16), (-10, 22), (8, 18), (24, 22), (-34, 10), (32, 12), (-2, 28))))
    for (bx, by, w, h, ink, pat), tail in zip(bubbles, tails):
        sc.body.append(speech(p, bx, by, w, h, ink, tail, pat))
    # fish, each facing a bubble
    sc.body.append(sc.fish(782, 58, 20, 'yellow'))
    sc.body.append(sc.fish(802, 146, 20, 'green'))
    sc.body.append(sc.fish(378, 60, 18, 'red', flip=True))
    sc.body.append(sc.bot('wave', 290, FLOOR))
    sc.body.append(sc.bubbles(640, 196, 30, 3, n=3, seed=4))
    sc.over.append(sc.seaweed(30, 116, phase=.4) + sc.seaweed(50, 80, p['weed_light'], width=4, phase=1.9))
    sc.over.append(sc.coral(842, .34, p['coral']))
    sc.over.append(sc.anemone(770, 14))
    return sc.render()


SCENES = {
    '30-topics': scene_topics,
    '30-topics-crawling': scene_crawling,
    '30-topics-indexing': scene_indexing,
    '30-topics-rendering-javascript': scene_rendering,
    '30-topics-how-search-works': scene_pipeline,
    '30-topics-index-and-signals': scene_signals,
    '30-topics-content-and-media': scene_media,
    '30-topics-international': scene_international,
}
