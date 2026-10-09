"""README illustrations, group C: topic areas about results and people: serving and ranking, trends, Search Console, the state of Search, AI features, publisher controls, community.

Build every scene with illus_common.Scene; see illus_a.scene_claims (20-claims) for the reference scene.
"""
import math

from illus_common import oa
from illus_common import (FLOOR, H, W, Scene, catmull, fmt, mix, stroke)   # noqa: F401


# ------------------------------------------------------------------------------------------------------------ helpers
def _rect(x, y, w, h, rx, fill, extra=''):
    return (f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" rx="{fmt(rx)}" fill="{fill}"'
            + (f' {extra}' if extra else '') + '/>')


def _circle(x, y, r, fill, extra=''):
    return f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{fill}"' + (f' {extra}' if extra else '') + '/>'


def _line(d, color, width, op=1.0, cap='round'):
    o = f' stroke-opacity="{fmt(op, 2)}"' if op < 1 else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{fmt(width)}" stroke-linecap="{cap}" stroke-linejoin="round"{o}/>'


def _glint(x, y, r, color, op=1.0):
    """A small four-point glint (never used in the AI card)."""
    k = r * 0.28
    d = (f'M{fmt(x)},{fmt(y - r)} Q{fmt(x + k)},{fmt(y - k)} {fmt(x + r)},{fmt(y)} Q{fmt(x + k)},{fmt(y + k)} {fmt(x)},{fmt(y + r)} '
         f'Q{fmt(x - k)},{fmt(y + k)} {fmt(x - r)},{fmt(y)} Q{fmt(x - k)},{fmt(y - k)} {fmt(x)},{fmt(y - r)} Z')
    return f'<path d="{d}" fill="{color}" fill-opacity="{fmt(op, 2)}"/>'


def _wavy(x0, y0, x1, y1, amp, waves, n=9, phase=0.0):
    """Points along a line from (x0, y0) to (x1, y1), swaying sideways like a ribbon (more towards the end)."""
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln, dx / ln
    pts = []
    for i in range(n):
        t = i / (n - 1)
        s = amp * math.sin(t * waves * 2 * math.pi + phase) * (0.35 + 0.65 * t)
        pts.append((x0 + dx * t + nx * s, y0 + dy * t + ny * s))
    return pts


def _ball(p, x, y, r, color, outline=True):
    """A glossy coloured ball (knobs, blips, bubble-bars): a darker crescent, the body, a highlight."""
    out = (_circle(x, y, r, mix(color, p['line'], .28)) + _circle(x - r * .14, y - r * .14, r * .82, color)
           + _circle(x - r * .36, y - r * .36, r * .26, '#ffffff', 'fill-opacity=".85"'))
    if outline:
        out += _circle(x, y, r, 'none', stroke(p, .8))
    return out


def _paper(p, cx, cy, rot, w, h, ink, lines=3):
    """A page card: white paper, a coloured header bar, a few grey lines."""
    x0, y0 = -w / 2, -h / 2
    ls = ''.join(f'M{fmt(x0 + 5)},{fmt(y0 + 14 + i * 5.5)} L{fmt(-x0 - 5 - (i % 2) * 6)},{fmt(y0 + 14 + i * 5.5)} '
                 for i in range(lines))
    return (f'<g transform="translate({fmt(cx)},{fmt(cy)}) rotate({fmt(rot)})">'
            + _rect(x0, y0, w, h, 3, p['paper'], stroke(p))
            + _rect(x0 + 4, y0 + 4, w - 8, 5, 2, ink)
            + _line(ls.strip(), p['paper_line'], 1.8)
            + '</g>')


# ------------------------------------------------------------------------------------------------------------ 30-topics-serving-ranking
def _podium_step(p, x0, w, top, base, cap, n, dot):
    st = stroke(p)
    h = base - top
    cx = x0 + w / 2
    my = top + 8 + (h - 8) / 2
    mr = min(11.0, (h - 10) / 2)
    out = [_rect(x0, top, w, h, 4, p['pearl'], st),
           _rect(x0 + w - 15, top + 3, 12, h - 5, 3, p['pearl_sh']),
           _rect(x0 + 5, top + 10, 4, h - 14, 2, p['pearl_hi']),
           _circle(cx, my, mr, mix(dot, '#ffffff', .72), stroke(p, .7))]
    for i in range(n):
        dx = (i - (n - 1) / 2) * mr * .62
        out.append(_circle(cx + dx, my, mr * .24, dot))
    out.append(_rect(x0 - 3, top - 5, w + 6, 10, 4, cap, st))
    out.append(_line(f'M{fmt(x0 + 3)},{fmt(top - 2)} L{fmt(x0 + w - 3)},{fmt(top - 2)}', mix(cap, '#ffffff', .45), 1.8))
    return ''.join(out)


def _medal_fish(sc, x, y, length, color, medal, ribbon):
    """A fish (nose left) wearing a medal on a ribbon round its gills."""
    p, L = sc.p, length
    cx, cy, r = x - .04 * L, y + .06 * L, .13 * L
    tails = ''
    for side in (-1, 1):       # two short notched ribbon tails under the rosette, splayed outwards
        a = (cx + side * .02 * L, cy)
        b = (cx + side * .1 * L, cy)
        c = (cx + side * .17 * L, cy + .34 * L)
        n = (cx + side * .115 * L, cy + .29 * L)
        d = (cx + side * .07 * L, cy + .36 * L)
        tails += (f'<path d="M{fmt(a[0])},{fmt(a[1])} L{fmt(b[0])},{fmt(b[1])} L{fmt(c[0])},{fmt(c[1])} L{fmt(n[0])},{fmt(n[1])} '
                  f'L{fmt(d[0])},{fmt(d[1])} Z" fill="{ribbon if side < 0 else mix(ribbon, "#ffffff", .25)}" {stroke(p, .7)}/>')
    rosette = (_circle(cx, cy, r * 1.18, mix(ribbon, '#ffffff', .2), stroke(p, .7)) + _ball(p, cx, cy, r * .82, medal))
    return sc.fish(x, y, L, color) + tails + rosette


