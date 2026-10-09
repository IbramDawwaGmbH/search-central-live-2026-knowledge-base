"""Deep Dive artwork as code: original underwater vector art for the Deep Dive edition (PDF, web edition, mindmap, brand).

Every shape is drawn here from numbers: water surface, light rays, sunlight blobs, layered seabed, coral, seaweed, fish,
starfish, bubbles, the small icons and our own mascot, the diver bot. Nothing is traced or copied from the event's material;
no photos, no logos, no copied mascots, and the reef colours are deliberately not any search-engine brand colours.
The diver bot (diver_bot, diver_bot_svg) is an original character; its docstring lists the guardrails that keep it so.

Units
    Primitives (fish, bubble, coral, ...) draw in the caller's user units: pass the position and size in whatever units the
    surrounding <svg> viewBox uses. The PDF underlay uses 0.1 mm (an A4 page is 2100 x 2970); the site and brand images use
    CSS px. Primitives return SVG *fragments* (no <svg> wrapper) so several can share one canvas.
    Whole pictures (top_wave, seabed, light_blobs, light_rays, wavy_rule, underwater_scene) and icons (icon_*, section_bubble,
    page_bubble) return a complete <svg> element with a viewBox; the icons are sized with a CSS length (number = mm).

Determinism
    No clock, no global randomness, no external references (no fonts, images or URLs are loaded; text in the bubbles names
    the bundled 'Figtree' family). Random placement uses random.Random(seed) only, and numbers are written with at most one
    decimal place (two inside the 100-unit icons), so the same arguments always give byte-identical SVG.

Gradient ids
    Functions that need <defs> (section_bubble, page_bubble, light_rays, underwater_scene) take a `uid` that prefixes every
    id, so several of them can live in one HTML document without clashing. Use a different uid for each copy on a page.

Palettes
    PALETTE is the light look (print and day-time screens); DARK is "night water" for screens. Both share key names where a
    role is the same, so `pal = DARK if dark else PALETTE` works for most pictures.

    from ocean_art import PALETTE, seabed, top_wave, underwater_scene
    svg = underwater_scene(794, 1123, seed=1, mood='light')    # A4 portrait cover at 96 dpi
"""
import math
import random
import re

__all__ = [
    'PALETTE', 'DARK', 'REEF', 'fmt', 'mix', 'catmull', 'sine_pts',
    'fish', 'mono_fish', 'fish_school', 'bubble', 'bubble_trail', 'seaweed', 'branch_coral', 'fan_coral', 'fern',
    'anemone', 'starfish', 'dots',
    'icon_question', 'icon_check', 'icon_boat', 'icon_bubble', 'section_bubble', 'page_bubble', 'wavy_rule',
    'top_wave', 'seabed', 'light_blobs', 'light_rays', 'underwater_scene', 'scene_safe_area',
    'BOT_POSES', 'BOT_FORBIDDEN_HEX', 'diver_bot', 'diver_bot_svg', 'diver_bot_box',
]

# ------------------------------------------------------------------------------------------------------------ palettes
PALETTE = {
    # text
    'ink': '#262d3b', 'body': '#3b4354', 'muted': '#687185', 'faint': '#98a1b3', 'nid': '#5d6679',
    # blues
    'blue': '#2f6fe0', 'blue_deep': '#2152c4', 'blue_wash': '#eef4fe', 'rule': '#e2e9f5', 'frame': '#d4e1f6',
    'wave_front': '#2f6fe0', 'wave_back': '#a9cbf6',
    # sky / water gradient, surface to depth
    'sky': ('#ffffff', '#f2f7fe', '#e2edfb', '#d2e2f8', '#c7d9f5'),
    'card': '#ffffff', 'page': '#ffffff',
    # seabed (monochrome print layer)
    'far': '#d3daf5', 'far_dk': '#bcc6ef', 'mid': '#a2aee6', 'mid_dk': '#8695da', 'near': '#7381cf',
    'band': '#4b56ad', 'dot_mid': '#c3cbf1', 'dot_near': '#97a3e0', 'star': '#e6eafb',
    # reef (screen layer)
    'fish_red': '#f26b4f', 'fish_yellow': '#f7c443', 'fish_green': '#1fa38a', 'fish_blue': '#3a8ee6',
    'weed': '#25a07e', 'weed_light': '#82cfb4', 'coral': '#ee6a3c', 'anemone': '#f7c443', 'anemone_dot': '#e08f12',
    'bubble_stroke': '#9fbbec', 'bubble_fill': '#ffffff', 'eye': '#253048',
    # quiz chips and labels
    'quiz_amber': '#f0a020', 'quiz_amber_text': '#9a6200', 'quiz_green': '#1f9a74', 'quiz_green_text': '#17805d',
    'label_slide': ('#2152c4', '#e4edfd'), 'label_stage': ('#6a45cf', '#eee8fc'), 'label_docs': ('#15784b', '#e0f3e8'),
    'label_analysis': ('#8f5200', '#fdefd6'), 'label_press': ('#b23a2e', '#fde6e1'),
    'verdict_ok': '#15784b', 'verdict_no': '#c2412f',
    # section bubble gradient (light centre, deep rim)
    'bubble_hi': '#5b92f0', 'bubble_lo': '#2556c9',
}

DARK = {
    'ink': '#eef3ff', 'body': '#c9d5ee', 'muted': '#93a3c4', 'faint': '#7d8db0', 'nid': '#a9b6d2',
    'blue': '#6fa3ff', 'blue_deep': '#8fb8ff', 'blue_wash': '#13295a', 'rule': '#1d3a72', 'frame': '#1d3a72',
    'wave_front': '#2f6fe0', 'wave_back': '#1b3f8f',
    'sky': ('#0b1b3d', '#0a1938', '#091733', '#08152f', '#08142e'),
    'card': '#0f2148', 'page': '#08142e',
    'far': '#16295a', 'far_dk': '#1d3468', 'mid': '#1b3270', 'mid_dk': '#243e80', 'near': '#223c85',
    'band': '#0a1430', 'dot_mid': '#22397a', 'dot_near': '#2c4895', 'star': '#2a4387',
    'fish_red': '#ff7a5e', 'fish_yellow': '#ffd055', 'fish_green': '#2fbf9f', 'fish_blue': '#4f9df2',
    'weed': '#2fb78f', 'weed_light': '#7fd6b9', 'coral': '#ff7a4a', 'anemone': '#ffd055', 'anemone_dot': '#e89a1c',
    'bubble_stroke': '#6f93d8', 'bubble_fill': '#9cc0ff', 'eye': '#0b1530',
    'quiz_amber': '#f0a020', 'quiz_amber_text': '#ffc766', 'quiz_green': '#1f9a74', 'quiz_green_text': '#5fd6ac',
    'label_slide': ('#a9c6ff', '#1a3266'), 'label_stage': ('#cbb8ff', '#2a2160'), 'label_docs': ('#8fe0b4', '#123a2c'),
    'label_analysis': ('#ffcf86', '#3d2a0c'), 'label_press': ('#ffb0a3', '#43201b'),
    'verdict_ok': '#8fe0b4', 'verdict_no': '#ff9a8a',
    'bubble_hi': '#6fa3ff', 'bubble_lo': '#2556c9',
}

REEF = ('red', 'yellow', 'green', 'blue')   # fish(color=...) accepts these names
_FINS = {'#f26b4f': '#dc5038', '#f7c443': '#eaa62a', '#1fa38a': '#158572', '#3a8ee6': '#2b73cc',
         '#ff7a5e': '#e85f45', '#ffd055': '#f0b033', '#2fbf9f': '#21a083', '#4f9df2': '#3b84dc'}


# ------------------------------------------------------------------------------------------------------------ helpers
def fmt(v, nd=1):
    """Compact number: at most nd decimals, no trailing zeros, never '-0'."""
    s = f'{v:.{nd}f}'.rstrip('0').rstrip('.') if nd else f'{v:.0f}'
    return '0' if s in ('-0', '') else s


