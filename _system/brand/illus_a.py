"""README illustrations, group A: the root README and the pipeline folders that hold the data
(root, 00-raw, 10-sources, 20-claims, 25-kits, 40-sessions, 50-maps, 70-private).

20-claims is the reference scene: it sets the quality bar and shows how a scene is built with illus_common.Scene.
"""
import math

from illus_common import oa
from illus_common import (FLOOR, H, W, Scene, fmt, mix, placeholder, stroke)   # noqa: F401


# ------------------------------------------------------------------------------------------------------------ props
def _sparkle(x, y, r, color, op=1.0):
    """A soft four-point glint."""
    k = r * 0.28
    d = (f'M{fmt(x)},{fmt(y - r)} Q{fmt(x + k)},{fmt(y - k)} {fmt(x + r)},{fmt(y)} Q{fmt(x + k)},{fmt(y + k)} {fmt(x)},{fmt(y + r)} '
         f'Q{fmt(x - k)},{fmt(y + k)} {fmt(x - r)},{fmt(y)} Q{fmt(x - k)},{fmt(y - k)} {fmt(x)},{fmt(y - r)} Z')
    return f'<path d="{d}" fill="{color}" fill-opacity="{fmt(op, 2)}"/>'


def pearl(p, x, y, r, outline=True, tint=None):
    """A glossy pearl: a cool crescent of shade on the lower right, a bright highlight upper left. tint colours it."""
    body = tint or p['pearl']
    shade = mix(body, p['pearl_sh'] if tint is None else p['line'], .25 if tint else 1.0)
    line = f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="none" {stroke(p, .8)}/>' if outline else ''
    return (f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{shade}"/>'
            f'<circle cx="{fmt(x - r * .17)}" cy="{fmt(y - r * .17)}" r="{fmt(r * .8)}" fill="{body}"/>'
            f'<circle cx="{fmt(x - r * .36)}" cy="{fmt(y - r * .36)}" r="{fmt(r * .27)}" fill="{p["pearl_hi"]}"/>' + line)


def claim_card(p, cx, cy, rot, label, w=34, h=46):
    """A labelled claim card: white card with a coloured label tab (slide / stage / docs / analysis / press), a pearl
    (the claim itself) and two text lines. Centred on (cx, cy), rotated rot degrees."""
    ink = oa.PALETTE['label_' + label][0]      # the saturated label colour in both waters (DARK holds light text colours)
    x0, y0 = -w / 2, -h / 2
    tab = (f'<path d="M{fmt(x0)},{fmt(y0 + 10)} L{fmt(x0)},{fmt(y0 + 5)} Q{fmt(x0)},{fmt(y0)} {fmt(x0 + 5)},{fmt(y0)} '
           f'L{fmt(-x0 - 5)},{fmt(y0)} Q{fmt(-x0)},{fmt(y0)} {fmt(-x0)},{fmt(y0 + 5)} L{fmt(-x0)},{fmt(y0 + 10)} Z" fill="{ink}"/>')
    lines = (f'<path d="M{fmt(x0 + 7)},{fmt(y0 + 33)} L{fmt(-x0 - 7)},{fmt(y0 + 33)} M{fmt(x0 + 7)},{fmt(y0 + 39)} L{fmt(-x0 - 13)},{fmt(y0 + 39)}" '
             f'stroke="{p["paper_line"]}" stroke-width="2.2" stroke-linecap="round"/>')
    return (f'<g transform="translate({fmt(cx)},{fmt(cy)}) rotate({fmt(rot)})">'
            f'<rect x="{fmt(x0)}" y="{fmt(y0)}" width="{w}" height="{h}" rx="5" fill="{p["paper"]}" {stroke(p)}/>'
            f'<rect x="{fmt(-x0 - 5)}" y="{fmt(y0 + 1)}" width="4" height="{fmt(h - 2)}" rx="2" fill="{p["paper_sh"]}"/>'
            + tab + pearl(p, 0, y0 + 21, 6.4, tint=mix(ink, '#ffffff', .62)) + lines +
            f'<rect x="{fmt(x0)}" y="{fmt(y0)}" width="{w}" height="{h}" rx="5" fill="none" {stroke(p)}/></g>')


def treasure_chest(sc, cx, base, w=150, body_h=60):
    """An open treasure chest standing on `base`, centred on cx: arched lid thrown back, gold bands and a lock plate,
    a warm glow and a heap of pearls at the rim. Returns (behind, front): draw cards between the two."""
    p = sc.p
    x0, x1 = cx - w / 2, cx + w / 2
    top = base - body_h
    st = stroke(p)
    # lid, thrown back: its inside faces us, darker wood, the arch at the top
    lid_top = top - 68
    lid = (f'M{fmt(x0 + 6)},{fmt(top)} L{fmt(x0 + 14)},{fmt(lid_top + 14)} Q{fmt(cx)},{fmt(lid_top - 12)} {fmt(x1 - 14)},{fmt(lid_top + 14)} '
           f'L{fmt(x1 - 6)},{fmt(top)} Z')
    inner = mix(p['wood_dk'], p['line'], .45)
    behind = [f'<path d="{lid}" fill="{p["wood_dk"]}" {st}/>',
              f'<path d="M{fmt(x0 + 16)},{fmt(top)} L{fmt(x0 + 22)},{fmt(lid_top + 20)} Q{fmt(cx)},{fmt(lid_top - 1)} {fmt(x1 - 22)},{fmt(lid_top + 20)} '
              f'L{fmt(x1 - 16)},{fmt(top)} Z" fill="{inner}"/>',
              # planks on the inside of the lid
              f'<path d="M{fmt(x0 + 19)},{fmt(top - 22)} L{fmt(x1 - 19)},{fmt(top - 22)} M{fmt(x0 + 21)},{fmt(top - 44)} L{fmt(x1 - 21)},{fmt(top - 44)}" '
              f'stroke="{p["wood_dk"]}" stroke-width="1.6" stroke-opacity=".8"/>',
              # gold rim of the lid
              f'<path d="M{fmt(x0 + 14)},{fmt(lid_top + 14)} Q{fmt(cx)},{fmt(lid_top - 12)} {fmt(x1 - 14)},{fmt(lid_top + 14)}" '
              f'stroke="{p["gold"]}" stroke-width="5" stroke-linecap="round"/>']
    glow = sc.radial('chestglow', p['gold'], .75 if not p['dark'] else .6, .32)
    behind.append(f'<ellipse cx="{fmt(cx)}" cy="{fmt(top - 14)}" rx="{fmt(w * .78)}" ry="{fmt(w * .5)}" fill="{glow}"/>')

    front = []
    # pearls heaped at the rim, back row first
    heap = [(-52, -3, 6.5), (-38, -6, 7.5), (-22, -8, 8), (-6, -9, 8.5), (11, -8, 8), (27, -7, 7.5), (42, -5, 7), (55, -2, 6),
            (-45, 1, 6.5), (-29, 0, 7.5), (-13, -1, 8), (3, -1, 8), (19, 0, 7.5), (35, 0, 7), (49, 2, 6)]
    for dx, dy, r in heap:
        front.append(pearl(p, cx + dx, top + dy, r))
    # body: wood front with plank lines, a shade on the right, gold bands, a lock plate
    body = f'M{fmt(x0)},{fmt(top)} L{fmt(x1)},{fmt(top)} L{fmt(x1 - 3)},{fmt(base - 6)} Q{fmt(x1 - 3)},{fmt(base)} {fmt(x1 - 9)},{fmt(base)} ' \
           f'L{fmt(x0 + 9)},{fmt(base)} Q{fmt(x0 + 3)},{fmt(base)} {fmt(x0 + 3)},{fmt(base - 6)} Z'
    front.append(f'<path d="{body}" fill="{p["wood"]}"/>')
    front.append(f'<path d="M{fmt(x1 - 26)},{fmt(top)} L{fmt(x1)},{fmt(top)} L{fmt(x1 - 3)},{fmt(base - 6)} Q{fmt(x1 - 3)},{fmt(base)} '
                 f'{fmt(x1 - 9)},{fmt(base)} L{fmt(x1 - 26)},{fmt(base)} Z" fill="{p["wood_dk"]}" fill-opacity=".55"/>')
    for k in (1, 2):
        yy = top + body_h * k / 3 + 2
        front.append(f'<path d="M{fmt(x0 + 5)},{fmt(yy)} L{fmt(x1 - 5)},{fmt(yy)}" stroke="{p["wood_dk"]}" stroke-width="1.6" '
                     f'stroke-linecap="round" stroke-opacity=".7"/>')
    front.append(f'<path d="M{fmt(x0 + 8)},{fmt(top + 13)} L{fmt(x0 + 40)},{fmt(top + 13)}" stroke="{p["wood_hi"]}" stroke-width="2" '
                 f'stroke-linecap="round" stroke-opacity=".8"/>')
    for bx in (x0 + 24, x1 - 24):
        front.append(f'<rect x="{fmt(bx - 6)}" y="{fmt(top)}" width="12" height="{fmt(body_h)}" fill="{p["gold"]}" {st}/>'
                     f'<circle cx="{fmt(bx)}" cy="{fmt(top + 9)}" r="1.8" fill="{p["gold_dk"]}"/>'
                     f'<circle cx="{fmt(bx)}" cy="{fmt(base - 9)}" r="1.8" fill="{p["gold_dk"]}"/>')
    front.append(f'<rect x="{fmt(x0 - 2)}" y="{fmt(top - 3)}" width="{fmt(w + 4)}" height="10" rx="3" fill="{p["gold"]}" {st}/>'
                 f'<path d="M{fmt(x0 + 4)},{fmt(top)} L{fmt(x1 - 4)},{fmt(top)}" stroke="{p["gold_hi"]}" stroke-width="2" stroke-linecap="round"/>')
    ly = top + 26
    front.append(f'<path d="M{fmt(cx - 13)},{fmt(ly - 12)} L{fmt(cx + 13)},{fmt(ly - 12)} L{fmt(cx + 13)},{fmt(ly + 4)} '
                 f'Q{fmt(cx + 13)},{fmt(ly + 14)} {fmt(cx)},{fmt(ly + 18)} Q{fmt(cx - 13)},{fmt(ly + 14)} {fmt(cx - 13)},{fmt(ly + 4)} Z" '
                 f'fill="{p["gold"]}" {st}/>'
                 f'<circle cx="{fmt(cx)}" cy="{fmt(ly - 1)}" r="3.6" fill="{p["line"]}"/>'
                 f'<path d="M{fmt(cx)},{fmt(ly)} L{fmt(cx)},{fmt(ly + 8)}" stroke="{p["line"]}" stroke-width="3.2" stroke-linecap="round"/>')
    front.append(f'<path d="{body}" fill="none" {st}/>')
    return ''.join(behind), ''.join(front)


