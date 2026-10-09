"""README illustrations, group D: the outputs and the system: outputs, media kit, developer kit, field guides, the system, brand, eval, PDF builder.

Build every scene with illus_common.Scene; see illus_a.scene_claims (20-claims) for the reference scene.
"""
import math

from illus_common import oa
from illus_common import (FLOOR, H, W, Scene, fmt, mix, placeholder, stroke)   # noqa: F401

INK = oa.PALETTE          # the saturated light inks (labels, quiz chips, paint), used in both waters


# ------------------------------------------------------------------------------------------------------------ small helpers
def _d(pts, close=True):
    """Polyline path data from [(x, y), ...]."""
    return 'M' + ' L'.join(f'{fmt(x)},{fmt(y)}' for x, y in pts) + (' Z' if close else '')


def _sparkle(x, y, r, color, op=1.0):
    """A soft four-point glint (same shape as the reference scene's)."""
    k = r * 0.28
    d = (f'M{fmt(x)},{fmt(y - r)} Q{fmt(x + k)},{fmt(y - k)} {fmt(x + r)},{fmt(y)} Q{fmt(x + k)},{fmt(y + k)} {fmt(x)},{fmt(y + r)} '
         f'Q{fmt(x - k)},{fmt(y + k)} {fmt(x - r)},{fmt(y)} Q{fmt(x - k)},{fmt(y - k)} {fmt(x)},{fmt(y - r)} Z')
    return f'<path d="{d}" fill="{color}" fill-opacity="{fmt(op, 2)}"/>'


def _stone(p):
    """Rock colours that read on both seabeds: (fill, shade, highlight)."""
    s = mix(p['metal'], p['mid_dk'], .45)
    return s, mix(s, p['line'], .28), mix(s, '#ffffff', .35)


def _rock(p, x0, x1, top, base=FLOOR + 2):
    """A flat-topped rock (seat, desk or ledge) from x0 to x1, top edge at `top`."""
    s, sh, hi = _stone(p)
    w = x1 - x0
    d = (f'M{fmt(x0 + 2)},{fmt(base)} C{fmt(x0 - 3)},{fmt(top + 12)} {fmt(x0 + 6)},{fmt(top)} {fmt(x0 + w * .3)},{fmt(top)} '
         f'L{fmt(x1 - w * .28)},{fmt(top + 1)} C{fmt(x1 - 4)},{fmt(top + 1)} {fmt(x1 + 3)},{fmt(top + 12)} {fmt(x1 - 1)},{fmt(base)} Z')
    shade = (f'M{fmt(x1 - w * .22)},{fmt(top + 1)} C{fmt(x1 - 4)},{fmt(top + 1)} {fmt(x1 + 3)},{fmt(top + 12)} {fmt(x1 - 1)},{fmt(base)} '
             f'L{fmt(x1 - w * .2)},{fmt(base)} C{fmt(x1 - w * .12)},{fmt(top + 14)} {fmt(x1 - w * .14)},{fmt(top + 5)} {fmt(x1 - w * .22)},{fmt(top + 1)} Z')
    return (f'<path d="{d}" fill="{s}"/><path d="{shade}" fill="{sh}"/>'
            f'<path d="M{fmt(x0 + 8)},{fmt(top + 4)} L{fmt(x0 + w * .42)},{fmt(top + 4)}" stroke="{hi}" stroke-width="2" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" {stroke(p)}/>')


def _check(x, y, r):
    """A green check chip (the quiz chips' green)."""
    return (f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{INK["quiz_green"]}"/>'
            f'<path d="M{fmt(x - r * .45)},{fmt(y + r * .02)} L{fmt(x - r * .12)},{fmt(y + r * .36)} L{fmt(x + r * .48)},{fmt(y - r * .3)}" '
            f'fill="none" stroke="#ffffff" stroke-width="{fmt(r * .32)}" stroke-linecap="round" stroke-linejoin="round"/>')


def _question(x, y, r):
    """An amber question chip: a hook and a dot drawn as shapes."""
    return (f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{INK["quiz_amber"]}"/>'
            f'<path d="M{fmt(x - r * .32)},{fmt(y - r * .22)} C{fmt(x - r * .3)},{fmt(y - r * .68)} {fmt(x + r * .38)},{fmt(y - r * .66)} '
            f'{fmt(x + r * .34)},{fmt(y - r * .26)} C{fmt(x + r * .3)},{fmt(y - r * .02)} {fmt(x)},{fmt(y)} {fmt(x)},{fmt(y + r * .2)}" '
            f'fill="none" stroke="#ffffff" stroke-width="{fmt(r * .26)}" stroke-linecap="round"/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y + r * .52)}" r="{fmt(r * .14)}" fill="#ffffff"/>')


def _gear(p, cx, cy, r, n, fill, rot=0.0, hub=None):
    """A gear wheel: n teeth, outer radius r, a darker inner ring and a hub."""
    ri, pts = r - max(3.5, r * .17), []
    for i in range(n):
        a0 = rot + 360 * i / n
        for f, rr in ((-.27, ri), (-.13, r), (.13, r), (.27, ri)):
            a = math.radians(a0 + f * 360 / n)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    dk = mix(fill, p['line'], .3)
    return (f'<path d="{_d(pts)}" fill="{fill}" {stroke(p)}/>'
            f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(ri * .68)}" fill="none" stroke="{dk}" stroke-width="2.2"/>'
            f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r * .24)}" fill="{hub or p["gold"]}" {stroke(p)}/>'
            f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r * .08)}" fill="{p["line"]}"/>')


def _card(p, cx, cy, rot, ink, icon='', w=30, h=40, lines=2):
    """A white card with a coloured tab. icon: a fragment in card coordinates (centre about (0, -2))."""
    x0, y0 = -w / 2, -h / 2
    tab = (f'<path d="M{fmt(x0)},{fmt(y0 + 9)} L{fmt(x0)},{fmt(y0 + 4)} Q{fmt(x0)},{fmt(y0)} {fmt(x0 + 4)},{fmt(y0)} '
           f'L{fmt(-x0 - 4)},{fmt(y0)} Q{fmt(-x0)},{fmt(y0)} {fmt(-x0)},{fmt(y0 + 4)} L{fmt(-x0)},{fmt(y0 + 9)} Z" fill="{ink}"/>')
    ln = f'M{fmt(x0 + 6)},{fmt(-y0 - 10)} L{fmt(-x0 - 6)},{fmt(-y0 - 10)}'
    if lines > 1:
        ln += f' M{fmt(x0 + 6)},{fmt(-y0 - 5)} L{fmt(-x0 - 11)},{fmt(-y0 - 5)}'
    return (f'<g transform="translate({fmt(cx)},{fmt(cy)}) rotate({fmt(rot)})">'
            f'<rect x="{fmt(x0)}" y="{fmt(y0)}" width="{fmt(w)}" height="{fmt(h)}" rx="4" fill="{p["paper"]}"/>'
            f'<rect x="{fmt(-x0 - 4.5)}" y="{fmt(y0 + 1)}" width="3.5" height="{fmt(h - 2)}" rx="1.7" fill="{p["paper_sh"]}"/>'
            + tab + icon +
            f'<path d="{ln}" stroke="{p["paper_line"]}" stroke-width="2" stroke-linecap="round"/>'
            f'<rect x="{fmt(x0)}" y="{fmt(y0)}" width="{fmt(w)}" height="{fmt(h)}" rx="4" fill="none" {stroke(p)}/></g>')


