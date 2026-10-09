"""Render the share image of the web edition once: _system/brand/social/og-image.png, 1200 x 630.

    python _system/brand/social/make_og_image.py              # writes og-image.png next to this script
    python _system/brand/social/make_og_image.py --out DIR    # writes it to DIR instead

Social sites (LinkedIn, X, Slack, Mastodon ...) show it when a page of the published community edition is shared: the web
edition's Open Graph and Twitter tags point to its copy in assets/social/ (site/build_site.py copies it; it never redraws it).
Run this by hand only when the artwork should change, then commit the PNG.

The same Deep Dive look as the README banner (_system/brand/make_brand.py, whose fonts, wavy rule, colours and text it reuses):
sunlit water with soft rays, a reef school, the seabed with seaweed, coral and an anemone, and the Diver bot (our own robot snorkel
diver from _system/ocean_art.py) waving beside the title. Original artwork only, never the event's logo or slides. Drawn as HTML +
inline SVG at 600 x 315 CSS px and photographed by Chromium (Playwright) at device scale 2; every request is blocked, the fonts are
data URLs. Deterministic: ocean_art draws from fixed seeds. The PNG must stay under 1 MB (the privacy guard's limit for brand images).
"""
import argparse, importlib.util, io, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRAND, SYSTEM = HERE.parent, HERE.parent.parent
W, H, SCALE = 600, 315, 2                     # CSS px; the PNG is 1200 x 630
MAX_BYTES = 1024 * 1024
TEXT_X = 40                                   # left edge of the text block
BOT_X, BOT_FLOOR, BOT_H = 470, 268, 176      # the Diver bot's centre line, the seabed line under its fins, its height

LINE = "Every claim from the event, checked against Google's documentation"
NOTE = 'Barcelona &nbsp;·&nbsp; 30 Sep – 2 Oct 2026 &nbsp;·&nbsp; free community edition'


def brand_module():
    spec = importlib.util.spec_from_file_location('make_brand_og', BRAND / 'make_brand.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def art(mb, oa):
    """The scene, 600 x 315 CSS px, light water (the banner's light theme)."""
    t = mb.DD_THEMES['light']
    pal = dict(oa.PALETTE)
    p = [f'<svg class="art" viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-hidden="true">',
         '<defs><linearGradient id="og-water" x1="0" y1="0" x2="0" y2="1">'
         + ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in t['water']) + '</linearGradient>'
         f'<radialGradient id="og-glow" cx="50%" cy="0%" r="70%"><stop offset="0" stop-color="{t["glow"]}" stop-opacity="{t["glow_op"]}"/>'
         f'<stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/></radialGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#og-water)"/>',
         f'<ellipse cx="420" cy="0" rx="330" ry="230" fill="url(#og-glow)"/>',
         mb._place(oa.light_rays(W, H, 'og', seed=11, n=7, opacity=t['ray_op'], reach=.9), 0, 0, W, H)]
    p.append(oa.fish_school(560, 46, 9, t['far_fish'], n=4, seed='og-far', mono=True))
    p.append(mb._place(oa.seabed(W, 96, 'slim', seed=31, dark=False, band=False, avoid=[(0, 330), (BOT_X - 64, BOT_X + 64)]), 0, H - 78, W, 96))
    p.append(oa.seaweed(14, H + 4, 92, pal['weed'], width=6.2, amp=6, wl=56, phase=.4))
    p.append(oa.seaweed(28, H + 4, 62, pal['weed_light'], width=4.8, amp=4.5, wl=48, phase=2.2))
    p.append(oa.anemone(548, H + 1, 22, pal=pal))
    p.append(oa.branch_coral(586, H + 2, .36, pal['coral'], width=4.6))
    p.append(oa.bubble_trail(566, 210, 120, 5.2, n=5, seed='og-a', pal=pal, **t['bubble']))
    p.append(oa.fish_school(560, 104, 15, 'blue', n=6, seed='og', pal=pal))
    p.append(oa.fish(446, 44, 22, 'red', flip=True, pal=pal))
    p.append(oa.fish(572, 160, 34, 'yellow', pal=pal))
    bw, bh = oa.diver_bot_box('wave', BOT_H)
    p.append(oa.diver_bot('wave', BOT_X, BOT_FLOOR - bh / 2, BOT_H, 'og-bot', unit_px=1.0))
    p.append(mb._place(oa.top_wave(W, 18, wl=50), 0, 0, W, 18))
    p.append('</svg>')
    return ''.join(p)