# ------------------------------------------------------------------------------------------------------------ scenes
def scene_claims(dark=False):
    """20-claims, "Claims: the source of truth": the Diver bot points at an open treasure chest on the seabed; labelled
    pearl-cards (one per claim label colour) rise from it in a fan, a warm glow behind them, a single card drifting free."""
    sc = Scene('20-claims', dark, seed=20, avoid=[(380, 640)], rays=6, glow=(520, -30, 380))
    p = sc.p
    cx = 520
    sc.under.append(sc.far_school(150, 64, 15, n=5, flip=True, seed=1))
    behind, front = treasure_chest(sc, cx, FLOOR - 2)
    sc.body.append(sc.shadow(cx, FLOOR, 92))
    sc.body.append(sc.shadow(318, FLOOR, 40))
    sc.body.append(behind)
    for i, label in enumerate(('slide', 'stage', 'docs', 'analysis', 'press')):
        k = i - 2
        sc.body.append(claim_card(p, cx + k * 29, 132 + abs(k) ** 1.5 * 6, k * 14, label))
    sc.body.append(front)
    # one card drifting free towards the bot, with a few bubbles
    sc.body.append(claim_card(p, 422, 96, -16, 'docs', 30, 40))
    sc.body.append(sc.bubble(404, 66, 3.6) + sc.bubble(414, 54, 2.4))
    sc.body.append(sc.bot('point', 318, FLOOR))
    for x, y, r, o in ((452, 112, 5, .9), (604, 104, 6, .9), (590, 150, 3.5, .7), (436, 150, 3, .6), (636, 128, 3.2, .7)):
        sc.body.append(_sparkle(x, y, r, p['gold_hi'] if not dark else p['gold'], o))
    sc.body.append(sc.bubbles(612, 92, 52, 4.2, n=4, seed=3))
    # reef dressing and company
    sc.body.append(sc.school(706, 70, 20, 'blue', n=5, seed=2))
    sc.body.append(sc.fish(176, 92, 26, 'yellow', flip=True))
    sc.over.append(sc.seaweed(34, 120, phase=.4) + sc.seaweed(52, 84, p['weed_light'], width=4, phase=1.9))
    sc.over.append(sc.anemone(742, 17))
    sc.over.append(sc.coral(818, .4))
    sc.over.append(sc.seaweed(852, 96, p['weed_light'], width=4, phase=2.6))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ small helpers
def _f(*xy):
    """'x,y x,y ...' from a flat list of numbers."""
    return ' '.join(f'{fmt(xy[i])},{fmt(xy[i + 1])}' for i in range(0, len(xy), 2))


def _thick(p, d, color, w, op=None):
    """A thick stroked line with the shared outline round it (rope, chain bar, wrench handle...)."""
    o = f' stroke-opacity="{fmt(op, 2)}"' if op is not None else ''
    return (f'<path d="{d}" fill="none" stroke="{p["line"]}" stroke-width="{fmt(w + 2 * p["lw"])}" stroke-linecap="round" '
            f'stroke-linejoin="round"{o}/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{fmt(w)}" stroke-linecap="round" stroke-linejoin="round"/>')


def _rock(p):
    """Rock colours (body, top, shade) derived from the seabed tokens, readable in both waters."""
    if p['dark']:
        return mix(p['near'], p['metal_dk'], .35), mix(p['near'], p['metal_dk'], .7), mix(p['near'], p['band'], .35)
    body = mix(p['mid_dk'], p['violet_lt'], .3)
    return body, mix(p['far'], '#ffffff', .2), mix(body, p['line'], .28)


SWIM_H = 124      # a swimming bot's box height that matches the standing bot's scale (BOT_H 108)


def _swim_pt(cx, base, pt, height=SWIM_H, flip=False):
    """Where the body-frame point pt (design units, before the swim pose's 112-degree turn) lands in the card."""
    bx, by, _, bh = oa._BOT_BOX['swim']
    s = height / bh
    x, y = oa._bapply(oa._brot(112, 0, 30), pt)
    return cx + (-s if flip else s) * (x - bx), base - height / 2 + s * (y - by)


def _glow(sc, name, x, y, rx, ry, color, op):
    return f'<ellipse cx="{fmt(x)}" cy="{fmt(y)}" rx="{fmt(rx)}" ry="{fmt(ry)}" fill="{sc.radial(name, color, op, .3)}"/>'


def _check_chip(p, x, y, s=9):
    """A small green check chip (rounded square, white tick), top-left at (x, y)."""
    return (f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(s)}" height="{fmt(s)}" rx="2.4" fill="{p["quiz_green"]}"/>'
            f'<path d="M{fmt(x + s * .25)},{fmt(y + s * .52)} L{fmt(x + s * .43)},{fmt(y + s * .7)} L{fmt(x + s * .76)},{fmt(y + s * .3)}" '
            f'fill="none" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')


def scallop(p, x, y, r, rot=0.0, color=None, rib=None):
    """A scallop shell, hinge at the bottom, centred on (x, y), radius r, rotated rot degrees."""
    color = color or mix(p['coral'], '#ffffff', .55)
    rib = rib or mix(color, p['line'], .22)
    n, pts = 7, []
    for i in range(n + 1):
        a = math.radians(-160 + 140 * i / n)
        pts.append((r * math.cos(a), r * .35 + r * 1.05 * math.sin(a)))
    d = f'M0,{fmt(r * .55)} L{fmt(pts[0][0])},{fmt(pts[0][1])}'
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        k = 1.18
        d += f' Q{fmt(mx * k)},{fmt((my - r * .35) * k + r * .35)} {fmt(bx)},{fmt(by)}'
    d += ' Z'
    ribs = ' '.join(f'M0,{fmt(r * .5)} L{fmt(px * .82)},{fmt((py - r * .35) * .82 + r * .35)}' for px, py in pts[1:-1])
    ear = f'M{fmt(-r * .32)},{fmt(r * .38)} L{fmt(r * .32)},{fmt(r * .38)} L{fmt(r * .2)},{fmt(r * .62)} L{fmt(-r * .2)},{fmt(r * .62)} Z'
    return (f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(rot)})">'
            f'<path d="{ear}" fill="{rib}" {stroke(p, .8)}/>'
            f'<path d="{d}" fill="{color}" {stroke(p, .8)}/>'
            f'<path d="{ribs}" stroke="{rib}" stroke-width="1.4" stroke-linecap="round"/></g>')


def photo(p, x, y, w, h, rot=0.0):
    """A blank photo print: white border, sky, a little mountain and wave, a sun dot. Centred on (x, y)."""
    sky = mix(p['glass_dk'], '#ffffff', .25)
    x0, y0, iw, ih = -w / 2 + 3, -h / 2 + 3, w - 6, h - 9
    return (f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(rot)})">'
            f'<rect x="{fmt(-w / 2)}" y="{fmt(-h / 2)}" width="{fmt(w)}" height="{fmt(h)}" rx="2" fill="{p["paper"]}" {stroke(p, .8)}/>'
            f'<rect x="{fmt(x0)}" y="{fmt(y0)}" width="{fmt(iw)}" height="{fmt(ih)}" fill="{sky}"/>'
            f'<path d="M{_f(x0, y0 + ih, x0 + iw * .38, y0 + ih * .35, x0 + iw * .7, y0 + ih)} Z" fill="{p["blue"]}"/>'
            f'<path d="M{_f(x0 + iw * .45, y0 + ih, x0 + iw * .72, y0 + ih * .55, x0 + iw, y0 + ih)} Z" fill="{p["blue_deep"]}" fill-opacity=".8"/>'
            f'<circle cx="{fmt(x0 + iw * .78)}" cy="{fmt(y0 + ih * .3)}" r="{fmt(ih * .14)}" fill="{p["gold"]}"/></g>')


# ------------------------------------------------------------------------------------------------------------ root
def lantern(sc, x, y, tint, name):
    """A small caged lantern hung on the dive line, centred on (x, y), glowing in `tint`."""
    p = sc.p
    glass = mix(tint, '#ffffff', .45)
    core = mix(tint, '#ffffff', .82)
    frame = mix(p['metal_dk'], p['line'], .35)
    st = stroke(p)
    return (_glow(sc, name, x, y + 2, 50, 46, tint, .75 if not p['dark'] else .6) +
            f'<path d="M{fmt(x - 7)},{fmt(y - 22)} Q{fmt(x)},{fmt(y - 33)} {fmt(x + 7)},{fmt(y - 22)}" fill="none" stroke="{frame}" stroke-width="2.2"/>'
            f'<path d="M{_f(x - 9, y - 23, x + 9, y - 23, x + 14, y - 15, x - 14, y - 15)} Z" fill="{frame}" {st}/>'
            f'<rect x="{fmt(x - 12)}" y="{fmt(y - 15)}" width="24" height="31" rx="5" fill="{glass}" {st}/>'
            f'<ellipse cx="{fmt(x)}" cy="{fmt(y + 1)}" rx="6.5" ry="9" fill="{core}"/>'
            f'<ellipse cx="{fmt(x)}" cy="{fmt(y + 3)}" rx="2.6" ry="4" fill="#ffffff"/>'
            f'<path d="M{fmt(x - 5.5)},{fmt(y - 14)} L{fmt(x - 5.5)},{fmt(y + 15)} M{fmt(x + 5.5)},{fmt(y - 14)} L{fmt(x + 5.5)},{fmt(y + 15)}" '
            f'stroke="{frame}" stroke-width="1.8"/>'
            f'<rect x="{fmt(x - 14)}" y="{fmt(y + 15)}" width="28" height="6" rx="2" fill="{frame}" {st}/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y + 24)}" r="2.6" fill="{frame}" {stroke(p, .7)}/>')


