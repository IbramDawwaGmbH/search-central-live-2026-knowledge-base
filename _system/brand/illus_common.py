"""Shared composition grammar for the README header illustrations (see make_illustrations.py).

Every illustration is one 880 x 240 card (rounded corners, its own background) so it reads on GitHub's light and dark pages.
The illustrator modules (illus_a.py ... illus_d.py) build each scene with a Scene from this module, so all 31 cards share:

    canvas      W x H = 880 x 240 user units, card corner RX = 18, a 1.5-unit frame in the palette's frame colour
    water       vertical gradient (light: white -> pale periwinkle; dark: night navy), one soft sun glow, light rays fanning
                from the surface, and a slim two-layer water surface along the top edge (SURFACE = 16 units deep)
    seabed      three low hills: far (horizon line HORIZON ~ 178) with small monochrome coral/fern/fan silhouettes, mid (~196),
                near (~214) with sand dots. Things stand on the near hill: their base line is FLOOR (224) and they get a soft
                contact shadow (Scene.shadow). bed.floor(x) gives the near hill's top at x if a prop must sit exactly on it.
    bot         the Diver bot (ocean_art.diver_bot) at about 45 % of the card height: BOT_H = 108 units for a standing pose,
                placed by its feet with Scene.bot(pose, cx, ...). Usually left of centre; the subject props sit centre-right.
    margins     SAFE = 28 units on every side for anything that matters; only reef dressing (seaweed, coral, fish) may cross it.

Layers (paint order) of Scene.render():
    background, glow, rays  ->  sc.under (things behind the seabed: distant fish, a lighthouse rising behind the hills)
    ->  far hill + decor, mid hill + decor, near hill + dots  ->  sc.body (the subject, the bot, props)
    ->  sc.over (foreground reef dressing at the edges)  ->  water surface  ->  frame

Ids: every id in a card must start with '<slug>-'. Scene.id(name) makes one; prefix_ids() rewrites a fragment that uses bare ids.
No text, no scripts, no external references, no randomness without a fixed seed: same arguments, same bytes.
"""
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # _system/, for ocean_art
import ocean_art as oa                                          # noqa: E402

fmt, mix, catmull = oa.fmt, oa.mix, oa.catmull

W, H, RX = 880, 240, 18
SURFACE = 18          # depth of the water surface band at the top
HORIZON = 178         # far hill line
FLOOR = 224           # base line of things standing on the near hill
BOT_H = 108           # standing Diver bot height (45 % of H)
SAFE = 28             # margin for anything that matters


# ------------------------------------------------------------------------------------------------------------ palette
_EXTRA_LIGHT = {
    # water
    'water': ('#ffffff', '#f1f6fe', '#e2edfb', '#d3e2f8', '#c7d9f5'),
    'glow': '#ffffff', 'ray': '#ffffff', 'ray_op': 0.55,
    # outline shared with the Diver bot, so props sit in the same drawing style
    'line': '#2e3870', 'lw': 1.6,
    # prop materials
    'wood': '#c98a52', 'wood_dk': '#a2683a', 'wood_hi': '#dfa874',
    'gold': '#f7c443', 'gold_dk': '#e3a82c', 'gold_hi': '#fde59a',
    'pearl': '#f7faff', 'pearl_sh': '#d9e4f6', 'pearl_hi': '#ffffff',
    'paper': '#ffffff', 'paper_sh': '#e6eefc', 'paper_line': '#9fbbec',
    'metal': '#a9b8dc', 'metal_dk': '#7d8fc2', 'metal_hi': '#dfe7f7',
    'glass': '#eaf3ff', 'glass_dk': '#bcd6f8',
    'shadow': '#3b4a9a', 'shadow_op': 0.16,
    'violet': '#6a45cf', 'violet_lt': '#b9a6f0',
}
_EXTRA_DARK = {
    'water': ('#16336f', '#112a5e', '#0d214d', '#0a1a3e', '#08142e'),
    'glow': '#9cc0ff', 'ray': '#9cc0ff', 'ray_op': 0.22,
    'line': '#3a4a96', 'lw': 1.6,
    'wood': '#b97c48', 'wood_dk': '#8f5c34', 'wood_hi': '#d39a66',
    'gold': '#ffd055', 'gold_dk': '#eab23a', 'gold_hi': '#ffe9a6',
    'pearl': '#f3f7ff', 'pearl_sh': '#c9d7f1', 'pearl_hi': '#ffffff',
    'paper': '#f3f7ff', 'paper_sh': '#cfdcf3', 'paper_line': '#7f9fdc',
    'metal': '#8ea2d4', 'metal_dk': '#6276b4', 'metal_hi': '#c6d4f2',
    'glass': '#cfe0ff', 'glass_dk': '#8fb0ea',
    'shadow': '#02081a', 'shadow_op': 0.35,
    'violet': '#9b7cf0', 'violet_lt': '#cbb8ff',
}