def page(mb, oa):
    t = mb.DD_THEMES['light']
    sep = (f'<svg class="sep" viewBox="0 0 10 10" width="10" height="10" aria-hidden="true">'
           f'<circle cx="5" cy="5" r="3.2" fill="none" stroke="{t["sep"]}" stroke-width="1.3"/></svg>')
    days = sep.join(f'<span>{d}</span>' for d in mb.DAYS)
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
{mb.dd_font_css()}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: {t["panel"]}; }}
.stage {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; }}
.art {{ position: absolute; inset: 0; }}
.text {{ position: absolute; left: {TEXT_X}px; top: 30px; width: 352px; height: 232px; display: flex; flex-direction: column; justify-content: center;
        font-family: 'Figtree'; }}
.eyebrow {{ font-weight: 700; font-size: 9.6px; line-height: 1.3; letter-spacing: .16em; text-transform: uppercase; color: {t["eyebrow"]}; }}
.title {{ margin-top: 10px; font-weight: 800; font-size: 50px; line-height: .98; letter-spacing: -.022em; color: {t["title"]}; }}
.title em {{ font-style: normal; color: {t["accent"]}; }}
.rule {{ display: block; margin: 14px 0 12px; }}
.line {{ font-weight: 400; font-size: 15px; line-height: 1.35; color: {t["line"]}; max-width: 330px; }}
.days {{ margin-top: 13px; font-weight: 700; font-size: 9px; line-height: 1; letter-spacing: .2em; text-transform: uppercase; color: {t["days"]};
        display: flex; align-items: center; gap: 9px; }}
.note {{ margin-top: 10px; font-weight: 400; font-size: 10.5px; line-height: 1.3; color: {t["line"]}; opacity: .85; }}
.sep {{ display: block; }}
</style></head><body><div class="stage">{art(mb, oa)}
<div class="text">
  <div class="eyebrow">{mb.EYEBROW}</div>
  <div class="title">{mb.TITLE_SMALL} <em>{mb.TITLE}</em></div>
  {mb.dd_rule(t["rule"], t["sep"])}
  <div class="line">{LINE}</div>
  <div class="days">{days}</div>
  <div class="note">{NOTE}</div>
</div></div></body></html>'''


def render(out):
    from html import unescape
    from PIL import Image
    from playwright.sync_api import sync_playwright
    text = unescape(LINE + NOTE)
    bad = sorted({c for c in text if ord(c) > 0xFF and c != '–'})
    if bad: raise SystemExit(f'the share image text has characters the bundled latin fonts may not cover: {bad}')
    sys.path.insert(0, str(SYSTEM))
    import ocean_art as oa
    mb = brand_module()
    html = page(mb, oa)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            ctx = browser.new_context(viewport={'width': W, 'height': H}, device_scale_factor=SCALE)
            ctx.route('**/*', lambda route: route.abort())   # no network: fonts are data URLs, nothing else is loaded
            pg = ctx.new_page()
            pg.set_content(html, wait_until='load')
            failed = pg.evaluate('''async () => { await Promise.allSettled([...document.fonts].map(f => f.load()));
                await document.fonts.ready; return [...document.fonts].filter(f => f.status !== 'loaded').map(f => f.family + ' ' + f.weight); }''')
            if failed: raise SystemExit(f'fonts failed to load: {failed}')
            png = pg.screenshot(clip={'x': 0, 'y': 0, 'width': W, 'height': H})
        finally:
            browser.close()
    img = Image.open(io.BytesIO(png)).convert('RGB')
    if img.size != (W * SCALE, H * SCALE): raise SystemExit(f'the share image is {img.size}, not {(W * SCALE, H * SCALE)}')
    buf = io.BytesIO()
    img.save(buf, 'PNG', optimize=True)
    if buf.tell() > MAX_BYTES: raise SystemExit(f'the share image is {buf.tell()} bytes, over {MAX_BYTES}')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'og-image.png').write_bytes(buf.getvalue())
    print(f'OK: {out / "og-image.png"} ({img.size[0]} x {img.size[1]}, {buf.tell() // 1024} KB)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(HERE))
    render(Path(ap.parse_args().out))


if __name__ == '__main__':
    main()
