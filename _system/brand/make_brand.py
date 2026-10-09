"""Render the brand assets used by the READMEs: the hero banners, the section divider, the palette strip and the README icons.

    python _system/brand/make_brand.py              # both styles: the DEFAULT style of _system/theme.yaml under the canonical
                                                    # names, the other style with its name in the file (see below), and icons/
    python _system/brand/make_brand.py --out DIR    # writes them to DIR instead
    python _system/brand/make_brand.py --style deep-dive
                                                    # one style only (art-deco or deep-dive), under the names the default gives it
    python _system/brand/make_brand.py --preview    # also writes <out>/_build/preview-*.png: the banners, the divider and the
                                                    # icons on GitHub's light (#ffffff) and dark (#0d1117) page, 800 px wide
    python _system/brand/make_brand.py --covers     # only renders page 1 of each built field guide (Deep Dive and Art Deco
                                                    # editions in 60-outputs/pdf) to covers/dayN-<edition>.png

File names follow the default style, so flipping `default:` in _system/theme.yaml and running this script again flips every
README (they only ever reference the canonical names):
    default style   banner-light.png, banner-dark.png, divider.svg, palette.svg
    other style     banner-<style>-light.png, banner-<style>-dark.png, divider-<style>.svg, palette-<style>.svg
                    (with deep-dive as the default: banner-art-deco-light.png, divider-art-deco.svg, ...)
A style's file under its other name is deleted when the style is written, so no binary is ever kept twice.

The Deep Dive set (the default) puts the text on open, sunlit water beside original underwater artwork from
_system/ocean_art.py: a reef school, a seabed with seaweed, coral and an anemone, and the Diver bot (our own robot snorkel
diver, ocean_art.diver_bot) waving from the seabed; the dark banner is the same scene in night water. Figtree throughout.
The Art Deco set is drawn exactly as before (same bytes): gold rays and stepped frames on cream or onyx.
icons/*.svg are small flat README icons (24 px, 64-unit viewBox) in Deep Dive colours that keep at least 3:1 contrast on
GitHub's white and on its dark #0d1117: the Diver bot's head, fish, bubbles, boat, coral, map, compass, anchor, book, lock,
code, starfish, seaweed and wave.

The banners are drawn as HTML + inline SVG and photographed by Chromium (Playwright) at device scale 2, so a
800 x 210 layout becomes a 1600 x 420 PNG that stays sharp on high-density screens. Only the bundled fonts in
_system/pdf/fonts/ are used, embedded as data URLs; every other request is blocked, so the render needs no network.
The Art Deco PNGs are reduced to a palette with Pillow (256 colours, or 192, 128, 96 if needed); the Deep Dive PNGs keep full
colour (their water gradients would band) unless that passes the limit. Every PNG must stay under 300 KB. The Art Deco divider
is the web edition's ornament (lines and a diamond) in gold; the Deep Dive divider is a two-layer wave line either side of a
glossy bubble, in mid blues that read on light and dark pages. Each palette strip shows its style's colours for
_system/brand/README.md. Two runs give byte-identical files.
"""
import argparse, base64, io, math, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / 'pdf' / 'fonts'
W, H, SCALE = 800, 210, 2          # CSS px; the PNG is W*SCALE x H*SCALE
MAX_BYTES = 300 * 1024

ONYX, CREAM = '#1a1712', '#f7f1e3'
GOLD, GOLD_D, GOLD_L = '#b08d3a', '#8a6d25', '#d9c08a'

EYEBROW = 'Search Central Live &nbsp;·&nbsp; Deep Dive Europe 2026'
TITLE_SMALL, TITLE = 'The', 'Knowledge Base'
LINE = 'An independent attendee knowledge base &nbsp;·&nbsp; Barcelona &nbsp;·&nbsp; 30 Sep – 2 Oct 2026'
DAYS = ('Crawling', 'Indexing', 'Serving')

# family -> [(weight, file)]: the faces the banner uses, latin subsets only. Every character on the banner is in them;
# a missing glyph would fall back to a system font, so keep the banner text to Latin-1 plus the en dash.
FONT_FILES = {
    'Poiret One': [(400, 'poiret-one-latin-400-normal.woff2')],
    'Italiana': [(400, 'italiana-latin-400-normal.woff2')],
    'Josefin': [(600, 'josefin-sans-latin-600-normal.woff2')],
    'Jost': [(400, 'jost-latin-400-normal.woff2')],
}

THEMES = {
    'dark': dict(bg=ONYX, panel=ONYX, ray=GOLD, ray_op=(0.34, 0.17), arch=GOLD, arch_op=0.62, glow=0.30, fade=0.8, sun=GOLD, sun_op=1,
                 frame=GOLD, frame_in=GOLD_D, eyebrow=GOLD_L, title=CREAM, small=GOLD_L, accent=GOLD, line='#ddd3bf',
                 days=GOLD_L, sep=GOLD),
    'light': dict(bg=CREAM, panel=CREAM, ray=GOLD, ray_op=(0.52, 0.28), arch=GOLD, arch_op=0.78, glow=0.24, fade=0.6, sun=GOLD, sun_op=1,
                  frame=GOLD, frame_in=GOLD, eyebrow=GOLD_D, title=ONYX, small=GOLD_D, accent=GOLD_D, line='#3a342b',
                  days=GOLD_D, sep=GOLD),
}


def font_css():
    out = []
    for family, faces in FONT_FILES.items():
        for weight, name in faces:
            data = base64.b64encode((FONTS / name).read_bytes()).decode('ascii')
            out.append(f"@font-face {{ font-family: '{family}'; font-weight: {weight}; font-display: block; "
                       f"src: url(data:font/woff2;base64,{data}) format('woff2'); }}")
    return '\n'.join(out)


def stepped(x, y, w, h, s):
    """Path of a rectangle whose four corners are stepped inwards by s (the Art Deco frame of the PDF covers)."""
    r, b = x + w, y + h
    return (f'M{x+s} {y}H{r-s}V{y+s}H{r}V{b-s}H{r-s}V{b}H{x+s}V{b-s}H{x}V{y+s}H{x+s}Z')