def _pearl(p, x, y, r, tint=None):
    body = tint or p['pearl']
    shade = mix(body, p['line'], .25) if tint else p['pearl_sh']
    return (f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{shade}"/>'
            f'<circle cx="{fmt(x - r * .17)}" cy="{fmt(y - r * .17)}" r="{fmt(r * .8)}" fill="{body}"/>'
            f'<circle cx="{fmt(x - r * .36)}" cy="{fmt(y - r * .36)}" r="{fmt(r * .27)}" fill="{p["pearl_hi"]}"/>'
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="none" {stroke(p, .8)}/>')


def _ocean_page(p, cx, cy, rot, w=30, h=40, fish=True):
    """A printed page in the ocean look: a wave band at the top, a seabed strip at the bottom, a small fish; no text."""
    x0, y0 = -w / 2, -h / 2
    band = (f'<path d="M{fmt(x0 + 2)},{fmt(y0 + 2)} L{fmt(-x0 - 2)},{fmt(y0 + 2)} L{fmt(-x0 - 2)},{fmt(y0 + 7)} '
            f'Q{fmt(w * .25)},{fmt(y0 + 10)} 0,{fmt(y0 + 7)} T{fmt(x0 + 2)},{fmt(y0 + 7)} Z" fill="{INK["wave_front"]}"/>')
    bed = (f'<path d="M{fmt(x0 + 2)},{fmt(-y0 - 7)} Q{fmt(x0 + w * .3)},{fmt(-y0 - 11)} {fmt(x0 + w * .55)},{fmt(-y0 - 8)} '
           f'T{fmt(-x0 - 2)},{fmt(-y0 - 9)} L{fmt(-x0 - 2)},{fmt(-y0 - 2)} L{fmt(x0 + 2)},{fmt(-y0 - 2)} Z" fill="{INK["mid"]}"/>')
    f = oa.mono_fish(-1, 0, w * .3, INK['coral'], flip=True) if fish else ''
    return (f'<g transform="translate({fmt(cx)},{fmt(cy)}) rotate({fmt(rot)})">'
            f'<rect x="{fmt(x0)}" y="{fmt(y0)}" width="{fmt(w)}" height="{fmt(h)}" rx="2.5" fill="{p["paper"]}"/>'
            + band + bed + f +
            f'<rect x="{fmt(x0)}" y="{fmt(y0)}" width="{fmt(w)}" height="{fmt(h)}" rx="2.5" fill="none" {stroke(p)}/></g>')


def _guide(p, cx, cy, rot=0.0, s=1.0):
    """A closed field guide: reef-yellow cover, a darker spine, white page edges and a small coral fish."""
    return (f'<g transform="translate({fmt(cx)},{fmt(cy)}) rotate({fmt(rot)}) scale({fmt(s, 3)})">'
            f'<rect x="-19" y="-15" width="42" height="31" rx="3.5" fill="{p["paper"]}" {stroke(p, 1 / s)}/>'
            f'<path d="M21,-10 L21,11 M17.5,-11 L17.5,12" stroke="{p["paper_line"]}" stroke-width="1.6"/>'
            f'<rect x="-22" y="-17" width="38" height="33" rx="4" fill="{p["gold"]}" {stroke(p, 1 / s)}/>'
            f'<rect x="-22" y="-17" width="8" height="33" rx="3.5" fill="{p["gold_dk"]}" {stroke(p, 1 / s)}/>'
            + oa.mono_fish(2.5, -.5, 17, INK['coral'], flip=True) + '</g>')


def _flying_book(p, cx, cy, s, lift_l, lift_r, rot=0.0):
    """An open field guide gliding like a ray: yellow cover wings curving up at the tips, white pages fanned on top."""
    def wing(f, fish):
        cover = (f'M0,0 C-14,-2 -30,{fmt(-f * .6)} -44,{fmt(-f)} C-41,{fmt(-f + 8)} -30,6 0,10 Z')
        pages = (f'M0,0 C-11,-12 -26,{fmt(-f - 8)} -40,{fmt(-f - 9)} L-44,{fmt(-f)} C-30,{fmt(-f * .6)} -14,-2 0,0 Z')
        out = (f'<path d="{cover}" fill="{p["gold"]}" {stroke(p, 1 / s)}/>'
               f'<path d="M-6,8 C-18,6 -30,3 -40,{fmt(-f + 4)}" fill="none" stroke="{p["gold_dk"]}" stroke-width="2.2" stroke-linecap="round"/>'
               f'<path d="{pages}" fill="{p["paper"]}" {stroke(p, 1 / s)}/>'
               f'<path d="M-3,-3 C-14,-9 -27,{fmt(-f * .8 - 4)} -39,{fmt(-f - 5)} M-2,-1 C-14,-5 -28,{fmt(-f * .7 - 1)} -41,{fmt(-f - 2)}" fill="none" '
               f'stroke="{p["paper_line"]}" stroke-width="1.2" stroke-opacity=".8"/>')
        if fish:
            out += oa.mono_fish(-22, 3.5 - f * .22, 10, INK['coral'], flip=False)
        return out
    return (f'<g transform="translate({fmt(cx)},{fmt(cy)}) rotate({fmt(rot)}) scale({fmt(s, 3)})">'
            + wing(lift_l, True) + f'<g transform="scale(-1,1)">{wing(lift_r, False)}</g>'
            f'<ellipse cx="0" cy="4" rx="3" ry="6" fill="{p["gold_dk"]}" {stroke(p, 1 / s)}/></g>')


def _reef_left(sc, tall=118):
    p = sc.p
    return sc.seaweed(32, tall, phase=.5) + sc.seaweed(54, tall * .7, p['weed_light'], width=4, phase=2.0)


# ------------------------------------------------------------------------------------------------------------ 60-outputs
def scene_outputs(dark=False):
    """60-outputs, "Outputs": a boat's hull breaks the surface and a line hoists a cargo net of everything the knowledge base
    produces (a globe for the web edition, a field guide, a toolbox for the developer kit, a conch for the media kit, a chip for
    the agent pack, two badges hanging under it) while the Diver bot stands on the seabed and points the load up to the boat."""
    sc = Scene('60-outputs', dark, seed=61, avoid=[(330, 720)], rays=6, glow=(660, -30, 380))
    p = sc.p
    st = stroke(p)
    sc.under.append(sc.far_school(170, 70, 14, n=5, flip=True, seed=1))
    # the hull, seen from below; the surface waves are drawn over its top
    hull = mix(p['line'], p['wave_front'], .42)
    hull_d = 'M478,-4 L492,4 C522,30 580,48 660,49 L778,48 C794,47 800,36 804,10 L814,-4 Z'
    clip = sc.id('hull')
    sc.defs.append(f'<clipPath id="{clip}"><path d="{hull_d}"/></clipPath>')
    sc.body.append(f'<path d="M786,46 L790,64 L806,64 L800,40 Z" fill="{mix(hull, p["line"], .4)}" {st}/>'
                   f'<path d="{hull_d}" fill="{hull}"/>'
                   f'<g clip-path="url(#{clip})" fill="none" stroke-linecap="round">'
                   f'<path d="M470,56 C560,56 620,41 664,41 C730,41 790,34 830,20 L830,60 Z" fill="{mix(hull, p["line"], .4)}"/>'
                   f'<path d="M488,14 C550,32 640,36 720,35 C770,34 800,28 820,22" stroke="{p["pearl"]}" stroke-width="4"/>'
                   f'<path d="M530,30 C590,42 640,44 700,43 M560,24 C620,34 700,36 780,22" stroke="{p["line"]}" stroke-width="1.4" stroke-opacity=".35"/>'
                   f'<path d="M540,46 C600,52 700,51 800,48" stroke="{p["coral"]}" stroke-width="6"/></g>'
                   f'<path d="{hull_d}" fill="none" {st}/>')
    # the block under the hull, the line and the hook
    cx = 600
    sc.body.append(f'<rect x="{cx - 7}" y="36" width="14" height="16" rx="4" fill="{p["metal"]}" {st}/>'
                   f'<circle cx="{cx}" cy="44" r="3.4" fill="{p["gold"]}" {stroke(p, .8)}/>'
                   f'<path d="M{cx},52 L{cx},78" stroke="{p["wood_dk"]}" stroke-width="2.4"/>'
                   f'<path d="M{cx},76 L{cx},82 C{cx},89 {cx - 8},89 {cx - 8},84" fill="none" stroke="{p["metal_dk"]}" stroke-width="3.4" stroke-linecap="round"/>')
    sc.body.append(sc.shadow(600, FLOOR, 86, op=.6))
    # the net bag: a faint fill behind the cargo
    bag = f'M{cx},90 C570,96 508,114 508,152 C508,190 546,208 600,208 C654,208 694,190 694,152 C694,114 630,96 {cx},90 Z'
    sc.body.append(f'<path d="{bag}" fill="{p["glass"]}" fill-opacity="{".16" if not dark else ".1"}"/>')
    # the cargo, large enough to read at README width
    cargo = []
    # globe (the web edition)
    gx, gy, gr = 552, 158, 25
    cargo.append(f'<circle cx="{gx}" cy="{gy}" r="{gr}" fill="{mix(INK["fish_blue"], "#ffffff", .25)}" {st}/>'
                 f'<path d="M{gx - 16},{gy - 13} C{gx - 5},{gy - 18} {gx + 3},{gy - 8} {gx - 4},{gy - 1} C{gx - 10},{gy + 5} {gx - 20},{gy} {gx - 16},{gy - 13} Z '
                 f'M{gx + 5},{gy + 5} C{gx + 16},{gy + 1} {gx + 21},{gy + 12} {gx + 10},{gy + 18} C{gx + 4},{gy + 20} {gx},{gy + 12} {gx + 5},{gy + 5} Z" '
                 f'fill="{INK["fish_green"]}" fill-opacity=".85"/>'
                 f'<ellipse cx="{gx}" cy="{gy}" rx="10" ry="{gr}" fill="none" stroke="{p["pearl"]}" stroke-width="1.6" stroke-opacity=".85"/>'
                 f'<path d="M{gx - gr},{gy} L{gx + gr},{gy}" stroke="{p["pearl"]}" stroke-width="1.6" stroke-opacity=".85"/>'
                 f'<circle cx="{gx}" cy="{gy}" r="{gr}" fill="none" {st}/>')
    # chip (the agent pack)
    kx, ky = 598, 124
    pins = ''.join(f'M{kx - 7 + 7 * i},{ky - 15} l0,-5 M{kx - 7 + 7 * i},{ky + 15} l0,5 M{kx - 15},{ky - 7 + 7 * i} l-5,0 M{kx + 15},{ky - 7 + 7 * i} l5,0 '
                   for i in range(3))
    cargo.append(f'<path d="{pins}" stroke="{p["metal_dk"]}" stroke-width="2.4" stroke-linecap="round"/>'
                 f'<rect x="{kx - 15}" y="{ky - 15}" width="30" height="30" rx="5" fill="{p["violet"]}" {st}/>'
                 f'<rect x="{kx - 8}" y="{ky - 8}" width="16" height="16" rx="2.5" fill="{p["violet_lt"]}"/>')
    # a field guide (the PDFs)
    cargo.append(_guide(p, 652, 132, rot=-10, s=1.12))
    # toolbox (the developer kit)
    tx, ty = 602, 184
    cargo.append(f'<path d="M{tx - 11},{ty - 13} L{tx - 11},{ty - 20} L{tx + 11},{ty - 20} L{tx + 11},{ty - 13}" fill="none" '
                 f'stroke="{p["metal_dk"]}" stroke-width="3.4" stroke-linejoin="round"/>'
                 f'<rect x="{tx - 27}" y="{ty - 13}" width="54" height="28" rx="5" fill="{INK["wave_front"]}" {st}/>'
                 f'<path d="M{tx - 27},{ty - 2} L{tx + 27},{ty - 2}" stroke="{p["line"]}" stroke-width="1.4" stroke-opacity=".6"/>'
                 f'<rect x="{tx - 5}" y="{ty - 6}" width="10" height="8" rx="1.5" fill="{p["gold"]}" {stroke(p, .8)}/>')
    # conch (the media kit), mouth to the right
    cargo.append(_conch(p, 676, 176, -6, s=.34))
    sc.body.append(''.join(cargo))
    # the mesh goes over the cargo, light enough to see through
    nclip = sc.id('net')
    sc.defs.append(f'<clipPath id="{nclip}"><path d="{bag}"/></clipPath>')
    mesh = []
    for k in range(-12, 16):
        x = 506 + k * 15
        mesh.append(f'M{x},86 l124,124 M{x + 124},86 l-124,124')
    sc.body.append(f'<g clip-path="url(#{nclip})"><path d="{" ".join(mesh)}" stroke="{p["wood_dk"] if not dark else p["wood_hi"]}" '
                   f'stroke-width="1.3" stroke-opacity="{".5" if not dark else ".6"}"/></g>'
                   f'<path d="{bag}" fill="none" stroke="{p["wood_dk"]}" stroke-width="3.2" stroke-linejoin="round"/>'
                   f'<circle cx="{cx - 3}" cy="89" r="4.5" fill="none" stroke="{p["gold"]}" stroke-width="2.6"/>')
    # two badges hanging off the net's sides
    for mx, my, rib in ((530, 206, INK['wave_front']), (690, 194, p['coral'])):
        sc.body.append(f'<path d="M{mx - 4},{my - 18} L{mx},{my - 5} L{mx + 4},{my - 18}" fill="none" stroke="{rib}" stroke-width="3.2" stroke-linejoin="round"/>'
                       f'<circle cx="{mx}" cy="{my}" r="7" fill="{p["gold"]}" {st}/>'
                       f'<circle cx="{mx}" cy="{my}" r="3.6" fill="none" stroke="{p["gold_dk"]}" stroke-width="1.4"/>')
    # the bot stands well clear of the load and points it up to the boat
    sc.body.append(sc.shadow(384, FLOOR, 40))
    sc.body.append(sc.bot('point', 380, FLOOR))
    sc.body.append(sc.bubbles(470, 140, 60, 3.4, n=4, seed=2))
    for x, y, r in ((494, 108, 4.5), (712, 120, 3.8), (640, 222, 3.2)):
        sc.body.append(_sparkle(x, y, r, p['gold_hi'] if not dark else p['gold'], .9))
    sc.body.append(sc.fish(760, 116, 24, 'yellow'))
    sc.over.append(_reef_left(sc))
    sc.over.append(sc.anemone(784, 15) + sc.coral(836, .38) + sc.seaweed(862, 90, p['weed_light'], width=4, phase=2.4))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 60-outputs/content
def _conch(p, mx, my, rot, s=1.0):
    """A big conch used as a megaphone: mouth (bell) on the right centred on (mx, my), spire to the left."""
    st = stroke(p, 1 / s)
    lip, throat, deep = mix(p['coral'], '#ffffff', .72), mix(p['coral'], '#ffffff', .42), mix(p['coral'], p['line'], .15)
    knobs = ''.join(f'<circle cx="{x}" cy="{y}" r="5.5" fill="{p["pearl"]}" {st}/>' for x, y in ((-96, -6), (-72, -19), (-46, -32)))
    return (f'<g transform="translate({fmt(mx)},{fmt(my)}) rotate({fmt(rot)}) scale({fmt(s, 3)})">' + knobs +
            f'<path d="M-128,10 C-104,-2 -60,-32 -2,-46 L-2,46 C-50,40 -96,28 -128,10 Z" fill="{p["pearl"]}"/>'
            f'<path d="M-128,10 C-96,28 -50,40 -2,46 L-2,36 C-50,30 -94,22 -128,10 Z" fill="{p["pearl_sh"]}"/>'
            f'<path d="M-100,-1 Q-92,10 -100,22 M-74,-17 Q-62,8 -74,32 M-46,-31 Q-30,5 -46,39" fill="none" stroke="{p["pearl_sh"]}" stroke-width="2.4" stroke-linecap="round"/>'
            f'<path d="M-120,4 C-96,-6 -64,-26 -20,-40" fill="none" stroke="{p["pearl_hi"]}" stroke-width="2.4" stroke-linecap="round"/>'
            f'<path d="M-128,10 C-104,-2 -60,-32 -2,-46 M-2,46 C-50,40 -96,28 -128,10" fill="none" {st}/>'
            f'<ellipse cx="2" cy="0" rx="17" ry="47" fill="{lip}" {st}/>'
            f'<ellipse cx="5" cy="2" rx="11" ry="37" fill="{throat}"/>'
            f'<ellipse cx="7" cy="4" rx="5.5" ry="23" fill="{deep}"/></g>')


def scene_content(dark=False):
    """60-outputs/content, "Media kit": a conch megaphone on a coral stand sends out rings of sound and cards (a fact with a
    green check, a myth with a crossed bubble, a quote as a speech bubble of dots), a little camera and a microphone."""
    sc = Scene('60-outputs-content', dark, seed=62, avoid=[(400, 740)], rays=6, glow=(600, -30, 380))
    p = sc.p
    st = stroke(p)
    sc.under.append(sc.far_school(150, 70, 14, n=5, flip=True, seed=1))
    mx, my = 566, 128
    # sound rings from the mouth
    rings = []
    for r, op in ((60, .75), (82, .5), (104, .3)):
        a0, a1 = math.radians(-42), math.radians(42)
        rings.append(f'<path d="M{fmt(mx + r * math.cos(a0))},{fmt(my + r * math.sin(a0))} A{r},{r} 0 0 1 '
                     f'{fmt(mx + r * math.cos(a1))},{fmt(my + r * math.sin(a1))}" fill="none" stroke="{p["blue"]}" '
                     f'stroke-width="3.2" stroke-linecap="round" stroke-opacity="{op}"/>')
    sc.body.append(''.join(rings))
    # the coral stand on a small rock, then the conch
    sc.body.append(sc.shadow(510, FLOOR, 60))
    sc.body.append(f'<path d="M512,{FLOOR - 4} L512,196 M512,200 C512,190 500,186 494,176 M512,198 C516,188 528,186 534,180" fill="none" '
                   f'stroke="{p["coral"]}" stroke-width="8" stroke-linecap="round"/>')
    sc.body.append(_rock(p, 478, 548, 210))
    sc.body.append(_conch(p, mx, my, -8))
    # cards and gear drifting out
    fact = _check(0, -2, 7.5)
    myth = (f'<circle cx="0" cy="-2" r="8" fill="{p["glass"]}" stroke="{p["paper_line"]}" stroke-width="1.6"/>'
            f'<path d="M-8,6 L8,-10" stroke="{INK["verdict_no"]}" stroke-width="3" stroke-linecap="round"/>')
    ink = INK['label_stage'][0]
    q = (f'<path d="M-9,-9 L9,-9 Q11,-9 11,-7 L11,1 Q11,3 9,3 L-1,3 L-6,7 L-5,3 L-9,3 Q-11,3 -11,1 L-11,-7 Q-11,-9 -9,-9 Z" '
         f'fill="{mix(ink, "#ffffff", .82)}" stroke="{ink}" stroke-width="1.6" stroke-linejoin="round"/>'
         + ''.join(f'<circle cx="{dx}" cy="-3" r="1.9" fill="{ink}"/>' for dx in (-5, 0, 5)))
    sc.body.append(_card(p, 668, 58, -10, INK['label_stage'][0], q))
    sc.body.append(_card(p, 712, 116, 8, INK['label_docs'][0], fact))
    sc.body.append(_card(p, 668, 182, -5, INK['label_press'][0], myth))
    # a small camera and a microphone drifting with them
    sc.body.append(f'<g transform="translate(452,70) rotate(-10)">'
                   f'<rect x="-7" y="-15" width="12" height="6" rx="2" fill="{p["metal_dk"]}" {st}/>'
                   f'<rect x="-17" y="-10" width="34" height="22" rx="5" fill="{p["metal"]}" {st}/>'
                   f'<circle cx="1" cy="1" r="8" fill="{p["line"]}"/><circle cx="1" cy="1" r="5" fill="{mix(p["blue"], p["line"], .3)}"/>'
                   f'<circle cx="-1" cy="-1" r="1.8" fill="#ffffff"/>'
                   f'<rect x="9" y="-7" width="5" height="3" rx="1" fill="{p["coral"]}"/></g>')
    sc.body.append(f'<g transform="translate(404,96) rotate(24)">'
                   f'<rect x="-3" y="6" width="6" height="22" rx="3" fill="{p["metal_dk"]}" {st}/>'
                   f'<rect x="-8" y="-12" width="16" height="22" rx="8" fill="{p["metal"]}" {st}/>'
                   f'<path d="M-6,-5 L6,-5 M-6,0 L6,0 M-6,5 L6,5 M-3,-11 L-3,9 M3,-11 L3,9" stroke="{p["metal_dk"]}" stroke-width="1.2"/>'
                   f'<rect x="-9" y="5" width="18" height="4" rx="2" fill="{p["gold"]}" {stroke(p, .8)}/></g>')
    sc.body.append(sc.shadow(304, FLOOR, 40))
    sc.body.append(sc.bot('point', 300, FLOOR))
    sc.body.append(sc.bubbles(380, 160, 40, 3.2, n=3, seed=2))
    for x, y, r in ((628, 30, 4), (740, 70, 3.5), (720, 205, 3.2)):
        sc.body.append(_sparkle(x, y, r, p['gold_hi'] if not dark else p['gold'], .85))
    sc.body.append(sc.fish(190, 96, 24, 'yellow', flip=True))
    sc.over.append(_reef_left(sc))
    sc.over.append(sc.anemone(784, 16) + sc.coral(838, .4) + sc.seaweed(864, 92, p['weed_light'], width=4, phase=2.6))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 60-outputs/dev
def scene_dev(dark=False):
    """60-outputs/dev, "Developer kit": a small submarine in a dry-dock cradle, the Diver bot peeking out of its hatch, a tool
    board with a wrench, a screwdriver and a gauge, a clipboard with three green checks and a wrench on the seabed."""
    sc = Scene('60-outputs-dev', dark, seed=63, avoid=[(340, 760)], rays=6, glow=(520, -30, 380))
    p = sc.p
    st = stroke(p)
    blue = INK['wave_front']
    blue_dk = mix(blue, p['line'], .4)
    sc.under.append(sc.far_school(170, 74, 14, n=5, flip=True, seed=1))
    sc.body.append(sc.shadow(510, FLOOR, 140))
    # cradle chocks
    for x in (440, 588):
        sc.body.append(f'<path d="M{x - 26},{FLOOR} L{x - 22},201 C{x - 10},210 {x + 10},210 {x + 22},201 L{x + 26},{FLOOR} Z" fill="{p["wood"]}" {st}/>'
                       f'<path d="M{x + 12},{FLOOR} L{x + 17},205 C{x + 20},204 {x + 21},202 {x + 22},201 L{x + 26},{FLOOR} Z" fill="{p["wood_dk"]}" fill-opacity=".6"/>')
    # propeller (behind the tail)
    sc.body.append(f'<path d="M654,172 L660,172" stroke="{p["metal_dk"]}" stroke-width="5"/>'
                   f'<ellipse cx="664" cy="160" rx="5" ry="13" fill="{p["coral"]}" {st}/>'
                   f'<ellipse cx="664" cy="185" rx="5" ry="13" fill="{p["coral"]}" {st}/>'
                   f'<circle cx="663" cy="172" r="4.5" fill="{p["gold"]}" {st}/>')
    # tail fins
    sc.body.append(f'<path d="M612,146 L626,122 L640,122 L640,154 Z" fill="{blue_dk}" {st}/>'
                   f'<path d="M616,200 L632,218 L644,218 L640,192 Z" fill="{blue_dk}" {st}/>')
    # hull
    hull = 'M412,140 L590,140 C624,140 650,156 656,172 C650,188 624,204 590,204 L412,204 C388,204 372,190 372,172 C372,154 388,140 412,140 Z'
    hclip = sc.id('hull')
    sc.defs.append(f'<clipPath id="{hclip}"><path d="{hull}"/></clipPath>')
    sc.body.append(f'<path d="{hull}" fill="{blue}"/>'
                   f'<g clip-path="url(#{hclip})"><rect x="360" y="162" width="310" height="12" fill="{p["pearl"]}"/>'
                   f'<rect x="360" y="188" width="310" height="20" fill="{blue_dk}"/>'
                   f'<path d="M392,150 C420,144 470,144 520,144" stroke="{mix(blue, "#ffffff", .45)}" stroke-width="3" fill="none" stroke-linecap="round"/>'
                   f'<path d="M548,140 L548,204" stroke="{p["line"]}" stroke-width="1.4" stroke-opacity=".5"/></g>'
                   f'<path d="{hull}" fill="none" {st}/>')
    # portholes on the pearl band
    for x in (414, 460, 584):
        sc.body.append(f'<circle cx="{x}" cy="168" r="10" fill="{p["metal"]}" {st}/>'
                       f'<circle cx="{x}" cy="168" r="6.5" fill="{p["glass_dk"]}"/>'
                       f'<path d="M{x - 3.5},165 A4,4 0 0 1 {x},163" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>')
    # rivets
    sc.body.append(f'<g fill="{mix(blue, "#ffffff", .5)}">' + ''.join(f'<circle cx="{x}" cy="196" r="1.6"/>' for x in range(400, 620, 22)) + '</g>')
    # conning tower with the open hatch
    tx = 506
    sc.body.append(f'<path d="M{tx - 34},141 L{tx - 27},116 L{tx + 27},116 L{tx + 34},141 Z" fill="{blue}" {st}/>'
                   f'<path d="M{tx + 16},116 L{tx + 27},116 L{tx + 34},141 L{tx + 21},141 Z" fill="{blue_dk}"/>'
                   f'<path d="M{tx - 34},141 L{tx - 27},116 L{tx + 27},116 L{tx + 34},141" fill="none" {st}/>')
    # the hatch lid thrown back (behind the bot)
    sc.body.append(f'<g transform="translate({tx + 34},100) rotate(14)"><ellipse cx="0" cy="0" rx="9" ry="16" fill="{p["metal"]}" {st}/>'
                   f'<ellipse cx="1.5" cy="0" rx="5" ry="11" fill="none" stroke="{p["metal_dk"]}" stroke-width="1.8"/>'
                   f'<path d="M-6,15 L-9,20" stroke="{p["metal_dk"]}" stroke-width="3" stroke-linecap="round"/></g>')
    sc.body.append(sc.bot('peek', tx - 2, 117, height=52))
    sc.body.append(f'<rect x="{tx - 30}" y="114" width="60" height="7" rx="3.5" fill="{p["metal"]}" {st}/>'
                   f'<path d="M{tx - 26},116.5 L{tx + 22},116.5" stroke="{p["metal_hi"]}" stroke-width="1.6" stroke-linecap="round"/>')
    # tool board on the right
    bx0, bx1, by0, by1 = 682, 742, 118, 186
    sc.body.append(sc.shadow(712, FLOOR, 34))
    sc.body.append(f'<path d="M{bx0 + 8},{by1} L{bx0 + 4},{FLOOR} M{bx1 - 8},{by1} L{bx1 - 4},{FLOOR}" stroke="{p["wood_dk"]}" stroke-width="4" stroke-linecap="round"/>'
                   f'<rect x="{bx0}" y="{by0}" width="{bx1 - bx0}" height="{by1 - by0}" rx="5" fill="{p["wood"]}" {st}/>'
                   f'<g fill="{p["wood_dk"]}">' + ''.join(f'<circle cx="{x}" cy="{y}" r="1.2"/>' for x in range(690, 740, 10) for y in (126, 178)) + '</g>')
    # wrench (hung), screwdriver, gauge
    sc.body.append(f'<g transform="translate(696,152) rotate(-8)">'
                   f'<rect x="-2.6" y="-16" width="5.2" height="30" rx="2.6" fill="{p["metal"]}" {stroke(p, .9)}/>'
                   f'<path d="M-7,-22 C-7,-28 7,-28 7,-22 L7,-15 C7,-11 -7,-11 -7,-15 Z M-2.5,-29 L-2.5,-21 L2.5,-21 L2.5,-29 Z" fill="{p["metal"]}" fill-rule="evenodd" {stroke(p, .9)}/></g>'
                   f'<g transform="translate(716,150)"><rect x="-3.5" y="-18" width="7" height="15" rx="3" fill="{p["gold"]}" {stroke(p, .9)}/>'
                   f'<path d="M0,-3 L0,16" stroke="{p["metal_dk"]}" stroke-width="2.6" stroke-linecap="round"/></g>'
                   f'<circle cx="732" cy="160" r="9" fill="{p["paper"]}" {st}/>'
                   f'<path d="M726,163 A6.5,6.5 0 0 1 738,163" fill="none" stroke="{INK["quiz_green"]}" stroke-width="2"/>'
                   f'<path d="M732,161 L736,155" stroke="{p["line"]}" stroke-width="1.8" stroke-linecap="round"/>')
    # clipboard checklist leaning against the left chock
    cb = (f'<g transform="translate(352,190) rotate(-9)">'
          f'<rect x="-17" y="-24" width="34" height="46" rx="4" fill="{p["wood"]}" {st}/>'
          f'<rect x="-13" y="-17" width="26" height="36" rx="2" fill="{p["paper"]}"/>'
          f'<rect x="-7" y="-27" width="14" height="7" rx="2.5" fill="{p["metal"]}" {stroke(p, .9)}/>')
    for i in range(3):
        y = -10 + i * 10
        cb += _check(-6, y, 3.6) + f'<path d="M0,{y} L9,{y}" stroke="{p["paper_line"]}" stroke-width="2" stroke-linecap="round"/>'
    sc.body.append(cb + '</g>')
    # a wrench lying in the foreground
    sc.over.append(f'<g transform="translate(298,226) rotate(-12)">'
                   f'<rect x="-20" y="-3.2" width="40" height="6.4" rx="3.2" fill="{p["metal"]}" {st}/>'
                   f'<path d="M20,-8 C28,-8 31,-3 31,0 C31,3 28,8 20,8 L22,3 L28,3 L28,-3 L22,-3 Z" fill="{p["metal"]}" {st}/>'
                   f'<path d="M-16,-1 L14,-1" stroke="{p["metal_hi"]}" stroke-width="1.6" stroke-linecap="round"/></g>')
    sc.body.append(sc.bubbles(536, 98, 56, 3.6, n=4, seed=2))
    sc.body.append(sc.school(222, 98, 18, 'blue', n=4, flip=True, seed=3))
    sc.body.append(sc.fish(632, 62, 22, 'yellow'))
    sc.over.append(_reef_left(sc))
    sc.over.append(sc.coral(826, .36) + sc.seaweed(856, 100, p['weed_light'], width=4, phase=2.2))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ 60-outputs/pdf
def scene_guides(dark=False):
    """60-outputs/pdf, "Field guides": open field guides glide through the water in a loose V like a flock of rays while the
    Diver bot sits on a rock reading one."""
    sc = Scene('60-outputs-pdf', dark, seed=64, avoid=[(180, 320), (400, 730)], rays=6, glow=(560, -30, 400))
    p = sc.p
    sc.under.append(sc.far_school(760, 160, 13, n=4, seed=1))
    flock = ((452, 112, 1.08, 14, 9, -4), (532, 76, .92, 10, 15, -8), (540, 150, .9, 16, 10, 2),
             (616, 52, .76, 13, 9, -6), (624, 128, .74, 8, 14, -2), (700, 92, .62, 12, 12, -5))
    for i, (x, y, s, fl, fr, rot) in enumerate(flock):
        # a short wake of bubbles behind each guide
        sc.body.append(sc.bubble(x + 50 * s, y + 3, 2.4 * s))
        sc.body.append(_flying_book(p, x, y, s, fl, fr, rot))
    sc.body.append(sc.shadow(250, FLOOR, 56))
    sc.body.append(_rock(p, 202, 300, 198))
    sc.body.append(sc.bot('read', 250, 200))
    for x, y, r in ((496, 40, 4.2), (676, 168, 3.6), (760, 60, 3.2)):
        sc.body.append(_sparkle(x, y, r, p['gold_hi'] if not dark else p['gold'], .85))
    sc.body.append(sc.fish(390, 196, 20, 'red', flip=True))
    sc.over.append(_reef_left(sc, 112))
    sc.over.append(sc.anemone(790, 16) + sc.coral(842, .38) + sc.seaweed(866, 84, p['weed_light'], width=4, phase=1.4))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ _system
def scene_system(dark=False):
    """_system, "The system": a cut-away submarine engine room: hull ribs, interlocking gears, a machine with a glowing
    porthole, pipes and a gauge, and a conveyor taking claim cards in on the left and pages, a guide and a map out on the right."""
    sc = Scene('_system', dark, seed=70, avoid=[(330, 760)], rays=5, glow=(540, -30, 380))
    p = sc.p
    st = stroke(p)
    # hull ribs: the cut-away frame (behind the seabed)
    rib = 'M342,250 C342,100 430,34 548,34 C666,34 754,100 754,250'
    rib2 = 'M372,250 C372,120 446,62 548,62 C650,62 724,120 724,250'
    sc.under.append(f'<path d="{rib} Z" fill="{p["metal"]}" fill-opacity="{".22" if not dark else ".16"}"/>'
                    f'<path d="{rib}" fill="none" stroke="{p["line"]}" stroke-width="15" stroke-opacity=".9"/>'
                    f'<path d="{rib}" fill="none" stroke="{p["metal"]}" stroke-width="12"/>'
                    f'<path d="{rib}" fill="none" stroke="{p["metal_dk"]}" stroke-width="1.6" stroke-dasharray="1.6 14" stroke-linecap="round"/>'
                    f'<path d="{rib2}" fill="none" stroke="{p["metal"]}" stroke-width="5" stroke-opacity=".55"/>')
    # gears
    sc.body.append(_gear(p, 466, 84, 30, 11, p['metal'], 6, p['gold']))
    sc.body.append(_gear(p, 509, 58, 20, 8, p['gold'], 10, p['metal_hi']))
    sc.body.append(_gear(p, 537, 86, 15, 7, p['metal'], 2, p['gold']))
    # conveyor
    sc.body.append(f'<path d="M352,212 L348,{FLOOR} M724,212 L728,{FLOOR}" stroke="{p["metal_dk"]}" stroke-width="5" stroke-linecap="round"/>'
                   f'<rect x="336" y="203" width="400" height="10" rx="5" fill="{p["metal_dk"]}" {st}/>'
                   f'<g fill="{p["metal_hi"]}">' + ''.join(f'<circle cx="{x}" cy="208" r="2.2"/>' for x in range(346, 736, 26)) + '</g>')
    # the machine with its porthole glow
    glow = sc.radial('boil', p['gold'], .8 if not dark else .7, .35)
    sc.body.append(f'<ellipse cx="506" cy="160" rx="70" ry="54" fill="{glow}"/>'
                   f'<rect x="454" y="112" width="104" height="96" rx="12" fill="{p["metal"]}" {st}/>'
                   f'<rect x="534" y="113" width="22" height="94" rx="10" fill="{p["metal_dk"]}" fill-opacity=".55"/>'
                   f'<rect x="460" y="182" width="16" height="22" rx="3" fill="{p["line"]}" fill-opacity=".75"/>'
                   f'<rect x="536" y="182" width="16" height="22" rx="3" fill="{p["line"]}" fill-opacity=".75"/>'
                   f'<path d="M462,124 L520,124" stroke="{p["metal_hi"]}" stroke-width="2.2" stroke-linecap="round"/>'
                   f'<circle cx="506" cy="152" r="19" fill="{p["gold"]}" {st}/>'
                   f'<circle cx="506" cy="152" r="13" fill="{p["gold_hi"]}"/>'
                   f'<circle cx="506" cy="152" r="19" fill="none" stroke="{p["metal_dk"]}" stroke-width="4"/>'
                   f'<circle cx="506" cy="152" r="21" fill="none" {st}/>'
                   f'<g fill="{p["metal_dk"]}"><circle cx="463" cy="120" r="1.8"/><circle cx="549" cy="120" r="1.8"/>'
                   f'<circle cx="463" cy="172" r="1.8"/><circle cx="549" cy="172" r="1.8"/></g>')
    # pipe from the machine to the gauge the bot checks
    sc.body.append(f'<path d="M454,140 L300,140 L300,{FLOOR}" fill="none" stroke="{p["line"]}" stroke-width="11" stroke-linejoin="round"/>'
                   f'<path d="M454,140 L300,140 L300,{FLOOR}" fill="none" stroke="{p["metal"]}" stroke-width="8" stroke-linejoin="round"/>'
                   f'<path d="M454,137.5 L302,137.5" stroke="{p["metal_hi"]}" stroke-width="2" stroke-linecap="round"/>'
                   + ''.join(f'<rect x="{x - 3}" y="133" width="6" height="14" rx="2" fill="{p["gold"]}" {stroke(p, .8)}/>' for x in (360, 430))
                   + f'<rect x="293" y="196" width="14" height="6" rx="2" fill="{p["gold"]}" {stroke(p, .8)}/>')
    gx, gy = 300, 168
    sc.body.append(f'<circle cx="{gx}" cy="{gy}" r="15" fill="{p["metal"]}" {st}/>'
                   f'<circle cx="{gx}" cy="{gy}" r="11" fill="{p["paper"]}"/>'
                   f'<path d="M{gx - 8},{gy + 3} A8.5,8.5 0 0 1 {gx + 5},{gy - 7}" fill="none" stroke="{INK["quiz_green"]}" stroke-width="2.4"/>'
                   f'<path d="M{gx + 5},{gy - 7} A8.5,8.5 0 0 1 {gx + 8.5},{gy + 2}" fill="none" stroke="{p["coral"]}" stroke-width="2.4"/>'
                   f'<path d="M{gx},{gy} L{gx + 4},{gy - 7}" stroke="{p["line"]}" stroke-width="2" stroke-linecap="round"/>'
                   f'<circle cx="{gx}" cy="{gy}" r="2" fill="{p["line"]}"/>')
    # cards in, pages / a guide / a map out
    for x, lab, rot in ((384, 'slide', -6), (416, 'docs', 5)):
        ink = INK['label_' + lab][0]
        sc.body.append(_card(p, x, 186, rot, ink, _pearl(p, 0, -1, 4.6, mix(ink, '#ffffff', .6)), w=22, h=30, lines=1))
    sc.body.append(_ocean_page(p, 586, 186, 4, 22, 30))
    sc.body.append(_guide(p, 632, 190, -4, .66))
    mp = (f'<g transform="translate(684,189) rotate(5)">'
          f'<path d="M-17,-13 L-6,-10 L6,-13 L17,-10 L17,13 L6,10 L-6,13 L-17,10 Z" fill="{mix(p["wood_hi"], "#ffffff", .45)}" {st}/>'
          f'<path d="M-6,-10 L-6,13 M6,-13 L6,10" stroke="{p["wood"]}" stroke-width="1.2"/>'
          f'<path d="M-12,6 C-6,2 -2,-6 4,-2 S10,4 12,-6" fill="none" stroke="{p["coral"]}" stroke-width="1.6" stroke-dasharray="2.4 2.4"/>'
          f'<path d="M10,-9 l4,4 M14,-9 l-4,4" stroke="{INK["verdict_no"]}" stroke-width="1.8" stroke-linecap="round"/></g>')
    sc.body.append(mp)
    sc.body.append(sc.shadow(236, FLOOR, 40))
    sc.body.append(sc.bot('point', 236, FLOOR))
    sc.body.append(sc.bubbles(560, 50, 30, 3.4, n=3, seed=2) + sc.bubbles(440, 46, 26, 2.8, n=3, seed=5))
    sc.body.append(sc.school(150, 70, 16, 'blue', n=4, flip=True, seed=3))
    sc.over.append(_reef_left(sc))
    sc.over.append(sc.anemone(786, 15) + sc.coral(840, .4) + sc.seaweed(866, 96, p['weed_light'], width=4, phase=2.9))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ _system/brand
def scene_brand(dark=False):
    """_system/brand, "Brand assets": the Diver bot paints a wave and a fish on a small canvas on an easel; beside it a
    scallop-shell palette holds blobs of the Deep Dive colours and a jar of seaweed-tipped brushes."""
    sc = Scene('_system-brand', dark, seed=71, avoid=[(300, 760)], rays=6, glow=(560, -30, 380))
    p = sc.p
    st = stroke(p)
    sc.under.append(sc.far_school(150, 66, 14, n=5, flip=True, seed=1))
    # easel (A-frame) and canvas
    ex = 400
    sc.body.append(sc.shadow(ex, FLOOR, 46))
    sc.body.append(f'<path d="M{ex},76 L{ex + 6},{FLOOR}" stroke="{p["wood_dk"]}" stroke-width="5" stroke-linecap="round"/>'
                   f'<path d="M{ex},70 L{ex - 38},{FLOOR} M{ex},70 L{ex + 38},{FLOOR}" stroke="{p["line"]}" stroke-width="8.2" stroke-linecap="round"/>'
                   f'<path d="M{ex},70 L{ex - 38},{FLOOR} M{ex},70 L{ex + 38},{FLOOR}" stroke="{p["wood"]}" stroke-width="5" stroke-linecap="round"/>')
    cx0, cy0, cw, ch = ex - 54, 86, 108, 74
    cl = sc.id('canvas')
    sc.defs.append(f'<clipPath id="{cl}"><rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="3"/></clipPath>')
    sc.body.append(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="3" fill="{p["paper"]}"/>'
                   f'<g clip-path="url(#{cl})">'
                   f'<rect x="{cx0}" y="{cy0 + 14}" width="{cw}" height="{ch}" fill="{mix(INK["blue_wash"], INK["wave_back"], .35)}"/>'
                   f'<path d="M{cx0 - 4},{cy0 + 16} Q{cx0 + 9},{cy0 + 8} {cx0 + 22},{cy0 + 16} T{cx0 + 48},{cy0 + 16} T{cx0 + 74},{cy0 + 16} T{cx0 + 100},{cy0 + 16} T{cx0 + 126},{cy0 + 16} '
                   f'L{cx0 + 126},{cy0} L{cx0 - 4},{cy0} Z" fill="{INK["wave_front"]}"/>'
                   f'<path d="M{cx0 - 4},{cy0 + ch - 12} Q{cx0 + 30},{cy0 + ch - 22} {cx0 + 60},{cy0 + ch - 14} T{cx0 + 120},{cy0 + ch - 16} L{cx0 + 120},{cy0 + ch + 2} L{cx0 - 4},{cy0 + ch + 2} Z" fill="{INK["mid"]}"/>'
                   + oa.fish(ex + 6, cy0 + 40, 30, INK['fish_red'], flip=True) +
                   oa.bubble(ex - 22, cy0 + 34, 3) + oa.bubble(ex - 28, cy0 + 26, 2) + '</g>'
                   f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="3" fill="none" {stroke(p, 1.3)}/>'
                   f'<rect x="{ex - 62}" y="{cy0 + ch}" width="124" height="7" rx="3" fill="{p["wood"]}" {st}/>'
                   f'<rect x="{ex - 10}" y="{cy0 - 8}" width="20" height="8" rx="2" fill="{p["wood_dk"]}" {st}/>')
    # the bot with a brush (glove at about (cx+21, FLOOR-43)); brush tip on the canvas edge
    bx = 252
    sc.body.append(sc.shadow(bx + 4, FLOOR, 40))
    sc.body.append(f'<path d="M{bx + 22},{FLOOR - 42} L{cx0 + 4},{cy0 + ch - 17}" stroke="{p["line"]}" stroke-width="5.6" stroke-linecap="round"/>'
                   f'<path d="M{bx + 22},{FLOOR - 42} L{cx0 + 4},{cy0 + ch - 17}" stroke="{p["wood"]}" stroke-width="3" stroke-linecap="round"/>'
                   f'<path d="M{cx0 + 18},{cy0 + ch - 28} q6,-5 12,-1 t12,-2" fill="none" stroke="{INK["fish_yellow"]}" stroke-width="3.4" stroke-linecap="round"/>'
                   f'<path d="M{cx0 + 3},{cy0 + ch - 17} L{cx0 + 10},{cy0 + ch - 21}" stroke="{p["line"]}" stroke-width="6.4" stroke-linecap="round"/>'
                   f'<path d="M{cx0 + 3},{cy0 + ch - 17} L{cx0 + 10},{cy0 + ch - 21}" stroke="{p["metal"]}" stroke-width="3.8" stroke-linecap="round"/>'
                   f'<path d="M{cx0 + 9},{cy0 + ch - 24} C{cx0 + 13},{cy0 + ch - 27} {cx0 + 18},{cy0 + ch - 29} {cx0 + 21},{cy0 + ch - 29} '
                   f'C{cx0 + 19},{cy0 + ch - 25} {cx0 + 16},{cy0 + ch - 20} {cx0 + 12},{cy0 + ch - 18} Z" fill="{INK["fish_yellow"]}" {stroke(p, .8)}/>')
    sc.body.append(sc.bot('point', bx, FLOOR))
    # scallop-shell palette propped on a rock
    sx, sy = 560, 196
    sc.body.append(sc.shadow(sx, FLOOR, 74))
    sc.body.append(_rock(p, sx - 46, sx + 46, 204))
    shell_c, shell_sh = mix(p['coral'], p['pearl'], .82), mix(p['coral'], p['pearl'], .64)
    R = 78
    rim, ribs = [], []
    n = 9
    for i in range(n + 1):
        a = math.radians(196 + 148 * i / n)
        rim.append((sx + R * math.cos(a), sy + R * .8 * math.sin(a)))
    d = f'M{fmt(sx)},{sy + 4} L{fmt(rim[0][0])},{fmt(rim[0][1])}'
    for (x0, y0), (x1, y1) in zip(rim, rim[1:]):
        mxp, myp = (x0 + x1) / 2, (y0 + y1) / 2
        k = 1.12
        d += f' Q{fmt(sx + (mxp - sx) * k)},{fmt(sy + (myp - sy) * k)} {fmt(x1)},{fmt(y1)}'
        ribs.append(f'M{fmt(sx)},{sy} L{fmt(x0 + (x0 - sx) * -.04)},{fmt(y0 + (y0 - sy) * -.04)}')
    d += ' Z'
    sc.body.append(f'<path d="{d}" fill="{shell_c}"/>'
                   f'<path d="{" ".join(ribs[1:])}" stroke="{shell_sh}" stroke-width="2.6" stroke-linecap="round"/>'
                   f'<path d="{d}" fill="none" {st}/>'
                   f'<path d="M{sx - 16},{sy + 6} L{sx - 9},{sy - 6} L{sx + 9},{sy - 6} L{sx + 16},{sy + 6} Z" fill="{shell_sh}" {st}/>')
    blobs = ((-44, -26, 9.5, INK['wave_front']), (-18, -46, 9, INK['band']), (12, -50, 9, INK['wave_back']),
             (40, -34, 9.5, INK['coral']), (-30, -6, 8, INK['fish_yellow']), (24, -12, 8.5, INK['label_stage'][0]),   # violet, not green: no four-colour dot set
             (-2, -24, 8, '#ffffff'))
    for dx, dy, r, c in blobs:
        x, y = sx + dx, sy + dy
        sc.body.append(f'<path d="M{fmt(x - r)},{fmt(y)} C{fmt(x - r)},{fmt(y - r * .9)} {fmt(x + r * .8)},{fmt(y - r * 1.1)} {fmt(x + r)},{fmt(y - r * .1)} '
                       f'C{fmt(x + r * 1.1)},{fmt(y + r * .8)} {fmt(x - r * .7)},{fmt(y + r * .9)} {fmt(x - r)},{fmt(y)} Z" fill="{c}" {stroke(p, .8)}/>'
                       f'<circle cx="{fmt(x - r * .35)}" cy="{fmt(y - r * .35)}" r="{fmt(r * .22)}" fill="#ffffff" fill-opacity=".85"/>')
    # jar of seaweed-tipped brushes
    jx = 690
    sc.body.append(sc.shadow(jx, FLOOR, 26))
    for dx, tip, ang in ((-9, p['weed'], -14), (0, p['weed_light'], 2), (9, p['coral'], 16)):
        a = math.radians(ang)
        hx, hy = jx + dx + math.sin(a) * 58, 216 - math.cos(a) * 58
        sc.body.append(f'<path d="M{jx + dx},214 L{fmt(hx)},{fmt(hy)}" stroke="{p["line"]}" stroke-width="4.8" stroke-linecap="round"/>'
                       f'<path d="M{jx + dx},214 L{fmt(hx)},{fmt(hy)}" stroke="{p["wood"]}" stroke-width="2.6" stroke-linecap="round"/>'
                       f'<g transform="translate({fmt(hx)},{fmt(hy)}) rotate({ang})">'
                       f'<path d="M0,2 C-7,-4 -5,-14 0,-22 C3,-15 7,-9 4,-4 C6,-8 9,-10 8,-14 C10,-6 6,0 0,2 Z" fill="{tip}" {stroke(p, .8)}/></g>')
    sc.body.append(f'<path d="M{jx - 19},170 L{jx + 19},170 L{jx + 17},{FLOOR - 4} Q{jx + 17},{FLOOR} {jx + 13},{FLOOR} L{jx - 13},{FLOOR} '
                   f'Q{jx - 17},{FLOOR} {jx - 17},{FLOOR - 4} Z" fill="{p["glass"]}" fill-opacity=".55" {st}/>'
                   f'<rect x="{jx - 21}" y="165" width="42" height="7" rx="3" fill="{p["glass_dk"]}" {st}/>'
                   f'<path d="M{jx - 12},180 L{jx - 12},212" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round" stroke-opacity=".8"/>')
    # coloured paint bubbles rising from the palette
    for x, y, r, c in ((604, 96, 4.6, INK['wave_front']), (590, 74, 3.4, INK['fish_yellow']), (612, 56, 2.6, INK['coral'])):
        sc.body.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" fill-opacity=".85" {stroke(p, .7)}/>'
                       f'<circle cx="{fmt(x - r * .35)}" cy="{fmt(y - r * .35)}" r="{fmt(r * .25)}" fill="#ffffff"/>')
    sc.body.append(sc.fish(176, 104, 22, 'yellow', flip=True))
    sc.over.append(_reef_left(sc))
    sc.over.append(sc.anemone(790, 15) + sc.coral(842, .38) + sc.seaweed(866, 92, p['weed_light'], width=4, phase=2.0))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ _system/eval