def scene_serving(dark=False):
    """30-topics-serving-ranking, "Serving and ranking": three fish with medals on a three-step podium, a short orderly queue
    waiting on the right, a tiny results card with three ranked lines, and the Diver bot pointing as the referee."""
    sc = Scene('30-topics-serving-ranking', dark, seed=31, avoid=[(400, 680)], rays=6, glow=(560, -30, 360))
    p = sc.p
    gold, silver, bronze = p['gold'], p['pearl_sh'], p['coral']
    blue = oa.PALETTE['label_slide'][0]
    sc.under.append(sc.far_school(170, 70, 14, n=4, flip=True, seed=1))
    # glow behind the winner
    g = sc.radial('win', p['gold'], .55 if not dark else .45, .3)
    sc.body.append(f'<ellipse cx="540" cy="118" rx="120" ry="78" fill="{g}"/>')
    sc.body.append(sc.shadow(540, FLOOR, 140, 7))
    sc.body.append(sc.shadow(322, FLOOR, 40))
    # podium: second (left), third (right), first (centre, tallest) drawn last
    sc.body.append(_podium_step(p, 422, 78, FLOOR - 46, FLOOR, mix(blue, '#ffffff', .25), 2, silver if not dark else p['metal']))
    sc.body.append(_podium_step(p, 580, 78, FLOOR - 30, FLOOR, mix(blue, '#ffffff', .25), 3, bronze))
    sc.body.append(_podium_step(p, 496, 88, FLOOR - 70, FLOOR, blue, 1, gold))
    # the medallists
    sc.body.append(_medal_fish(sc, 461, FLOOR - 76, 44, 'blue', p['pearl'], oa.PALETTE['label_slide'][0]))
    sc.body.append(_medal_fish(sc, 619, FLOOR - 60, 42, 'yellow', p['coral'], oa.PALETTE['label_stage'][0]))
    sc.body.append(_medal_fish(sc, 541, FLOOR - 102, 50, 'red', p['gold'], oa.PALETTE['label_slide'][0]))
    for x, y, r, o in ((506, 98, 5.5, .95), (578, 86, 4, .8), (590, 116, 3, .7), (497, 128, 3, .6)):
        sc.body.append(_glint(x, y, r, p['gold_hi'] if not dark else p['gold'], o))
    # the queue waiting its turn (retrieval): small fish in a neat line on a dotted lane
    sc.body.append(_line('M690,104 L800,104', p['paper_line'], 1.6, .7).replace('/>', ' stroke-dasharray="1 6"/>'))
    for i, (col, ln) in enumerate((('blue', 20), ('blue', 19), ('blue', 18), ('blue', 17))):   # one colour: no four-colour row
        sc.body.append(sc.fish(706 + i * 27, 94, ln, col))
    # a tiny results card: three ranked rows (gold, pearl, coral dots; the first bar longest)
    card = [_rect(-27, -24, 54, 48, 6, p['paper'], stroke(p)), _rect(-27, -24, 54, 9, 4, p['paper_sh'])]
    for i, (c, ln) in enumerate(((gold, 30), (p['metal'], 24), (bronze, 19))):
        yy = -9 + i * 11
        card.append(_circle(-17, yy, 3.4, c, stroke(p, .5)))
        card.append(_line(f'M-9,{yy} L{-9 + ln},{yy}', blue if i == 0 else p['paper_line'], 3))
    sc.body.append(f'<g transform="translate(392,96) rotate(-7)">' + ''.join(card) + '</g>')
    sc.body.append(sc.bubble(372, 60, 3.4) + sc.bubble(380, 48, 2.2))
    sc.body.append(sc.bot('point', 322, FLOOR))
    # dressing
    sc.body.append(sc.fish(150, 96, 24, 'yellow', flip=True))
    sc.over.append(sc.seaweed(30, 118, phase=.8) + sc.seaweed(52, 80, p['weed_light'], width=4, phase=2.2))
    sc.over.append(sc.coral(812, .38, flip=True))
    sc.over.append(sc.anemone(760, 15))
    sc.over.append(sc.seaweed(856, 92, p['weed_light'], width=4, phase=1.3))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 30-topics-search-trends
def scene_trends(dark=False):
    """30-topics-search-trends, "Search trends": columns of bubbles rising across the seabed like a bar chart, a kelp strand
    tracing the climbing trend over their tops, a small flag on the spike, and the Diver bot reading on the right."""
    sc = Scene('30-topics-search-trends', dark, seed=32, avoid=[(210, 600)], rays=6, glow=(420, -30, 380))
    p = sc.p
    lo, hi = (mix(p['glass_dk'], '#ffffff', .2), '#2f6fe0') if not dark else ('#5f86d6', '#4f9df2')
    counts = (2, 3, 2, 4, 6, 7)
    xs = [262 + i * 56 for i in range(6)]
    r, step, base = 10.5, 19.5, FLOOR - 14
    # chart frame: faint gridlines and a slim metal base
    grid = ' '.join(f'M232,{fmt(base + r - k * 39)} L586,{fmt(base + r - k * 39)}' for k in (1, 2, 3))
    sc.body.append(_line(grid, p['paper_line'], 1.2, .55).replace('/>', ' stroke-dasharray="2 5"/>'))
    sc.body.append(sc.shadow(408, FLOOR, 190, 6))
    sc.body.append(_rect(228, base + r + 1, 362, 8, 4, p['metal'], stroke(p)))
    sc.body.append(_line(f'M234,{fmt(base + r + 3.5)} L584,{fmt(base + r + 3.5)}', p['metal_hi'], 1.6))
    tops = []
    for i, (x, n) in enumerate(zip(xs, counts)):
        c = mix(lo, hi, i / 5)
        for k in range(n):
            y = base - k * step
            sc.body.append(_ball(p, x, y, r * (1 - .03 * k), c))
        tops.append((x, base - (n - 1) * step - r))
    # kelp strand tracing the trend: rooted on the left, climbing over the tops of the columns
    pts = [(236, base + r)] + [(x, y - 12) for x, y in tops] + [(612, tops[-1][1] - 30)]
    kelp = catmull(pts, tension=.5)
    sc.body.append(_line(kelp, mix(p['weed'], p['line'], .15), 5.4))
    sc.body.append(_line(kelp, p['weed'], 3.2))
    for i, (x, y) in enumerate(pts[1:]):
        s = -1 if i % 2 else 1
        a = -35 * s - 20
        sc.body.append(f'<ellipse cx="{fmt(x + 5)}" cy="{fmt(y - 2 * s)}" rx="8" ry="3.2" fill="{p["weed_light"]}" '
                       f'transform="rotate({fmt(a)} {fmt(x)} {fmt(y)})"/>')
    ex, ey = pts[-1]
    sc.body.append(f'<ellipse cx="{fmt(ex + 3)}" cy="{fmt(ey - 4)}" rx="9" ry="4.2" fill="{p["weed"]}" '
                   f'transform="rotate(-38 {fmt(ex)} {fmt(ey)})"/>')
    # a little flag on the spike (column 5)
    fx, fy = tops[4]
    sc.body.append(_line(f'M{fmt(fx + 4)},{fmt(fy + 2)} L{fmt(fx + 4)},{fmt(fy - 30)}', p['line'], 1.8))
    sc.body.append(f'<path d="M{fmt(fx + 5)},{fmt(fy - 30)} L{fmt(fx + 24)},{fmt(fy - 24)} L{fmt(fx + 5)},{fmt(fy - 18)} Z" '
                   f'fill="{p["coral"]}" {stroke(p, .8)}/>')
    sc.body.append(sc.bubbles(xs[-1] + 2, tops[-1][1] - 44, 40, 3.4, n=3, seed=2))
    # the Diver bot reads on a flat rock at the right
    sc.body.append(sc.shadow(690, FLOOR, 52))
    sc.body.append(f'<path d="M640,{FLOOR} C640,206 652,200 690,200 C728,200 742,206 742,{FLOOR} Z" fill="{mix(p["mid"], p["near"], .5)}" '
                   f'{stroke(p)}/>')
    sc.body.append(_line('M652,206 C668,203 690,203 708,204', p['dot_mid'] if not dark else p['dot_near'], 2.2))
    sc.body.append(sc.bot('read', 690, 204, height=100, flip=True))
    # dressing
    sc.body.append(sc.school(118, 70, 18, 'blue', n=4, flip=True, seed=4))
    sc.over.append(sc.seaweed(34, 112, phase=.2) + sc.seaweed(56, 74, p['weed_light'], width=4, phase=2.0))
    sc.over.append(sc.anemone(790, 14))
    sc.over.append(sc.coral(842, .34))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 30-topics-search-console
def _sector(cx, cy, r, a0, a1):
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    return f'M{fmt(cx)},{fmt(cy)} L{fmt(x0)},{fmt(y0)} A{fmt(r)},{fmt(r)} 0 0 1 {fmt(x1)},{fmt(y1)} Z'


