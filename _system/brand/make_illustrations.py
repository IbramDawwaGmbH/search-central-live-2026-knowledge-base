"""Draw the README header illustrations: one 880 x 240 card per tracked README.md, in light and night water.

    python _system/brand/make_illustrations.py                   # write _system/brand/illustrations/<slug>-light.svg / -dark.svg
    python _system/brand/make_illustrations.py --check           # draw and check everything, write nothing
    python _system/brand/make_illustrations.py --only 20-claims,root
                                                                 # draw and write only these slugs (the README check still runs)
    python _system/brand/make_illustrations.py --preview DIR     # also render DIR/contact-sheet.png (every card, light on GitHub's
                                                                 # white page, dark on its #0d1117 page) and DIR/<slug>.png per
                                                                 # slug drawn, with Playwright Chromium at device scale 2

Scenes live in the group modules _system/brand/illus_*.py (except illus_common.py, the shared grammar). Each exposes
SCENES = {slug: function(dark: bool) -> svg string}. A slug is the README's folder with "/" turned into "-" ("root" for the
top-level README): 30-topics/crawling/README.md -> "30-topics-crawling", _system/pdf/README.md -> "_system-pdf".

Every card is checked before anything is written:
    - well-formed XML, root <svg> with viewBox "0 0 880 240";
    - under 80 KB (a warning above 40 KB);
    - no <text>, <script>, <image>, <foreignObject>, <style>, event handlers or style attributes, no external reference
      (every url() and href points at an id in the same file);
    - every id unique and prefixed with "<slug>-";
    - none of the search-engine brand colours (ocean_art.BOT_FORBIDDEN_HEX);
    - deterministic (drawn twice, same bytes); LF line endings, UTF-8;
and the set of slugs must match the tracked READMEs (git ls-files '*README.md'): a README without a scene, or a scene without
a README, stops the run. Scenes still marked as placeholders (illus_common.placeholder) are listed as warnings.
"""
import argparse
import importlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'illustrations'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

MAX_BYTES, WARN_BYTES = 80 * 1024, 40 * 1024
FORBIDDEN_TAGS = ('text', 'script', 'image', 'foreignObject', 'style', 'iframe', 'a', 'use')
GITHUB_BG = {'light': '#ffffff', 'dark': '#0d1117'}


def slug_for(readme):
    """'30-topics/crawling/README.md' -> '30-topics-crawling'; 'README.md' -> 'root'."""
    parent = Path(readme).parent.as_posix()
    return 'root' if parent in ('', '.') else parent.replace('/', '-')