def _hex(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """Blend two #rrggbb colours: t=0 gives a, t=1 gives b."""
    pa, pb = _hex(a), _hex(b)
    return '#' + ''.join(f'{round(x + (y - x) * t):02x}' for x, y in zip(pa, pb))


def catmull(pts, closed=False, tension=0.5, nd=1):
    """Smooth SVG path data through the points (Catmull-Rom spline written as cubic Beziers)."""
    n = len(pts)
    ext = ([pts[-1]] + list(pts) + [pts[0], pts[1]]) if closed else ([pts[0]] + list(pts) + [pts[-1]])
    d = [f'M{fmt(pts[0][0], nd)},{fmt(pts[0][1], nd)}']
    for i in (range(1, n + 1) if closed else range(1, n)):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        d.append(f'C{fmt(c1[0], nd)},{fmt(c1[1], nd)} {fmt(c2[0], nd)},{fmt(c2[1], nd)} {fmt(p2[0], nd)},{fmt(p2[1], nd)}')
    if closed:
        d.append('Z')
    return ' '.join(d)


def sine_pts(x0, x1, y0, amp, wl, phase=0.0, step=10):
    """Points of a sine wave from x0 to x1 around baseline y0 (amplitude amp, wavelength wl)."""
    n = max(2, int(round((x1 - x0) / step)))
    return [(x0 + (x1 - x0) * i / n, y0 + amp * math.sin(2 * math.pi * (x0 + (x1 - x0) * i / n) / wl + phase))
            for i in range(n + 1)]


def _rng(seed):
    return random.Random(f'ocean-art:{seed}')


def _svg(w, h, body, cls='', extra='', defs=''):
    c = f' class="{cls}"' if cls else ''
    d = f'<defs>{defs}</defs>' if defs else ''
    return (f'<svg viewBox="0 0 {fmt(w)} {fmt(h)}" xmlns="http://www.w3.org/2000/svg"{c} aria-hidden="true" focusable="false"{extra}>'
            f'{d}{body}</svg>')


def _size(size):
    return f'{fmt(size, 2)}mm' if isinstance(size, (int, float)) else str(size)


def _reef(color, pal=PALETTE):
    return pal['fish_' + color] if color in REEF else color


# ------------------------------------------------------------------------------------------------------------ sea life
TAIL_CSS = ('<style>.tail{transform-box:fill-box;transform-origin:0 50%;animation:tail 2.2s ease-in-out infinite}'
            '.tail.t1{animation-duration:1.9s;animation-delay:-.7s}'
            '@keyframes tail{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(6deg)}}'
            '@media (prefers-reduced-motion:reduce){.tail{animation:none}}</style>')


def fish(x, y, length, color='red', flip=False, fin=None, eye_ring='#ffffff', pal=PALETTE, tail=None):
    """Flat friendly fish centred at (x, y), nose to the left (flip=True swims right). `color` is a REEF name or a hex.
    Two-tone body (lighter belly), darker fins, gill line and a bright eye. Drawn at base length 100, scaled to `length`.
    tail (screens only, default None): a class for a <g> around the tail fin, so CSS can wag it about its joint;
    TAIL_CSS is a ready <style> for class 'tail' (add 't1' for a second timing). None draws exactly the still fish."""
    c = _reef(color, pal)
    fin = fin or _FINS.get(c.lower(), mix(c, '#1b2340', 0.16))
    belly = mix(c, '#ffffff', 0.28)
    s = length / 100.0
    tr = f'translate({fmt(x)},{fmt(y)}) scale({"-" if flip else ""}{fmt(s, 3)},{fmt(s, 3)})'
    tail_path = f'<path d="M33,0 C43,-7 52,-15 62,-21 C57.5,-7 57.5,7 62,21 C52,15 43,7 33,0 Z" fill="{fin}"/>'
    return (f'<g transform="{tr}">'
            + (f'<g class="{tail}">{tail_path}</g>' if tail else tail_path) +
            f'<path d="M-13,-20 C-4,-36 15,-35 23,-15 Z" fill="{fin}"/>'
            f'<path d="M-50,0 C-37,-29 19,-29 40,0 C19,29 -37,29 -50,0 Z" fill="{c}"/>'
            f'<path d="M-47.5,4.5 C-33,24 16,25 37.5,4 C15,14.5 -30,15 -47.5,4.5 Z" fill="{belly}"/>'
            f'<path d="M-9,4 C-1,-1 11,2 16,11 C7,14 -3,12 -9,4 Z" fill="{fin}"/>'
            f'<path d="M-18,-14 Q-11,0 -18,14" fill="none" stroke="#ffffff" stroke-opacity=".6" stroke-width="3.2" stroke-linecap="round"/>'
            f'<circle cx="-31" cy="-5" r="6.6" fill="{eye_ring}"/>'
            f'<circle cx="-32.6" cy="-5" r="3.3" fill="{pal["eye"]}"/>'
            f'<circle cx="-33.6" cy="-6.3" r="1.1" fill="#ffffff"/>'
            f'</g>')


def mono_fish(x, y, length, color, flip=False, opacity=None):
    """One-colour fish silhouette for the print layer (same outline as fish, no details)."""
    s = length / 100.0
    tr = f'translate({fmt(x)},{fmt(y)}) scale({"-" if flip else ""}{fmt(s, 3)},{fmt(s, 3)})'
    op = f' fill-opacity="{fmt(opacity, 2)}"' if opacity is not None else ''
    return (f'<g transform="{tr}" fill="{color}"{op}>'
            f'<path d="M33,0 C43,-7 52,-15 62,-21 C57.5,-7 57.5,7 62,21 C52,15 43,7 33,0 Z"/>'
            f'<path d="M-13,-20 C-4,-36 15,-35 23,-15 Z"/>'
            f'<path d="M-50,0 C-37,-29 19,-29 40,0 C19,29 -37,29 -50,0 Z"/>'
            f'</g>')


def fish_school(x, y, length, color='blue', n=6, flip=False, seed=0, spread=1.0, mono=False, pal=PALETTE):
    """A loose school of n fish of one colour heading the same way, led by the fish at (x, y). Deterministic per seed."""
    rnd = _rng(f'school:{seed}')
    d = 1 if flip else -1                    # swimming direction in x
    out, slots = [], [(0, 0)]
    rows = [(1, -1), (1, 1), (2, -2), (2, 0), (2, 2), (3, -1), (3, 1), (4, -2), (4, 0), (4, 2), (5, -1), (5, 1)]
    slots += rows[:n - 1]
    placed = []
    for col, row in slots:
        sx = x - d * col * length * 1.15 * spread + rnd.uniform(-0.12, 0.12) * length
        sy = y + row * length * 0.42 * spread + rnd.uniform(-0.1, 0.1) * length
        ln = length * (1 - 0.06 * col) * rnd.uniform(0.92, 1.04)
        placed.append((sx, sy, ln))
    for sx, sy, ln in sorted(placed, key=lambda p: p[1]):
        out.append(mono_fish(sx, sy, ln, color, flip=flip) if mono else fish(sx, sy, ln, color, flip=flip, pal=pal))
    return ''.join(out)


def bubble(x, y, r, stroke=None, fill=None, fill_op=0.55, highlight=True, pal=PALETTE):
    """Bubble: soft filled circle with a thin rim and a bright highlight arc on the upper right."""
    stroke = stroke or pal['bubble_stroke']
    fill = fill or pal['bubble_fill']
    out = (f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{fill}" fill-opacity="{fmt(fill_op, 2)}" '
           f'stroke="{stroke}" stroke-width="{fmt(max(0.6, min(r * 0.12, 1.2 + r * 0.05)), 2)}"/>')
    if highlight and r >= 2.5:
        a0, a1, rr = math.radians(20), math.radians(72), r * 0.64
        p0 = (x + rr * math.cos(a1), y - rr * math.sin(a1))
        p1 = (x + rr * math.cos(a0), y - rr * math.sin(a0))
        out += (f'<path d="M{fmt(p0[0])},{fmt(p0[1])} A{fmt(rr)},{fmt(rr)} 0 0 1 {fmt(p1[0])},{fmt(p1[1])}" fill="none" '
                f'stroke="#ffffff" stroke-width="{fmt(max(r * 0.2, 0.6), 2)}" stroke-linecap="round"/>')
    return out


def bubble_trail(x, y, height, r, n=5, seed=0, drift=None, pal=PALETTE, **kw):
    """A column of n bubbles rising from (x, y), getting smaller towards the top, with a slight sideways wobble."""
    rnd = _rng(f'trail:{seed}')
    drift = r * 1.6 if drift is None else drift
    out = []
    for i in range(n):
        t = i / max(1, n - 1)
        by = y - height * (t ** 0.9)
        bx = x + drift * math.sin(t * 5.2 + rnd.uniform(-0.4, 0.4))
        br = r * (1 - 0.55 * t) * rnd.uniform(0.85, 1.1)
        out.append(bubble(bx, by, br, pal=pal, **kw))
    return ''.join(out)


def seaweed(x, y, height, color, width=13, amp=16, wl=110, phase=0.0, lean=0.0):
    """Wavy ribbon of seaweed rising from (x, y), swaying more towards the tip."""
    pts = []
    for i in range(25):
        t = i / 24
        pts.append((x + amp * (0.3 + 0.7 * t) * math.sin(2 * math.pi * t * height / wl + phase) + lean * t * height,
                    y - t * height))
    return (f'<path d="{catmull(pts)}" fill="none" stroke="{color}" stroke-width="{fmt(width)}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


_CORAL = [
    [(0, 0), (0, -60), (-4, -110)],
    [(0, -40), (30, -70), (34, -120), (30, -160)],
    [(0, -50), (-34, -78), (-44, -128)],
    [(-4, -110), (-8, -170), (-4, -205)],
    [(-8, -160), (-30, -186), (-34, -214)],
    [(32, -120), (58, -146), (64, -180)],
    [(-44, -128), (-66, -150), (-70, -176)],
    [(31, -150), (14, -178), (14, -200)],
    [(-4, -170), (16, -196)],
]


def branch_coral(x, y, scale, color, width=9, flip=False):
    """Branching coral: round-capped strokes in a hand-drawn tree, base at (x, y), about 215*scale high and 135*scale wide."""
    m = -1 if flip else 1
    paths = [catmull([(x + m * px * scale, y + py * scale) for px, py in seg]) for seg in _CORAL]
    return (f'<g fill="none" stroke="{color}" stroke-width="{fmt(width)}" stroke-linecap="round" stroke-linejoin="round">'
            + ''.join(f'<path d="{d}"/>' for d in paths) + '</g>')


def fan_coral(x, y, h, color, n=9, spread=58, width=4.2):
    """Fan coral: thin strands that curve up and out from one base at (x, y); h is the height."""
    out = []
    for i in range(n):
        t = i / (n - 1) - 0.5
        a = math.radians(t * 2 * spread)
        hh = h * (1 - 0.28 * abs(t) * 2) * (0.92 + 0.08 * math.cos(i * 1.7))
        tx, ty = x + math.sin(a) * hh, y - math.cos(a) * hh
        cx, cy = x + math.sin(a) * hh * 0.25, y - hh * 0.62
        out.append(f'<path d="M{fmt(x)},{fmt(y)} Q{fmt(cx)},{fmt(cy)} {fmt(tx)},{fmt(ty)}"/>')
        if i % 2 == 0:
            mx, my = x + (tx - x) * 0.62, y + (ty - y) * 0.62
            out.append(f'<path d="M{fmt(mx)},{fmt(my)} l{fmt(math.copysign(h * 0.09, t or 1))},{fmt(-h * 0.145)}" '
                       f'stroke-width="{fmt(width * 0.8)}"/>')
    return (f'<g fill="none" stroke="{color}" stroke-width="{fmt(width)}" stroke-linecap="round">' + ''.join(out) + '</g>')


def fern(x, y, height, color, leaves=9, lean=0.0, size=1.0):
    """Fern-like seaweed: a gently curved stem with paired leaflets and a rounded bud on top. size scales the leaves."""
    stem = [(x + lean * height * (i / 10) ** 2, y - height * i / 10) for i in range(11)]
    out = [f'<path d="{catmull(stem)}" fill="none" stroke="{color}" stroke-width="{fmt(5 * size)}" stroke-linecap="round"/>']
    for i in range(1, leaves + 1):
        t = i / (leaves + 1)
        sx, sy = x + lean * height * t * t, y - height * t
        L = (34 - 18 * t) * size
        for side in (-1, 1):
            ex, ey = sx + side * L, sy - L * 0.55
            cx, cy = sx + side * L * 0.55, sy + L * 0.05
            out.append(f'<path d="M{fmt(sx)},{fmt(sy)} Q{fmt(cx)},{fmt(cy)} {fmt(ex)},{fmt(ey)} '
                       f'Q{fmt(sx + side * L * 0.35)},{fmt(sy - L * 0.55)} {fmt(sx)},{fmt(sy)} Z"/>')
    out.append(f'<ellipse cx="{fmt(x + lean * height)}" cy="{fmt(y - height - 8 * size)}" rx="{fmt(9 * size)}" ry="{fmt(13 * size)}"/>')
    return f'<g fill="{color}">' + ''.join(out) + '</g>'


def anemone(x, y, r, color=None, base=None, dot=None, seed=7, pal=PALETTE):
    """Dome anemone of radius r sitting on a small base at (x, y), with a bumpy frill and a dotted texture.
    Pass one colour for color, base and dot to get a monochrome silhouette."""
    color = color or pal['anemone']
    base = base or pal['coral']
    dot = dot or pal['anemone_dot']
    out = [f'<path d="M{fmt(x - r * 0.55)},{fmt(y)} L{fmt(x - r * 0.4)},{fmt(y - r * 0.32)} '
           f'L{fmt(x + r * 0.4)},{fmt(y - r * 0.32)} L{fmt(x + r * 0.55)},{fmt(y)} Z" fill="{base}"/>']
    cy0 = y - r * 0.3
    for i in range(13):
        a = math.pi + math.pi * i / 12
        out.append(f'<circle cx="{fmt(x + r * math.cos(a))}" cy="{fmt(cy0 + r * math.sin(a))}" r="{fmt(r * 0.17)}" fill="{color}"/>')
    out.append(f'<path d="M{fmt(x - r)},{fmt(cy0)} A{fmt(r)},{fmt(r)} 0 0 1 {fmt(x + r)},{fmt(cy0)} Z" fill="{color}"/>')
    rnd = _rng(f'anemone:{seed}')
    for i in range(16):                      # stratified angles, so the dots spread evenly over the dome
        a = math.pi + (0.1 + 0.8 * (i + rnd.random()) / 16) * math.pi
        rr = r * (0.22 + 0.6 * rnd.random())
        out.append(f'<circle cx="{fmt(x + rr * math.cos(a))}" cy="{fmt(cy0 + rr * math.sin(a))}" r="{fmt(r * 0.06)}" fill="{dot}"/>')
    return ''.join(out)


def starfish(x, y, r, color, rot=0.0):
    """Soft five-armed starfish of radius r centred at (x, y), rotated rot degrees."""
    pts = []
    for i in range(10):
        a = math.radians(rot - 90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return f'<path d="{catmull(pts, closed=True, tension=0.35)}" fill="{color}"/>'


def dots(x0, x1, top, depth, n, color, rmin=2.5, rmax=6, seed=0):
    """Scatter n small dots between x0 and x1, from `top` (a number, or a function of x giving the top edge) to top+depth."""
    rnd = _rng(f'dots:{seed}')
    fn = top if callable(top) else (lambda _x: top)
    out = []
    for _ in range(n):
        x = x0 + rnd.random() * (x1 - x0)
        yy = fn(x) + rnd.random() * depth
        out.append(f'<circle cx="{fmt(x)}" cy="{fmt(yy)}" r="{fmt(rmin + rnd.random() * (rmax - rmin))}"/>')
    return f'<g fill="{color}">' + ''.join(out) + '</g>'


# ------------------------------------------------------------------------------------------------------------ icons
def _chip(size, cls, body, label=None):
    a = f' role="img" aria-label="{label}"' if label else ' aria-hidden="true"'
    return (f'<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" class="{cls}" '
            f'style="width:{_size(size)};height:{_size(size)}" focusable="false"{a}>{body}</svg>')


def icon_question(size=6.4, color=None, cls='chip'):
    """Rounded amber chip with a white question mark (the quiz 'True or false?' marker)."""
    color = color or PALETTE['quiz_amber']
    return _chip(size, cls, f'<rect width="64" height="64" rx="16" fill="{color}"/>'
                 '<path d="M23,24 C23,15 41,14 41,24 C41,31 32,31 32,39" fill="none" stroke="#ffffff" stroke-width="7" '
                 'stroke-linecap="round" stroke-linejoin="round"/><circle cx="32" cy="49" r="4.6" fill="#ffffff"/>')


def icon_check(size=6.4, color=None, cls='chip'):
    """Rounded green chip with a white check mark (the quiz answer marker)."""
    color = color or PALETTE['quiz_green']
    return _chip(size, cls, f'<rect width="64" height="64" rx="16" fill="{color}"/>'
                 '<path d="M18,33 L28,43 L47,22" fill="none" stroke="#ffffff" stroke-width="7.5" stroke-linecap="round" '
                 'stroke-linejoin="round"/>')


def icon_boat(size=5.6, color=None, cls='ico'):
    """Small paper boat on a wave line (the 'What to do' marker)."""
    color = color or PALETTE['blue']
    return _chip(size, cls,
                 f'<path d="M10,39 L54,39 C52,44 47.5,48 42,48 L22,48 C16.5,48 12,44 10,39 Z" fill="{color}"/>'
                 f'<path d="M30,10 L30,36 L13,36 Z" fill="{color}" fill-opacity=".5"/>'
                 f'<path d="M34,15 L34,36 L49,36 Z" fill="{color}" fill-opacity=".78"/>'
                 f'<path d="M5,56 C10,52.5 15,52.5 20,56 C25,59.5 30,59.5 35,56 C40,52.5 45,52.5 50,56 C53,58 56,58.5 59,57.5" '
                 f'fill="none" stroke="{color}" stroke-width="3.4" stroke-linecap="round"/>')


def icon_bubble(size=5.6, color=None, cls='ico'):
    """Three rising outline bubbles with highlight arcs (a small ornament or list marker)."""
    color = color or PALETTE['blue']
    parts = []
    for cx, cy, r in ((25, 41, 15), (45.5, 22, 9.5), (50, 46, 5.5)):
        a0, a1, rr = math.radians(18), math.radians(74), r * 0.6
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" fill-opacity=".12" stroke="{color}" stroke-width="3.2"/>')
        parts.append(f'<path d="M{fmt(cx + rr * math.cos(a1), 2)},{fmt(cy - rr * math.sin(a1), 2)} A{fmt(rr, 2)},{fmt(rr, 2)} 0 0 1 '
                     f'{fmt(cx + rr * math.cos(a0), 2)},{fmt(cy - rr * math.sin(a0), 2)}" fill="none" stroke="{color}" '
                     f'stroke-width="{fmt(max(2.2, r * 0.2), 2)}" stroke-linecap="round" stroke-opacity=".7"/>')
    return _chip(size, cls, ''.join(parts))


def _arc(cx, cy, r, a0, a1, width, opacity, color='#ffffff'):
    """Arc on a circle from angle a1 to a0 (degrees, counter-clockwise from 3 o'clock, y up)."""
    p0 = (cx + r * math.cos(math.radians(a1)), cy - r * math.sin(math.radians(a1)))
    p1 = (cx + r * math.cos(math.radians(a0)), cy - r * math.sin(math.radians(a0)))
    return (f'<path d="M{fmt(p0[0], 2)},{fmt(p0[1], 2)} A{fmt(r, 2)},{fmt(r, 2)} 0 0 1 {fmt(p1[0], 2)},{fmt(p1[1], 2)}" fill="none" '
            f'stroke="{color}" stroke-opacity="{fmt(opacity, 2)}" stroke-width="{fmt(width, 2)}" stroke-linecap="round"/>')


def _num_size(num, base):
    return base if len(str(num)) <= 2 else base * 0.78


def section_bubble(num, uid, size=15, dark=False, cls='secbubble'):
    """Glossy blue bubble with a white section number (e.g. '03'): radial gradient, soft rim, highlight arc and glint.
    uid makes the gradient ids unique in the document."""
    p = DARK if dark else PALETTE
    g, s = f'{uid}-sb-fill', f'{uid}-sb-shine'
    defs = (f'<radialGradient id="{g}" cx="36%" cy="30%" r="78%">'
            f'<stop offset="0" stop-color="{mix(p["bubble_hi"], "#ffffff", 0.12)}"/><stop offset=".55" stop-color="{mix(p["bubble_hi"], p["bubble_lo"], 0.55)}"/>'
            f'<stop offset="1" stop-color="{p["bubble_lo"]}"/></radialGradient>'
            f'<radialGradient id="{s}" cx="50%" cy="100%" r="60%">'
            f'<stop offset="0" stop-color="#ffffff" stop-opacity=".22"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>')
    fs = _num_size(num, 38)
    body = (f'<circle cx="50" cy="50" r="47" fill="url(#{g})"/>'
            f'<ellipse cx="50" cy="80" rx="30" ry="14" fill="url(#{s})"/>'
            f'<circle cx="50" cy="50" r="46" fill="none" stroke="{mix(p["bubble_lo"], "#0b1b3d", 0.25)}" stroke-opacity=".35" stroke-width="2"/>'
            f'{_arc(50, 50, 37, 120, 160, 5.2, 0.75)}'
            f'<text x="50" y="{fmt(50 + fs * 0.35, 2)}" text-anchor="middle" font-family="Figtree" font-weight="800" '
            f'font-size="{fmt(fs, 2)}" fill="#ffffff" letter-spacing="-1">{num}</text>')
    return (f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" class="{cls}" '
            f'style="width:{_size(size)};height:{_size(size)}" aria-hidden="true" focusable="false"><defs>{defs}</defs>{body}</svg>')


def page_bubble(num, uid, size=6.8, color='#ffffff', cls='pnb'):
    """Page number in a glassy outline bubble, for the indigo footer band. Labelled 'Page N' for assistive tech."""
    g = f'{uid}-pb-glass'
    fs = _num_size(num, 44)
    defs = (f'<radialGradient id="{g}" cx="38%" cy="30%" r="80%"><stop offset="0" stop-color="{color}" stop-opacity=".3"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity=".06"/></radialGradient>')
    body = (f'<circle cx="50" cy="50" r="45" fill="url(#{g})" stroke="{color}" stroke-opacity=".82" stroke-width="5"/>'
            f'{_arc(50, 50, 34, 118, 160, 6.5, 0.9, color)}'
            f'<text x="50" y="{fmt(50 + fs * 0.36, 2)}" text-anchor="middle" font-family="Figtree" font-weight="800" '
            f'font-size="{fmt(fs, 2)}" fill="{color}">{num}</text>')
    return (f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" class="{cls}" '
            f'style="width:{_size(size)};height:{_size(size)}" role="img" aria-label="Page {num}" focusable="false">'
            f'<defs>{defs}</defs>{body}</svg>')


def wavy_rule(width=1000, color='#bcd3f5', amp=4, wl=60, stroke=2.4, cls='wavyrule'):
    """A thin wavy line, stretched to its box (preserveAspectRatio none): a divider between sections."""
    h = 2 * amp + 2 * stroke + 4
    pts = sine_pts(0, width, h / 2, amp, wl, step=wl / 12)
    return _svg(width, h, f'<path d="{catmull(pts)}" fill="none" stroke="{color}" stroke-width="{fmt(stroke)}" stroke-linecap="round"/>',
                cls, ' preserveAspectRatio="none"')


# ------------------------------------------------------------------------------------------------------------ water surface
def _surface(width, height, pal, glint=True, wl=None, y0=0.0):
    """Two-layer water surface paths (back light wave, front blue wave, light glints) filling from y0 down to the wave line."""
    wl = wl or height * 1.25
    amp = height * 0.075
    back = sine_pts(-wl, width + wl, y0 + height * 0.62, amp, wl, phase=1.9, step=wl / 15)
    front = sine_pts(-wl, width + wl, y0 + height * 0.42, amp, wl, phase=0.0, step=wl / 15)
    close = f' L{fmt(width + wl)},{fmt(y0 - 1)} L{fmt(-wl)},{fmt(y0 - 1)} Z'
    out = (f'<path d="{catmull(back)}{close}" fill="{pal["wave_back"]}"/>'
           f'<path d="{catmull(front)}{close}" fill="{pal["wave_front"]}"/>')
    if glint:
        g = sine_pts(-wl, width + wl, y0 + height * 0.22, amp * 0.55, wl, phase=0.0, step=wl / 15)
        out += (f'<path d="{catmull(g)}" fill="none" stroke="#ffffff" stroke-opacity=".24" stroke-width="{fmt(height * 0.022, 2)}" '
                f'stroke-linecap="round" stroke-dasharray="{fmt(wl * 0.3)} {fmt(wl * 0.7)}"/>')
    return out


def top_wave(width=2100, height=120, dark=False, glint=True, wl=None, cls='topwave'):
    """Water surface along the top edge: a light back wave and a blue front wave, with faint light glints.
    Stretches to its box (preserveAspectRatio none). wl is the wavelength (default 1.25 x height)."""
    pal = DARK if dark else PALETTE
    return _svg(width, height, _surface(width, height, pal, glint, wl), cls, ' preserveAspectRatio="none"')


# ------------------------------------------------------------------------------------------------------------ seabed
_SEABED = {
    #           far   mid   near  band  (fractions of height: top line of each layer)  amps,  decor scale ref height
    'tall': dict(far=0.37, mid=0.53, near=0.70, band=0.86, amp=(0.048, 0.052, 0.042, 0.011), ref=640, wl=(1.0, 0.85, 0.72)),
    'slim': dict(far=0.27, mid=0.43, near=0.58, band=0.72, amp=(0.05, 0.055, 0.045, 0.016), ref=360, wl=(1.0, 0.85, 0.72)),
}


def _ridge(rnd, width, base, amp, wl):
    """A smooth hill line: two summed sines with seeded phases. Returns (points for catmull, y(x) function)."""
    p1, p2 = rnd.uniform(0, 6.283), rnd.uniform(0, 6.283)
    w1, w2 = wl * rnd.uniform(0.9, 1.1), wl * rnd.uniform(0.42, 0.55)

    def y(x):
        return base + amp * math.sin(2 * math.pi * x / w1 + p1) + amp * 0.38 * math.sin(2 * math.pi * x / w2 + p2)
    step = w2 / 6
    n = int((width + 2 * step) / step) + 2
    pts = [(-step + i * step, y(-step + i * step)) for i in range(n)]
    return pts, y


def _slots(rnd, x0, x1, gap, avoid):
    """Decor positions between x0 and x1, about `gap` apart with jitter, skipping the avoid ranges [(a, b), ...]."""
    out, x = [], x0 + gap * rnd.uniform(0.15, 0.6)
    while x < x1:
        if not any(a <= x <= b for a, b in avoid):
            out.append(x)
        x += gap * rnd.uniform(0.75, 1.3)
    return out


_SWAY_N = 6     # sway=True: the plants cycle through this many timing classes (s0 .. s5)


def _sway_css():
    """The <style> of an animated seabed (seabed(sway=True)): each plant rocks a few degrees about its base. Timing comes
    from the plant's index (class sN), never from the random generator, so the drawing stays the same as the still seabed."""
    rules = ''.join(f'.s{i}{{animation-duration:{fmt(5.2 + 3.6 * ((i * 5) % _SWAY_N) / (_SWAY_N - 1), 2)}s;'
                    f'animation-delay:-{fmt(0.9 + 1.3 * i, 2)}s}}' for i in range(_SWAY_N))
    return ('<style>.sway{transform-box:fill-box;transform-origin:50% 100%;animation:sway 7s ease-in-out infinite}'
            '.sway.fan{animation-name:sway-fan}' + rules +
            '@keyframes sway{0%,100%{transform:rotate(-3deg)}50%{transform:rotate(3deg)}}'
            '@keyframes sway-fan{0%,100%{transform:rotate(-1.8deg)}50%{transform:rotate(1.8deg)}}'
            '@media (prefers-reduced-motion:reduce){.sway{animation:none}}</style>')


def _bed(width, height, top, h, pal, rnd, variant='tall', avoid=(), decor=True, star=True, scale=None, sway=False):
    """Layered seabed drawn into the box y = top .. top + h (hills run to top + h + 10). Returns (svg, layer functions).
    scale sets the size of decoration, dots and starfish (default: h / the variant's reference height).
    sway=True wraps each fern and fan coral in <g class="sway sN"> for _sway_css (branch coral stays still)."""
    v = _SEABED[variant]
    u = scale or h / v['ref']               # decor scale
    W = width
    layers = {}
    wl0 = max(h * 2.6, 900 * u)
    for i, k in enumerate(('far', 'mid', 'near')):
        layers[k] = _ridge(rnd, W, top + v[k] * h, v['amp'][i] * h, wl0 * v['wl'][i])
    bottom = top + h + 10

    def hill(pts, color):
        return f'<path d="{catmull(pts)} L{fmt(W + 40)},{fmt(bottom)} L-40,{fmt(bottom)} Z" fill="{color}"/>'

    plants = [0]

    def plant(svg, kind):
        if not sway:
            return svg
        n = plants[0]
        plants[0] += 1
        return f'<g class="sway s{n % _SWAY_N}{" fan" if kind == "fan" else ""}">{svg}</g>'

    out = []
    far_pts, fy = layers['far']
    mid_pts, my = layers['mid']
    near_pts, ny = layers['near']
    if decor:
        for i, x in enumerate(_slots(rnd, W * 0.03, W * 0.97, 520 * u, avoid)):
            kind = rnd.choice(('fan', 'fern', 'fan', 'coral'))
            base = fy(x) + 14 * u
            if kind == 'fan':
                out.append(plant(fan_coral(x, base, rnd.uniform(52, 74) * u, pal['far_dk'], n=rnd.choice((8, 9)), width=4 * u), kind))
            elif kind == 'fern':
                out.append(plant(fern(x, base, rnd.uniform(70, 92) * u, pal['far_dk'], leaves=6, lean=rnd.uniform(-0.18, 0.18), size=0.7 * u),
                                 kind))
            else:
                out.append(branch_coral(x, base, 0.42 * u, pal['far_dk'], width=6 * u, flip=rnd.random() < 0.5))
    out.append(hill(far_pts, pal['far']))
    if decor:
        for x in _slots(rnd, W * 0.05, W * 0.95, 430 * u, avoid):
            kind = rnd.choice(('fern', 'coral', 'fan', 'fern'))
            base = my(x) + 14 * u
            if kind == 'fern':
                out.append(plant(fern(x, base, rnd.uniform(84, 112) * u, pal['mid_dk'], leaves=rnd.choice((6, 7, 8)),
                                      lean=rnd.uniform(-0.22, 0.16), size=0.85 * u), kind))
            elif kind == 'coral':
                out.append(branch_coral(x, base + 2 * u, rnd.uniform(0.52, 0.64) * u, pal['mid_dk'], width=7.5 * u, flip=rnd.random() < 0.5))
            else:
                out.append(plant(fan_coral(x, base, rnd.uniform(90, 112) * u, pal['mid_dk'], n=11, width=5 * u), kind))
    out.append(hill(mid_pts, pal['mid']))
    out.append(dots(0, W, lambda x: my(x) + 16 * u, (v['near'] - v['mid']) * h + 30 * u, int(W / (46 * u)) or 1,
                    pal['dot_mid'], 2.5 * u, 5.5 * u, seed=rnd.random()))
    if star:
        for x in _slots(rnd, W * 0.12, W * 0.9, 1100 * u, avoid):
            out.append(starfish(x, my(x) + (v['near'] - v['mid']) * h * 0.55, rnd.uniform(20, 27) * u, pal['star'], rot=rnd.uniform(-20, 25)))
    out.append(hill(near_pts, pal['near']))
    out.append(dots(0, W, lambda x: ny(x) + 16 * u, (v['band'] - v['near']) * h + 20 * u, int(W / (52 * u)) or 1,
                    pal['dot_near'], 2.5 * u, 6 * u, seed=rnd.random()))
    if star:
        for x in _slots(rnd, W * 0.3, W * 0.8, 1400 * u, avoid):
            out.append(starfish(x, ny(x) + (v['band'] - v['near']) * h * 0.45, rnd.uniform(18, 24) * u, pal['dot_mid'], rot=rnd.uniform(0, 40)))
    return ''.join(out), {'far': fy, 'mid': my, 'near': ny}


def seabed(width=2100, height=640, variant='tall', seed=26, dark=False, band=True, band_top=None, dy=0, avoid=(), cls='seabed',
           sway=False):
    """Monochrome layered seabed (far, middle and near hills with coral, fern and fan silhouettes, dots and starfish),
    ending in a flat-topped indigo footer band for the running footer.

    variant 'tall' is the full page-bottom scene of the sample; 'slim' is the shallow strip for content pages.
    band=False leaves the band out; band_top (user units) moves its top line. dy shifts the hills and decoration down
    (the band does not move), so the tallest piece can clear a card above it. avoid=[(x0, x1), ...] keeps decoration
    out of those x ranges. dark=True uses the night-water silhouettes.
    sway=True (screens only) is the same picture with each fern and fan coral in a <g class="sway sN"> and CSS keyframes
    inside the SVG that rock them gently about their bases (5-9 s, staggered); remove the <style> and those groups and
    it is the still seabed, byte for byte. The motion stops under prefers-reduced-motion: reduce."""
    pal = DARK if dark else PALETTE
    rnd = _rng(f'seabed:{variant}:{seed}')
    v = _SEABED[variant]
    body, _ = _bed(width, height, 0, height, pal, rnd, variant, avoid, sway=sway)
    out = [f'<g transform="translate(0,{fmt(dy)})">{body}</g>' if dy else body]
    if band:
        bt = v['band'] * height if band_top is None else band_top
        wave = sine_pts(-30, width + 30, bt, v['amp'][3] * height, max(width / 4, 300), phase=0.6, step=max(width / 70, 10))
        out.append(f'<path d="{catmull(wave)} L{fmt(width + 30)},{fmt(height + 10)} L-30,{fmt(height + 10)} Z" fill="{pal["band"]}"/>')
    return _svg(width, height, (_sway_css() if sway else '') + ''.join(out), cls)


# ------------------------------------------------------------------------------------------------------------ light
_BLOBS = [
    ([(-60, 150), (260, 110), (520, 210), (430, 420), (140, 520), (-60, 470)], 0.75),
    ([(1700, 120), (2000, 90), (2170, 230), (2150, 560), (1930, 610), (1780, 420)], 0.7),
    ([(-80, 1500), (120, 1380), (260, 1560), (200, 1900), (-60, 2050)], 0.55),
    ([(1900, 1850), (2120, 1700), (2200, 2100), (2050, 2300), (1880, 2120)], 0.55),
]


def _blobs(width, height, color, opacity, ripple):
    sx, sy = width / 2100, height / 2970
    out = [f'<path d="{catmull([(x * sx, y * sy) for x, y in pts], closed=True)}" fill="{color}" fill-opacity="{fmt(op * opacity, 2)}"/>'
           for pts, op in _BLOBS]
    if ripple:
        w1 = sine_pts(-30, width + 30, height * 0.771, 30 * sy, width * 0.43, phase=0.4, step=max(width / 70, 4))
        out.append(f'<path d="{catmull(w1)} L{fmt(width + 30)},{fmt(height)} L-30,{fmt(height)} Z" fill="{color}" '
                   f'fill-opacity="{fmt(0.38 * opacity, 2)}"/>')
    return ''.join(out)


def light_blobs(width=2100, height=2970, color='#ffffff', opacity=1.0, ripple=True, cls='light'):
    """Soft lighter shapes in the water, like sunlight through the surface, plus a wide pale ripple band low down.
    Laid out for a portrait page and stretched to the box (preserveAspectRatio none)."""
    return _svg(width, height, _blobs(width, height, color, opacity, ripple), cls, ' preserveAspectRatio="none"')


def _rays(width, height, uid, seed, n, opacity, color, top=0.0, reach=0.8):
    rnd = _rng(f'rays:{seed}')
    g = f'{uid}-ray'
    defs = (f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="{fmt(opacity, 2)}"/>'
            f'<stop offset=".55" stop-color="{color}" stop-opacity="{fmt(opacity * 0.35, 2)}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>')
    out = []
    src = width * rnd.uniform(0.38, 0.62)             # the sun sits above the surface, slightly off centre
    span = width * 1.1
    for i in range(n):
        t = (i + 0.5) / n
        x_top = width * (-0.05 + 1.1 * t) + rnd.uniform(-0.03, 0.03) * width
        w_top = width * rnd.uniform(0.025, 0.05)
        length = height * reach * rnd.uniform(0.75, 1.0)
        lean = (x_top - src) / span * 0.9            # rays fan out from the sun
        w_bot = w_top * rnd.uniform(2.2, 3.2)
        xb = x_top + lean * length
        y0, y1 = top, top + length
        op = rnd.uniform(0.55, 1.0)
        for k in (1.0, 0.62, 0.3):                   # nested shafts give the ray a soft edge without a blur filter
            wt, wb = w_top * k, w_bot * k
            out.append(f'<path d="M{fmt(x_top - wt / 2)},{fmt(y0)} L{fmt(x_top + wt / 2)},{fmt(y0)} '
                       f'L{fmt(xb + wb / 2)},{fmt(y1)} L{fmt(xb - wb / 2)},{fmt(y1)} Z" fill="url(#{g})" fill-opacity="{fmt(op / 3, 2)}"/>')
    return defs, ''.join(out)


def light_rays(width, height, uid, seed=3, n=7, opacity=0.4, color='#ffffff', reach=0.8, cls='rays'):
    """Soft shafts of sunlight fanning down from the surface (for covers and banners). They fade out by `reach` x height."""
    defs, body = _rays(width, height, uid, seed, n, opacity, color, reach=reach)
    return _svg(width, height, body, cls, ' preserveAspectRatio="none"', defs)


# ------------------------------------------------------------------------------------------------------------ full scene
def scene_safe_area(width, height):
    """The (x0, y0, x1, y1) box that underwater_scene keeps free of fish, bubbles and reef, for a title or text block."""
    if width / height >= 1.6:          # wide banner: text on the left
        return (width * 0.05, height * 0.16, width * 0.56, height * 0.62)
    return (width * 0.08, height * 0.11, width * 0.92, height * 0.47)


def underwater_scene(width, height, seed=1, mood='light', uid='scene', band=None, cls='scene'):
    """A complete full-bleed underwater picture for covers and banners: gradient water from a bright surface to the deep,
    a sun glow and soft light rays, a two-layer water surface, rising bubble trails, a small school of fish with two
    companions, and a layered seabed with reef colour (seaweed, branching coral, anemone) in front of monochrome silhouettes.

    mood 'light' is day water (white surface to periwinkle, indigo footer band); 'deep' is night water for white text on top.
    The box scene_safe_area(width, height) stays free of fish, bubbles and reef, so a title can sit there.
    Portrait and square sizes get the cover layout; width/height >= 1.6 gets the banner layout (text on the left).
    band (default: True for portrait, False for wide) adds the flat footer band at the bottom."""
    if mood not in ('light', 'deep'):
        raise ValueError(f"mood must be 'light' or 'deep', not {mood!r}")
    deep = mood == 'deep'
    W, H = float(width), float(height)
    wide = W / H >= 1.6
    band = (not wide) if band is None else band
    pal = dict(DARK if deep else PALETTE)
    rnd = _rng(f'scene:{seed}:{mood}:{int(wide)}')
    u = H / 440.0 if wide else W / 1000.0           # one scene unit: fish and reef scale with the picture

    if deep:
        water = (('0', '#3f7fe6'), ('.16', '#2a62d4'), ('.42', '#1f4bb4'), ('.7', '#173983'), ('1', '#0e2357'))
        pal.update(far='#1d3a86', far_dk='#2a4a9a', mid='#183175', mid_dk='#22408b', near='#132863', dot_mid='#22408a',
                   dot_near='#1d3878', star='#2c4a9a', band='#0a1430', wave_back='#5d92ee', wave_front='#2f6fe0')
        glow, ray_op, far_fish = '#bcd6ff', 0.2, '#3a63c0'
        bubble_kw = dict(stroke='#9cc0ff', fill='#cfe0ff', fill_op=0.16)
    else:
        water = (('0', '#ffffff'), ('.14', '#f3f8fe'), ('.4', '#dfeafb'), ('.66', '#c8d9f5'), ('1', '#b3c6f0'))
        pal.update(far='#c3cdf2', far_dk='#aab6ea', mid='#9ba8e3', mid_dk='#8191d8', near='#7381cf')
        glow, ray_op, far_fish = '#ffffff', 0.62, '#a9b8e8'
        bubble_kw = dict(fill_op=0.6)

    gid, glid = f'{uid}-water', f'{uid}-glow'
    defs = (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            + ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in water) + '</linearGradient>'
            f'<radialGradient id="{glid}" cx="50%" cy="0%" r="70%">'
            f'<stop offset="0" stop-color="{glow}" stop-opacity="{".45" if deep else ".9"}"/>'
            f'<stop offset="1" stop-color="{glow}" stop-opacity="0"/></radialGradient>')
    out = [f'<rect width="{fmt(W)}" height="{fmt(H)}" fill="url(#{gid})"/>']
    sun_x = W * (0.62 if wide else 0.58)
    out.append(f'<ellipse cx="{fmt(sun_x)}" cy="0" rx="{fmt(W * (0.5 if wide else 0.75))}" ry="{fmt(H * (0.8 if wide else 0.42))}" '
               f'fill="url(#{glid})"/>')

    bed_top = H * (0.64 if wide else 0.70)
    bed_h = H - bed_top
    rdefs, rays = _rays(W, H, uid, f'{seed}:{mood}', 7 if wide else 8, ray_op, '#ffffff', reach=0.95 if wide else 0.8)
    defs += rdefs
    out.append(rays)

    # faint far fish, small, away from the text box
    if wide:
        out.append(fish_school(W * 0.94, H * 0.2, 16 * u, far_fish, n=4, seed=f'{seed}f', mono=True))
    else:
        out.append(fish_school(W * 0.82, H * 0.5, 20 * u, far_fish, n=4, seed=f'{seed}f', mono=True))

    # seabed silhouettes
    bed, layer = _bed(W, H, bed_top, bed_h * (1.0 if band else 1.1), pal, rnd, 'tall', scale=u * (0.62 if wide else 0.8))
    out.append(bed)

    # reef colour in the two bottom corners
    reef = []
    if wide:
        foot = H
        lx, rx = W * 0.03, W * 0.93
        reef.append(seaweed(lx, foot + 6 * u, bed_h * 1.12, pal['weed'], width=12 * u, amp=11 * u, wl=110 * u, phase=0.3))
        reef.append(seaweed(lx + 30 * u, foot + 6 * u, bed_h * 0.78, pal['weed_light'], width=9 * u, amp=9 * u, wl=95 * u, phase=2.2))
        reef.append(branch_coral(rx, foot + 4 * u, 0.82 * u, pal['coral'], width=10 * u))
        reef.append(anemone(rx - 110 * u, foot - 2 * u, 40 * u, pal=pal))
        reef.append(seaweed(rx + 70 * u, foot + 6 * u, bed_h * 0.7, pal['weed'], width=9 * u, amp=8 * u, wl=90 * u, phase=1.1))
    else:
        foot = bed_top + 0.86 * bed_h if band else H
        lx, rx = W * 0.065, W * 0.875
        reef.append(seaweed(lx, foot + 8 * u, bed_h * 0.95, pal['weed'], width=13 * u, amp=13 * u, wl=125 * u, phase=0.3))
        reef.append(seaweed(lx + 36 * u, foot + 10 * u, bed_h * 0.64, pal['weed_light'], width=10 * u, amp=11 * u, wl=100 * u, phase=2.2))
        reef.append(branch_coral(rx, foot + 6 * u, 1.0 * u, pal['coral'], width=11.5 * u))
        reef.append(anemone(rx - 128 * u, foot + 4 * u, 46 * u, pal=pal))
        reef.append(seaweed(rx + 78 * u, foot + 8 * u, bed_h * 0.5, pal['weed_light'], width=9 * u, amp=8 * u, wl=90 * u, phase=1.4))
    out.append(''.join(reef))
    if band:
        bt = bed_top + 0.86 * bed_h
        wave = sine_pts(-30, W + 30, bt, 0.011 * bed_h, W / 2.5, phase=0.6, step=W / 60)
        out.append(f'<path d="{catmull(wave)} L{fmt(W + 30)},{fmt(H + 10)} L-30,{fmt(H + 10)} Z" fill="{pal["band"]}"/>')

    # bubbles rising from the reef, outside the text box
    if wide:
        out.append(bubble_trail(W * 0.045, H * 0.62, H * 0.4, 8 * u, n=5, seed=f'{seed}a', pal=pal, **bubble_kw))
        out.append(bubble_trail(W * 0.905, H * 0.68, H * 0.42, 9 * u, n=6, seed=f'{seed}b', pal=pal, **bubble_kw))
    else:
        out.append(bubble_trail(W * 0.09, foot - bed_h * 0.98, H * 0.16, 11 * u, n=5, seed=f'{seed}a', pal=pal, **bubble_kw))
        out.append(bubble_trail(W * 0.86, foot - bed_h * 0.9, H * 0.1, 12 * u, n=4, seed=f'{seed}b', pal=pal, **bubble_kw))
        out.append(bubble_trail(W * 0.4, H * 0.66, H * 0.1, 8 * u, n=3, seed=f'{seed}c', pal=pal, **bubble_kw))

    # the school: one colour, heading left; two companions in other reef colours
    if wide:
        out.append(fish_school(W * 0.7, H * 0.36, 30 * u, 'blue', n=7, seed=seed, pal=pal))
        out.append(fish(W * 0.84, H * 0.52, 66 * u, 'yellow', pal=pal))
        out.append(fish(W * 0.62, H * 0.6, 40 * u, 'red', flip=True, pal=pal))
    else:
        out.append(fish_school(W * 0.62, H * 0.56, 44 * u, 'blue', n=7, seed=seed, pal=pal))
        out.append(fish(W * 0.24, H * 0.6, 104 * u, 'yellow', flip=True, pal=pal))
        out.append(fish(W * 0.8, H * 0.635, 62 * u, 'red', pal=pal))

    # the water surface on top of everything
    sh = H * (0.07 if wide else 0.04)
    out.append(_surface(W, sh, pal, True, wl=sh * (2.2 if wide else 1.7)))
    return _svg(W, H, ''.join(out), cls, ' preserveAspectRatio="xMidYMid slice"', defs)


# ------------------------------------------------------------------------------------------------------------ diver bot


BOT_POSES = ('swim', 'wave', 'read', 'point', 'peek', 'head')
BOT_FORBIDDEN_HEX = ('#4285f4', '#ea4335', '#fbbc05', '#34a853')

_BOT_LIGHT = {
    'line': '#2e3870', 'stalk': '#2152c4',
    'shell': '#f7faff', 'shade': '#d9e4f6', 'hi': '#ffffff', 'joint': '#c6d4ee',
    'frame': '#2f6fe0', 'frame_hi': '#6c9cf2', 'strap': '#4b56ad', 'rivet': '#a9cbf6',
    'glass_top': '#f2f8ff', 'glass_bot': '#bcd6f8', 'eye': '#253048', 'mouth': '#253048', 'tongue': '#f26b4f',
    'cheek': '#f26b4f',
    'deep_top': '#0b1b3d', 'deep_bot': '#2152c4', 'deep_eye': '#ffffff', 'eye_glow': '#9cc0ff',
    'panel': '#2f6fe0', 'panel_line': '#a9cbf6', 'belt': '#4b56ad', 'buckle': '#f7c443',
    'glove': '#3a8ee6', 'glove_sh': '#2b73cc',
    'fin': '#ee6a3c', 'fin_rib': '#f5916b', 'snorkel': '#ee6a3c', 'snorkel_band': '#ffffff',
    'bulb': '#f7c443', 'bulb_core': '#fff3c4', 'glow': '#f7c443',
    'cover': '#f7c443', 'cover_dk': '#e3a82c', 'page': '#ffffff', 'page_sh': '#e6eefc', 'ink': '#9fbbec', 'fish': '#ee6a3c',
    'motion': '#7fa8ec',
}
_BOT_DARK = dict(_BOT_LIGHT, **{
    'line': '#3a4a96', 'stalk': '#8fb8ff',
    'shell': '#f3f7ff', 'shade': '#c9d7f1', 'joint': '#aebfe0',
    'frame': '#4f8ff0', 'frame_hi': '#8fb8ff', 'strap': '#6a75d6', 'rivet': '#cfe2ff',
    'panel': '#3a8ee6', 'panel_line': '#cfe2ff', 'belt': '#6a75d6', 'buckle': '#ffd055',
    'glove': '#4f9df2', 'glove_sh': '#3b84dc',
    'fin': '#ff7a4a', 'fin_rib': '#ffa27a', 'snorkel': '#ff7a4a',
    'bulb': '#ffd055', 'glow': '#ffd055', 'cover': '#ffd055', 'cover_dk': '#eab23a', 'fish': '#ff7a5e',
    'motion': '#8fb8ff',
})
_BOT_BUBBLES = (dict(), dict(stroke='#9cc0ff', fill='#cfe0ff', fill_op=0.18))   # light, night water

# Each pose's bounding box in design units (cx, cy, w, h), outline included; measured from the drawing.
_BOT_BOX = {
    'swim': (41.4, 2.1, 310.3, 282.1), 'wave': (16.1, -18.5, 176.8, 246.2), 'read': (0.9, -17.9, 154.5, 244.1),
    'point': (28.7, -18.3, 192.9, 246.5), 'peek': (-4.7, -57.7, 143.2, 119.3), 'head': (4.0, -70.5, 127.0, 130.0),
    'head-low': (6.5, -63.8, 112.0, 116.5), 'head-tiny': (6.5, -52.5, 112.0, 94.0),
}


def _bn(v):
    return fmt(v, 2)


def _bmul(a, b):
    return (a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1], a[0] * b[2] + a[2] * b[3], a[1] * b[2] + a[3] * b[3],
            a[0] * b[4] + a[2] * b[5] + a[4], a[1] * b[4] + a[3] * b[5] + a[5])


def _brot(deg, cx=0.0, cy=0.0):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return _bmul(_bmul((1, 0, 0, 1, cx, cy), (c, s, -s, c, 0, 0)), (1, 0, 0, 1, -cx, -cy))


def _bapply(m, p):
    return (m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5])