def diamond(cx, cy, r, fill):
    return f'<path d="M{cx} {cy-r}L{cx+r} {cy}L{cx} {cy+r}L{cx-r} {cy}Z" fill="{fill}"/>'


def ornament(width, color):
    """The web edition's ornament (two rules either side of a diamond flanked by two small open diamonds)."""
    c = width / 2
    return (f'<svg class="orn" viewBox="0 0 {width} 20" width="{width}" height="20" aria-hidden="true">'
            f'<path d="M0 10H{c-21}M{c+21} 10H{width}" stroke="{color}" stroke-width="1"/>'
            f'<path d="M18 14.5H{c-25}M{c+25} 14.5H{width-18}" stroke="{color}" stroke-width=".5"/>'
            f'<path d="M{c} 1l9 9-9 9-9-9z" fill="{color}"/>'
            f'<path d="M{c-16} 10l4-4 4 4-4 4zM{c+8} 10l4-4 4 4-4 4z" fill="none" stroke="{color}" stroke-width=".8"/></svg>')


PANEL = (128, 22, 544, 158)   # x, y, w, h of the framed text panel


def art(t):
    """Background: glow, sunburst rays and stepped arches rising from the bottom centre, the outer frame."""
    cx, cy = W / 2, H + 6
    p = [f'<svg class="art" viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-hidden="true">',
         '<defs>'
         f'<radialGradient id="glow" cx="50%" cy="100%" r="62%"><stop offset="0" stop-color="{GOLD}" stop-opacity="{t["glow"]}"/>'
         f'<stop offset="1" stop-color="{t["bg"]}" stop-opacity="0"/></radialGradient>'
         f'<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["bg"]}" stop-opacity="{t["fade"]}"/>'
         f'<stop offset=".55" stop-color="{t["bg"]}" stop-opacity=".2"/><stop offset="1" stop-color="{t["bg"]}" stop-opacity="0"/></linearGradient>'
         '</defs>',
         f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
         f'<rect width="{W}" height="{H}" fill="url(#glow)"/>']
    n = 64
    for i in range(1, n):
        a = math.pi * i / n
        x2, y2 = cx - math.cos(a) * 1000, cy - math.sin(a) * 1000
        major = i % 2 == 0
        p.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{t["ray"]}" '
                 f'stroke-width="{0.9 if major else 0.5}" stroke-opacity="{t["ray_op"][0 if major else 1]}"/>')
    for k, r in enumerate((54, 66, 78, 150, 200, 262, 336, 420)):
        sw = 1.6 if k in (0, 3) else 0.7
        p.append(f'<path d="M{cx-r} {cy}A{r} {r} 0 0 1 {cx+r} {cy}" fill="none" stroke="{t["arch"]}" '
                 f'stroke-width="{sw}" stroke-opacity="{t["arch_op"]}"/>')
    p.append(f'<rect width="{W}" height="{H}" fill="url(#fade)"/>')
    # the rising sun breaks the bottom of the outer frame: the frame is masked out in a ring just wider than the sun
    sun_r = 40
    p.append(f'<mask id="gap" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#fff"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{sun_r + 5}" fill="#000"/></mask>')
    p.append(f'<path d="M{cx-sun_r} {cy}A{sun_r} {sun_r} 0 0 1 {cx+sun_r} {cy}Z" fill="{t["sun"]}" fill-opacity="{t["sun_op"]}"/>')
    # outer frame: a stepped double rule with diamonds in the corners
    p.append(f'<g mask="url(#gap)" fill="none" stroke="{t["frame"]}">'
             f'<path d="{stepped(6, 6, W-12, H-12, 11)}" stroke-width="1.1"/>'
             f'<path d="{stepped(10.5, 10.5, W-21, H-21, 8)}" stroke-width=".5"/></g>')
    for x, y in ((11.5, 11.5), (W - 11.5, 11.5), (11.5, H - 11.5), (W - 11.5, H - 11.5)):
        p.append(diamond(x, y, 3, t['frame']))
    # the text panel: solid, with its own stepped double frame
    x, y, w, h = PANEL
    p.append(f'<path d="{stepped(x, y, w, h, 9)}" fill="{t["panel"]}"/>')
    p.append(f'<path d="{stepped(x, y, w, h, 9)}" fill="none" stroke="{t["frame"]}" stroke-width="1"/>')
    p.append(f'<path d="{stepped(x+5, y+5, w-10, h-10, 6)}" fill="none" stroke="{t["frame_in"]}" stroke-width=".5"/>')
    p.append('</svg>')
    return ''.join(p)


def page(theme):
    t = THEMES[theme]
    x, y, w, h = PANEL
    sep = f'<svg class="sep" viewBox="0 0 8 8" width="8" height="8" aria-hidden="true">{diamond(4, 4, 3.4, t["sep"])}</svg>'
    days = sep.join(f'<span>{d}</span>' for d in DAYS)
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
{font_css()}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: {t["bg"]}; }}
.stage {{ position: relative; width: {W}px; height: {H}px; }}
.art {{ position: absolute; inset: 0; }}
.text {{ position: absolute; left: {x}px; top: {y}px; width: {w}px; height: {h}px; display: flex; flex-direction: column;
        align-items: center; justify-content: center; text-align: center; padding-bottom: 2px; }}
.eyebrow {{ font: 600 9.6px/1 'Josefin'; letter-spacing: .34em; text-transform: uppercase; color: {t["eyebrow"]}; margin-right: -.34em; }}
.title {{ margin-top: 10px; line-height: 1; white-space: nowrap; }}
.title .small {{ font: 400 27px/1 'Italiana'; color: {t["small"]}; letter-spacing: .02em; margin-right: 10px; }}
.title .big {{ font: 400 39px/1 'Poiret One'; color: {t["title"]}; letter-spacing: .12em; text-transform: uppercase; margin-right: -.12em; }}
.orn {{ display: block; margin: 7px auto 7px; }}
.line {{ font: 400 12.4px/1.3 'Jost'; color: {t["line"]}; letter-spacing: .01em; }}
.days {{ margin-top: 10px; font: 600 8.6px/1 'Josefin'; letter-spacing: .38em; text-transform: uppercase; color: {t["days"]};
        display: flex; align-items: center; gap: 12px; }}