def _turtle(p, x, base):
    """A wise old sea turtle sitting upright, facing left, with round spectacles and a clipboard of three marks."""
    st = stroke(p)
    shell, shell_dk = INK['fish_green'], mix(INK['fish_green'], p['line'], .35)
    skin, skin_dk = mix(p['weed_light'], p['pearl'], .35), mix(p['weed_light'], p['line'], .2)
    belly = mix(p['gold_hi'], p['pearl'], .35)
    out = []
    # back flipper/foot and tail
    out.append(f'<path d="M{x + 18},{base - 6} C{x + 34},{base - 8} {x + 42},{base - 2} {x + 36},{base} L{x + 10},{base} Z" fill="{skin}" {st}/>')
    # carapace (seen from the side, on the back)
    out.append(f'<path d="M{x - 6},{base - 4} C{x - 10},{base - 64} {x + 6},{base - 102} {x + 30},{base - 98} '
               f'C{x + 52},{base - 92} {x + 54},{base - 40} {x + 34},{base - 4} Z" fill="{shell}" {st}/>'
               f'<path d="M{x + 18},{base - 96} C{x + 26},{base - 74} {x + 26},{base - 40} {x + 18},{base - 10} '
               f'M{x + 22},{base - 70} L{x + 44},{base - 66} M{x + 24},{base - 40} L{x + 44},{base - 34} M{x + 6},{base - 82} L{x + 20},{base - 76} '
               f'M{x + 2},{base - 50} L{x + 22},{base - 54}" fill="none" stroke="{shell_dk}" stroke-width="2.2" stroke-linecap="round"/>')
    # plastron (belly) and head
    out.append(f'<path d="M{x - 2},{base - 4} C{x - 20},{base - 30} {x - 20},{base - 74} {x - 2},{base - 92} '
               f'C{x + 8},{base - 70} {x + 8},{base - 30} {x + 10},{base - 4} Z" fill="{belly}" {st}/>'
               f'<path d="M{x - 14},{base - 30} L{x + 6},{base - 30} M{x - 16},{base - 54} L{x + 5},{base - 54} M{x - 12},{base - 76} L{x + 4},{base - 76}" '
               f'stroke="{mix(belly, p["line"], .2)}" stroke-width="1.6" stroke-linecap="round"/>')
    hx, hy = x - 16, base - 106
    out.append(f'<path d="M{x - 6},{base - 88} C{x - 10},{base - 98} {hx + 6},{hy + 12} {hx + 2},{hy + 10}" fill="none" stroke="{p["line"]}" stroke-width="14.6" stroke-linecap="round"/>'
               f'<path d="M{x - 6},{base - 88} C{x - 10},{base - 98} {hx + 6},{hy + 12} {hx + 2},{hy + 10}" fill="none" stroke="{skin}" stroke-width="11.4" stroke-linecap="round"/>'
               f'<path d="M{hx + 18},{hy + 2} C{hx + 18},{hy - 16} {hx - 12},{hy - 18} {hx - 18},{hy - 2} C{hx - 22},{hy + 8} {hx - 14},{hy + 14} {hx - 4},{hy + 14} '
               f'C{hx + 8},{hy + 14} {hx + 18},{hy + 12} {hx + 18},{hy + 2} Z" fill="{skin}" {st}/>'
               f'<path d="M{hx - 17},{hy + 6} C{hx - 10},{hy + 10} {hx - 4},{hy + 9} {hx},{hy + 6}" fill="none" stroke="{skin_dk}" stroke-width="1.8" stroke-linecap="round"/>'
               f'<circle cx="{hx - 6}" cy="{hy - 4}" r="2.6" fill="{p["eye"]}"/><circle cx="{hx - 6.8}" cy="{hy - 4.8}" r=".9" fill="#ffffff"/>'
               f'<circle cx="{hx - 6}" cy="{hy - 4}" r="6" fill="{p["glass"]}" fill-opacity=".25" stroke="{p["gold_dk"]}" stroke-width="1.8"/>'
               f'<path d="M{hx},{hy - 5} L{hx + 12},{hy - 7}" stroke="{p["gold_dk"]}" stroke-width="1.6"/>'
               f'<path d="M{hx - 11},{hy - 12} Q{hx - 6},{hy - 15} {hx - 1},{hy - 12}" fill="none" stroke="{p["pearl"]}" stroke-width="2.4" stroke-linecap="round"/>')
    # clipboard held in front, then the front flipper over it
    cx, cy = x - 34, base - 58
    out.append(f'<g transform="translate({cx},{cy}) rotate(-8)">'
               f'<rect x="-17" y="-24" width="34" height="46" rx="4" fill="{p["wood"]}" {st}/>'
               f'<rect x="-13" y="-17" width="26" height="36" rx="2" fill="{p["paper"]}"/>'
               f'<rect x="-7" y="-27" width="14" height="7" rx="2.5" fill="{p["metal"]}" {stroke(p, .9)}/>'
               + _check(-6, -11, 4.4) + _check(-6, -1, 4.4) + _question(-6, 9.5, 4.8)
               + f'<circle cx="-6" cy="9.5" r="4.8" fill="none" stroke="{INK["quiz_amber_text"]}" stroke-width="1"/>' +
               ''.join(f'<path d="M1,{y} L9,{y}" stroke="{p["paper_line"]}" stroke-width="2" stroke-linecap="round"/>' for y in (-11, -1, 9.5)) +
               '</g>')
    out.append(f'<path d="M{x - 4},{base - 70} C{x - 14},{base - 66} {cx + 4},{cy + 6} {cx + 2},{cy + 14} '
               f'C{cx + 8},{cy + 18} {x - 4},{base - 52} {x + 2},{base - 58} Z" fill="{skin}" {st}/>')
    return ''.join(out)