def _bst(c, k=1.0):
    return f'stroke="{c["line"]}" stroke-width="{_bn(c["lw"] * k)}" stroke-linejoin="round" stroke-linecap="round"'


def _bunion(c, shapes, fill, k=1.0):
    """Shapes merged into one silhouette: an outline pass for all of them, then a fill pass (no inner outlines)."""
    return (''.join(s.replace('/>', f' fill="{c["line"]}" stroke="{c["line"]}" stroke-width="{_bn(c["lw"] * 2 * k)}" '
                               f'stroke-linejoin="round"/>') for s in shapes)
            + ''.join(s.replace('/>', f' fill="{fill}"/>') for s in shapes))


# --- head --------------------------------------------------------------------------------------------------------------
_DOME = 'M-47,-44 C-47,-78 -26,-97 0,-97 C26,-97 47,-78 47,-44 L47,-28 C47,-15 39,-8 26,-8 L-26,-8 C-39,-8 -47,-15 -47,-28 Z'
_DOME_SHADE = 'M18,-94 C37,-87 47,-68 47,-44 L47,-28 C47,-15 39,-8 26,-8 L18,-8 C31,-10 39,-18 39,-30 L39,-46 C39,-68 32,-84 18,-94 Z'


def _bot_antenna(c, low=False):
    if c['tiny']:
        return ''
    w, top, by, br = (6.2, -103, -109, 10.5) if low else (3.8, -111, -118, 8.2)
    d = f'M0,-95 L0,{top}'
    out = (f'<path d="{d}" fill="none" stroke="{c["line"]}" stroke-width="{_bn(w + 2 * c["lw"])}" stroke-linecap="round"/>'
           f'<path d="{d}" fill="none" stroke="{c["stalk"]}" stroke-width="{_bn(w)}" stroke-linecap="round"/>')
    if not low:
        out += f'<circle cx="0" cy="{by}" r="{20 if c["dark"] else 15}" fill="url(#{c["uid"]}-glow)"/>'
    out += f'<circle cx="0" cy="{by}" r="{br}" fill="{c["bulb"]}" {_bst(c)}/>'
    if not low:
        out += f'<circle cx="-2.6" cy="{_bn(by - 2.6)}" r="2.5" fill="{c["bulb_core"]}"/>'
    return out