def tracked_readmes():
    try:
        out = subprocess.run(['git', 'ls-files', '*README.md'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        files = [l.strip() for l in out.splitlines() if l.strip()]
    except (OSError, subprocess.CalledProcessError):
        files = []
    if not files:
        raise SystemExit('could not list the tracked READMEs (git ls-files)')
    return {slug_for(f): f for f in files}


def load_scenes():
    """{slug: (module name, function)} from every _system/brand/illus_*.py except illus_common."""
    scenes = {}
    for path in sorted(HERE.glob('illus_*.py')):
        if path.stem == 'illus_common':
            continue
        mod = importlib.import_module(path.stem)
        for slug, fn in getattr(mod, 'SCENES', {}).items():
            if slug in scenes:
                raise SystemExit(f'{slug}: drawn by both {scenes[slug][0]} and {path.stem}')
            scenes[slug] = (path.stem, fn)
    return scenes


def check_svg(slug, variant, svg):
    """Problems with one card (empty list = fine)."""
    from ocean_art import BOT_FORBIDDEN_HEX
    errs = []
    where = f'{slug}-{variant}.svg'
    size = len(svg.encode('utf-8'))
    if size > MAX_BYTES:
        errs.append(f'{where}: {size} bytes, over the {MAX_BYTES} limit')
    if '\r' in svg:
        errs.append(f'{where}: CR line endings')
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as e:
        return errs + [f'{where}: not well-formed XML ({e})']
    if root.tag != '{http://www.w3.org/2000/svg}svg' or root.get('viewBox') != '0 0 880 240':
        errs.append(f'{where}: root must be <svg viewBox="0 0 880 240">')
    ids = []
    for el in root.iter():
        tag = el.tag.split('}')[-1]
        if tag in FORBIDDEN_TAGS:
            errs.append(f'{where}: <{tag}> is not allowed')
        for k, v in el.attrib.items():
            name = k.split('}')[-1]
            if name.lower().startswith('on') or name in ('style', 'class'):
                errs.append(f'{where}: attribute {name} on <{tag}> is not allowed')
            if name == 'id':
                ids.append(v)
            if name == 'href' and not v.startswith('#'):
                errs.append(f'{where}: external href {v!r}')
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        errs.append(f'{where}: duplicate ids {dup[:5]}')
    bad = [i for i in ids if not i.startswith(f'{slug}-')]
    if bad:
        errs.append(f'{where}: ids without the "{slug}-" prefix: {bad[:5]}')
    for ref in re.findall(r'url\(([^)]*)\)', svg):
        if not ref.startswith('#') or ref[1:] not in ids:
            errs.append(f'{where}: url({ref}) does not point at an id in this file')
    low = svg.lower()
    for hx in BOT_FORBIDDEN_HEX:
        if hx in low:
            errs.append(f'{where}: brand colour {hx} is not allowed')
    if not svg.endswith('\n'):
        errs.append(f'{where}: no final newline')
    return errs


def draw(slugs, scenes):
    """{slug: {'light': svg, 'dark': svg}} plus errors and warnings."""
    out, errs, warns = {}, [], []
    for slug in slugs:
        mod, fn = scenes[slug]
        if getattr(fn, 'placeholder', False):
            warns.append(f'{slug}: placeholder scene ({mod})')
        cards = {}
        for variant, dark in (('light', False), ('dark', True)):
            try:
                svg = fn(dark)
                again = fn(dark)
            except Exception as e:                                    # report every broken scene, not just the first
                errs.append(f'{slug}-{variant}: {type(e).__name__}: {e} ({mod})')
                continue
            if svg != again:
                errs.append(f'{slug}-{variant}: two draws differ (not deterministic)')
            errs += check_svg(slug, variant, svg)
            if len(svg.encode('utf-8')) > WARN_BYTES:
                warns.append(f'{slug}-{variant}.svg: {len(svg.encode("utf-8")) // 1024} KB (aim for under 40 KB)')
            cards[variant] = svg
        out[slug] = cards
    return out, errs, warns


def preview(cards, folder, per_slug=True):
    from playwright.sync_api import sync_playwright
    import html
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    def page(items):
        rows = []
        for slug, c in items:
            cells = ''.join(f'<div class="cell" style="background:{GITHUB_BG[v]}"><img src="data:image/svg+xml;charset=utf-8,'
                            f'{html.escape(_url(c[v]))}"></div>' for v in ('light', 'dark') if v in c)
            rows.append(f'<div class="row"><div class="lbl">{html.escape(slug)}</div>{cells}</div>')
        return ('<!doctype html><meta charset="utf-8"><style>body{margin:0;font:13px/1.3 system-ui,sans-serif;background:#e9edf3}'
                '.row{display:grid;grid-template-columns:150px 1fr 1fr;gap:0;align-items:stretch}'
                '.lbl{padding:12px 8px;color:#333;word-break:break-all}.cell{padding:10px 14px}img{width:100%;display:block}</style>'
                + ''.join(rows))

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1500, 'height': 800}, device_scale_factor=1)
        ctx.route('**/*', lambda route: route.abort() if not route.request.url.startswith('data:') else route.continue_())
        pg = ctx.new_page()
        pg.set_content(page(sorted(cards.items())), wait_until='load')
        pg.screenshot(path=str(folder / 'contact-sheet.png'), full_page=True)
        if per_slug:
            ctx2 = browser.new_context(viewport={'width': 940, 'height': 600}, device_scale_factor=2)
            pg2 = ctx2.new_page()
            for slug, c in sorted(cards.items()):
                body = ''.join(f'<div style="background:{GITHUB_BG[v]};padding:15px 30px"><img style="width:880px;display:block" '
                               f'src="data:image/svg+xml;charset=utf-8,{html.escape(_url(c[v]))}"></div>' for v in ('light', 'dark') if v in c)
                pg2.set_content(f'<!doctype html><meta charset="utf-8"><body style="margin:0">{body}', wait_until='load')
                pg2.screenshot(path=str(folder / f'{slug}.png'), full_page=True)
        browser.close()
    return folder / 'contact-sheet.png'


def _url(svg):
    from urllib.parse import quote
    return quote(svg, safe='')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='draw and check everything, write nothing')
    ap.add_argument('--only', help='comma-separated slugs to draw and write')
    ap.add_argument('--preview', metavar='DIR', help='render a contact sheet (and one PNG per slug) into DIR')
    ap.add_argument('--out', default=str(OUT), help='output folder (default _system/brand/illustrations)')
    a = ap.parse_args(argv)

    readmes = tracked_readmes()
    scenes = load_scenes()
    errs = [f'{slug}: no scene for {readmes[slug]}' for slug in sorted(set(readmes) - set(scenes))]
    errs += [f'{slug}: scene without a tracked README ({scenes[slug][0]})' for slug in sorted(set(scenes) - set(readmes))]
    slugs = sorted(set(readmes) & set(scenes))
    if a.only:
        want = [s.strip() for s in a.only.split(',') if s.strip()]
        unknown = [s for s in want if s not in scenes]
        if unknown:
            raise SystemExit(f'unknown slugs: {unknown}')
        slugs = want
    cards, e2, warns = draw(slugs, scenes)
    errs += e2
    for w in warns:
        print('warning:', w)
    if errs:
        for e in errs:
            print('error:', e, file=sys.stderr)
        raise SystemExit(f'{len(errs)} problem(s); nothing written')
    if not a.check:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        for slug, c in cards.items():
            for variant, svg in c.items():
                with open(out / f'{slug}-{variant}.svg', 'w', encoding='utf-8', newline='\n') as f:
                    f.write(svg)
        total = sum(len(s.encode('utf-8')) for c in cards.values() for s in c.values())
        print(f'wrote {sum(len(c) for c in cards.values())} cards for {len(cards)} slugs to {out} ({total // 1024} KB)')
    if a.preview:
        sheet = preview(cards, a.preview, per_slug=True)
        print(f'preview: {sheet}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