def _gauge(p, cx, cy, r, needle, screen):
    """A round dial: pearl face, a coloured arc of ticks, a needle at `needle` degrees (0 = left, 180 = right)."""
    st = stroke(p)
    out = [_circle(cx, cy, r, p['metal'], st), _circle(cx, cy, r - 3, p['pearl'])]
    for k, col in ((0, p['fish_green']), (1, p['gold']), (2, p['coral'])):
        a0, a1 = 200 + k * 47, 200 + (k + 1) * 47 - 4
        rr = r - 6
        x0, y0 = cx + rr * math.cos(math.radians(a0)), cy + rr * math.sin(math.radians(a0))
        x1, y1 = cx + rr * math.cos(math.radians(a1)), cy + rr * math.sin(math.radians(a1))
        out.append(_line(f'M{fmt(x0)},{fmt(y0)} A{fmt(rr)},{fmt(rr)} 0 0 1 {fmt(x1)},{fmt(y1)}', col, 2.6, cap='butt'))
    a = math.radians(180 + needle)
    out.append(_line(f'M{fmt(cx)},{fmt(cy)} L{fmt(cx + (r - 6) * math.cos(a))},{fmt(cy + (r - 6) * math.sin(a))}', p['line'], 2))
    out.append(_circle(cx, cy, 2.4, p['line']))
    return ''.join(out)