def _bot_snorkel(c, low=False):
    if low:
        d, w = 'M44,-34 C55,-34 60,-40 60,-50 L60,-82 C60,-90 56,-94 50,-95', 13.0
        return (f'<path d="{d}" fill="none" stroke="{c["line"]}" stroke-width="{_bn(w + 2 * c["lw"])}" stroke-linecap="round"/>'
                f'<path d="{d}" fill="none" stroke="{c["snorkel"]}" stroke-width="{_bn(w)}" stroke-linecap="round"/>')
    d, w = 'M27,-21 C44,-17 58,-25 58,-42 L58,-96 C58,-104 54,-108 47,-109', 9.5
    out = (f'<path d="{d}" fill="none" stroke="{c["line"]}" stroke-width="{_bn(w + 2 * c["lw"])}" stroke-linecap="round"/>'
           f'<path d="{d}" fill="none" stroke="{c["snorkel"]}" stroke-width="{_bn(w)}" stroke-linecap="round"/>')
    if c['full']:
        out += (f'<path d="M53.4,-76 L62.6,-76 M53.4,-87 L62.6,-87" stroke="{c["snorkel_band"]}" stroke-width="3" '
                f'stroke-linecap="round"/>')
    # mouthpiece plugged into the mask's lower rim, and the strap clip holding the tube
    out += (f'<rect x="17" y="-27" width="13" height="10" rx="4" transform="rotate(14 23.5 -22)" fill="{c["strap"]}" {_bst(c)}/>'
            f'<rect x="45" y="-56" width="20" height="11" rx="4" fill="{c["strap"]}" {_bst(c)}/>')
    return out