.days span {{ margin-right: -.38em; }}
.sep {{ display: block; }}
</style></head><body><div class="stage">{art(t)}
<div class="text">
  <div class="eyebrow">{EYEBROW}</div>
  <div class="title"><span class="small">{TITLE_SMALL}</span><span class="big">{TITLE}</span></div>
  {ornament(220, t["accent"])}
  <div class="line">{LINE}</div>
  <div class="days">{days}</div>
</div></div></body></html>'''


def divider_svg():
    """600 x 24 gold ornament on a transparent background, readable on light and dark pages."""
    w, h, c, y = 600, 24, 300, 12
    g = GOLD
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Ornamental divider">'
            '<title>Ornamental divider</title>'
            '<defs>'
            f'<linearGradient id="l" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{c}" y2="0">'
            f'<stop offset="0" stop-color="{g}" stop-opacity="0"/><stop offset=".55" stop-color="{g}"/></linearGradient>'
            f'<linearGradient id="r" gradientUnits="userSpaceOnUse" x1="{w}" y1="0" x2="{c}" y2="0">'
            f'<stop offset="0" stop-color="{g}" stop-opacity="0"/><stop offset=".55" stop-color="{g}"/></linearGradient>'
            '</defs>'
            f'<path d="M0 {y}H{c-27}" stroke="url(#l)" stroke-width="1.4"/>'
            f'<path d="M{c+27} {y}H{w}" stroke="url(#r)" stroke-width="1.4"/>'
            f'<path d="M40 {y+5}H{c-31}" stroke="url(#l)" stroke-width=".8"/>'
            f'<path d="M{c+31} {y+5}H{w-40}" stroke="url(#r)" stroke-width=".8"/>'
            f'<path d="M{c} {y-10}L{c+10} {y}L{c} {y+10}L{c-10} {y}Z" fill="{g}"/>'
            f'<path d="M{c-22} {y}l5-5 5 5-5 5zM{c+12} {y}l5-5 5 5-5 5z" fill="none" stroke="{g}" stroke-width="1.1"/>'
            '</svg>\n')


PALETTE = (('Onyx', ONYX), ('Cream', CREAM), ('Gold', GOLD), ('Dark gold', GOLD_D), ('Light gold', GOLD_L))


def palette_svg():
    """Five swatches with stepped corners and a gold hairline, so cream shows on white and onyx on a dark page."""
    sw, sh, gap = 64, 40, 16
    w = len(PALETTE) * sw + (len(PALETTE) - 1) * gap
    names = ', '.join(name.lower() for name, _ in PALETTE)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {sh}" width="{w}" height="{sh}" role="img" '
         f'aria-label="Brand palette, left to right: {names}"><title>Brand palette, left to right: {names}</title>']
    for i, (_, colour) in enumerate(PALETTE):
        x = i * (sw + gap)
        p.append(f'<path d="{stepped(x + .5, .5, sw - 1, sh - 1, 5)}" fill="{colour}" stroke="{GOLD}"/>')
    p.append('</svg>\n')
    return ''.join(p)


# ------------------------------------------------------------------ Deep Dive: the same text, under water
# Original artwork from _system/ocean_art.py (never the event's logo or slide template): sunlit water with soft rays, a two-layer
# surface, a school of reef fish with two companions, rising bubbles and a layered seabed with seaweed, coral and an anemone.
# The text sits on the open water on the left; the life keeps to the right and the bottom. Figtree, as in the Deep Dive edition.
DD_FONT_FILES = {'Figtree': [(400, 'figtree-latin-400-normal.woff2'), (700, 'figtree-latin-700-normal.woff2'),
                             (800, 'figtree-latin-800-normal.woff2')]}
DD_TEXT_X = 54                      # CSS px: left edge of the text block
BOT_X, BOT_FLOOR, BOT_H = 566, 192, 128   # CSS px: the Diver bot's centre line, the seabed line under its fins, its height
BOT_FISH = (512, 40)                # a small red fish swimming ahead of the bot, above the end of the title

DD_THEMES = {
    'light': dict(water=(('0', '#f7faff'), ('.22', '#eff5fe'), ('.55', '#e1ecfb'), ('1', '#c9daf6')), glow='#ffffff', glow_op=.95,
                  ray_op=.55, eyebrow='#2152c4', title='#262d3b', accent='#2f6fe0', line='#3b4354', days='#2152c4', rule='#9fc0f2',
                  sep='#6f9be6', far_fish='#b4c2ec', bubble=dict(fill_op=.6), panel='#ffffff'),
    'dark': dict(water=(('0', '#2a5fcf'), ('.2', '#1f4bb4'), ('.52', '#16357f'), ('1', '#0c1f4f')), glow='#bcd6ff', glow_op=.38,
                 ray_op=.2, eyebrow='#a9c6ff', title='#ffffff', accent='#8fb8ff', line='#d5def2', days='#a9c6ff', rule='#4f7fd8',
                 sep='#6fa3ff', far_fish='#3a63c0', bubble=dict(stroke='#9cc0ff', fill='#cfe0ff', fill_op=.16), panel='#0f2148'),
}


def _place(svg, x, y, w, h):
    """Position a complete ocean_art <svg> (it carries only a viewBox) inside the banner's own SVG."""
    assert svg.startswith('<svg viewBox=')
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}"' + svg[4:]


def dd_art(theme):
    """The Deep Dive banner background, 800 x 210 CSS px; deterministic (ocean_art draws from fixed seeds, never the clock)."""
    sys.path.insert(0, str(HERE.parent))
    import ocean_art as oa
    t, dark = DD_THEMES[theme], theme == 'dark'
    pal = dict(oa.DARK if dark else oa.PALETTE)
    p = [f'<svg class="art" viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-hidden="true">',
         '<defs><linearGradient id="dd-water" x1="0" y1="0" x2="0" y2="1">'
         + ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in t['water']) + '</linearGradient>'
         f'<radialGradient id="dd-glow" cx="50%" cy="0%" r="70%"><stop offset="0" stop-color="{t["glow"]}" stop-opacity="{t["glow_op"]}"/>'
         f'<stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/></radialGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#dd-water)"/>',
         f'<ellipse cx="560" cy="0" rx="420" ry="190" fill="url(#dd-glow)"/>',
         _place(oa.light_rays(W, H, f'dd-{theme}', seed=11, n=8, opacity=t['ray_op'], reach=.95), 0, 0, W, H)]
    # far, faint fish beyond the school
    p.append(oa.fish_school(744, 40, 10, t['far_fish'], n=4, seed='brand-far', mono=True))
    # the seabed: monochrome layers, decoration kept away from the text block
    p.append(_place(oa.seabed(W, 76, 'slim', seed=31, dark=dark, band=False, avoid=[(0, 520), (BOT_X - 52, BOT_X + 52)]), 0, H - 64, W, 76))
    # reef colour in the corners
    p.append(oa.seaweed(16, H + 4, 74, pal['weed'], width=5.6, amp=5, wl=50, phase=.4))
    p.append(oa.seaweed(29, H + 4, 50, pal['weed_light'], width=4.4, amp=4, wl=44, phase=2.2))
    p.append(oa.anemone(690, H + 1, 20, pal=pal))
    p.append(oa.branch_coral(748, H + 2, .38, pal['coral'], width=4.6))
    p.append(oa.seaweed(781, H + 4, 46, pal['weed'], width=4.4, amp=4, wl=42, phase=1.1))
    # bubbles rising from the reef
    p.append(oa.bubble_trail(737, 150, 96, 4.8, n=5, seed='brand-a', pal=pal, **t['bubble']))
    # the school, heading left towards the text, and two companions
    p.append(oa.fish_school(622, 72, 16.5, 'blue', n=7, seed='brand', pal=pal))
    p.append(oa.fish(700, 120, 38, 'yellow', pal=pal))
    p.append(oa.fish(BOT_FISH[0], BOT_FISH[1], 20, 'red', flip=True, pal=pal))
    # the Diver bot stands on the seabed between the text and the reef, waving at the reader (night water: dark=True)
    bw, bh = oa.diver_bot_box('wave', BOT_H)
    p.append(oa.diver_bot('wave', BOT_X, BOT_FLOOR - bh / 2, BOT_H, f'dd-{theme}-bot', dark=dark, unit_px=1.0))
    # the water surface on top
    p.append(_place(oa.top_wave(W, 16, dark=dark, wl=44), 0, 0, W, 16))
    p.append('</svg>')
    return ''.join(p)


def dd_font_css():
    out = []
    for family, faces in DD_FONT_FILES.items():
        for weight, name in faces:
            data = base64.b64encode((FONTS / name).read_bytes()).decode('ascii')
            out.append(f"@font-face {{ font-family: '{family}'; font-weight: {weight}; font-display: block; "
                       f"src: url(data:font/woff2;base64,{data}) format('woff2'); }}")
    return '\n'.join(out)


def dd_rule(color, bubble):
    """A short wavy rule ending in a small bubble: the Deep Dive answer to the Art Deco ornament."""
    return (f'<svg class="rule" viewBox="0 0 132 12" width="132" height="12" aria-hidden="true">'
            f'<path d="M1 6C5.5 2.4 10 2.4 14.5 6S23.5 9.6 28 6 37 2.4 41.5 6 50.5 9.6 55 6 64 2.4 68.5 6 77.5 9.6 82 6 91 2.4 95.5 6 104.5 9.6 109 6"'
            f' fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
            f'<circle cx="122" cy="6" r="4.4" fill="none" stroke="{bubble}" stroke-width="1.5"/>'
            f'<path d="M122.6 3.4A2.7 2.7 0 0 1 124.7 5.4" fill="none" stroke="{bubble}" stroke-width="1.1" stroke-linecap="round"/></svg>')


def dd_page(theme):
    t = DD_THEMES[theme]
    sep = (f'<svg class="sep" viewBox="0 0 10 10" width="10" height="10" aria-hidden="true">'
           f'<circle cx="5" cy="5" r="3.2" fill="none" stroke="{t["sep"]}" stroke-width="1.3"/></svg>')
    days = sep.join(f'<span>{d}</span>' for d in DAYS)
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
{dd_font_css()}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: {t["panel"]}; }}
.stage {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; }}
.art {{ position: absolute; inset: 0; }}
.text {{ position: absolute; left: {DD_TEXT_X}px; top: 16px; height: 150px; display: flex; flex-direction: column; justify-content: center;
        font-family: 'Figtree'; }}
.eyebrow {{ font-weight: 700; font-size: 9.4px; line-height: 1; letter-spacing: .17em; text-transform: uppercase; color: {t["eyebrow"]}; }}
.title {{ margin-top: 9px; font-weight: 800; font-size: 40px; line-height: 1; letter-spacing: -.018em; color: {t["title"]}; white-space: nowrap; }}
.title em {{ font-style: normal; color: {t["accent"]}; }}
.rule {{ display: block; margin: 11px 0 10px; }}
.line {{ font-weight: 400; font-size: 12.6px; line-height: 1.3; color: {t["line"]}; }}
.days {{ margin-top: 9px; font-weight: 700; font-size: 8.6px; line-height: 1; letter-spacing: .2em; text-transform: uppercase; color: {t["days"]};
        display: flex; align-items: center; gap: 9px; }}
.sep {{ display: block; }}
</style></head><body><div class="stage">{dd_art(theme)}
<div class="text">
  <div class="eyebrow">{EYEBROW}</div>
  <div class="title">{TITLE_SMALL} <em>{TITLE}</em></div>
  {dd_rule(t["rule"], t["sep"])}
  <div class="line">{LINE}</div>
  <div class="days">{days}</div>
</div></div></body></html>'''