def anchor(p, x, y):
    """A small anchor, ring at (x, y), crown about 36 units lower."""
    m, md = p['metal'], p['metal_dk']
    arms = f'M{fmt(x - 19)},{fmt(y + 23)} Q{fmt(x - 16)},{fmt(y + 37)} {fmt(x)},{fmt(y + 37)} Q{fmt(x + 16)},{fmt(y + 37)} {fmt(x + 19)},{fmt(y + 23)}'
    return (_thick(p, arms, md, 4.4) +
            f'<path d="M{_f(x - 23, y + 25, x - 19, y + 17, x - 14, y + 26)} Z" fill="{md}" {stroke(p)}/>'
            f'<path d="M{_f(x + 23, y + 25, x + 19, y + 17, x + 14, y + 26)} Z" fill="{md}" {stroke(p)}/>' +
            _thick(p, f'M{fmt(x)},{fmt(y + 5)} L{fmt(x)},{fmt(y + 36)}', m, 4.6) +
            _thick(p, f'M{fmt(x - 13)},{fmt(y + 11)} L{fmt(x + 13)},{fmt(y + 11)}', md, 3.6) +
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="4.6" fill="none" stroke="{p["line"]}" stroke-width="4.4"/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="4.6" fill="none" stroke="{m}" stroke-width="2"/>')


def scene_root(dark=False):
    """root, "The three days" spot card: the Diver bot swims down a dive line hung from a buoy, with three glowing
    lanterns at three depths (crawling, indexing, serving) and fish circling the deepest one."""
    sc = Scene('root', dark, seed=3, avoid=[(500, 640)], rays=6, glow=(560, -40, 380))
    p = sc.p
    lx = 572
    sway = lambda y: lx + 4.5 * math.sin((y - 30) / 52)          # noqa: E731  the line's gentle sway
    ys = list(range(30, 186, 13)) + [186]
    rope = oa.catmull([(sway(y), y) for y in ys])
    tints = (mix(p['blue'], '#ffffff', .35), p['fish_green'], p['gold'])
    sc.under.append(sc.far_school(150, 70, 14, n=5, flip=True, seed=1))
    sc.body.append(sc.shadow(lx, FLOOR - 1, 30))
    sc.body.append(_thick(p, rope, p['wood'], 2.6))
    sc.body.append(f'<path d="{rope}" fill="none" stroke="{p["wood_hi"]}" stroke-width="1.1" stroke-dasharray="2 4" stroke-linecap="round"/>')
    sc.body.append(anchor(p, sway(186), 188))
    for i, (y, side, tint) in enumerate(zip((66, 114, 162), (-1, 1, -1), tints)):
        x, ty = sway(y) + side * 26, y - 30
        rx_ = sway(y - 44)
        sc.body.append(f'<ellipse cx="{fmt(rx_)}" cy="{fmt(y - 44)}" rx="3.6" ry="3" fill="{p["wood_dk"]}" {stroke(p, .6)}/>'
                       f'<path d="M{fmt(rx_)},{fmt(y - 44)} Q{fmt((rx_ + x) / 2)},{fmt(y - 40)} {fmt(x)},{fmt(ty)}" fill="none" '
                       f'stroke="{p["wood_dk"]}" stroke-width="1.6"/>')
        sc.body.append(lantern(sc, x, y, tint, f'lamp{i}'))
        for k in range(i + 1):             # one bead per day on the lantern's cord
            t = .3 + .22 * k
            bx_ = (1 - t) ** 2 * rx_ + 2 * (1 - t) * t * (rx_ + x) / 2 + t * t * x
            by_ = (1 - t) ** 2 * (y - 44) + 2 * (1 - t) * t * (y - 40) + t * t * ty
            sc.body.append(f'<circle cx="{fmt(bx_)}" cy="{fmt(by_)}" r="2.3" fill="{p["pearl"]}" {stroke(p, .55)}/>')
    # the buoy, bobbing under the surface band
    sc.body.append(f'<ellipse cx="{lx}" cy="13" rx="24" ry="15" fill="{p["pearl"]}" {stroke(p)}/>'
                   f'<path d="M{lx - 23.6},16 A24,15 0 0 0 {lx + 23.6},16 Z" fill="{p["blue"]}"/>'
                   f'<path d="M{lx - 22},21 A24,15 0 0 0 {lx + 22},21" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-opacity=".8"/>'
                   f'<ellipse cx="{lx}" cy="13" rx="24" ry="15" fill="none" {stroke(p)}/>'
                   f'<circle cx="{lx}" cy="30" r="3.4" fill="none" stroke="{p["metal_dk"]}" stroke-width="2.2"/>')
    # fish circling the deepest lantern
    sc.body.append(sc.fish(500, 140, 17, 'yellow', flip=True) + sc.fish(590, 186, 16, 'red') + sc.fish(512, 192, 12, 'blue', flip=True))
    sc.body.append(sc.bot('swim', 404, 170, height=SWIM_H))
    sc.body.append(sc.fish(760, 76, 20, 'blue') + sc.bubbles(640, 96, 40, 3.4, n=3, seed=4))
    sc.over.append(sc.seaweed(30, 116, phase=.8) + sc.seaweed(52, 78, p['weed_light'], width=4, phase=2.2))
    sc.over.append(sc.coral(826, .36, flip=True) + sc.anemone(772, 14))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 00-raw
def _film(p, d, w=9):
    """A film-strip ribbon along the path d: dark band with light perforations."""
    film = mix(p['line'], p['blue_deep'], .25)
    return (f'<path d="{d}" fill="none" stroke="{film}" stroke-width="{w}" stroke-linecap="butt"/>'
            f'<path d="{d}" fill="none" stroke="{p["glass_dk"]}" stroke-width="{fmt(w * .78)}" stroke-dasharray="1.6 3.4"/>'
            f'<path d="{d}" fill="none" stroke="{film}" stroke-width="{fmt(w * .5)}"/>'
            f'<path d="{d}" fill="none" stroke="{p["glass"]}" stroke-width="{fmt(w * .34)}" stroke-dasharray="8 3" stroke-opacity=".85"/>')


def tape_reel(p, x, y, r):
    md = p['metal_dk']
    spokes = ' '.join(f'M{fmt(x + r * .3 * math.cos(a))},{fmt(y + r * .3 * math.sin(a))} L{fmt(x + r * .8 * math.cos(a))},{fmt(y + r * .8 * math.sin(a))}'
                      for a in (math.radians(20 + 120 * k) for k in range(3)))
    return (f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{p["metal"]}" {stroke(p, .8)}/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r * .78)}" fill="{mix(p["line"], p["wood_dk"], .4)}"/>'
            f'<path d="{spokes}" stroke="{p["metal_hi"]}" stroke-width="2.4" stroke-linecap="round"/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r * .26)}" fill="{p["metal_hi"]}" stroke="{md}" stroke-width="1"/>')


def note_page(p, x, y, w, h, rot):
    curl = f'M{fmt(w / 2 - 9)},{fmt(h / 2)} Q{fmt(w / 2 - 2)},{fmt(h / 2 - 3)} {fmt(w / 2)},{fmt(h / 2 - 10)} L{fmt(w / 2 - 6)},{fmt(h / 2 - 8)} Z'
    lines = ' '.join(f'M{fmt(-w / 2 + 5)},{fmt(-h / 2 + 7 + k * 5.5)} L{fmt(w / 2 - 5 - (k % 2) * 6)},{fmt(-h / 2 + 7 + k * 5.5)}' for k in range(3))
    return (f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(rot)})">'
            f'<path d="M{_f(-w / 2, -h / 2, w / 2, -h / 2, w / 2, h / 2 - 10, w / 2 - 9, h / 2, -w / 2, h / 2)} Z" fill="{p["paper"]}" {stroke(p, .8)}/>'
            f'<path d="{curl}" fill="{p["paper_sh"]}" {stroke(p, .6)}/>'
            f'<path d="{lines}" stroke="{p["paper_line"]}" stroke-width="1.8" stroke-linecap="round"/></g>')


def sound_clam(p, x, y, r, rot=0.0):
    """A clam with a sound wave on it (an audio recording)."""
    sh = mix(p['violet_lt'], '#ffffff', .4)
    wave = ' '.join(f'M{fmt(-r * .6 + k * r * .2)},{fmt(-h)} L{fmt(-r * .6 + k * r * .2)},{fmt(h)}'
                    for k, h in enumerate((1.5, 3.5, 6, 3, 5, 2, 1)))
    return (f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(rot)})">'
            f'<path d="M{fmt(-r)},0 C{fmt(-r)},{fmt(-r * .9)} {fmt(r)},{fmt(-r * .9)} {fmt(r)},0 C{fmt(r)},{fmt(r * .5)} {fmt(-r)},{fmt(r * .5)} {fmt(-r)},0 Z" '
            f'fill="{sh}" {stroke(p, .8)}/>'
            f'<path d="{wave}" stroke="{p["violet"]}" stroke-width="1.7" stroke-linecap="round" transform="translate(0,{fmt(-r * .22)})"/></g>')