def _bot_blink_css(c):
    """The <style> of a blinking bot (diver_bot(blink=...)): the eyes squash to 10% height for about 120 ms once per period.
    Class and keyframe names carry the uid, so several bots can share a document."""
    k, p = f'{c["uid"]}-blink', c['blink']
    t = 6 / p                                   # 60 ms to close and 60 ms to open again, in percent of the period
    return (f'<style>.{k}{{transform-box:fill-box;transform-origin:50% 50%;animation:{k} {fmt(p, 2)}s linear infinite}}'
            f'@keyframes {k}{{0%,80%,{fmt(80 + 2 * t, 2)}%,100%{{transform:scaleY(1)}}{fmt(80 + t, 2)}%{{transform:scaleY(.1)}}}}'
            f'@media (prefers-reduced-motion:reduce){{.{k}{{animation:none}}}}</style>')


def _bot_eyes(c, svg):
    """The eyes, wrapped in the blink group when the bot blinks (unchanged otherwise)."""
    return f'<g class="{c["uid"]}-blink">{svg}</g>' if c.get('blink') else svg


def _bot_face(c, eyes='open', look=(0.0, 0.0), mouth='smile', low=False):
    lx, ly = look
    deep = c['deep']
    eye = c['deep_eye'] if deep else c['eye']
    mc = c['deep_eye'] if deep else c['mouth']
    out = []
    if low:
        out.append(_bot_eyes(c, ''.join(f'<ellipse cx="{ex}" cy="-49" rx="8.2" ry="10.2" fill="{eye}"/>' for ex in (-12.5, 12.5))))
        out.append(f'<path d="M-9,-33.5 Q0,-25 9,-33.5" fill="none" stroke="{mc}" stroke-width="5.6" stroke-linecap="round"/>')
        return ''.join(out)
    if deep and c['dark']:
        for ex in (-13, 13):
            out.append(f'<circle cx="{_bn(ex + lx)}" cy="{_bn(-50 + ly)}" r="13" fill="url(#{c["uid"]}-eyeglow)"/>')
    ey = []
    if eyes == 'happy':
        for ex in (-13, 13):
            ey.append(f'<path d="M{_bn(ex - 6 + lx)},{_bn(-48 + ly)} Q{_bn(ex + lx)},{_bn(-57 + ly)} {_bn(ex + 6 + lx)},{_bn(-48 + ly)}" '
                      f'fill="none" stroke="{eye}" stroke-width="3.8" stroke-linecap="round"/>')
    else:
        for ex in (-13, 13):
            ey.append(f'<ellipse cx="{_bn(ex + lx)}" cy="{_bn(-50 + ly)}" rx="5.4" ry="7" fill="{eye}"/>')
            if not deep:
                ey.append(f'<circle cx="{_bn(ex + lx - 1.8)}" cy="{_bn(-52.6 + ly)}" r="2.1" fill="#ffffff"/>')
    out.append(_bot_eyes(c, ''.join(ey)))
    if c['full']:
        for ex in (-24, 24):
            out.append(f'<ellipse cx="{_bn(ex + lx * .5)}" cy="{_bn(-39 + ly * .5)}" rx="5" ry="3" fill="{c["cheek"]}" '
                       f'fill-opacity="{".6" if deep else ".45"}"/>')
    mx, my = lx * .5, ly * .5
    if mouth == 'open':
        fill = '#e8f0ff' if deep else c['mouth']
        out.append(f'<path d="M{_bn(-7 + mx)},{_bn(-36 + my)} Q{_bn(mx)},{_bn(-35.4 + my)} {_bn(7 + mx)},{_bn(-36 + my)} '
                   f'Q{_bn(6 + mx)},{_bn(-27 + my)} {_bn(mx)},{_bn(-27 + my)} Q{_bn(-6 + mx)},{_bn(-27 + my)} {_bn(-7 + mx)},{_bn(-36 + my)} Z" '
                   f'fill="{fill}"/>'
                   f'<path d="M{_bn(-3.6 + mx)},{_bn(-28.6 + my)} Q{_bn(mx)},{_bn(-32.5 + my)} {_bn(3.6 + mx)},{_bn(-28.6 + my)} '
                   f'Q{_bn(mx)},{_bn(-27 + my)} {_bn(-3.6 + mx)},{_bn(-28.6 + my)} Z" fill="{c["tongue"]}"/>')
    elif mouth == 'o':
        out.append(f'<ellipse cx="{_bn(mx)}" cy="{_bn(-31 + my)}" rx="3.4" ry="4" fill="{mc}"/>')
    else:
        out.append(f'<path d="M{_bn(-7 + mx)},{_bn(-35 + my)} Q{_bn(mx)},{_bn(-28.5 + my)} {_bn(7 + mx)},{_bn(-35 + my)}" fill="none" '
                   f'stroke="{mc}" stroke-width="3" stroke-linecap="round"/>')
    return ''.join(out)