def scene_eval(dark=False):
    """_system/eval, "Evaluating an agent on the agent pack": the Diver bot sits a diving exam at a rock desk with an answer
    sheet and a shell stopwatch, while a wise turtle examiner ticks the answers on a clipboard."""
    sc = Scene('_system-eval', dark, seed=72, avoid=[(260, 720)], rays=6, glow=(520, -30, 380))
    p = sc.p
    st = stroke(p)
    sc.under.append(sc.far_school(160, 64, 14, n=5, flip=True, seed=1))
    # the bot on a stone seat, reading its guide (the agent pack)
    sc.body.append(sc.shadow(300, FLOOR, 50))
    sc.body.append(_rock(p, 258, 340, 206))
    sc.body.append(sc.bot('read', 300, 206))
    # rock desk: top face, front face, two stone legs
    s, sh, hi = _stone(p)
    dx0, dx1 = 382, 540
    sc.body.append(sc.shadow((dx0 + dx1) / 2, FLOOR, 86))
    sc.body.append(''.join(f'<path d="M{x - 11},{FLOOR} L{x - 8},186 L{x + 8},186 L{x + 11},{FLOOR} Z" fill="{sh}" {st}/>' for x in (dx0 + 26, dx1 - 26)))
    top = f'M{dx0 + 10},164 L{dx1 - 4},164 L{dx1 + 4},178 L{dx0},178 Z'
    sc.body.append(f'<path d="{top}" fill="{hi}" {st}/>'
                   f'<path d="M{dx0},178 L{dx1 + 4},178 L{dx1 + 2},190 Q{dx1},193 {dx1 - 4},193 L{dx0 + 4},193 Q{dx0},193 {dx0},189 Z" fill="{s}" {st}/>'
                   f'<path d="M{dx1 - 24},180 L{dx1 - 4},180" stroke="{sh}" stroke-width="2" stroke-linecap="round"/>')
    # answer sheet (bubble rows, one filled per row) and pencil
    sheet = 'M404,166.5 L470,166.5 L474,176.5 L400,176.5 Z'
    rows = ''
    for i, (y, pick) in enumerate(((169.4, 1), (171.9, 3), (174.4, 0))):
        for j in range(4):
            xx = 414 + j * 9 + (y - 166.5) * -.4 + (i * 0)
            fill = f'fill="{INK["blue_deep"]}"' if j == pick else f'fill="none" stroke="{p["paper_line"]}" stroke-width=".8"'
            rows += f'<ellipse cx="{fmt(xx)}" cy="{fmt(y)}" rx="2.6" ry="1" {fill}/>'
    sc.body.append(f'<path d="{sheet}" fill="{p["paper"]}" {stroke(p, .8)}/>' + rows +
                   f'<path d="M452,170 L470,168" stroke="{p["paper_line"]}" stroke-width="1.2" stroke-linecap="round"/>'
                   f'<path d="M478,173 L506,167" stroke="{p["line"]}" stroke-width="4.4" stroke-linecap="round"/>'
                   f'<path d="M478,173 L506,167" stroke="{p["gold"]}" stroke-width="2.4" stroke-linecap="round"/>'
                   f'<path d="M506,167 L509,166.4" stroke="{p["coral"]}" stroke-width="2.4" stroke-linecap="round"/>')
    # shell stopwatch on the desk
    wx, wy = 522, 150
    ribs = ''.join(f'M{fmt(wx + 13 * math.cos(math.radians(a)))},{fmt(wy + 13 * math.sin(math.radians(a)))} '
                   f'L{fmt(wx + 10 * math.cos(math.radians(a)))},{fmt(wy + 10 * math.sin(math.radians(a)))} ' for a in range(0, 360, 30))
    sc.body.append(f'<rect x="{wx - 3}" y="{wy - 19}" width="6" height="6" rx="1.5" fill="{p["gold"]}" {stroke(p, .8)}/>'
                   f'<path d="M{wx + 9},{wy - 14} l4,-4" stroke="{p["gold_dk"]}" stroke-width="2.4" stroke-linecap="round"/>'
                   f'<circle cx="{wx}" cy="{wy}" r="14" fill="{mix(p["coral"], p["pearl"], .72)}" {st}/>'
                   f'<path d="{ribs}" stroke="{mix(p["coral"], p["pearl"], .45)}" stroke-width="1.6"/>'
                   f'<circle cx="{wx}" cy="{wy}" r="9" fill="{p["paper"]}" {stroke(p, .8)}/>'
                   f'<path d="M{wx},{wy} L{wx},{wy - 6.5} M{wx},{wy} L{wx + 4.5},{wy + 2}" stroke="{p["line"]}" stroke-width="1.6" stroke-linecap="round"/>'
                   f'<path d="M{wx},{wy} L{wx},{wy - 9} A9,9 0 0 1 {fmt(wx + 9 * math.cos(math.radians(-30)))},{fmt(wy + 9 * math.sin(math.radians(-30)))} Z" '
                   f'fill="{INK["quiz_green"]}" fill-opacity=".3"/>')
    # the turtle examiner
    sc.body.append(sc.shadow(640, FLOOR, 46))
    sc.body.append(_turtle(p, 632, FLOOR))
    sc.body.append(sc.bubbles(612, 100, 40, 3.2, n=3, seed=2))
    sc.body.append(_sparkle(560, 128, 4.2, p['gold_hi'] if not dark else p['gold'], .9) + _sparkle(364, 92, 3.4, p['gold_hi'] if not dark else p['gold'], .8))
    sc.body.append(sc.school(176, 104, 16, 'blue', n=4, flip=True, seed=3))
    sc.over.append(_reef_left(sc))
    sc.over.append(sc.anemone(772, 15) + sc.coral(836, .4) + sc.seaweed(864, 96, p['weed_light'], width=4, phase=2.5))
    return sc.render()