def dd_divider_svg():
    """600 x 24 Deep Dive divider: a soft wave line either side of a glossy bubble with two small ones rising, on a transparent
    ground. Mid blues read on GitHub's white and its dark #0d1117."""
    w, h, c, y = 600, 24, 300, 13
    blue, lite = '#3f7fe6', '#7ea6ec'

    def wave(x0, x1):
        n, step = 0, 9.0                                  # quarter wavelength (one wave = 36 px)
        x = x0
        d = [f'M{x0} {y}']
        while x + 2 * step <= x1 + .01:
            k = -1 if n % 2 == 0 else 1
            d.append(f'Q{x + step:g} {y + 3.2 * k:g} {x + 2 * step:g} {y}')
            x += 2 * step; n += 1
        return ''.join(d)
    left, right = wave(c - 24 - 252, c - 24), wave(c + 24, c + 24 + 252)
    back_l, back_r = wave(c - 24 - 216, c - 24 - 18), wave(c + 24 + 18, c + 24 + 216)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Wave divider">'
            '<title>Wave divider</title>'
            '<defs>'
            f'<linearGradient id="dl" gradientUnits="userSpaceOnUse" x1="{c - 276}" y1="0" x2="{c - 24}" y2="0">'
            f'<stop offset="0" stop-color="{lite}" stop-opacity="0"/><stop offset=".6" stop-color="{lite}"/><stop offset="1" stop-color="{blue}"/></linearGradient>'
            f'<linearGradient id="dr" gradientUnits="userSpaceOnUse" x1="{c + 276}" y1="0" x2="{c + 24}" y2="0">'
            f'<stop offset="0" stop-color="{lite}" stop-opacity="0"/><stop offset=".6" stop-color="{lite}"/><stop offset="1" stop-color="{blue}"/></linearGradient>'
            f'<radialGradient id="db" cx=".38" cy=".32" r=".8"><stop offset="0" stop-color="#9cc2ff"/><stop offset=".55" stop-color="#3f7fe6"/>'
            f'<stop offset="1" stop-color="#2152c4"/></radialGradient>'
            '</defs>'
            f'<g transform="translate(9 4)" opacity=".45"><path d="{back_l}" fill="none" stroke="url(#dl)" stroke-width="1" stroke-linecap="round"/></g>'
            f'<g transform="translate(-9 4)" opacity=".45"><path d="{back_r}" fill="none" stroke="url(#dr)" stroke-width="1" stroke-linecap="round"/></g>'
            f'<path d="{left}" fill="none" stroke="url(#dl)" stroke-width="1.6" stroke-linecap="round"/>'
            f'<path d="{right}" fill="none" stroke="url(#dr)" stroke-width="1.6" stroke-linecap="round"/>'
            f'<circle cx="{c}" cy="{y}" r="8" fill="url(#db)"/>'
            f'<path d="M{c + .6} {y - 5.2}A5.2 5.2 0 0 1 {c + 5.1} {y - 1.4}" fill="none" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round"/>'
            f'<circle cx="{c - 14}" cy="{y - 7}" r="3" fill="none" stroke="{blue}" stroke-width="1.2"/>'
            f'<circle cx="{c + 13.5}" cy="{y - 8.5}" r="2" fill="none" stroke="{blue}" stroke-width="1.1"/>'
            '</svg>\n')