def _bot_head(c, eyes='open', look=(0, 0), mouth='smile', low=False):
    """Dome, strap, mask with face, snorkel and antenna. Neck joint at (0, -8)."""
    uid = c['uid']
    glass = f'url(#{uid}-deep)' if c['deep'] else f'url(#{uid}-glass)'
    out = [_bot_antenna(c, low),
           f'<path d="{_DOME}" fill="{c["shell"]}" {_bst(c)}/>',
           f'<path d="{_DOME_SHADE}" fill="{c["shade"]}"/>']
    if not low:
        out.append('<ellipse cx="-22" cy="-82" rx="11" ry="5.5" transform="rotate(-28 -22 -82)" fill="#ffffff"/>')
    out.append(f'<path d="{_DOME}" fill="none" {_bst(c)}/>')
    if low:
        out.append(_bunion(c, ['<ellipse cx="0" cy="-45" rx="39.5" ry="30"/>'], c['frame']))
        out.append(f'<ellipse cx="0" cy="-45" rx="32.5" ry="24" fill="{glass}"/>')
        out.append(_bot_face(c, low=True))
        if not c['tiny']:
            out.append('<path d="M-25,-56 C-21,-63 -15,-66 -9,-66" fill="none" stroke="#ffffff" stroke-opacity=".5" '
                       'stroke-width="4" stroke-linecap="round"/>')
        out.append(_bot_snorkel(c, low=True))
        return ''.join(out)
    # strap wrapping the dome, ear disc on the left
    out.append(f'<path d="M-46.4,-58 Q0,-51 46.4,-58 L47,-43 Q0,-36 -47,-43 Z" fill="{c["strap"]}" {_bst(c)}/>')
    out.append(f'<circle cx="-48" cy="-50" r="9" fill="{c["strap"]}" {_bst(c)}/>'
               f'<circle cx="-48" cy="-50" r="3.4" fill="{c["rivet"]}"/>')
    # dive mask: oval lens with a nose pocket
    out.append(_bunion(c, ['<ellipse cx="0" cy="-49" rx="40" ry="25"/>', '<ellipse cx="0" cy="-29" rx="15.5" ry="12.5"/>'],
                       c['frame']))
    out.append(f'<path d="M-31,-67 C-18,-75 18,-75 31,-67" fill="none" stroke="{c["frame_hi"]}" stroke-width="3.2" stroke-linecap="round"/>')
    if c['full']:
        out.append(f'<circle cx="-35.5" cy="-49" r="2.3" fill="{c["rivet"]}"/><circle cx="35.5" cy="-49" r="2.3" fill="{c["rivet"]}"/>')
    lens = (f'M-32.5,-49 C-32.5,-61 -18,-67.5 0,-67.5 C18,-67.5 32.5,-61 32.5,-49 C32.5,-39 24,-33.5 13,-32.5 '
            f'C11,-25 6,-21.5 0,-21.5 C-6,-21.5 -11,-25 -13,-32.5 C-24,-33.5 -32.5,-39 -32.5,-49 Z')
    out.append(f'<path d="{lens}" fill="{glass}" stroke="{c["line"]}" stroke-width="{_bn(c["lw"] * .7)}" stroke-linejoin="round"/>')
    out.append(_bot_face(c, eyes, look, mouth))
    glare_op = '.35' if c['deep'] else '.9'
    out.append(f'<path d="M-25,-57 C-22,-62 -15,-65 -8,-65.5" fill="none" stroke="#ffffff" stroke-opacity="{glare_op}" '
               f'stroke-width="3.6" stroke-linecap="round"/>')
    out.append(_bot_snorkel(c))
    return ''.join(out)