# ------------------------------------------------------------------------------------------------------------ _system/pdf
def scene_press(dark=False):
    """_system/pdf, "Field guide PDFs": a hand printing press with a big wheel turns blank templates into ocean-styled pages
    that stack up and are bound into a yellow field guide; the Diver bot waves beside the pile."""
    sc = Scene('_system-pdf', dark, seed=73, avoid=[(290, 760)], rays=6, glow=(460, -30, 380))
    p = sc.p
    st = stroke(p)
    blue = INK['wave_front']
    blue_dk = mix(blue, p['line'], .4)
    sc.under.append(sc.far_school(170, 70, 14, n=5, flip=True, seed=1))
    px0, px1 = 352, 512
    sc.body.append(sc.shadow((px0 + px1) / 2, FLOOR, 100))
    # feed tray with blank templates, on the left
    sc.body.append(f'<path d="M292,200 L352,192" stroke="{p["metal_dk"]}" stroke-width="5" stroke-linecap="round"/>'
                   f'<path d="M298,201 L296,{FLOOR}" stroke="{p["metal_dk"]}" stroke-width="4" stroke-linecap="round"/>')
    for i in range(3):
        sc.body.append(f'<g transform="translate({314 + i * 3},{184 - i * 3}) rotate(-8)">'
                       f'<rect x="-16" y="-4" width="34" height="6" rx="1.5" fill="{p["paper"]}" {stroke(p, .9)}/></g>')
    sc.body.append(f'<g transform="translate(318,128) rotate(-10)"><rect x="-15" y="-20" width="30" height="40" rx="2.5" fill="{p["paper"]}" {st}/>'
                   f'<rect x="-11" y="-16" width="22" height="32" rx="1.5" fill="none" stroke="{p["paper_line"]}" stroke-width="1.2" stroke-dasharray="3 2.4"/></g>')
    # press: base, columns, head, screw, platen
    sc.body.append(f'<rect x="{px0}" y="194" width="{px1 - px0}" height="{FLOOR - 194}" rx="5" fill="{blue_dk}" {st}/>'
                   f'<rect x="{px0 + 14}" y="186" width="{px1 - px0 - 28}" height="9" rx="2" fill="{p["metal"]}" {st}/>'
                   f'<rect x="{px0 + 22}" y="180" width="{px1 - px0 - 44}" height="6" rx="1" fill="{p["paper"]}" {stroke(p, .8)}/>')
    for x in (px0 + 10, px1 - 26):
        sc.body.append(f'<rect x="{x}" y="86" width="16" height="108" rx="3" fill="{blue}" {st}/>'
                       f'<path d="M{x + 4},92 L{x + 4},188" stroke="{mix(blue, "#ffffff", .4)}" stroke-width="2.4" stroke-linecap="round"/>')
    mx = (px0 + px1) / 2
    sc.body.append(f'<rect x="{mx - 5}" y="98" width="10" height="44" fill="{p["metal"]}" {st}/>'
                   f'<path d="M{mx - 5},106 L{mx + 5},110 M{mx - 5},114 L{mx + 5},118 M{mx - 5},122 L{mx + 5},126 M{mx - 5},130 L{mx + 5},134" stroke="{p["metal_dk"]}" stroke-width="1.6"/>'
                   f'<rect x="{px0 + 30}" y="142" width="{px1 - px0 - 60}" height="16" rx="3" fill="{p["metal"]}" {st}/>'
                   f'<rect x="{px0 + 30}" y="154" width="{px1 - px0 - 60}" height="4" fill="{p["metal_dk"]}"/>'
                   f'<rect x="{px0 - 4}" y="74" width="{px1 - px0 + 8}" height="26" rx="7" fill="{blue}" {st}/>'
                   f'<path d="M{px0 + 4},82 L{px1 - 30},82" stroke="{mix(blue, "#ffffff", .4)}" stroke-width="2.4" stroke-linecap="round"/>'
                   f'<rect x="{mx - 14}" y="80" width="28" height="12" rx="3" fill="{p["gold"]}" {stroke(p, .9)}/>')
    # the big wheel on the right side of the press
    wx, wy, wr = 528, 128, 36
    spokes = ' '.join(f'M{wx},{wy} L{fmt(wx + wr * math.cos(math.radians(a)))},{fmt(wy + wr * math.sin(math.radians(a)))}' for a in range(15, 360, 60))
    knobs = ''.join(f'<circle cx="{fmt(wx + (wr + 6) * math.cos(math.radians(a)))}" cy="{fmt(wy + (wr + 6) * math.sin(math.radians(a)))}" r="4.4" '
                    f'fill="{p["gold"]}" {stroke(p, .9)}/>' for a in range(15, 360, 60))
    sc.body.append(f'<path d="{spokes}" stroke="{p["line"]}" stroke-width="6.4" stroke-linecap="round"/>'
                   f'<path d="{spokes}" stroke="{p["metal"]}" stroke-width="3.6" stroke-linecap="round"/>' + knobs +
                   f'<circle cx="{wx}" cy="{wy}" r="{wr}" fill="none" stroke="{p["line"]}" stroke-width="9.6"/>'
                   f'<circle cx="{wx}" cy="{wy}" r="{wr}" fill="none" stroke="{p["metal"]}" stroke-width="6.4"/>'
                   f'<path d="M{wx - wr * .7:.1f},{wy - wr * .7:.1f} A{wr},{wr} 0 0 1 {wx + wr * .5:.1f},{wy - wr * .86:.1f}" fill="none" stroke="{p["metal_hi"]}" stroke-width="2" stroke-linecap="round"/>'
                   f'<circle cx="{wx}" cy="{wy}" r="8" fill="{p["gold"]}" {st}/><circle cx="{wx}" cy="{wy}" r="2.6" fill="{p["line"]}"/>')
    # printed pages: one drifting out, the stack, and the bound guide
    sc.body.append(_ocean_page(p, 586, 92, 10, 30, 40))
    sx = 628
    sc.body.append(sc.shadow(sx, FLOOR, 40))
    for i in range(7):
        y = FLOOR - 4 - i * 4.2
        sc.body.append(f'<rect x="{sx - 30 + (i % 2) * 1.5}" y="{fmt(y)}" width="58" height="4.2" rx="1.2" fill="{p["paper"] if i % 2 else p["paper_sh"]}" {stroke(p, .7)}/>')
    sc.body.append(_guide(p, sx + 2, 180, -4, .8))
    sc.body.append(_ocean_page(p, sx - 36, 204, -10, 24, 32))
    for x, y, r in ((566, 60, 4.2), (668, 112, 3.6), (606, 140, 3)):
        sc.body.append(_sparkle(x, y, r, p['gold_hi'] if not dark else p['gold'], .85))
    sc.body.append(sc.shadow(708, FLOOR, 38))
    sc.body.append(sc.bot('wave', 712, FLOOR, flip=True))
    sc.body.append(sc.bubbles(434, 66, 40, 3.2, n=3, seed=2))
    sc.body.append(sc.school(200, 100, 16, 'blue', n=4, flip=True, seed=3))
    sc.over.append(_reef_left(sc))
    sc.over.append(sc.coral(842, .36) + sc.seaweed(866, 94, p['weed_light'], width=4, phase=1.7))
    return sc.render()


SCENES = {
    '60-outputs': scene_outputs,
    '60-outputs-content': scene_content,
    '60-outputs-dev': scene_dev,
    '60-outputs-pdf': scene_guides,
    '_system': scene_system,
    '_system-brand': scene_brand,
    '_system-eval': scene_eval,
    '_system-pdf': scene_press,
}