def scene_raw(dark=False):
    """00-raw, "Raw inputs": the Diver bot hauls a bulging rope net off the seabed, full of unsorted shells, photos, film,
    tape, notes and a recorded clam, with a little puff of sand where it lifts."""
    sc = Scene('00-raw', dark, seed=7, avoid=[(450, 700)], rays=6, glow=(560, -40, 380))
    p = sc.p
    sc.under.append(sc.far_school(720, 62, 14, n=5, seed=1))
    # sand puff under the lifting net
    puff = mix(p['near'], '#ffffff', .4 if not dark else .14)
    for x, y, rx, ry, o in ((520, 216, 34, 7, .7), (578, 219, 48, 8, .8), (642, 215, 30, 6, .6), (606, 209, 18, 6, .45), (490, 210, 14, 5, .45)):
        sc.body.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{puff}" fill-opacity="{o}"/>')
    sc.body.append(oa.dots(470, 690, 196, 18, 12, puff, .9, 2, seed='raw-puff'))
    # spilled items on the seabed
    sc.body.append(sc.shadow(690, FLOOR - 1, 20) + photo(p, 690, 213, 30, 24, 14))
    sc.body.append(scallop(p, 458, 214, 9, -18, color=mix(p['gold_hi'], '#ffffff', .2)))
    # the net bag
    bag = [(512, 118), (548, 116), (600, 122), (644, 140), (662, 170), (652, 200), (614, 212), (560, 214), (512, 206), (488, 184),
           (486, 156), (496, 132)]
    d = oa.catmull(bag, closed=True)
    clip = sc.id('net')
    sc.defs.append(f'<clipPath id="{clip}"><path d="{d}"/></clipPath>')
    inside = mix(p['wood_dk'], p['line'], .35)
    items = [
        f'<path d="{d}" fill="{inside}" fill-opacity="{".4" if not dark else ".6"}"/>',
        _film(p, 'M492,196 C530,186 548,150 600,148 C628,147 640,160 668,150'),
        scallop(p, 524, 138, 15, -14, color=mix(p['coral'], '#ffffff', .5)),
        photo(p, 552, 164, 38, 30, -12),
        tape_reel(p, 606, 146, 17),
        sound_clam(p, 512, 178, 16, 8),
        scallop(p, 640, 168, 13, 22, color=mix(p['gold_hi'], '#ffffff', .2)),
        note_page(p, 594, 190, 30, 26, 10),
        photo(p, 632, 196, 28, 22, 18),
        scallop(p, 552, 202, 12, -30, color=p['pearl']),
        scallop(p, 572, 128, 10, 30, color=mix(p['violet_lt'], '#ffffff', .4)),
    ]
    mesh = []
    for k in range(-14, 16):
        x = 500 + k * 14
        mesh.append(f'M{x},110 l110,110 M{x + 110},110 l-110,110')
    net_col = p['wood_hi'] if not dark else mix(p['wood_hi'], '#ffffff', .2)
    sc.body.append(f'<g clip-path="url(#{clip})">' + ''.join(items) +
                   f'<path d="{" ".join(mesh)}" fill="none" stroke="{p["wood_dk"]}" stroke-width="2.6" stroke-opacity=".55"/>'
                   f'<path d="{" ".join(mesh)}" fill="none" stroke="{net_col}" stroke-width="1.5"/></g>')
    sc.body.append(f'<path d="{d}" fill="none" stroke="{p["line"]}" stroke-width="5"/>'
                   f'<path d="{d}" fill="none" stroke="{p["wood"]}" stroke-width="2.6"/>')
    # a film strip tail escaping the net, curling onto the sand
    sc.body.append(_film(p, 'M650,190 C672,196 668,214 700,222 C716,226 730,220 738,214'))
    # the bot, swimming up and away to the left, the rope taut from its glove to the gathered neck
    cxb, base, rot = 300, 124, 24
    cyb = base - SWIM_H / 2
    a = math.radians(rot)
    bx_, by_ = _swim_pt(cxb, base, (30, 57), flip=True)        # the belt, at the hip
    gx = cxb + (bx_ - cxb) * math.cos(a) - (by_ - cyb) * math.sin(a)
    gy = cyb + (bx_ - cxb) * math.sin(a) + (by_ - cyb) * math.cos(a)
    ang = fmt(math.degrees(math.atan2(116 - gy, 506 - gx)))
    sc.body.append(f'<ellipse cx="510" cy="118" rx="8" ry="6" fill="{p["wood"]}" {stroke(p)}/>'
                   f'<path d="M505,114 L512,122 M509,113 L515,120" stroke="{p["wood_dk"]}" stroke-width="1.4" stroke-linecap="round"/>')
    sc.body.append(f'<g transform="rotate({rot} {cxb} {cyb})">' + sc.bot('swim', cxb, base, height=SWIM_H, flip=True) + '</g>')
    sc.body.append(_thick(p, f'M{fmt(gx)},{fmt(gy)} L506,116', p['wood'], 2.6) +
                   f'<g transform="rotate({ang} {fmt(gx)} {fmt(gy)})">'
                   f'<rect x="{fmt(gx - 6)}" y="{fmt(gy - 4)}" width="12" height="8" rx="4" fill="none" stroke="{p["line"]}" stroke-width="4.6"/>'
                   f'<rect x="{fmt(gx - 6)}" y="{fmt(gy - 4)}" width="12" height="8" rx="4" fill="none" stroke="{p["gold"]}" stroke-width="2"/></g>')
    sc.body.append(sc.bubbles(680, 128, 46, 3.6, n=4, seed=5))
    sc.body.append(sc.fish(150, 150, 22, 'red', flip=True))
    sc.over.append(sc.seaweed(28, 104, phase=1.2) + sc.seaweed(50, 70, p['weed_light'], width=4, phase=.3))
    sc.over.append(sc.coral(812, .34) + sc.seaweed(850, 90, p['weed_light'], width=4, phase=2.0))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 10-sources
def jar(p, cx, base, w, h, ink, content):
    """A clear glass jar on `base`: a coloured collar band (no text), a metal lid, the content seen through the glass."""
    x0, top = cx - w / 2, base - h
    body = (f'M{fmt(x0 + 3)},{fmt(top + 8)} Q{fmt(x0)},{fmt(top + 10)} {fmt(x0)},{fmt(top + 18)} L{fmt(x0)},{fmt(base - 7)} '
            f'Q{fmt(x0)},{fmt(base)} {fmt(x0 + 7)},{fmt(base)} L{fmt(x0 + w - 7)},{fmt(base)} Q{fmt(x0 + w)},{fmt(base)} {fmt(x0 + w)},{fmt(base - 7)} '
            f'L{fmt(x0 + w)},{fmt(top + 18)} Q{fmt(x0 + w)},{fmt(top + 10)} {fmt(x0 + w - 3)},{fmt(top + 8)} Z')
    glass_op = '.55' if not p['dark'] else '.4'
    return (f'<path d="{body}" fill="{p["glass"]}" fill-opacity="{glass_op}"/>' + content +
            f'<path d="M{fmt(x0 + w - 9)},{fmt(top + 14)} L{fmt(x0 + w - 9)},{fmt(base - 4)} Q{fmt(x0 + w - 3)},{fmt(base - 6)} {fmt(x0 + w - 3)},{fmt(base - 12)} '
            f'L{fmt(x0 + w - 3)},{fmt(top + 16)} Z" fill="{p["glass_dk"]}" fill-opacity=".55"/>'
            f'<path d="M{fmt(x0 + 6)},{fmt(top + 22)} L{fmt(x0 + 6)},{fmt(base - 12)}" stroke="#ffffff" stroke-width="3" stroke-linecap="round" stroke-opacity=".85"/>'
            f'<rect x="{fmt(x0)}" y="{fmt(top + 14)}" width="{fmt(w)}" height="8" fill="{ink}"/>'
            f'<path d="{body}" fill="none" {stroke(p)}/>'
            f'<rect x="{fmt(cx - w * .42)}" y="{fmt(top)}" width="{fmt(w * .84)}" height="9" rx="3" fill="{p["metal"]}" {stroke(p)}/>'
            f'<path d="M{fmt(cx - w * .36)},{fmt(top + 3)} L{fmt(cx + w * .2)},{fmt(top + 3)}" stroke="{p["metal_hi"]}" stroke-width="1.8" stroke-linecap="round"/>')


def _slides(p, cx, base, ink):
    out = ''
    for k, (dx, dy, r) in enumerate(((-4, -10, -8), (3, -20, 5), (-2, -31, -3))):
        x, y = cx + dx, base + dy
        out += (f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({r})"><rect x="-12" y="-8" width="24" height="16" rx="2" fill="{p["paper"]}" {stroke(p, .7)}/>'
                f'<rect x="-12" y="-8" width="24" height="4.5" rx="2" fill="{ink}"/>'
                f'<path d="M-8,0 L6,0 M-8,4 L2,4" stroke="{p["paper_line"]}" stroke-width="1.6" stroke-linecap="round"/></g>')
    return out


def _scroll(p, cx, base):
    y = base - 18
    lines = ' '.join(f'M{fmt(cx - 9)},{fmt(y + 8 + k * 5)} L{fmt(cx + 6 - (k % 2) * 5)},{fmt(y + 8 + k * 5)}' for k in range(3))
    return (f'<path d="M{_f(cx - 12, y, cx + 12, y, cx + 12, y + 22, cx - 12, y + 22)} Z" fill="{p["paper"]}" {stroke(p, .7)}/>'
            f'<path d="{lines}" stroke="{p["paper_line"]}" stroke-width="1.6" stroke-linecap="round"/>'
            f'<rect x="{fmt(cx - 15)}" y="{fmt(y - 12)}" width="30" height="13" rx="6.5" fill="{p["paper_sh"]}" {stroke(p, .7)}/>'
            f'<ellipse cx="{fmt(cx + 15)}" cy="{fmt(y - 5.5)}" rx="3.2" ry="6.5" fill="{p["paper"]}" {stroke(p, .7)}/>'
            f'<rect x="{fmt(cx - 15)}" y="{fmt(y - 22)}" width="30" height="11" rx="5.5" fill="{p["paper"]}" {stroke(p, .7)}/>')


def _pearl_string(p, cx, base):
    pts = []
    for k in range(11):
        a = math.radians(180 + k * 40)
        rr = 13 - k * .55
        pts.append((cx + rr * math.cos(a), base - 12 + rr * .5 * math.sin(a) - k * 1.9))
    out = f'<path d="{oa.catmull(pts)}" fill="none" stroke="{p["gold_dk"]}" stroke-width="1.2"/>'
    for x, y in pts:
        out += pearl(p, x, y, 3.4, outline=False)
    return out