def tokens(dark=False):
    """All colours a scene may use: ocean_art's PALETTE / DARK plus the prop materials above (same keys in both)."""
    p = dict(oa.DARK if dark else oa.PALETTE)
    p.update(_EXTRA_DARK if dark else _EXTRA_LIGHT)
    p['dark'] = dark
    return p


def stroke(p, k=1.0):
    """The soft outline every prop uses (the Diver bot's line colour and weight)."""
    return f'stroke="{p["line"]}" stroke-width="{fmt(p["lw"] * k, 2)}" stroke-linejoin="round" stroke-linecap="round"'


def wave_path(y0, amp, wl, shift=0.0, x0=None, x1=None):
    """A compact sine-like wave line from x0 to x1 (default: past both card edges) around y0: one quadratic curve per half
    wavelength (Q then T), so a full-width wave costs a few hundred bytes. Path data only, starting with M."""
    x0 = -wl + shift % wl if x0 is None else x0
    x1 = W + wl if x1 is None else x1
    d = [f'M{fmt(x0)},{fmt(y0)} Q{fmt(x0 + wl / 4)},{fmt(y0 - 2 * amp)} {fmt(x0 + wl / 2)},{fmt(y0)}']
    x = x0 + wl / 2
    while x < x1:
        x += wl / 2
        d.append(f'T{fmt(x)},{fmt(y0)}')
    return ' '.join(d)


# ------------------------------------------------------------------------------------------------------------ ids
_ID = re.compile(r'\bid="([^"]+)"')


def prefix_ids(svg, prefix):
    """Prefix every id defined in the fragment, and every url(#id) / href="#id" that points at one of them."""
    ids = set(_ID.findall(svg))
    if not ids:
        return svg

    def sub_ref(m):
        return m.group(1) + (f'{prefix}-{m.group(2)}' if m.group(2) in ids else m.group(2)) + m.group(3)
    svg = _ID.sub(lambda m: f'id="{prefix}-{m.group(1)}"', svg)
    svg = re.sub(r'(url\(#)([^)]+)(\))', sub_ref, svg)
    return re.sub(r'(href="#)([^"]+)(")', sub_ref, svg)


# ------------------------------------------------------------------------------------------------------------ seabed
class Bed:
    """The three seabed hills of a card. far / mid / floor(x) give each hill's top line at x."""

    def __init__(self, p, seed, avoid=(), decor=True):
        rnd = oa._rng(f'illus-bed:{seed}')
        self.far_pts, self.far = oa._ridge(rnd, W, HORIZON, 4.5, 560)
        self.mid_pts, self.mid = oa._ridge(rnd, W, 196, 4.5, 470)
        self.near_pts, self.floor = oa._ridge(rnd, W, 214, 3.0, 400)
        out = []

        def hill(pts, color):
            return f'<path d="{catmull(pts)} L{W + 40},{H + 10} L-40,{H + 10} Z" fill="{color}"/>'

        if decor:   # small monochrome silhouettes on the far hill
            for x in oa._slots(rnd, 40, W - 40, 185, avoid):
                kind = rnd.choice(('fan', 'fern', 'coral', 'fan'))
                base = self.far(x) + 4
                if kind == 'fan':
                    out.append(oa.fan_coral(x, base, rnd.uniform(17, 24), p['far_dk'], n=7, width=1.6))
                elif kind == 'fern':
                    out.append(oa.fern(x, base, rnd.uniform(20, 27), p['far_dk'], leaves=5, lean=rnd.uniform(-.2, .2), size=.24))
                else:
                    out.append(oa.branch_coral(x, base, .12, p['far_dk'], width=2.2, flip=rnd.random() < .5))
        out.append(hill(self.far_pts, p['far']))
        if decor:
            for x in oa._slots(rnd, 60, W - 60, 240, avoid):
                kind = rnd.choice(('fern', 'fan', 'coral'))
                base = self.mid(x) + 4
                if kind == 'fern':
                    out.append(oa.fern(x, base, rnd.uniform(26, 34), p['mid_dk'], leaves=6, lean=rnd.uniform(-.2, .15), size=.3))
                elif kind == 'fan':
                    out.append(oa.fan_coral(x, base, rnd.uniform(24, 30), p['mid_dk'], n=9, width=1.8))
                else:
                    out.append(oa.branch_coral(x, base, .15, p['mid_dk'], width=2.6, flip=rnd.random() < .5))
        out.append(hill(self.mid_pts, p['mid']))
        out.append(oa.dots(0, W, lambda x: self.mid(x) + 5, 14, 24, p['dot_mid'], 0.9, 2.0, seed=f'{seed}-m'))
        out.append(hill(self.near_pts, p['near']))
        out.append(oa.dots(0, W, lambda x: self.floor(x) + 5, 20, 28, p['dot_near'], 0.9, 2.2, seed=f'{seed}-n'))
        self.svg = ''.join(out)