def scene_console(dark=False):
    """30-topics-search-console, "Search Console": a sonar dashboard on the seabed: a big round sonar screen with rings, a
    sweep and blips, a small line-chart screen, two gauges and a row of toggles, with the Diver bot pointing at it."""
    sc = Scene('30-topics-search-console', dark, seed=33, avoid=[(400, 700)], rays=6, glow=(520, -30, 380))
    p = sc.p
    st = stroke(p)
    scr_top, scr_bot = '#0e2a5c', '#0b1b3d'
    teal = '#7fd6b9'
    sc.under.append(sc.far_school(720, 64, 14, n=4, seed=1))
    # the screen glow (stronger at night)
    g = sc.radial('sonar', teal, .35 if not dark else .5, .3)
    sc.body.append(f'<ellipse cx="510" cy="106" rx="104" ry="78" fill="{g}"/>')
    sc.body.append(sc.shadow(548, FLOOR, 140, 7))
    sc.body.append(sc.shadow(342, FLOOR, 40))
    # cable trailing off to the right along the seabed
    sc.body.append(_line('M664,212 C700,216 720,224 760,222 C800,220 830,226 900,224', p['metal_dk'], 3.4))
    # desk: legs, body, top slab, front panel with toggles and lights
    for lx in (436, 652):
        sc.body.append(_rect(lx, 206, 14, FLOOR - 206, 3, p['metal_dk'], st))
    sc.body.append(_rect(420, 168, 254, 42, 7, p['metal_hi'], st))
    sc.body.append(_rect(640, 170, 32, 38, 6, p['metal'], 'fill-opacity=".55"'))
    sc.body.append(_rect(412, 160, 270, 11, 4, p['metal'], st))
    sc.body.append(_line('M418,163 L676,163', p['metal_hi'], 1.6))
    for i in range(5):
        tx = 450 + i * 26
        up = i in (0, 2, 3)
        sc.body.append(_rect(tx - 6, 180, 12, 20, 5, p['line']))
        sc.body.append(_ball(p, tx, 185 if up else 195, 4, p['pearl'], outline=False))
    for i, c in enumerate((p['fish_green'], p['fish_green'], p['gold'])):
        sc.body.append(_circle(600 + i * 14, 190, 3.6, c, stroke(p, .6)))
    # sonar: bezel on a neck, deep screen, rings, sweep, blips
    cx, cy, R = 506, 102, 54
    sc.body.append(_rect(494, 150, 24, 14, 3, p['metal_dk'], st))
    sc.body.append(_circle(cx, cy, R, p['metal'], st))
    sc.body.append(_circle(cx, cy, R - 4, p['metal_dk']))
    scr = sc.linear('scr', [(0, scr_top), (1, scr_bot)])
    sc.body.append(_circle(cx, cy, R - 8, scr))
    rings = ''.join(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none"/>' for rr in (12, 24, 36))
    sc.body.append(f'<g stroke="{teal}" stroke-opacity=".45" stroke-width="1.2">{rings}'
                   f'<path d="M{cx - 46},{cy} L{cx + 46},{cy} M{cx},{cy - 46} L{cx},{cy + 46}" stroke-opacity=".25"/></g>')
    for a0, op in ((-110, .1), (-75, .16), (-50, .24)):
        sc.body.append(f'<path d="{_sector(cx, cy, 45, a0, -28)}" fill="{teal}" fill-opacity="{op}"/>')
    a = math.radians(-28)
    sc.body.append(_line(f'M{cx},{cy} L{fmt(cx + 45 * math.cos(a))},{fmt(cy + 45 * math.sin(a))}', teal, 2))
    for bx, by, br, c in ((cx + 22, cy - 22, 3.4, p['gold']), (cx - 18, cy + 14, 2.8, p['coral']), (cx + 10, cy + 28, 2.4, teal),
                          (cx - 26, cy - 12, 2.2, teal)):
        sc.body.append(_circle(bx, by, br * 2.2, c, 'fill-opacity=".2"') + _circle(bx, by, br, c))
    sc.body.append(f'<path d="M{cx - 40},{cy - 24} A46,46 0 0 1 {cx - 12},{cy - 43}" fill="none" stroke="#ffffff" '
                   f'stroke-opacity=".35" stroke-width="3" stroke-linecap="round"/>')
    # side panel: a little line chart and two gauges
    sc.body.append(_rect(574, 64, 102, 96, 8, p['metal_hi'], st))
    sc.body.append(_rect(582, 72, 86, 40, 4, scr))
    sc.body.append(_line('M586,104 L664,104', teal, 1, .3))
    chart = 'M588,102 L600,96 L612,99 L624,90 L636,92 L648,82 L662,78'
    sc.body.append(f'<path d="{chart} L662,108 L588,108 Z" fill="{teal}" fill-opacity=".18"/>')
    sc.body.append(_line(chart, teal, 2))
    sc.body.append(_circle(662, 78, 2.6, p['gold']))
    sc.body.append(_gauge(p, 602, 135, 16, 50, scr))
    sc.body.append(_gauge(p, 648, 135, 16, 128, scr))
    sc.body.append(sc.bot('point', 342, FLOOR))
    # dressing
    sc.body.append(sc.fish(176, 88, 24, 'red', flip=True))
    sc.over.append(sc.seaweed(30, 120, phase=1.2) + sc.seaweed(54, 82, p['weed_light'], width=4, phase=.4))
    sc.over.append(sc.anemone(764, 16))
    sc.over.append(sc.coral(826, .36))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 30-topics-search-landscape
def _manta(x, y, w, color, op=1.0):
    """A distant manta ray seen from above, gliding: wide curved wings, two head lobes, a thin tail."""
    s = w / 100
    half = [(0, -9), (6, -12), (16, -11), (30, -6), (50, 6), (34, 5), (20, 9), (10, 17), (0, 19)]
    pts = half + [(-px, py) for px, py in reversed(half[1:-1])]
    d = 'M' + ' L'.join(f'{fmt(x + px * s)},{fmt(y + py * s)}' for px, py in pts) + ' Z'
    lobes = f'M{fmt(x - 4 * s)},{fmt(y - 9 * s)} l{fmt(-2 * s)},{fmt(-5 * s)} M{fmt(x + 4 * s)},{fmt(y - 9 * s)} l{fmt(2 * s)},{fmt(-5 * s)}'
    o = f' fill-opacity="{fmt(op, 2)}"' if op < 1 else ''
    return (f'<path d="{d}" fill="{color}"{o} stroke="{color}" stroke-width="{fmt(3 * s)}" stroke-linejoin="round"/>'
            + _line(lobes + f' M{fmt(x)},{fmt(y + 18 * s)} q{fmt(2 * s)},{fmt(14 * s)} {fmt(-3 * s)},{fmt(28 * s)}', color, 1.6 * s, op))


def _spire(x, base, h, w, color):
    """A distant rock spire (sea stack) rising from a ridge."""
    return (f'<path d="M{fmt(x - w / 2)},{fmt(base)} C{fmt(x - w * .45)},{fmt(base - h * .55)} {fmt(x - w * .3)},{fmt(base - h)} {fmt(x)},{fmt(base - h)} '
            f'C{fmt(x + w * .3)},{fmt(base - h)} {fmt(x + w * .4)},{fmt(base - h * .5)} {fmt(x + w / 2)},{fmt(base)} Z" fill="{color}"/>')


def scene_landscape(dark=False):
    """30-topics-search-landscape, "The state of Search": a wide panorama. The Diver bot stands on a rocky outcrop on the left
    and points out over a deep valley of receding ridges, spires and distant reefs, a winding path leading to a bright horizon."""
    sc = Scene('30-topics-search-landscape', dark, seed=34, avoid=[(380, 880)], rays=7, glow=(740, 150, 320), decor=False)
    p = sc.p
    rnd = oa._rng('30-topics-search-landscape:ridges')
    haze = p['water'][3]
    sun = (744, 156)
    rim_col, rim_op = ('#ffffff', .6) if not dark else ('#9cc0ff', .26)
    # the bright horizon: a warm glow and a few soft beams fanning up from it
    warm = sc.radial('sun', p['gold_hi'] if not dark else p['gold'], .9 if not dark else .42, .3)
    beam = '#ffffff' if not dark else p['gold_hi']
    for a0, a1, op in ((196, 204, .5), (214, 221, .4), (232, 238, .32), (250, 255, .25)):
        r = 520
        x0, y0 = sun[0] + r * math.cos(math.radians(a0)), sun[1] + r * math.sin(math.radians(a0))
        x1, y1 = sun[0] + r * math.cos(math.radians(a1)), sun[1] + r * math.sin(math.radians(a1))
        sc.under.append(f'<path d="M{sun[0]},{sun[1]} L{fmt(x0)},{fmt(y0)} L{fmt(x1)},{fmt(y1)} Z" fill="{beam}" '
                        f'fill-opacity="{fmt(op * (.55 if not dark else .1), 2)}"/>')
    sc.under.append(f'<ellipse cx="{sun[0]}" cy="{sun[1] + 4}" rx="210" ry="76" fill="{warm}"/>')
    sc.under.append(sc.far_school(560, 104, 8, n=6, seed=2))
    sc.under.append(_manta(470, 70, 46, mix(haze, p['far_dk'], .7)))
    # receding ridges behind the seabed hills, palest first, each with a lit rim; spires and reefs on them
    ridges = ((144, 6, 520, .25), (156, 5, 430, .5), (167, 4.5, 380, .78))
    for i, (base, amp, wl, k) in enumerate(ridges):
        pts, fn = oa._ridge(rnd, W, base, amp, wl)
        col = mix(haze, p['far'] if not dark else p['far_dk'], k)
        dk = mix(haze, p['far_dk'] if not dark else p['mid'], k)
        if i == 0:
            for x, h, w in ((452, 34, 16), (474, 22, 12), (806, 40, 18), (834, 26, 12), (300, 24, 14)):
                sc.under.append(_spire(x, fn(x) + 4, h, w, dk))
        else:
            for x in range(120 + 70 * i, W - 30, 170):
                if abs(x - sun[0]) > 30:
                    sc.under.append(oa.fan_coral(x, fn(x) + 3, 10 + 4 * i, dk, n=6, width=1.3) if i == 1 else
                                    oa.branch_coral(x, fn(x) + 3, .075, dk, width=1.8, flip=x % 2 == 0))
        sc.under.append(f'<path d="{catmull(pts)} L{W + 40},{H + 10} L-40,{H + 10} Z" fill="{col}"/>')
        sc.under.append(_line(catmull([pt for pt in pts if 340 < pt[0] < 900]), rim_col, 1.4, rim_op))
    core = sc.radial('core', '#ffffff', .95, .45)
    sc.under.append(f'<ellipse cx="{sun[0]}" cy="{sun[1]}" rx="30" ry="20" fill="{core}"/>' + _circle(sun[0], sun[1], 4.5, '#ffffff'))
    # the winding path from the foreground to the horizon
    centre = [(606, 248), (556, 230), (584, 214), (640, 201), (680, 189), (712, 176), (736, 164)]
    widths = [62, 48, 34, 22, 13, 7, 2]
    left, right = [], []
    for i, ((x, y), w) in enumerate(zip(centre, widths)):
        x2, y2 = centre[min(i + 1, len(centre) - 1)]
        x1, y1 = centre[max(i - 1, 0)]
        dx, dy = x2 - x1, y2 - y1
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln * w / 2, dx / ln * w / 2 * .45
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    path = catmull(left + right[::-1], closed=True, tension=.45)
    sand = mix(p['near'], '#ffffff', .55) if not dark else mix(p['near'], '#9cc0ff', .38)
    sc.body.append(f'<path d="{path}" fill="{sand}"/>')
    sc.body.append(_line(catmull(centre[1:]), mix(sand, '#ffffff', .5), 1.4, .7).replace('/>', ' stroke-dasharray="2 8"/>'))
    for x, s in ((452, .1), (520, .07), (826, .12)):
        sc.body.append(oa.branch_coral(x, sc.bed.mid(x) + 4, s, p['mid_dk'], width=2.4))
    # the outcrop on the left, a lit top face and a shaded cliff, with the Diver bot on top
    body = mix(p['near'], p['band'], .3) if not dark else mix(p['near'], p['band'], .5)
    top = mix(p['near'], '#ffffff', .3) if not dark else mix(p['near'], '#9cc0ff', .22)
    side = mix(body, p['line'], .25)
    sc.body.append(f'<path d="M-20,{H + 6} L-20,190 C10,180 40,176 80,176 L292,170 C306,170 314,176 320,186 L340,212 '
                   f'C350,226 356,236 362,{H + 6} Z" fill="{body}"/>')
    sc.body.append(f'<path d="M292,170 C306,170 314,176 320,186 L340,212 C350,226 356,236 362,{H + 6} L300,{H + 6} '
                   f'C304,226 300,204 292,190 Z" fill="{side}"/>')
    sc.body.append(f'<path d="M-20,190 C10,180 40,176 80,176 L292,170 C302,170 308,173 312,178 L280,181 L90,185 C50,186 20,190 -20,198 Z" '
                   f'fill="{top}"/>')
    sc.body.append(_line('M120,198 L134,212 L128,226 M220,192 L230,208 M60,204 L70,218', mix(body, p['line'], .35), 1.8, .7))
    sc.body.append(sc.shadow(232, 176, 34))
    sc.body.append(sc.bot('point', 232, 176, height=96))
    sc.body.append(sc.bubbles(282, 120, 40, 3, n=3, seed=3))
    # life in the valley
    sc.body.append(sc.school(404, 92, 14, 'blue', n=4, flip=True, seed=5))
    sc.body.append(sc.fish(842, 64, 20, 'yellow'))
    sc.over.append(sc.seaweed(24, 100, phase=.6) + sc.seaweed(46, 66, p['weed_light'], width=4, phase=2.4))
    sc.over.append(sc.coral(852, .3, flip=True))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 30-topics-ai-features
def scene_ai(dark=False):
    """30-topics-ai-features, "AI and Search": a large glowing jellyfish whose bell is patterned like a network reaches its
    tentacles down to page cards and a book on the seabed, while the Diver bot waves up at it."""
    sc = Scene('30-topics-ai-features', dark, seed=35, avoid=[(430, 700)], rays=6, glow=(560, -30, 360))
    p = sc.p
    vio, vlt = p['violet'], p['violet_lt']
    cx, top, rim = 566, 34, 102
    x0, x1 = cx - 72, cx + 72
    # glow behind the bell
    g = sc.radial('jelly', vlt if not dark else vio, .55 if not dark else .55, .32)
    sc.body.append(f'<ellipse cx="{cx}" cy="80" rx="150" ry="104" fill="{g}"/>')
    # things on the seabed the tentacles reach: three page cards and an open book
    sc.body.append(sc.shadow(574, FLOOR, 120, 6))
    sc.body.append(sc.shadow(316, FLOOR, 38))
    inks = [oa.PALETTE['label_' + k][0] for k in ('slide', 'docs', 'stage')]
    cards = ((488, 202, -8, inks[0]), (532, 206, 5, inks[1]), (578, 200, -3, inks[2]))
    for x, y, r, ink in cards:
        sc.body.append(_paper(p, x, y, r, 34, 40, ink))
    bk = oa.PALETTE['label_slide'][0]
    bx, by = 642, 212
    sc.body.append(f'<path d="M{bx - 34},{by + 6} L{bx - 30},{by - 12} Q{bx - 15},{by - 17} {bx},{by - 10} Q{bx + 15},{by - 17} {bx + 30},{by - 12} '
                   f'L{bx + 34},{by + 6} Q{bx + 17},{by + 1} {bx},{by + 8} Q{bx - 17},{by + 1} {bx - 34},{by + 6} Z" fill="{bk}" {stroke(p)}/>')
    sc.body.append(f'<path d="M{bx - 29},{by + 2} L{bx - 26},{by - 13} Q{bx - 13},{by - 17} {bx},{by - 9} L{bx},{by + 4} '
                   f'Q{bx - 14},{by - 2} {bx - 29},{by + 2} Z M{bx + 29},{by + 2} L{bx + 26},{by - 13} Q{bx + 13},{by - 17} {bx},{by - 9} '
                   f'L{bx},{by + 4} Q{bx + 14},{by - 2} {bx + 29},{by + 2} Z" fill="{p["paper"]}" {stroke(p, .8)}/>')
    sc.body.append(_line(f'M{bx - 22},{by - 7} L{bx - 7},{by - 5} M{bx - 23},{by - 2} L{bx - 7},{by} M{bx + 7},{by - 5} L{bx + 22},{by - 7} '
                         f'M{bx + 7},{by} L{bx + 21},{by - 2}', p['paper_line'], 1.6))
    # tentacles: from the rim down to the cards and the book, each ending in a glowing node
    targets = ((482, 180), (530, 184), (580, 178), (626, 196), (656, 196))
    starts = (cx - 50, cx - 24, cx + 2, cx + 26, cx + 50)
    tcol = vlt if not dark else mix(vlt, '#ffffff', .2)
    node_g = sc.radial('node', vlt if not dark else '#ffffff', .9 if not dark else .7, .35)
    for i, ((tx, ty), sx) in enumerate(zip(targets, starts)):
        pts = _wavy(sx, rim + 4, tx, ty - 4, 5, 1.6, n=8, phase=i * 1.3)
        sc.body.append(_line(catmull(pts), mix(vio, p['line'], .2) if not dark else vio, 3.2, .35))
        sc.body.append(_line(catmull(pts), tcol, 1.8, .95))
        sc.body.append(_circle(tx, ty - 4, 7, node_g) + _circle(tx, ty - 4, 2.8, '#ffffff', stroke(p, .5)))
    # oral arms: short frilly ribbons in the middle
    for i, (dx, ln) in enumerate(((-12, 52), (6, 64), (20, 46))):
        pts = _wavy(cx + dx, rim, cx + dx + 4, rim + ln, 6, 1.3, n=8, phase=1 + i)
        sc.body.append(_line(catmull(pts), mix(vlt, vio, .35), 5, .75))
    # the bell: a dome with a scalloped rim, a soft vertical gradient, a highlight and a network of nodes
    bell = sc.linear('bell', [(0, mix(vlt, '#ffffff', .35)), (.55, vlt), (1, mix(vlt, vio, .55))])
    sc_d = [f'M{x0},{rim} C{x0 - 4},{top + 30} {cx - 40},{top} {cx},{top} C{cx + 40},{top} {x1 + 4},{top + 30} {x1},{rim}']
    n = 7
    for k in range(n):
        xa = x1 - (k + 1) * (x1 - x0) / n
        xm = x1 - (k + .5) * (x1 - x0) / n
        sc_d.append(f'Q{fmt(xm)},{rim + 9} {fmt(xa)},{rim}')
    bell_d = ' '.join(sc_d) + ' Z'
    sc.body.append(f'<path d="{bell_d}" fill="{bell}" fill-opacity=".94"/>')
    sc.body.append(f'<path d="M{x0 + 6},{rim - 2} C{x0 + 20},{rim - 14} {x1 - 20},{rim - 14} {x1 - 6},{rim - 2}" fill="none" '
                   f'stroke="{vio}" stroke-opacity=".35" stroke-width="2.4" stroke-linecap="round"/>')
    nodes = [(cx - 44, 80), (cx - 22, 58), (cx, 72), (cx + 26, 56), (cx + 46, 80), (cx - 20, 90), (cx + 18, 92), (cx + 2, 46)]
    links = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 2), (2, 6), (6, 4), (1, 7), (7, 3), (5, 6)]
    net_col = '#ffffff' if not dark else mix(vlt, '#ffffff', .6)
    d = ' '.join(f'M{nodes[a][0]},{nodes[a][1]} L{nodes[b][0]},{nodes[b][1]}' for a, b in links)
    sc.body.append(_line(d, net_col, 1.4, .8))
    for i, (x, y) in enumerate(nodes):
        sc.body.append(_circle(x, y, 3.4 if i == 2 else 2.4, net_col, f'stroke="{vio}" stroke-width=".9" stroke-opacity=".6"'))
    sc.body.append(f'<path d="M{cx - 54},{rim - 22} C{cx - 56},{top + 30} {cx - 36},{top + 10} {cx - 12},{top + 8}" fill="none" '
                   f'stroke="#ffffff" stroke-opacity=".6" stroke-width="4" stroke-linecap="round"/>')
    sc.body.append(f'<path d="{bell_d}" fill="none" {stroke(p)}/>')
    sc.body.append(sc.bubbles(cx + 74, 52, 34, 3, n=3, seed=2) + sc.bubbles(cx - 84, 70, 30, 2.6, n=3, seed=5))
    sc.body.append(sc.bot('wave', 316, FLOOR))
    # dressing
    sc.body.append(sc.school(160, 80, 16, 'blue', n=4, flip=True, seed=3))
    sc.over.append(sc.seaweed(28, 116, phase=2.1) + sc.seaweed(50, 76, p['weed_light'], width=4, phase=.9))
    sc.over.append(sc.coral(820, .38))
    sc.over.append(sc.anemone(758, 15))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 30-topics-publisher-controls