def scene_sources(dark=False):
    """10-sources, "Cleaned sources": the Diver bot points at a shell being rinsed in a vent's bubble shower; on a rock
    shelf, four clear jars with coloured bands hold tidy material: slides, a transcript scroll, a photo, a pearl string."""
    sc = Scene('10-sources', dark, seed=10, avoid=[(370, 720)], rays=6, glow=(560, -40, 380))
    p = sc.p
    body, top, shade = _rock(p)
    sc.under.append(sc.far_school(720, 60, 14, n=4, seed=2))
    # the rock shelf
    sc.body.append(sc.shadow(586, FLOOR + 1, 150, 9))
    shelf = 'M450,227 L454,186 Q456,174 470,173 L702,171 Q716,172 718,184 L724,227 Z'
    sc.body.append(f'<path d="{shelf}" fill="{body}" {stroke(p)}/>'
                   f'<path d="M454,186 Q456,174 470,173 L702,171 Q716,172 718,184 Q600,190 454,186 Z" fill="{top}"/>'
                   f'<path d="M690,190 Q706,200 704,227 L724,227 L718,186 Z" fill="{shade}" fill-opacity=".5"/>'
                   f'<path d="M470,182 L540,180" stroke="#ffffff" stroke-opacity=".5" stroke-width="2" stroke-linecap="round"/>'
                   f'<path d="{shelf}" fill="none" {stroke(p)}/>')
    inks = {k: oa.PALETTE['label_' + k][0] for k in ('slide', 'stage', 'docs', 'analysis')}
    b = 180
    sc.body.append(jar(p, 494, b, 44, 64, inks['slide'], _slides(p, 494, b - 2, inks['slide'])))
    sc.body.append(jar(p, 554, b, 46, 78, inks['stage'], _scroll(p, 554, b - 6)))
    sc.body.append(jar(p, 613, b, 42, 56, inks['docs'], photo(p, 612, b - 17, 26, 22, -6)))
    sc.body.append(jar(p, 670, b, 44, 68, inks['analysis'], _pearl_string(p, 670, b - 2)))
    # the rinse: a small vent sends a shower of bubbles up through a shell
    vx = 398
    sc.body.append(sc.shadow(vx, FLOOR, 22))
    sc.body.append(f'<path d="M{_f(vx - 20, 226, vx - 9, 199, vx + 9, 199, vx + 20, 226)} Z" fill="{body}" {stroke(p)}/>'
                   f'<ellipse cx="{vx}" cy="199" rx="9" ry="3" fill="{mix(body, p["line"], .45)}" {stroke(p, .8)}/>'
                   f'<path d="M{vx + 8},206 L{vx + 14},224" stroke="{shade}" stroke-width="2" stroke-linecap="round"/>')
    for k, (dx, y, r) in enumerate(((-3, 188, 3.4), (4, 176, 4.4), (-5, 164, 3), (8, 154, 2.6), (-11, 140, 4), (12, 126, 3.4),
                                    (-6, 118, 2.6), (3, 108, 5), (-10, 94, 3), (9, 84, 3.6), (-2, 70, 2.6))):
        sc.body.append(sc.bubble(vx + dx, y, r))
    sc.body.append(scallop(p, vx + 1, 140, 15, -8, color=mix(p['coral'], '#ffffff', .45)))
    for x, y, r in ((vx - 24, 128, 5), (vx + 22, 150, 4), (vx + 18, 118, 3)):
        sc.body.append(_sparkle(x, y, r, p['gold_hi'] if not dark else p['gold'], .9))
    # still to rinse: a little heap of sandy shells behind the bot
    sc.body.append(scallop(p, 214, 214, 10, -20, color=mix(p['gold_hi'], p['wood_hi'], .4)) +
                   scallop(p, 232, 218, 8, 24, color=mix(p['coral'], p['wood_hi'], .5)))
    sc.body.append(sc.shadow(292, FLOOR, 40))
    sc.body.append(sc.bot('point', 292, FLOOR))
    sc.body.append(sc.fish(168, 96, 24, 'yellow', flip=True))
    sc.over.append(sc.seaweed(30, 112, phase=.2) + sc.seaweed(54, 76, p['weed_light'], width=4, phase=1.5))
    sc.over.append(sc.anemone(762, 15) + sc.coral(830, .38, flip=True))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 25-kits
def _wrench(p, x0, y0, x1, y1):
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    ln = math.hypot(x1 - x0, y1 - y0)
    m, md = p['metal'], p['metal_dk']
    return (f'<g transform="translate({fmt(x0)},{fmt(y0)}) rotate({fmt(ang)})">'
            f'<rect x="0" y="-3.4" width="{fmt(ln - 6)}" height="6.8" rx="3.4" fill="{m}" {stroke(p)}/>'
            f'<path d="M{fmt(ln - 8)},-7 C{fmt(ln + 4)},-12 {fmt(ln + 12)},-4 {fmt(ln + 9)},-1 L{fmt(ln + 2)},-2 L{fmt(ln + 2)},2 L{fmt(ln + 9)},1 '
            f'C{fmt(ln + 12)},4 {fmt(ln + 4)},12 {fmt(ln - 8)},7 Z" fill="{m}" {stroke(p)}/>'
            f'<path d="M4,-1 L{fmt(ln - 12)},-1" stroke="{p["metal_hi"]}" stroke-width="1.6" stroke-linecap="round"/>'
            f'<circle cx="5" cy="0" r="1.6" fill="{md}"/></g>')


def _gear(p, x, y, r, color, teeth=8):
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        rr = r if (i % 4) in (1, 2) else r * .78
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return (f'<path d="M{" L".join(f"{fmt(a)},{fmt(b)}" for a, b in pts)} Z" fill="{color}" {stroke(p)}/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r * .32)}" fill="{p["paper"]}" {stroke(p, .8)}/>')


def _conch(p, x, y, s=1.0, rot=0.0):
    """A conch shell used as a megaphone, mouth to the right."""
    c, sh = mix(p['coral'], '#ffffff', .35), p['coral']
    return (f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(rot)}) scale({fmt(s, 2)})">'
            f'<path d="M-18,0 C-14,-6 -2,-10 10,-14 C14,-6 14,6 10,14 C-2,10 -14,6 -18,0 Z" fill="{c}" {stroke(p)}/>'
            f'<path d="M-14,-2 L-11,-6 M-8,-5 L-5,-9 M-2,-7 L1,-11" stroke="{sh}" stroke-width="1.8" stroke-linecap="round"/>'
            f'<ellipse cx="10" cy="0" rx="4.5" ry="14" fill="{mix(p["coral"], "#ffffff", .7)}" {stroke(p)}/>'
            f'<ellipse cx="11" cy="0" rx="2" ry="8" fill="{sh}"/>'
            f'<path d="M18,-8 Q22,0 18,8 M23,-12 Q29,0 23,12" fill="none" stroke="{p["blue"]}" stroke-width="1.8" stroke-linecap="round"/></g>')


def _camera(p, x, y, rot=0.0):
    md = mix(p['metal_dk'], p['line'], .3)
    return (f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(rot)})">'
            f'<rect x="-6" y="-12" width="10" height="5" rx="1.5" fill="{md}" {stroke(p, .8)}/>'
            f'<rect x="-13" y="-8" width="26" height="17" rx="3.5" fill="{md}" {stroke(p)}/>'
            f'<circle cx="1" cy="0.5" r="6.2" fill="{p["metal_hi"]}" {stroke(p, .8)}/>'
            f'<circle cx="1" cy="0.5" r="3.4" fill="{p["blue_deep"]}"/><circle cx="-0.2" cy="-0.8" r="1.2" fill="#ffffff"/>'
            f'<circle cx="9.5" cy="-4.5" r="1.4" fill="{p["gold"]}"/></g>')


def _speech(p, x, y, w=26, h=18):
    return (f'<path d="M{fmt(x - w / 2 + 5)},{fmt(y - h / 2)} L{fmt(x + w / 2 - 5)},{fmt(y - h / 2)} Q{fmt(x + w / 2)},{fmt(y - h / 2)} {fmt(x + w / 2)},{fmt(y - h / 2 + 5)} '
            f'L{fmt(x + w / 2)},{fmt(y + h / 2 - 5)} Q{fmt(x + w / 2)},{fmt(y + h / 2)} {fmt(x + w / 2 - 5)},{fmt(y + h / 2)} L{fmt(x - 2)},{fmt(y + h / 2)} '
            f'L{fmt(x - 9)},{fmt(y + h / 2 + 6)} L{fmt(x - 8)},{fmt(y + h / 2)} L{fmt(x - w / 2 + 5)},{fmt(y + h / 2)} Q{fmt(x - w / 2)},{fmt(y + h / 2)} '
            f'{fmt(x - w / 2)},{fmt(y + h / 2 - 5)} L{fmt(x - w / 2)},{fmt(y - h / 2 + 5)} Q{fmt(x - w / 2)},{fmt(y - h / 2)} {fmt(x - w / 2 + 5)},{fmt(y - h / 2)} Z" '
            f'fill="{p["paper"]}" {stroke(p)}/>' +
            ''.join(f'<circle cx="{fmt(x + dx)}" cy="{fmt(y)}" r="2" fill="{p["blue"]}"/>' for dx in (-6, 0, 6)))


def _tray(p, x0, x1, top, h, shade):
    blue = p['blue']
    return (f'<path d="M{_f(x0, top, x1, top, x1 - 2, top + h, x0 + 2, top + h)} Z" fill="{blue}" {stroke(p)}/>'
            f'<path d="M{_f(x1 - 12, top, x1, top, x1 - 2, top + h, x1 - 12, top + h)} Z" fill="{shade}"/>'
            f'<path d="M{fmt(x0 + 4)},{fmt(top + 4)} L{fmt(x1 - 16)},{fmt(top + 4)}" stroke="{mix(blue, "#ffffff", .4)}" stroke-width="2" stroke-linecap="round"/>'
            f'<path d="M{_f(x0, top, x1, top, x1 - 2, top + h, x0 + 2, top + h)} Z" fill="none" {stroke(p)}/>')