# ------------------------------------------------------------------------------------------------------------ scene
class Scene:
    """One card. Append SVG fragments to sc.under / sc.body / sc.over and defs to sc.defs, then return sc.render().

        sc = Scene('20-claims', dark, seed=20, avoid=[(420, 640)])
        sc.body.append(sc.shadow(520, FLOOR, 70))
        sc.body.append(sc.bot('point', 300, FLOOR))
        return sc.render()

    seed    picks the seabed hills and decor (keep it fixed per slug);  avoid  x ranges kept free of seabed decor;
    rays    number of light rays (0 = none);  glow  (x, y, r) of the soft sun glow, or None;  surface  draw the top waves.
    """

    def __init__(self, slug, dark=False, seed=0, avoid=(), rays=6, glow=(600, -40, 360), surface=True, decor=True):
        self.slug, self.dark, self.seed = slug, dark, seed
        self.p = tokens(dark)
        self.defs, self.under, self.body, self.over = [], [], [], []
        self.bed = Bed(self.p, f'{slug}:{seed}', avoid, decor)
        self._rays, self._glow, self._surface = rays, glow, surface
        self._n = 0

    # helpers --------------------------------------------------------------------------------------------------------
    def id(self, name):
        """A document-unique id for this card: '<slug>-<name>'."""
        return f'{self.slug}-{name}'

    def uid(self, name='u'):
        """A fresh id prefix (for ocean_art functions that take a uid, like diver_bot)."""
        self._n += 1
        return f'{self.slug}-{name}{self._n}'

    def bot(self, pose, cx, base=FLOOR, height=BOT_H, flip=False, lod='full'):
        """The Diver bot with its box bottom on `base` (feet, seat line or edge) and its box `height` units tall, centred on cx.
        For 'swim' and 'head', base is simply the bottom of the box. Returns the fragment."""
        bw, bh = oa.diver_bot_box(pose, 100.0)
        size = height * max(bw, bh) / bh
        return oa.diver_bot(pose, cx, base - height / 2, size, self.uid('bot'), dark=self.dark, flip=flip, lod=lod)

    def shadow(self, cx, y, rx, ry=None, op=1.0):
        """Soft contact shadow under something standing on the seabed."""
        ry = ry or max(2.5, rx * 0.13)
        p = self.p
        out = ''
        for k, o in ((1.0, .35), (.72, .55), (.45, .8)):
            out += (f'<ellipse cx="{fmt(cx)}" cy="{fmt(y)}" rx="{fmt(rx * k)}" ry="{fmt(ry * k)}" fill="{p["shadow"]}" '
                    f'fill-opacity="{fmt(p["shadow_op"] * o * op, 2)}"/>')
        return out

    def radial(self, name, color, op=1.0, mid=0.4):
        """A radial gradient fading `color` to transparent (for glows); returns its url()."""
        gid = self.id(name)
        self.defs.append(f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{fmt(op, 2)}"/>'
                         f'<stop offset=".5" stop-color="{color}" stop-opacity="{fmt(op * mid, 2)}"/>'
                         f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')
        return f'url(#{gid})'

    def linear(self, name, stops, x2=0, y2=1):
        """A linear gradient (top to bottom by default) from [(offset, colour), ...]; returns its url()."""
        gid = self.id(name)
        s = ''.join(f'<stop offset="{fmt(o, 2)}" stop-color="{c}"/>' for o, c in stops)
        self.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">{s}</linearGradient>')
        return f'url(#{gid})'

    def fish(self, x, y, length, color='red', flip=False):
        return oa.fish(x, y, length, color, flip=flip, pal=self.p)

    def school(self, x, y, length, color='blue', n=5, flip=False, seed=0, spread=1.0):
        return oa.fish_school(x, y, length, color, n=n, flip=flip, seed=f'{self.slug}:{seed}', spread=spread, pal=self.p)

    def far_school(self, x, y, length, n=5, flip=False, seed=0):
        """A faint monochrome school in the distance (print-layer style)."""
        col = self.p['far_dk'] if not self.dark else self.p['mid_dk']
        return oa.fish_school(x, y, length, col, n=n, flip=flip, seed=f'{self.slug}:far{seed}', mono=True)

    def bubbles(self, x, y, height, r, n=4, seed=0):
        kw = dict(stroke='#9cc0ff', fill='#cfe0ff', fill_op=0.18) if self.dark else {}
        return oa.bubble_trail(x, y, height, r, n=n, seed=f'{self.slug}:{seed}', pal=self.p, **kw)

    def bubble(self, x, y, r):
        kw = dict(stroke='#9cc0ff', fill='#cfe0ff', fill_op=0.18) if self.dark else {}
        return oa.bubble(x, y, r, pal=self.p, **kw)

    def seaweed(self, x, height, color=None, width=5, phase=0.0, lean=0.0, base=H + 6):
        return oa.seaweed(x, base, height, color or self.p['weed'], width=width, amp=7, wl=70, phase=phase, lean=lean)

    def coral(self, x, scale, color=None, flip=False, base=H + 4):
        return oa.branch_coral(x, base, scale, color or self.p['coral'], width=max(2.5, 30 * scale), flip=flip)

    def anemone(self, x, r, base=None):
        return oa.anemone(x, base if base is not None else self.bed.floor(x) + 8, r, pal=self.p)

    # output ---------------------------------------------------------------------------------------------------------
    def _background(self):
        p, out = self.p, []
        stops = p['water']
        bg = self.linear('bg', [(i / (len(stops) - 1), c) for i, c in enumerate(stops)])
        out.append(f'<rect width="{W}" height="{H}" fill="{bg}"/>')
        if self._glow:
            gx, gy, gr = self._glow
            g = self.radial('glow', p['glow'], .9 if not self.dark else .28, .35)
            out.append(f'<ellipse cx="{fmt(gx)}" cy="{fmt(gy)}" rx="{fmt(gr)}" ry="{fmt(gr * .55)}" fill="{g}"/>')
        if self._rays:
            defs, rays = oa._rays(W, H, self.id('rays'), f'{self.slug}:{self.seed}', self._rays, p['ray_op'], p['ray'],
                                  top=SURFACE * .5, reach=.92)
            self.defs.append(defs)
            out.append(rays)
        return ''.join(out)

    def _surface_svg(self):
        if not self._surface:
            return ''
        p, wl = self.p, 74.0
        return (f'<path d="{wave_path(SURFACE * .62, 1.8, wl, 30)} L{W + wl},-1 L{-wl},-1 Z" fill="{p["wave_back"]}"/>'
                f'<path d="{wave_path(SURFACE * .42, 1.8, wl, 0)} L{W + wl},-1 L{-wl},-1 Z" fill="{p["wave_front"]}"/>'
                f'<path d="{wave_path(SURFACE * .22, .8, wl, 0)}" stroke="#ffffff" stroke-opacity=".24" stroke-width=".9" '
                f'stroke-linecap="round" stroke-dasharray="{fmt(wl * .3)} {fmt(wl * .7)}"/>')

    def render(self):
        p = self.p
        back = self._background()            # registers its defs first
        clip = self.id('card')
        frame = (f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{RX - .75}" fill="none" '
                 f'stroke="{p["frame"]}" stroke-width="1.5"/>')
        body = (back + ''.join(self.under) + self.bed.svg + ''.join(self.body) + ''.join(self.over) + self._surface_svg())
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
               f'<defs><clipPath id="{clip}"><rect width="{W}" height="{H}" rx="{RX}"/></clipPath>{"".join(self.defs)}</defs>'
               f'<g clip-path="url(#{clip})">{body}</g>{frame}</svg>')
        svg = re.sub(r' class="[^"]*"', '', svg)        # ocean_art's CSS hooks mean nothing inside an <img>
        return svg + '\n'


def placeholder(slug):
    """A scene function for a README whose illustration is not drawn yet: the empty card, flagged as a placeholder."""
    def scene(dark=False):
        return Scene(slug, dark, seed=1).render()
    scene.placeholder = True
    return scene