def scene_controls(dark=False):
    """30-topics-publisher-controls, "Publisher controls": a metal control panel on the seabed with a big lever, three
    sliders and two switches; two outlet pipes release one full stream of bubbles and one throttled stream."""
    sc = Scene('30-topics-publisher-controls', dark, seed=36, avoid=[(380, 760)], rays=6, glow=(560, -30, 360))
    p = sc.p
    st = stroke(p)
    blue = oa.PALETTE['label_slide'][0]
    sc.under.append(sc.far_school(200, 66, 14, n=4, flip=True, seed=1))
    sc.body.append(sc.shadow(520, FLOOR, 110, 6))
    sc.body.append(sc.shadow(328, FLOOR, 40))
    # outlet pipes (behind the panel), each with a gold joint, a hand wheel and an upturned nozzle
    pipe = mix(p['metal'], p['metal_dk'], .3)
    for y, x_end, top in ((116, 672, 86), (176, 732, 146)):
        d = f'M600,{y} L{x_end - 14},{y} Q{x_end},{y} {x_end},{y - 14} L{x_end},{top}'
        sc.body.append(_line(d, p['line'], 13) + _line(d, pipe, 10) + _line(f'M600,{y - 2.5} L{x_end - 16},{y - 2.5}', p['metal_hi'], 2))
        sc.body.append(_rect(x_end - 9, top - 6, 18, 10, 3, p['gold'], st))
        sc.body.append(_rect(612, y - 8, 8, 16, 2, p['gold'], st))
    for wx, wy, rot in ((640, 116, 0), (686, 176, 30)):
        hy = wy - 12
        spokes = ' '.join(f'M{wx},{hy} L{fmt(wx + 9 * math.cos(math.radians(rot + a)))},{fmt(hy + 9 * math.sin(math.radians(rot + a)))}'
                          for a in (0, 90, 180, 270))
        sc.body.append(_line(f'M{wx},{wy} L{wx},{hy}', p['line'], 3)
                       + _circle(wx, hy, 10, 'none', f'stroke="{p["line"]}" stroke-width="5.2"')
                       + _circle(wx, hy, 10, 'none', f'stroke="{p["coral"]}" stroke-width="3"')
                       + _line(spokes, p['coral'], 1.8) + _circle(wx, hy, 2.6, p['gold'], stroke(p, .6)))
    # the two streams: one full, one throttled
    sc.body.append(sc.bubbles(670, 74, 52, 6.6, n=6, seed=4) + sc.bubbles(678, 70, 40, 4.4, n=4, seed=9))
    sc.body.append(sc.bubbles(664, 30, 8, 3.2, n=2, seed=7))
    # throttled: a few small bubbles, spaced out, so it still reads as a stream at README width
    sc.body.append(sc.bubble(732, 134, 3.6) + sc.bubble(736, 112, 3) + sc.bubble(730, 92, 2.4) + sc.bubble(734, 74, 1.9))
    # the panel
    x0, y0, x1 = 432, 76, 602
    for lx in (444, 576):
        sc.body.append(_rect(lx, 210, 14, FLOOR - 210, 3, p['metal_dk'], st))
    sc.body.append(_rect(x0, y0, x1 - x0, 136, 9, p['metal_hi'], st))
    sc.body.append(_rect(x1 - 18, y0 + 4, 14, 128, 5, p['metal'], 'fill-opacity=".6"'))
    sc.body.append(_rect(x0, y0, x1 - x0, 16, 8, blue, st))
    sc.body.append(_rect(x0 + 1, y0 + 9, x1 - x0 - 2, 7, 0, blue))
    for i, c in enumerate((p['fish_green'], p['gold'], p['coral'])):
        sc.body.append(_circle(x0 + 16 + i * 12, y0 + 8, 3, c))
    for k in range(4):
        sc.body.append(_circle(x0 + 8 + (k % 2) * (x1 - x0 - 16), y0 + 26 + (k // 2) * 100, 2, p['metal_dk']))
    # three sliders
    for i, ky in enumerate((114, 140, 104)):
        sx = 458 + i * 28
        sc.body.append(_rect(sx - 3.5, 104, 7, 58, 3.5, p['line']))
        sc.body.append(_line(' '.join(f'M{sx + 8},{104 + t * 14.5} l5,0' for t in range(5)), p['metal_dk'], 1.4))
        sc.body.append(_rect(sx - 9, ky - 5, 18, 12, 4, p['pearl'], st))
        sc.body.append(_line(f'M{sx - 4},{ky + 1} L{sx + 4},{ky + 1}', blue, 2))
    # two switches with lights (on: teal, off: dim coral)
    for i, (on, light) in enumerate(((True, p['fish_green']), (False, p['coral']))):
        tx = 554 + i * 0
        ty = 108 + i * 42
        sc.body.append(_rect(tx - 14, ty - 2, 28, 34, 6, p['metal'], st))
        sc.body.append(_line(f'M{tx},{ty + 15} L{tx},{ty + (3 if on else 27)}', p['line'], 4.4))
        sc.body.append(_ball(p, tx, ty + (3 if on else 27), 4.6, p['pearl']))
        sc.body.append(_circle(tx + 24, ty + 6, 3.6, light if on else mix(light, p['metal_hi'], .55), stroke(p, .6)))
        if on:
            sc.body.append(_circle(tx + 24, ty + 6, 7, light, 'fill-opacity=".22"'))
    sc.body.append(_line(' '.join(f'M{x0 + 22},{186 + k * 6} L{x0 + 92},{186 + k * 6}' for k in range(4)), p['metal'], 2))
    # the lever: a quadrant on the panel's side, the handle pulled back to the bot's glove
    px, py = 432, 196
    sc.body.append(f'<path d="M{px},{py - 30} A30,30 0 0 0 {px},{py + 26} Z" fill="{p["metal"]}" {st}/>')
    sc.body.append(_line(' '.join(f'M{fmt(px - 24 * math.sin(math.radians(a)))},{fmt(py - 24 * math.cos(math.radians(a)))} '
                                  f'l{fmt(-5 * math.sin(math.radians(a)))},{fmt(-5 * math.cos(math.radians(a)))}' for a in (20, 50, 80, 110)),
                         p['line'], 1.6))
    gx, gy = 348, 182
    sc.body.append(_line(f'M{px},{py} L{gx + 4},{gy}', p['line'], 7.4) + _line(f'M{px},{py} L{gx + 4},{gy}', p['metal_dk'], 4.4))
    sc.body.append(_circle(px, py, 6, p['gold'], st))
    sc.body.append(sc.bot('point', 327, FLOOR))
    sc.body.append(_ball(p, gx - 2, gy - 6, 6.5, p['coral']))
    # dressing
    sc.body.append(sc.fish(150, 100, 24, 'yellow', flip=True))
    sc.over.append(sc.seaweed(30, 112, phase=1.6) + sc.seaweed(52, 78, p['weed_light'], width=4, phase=.3))
    sc.over.append(sc.anemone(792, 15))
    sc.over.append(sc.coral(846, .34, flip=True))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 30-topics-community
def _turtle(p, x, base, s=1.0):
    """A sitting sea turtle facing left: a domed shell with a hexagon plate pattern, a head, front and back flippers."""
    st = stroke(p)
    skin = mix(p['fish_green'], '#ffffff', .35)
    shell, plate = p['weed'], mix(p['weed'], '#ffffff', .38)
    w, h = 76 * s, 42 * s
    rim = base - 6 * s
    top = rim - h
    o = [f'<path d="M{fmt(x + w * .3)},{fmt(rim)} Q{fmt(x + w * .55)},{fmt(base - 2 * s)} {fmt(x + w * .62)},{fmt(base)} '
         f'L{fmt(x + w * .28)},{fmt(base)} Z" fill="{skin}" {st}/>',
         # head and neck reaching out towards the fire
         f'<path d="M{fmt(x - w * .4)},{fmt(rim - h * .1)} C{fmt(x - w * .55)},{fmt(rim - h * .2)} {fmt(x - w * .6)},{fmt(rim - h * .55)} '
         f'{fmt(x - w * .72)},{fmt(rim - h * .62)} C{fmt(x - w * .9)},{fmt(rim - h * .7)} {fmt(x - w * .92)},{fmt(rim - h * .3)} '
         f'{fmt(x - w * .76)},{fmt(rim - h * .22)} C{fmt(x - w * .64)},{fmt(rim - h * .16)} {fmt(x - w * .56)},{fmt(rim + 2 * s)} '
         f'{fmt(x - w * .36)},{fmt(rim + 2 * s)} Z" fill="{skin}" {st}/>',
         _circle(x - w * .76, rim - h * .47, 2.8 * s, p['eye']),
         _circle(x - w * .77, rim - h * .5, 1 * s, '#ffffff'),
         _line(f'M{fmt(x - w * .87)},{fmt(rim - h * .34)} q{fmt(4 * s)},{fmt(2.4 * s)} {fmt(8 * s)},{fmt(.4 * s)}', p['line'], 1.2),
         f'<path d="M{fmt(x - w / 2)},{fmt(rim)} C{fmt(x - w * .48)},{fmt(top + 2 * s)} {fmt(x - w * .2)},{fmt(top)} {fmt(x)},{fmt(top)} '
         f'C{fmt(x + w * .2)},{fmt(top)} {fmt(x + w * .48)},{fmt(top + 2 * s)} {fmt(x + w / 2)},{fmt(rim)} Z" fill="{shell}" {st}/>']
    cy, rx, ry = rim - h * .5, w * .16, h * .26
    hexa = [(x - rx, cy), (x - rx * .5, cy - ry), (x + rx * .5, cy - ry), (x + rx, cy), (x + rx * .5, cy + ry), (x - rx * .5, cy + ry)]
    ends = [(x - w * .47, rim - 2 * s), (x - w * .3, top + 5 * s), (x + w * .3, top + 5 * s), (x + w * .47, rim - 2 * s),
            (x + w * .16, rim), (x - w * .16, rim)]
    d = 'M' + ' L'.join(f'{fmt(a)},{fmt(b)}' for a, b in hexa) + ' Z ' + ' '.join(
        f'M{fmt(a)},{fmt(b)} L{fmt(c)},{fmt(e)}' for (a, b), (c, e) in zip(hexa, ends))
    o.append(_line(d, plate, 2.2))
    o.append(f'<path d="M{fmt(x - w * .36)},{fmt(rim - h * .55)} C{fmt(x - w * .3)},{fmt(top + 8 * s)} {fmt(x - w * .16)},{fmt(top + 4 * s)} '
             f'{fmt(x - w * .04)},{fmt(top + 3.5 * s)}" fill="none" stroke="#ffffff" stroke-opacity=".45" stroke-width="2.6" stroke-linecap="round"/>')
    o.append(_rect(x - w / 2 - 3 * s, rim - 3 * s, w + 6 * s, 7 * s, 3.5 * s, mix(shell, p['line'], .2), st))
    o.append(f'<path d="M{fmt(x - w * .34)},{fmt(base - 4 * s)} Q{fmt(x - w * .6)},{fmt(base - 3 * s)} {fmt(x - w * .66)},{fmt(base)} '
             f'L{fmt(x - w * .22)},{fmt(base)} Z" fill="{skin}" {st}/>')
    return ''.join(o)


def _crab(p, x, base, s=1.0):
    """A small crab facing us, claws up."""
    st = stroke(p)
    c, cd = p['coral'], mix(p['coral'], p['line'], .25)
    o = []
    legs = ' '.join(f'M{fmt(x + side * 10 * s)},{fmt(base - 7 * s - k * 3 * s)} q{fmt(side * 8 * s)},{fmt(-2 * s)} {fmt(side * 11 * s)},{fmt(7 * s + k * 2 * s)}'
                    for side in (-1, 1) for k in range(3))
    o.append(_line(legs, cd, 2.4))
    for side in (-1, 1):
        ax, ay = x + side * 15 * s, base - 22 * s
        o.append(_line(f'M{fmt(x + side * 9 * s)},{fmt(base - 12 * s)} Q{fmt(x + side * 16 * s)},{fmt(base - 14 * s)} {fmt(ax)},{fmt(ay)}', cd, 3))
        o.append(f'<path d="M{fmt(ax)},{fmt(ay + 3 * s)} C{fmt(ax - 7 * s)},{fmt(ay)} {fmt(ax - 6 * s)},{fmt(ay - 10 * s)} {fmt(ax)},{fmt(ay - 11 * s)} '
                 f'L{fmt(ax + side * 1 * s)},{fmt(ay - 5 * s)} L{fmt(ax + side * 5 * s)},{fmt(ay - 10 * s)} C{fmt(ax + 8 * s)},{fmt(ay - 6 * s)} '
                 f'{fmt(ax + 6 * s)},{fmt(ay + 2 * s)} {fmt(ax)},{fmt(ay + 3 * s)} Z" fill="{c}" {st}/>')
    o.append(f'<ellipse cx="{fmt(x)}" cy="{fmt(base - 9 * s)}" rx="{fmt(14 * s)}" ry="{fmt(9 * s)}" fill="{c}" {st}/>')
    o.append(f'<path d="M{fmt(x - 9 * s)},{fmt(base - 6 * s)} Q{fmt(x)},{fmt(base - 1 * s)} {fmt(x + 9 * s)},{fmt(base - 6 * s)}" fill="none" '
             f'stroke="{cd}" stroke-width="1.6" stroke-linecap="round"/>')
    for side in (-1, 1):
        ex = x + side * 5 * s
        o.append(_line(f'M{fmt(ex)},{fmt(base - 16 * s)} L{fmt(ex)},{fmt(base - 22 * s)}', cd, 2))
        o.append(_circle(ex, base - 24 * s, 3 * s, '#ffffff', stroke(p, .6)) + _circle(ex - side * .6, base - 23.6 * s, 1.4 * s, p['eye']))
    return ''.join(o)


def _octopus(p, x, base, s=1.0):
    """A friendly octopus sitting with its arms curled on the ground."""
    st = stroke(p)
    body, shade = p['violet_lt'], mix(p['violet_lt'], p['violet'], .45)
    o = []
    for k, (dx, cx2, cy2) in enumerate(((-30, -40, -10), (-18, -26, 2), (18, 26, 2), (30, 40, -10))):
        ex, ey = x + dx * s, base - 2 * s
        d = (f'M{fmt(x + dx * .25 * s)},{fmt(base - 26 * s)} Q{fmt(x + cx2 * s)},{fmt(base - 12 * s + cy2 * s * .2)} {fmt(ex)},{fmt(ey)} '
             f'q{fmt(math.copysign(7, dx) * s)},{fmt(-2 * s)} {fmt(math.copysign(5, dx) * s)},{fmt(-9 * s)}')
        o.append(_line(d, p['line'], 8.6 * s) + _line(d, shade if k in (0, 3) else body, 6 * s))
    o.append(f'<path d="M{fmt(x - 20 * s)},{fmt(base - 18 * s)} C{fmt(x - 26 * s)},{fmt(base - 64 * s)} {fmt(x + 26 * s)},{fmt(base - 64 * s)} '
             f'{fmt(x + 20 * s)},{fmt(base - 18 * s)} C{fmt(x + 12 * s)},{fmt(base - 8 * s)} {fmt(x - 12 * s)},{fmt(base - 8 * s)} '
             f'{fmt(x - 20 * s)},{fmt(base - 18 * s)} Z" fill="{body}" {st}/>')
    o.append(f'<path d="M{fmt(x + 12 * s)},{fmt(base - 50 * s)} C{fmt(x + 20 * s)},{fmt(base - 42 * s)} {fmt(x + 20 * s)},{fmt(base - 26 * s)} '
             f'{fmt(x + 14 * s)},{fmt(base - 16 * s)}" fill="none" stroke="{shade}" stroke-width="{fmt(4 * s)}" stroke-linecap="round"/>')
    o.append(_circle(x - 9 * s, base - 50 * s, 3 * s, '#ffffff', 'fill-opacity=".7"'))
    for side in (-1, 1):
        o.append(_circle(x + side * 7 * s, base - 33 * s, 3.4 * s, '#ffffff') + _circle(x + side * 7 * s - 1, base - 33 * s, 1.9 * s, p['eye']))
    o.append(_line(f'M{fmt(x - 4 * s)},{fmt(base - 24 * s)} q{fmt(4 * s)},{fmt(3 * s)} {fmt(8 * s)},0', p['line'], 1.4))
    return ''.join(o)


def scene_community(dark=False):
    """30-topics-community, "Working with Google": the Diver bot, a crab, an octopus, a turtle and two fish gathered round a
    campfire of glowing gold bubbles rising from a stone-ringed vent; a shared scroll lies open in front of them."""
    sc = Scene('30-topics-community', dark, seed=37, avoid=[(360, 740)], rays=5, glow=(540, -30, 340))
    p = sc.p
    fx = 532
    warm = sc.radial('fire', p['gold'], .7 if not dark else .62, .3)
    sc.body.append(f'<ellipse cx="{fx}" cy="170" rx="160" ry="98" fill="{warm}"/>')
    sc.body.append(sc.shadow(fx + 40, FLOOR, 190, 7))
    # the octopus sits behind the fire, to the right
    sc.body.append(_octopus(p, fx + 56, FLOOR - 20, .92))
    # back stones of the ring, the vent, the rising gold bubbles, front stones
    stone, stone_dk = p['metal'], p['metal_dk']
    sc.body.append(f'<ellipse cx="{fx}" cy="{FLOOR - 7}" rx="36" ry="9" fill="{mix(p["line"], p["near"], .3)}"/>')
    for dx, dy, rx in ((-28, -12, 9), (-8, -15, 9), (12, -15, 9), (31, -12, 8)):
        sc.body.append(f'<ellipse cx="{fx + dx}" cy="{FLOOR + dy}" rx="{rx}" ry="6" fill="{stone_dk}" {stroke(p)}/>')
    core = sc.radial('core', p['gold_hi'], .95, .5)
    sc.body.append(f'<ellipse cx="{fx}" cy="{FLOOR - 18}" rx="30" ry="20" fill="{core}"/>')
    rnd = oa._rng('community:fire')
    for i in range(14):
        t = i / 13
        y = FLOOR - 14 - t * 96
        x = fx + math.sin(t * 7 + 1) * (3 + 7 * t) + rnd.uniform(-4, 4)
        r = 10.5 * (1 - .74 * t) * rnd.uniform(.82, 1.1)
        col = mix(p['gold'], p['gold_hi'], t)
        if i % 3 == 0:
            col = mix(p['coral'], p['gold'], .25 + .5 * t)
        sc.body.append(_circle(x, y, r, col, f'fill-opacity="{fmt(.95 - .45 * t, 2)}"')
                       + _circle(x - r * .35, y - r * .35, r * .3, '#ffffff', f'fill-opacity="{fmt(.8 - .3 * t, 2)}"'))
    for dx, dy, rx in ((-40, -4, 10), (-14, -1, 11), (12, -1, 11), (38, -4, 10)):
        sc.body.append(f'<ellipse cx="{fx + dx}" cy="{FLOOR + dy}" rx="{rx}" ry="7" fill="{stone}" {stroke(p)}/>'
                       f'<ellipse cx="{fx + dx - 2}" cy="{FLOOR + dy - 3}" rx="{rx * .5}" ry="2" fill="{p["metal_hi"]}"/>')
    # the circle: the bot reading on the left, the crab beside it, the turtle on the right, two fish above
    sc.body.append(sc.shadow(392, FLOOR, 40))
    sc.body.append(sc.bot('read', 392, FLOOR, height=100))
    sc.body.append(sc.shadow(466, FLOOR, 20))
    sc.body.append(_crab(p, 466, FLOOR + 1, .92))
    sc.body.append(sc.shadow(706, FLOOR, 46))
    sc.body.append(_turtle(p, 708, FLOOR, 1.0))
    sc.body.append(sc.fish(458, 108, 26, 'blue', flip=True))
    sc.body.append(sc.fish(640, 92, 24, 'red'))
    # the shared scroll, unrolled on the sand between the octopus and the turtle
    sx0, sx1, sy = 604, 664, FLOOR - 1
    sc.body.append(f'<path d="M{sx0},{sy - 10} L{sx1},{sy - 10} L{sx1 + 2},{sy + 2} L{sx0 - 2},{sy + 2} Z" fill="{p["paper"]}" {stroke(p)}/>')
    sc.body.append(_line(f'M{sx0 + 7},{sy - 6} L{sx1 - 8},{sy - 6} M{sx0 + 7},{sy - 2} L{sx1 - 16},{sy - 2}', p['paper_line'], 1.5))
    for x in (sx0, sx1):
        sc.body.append(_rect(x - 4.5, sy - 14, 9, 19, 4.5, p['wood_hi'], stroke(p)) + _line(f'M{x},{sy - 11} L{x},{sy + 2}', p['wood_dk'], 1.4))
    sc.body.append(sc.bubbles(fx + 2, 52, 22, 2.4, n=3, seed=6))
    # dressing
    sc.body.append(sc.school(170, 74, 15, 'yellow', n=3, flip=True, seed=2))
    sc.over.append(sc.seaweed(30, 114, phase=.5) + sc.seaweed(52, 80, p['weed_light'], width=4, phase=2.7))
    sc.over.append(sc.anemone(790, 13))
    sc.over.append(sc.coral(840, .36, flip=True))
    return sc.render()


SCENES = {
    '30-topics-serving-ranking': scene_serving,
    '30-topics-search-trends': scene_trends,
    '30-topics-search-console': scene_console,
    '30-topics-search-landscape': scene_landscape,
    '30-topics-ai-features': scene_ai,
    '30-topics-publisher-controls': scene_controls,
    '30-topics-community': scene_community,
}