DD_PALETTE = (('Ink', '#262d3b', 1), ('Night water', '#0f2148', 1), ('Deep blue', '#2152c4', 0), ('Ocean blue', '#2f6fe0', 0), ('Wave', '#a9cbf6', 0),
              ('Sky', '#e2edfb', 1), ('Indigo', '#4b56ad', 0), ('Periwinkle', '#a2aee6', 0), None,
              ('Coral', '#ee6a3c', 0), ('Sun', '#f7c443', 0), ('Reef green', '#1fa38a', 0))   # name, colour, hairline (pale or near-black)


def dd_palette_svg():
    """The Deep Dive colours as rounded swatches: water and seabed, then the reef accents after a wider gap. A soft blue
    hairline round the palest and the darkest swatches keeps them visible on a white and on a dark page."""
    sw, sh, gap, group = 44, 40, 10, 26
    xs, x = [], 0
    for item in DD_PALETTE:
        if item is None: x += group - gap; continue
        xs.append((x, item)); x += sw + gap
    w = x - gap
    names = ', '.join(name.lower() for _, (name, _, _) in xs)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {sh}" width="{w}" height="{sh}" role="img" '
         f'aria-label="Deep Dive palette, left to right: {names}"><title>Deep Dive palette, left to right: {names}</title>']
    for x, (_, colour, line) in xs:
        edge = ' stroke="#7ea6ec" stroke-opacity=".75"' if line else ''
        p.append(f'<rect x="{x + .5}" y=".5" width="{sw - 1}" height="{sh - 1}" rx="11" fill="{colour}"{edge}/>')
    p.append('</svg>\n')
    return ''.join(p)


def quantize(png_bytes):
    from PIL import Image
    img = Image.open(io.BytesIO(png_bytes)).convert('RGB')
    for colors in (256, 192, 128, 96):
        q = img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
        buf = io.BytesIO()
        q.save(buf, 'PNG', optimize=True)
        if buf.tell() <= MAX_BYTES:
            return buf.getvalue(), img.size, colors
    raise SystemExit(f'banner is {buf.tell()} bytes even at {colors} colours (limit {MAX_BYTES})')


def full_colour(png_bytes):
    """The Deep Dive banners keep every colour (their soft water gradients band when reduced to a palette): an optimised RGB
    PNG when it fits under MAX_BYTES, otherwise the palette reduction above."""
    from PIL import Image
    img = Image.open(io.BytesIO(png_bytes)).convert('RGB')
    buf = io.BytesIO()
    img.save(buf, 'PNG', optimize=True)
    return (buf.getvalue(), img.size, 'all') if buf.tell() <= MAX_BYTES else quantize(png_bytes)


def check_text():
    """Every banner character must be in the latin subsets embedded above (Latin-1 and the en dash)."""
    from html import unescape
    text = unescape(''.join((EYEBROW, TITLE_SMALL, TITLE, LINE) + DAYS))
    bad = sorted({c for c in text if ord(c) > 0xFF and c != '–'})
    if bad:
        raise SystemExit(f'banner text has characters the bundled latin fonts may not cover: {bad}')


STYLES = ('art-deco', 'deep-dive')