# --- body --------------------------------------------------------------------------------------------------------------
_TORSO = 'M-29,-3 L29,-3 C37,-3 41,3 42,11 L45,51 C46,61 39,68 29,68 L-29,68 C-39,68 -46,61 -45,51 L-42,11 C-41,3 -37,-3 -29,-3 Z'
_TORSO_SHADE = 'M22,-3 L29,-3 C37,-3 41,3 42,11 L45,51 C46,61 39,68 29,68 L23,68 C32,65 37,58 36,48 L34,12 C33,4 29,-1 22,-3 Z'


def _bot_body(c):
    out = (f'<rect x="-13" y="-12" width="26" height="14" rx="5" fill="{c["joint"]}" {_bst(c)}/>'
           f'<path d="{_TORSO}" fill="{c["shell"]}" {_bst(c)}/>'
           f'<path d="{_TORSO_SHADE}" fill="{c["shade"]}"/>'
           f'<path d="{_TORSO}" fill="none" {_bst(c)}/>'
           f'<rect x="-21" y="9" width="42" height="33" rx="9" fill="{c["panel"]}" {_bst(c)}/>')
    if c['full']:
        out += (f'<path d="M-13,28 q4.3,-6 8.6,0 t8.6,0 t8.6,0" fill="none" stroke="{c["panel_line"]}" stroke-width="3" stroke-linecap="round"/>'
                f'<circle cx="11" cy="17.5" r="3" fill="none" stroke="{c["panel_line"]}" stroke-width="2"/>'
                f'<circle cx="5.5" cy="15" r="1.7" fill="{c["panel_line"]}"/>')
    out += (f'<path d="M-45.4,50 L45.4,50 L45.6,58 C45.8,60 45.8,61 45.6,62 L-45.6,62 C-45.8,61 -45.8,60 -45.6,58 Z" '
            f'fill="{c["belt"]}" {_bst(c)}/>')
    if c['full']:
        out += f'<rect x="-6" y="48.5" width="12" height="15" rx="3" fill="{c["buckle"]}" {_bst(c)}/>'
    return out


def _bot_arm(c, side, a):
    """side +1 right / -1 left; a = degrees outward from hanging down (negative = across the body)."""
    tr = f'translate({_bn(40 * side)},10) scale({side},1) rotate({_bn(-a)})'
    return (f'<g transform="{tr}">'
            f'<rect x="-7.5" y="-6" width="15" height="36" rx="7.5" fill="{c["shell"]}" {_bst(c)}/>'
            f'<path d="M1.5,-4 C5,-3 7.5,-1 7.5,2 L7.5,26 C7.5,28 6,29.5 4,29.5 Z" fill="{c["shade"]}"/>'
            f'<rect x="-9" y="22" width="18" height="8" rx="3.5" fill="{c["strap"]}" {_bst(c)}/>'
            f'<ellipse cx="-9" cy="35" rx="5" ry="7" transform="rotate(-28 -9 35)" fill="{c["glove"]}" {_bst(c)}/>'
            f'<path d="M-10,33 C-10,44 -5,48 1,48 C8,48 11,43 11,36 C11,30 7,28 0,28 C-6,28 -10,29 -10,33 Z" fill="{c["glove"]}" {_bst(c)}/>'
            f'<path d="M5,31 C9,33 10,37 9,41" fill="none" stroke="{c["glove_sh"]}" stroke-width="2.6" stroke-linecap="round"/>'
            f'</g>')


def _bot_leg_pt(side, a, length, p):
    """Where the leg-local point p (fin frame) lands in the body frame, for a leg drawn by _bot_leg(side, a, length)."""
    m = _bmul(_bmul((1, 0, 0, 1, 19 * side, 64), (side, 0, 0, 1, 0, 0)), _brot(-a))
    return _bapply(m, (p[0], p[1] + length - 28.0))


def _bot_leg(c, side, a=0.0, fin='stand', length=28.0):
    tr = f'translate({_bn(19 * side)},64) scale({side},1) rotate({_bn(-a)})'
    dy = length - 28.0
    if fin == 'stand':   # flipper splayed outward, seen from the front
        fin_d = 'M-7,22 C2,19 18,20 34,27 C40,30 39,36 33,37 C18,39 2,38 -8,36 C-12,33 -12,25 -7,22 Z'
        ribs = 'M6,24 C12,27 17,31 20,36.5 M17,24.5 C23,27 27,31 29,36'
    else:                # kicking: the flipper continues the leg
        fin_d = 'M-9,18 L9,18 C13,30 17,42 18,52 C18,58 13,60 8,57 C4,61 -4,61 -8,57 C-13,60 -18,58 -18,52 C-17,42 -13,30 -9,18 Z'
        ribs = 'M-4,26 L-7,52 M4,26 L7,52'
    out = (f'<g transform="{tr}">'
           f'<rect x="-8" y="-4" width="16" height="{_bn(length)}" rx="7" fill="{c["shell"]}" {_bst(c)}/>'
           f'<path d="M2,-2 C6,-1 8,1 8,4 L8,{_bn(20 + dy)} C8,{_bn(22 + dy)} 6,{_bn(23 + dy)} 4,{_bn(23 + dy)} Z" fill="{c["shade"]}"/>'
           f'<g transform="translate(0,{_bn(dy)})"><path d="{fin_d}" fill="{c["fin"]}" {_bst(c)}/>')
    if c['full']:
        out += f'<path d="{ribs}" fill="none" stroke="{c["fin_rib"]}" stroke-width="2.6" stroke-linecap="round"/>'
    return out + '</g></g>'


_FISH_BODY = 'M-50,0 C-37,-29 19,-29 40,0 C19,29 -37,29 -50,0 Z'
_FISH_TAIL = 'M33,0 C43,-7 52,-15 62,-21 C57.5,-7 57.5,7 62,21 C52,15 43,7 33,0 Z'


def _bot_fish(c, x, y, s, flip=False):
    return (f'<g transform="translate({_bn(x)},{_bn(y)}) scale({"-" if flip else ""}{_bn(s)},{_bn(s)})" fill="{c["fish"]}">'
            f'<path d="{_FISH_TAIL}"/><path d="{_FISH_BODY}"/><circle cx="-31" cy="-5" r="6.5" fill="#ffffff"/></g>')


def _bot_book(c, cx, cy, tilt=0.0, scale=1.22):
    """The open field guide: reef-yellow cover, white pages, text lines on the left page, a coral fish on the right."""
    out = (f'<g transform="translate({_bn(cx)},{_bn(cy)}) rotate({_bn(tilt)}) scale({_bn(scale)})">'
           f'<path d="M-34,-15 L0,-11 L34,-15 L34,18 L0,22 L-34,18 Z" fill="{c["cover"]}" {_bst(c, 1 / scale)}/>'
           f'<path d="M-29,-17 C-18,-19 -7,-17 0,-13 L0,17 C-7,13 -18,12 -29,14 Z" fill="{c["page"]}" {_bst(c, 1 / scale)}/>'
           f'<path d="M29,-17 C18,-19 7,-17 0,-13 L0,17 C7,13 18,12 29,14 Z" fill="{c["page_sh"]}" {_bst(c, 1 / scale)}/>'
           f'<path d="M-24,-9 L-6,-7.5 M-24,-2 L-6,-0.5 M-24,5 L-11,6" stroke="{c["ink"]}" stroke-width="2.4" stroke-linecap="round"/>'
           + _bot_fish(c, 14.5, -1.5, 0.17, flip=True) +
           f'<path d="M7,10 L23,8.5" stroke="{c["ink"]}" stroke-width="2.4" stroke-linecap="round"/></g>')
    return out


def _bot_book_closed(c, cx, cy, rot=0.0):
    """The guide closed and tucked under an arm: yellow cover with a coral fish, visible white page edges and a spine."""
    return (f'<g transform="translate({_bn(cx)},{_bn(cy)}) rotate({_bn(rot)})">'
            f'<rect x="-19" y="-15" width="42" height="31" rx="3.5" fill="{c["page"]}" {_bst(c)}/>'
            f'<path d="M21,-10 L21,11 M17.5,-11 L17.5,12" stroke="{c["ink"]}" stroke-width="1.6"/>'
            f'<rect x="-22" y="-17" width="38" height="33" rx="4" fill="{c["cover"]}" {_bst(c)}/>'
            f'<rect x="-22" y="-17" width="8" height="33" rx="3.5" fill="{c["cover_dk"]}" {_bst(c)}/>'
            + _bot_fish(c, 2.5, -0.5, 0.17, flip=True) + '</g>')


def _bot_bubbles(c, pts):
    kw = _BOT_BUBBLES[1 if c['dark'] else 0]
    pal = DARK if c['dark'] else PALETTE
    return ''.join(bubble(x, y, r, pal=pal, **kw) for x, y, r in pts)


def _bot_defs(c):
    u = c['uid']
    return (f'<defs><linearGradient id="{u}-glass" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{c["glass_top"]}"/><stop offset="1" stop-color="{c["glass_bot"]}"/></linearGradient>'
            f'<linearGradient id="{u}-deep" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset=".15" stop-color="{c["deep_top"]}"/><stop offset="1" stop-color="{c["deep_bot"]}"/></linearGradient>'
            f'<radialGradient id="{u}-glow"><stop offset="0" stop-color="{c["glow"]}" stop-opacity="{".8" if c["dark"] else ".6"}"/>'
            f'<stop offset=".45" stop-color="{c["glow"]}" stop-opacity="{".3" if c["dark"] else ".2"}"/>'
            f'<stop offset="1" stop-color="{c["glow"]}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="{u}-eyeglow"><stop offset="0" stop-color="{c["eye_glow"]}" stop-opacity=".7"/>'
            f'<stop offset="1" stop-color="{c["eye_glow"]}" stop-opacity="0"/></radialGradient>'
            f'<clipPath id="{u}-peek"><rect x="-200" y="-300" width="400" height="300"/></clipPath></defs>')