def scene_kits(dark=False):
    """25-kits, "Kit sources": the Diver bot peeks over an open diver's toolbox; developer tools fan out in the left tray,
    media tools in the right, and a checklist with green ticks is clipped to the front."""
    sc = Scene('25-kits', dark, seed=25, avoid=[(340, 740)], rays=6, glow=(540, -40, 380))
    p = sc.p
    cx = 540
    blue = p['blue']
    shade = mix(blue, p['line'], .38)
    inner = mix(p['line'], p['blue_deep'], .25)
    sc.under.append(sc.far_school(160, 66, 14, n=5, flip=True, seed=1))
    sc.body.append(sc.shadow(cx, FLOOR, 120, 9))
    # links from the trays down to the box sides
    md = p['metal_dk']
    for a in ('M404,140 L452,192', 'M434,140 L452,172', 'M676,140 L628,192', 'M646,140 L628,172'):
        sc.body.append(_thick(p, a, md, 4))
    # left tray: the developer tools
    sc.body.append(_wrench(p, 370, 132, 400, 82))
    for d in ('M410,100 L401,109 L410,118', 'M424,100 L433,109 L424,118'):
        sc.body.append(_thick(p, d, p['violet'], 3.6))
    sc.body.append(_gear(p, 446, 116, 11, p['gold']))
    sc.body.append(_tray(p, 358, 462, 122, 20, shade))
    # right tray: the media tools
    sc.body.append(_conch(p, 650, 106, 1.0, -20))
    sc.body.append(_camera(p, 692, 112, 6))
    sc.body.append(_speech(p, 706, 88))
    sc.body.append(_tray(p, 618, 722, 122, 20, shade))
    # the bot peeks over the back rim of the box
    rim = 156
    sc.body.append(sc.bot('peek', cx, rim - 2, height=68))
    sc.body.append(f'<path d="M{_f(452, rim, 628, rim, 636, rim + 11, 444, rim + 11)} Z" fill="{inner}" {stroke(p)}/>'
                   f'<path d="M{_f(450, rim - 2.5, 630, rim - 2.5, 630, rim + 2.5, 450, rim + 2.5)} Z" fill="{mix(blue, "#ffffff", .3)}" {stroke(p)}/>')
    # the box
    box = (f'M444,166 L636,166 L634,214 Q634,222 626,222 L454,222 Q446,222 446,214 Z')
    sc.body.append(f'<path d="{box}" fill="{blue}"/>'
                   f'<path d="M604,166 L636,166 L634,214 Q634,222 626,222 L604,222 Z" fill="{shade}"/>'
                   f'<rect x="442" y="164" width="196" height="9" rx="3" fill="{mix(blue, "#ffffff", .25)}" {stroke(p)}/>'
                   f'<path d="M454,180 L500,180" stroke="{mix(blue, "#ffffff", .45)}" stroke-width="2.2" stroke-linecap="round"/>'
                   f'<path d="M450,206 L630,206" stroke="{shade}" stroke-width="2" stroke-linecap="round"/>'
                   f'<path d="{box}" fill="none" {stroke(p)}/>')
    for lx in (472, 608):
        sc.body.append(f'<rect x="{lx - 7}" y="170" width="14" height="17" rx="3" fill="{p["gold"]}" {stroke(p)}/>'
                       f'<rect x="{lx - 3.5}" y="180" width="7" height="4" rx="1.5" fill="{p["gold_dk"]}"/>')
    # the checklist, clipped to the front
    sc.body.append(f'<rect x="521" y="178" width="38" height="38" rx="3" fill="{p["paper"]}" {stroke(p)}/>'
                   f'<rect x="532" y="174" width="16" height="7" rx="2" fill="{p["metal"]}" {stroke(p, .8)}/>' +
                   _check_chip(p, 526, 186) + _check_chip(p, 526, 201) +
                   f'<path d="M539,190.5 L553,190.5 M539,205.5 L550,205.5" stroke="{p["paper_line"]}" stroke-width="2" stroke-linecap="round"/>')
    for x, y, r in ((488, 104, 4.5), (596, 98, 5)):
        sc.body.append(_sparkle(x, y, r, p['gold_hi'] if not dark else p['gold'], .9))
    sc.body.append(sc.bubbles(560, 92, 46, 3.2, n=4, seed=3))
    sc.body.append(sc.fish(250, 138, 24, 'yellow', flip=True) + sc.fish(212, 164, 16, 'red', flip=True))
    sc.over.append(sc.seaweed(30, 118, phase=.6) + sc.seaweed(52, 80, p['weed_light'], width=4, phase=2.1))
    sc.over.append(sc.anemone(770, 16) + sc.coral(834, .4))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 40-sessions
def scene_sessions(dark=False):
    """40-sessions, "Sessions": the Diver bot waves from a seabed stage framed by kelp curtains, under a spotlight, beside a
    lectern and a presentation screen, with a front row of fish watching."""
    sc = Scene('40-sessions', dark, seed=40, avoid=[(270, 670)], rays=4, glow=(470, -40, 360))
    p = sc.p
    cx = 470
    body, top, shade = _rock(p)
    sc.under.append(sc.far_school(150, 70, 14, n=4, flip=True, seed=1) + sc.far_school(780, 60, 13, n=4, seed=2))
    # spotlight cone from the surface
    gid = sc.id('spot')
    beam = '#ffffff' if not dark else '#cfe0ff'
    sc.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{beam}" stop-opacity="{".85" if not dark else ".32"}"/>'
                   f'<stop offset="1" stop-color="{beam}" stop-opacity="{".15" if not dark else ".06"}"/></linearGradient>')
    sc.body.append(f'<path d="M{_f(cx - 30, 50, cx + 30, 50, cx + 80, 194, cx - 80, 194)} Z" fill="url(#{gid})"/>')
    # the stage
    sc.body.append(sc.shadow(cx, FLOOR + 2, 180, 8))
    stage = f'M{_f(296, 228, 298, 196)} Q300,188 312,188 L628,188 Q640,188 642,196 L644,228 Z'
    sc.body.append(f'<path d="{stage}" fill="{body}" {stroke(p)}/>'
                   f'<path d="M298,198 Q300,188 312,188 L628,188 Q640,188 642,198 Q470,204 298,198 Z" fill="{top}"/>'
                   f'<path d="M300,212 Q470,218 640,212" fill="none" stroke="{shade}" stroke-width="2" stroke-linecap="round"/>'
                   f'<path d="{stage}" fill="none" {stroke(p)}/>')
    sc.body.append(f'<ellipse cx="{cx}" cy="196" rx="74" ry="5.5" fill="{beam}" fill-opacity="{".7" if not dark else ".22"}"/>')
    # the screen on its stand
    md = mix(p['metal_dk'], p['line'], .3)
    sc.body.append(f'<path d="M562,150 L552,196 M562,150 L572,196 M562,150 L562,194" stroke="{md}" stroke-width="2.4" stroke-linecap="round"/>'
                   f'<rect x="522" y="98" width="80" height="54" rx="4" fill="{p["paper"]}" {stroke(p)}/>'
                   f'<rect x="527" y="103" width="70" height="44" rx="2" fill="{mix(p["glass_dk"], "#ffffff", .35)}"/>'
                   f'<path d="{oa.catmull(oa.sine_pts(527, 597, 134, 3, 23, step=4))} L597,147 L527,147 Z" fill="{p["blue"]}" fill-opacity=".85"/>'
                   + oa.mono_fish(560, 118, 22, p['blue_deep'], flip=True) +
                   f'<circle cx="586" cy="111" r="3.4" fill="{p["gold"]}"/>'
                   f'<rect x="522" y="98" width="80" height="54" rx="4" fill="none" {stroke(p)}/>')
    # the bot behind the lectern
    sc.body.append(sc.bot('wave', cx, 194))
    lec = mix(p['wood'], p['wood_dk'], .2)
    sc.body.append(f'<path d="M{_f(436, 162, 466, 162, 470, 195, 432, 195)} Z" fill="{lec}" {stroke(p)}/>'
                   f'<path d="M{_f(458, 162, 466, 162, 470, 195, 461, 195)} Z" fill="{p["wood_dk"]}" fill-opacity=".6"/>'
                   f'<path d="M{_f(428, 158, 472, 150, 476, 158, 432, 166)} Z" fill="{p["wood_hi"]}" {stroke(p)}/>'
                   f'<path d="M442,180 q4,-4 8,0 t8,0" fill="none" stroke="{p["wood_hi"]}" stroke-width="2" stroke-linecap="round"/>'
                   f'<path d="M{_f(436, 162, 466, 162, 470, 195, 432, 195)} Z" fill="none" {stroke(p)}/>')
    # kelp curtains and the swagged valance
    weed, weed_dk = p['weed'], mix(p['weed'], p['line'], .35)
    left = 'M292,30 L360,30 C356,74 336,126 322,150 C328,168 336,182 340,196 L292,196 Z'
    folds = 'M310,34 C312,80 314,120 312,150 M330,34 C330,80 324,124 316,150 M346,34 C344,84 330,126 320,150 M314,152 C314,170 318,184 320,194'
    for m in (False, True):
        g = f'<g transform="translate(940,0) scale(-1,1)">' if m else '<g>'
        sc.body.append(g + f'<path d="{left}" fill="{weed}" {stroke(p)}/>'
                       f'<path d="{folds}" fill="none" stroke="{weed_dk}" stroke-width="2" stroke-linecap="round"/>'
                       f'<path d="M300,40 C302,90 304,130 302,150" fill="none" stroke="{p["weed_light"]}" stroke-width="2.4" stroke-linecap="round" stroke-opacity=".8"/>'
                       f'<rect x="308" y="146" width="22" height="7" rx="3.5" fill="{p["gold"]}" {stroke(p, .8)}/></g>')
    val = 'M286,22 L654,22 L654,46 Q594,66 532,46 Q470,66 408,46 Q346,66 286,46 Z'
    sc.body.append(f'<path d="{val}" fill="{weed_dk}" {stroke(p)}/>'
                   f'<path d="M290,40 Q348,58 408,40 Q470,58 532,40 Q594,58 650,40" fill="none" stroke="{p["weed_light"]}" stroke-width="2" stroke-opacity=".7"/>')
    for x in (408, 532):
        sc.body.append(f'<path d="M{x},46 L{x},56" stroke="{p["gold_dk"]}" stroke-width="2"/><circle cx="{x}" cy="59" r="3.6" fill="{p["gold"]}" {stroke(p, .7)}/>')
    for x, tint in ((347, mix(p['blue'], '#ffffff', .35)), (470, p['fish_green']), (593, p['gold'])):
        sc.body.append(f'<path d="M{_f(x - 7, 56, x + 7, 56, x, 72)} Z" fill="{tint}" {stroke(p, .8)}/>'
                       f'<path d="M{x},50 L{x},56" stroke="{p["line"]}" stroke-width="1.2"/>')
    # the audience: a front row of fish silhouettes
    aud = mix(p['line'], p['near'], .25) if not dark else mix(p['band'], p['near'], .3)
    for x, y, ln, fl in ((352, 228, 30, True), (398, 232, 26, True), (548, 231, 28, False), (596, 227, 30, False), (640, 233, 24, False)):
        sc.over.append(oa.mono_fish(x, y, ln, aud, flip=fl))
    sc.over.append(sc.seaweed(30, 120, phase=1.0) + sc.seaweed(54, 82, p['weed_light'], width=4, phase=.2))
    sc.over.append(sc.coral(820, .38, flip=True) + sc.anemone(762, 14))
    sc.body.append(sc.fish(196, 120, 22, 'red', flip=True) + sc.fish(730, 120, 20, 'yellow'))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 50-maps