def default_style():
    """The default style named in _system/theme.yaml (read and checked by _system/theme.py)."""
    sys.path.insert(0, str(HERE.parent))
    from theme import default_style as theme_default
    return theme_default()


def names(style, default):
    """File names of one style's set: the canonical names for the default style, the style's own name in every file otherwise."""
    if style not in STYLES or default not in STYLES:
        raise ValueError(f'style must be one of {", ".join(STYLES)}: {style!r}, default {default!r}')
    tag, sfx = ('', '') if style == default else (f'{style}-', f'-{style}')
    return {'light': f'banner-{tag}light.png', 'dark': f'banner-{tag}dark.png', 'divider': f'divider{sfx}.svg', 'palette': f'palette{sfx}.svg'}


def render(out, style='deep-dive', default=None):
    """Draw one style's banners, divider and palette into `out` under the names `default` gives them (theme.yaml's default when
    None) and delete that style's files under its other names; returns {file name: (path, size, bytes, colours)} for the PNGs."""
    from playwright.sync_api import sync_playwright
    check_text()
    default = default or default_style()
    n = names(style, default)
    out.mkdir(parents=True, exist_ok=True)
    if style == 'art-deco':
        pages = [(n[theme], page(theme)) for theme in THEMES]
        svgs = ((n['divider'], divider_svg()), (n['palette'], palette_svg()))
    else:
        pages = [(n[theme], dd_page(theme)) for theme in DD_THEMES]
        svgs = ((n['divider'], dd_divider_svg()), (n['palette'], dd_palette_svg()))
    results = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={'width': W, 'height': H}, device_scale_factor=SCALE)
        ctx.route('**/*', lambda route: route.abort())   # no network: fonts are data URLs, nothing else is loaded
        pg = ctx.new_page()
        for name, html in pages:
            pg.set_content(html, wait_until='load')
            # load every bundled face, then make sure none failed: a failed face would fall back to a system font
            failed = pg.evaluate('''async () => { await Promise.allSettled([...document.fonts].map(f => f.load()));
                await document.fonts.ready;
                return [...document.fonts].filter(f => f.status !== 'loaded').map(f => f.family + ' ' + f.weight); }''')
            if failed:
                raise SystemExit(f'bundled fonts did not load: {failed}')
            png = pg.screenshot(clip={'x': 0, 'y': 0, 'width': W, 'height': H})
            data, size, colors = quantize(png) if style == 'art-deco' else full_colour(png)
            path = out / name
            path.write_bytes(data)
            results[name] = (path, size, len(data), colors)
        browser.close()
    for name, svg in svgs:
        (out / name).write_text(svg, encoding='utf-8', newline='\n')
    # the default style under its own name (left from before the default flipped): deleted, so no binary is kept twice
    if style == default:
        for name in sorted(names(style, next(x for x in STYLES if x != style)).values()):
            (out / name).unlink(missing_ok=True)
    return results


# ------------------------------------------------------------------ README icons: flat, 24 px, Deep Dive colours
# Every edge colour keeps at least 3:1 contrast (WCAG non-text) on GitHub's white #ffffff and on its dark #0d1117:
# blue #2f6fe0 4.7 / 4.0, sky blue #3a8ee6 3.4 / 5.6, light blue #5b92f0 3.1 / 6.1, coral #ee6a3c 3.1 / 6.1, reef green #1fa38a
# 3.2 / 6.0, seaweed #25a07e 3.3 / 5.8. Pale fills (#cfe0fb, #a9cbf6, the guide's yellow #f7c443) only sit inside a blue edge.
IC_BLUE, IC_SKY, IC_LIGHT, IC_CORAL, IC_GREEN, IC_WEED = '#2f6fe0', '#3a8ee6', '#5b92f0', '#ee6a3c', '#1fa38a', '#25a07e'
IC_PALE, IC_WAVE, IC_SUN, IC_NAVY, IC_FIN = '#cfe0fb', '#a9cbf6', '#f7c443', '#2152c4', '#dc5038'
ICON_PX = 24
ICONS = {'bot': 'The Diver bot, our robot snorkel diver', 'fish': 'A reef fish', 'bubble': 'Bubbles', 'boat': 'A paper boat',
         'coral': 'Branching coral', 'map': 'A folded map', 'compass': 'A compass', 'anchor': 'An anchor',
         'book': 'A field guide', 'lock': 'A padlock', 'code': 'Code brackets', 'starfish': 'A starfish',
         'seaweed': 'Seaweed', 'wave': 'Waves'}