# --- poses -------------------------------------------------------------------------------------------------------------
def _bot_figure(c, pose):
    """The pose in design units (standing: neck at (0,-8), feet at about y 103)."""
    if pose == 'head':
        return _bot_head(c)
    if pose in ('head-low', 'head-tiny'):
        return _bot_head(c, low=True)
    if pose == 'wave':
        motion = ''
        if c['full']:
            motion = (f'<path d="M62,-104 C70,-112 74,-120 74,-130 M90,-94 C98,-100 102,-108 102,-116" fill="none" '
                      f'stroke="{c["motion"]}" stroke-width="3.4" stroke-linecap="round"/>')
        return (_bot_leg(c, -1) + _bot_leg(c, 1) + _bot_arm(c, -1, 14) + _bot_body(c) +
                f'<g transform="rotate(-6 0 -8)">{_bot_head(c, eyes="happy", mouth="open")}</g>' +
                _bot_arm(c, 1, 152) + motion)
    if pose == 'read':      # sitting, legs out, the open guide on the lap
        return (_bot_leg(c, -1, 66, fin='kick', length=20) + _bot_leg(c, 1, 66, fin='kick', length=20) + _bot_body(c) +
                f'<g transform="rotate(5 0 -8)">{_bot_head(c, look=(2, 4), mouth="smile")}</g>' +
                _bot_book(c, 0, 33, -3) + _bot_arm(c, -1, -14) + _bot_arm(c, 1, -12))
    if pose == 'point':
        spark = _bot_bubbles(c, ((106, -6, 5.5), (119, -19, 3.6), (117, 6, 2.6))) if c['full'] else ''
        return (_bot_leg(c, -1, 2) + _bot_leg(c, 1) + _bot_arm(c, -1, 18) + _bot_body(c) +
                f'<g transform="rotate(7 0 -8)">{_bot_head(c, look=(4, -1), mouth="open")}</g>' +
                _bot_arm(c, 1, 92) + spark)
    if pose == 'peek':
        hands = ''
        for side in (-1, 1):
            hands += (f'<g transform="translate({41 * side},0) scale({side},1)">'
                      f'<path d="M-11,2 C-11,-8 -6,-12 0,-12 C7,-12 12,-8 12,1 Z" fill="{c["glove"]}" {_bst(c)}/>'
                      f'<path d="M-4,-11 L-4,-2 M3,-11.5 L3,-2" stroke="{c["glove_sh"]}" stroke-width="2.2" stroke-linecap="round"/>'
                      f'</g>')
        head = f'<g transform="translate(0,26) rotate(-8 0 -8)">{_bot_head(c, look=(-3, -2), mouth="o")}</g>'
        return f'<g clip-path="url(#{c["uid"]}-peek)">{head}</g>' + hands
    if pose == 'swim':      # nose-down dive to the right; the head is mirrored so the snorkel points up and back
        body_rot, head_rot = 112, -58
        m_body = _brot(body_rot, 0, 30)
        m_head = _bmul(_bmul(m_body, _brot(head_rot, 0, -8)), (-1, 0, 0, 1, 0, 0))
        inner = (_bot_leg(c, -1, 16, fin='kick') + _bot_leg(c, 1, 24, fin='kick', length=19) + _bot_body(c) +
                 _bot_book_closed(c, -6, 34, 96) + _bot_arm(c, -1, -38) + _bot_arm(c, 1, 196) +
                 f'<g transform="rotate({head_rot} 0 -8) scale(-1,1)">{_bot_head(c, look=(-3, -1), mouth="smile")}</g>')
        out = f'<g transform="rotate({body_rot} 0 30)">{inner}</g>'
        if c['full']:
            tx, ty = _bapply(m_head, (47, -110))
            trail = ((tx - 3, ty - 14, 4.6), (tx + 6, ty - 31, 6.4), (tx - 2, ty - 50, 3.8), (tx + 8, ty - 64, 5))
            fa = _bapply(m_body, _bot_leg_pt(-1, 16, 28, (0, 60)))
            fb = _bapply(m_body, _bot_leg_pt(1, 24, 19, (0, 60)))
            kick = ((fa[0] - 12, fa[1] - 8, 4.2), (fa[0] - 25, fa[1] - 18, 2.8), (fb[0] - 14, fb[1] + 3, 3.2))
            out += _bot_bubbles(c, trail + kick)
        return out
    raise ValueError(f'unknown diver_bot pose {pose!r}')


def _bot_key(pose, px):
    if pose not in BOT_POSES:
        raise ValueError(f'diver_bot pose must be one of {BOT_POSES}, not {pose!r}')
    if pose == 'head' and px <= 36:
        return 'head-tiny' if px < 20 else 'head-low'
    return pose


def diver_bot_box(pose, size, px=None):
    """(width, height) in user units of the pose's box when drawn with diver_bot(..., size). px: rendered px of `size`."""
    _, _, w, h = _BOT_BOX[_bot_key(pose, size if px is None else px)]
    s = size / max(w, h)
    return (w * s, h * s)


def diver_bot(pose, x, y, size, uid, dark=False, flip=False, unit_px=1.0, lod=None, blink=False):
    """Diver bot: the Deep Dive mascot, an ORIGINAL friendly robot snorkel diver drawn from numbers (never traced or copied).

    Anatomy (design units; the standing figure is about 250 units tall, neck joint at (0, -8)):
        head    a pearl-white rounded DOME (wider than tall at the base, no corners) with one straight antenna stalk and ONE
                glowing yellow bulb; an indigo mask STRAP wraps the dome, ending in an ear disc on the left and a clip on the right.
        mask    one oval dive mask with a NOSE POCKET at the bottom (that pocket is what makes it a diver, not an astronaut): a blue
                frame, two single-colour rivets at cover size, and the face behind the glass. Light glass (pale blue, dark eyes) on
                light backgrounds; deep glass (#0b1b3d -> #2152c4, white eyes and smile) in night water and in the small head icon.
        snorkel a coral tube running up the right side of the dome, held by the strap clip, its mouthpiece plugged into the
                mask's lower rim; two white bands at full detail.
        body    a pearl-white rounded torso with a blue chest panel (a little wave and two bubbles), an indigo belt with a yellow
                buckle, pearl arms with indigo cuffs and blue mitten gloves, short legs and CORAL fins.
        guide   the field guide is always a BOOK (open, or closed with visible page edges) with a reef-yellow cover and a small
                coral fish on it: the one warm focal point; warm areas stay small, the bot is mostly white and blue.

    Guardrails (an independent guide must never look like the event's official mascot; keep them when you edit):
        - fins always coral, never yellow;  - the guide always a book with a fish, never a flat tablet slab;
        - nothing spiky or crest-like on the dome, no hair;  - the head is a dome with an oval mask: never a rectangular head,
          never a horizontal slot visor;  - the body is pearl white, never grey;  - the antenna is one straight stalk with one bulb;
        - no rows of chest dots, no ring of dots, never more than one dot colour, no speech-bubble frame, no hats;
        - only Deep Dive palette colours; none of #4285f4 #ea4335 #fbbc05 #34a853 (BOT_FORBIDDEN_HEX) anywhere.

    API
        diver_bot(pose, x, y, size, uid, dark=False, flip=False, unit_px=1.0, lod=None) -> SVG fragment (a <g> with its own <defs>)
            The pose's bounding box is centred on (x, y) and its LARGER side is `size` user units (diver_bot_box gives the box).
            unit_px = CSS px per user unit, so the bot can pick its detail and line weight: 1 on the site and brand images,
            0.378 in the PDF underlays (0.1 mm units). lod 'full' or 'simple' overrides the automatic level of detail
            (simple below 120 px: no chest wave, cheeks, buckle, rivets or bubbles, and a heavier line).
            dark=True is the night-water variant (deep glass with softly glowing eyes, haloed bulb, lighter outline).
            flip=True mirrors it (swim heading left, point to the left). uid prefixes every id: use a new uid for each copy.
            blink (screens only, default off) adds a short blink: the eyes squash for about 120 ms once every `blink`
            seconds (True means 5), by CSS keyframes inside the fragment (class and keyframe names carry the uid; still
            under prefers-reduced-motion: reduce). Off, the output is exactly the still bot.
        diver_bot_svg(pose, size_css, uid, dark=False, flip=False, cls='bot', label=None, px=None, square=False, blink=False) -> <svg>
            size_css is the HEIGHT: a number means mm (as for the other icons), or a CSS length such as '32px' or '18mm'.
            Pass px when size_css is relative ('2em') so the bot knows its rendered size. label adds role="img" + aria-label.
            square=True pads the box to a square (favicons, avatars).
        diver_bot_box(pose, size, px=None) -> (width, height) of the pose's box for that size.
        BOT_POSES = ('swim', 'wave', 'read', 'point', 'peek', 'head')

    Poses
        swim   diving forward, head to the right and 22 degrees nose-down, kicking (one fin up, one down), leading glove forward,
               the closed guide tucked under the other arm, a bubble trail from the snorkel and kick bubbles behind the fins.
        wave   standing, waving with a happy face and motion arcs. The bottom of the box is the floor line.
        read   SITTING with the open guide, looking down into it. The bottom of the box is the seat line (put it on the seabed).
        point  standing, pointing right (flip=True: left) with a few bubbles at the glove. The bottom of the box is the floor.
        peek   head and two gloves peeking over an edge; the bottom of the box IS the edge (draw the card edge there).
        head   the head alone for avatars, favicons and README icons. At 36 px and below it switches to the high-contrast icon
               (deep glass, big white eyes, white smile, chunky coral snorkel stub); below 20 px the antenna is dropped too.

    """
    px = size * unit_px
    key = _bot_key(pose, px)
    if lod not in (None, 'full', 'simple'):
        raise ValueError(f"lod must be 'full', 'simple' or None, not {lod!r}")
    lod = lod or ('simple' if px < 120 else 'full')
    bx, by, bw, bh = _BOT_BOX[key]
    s = size / max(bw, bh)
    if key in ('head-low', 'head-tiny'):
        stroke_px = min(max(px * 0.05, 0.8), 1.4)
    elif lod == 'simple':
        stroke_px = min(max(px * 0.016, 1.2), 2.2)
    else:
        stroke_px = min(max(px * 0.0105, 1.1), 3.0)
    c = dict(_BOT_DARK if dark else _BOT_LIGHT, uid=uid, dark=dark, full=(lod == 'full' and key == pose),
             tiny=(key == 'head-tiny'), deep=(dark or key != pose),
             lw=stroke_px / (s * unit_px), blink=(5.0 if blink is True else float(blink or 0)))
    sx = -s if flip else s
    return (f'<g class="diverbot diverbot-{pose}" transform="translate({_bn(x)},{_bn(y)}) scale({fmt(sx, 4)},{fmt(s, 4)}) '
            f'translate({_bn(-bx)},{_bn(-by)})">' + _bot_defs(c) + (_bot_blink_css(c) if c['blink'] else '')
            + _bot_figure(c, key) + '</g>')


def _css_px(size_css):
    if isinstance(size_css, (int, float)):
        return size_css * 96 / 25.4, f'{fmt(size_css, 2)}mm'
    s = str(size_css).strip()
    for unit, k in (('px', 1.0), ('mm', 96 / 25.4), ('cm', 96 / 2.54), ('pt', 96 / 72), ('in', 96.0)):
        if s.endswith(unit):
            try:
                return float(s[:-len(unit)]) * k, s
            except ValueError:
                break
    return None, s


def diver_bot_svg(pose, size_css, uid, dark=False, flip=False, cls='bot', label=None, px=None, square=False, blink=False):
    """Complete <svg> of the diver bot, `size_css` high (number = mm, or a CSS length); width follows the pose's box.
    square=True centres the pose in a square box (favicons, avatars): size_css is then both width and height.
    blink: see diver_bot (default off)."""
    hpx, css = _css_px(size_css)
    hpx = px or hpx or 48.0
    key = _bot_key(pose, hpx)                      # first guess; the head switches by its rendered size
    _, _, w, h = _BOT_BOX[key]
    key = _bot_key(pose, max(w, h) * hpx / (max(w, h) if square else h))
    _, _, w, h = _BOT_BOX[key]
    side = max(w, h)
    if square:
        w = h = side
    unit_px = hpx / h
    m = re.match(r'^([0-9.]+)([a-z%]*)$', css)
    width = f'{fmt(float(m.group(1)) * w / h, 2)}{m.group(2)}' if m else None
    a = f' role="img" aria-label="{label}"' if label else ' aria-hidden="true"'
    style = f'height:{css}' + (f';width:{width}' if width else '')
    return (f'<svg viewBox="0 0 {_bn(w)} {_bn(h)}" xmlns="http://www.w3.org/2000/svg" class="{cls}" style="{style}" '
            f'focusable="false"{a}>' + diver_bot(pose, w / 2, h / 2, side, uid, dark, flip, unit_px, blink=blink) + '</svg>')