def scene_maps(dark=False):
    """50-maps, "Maps": the Diver bot sits reading beside a large map unrolled on the seabed, with a branching tree of
    routes, a dotted path to a marked spot and a compass rose; a rolled map and a compass lie nearby."""
    sc = Scene('50-maps', dark, seed=50, avoid=[(330, 750)], rays=6, glow=(560, -40, 380))
    p = sc.p
    body, top, shade = _rock(p)
    BY, FY, BL, BR, FL, FR = 142.0, 214.0, 412.0, 692.0, 380.0, 718.0

    def pr(u, v):
        xl, xr = BL + (FL - BL) * v, BR + (FR - BR) * v
        return xl + (xr - xl) * u, BY + (FY - BY) * v

    def sc_at(v):
        return .8 + .3 * v

    parch = mix(p['gold_hi'], '#ffffff', .5)
    parch_dk = mix(p['gold_hi'], p['wood_hi'], .55)
    ink = mix(p['wood_dk'], p['line'], .35)
    sc.under.append(sc.far_school(170, 70, 14, n=5, flip=True, seed=1))
    sc.body.append(sc.shadow(545, FY + 4, 190, 10))
    # parchment with a slightly ragged edge
    rnd = oa._rng('maps-edge')
    edge = []
    for side in range(4):
        for k in range(8):
            t = k / 8
            u, v = [(t, 0), (1, t), (1 - t, 1), (0, 1 - t)][side]
            x, y = pr(u, v)
            j = rnd.uniform(-1.6, 1.6)
            edge.append((x + (j if side in (1, 3) else 0), y + (j * .6 if side in (0, 2) else 0)))
    ed = oa.catmull(edge, closed=True, tension=.2)
    sc.body.append(f'<path d="{ed}" fill="{parch}" {stroke(p)}/>')
    inset = [pr(.035, .07), pr(.975, .07), pr(.975, .92), pr(.035, .92)]
    sc.body.append(f'<path d="M{" L".join(f"{fmt(a)},{fmt(b)}" for a, b in inset)} Z" fill="none" stroke="{parch_dk}" stroke-width="1.4" '
                   f'stroke-dasharray="5 3"/>')
    # soft creases (fold lines)
    for u in (1 / 3, 2 / 3):
        (x0, y0), (x1, y1) = pr(u, 0), pr(u, 1)
        sc.body.append(f'<path d="M{fmt(x0)},{fmt(y0)} L{fmt(x1)},{fmt(y1)}" stroke="{parch_dk}" stroke-width="1.6"/>')
    (x0, y0), (x1, y1) = pr(0, .5), pr(1, .5)
    sc.body.append(f'<path d="M{fmt(x0)},{fmt(y0)} L{fmt(x1)},{fmt(y1)}" stroke="{parch_dk}" stroke-width="1.2"/>')
    # the topic tree
    nodes = {'r': (.13, .6), 'a': (.3, .5), 'b1': (.46, .2), 'b2': (.48, .52), 'b3': (.45, .84),
             'c1': (.6, .1), 'c2': (.62, .3), 'c3': (.64, .48), 'c4': (.63, .66), 'c5': (.6, .9)}
    edges = [('r', 'a'), ('a', 'b1'), ('a', 'b2'), ('a', 'b3'), ('b1', 'c1'), ('b1', 'c2'), ('b2', 'c3'), ('b2', 'c4'), ('b3', 'c5')]
    d = ''
    for a, b in edges:
        (ua, va), (ub, vb) = nodes[a], nodes[b]
        (xa, ya), (xb, yb), (xm, ym) = pr(ua, va), pr(ub, vb), pr((ua + ub) / 2, va)
        d += f'M{fmt(xa)},{fmt(ya)} Q{fmt(xm)},{fmt(ym)} {fmt(xb)},{fmt(yb)} '
    sc.body.append(f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round"/>')
    cols = {'r': p['gold_dk'], 'a': ink, 'b1': 'slide', 'b2': 'docs', 'b3': 'stage', 'c1': 'slide', 'c2': 'slide', 'c3': 'docs',
            'c4': 'docs', 'c5': 'stage'}
    for k, (u, v) in nodes.items():
        x, y = pr(u, v)
        c = cols[k]
        c = oa.PALETTE['label_' + c][0] if c in ('slide', 'docs', 'stage') else c
        r = (6.4 if k == 'r' else 4.6 if len(k) == 1 or k.startswith('b') else 3.6) * sc_at(v)
        sc.body.append(f'<ellipse cx="{fmt(x)}" cy="{fmt(y)}" rx="{fmt(r)}" ry="{fmt(r * .62)}" fill="{c}" stroke="{p["paper"]}" stroke-width="1.2"/>')
    # the dotted route to the marked spot
    route = [pr(.63, .66), pr(.72, .78), pr(.8, .7), pr(.82, .5), pr(.87, .4)]
    sc.body.append(f'<path d="{oa.catmull(route)}" fill="none" stroke="{p["coral"]}" stroke-width="2.2" stroke-dasharray="1 4.4" stroke-linecap="round"/>')
    xx, xy_ = pr(.9, .34)
    sc.body.append(f'<path d="M{fmt(xx - 6)},{fmt(xy_ - 3.6)} L{fmt(xx + 6)},{fmt(xy_ + 3.6)} M{fmt(xx + 6)},{fmt(xy_ - 3.6)} L{fmt(xx - 6)},{fmt(xy_ + 3.6)}" '
                   f'stroke="{p["coral"]}" stroke-width="3" stroke-linecap="round"/>')
    # compass rose in the back corner
    rx_, ry_ = pr(.88, .12)
    rose = []
    for i in range(8):
        a = math.radians(i * 45)
        L = 12 if i % 2 == 0 else 7
        rose.append((f'M{fmt(rx_ + L * math.cos(a))},{fmt(ry_ + L * .5 * math.sin(a))} L{fmt(rx_ + 3 * math.cos(a + math.pi / 2))},{fmt(ry_ + 1.5 * math.sin(a + math.pi / 2))} '
                     f'L{fmt(rx_ + 3 * math.cos(a - math.pi / 2))},{fmt(ry_ + 1.5 * math.sin(a - math.pi / 2))} Z', i == 6))
    sc.body.append(f'<ellipse cx="{fmt(rx_)}" cy="{fmt(ry_)}" rx="9" ry="4.6" fill="none" stroke="{ink}" stroke-width="1.2"/>' +
                   ''.join(f'<path d="{d}" fill="{p["coral"] if n else ink}"/>' for d, n in rose))
    # left end still rolled, stones on the right corners
    (x0, y0), (x1, y1) = pr(0, 0), pr(0, 1)
    rl = f'M{fmt(x0 - 2)},{fmt(y0 - 2)} L{fmt(x1 - 2)},{fmt(y1)}'
    sc.body.append(_thick(p, rl, parch_dk, 11) +
                   f'<path d="M{fmt(x0 + 1)},{fmt(y0 + 2)} L{fmt(x1 + 1)},{fmt(y1 - 2)}" stroke="{parch}" stroke-width="3" stroke-linecap="round"/>'
                   f'<ellipse cx="{fmt(x1 - 2)}" cy="{fmt(y1)}" rx="5.5" ry="5.5" fill="{parch}" {stroke(p)}/>'
                   f'<path d="M{fmt(x1 - 2)},{fmt(y1)} m-2.6,0 a2.6,2.6 0 1 0 5.2,0" fill="none" stroke="{parch_dk}" stroke-width="1.4"/>')
    for x, y, rx, ry in ((690, 144, 16, 9), (718, 214, 19, 11)):
        sc.body.append(sc.shadow(x, y + ry - 2, rx * 1.1) +
                       f'<path d="M{fmt(x - rx)},{fmt(y + ry * .6)} C{fmt(x - rx)},{fmt(y - ry)} {fmt(x + rx)},{fmt(y - ry * 1.1)} {fmt(x + rx)},{fmt(y + ry * .6)} Z" fill="{body}" {stroke(p)}/>'
                       f'<path d="M{fmt(x - rx * .5)},{fmt(y - ry * .35)} Q{fmt(x)},{fmt(y - ry * .75)} {fmt(x + rx * .45)},{fmt(y - ry * .4)}" fill="none" stroke="{top}" stroke-width="2.4" stroke-linecap="round"/>')
    # a rolled second map behind, tied with a ribbon
    sc.body.append(sc.shadow(746, 196, 26) +
                   f'<g transform="rotate(-14 742 186)"><rect x="716" y="179" width="54" height="14" rx="7" fill="{parch}" {stroke(p)}/>'
                   f'<ellipse cx="770" cy="186" rx="3.6" ry="7" fill="{parch_dk}" {stroke(p, .8)}/>'
                   f'<rect x="738" y="178" width="5" height="16" fill="{p["coral"]}" {stroke(p, .7)}/></g>')
    # a real compass on the sand
    cxp, cyp = 352, 220
    sc.body.append(sc.shadow(cxp, cyp + 4, 15) +
                   f'<ellipse cx="{cxp}" cy="{cyp}" rx="14" ry="8.6" fill="{p["gold"]}" {stroke(p)}/>'
                   f'<ellipse cx="{cxp}" cy="{cyp - 1}" rx="10.5" ry="6" fill="{p["paper"]}" stroke="{p["gold_dk"]}" stroke-width="1.2"/>'
                   f'<path d="M{_f(cxp - 1.4, cyp - 1, cxp + 7, cyp - 4.5, cxp + 1.4, cyp)} Z" fill="{p["coral"]}"/>'
                   f'<path d="M{_f(cxp - 1.4, cyp - 1, cxp - 7, cyp + 2.5, cxp + 1.4, cyp)} Z" fill="{p["blue_deep"]}"/>'
                   f'<circle cx="{cxp}" cy="{cyp - 9}" r="2.6" fill="none" stroke="{p["gold_dk"]}" stroke-width="1.6"/>')
    sc.body.append(sc.shadow(296, FLOOR, 38))
    sc.body.append(sc.bot('read', 296, FLOOR))
    sc.body.append(sc.fish(560, 96, 20, 'yellow') + sc.school(160, 112, 16, 'blue', n=3, flip=True, seed=4))
    sc.over.append(sc.seaweed(30, 110, phase=.5) + sc.seaweed(52, 72, p['weed_light'], width=4, phase=1.8))
    sc.over.append(sc.coral(836, .36, flip=True) + sc.seaweed(806, 70, p['weed_light'], width=4, phase=.9))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 70-private
def _chain(p, x0, y0, x1, y1, bend, n):
    """A short chain of n links along a quadratic curve from (x0, y0) to (x1, y1), sagging by `bend`."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + bend
    m, out = p['metal'], ''
    for i in range(n):
        t = (i + .5) / n
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1
        dx = 2 * (1 - t) * (mx - x0) + 2 * t * (x1 - mx)
        dy = 2 * (1 - t) * (my - y0) + 2 * t * (y1 - my)
        ang = fmt(math.degrees(math.atan2(dy, dx)))
        if i % 2 == 0:
            out += (f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({ang})">'
                    f'<ellipse rx="5.2" ry="3.4" fill="none" stroke="{p["line"]}" stroke-width="4.6"/>'
                    f'<ellipse rx="5.2" ry="3.4" fill="none" stroke="{m}" stroke-width="2"/></g>')
        else:
            out += (f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({ang})">'
                    f'<rect x="-5.6" y="-1.6" width="11.2" height="3.2" rx="1.6" fill="{p["metal_dk"]}" {stroke(p, .8)}/></g>')
    return out


def _ring(p, x, y, r=5.6):
    return (f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="none" stroke="{p["line"]}" stroke-width="5.6"/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="none" stroke="{p["metal"]}" stroke-width="2.6"/>'
            f'<path d="M{fmt(x - r * .7)},{fmt(y - r * .7)} A{fmt(r)},{fmt(r)} 0 0 1 {fmt(x + r * .2)},{fmt(y - r)}" fill="none" '
            f'stroke="{p["metal_hi"]}" stroke-width="1.2" stroke-linecap="round"/>')


def padlock(p, x, y):
    """A gold padlock, shackle top at about (x, y - 12), body centred on (x, y + 8)."""
    sh = f'M{fmt(x - 8)},{fmt(y)} L{fmt(x - 8)},{fmt(y - 5)} A8,8 0 0 1 {fmt(x + 8)},{fmt(y - 5)} L{fmt(x + 8)},{fmt(y)}'
    return (f'<path d="{sh}" fill="none" stroke="{p["line"]}" stroke-width="5.8"/>'
            f'<path d="{sh}" fill="none" stroke="{p["metal"]}" stroke-width="3"/>'
            f'<rect x="{fmt(x - 14)}" y="{fmt(y - 1)}" width="28" height="24" rx="5" fill="{p["gold"]}" {stroke(p)}/>'
            f'<path d="M{fmt(x + 7)},{fmt(y)} L{fmt(x + 13)},{fmt(y)} L{fmt(x + 13)},{fmt(y + 21)} L{fmt(x + 7)},{fmt(y + 21)} Z" fill="{p["gold_dk"]}"/>'
            f'<path d="M{fmt(x - 10)},{fmt(y + 3)} L{fmt(x + 2)},{fmt(y + 3)}" stroke="{p["gold_hi"]}" stroke-width="2" stroke-linecap="round"/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y + 10)}" r="3.2" fill="{p["line"]}"/>'
            f'<path d="M{fmt(x)},{fmt(y + 11)} L{fmt(x)},{fmt(y + 17)}" stroke="{p["line"]}" stroke-width="2.8" stroke-linecap="round"/>'
            f'<rect x="{fmt(x - 14)}" y="{fmt(y - 1)}" width="28" height="24" rx="5" fill="none" {stroke(p)}/>')


def scene_private(dark=False):
    """70-private, "Private notes": a giant clam shut tight, its wavy lips sealed by a gold padlock and a short chain
    between two rings, a faint glow at the seam and a starfish on top; the Diver bot stands guard on the right."""
    sc = Scene('70-private', dark, seed=70, avoid=[(270, 570)], rays=4, glow=(420, -40, 340))
    p = sc.p
    cx, seam, w = 420, 170, 250
    x0, x1 = cx - w / 2, cx + w / 2
    top_y, folds, amp = seam - 70, 5, 8.5
    shell = mix(p['pearl'], p['violet_lt'], .16)
    band = mix(p['pearl_sh'], p['violet_lt'], .4)
    low, low_band = mix(p['pearl_sh'], p['metal'], .4), mix(p['metal'], p['violet_lt'], .25)

    def wy(x):
        return seam + amp * math.sin(2 * math.pi * folds * (x - x0) / w)

    xs = [x0 + w * i / 60 for i in range(61)]
    wave = ' '.join(f'{fmt(x)},{fmt(wy(x))}' for x in xs)
    wave_back = ' '.join(f'{fmt(x)},{fmt(wy(x))}' for x in reversed(xs))
    upper = (f'M{fmt(x0)},{seam} C{fmt(x0)},{fmt(seam - 56)} {fmt(cx - 78)},{fmt(top_y)} {cx},{fmt(top_y)} '
             f'C{fmt(cx + 78)},{fmt(top_y)} {fmt(x1)},{fmt(seam - 56)} {fmt(x1)},{seam} L{wave_back} Z')
    lower = (f'M{wave} C{fmt(x1 - 4)},{fmt(seam + 34)} {fmt(cx + 72)},{FLOOR - 2} {cx},{FLOOR - 2} '
             f'C{fmt(cx - 72)},{FLOOR - 2} {fmt(x0 + 4)},{fmt(seam + 34)} {fmt(x0)},{seam} Z')
    cu, cl = sc.id('upper'), sc.id('lower')
    sc.defs.append(f'<clipPath id="{cu}"><path d="{upper}"/></clipPath><clipPath id="{cl}"><path d="{lower}"/></clipPath>')
    sc.under.append(sc.far_school(744, 66, 14, n=4, seed=1))
    sc.body.append(sc.shadow(cx, FLOOR, 146, 10))
    # sea grass behind
    grass = ''
    for x, h, lean, c in ((292, 34, -.5, 'weed'), (306, 22, -.2, 'weed_light'), (282, 20, -.8, 'weed_light'),
                          (536, 30, .45, 'weed'), (550, 22, .7, 'weed_light'), (560, 36, .5, 'weed')):
        grass += (f'<path d="M{x},{FLOOR} Q{fmt(x + lean * h * .3)},{fmt(FLOOR - h * .6)} {fmt(x + lean * h)},{fmt(FLOOR - h)}" fill="none" '
                  f'stroke="{p[c]}" stroke-width="3.6" stroke-linecap="round"/>')
    sc.body.append(grass)
    sc.body.append(_glow(sc, 'seam', cx, seam, 160, 36, p['violet_lt'], .75 if not dark else .8))
    # folds: a darker band for every second half-wave of the lips, narrowing towards the hinge
    def bands(clip, fill, apex_y, k_apex, sign):
        out = ''
        for i in range(2 * folds):
            if (i % 2 == 0) != (sign > 0):
                continue
            xa, xb = x0 + w * i / (2 * folds), x0 + w * (i + 1) / (2 * folds)
            seg = ' '.join(f'{fmt(x)},{fmt(wy(x))}' for x in (xa + (xb - xa) * j / 6 for j in range(7)))
            out += (f'<path d="M{seg} L{fmt(cx + (xb - cx) * k_apex)},{fmt(apex_y)} L{fmt(cx + (xa - cx) * k_apex)},{fmt(apex_y)} Z"/>')
        return f'<g clip-path="url(#{clip})" fill="{fill}">{out}</g>'
    sc.body.append(f'<path d="{lower}" fill="{low}"/>' + bands(cl, low_band, FLOOR, .3, -1) + f'<path d="{lower}" fill="none" {stroke(p)}/>')
    sc.body.append(f'<path d="{upper}" fill="{shell}"/>' + bands(cu, band, top_y, .22, 1) +
                   f'<path d="M{fmt(cx + 30)},{fmt(top_y + 1)} C{fmt(cx + 90)},{fmt(top_y + 4)} {fmt(x1 - 2)},{fmt(seam - 40)} {fmt(x1)},{seam} '
                   f'L{fmt(x1 - 20)},{fmt(seam - 4)} C{fmt(x1 - 26)},{fmt(seam - 36)} {fmt(cx + 76)},{fmt(top_y + 12)} {fmt(cx + 30)},{fmt(top_y + 1)} Z" '
                   f'fill="{p["line"]}" fill-opacity=".1"/>'
                   f'<path d="M{fmt(cx - 84)},{fmt(top_y + 18)} Q{fmt(cx - 44)},{fmt(top_y + 3)} {fmt(cx + 4)},{fmt(top_y + 3)}" fill="none" '
                   f'stroke="#ffffff" stroke-width="3.2" stroke-linecap="round" stroke-opacity=".9"/>'
                   f'<path d="{upper}" fill="none" {stroke(p)}/>')
    # the glowing seam between the lips
    sc.body.append(f'<path d="M{wave}" fill="none" stroke="{p["violet_lt"]}" stroke-width="3.6" stroke-linecap="round"/>'
                   f'<path d="M{wave}" fill="none" stroke="#ffffff" stroke-width="1.2" stroke-opacity=".9"/>')
    # starfish resting on top
    sf = p['coral']
    sc.body.append(f'<g transform="translate(486,{fmt(top_y + 4)}) scale(1,.6)">' + oa.starfish(0, 0, 15, sf, rot=14) +
                   ''.join(f'<circle cx="{fmt(7 * math.cos(math.radians(a)))}" cy="{fmt(7 * math.sin(math.radians(a)))}" r="1.2" '
                           f'fill="{mix(sf, "#ffffff", .45)}"/>' for a in range(-76, 284, 72)) + '</g>')
    # two rings, a short chain through them and the padlock closing it
    r1, r2, lk = (cx - 34, seam - 20), (cx + 34, seam + 24), (cx + 2, seam + 2)
    sc.body.append(_glow(sc, 'lock', lk[0], lk[1] + 10, 34, 28, p['gold'], .45))
    sc.body.append(_ring(p, *r1) + _ring(p, *r2))
    sc.body.append(_chain(p, r1[0] + 4, r1[1] + 4, lk[0] - 6, lk[1] - 4, 6, 4) + _chain(p, lk[0] + 6, lk[1] - 4, r2[0] - 3, r2[1] - 4, 8, 4))
    sc.body.append(padlock(p, *lk))
    # the bot stands guard on the right
    sc.body.append(sc.shadow(652, FLOOR, 40))
    sc.body.append(sc.bot('point', 652, FLOOR, flip=True))
    sc.body.append(sc.fish(730, 98, 18, 'blue', flip=True))
    sc.over.append(sc.seaweed(30, 116, phase=1.4) + sc.seaweed(52, 80, p['weed_light'], width=4, phase=.6))
    sc.over.append(sc.anemone(774, 14) + sc.coral(836, .38))
    return sc.render()


SCENES = {
    'root': scene_root,
    '00-raw': scene_raw,
    '10-sources': scene_sources,
    '20-claims': scene_claims,
    '25-kits': scene_kits,
    '40-sessions': scene_sessions,
    '50-maps': scene_maps,
    '70-private': scene_private,
}