def _icon_body(name, oa):
    sm = dict(stroke=IC_SKY, fill=IC_WAVE, fill_op=.5)          # a small companion bubble
    if name == 'bot':
        return oa.diver_bot('head', 32, 32.5, 58, 'icon-bot', unit_px=ICON_PX / 64)
    if name == 'fish':
        return oa.fish(35, 33, 50, 'red', flip=True, fin=IC_FIN) + oa.bubble(8, 16, 4.2, **sm)
    if name == 'bubble':
        out = []
        for cx, cy, r, w in ((25, 41, 16, 3.6), (46, 21, 10, 3.2), (51, 47, 5.6, 2.8)):
            rr = r * .6
            out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{IC_WAVE}" fill-opacity=".55" stroke="{IC_BLUE}" stroke-width="{w}"/>'
                       f'<path d="M{cx + rr * .31:.2f} {cy - rr * .95:.2f}A{rr:.2f} {rr:.2f} 0 0 1 {cx + rr * .95:.2f} {cy - rr * .31:.2f}" '
                       f'fill="none" stroke="{IC_LIGHT}" stroke-width="{max(2.2, r * .2):.1f}" stroke-linecap="round"/>')
        return ''.join(out)
    if name == 'boat':
        return (f'<path d="M30 8V37H11Z" fill="{IC_LIGHT}"/><path d="M34 13V37H51Z" fill="{IC_SKY}"/>'
                f'<path d="M7 40H57C55 46 50 50 44 50H20C14 50 9 46 7 40Z" fill="{IC_BLUE}"/>'
                f'<path d="M4 57.5C9 54 14 54 19 57.5S29 61 34 57.5 44 54 49 57.5 57 60 60 59" fill="none" stroke="{IC_SKY}" '
                f'stroke-width="3.6" stroke-linecap="round"/>')
    if name == 'coral':
        return oa.branch_coral(30, 60, .25, IC_CORAL, width=5.4) + oa.bubble(52, 14, 4.6, **sm) + oa.bubble(46, 26, 2.8, **sm)
    if name == 'map':
        return (f'<path d="M7 15L23 9V51L7 57Z" fill="{IC_PALE}"/><path d="M23 9L41 15V57L23 51Z" fill="{IC_WAVE}"/>'
                f'<path d="M41 15L57 9V51L41 57Z" fill="{IC_PALE}"/>'
                f'<path d="M14 45C19 37 24 40 29 33S37 25 44 27" fill="none" stroke="{IC_CORAL}" stroke-width="3.2" stroke-linecap="round" stroke-dasharray=".5 6"/>'
                f'<path d="M45.5 18.5L53.5 26.5M53.5 18.5L45.5 26.5" stroke="{IC_CORAL}" stroke-width="3.6" stroke-linecap="round"/>'
                f'<path d="M7 15L23 9L41 15L57 9V51L41 57L23 51L7 57Z" fill="none" stroke="{IC_BLUE}" stroke-width="3.6" stroke-linejoin="round"/>')
    if name == 'compass':
        ticks = ''.join(f'<path d="M{32 + 21 * dx:g} {32 + 21 * dy:g}L{32 + 17 * dx:g} {32 + 17 * dy:g}"/>' for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
        return (f'<circle cx="32" cy="32" r="26" fill="{IC_PALE}" stroke="{IC_BLUE}" stroke-width="4"/>'
                f'<g stroke="{IC_BLUE}" stroke-width="2.6" stroke-linecap="round">{ticks}</g>'
                f'<path d="M32 13L38.5 32H25.5Z" fill="{IC_CORAL}"/><path d="M32 51L38.5 32H25.5Z" fill="{IC_NAVY}"/>'
                f'<circle cx="32" cy="32" r="3.4" fill="#ffffff"/>')
    if name == 'anchor':
        return (f'<g fill="none" stroke="{IC_BLUE}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">'
                f'<circle cx="32" cy="11.5" r="5.5"/><path d="M32 17V56M21 25H43"/><path d="M11 38C12 49 21 56 32 56S52 49 53 38"/>'
                f'<path d="M6 43L11 37L16 43M48 43L53 37L58 43"/></g>')
    if name == 'book':
        return (f'<path d="M8 50C8 47.8 9.8 46 12 46H52V58H12C9.8 58 8 56.2 8 54Z" fill="#ffffff" stroke="{IC_BLUE}" stroke-width="3.4" stroke-linejoin="round"/>'
                f'<path d="M12 6H46C49.3 6 52 8.7 52 12V46H12C9.8 46 8 47.8 8 50V10C8 7.8 9.8 6 12 6Z" fill="{IC_SUN}" stroke="{IC_BLUE}" stroke-width="3.4" stroke-linejoin="round"/>'
                f'<path d="M17 8V45" stroke="{IC_BLUE}" stroke-width="3"/>'
                + oa.fish(35.5, 26, 24, 'red', flip=True, fin=IC_FIN))
    if name == 'lock':
        return (f'<path d="M21 29V21C21 14.9 25.9 10 32 10S43 14.9 43 21V29" fill="none" stroke="{IC_SKY}" stroke-width="5.5" stroke-linecap="round"/>'
                f'<rect x="12" y="27" width="40" height="30" rx="8" fill="{IC_BLUE}"/>'
                f'<circle cx="32" cy="39" r="4.6" fill="#ffffff"/><path d="M32 41V48" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>')
    if name == 'code':
        return (f'<g fill="none" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round">'
                f'<path d="M21 17L7 32L21 47M43 17L57 32L43 47" stroke="{IC_BLUE}"/><path d="M37 11L27 53" stroke="{IC_CORAL}"/></g>')
    if name == 'starfish':
        return oa.starfish(32, 34, 28, IC_CORAL, rot=0) + ''.join(
            f'<circle cx="{32 + 9 * dx:.1f}" cy="{34 + 9 * dy:.1f}" r="2.2" fill="#ffffff" fill-opacity=".75"/>'
            for dx, dy in ((0, -1), (.95, -.31), (.59, .81), (-.59, .81), (-.95, -.31)))
    if name == 'seaweed':
        return (oa.seaweed(24, 63, 56, IC_WEED, width=7.5, amp=6, wl=30, phase=.3)
                + oa.seaweed(42, 63, 40, IC_GREEN, width=6.5, amp=5, wl=26, phase=2.1) + oa.bubble(51, 12, 4.4, **sm))
    if name == 'wave':
        def line(y, amp):
            return f'M5 {y}' + ''.join(f'Q{5 + 13.5 * i + 6.75:g} {y + (-amp if i % 2 == 0 else amp)} {5 + 13.5 * (i + 1):g} {y}' for i in range(4))
        return (f'<path d="{line(23, 6)}" fill="none" stroke="{IC_LIGHT}" stroke-width="4.4" stroke-linecap="round"/>'
                f'<path d="{line(41, 6)}" fill="none" stroke="{IC_BLUE}" stroke-width="4.8" stroke-linecap="round"/>')
    raise ValueError(f'unknown icon {name!r}')


def icon_svg(name):
    """One README icon as a complete SVG file, 24 x 24 px (a 64-unit viewBox). The <title> names it; a README that uses it
    beside text gives the <img> an empty alt, since the heading or cell already says what it is."""
    sys.path.insert(0, str(HERE.parent))
    import ocean_art as oa
    title = ICONS[name]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{ICON_PX}" height="{ICON_PX}" role="img" '
            f'aria-label="{title}"><title>{title}</title>{_icon_body(name, oa)}</svg>\n')


def icons(out):
    """Write every icon to out/icons/<name>.svg and return the paths. Pure SVG text: deterministic, no browser needed."""
    sys.path.insert(0, str(HERE.parent))
    from ocean_art import BOT_FORBIDDEN_HEX
    dest = out / 'icons'
    dest.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in ICONS:
        svg = icon_svg(name)
        bad = [h for h in BOT_FORBIDDEN_HEX if h in svg.lower()]
        if bad:
            raise SystemExit(f'icon {name} uses a forbidden colour: {bad}')
        (dest / f'{name}.svg').write_text(svg, encoding='utf-8', newline='\n')
        paths.append(dest / f'{name}.svg')
    return paths


def preview(out, style='deep-dive', default=None):
    """GitHub-like pages (light #ffffff, dark #0d1117, 800 px content column) showing one style's banner and divider and the
    icons in a heading and in a row, as GitHub shows them."""
    from playwright.sync_api import sync_playwright
    default = default or default_style()
    n = names(style, default)
    build = out / '_build'
    build.mkdir(exist_ok=True)
    tag = '' if style == default else f'{style}-'
    ic = lambda k: (out / 'icons' / f'{k}.svg').as_uri()
    row = ''.join(f'<img src="{ic(k)}" width="24" height="24" alt="" style="margin:0 7px">' for k in ICONS)
    h2 = 'style="border-bottom:1px solid #8884;padding-bottom:.3em;font-weight:600;font-size:24px"'
    shots = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg = browser.new_page(viewport={'width': 880, 'height': 520})
        for theme, bg, fg in (('light', '#ffffff', '#1f2328'), ('dark', '#0d1117', '#e6edf3')):
            html = (f'<!doctype html><body style="margin:0;background:{bg};color:{fg};font:16px -apple-system,Segoe UI,sans-serif">'
                    f'<div style="width:800px;margin:24px auto">'
                    f'<img src="{(out / n[theme]).as_uri()}" width="800" alt="">'
                    f'<p style="text-align:center;margin:28px 0"><img src="{(out / n["divider"]).as_uri()}" width="600" alt=""></p>'
                    f'<h2 {h2}><img src="{ic("bot")}" width="24" height="24" alt=""> Two editions</h2>'
                    f'<h2 {h2}><img src="{ic("map")}" width="24" height="24" alt=""> Where things are</h2>'
                    f'<p>{row}</p><p>Body text for scale.</p></div>')
            p = build / f'preview-{tag}{theme}.html'
            p.write_text(html, encoding='utf-8')
            pg.goto(p.as_uri())
            pg.wait_for_timeout(200)
            shot = build / f'preview-{tag}{theme}.png'
            pg.screenshot(path=str(shot), full_page=True)
            shots.append(shot)
        browser.close()
    return shots


# ------------------------------------------------------------------ covers: page 1 of each built field guide, for a README showcase
PDF_DIR = HERE.parent.parent / '60-outputs' / 'pdf'
COVER_RE = re.compile(r'day(\d+)-field-guide-(art-deco|deep-dive)\.pdf')
COVER_W = 720                       # px: wide enough to stay sharp when two covers sit side by side in a README


def covers(out, pdf_dir=PDF_DIR):
    """Render page 1 of every dayN-field-guide-{art-deco,deep-dive}.pdf in pdf_dir to out/covers/dayN-<edition>.png (720 px wide,
    full colour, or reduced to a palette when that is needed to stay under 300 KB). Rendering with pdfium has no clock or randomness, so two runs give
    byte-identical files. The modern edition is left out: the showcase compares the two styled editions."""
    import pypdfium2 as pdfium
    found = sorted((int(m[1]), m[2], p) for p in pdf_dir.glob('*.pdf') if (m := COVER_RE.fullmatch(p.name)))
    if not found:
        raise SystemExit(f'no dayN-field-guide-art-deco.pdf or -deep-dive.pdf in {pdf_dir}: build the field guides first (_system/pdf/make_pdf.py)')
    dest = out / 'covers'
    dest.mkdir(parents=True, exist_ok=True)
    results = []
    for day, edition, p in found:
        doc = pdfium.PdfDocument(str(p))
        try:
            pg = doc[0]
            bitmap = pg.render(scale=COVER_W / pg.get_width(), may_draw_forms=False)
            img = bitmap.to_pil().convert('RGB')
            pg.close()
        finally:
            doc.close()
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        data, size, colors = full_colour(buf.getvalue())
        path = dest / f'day{day}-{edition}.png'
        path.write_bytes(data)
        results.append((path, size, len(data), colors))
    return results


def main():
    sys.stdout.reconfigure(errors='replace')
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--out', default=str(HERE), help='folder for the banners, the divider, the palette and icons/ (default: this folder)')
    ap.add_argument('--style', choices=STYLES + ('all',), default='all',
                    help="which brand set to draw: all (the default: both, named after theme.yaml's default), art-deco or deep-dive")
    ap.add_argument('--default', choices=STYLES, default=None,
                    help="name the files as if theme.yaml's default were this style (default: read _system/theme.yaml)")
    ap.add_argument('--preview', action='store_true', help='also write GitHub-like previews to <out>/_build/')
    ap.add_argument('--covers', action='store_true', help='only render page 1 of each Deep Dive and Art Deco field guide to <out>/covers/')
    ap.add_argument('--pdfs', default=str(PDF_DIR), help='folder holding the field guides for --covers (default: 60-outputs/pdf)')
    args = ap.parse_args()
    out = Path(args.out)
    if args.covers:
        for path, size, n, colors in covers(out, Path(args.pdfs)):
            print(f'OK: covers/{path.name}: {size[0]} x {size[1]} px, {n // 1024} KB, {colors} colours')
        return 0
    default = args.default or default_style()
    styles = sorted(STYLES, key=lambda x: x != default) if args.style == 'all' else [args.style]
    print(f'default style: {default} (it gets the canonical names)')
    for style in styles:
        for name, (path, size, n, colors) in render(out, style, default).items():
            print(f'OK: {name}: {size[0]} x {size[1]} px, {n // 1024} KB, {colors} colours')
        nm = names(style, default)
        print(f'OK: {nm["divider"]}, {nm["palette"]}')
    print(f'OK: icons/: {len(icons(out))} icons')
    if args.preview:
        for style in styles:
            for shot in preview(out, style, default):
                print(f'preview: {shot}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
