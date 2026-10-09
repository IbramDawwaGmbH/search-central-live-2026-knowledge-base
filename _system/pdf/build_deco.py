import re, math, io, shutil, sys
from html import escape
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from common import BUILD, OUT, BuildError, config, day_data, paginate, check_fonts, overlay_fonts

SYM = "'Noto Symbols'"

GOLD, GOLD_D, GOLD_L = '#b08d3a', '#8a6d25', '#d9c08a'
ONYX, CREAM = '#1a1712', '#f7f1e3'

# ---------------------------------------------------------------- cover
def orn(width=260, color=GOLD):
    c = width / 2
    return (f'<svg class="orn" viewBox="0 0 {width} 20" xmlns="http://www.w3.org/2000/svg">'
            f'<line x1="0" y1="10" x2="{c-22}" y2="10" stroke="{color}" stroke-width="0.8"/>'
            f'<line x1="{c+22}" y1="10" x2="{width}" y2="10" stroke="{color}" stroke-width="0.8"/>'
            f'<line x1="18" y1="14" x2="{c-26}" y2="14" stroke="{color}" stroke-width="0.4"/>'
            f'<line x1="{c+26}" y1="14" x2="{width-18}" y2="14" stroke="{color}" stroke-width="0.4"/>'
            f'<path d="M{c} 1L{c+9} 10L{c} 19L{c-9} 10Z" fill="{color}"/>'
            f'<path d="M{c-16} 10L{c-12} 6L{c-8} 10L{c-12} 14Z" fill="none" stroke="{color}" stroke-width="0.8"/>'
            f'<path d="M{c+16} 10L{c+12} 6L{c+8} 10L{c+12} 14Z" fill="none" stroke="{color}" stroke-width="0.8"/></svg>')

def cover_svg():
    W, H = 794, 1123
    cx, cy = W / 2, H + 40
    p = [f'<svg class="art" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
         '<defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a1712" stop-opacity="1"/><stop offset="0.36" stop-color="#1a1712" stop-opacity="0.94"/><stop offset="0.62" stop-color="#1a1712" stop-opacity="0"/></linearGradient>'
         '<radialGradient id="glow" cx="50%" cy="100%" r="70%"><stop offset="0" stop-color="#b08d3a" stop-opacity="0.32"/><stop offset="1" stop-color="#1a1712" stop-opacity="0"/></radialGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="{ONYX}"/>',
         f'<rect width="{W}" height="{H}" fill="url(#glow)"/>']
    # sunburst rays
    n = 44
    for i in range(n + 1):
        a = math.pi * (i / n)
        x2 = cx - math.cos(a) * 1400; y2 = cy - math.sin(a) * 1400
        w = 1.1 if i % 2 == 0 else 0.5
        op = 0.38 if i % 2 == 0 else 0.2
        p.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{GOLD}" stroke-width="{w}" stroke-opacity="{op}"/>')
    # stepped concentric arches
    for k, r in enumerate([120, 170, 220, 300, 380, 470]):
        sw = 2.2 if k in (0, 3) else 0.9
        p.append(f'<path d="M{cx-r} {cy}A{r} {r} 0 0 1 {cx+r} {cy}" fill="none" stroke="{GOLD}" stroke-width="{sw}" stroke-opacity="0.85"/>')
    p.append(f'<path d="M{cx-120} {cy}A120 120 0 0 1 {cx+120} {cy}Z" fill="{GOLD}" fill-opacity="0.9"/>')
    # fade top so text stays clean
    p.append(f'<rect width="{W}" height="{H}" fill="url(#fade)"/>')
    # dark band behind meta
    p.append(f'<rect x="150" y="{H-250}" width="{W-300}" height="150" fill="{ONYX}"/>')
    p.append(f'<rect x="150" y="{H-250}" width="{W-300}" height="150" fill="none" stroke="{GOLD}" stroke-width="0.8"/>')
    p.append(f'<rect x="156" y="{H-244}" width="{W-312}" height="138" fill="none" stroke="{GOLD}" stroke-width="0.4"/>')
    # frame with stepped corners
    def frame(m, sw, step):
        s = step
        d = (f'M{m+s} {m}H{W-m-s}V{m+s}H{W-m}V{H-m-s}H{W-m-s}V{H-m}H{m+s}V{H-m-s}H{m}V{m+s}H{m+s}Z')
        return f'<path d="{d}" fill="none" stroke="{GOLD}" stroke-width="{sw}"/>'
    p.append(frame(26, 1.2, 18))
    p.append(frame(34, 0.5, 14))
    for (x, y) in [(26 + 9, 26 + 9), (W - 35, 35), (35, H - 35), (W - 35, H - 35)]:
        p.append(f'<path d="M{x} {y-5}L{x+5} {y}L{x} {y+5}L{x-5} {y}Z" fill="{GOLD}"/>')
    # top chevrons
    for i in range(3):
        y = 70 + i * 7
        p.append(f'<path d="M{cx-40+i*8} {y}L{cx} {y+14-i*2}L{cx+40-i*8} {y}" fill="none" stroke="{GOLD}" stroke-width="0.8" stroke-opacity="{0.9-i*0.25}"/>')
    p.append('</svg>')
    return ''.join(p)

COVER = '''<div class="cover">
  {art}
  <div class="inner">
    <div class="eyebrow">Search Central Live &nbsp;·&nbsp; Deep Dive Europe 2026</div>
    <div class="ed">{ed}</div>
    {orn}
    <div class="t1">{t1}</div>
    <div class="t2">{t2}</div>
    <div class="t3">{t3}</div>
    <div class="sub">{sub}</div>
  </div>
  <div class="meta">
    <div class="k">Notes &amp; guide by</div>
    <div class="name">{author}</div>
    <div class="v">{date}</div>
  </div>
</div>
'''

# ---------------------------------------------------------------- SVG recolour
TEXT_MAP = {'#2457e6': GOLD_D, '#0f1d33': '#1d1a16', '#667085': '#7a6f5d', '#98a2b3': '#a89a7e', '#2a3446': '#3a342b',
            '#0b8a5f': '#1e5b4b', '#c8372d': '#7d2c38', '#6d3fd6': '#2f4a6b', '#b86e00': GOLD_D,
            '#bcd0ff': GOLD_L, '#dbe5ff': '#e7dcc4', '#e3eaff': '#e7dcc4'}
FILL_MAP = {'#2457e6': '#1d1a16', '#e8eefd': '#efe5cf', '#0f1d33': '#1d1a16', '#0b1a33': '#1d1a16', '#f5f7fb': '#f1e9d6',
            '#e3f4ec': '#dde8e1', '#fbe7e5': '#f1dfdf', '#fff': '#fbf7ec', '#667085': GOLD_D, '#98a2b3': GOLD,
            '#c8372d': '#7d2c38', '#0b8a5f': '#1e5b4b', '#b86e00': GOLD_D}
STROKE_MAP = {'#2457e6': GOLD, '#c7cdd8': '#cdbf9f', '#e4e7ec': '#d9cdb3', '#98a2b3': GOLD, '#667085': GOLD_D,
              '#0b8a5f': '#1e5b4b', '#c8372d': '#7d2c38', '#6d3fd6': '#2f4a6b', '#bcd0ff': GOLD_L, '#b86e00': GOLD_D}
INLINE_MAP = {'#2457e6': GOLD_D, '#0b8a5f': '#1e5b4b', '#6d3fd6': '#7d2c38', '#b86e00': '#2f4a6b', '#667085': '#7a6f5d', '#c8372d': '#7d2c38'}
RECOLORED = ('rect', 'text', 'tspan', 'path', 'circle', 'line', 'polygon', 'g', 'svg', 'marker')

def unmapped_colours(html):
    """Every colour the Art Deco recolouring would leave in its modern value: an SVG fill or stroke missing from TEXT_MAP,
    FILL_MAP or STROKE_MAP (white excepted), a colour on an SVG element the recolouring skips, or an inline style="color:..."
    missing from INLINE_MAP."""
    bad = set()
    for svg in re.findall(r'<svg viewBox.*?</svg>', html, flags=re.S):
        for m in re.finditer(r'<([a-zA-Z][\w-]*)\b[^>]*>', svg):
            name = m.group(1)
            for attr, v in re.findall(r'\s((?:stop-)?color|fill|stroke)="(#[0-9a-fA-F]{3,6})"', m.group(0)):
                table = (TEXT_MAP if name in ('text', 'tspan', 'g') else FILL_MAP) if attr == 'fill' else STROKE_MAP if attr == 'stroke' else {}
                if name not in RECOLORED or (v.lower() not in table and v.lower() not in ('#fff', '#ffffff')):
                    bad.add(f'<{name} {attr}="{v}">')
    bad |= {f'style="color:{v}"' for v in re.findall(r'style="color:(#[0-9a-fA-F]{3,6})"', html) if v.lower() not in INLINE_MAP}
    return sorted(bad)

def recolor_tag(m):
    tag = m.group(0)
    name = m.group(1)
    def sub(attr, table):
        nonlocal tag
        tag = re.sub(rf'{attr}="(#[0-9a-fA-F]{{3,6}})"', lambda mm: f'{attr}="{table.get(mm.group(1).lower(), mm.group(1))}"', tag)
    if name in ('text', 'tspan', 'g'):
        # white text stays white (sits on dark fills)
        sub('fill', TEXT_MAP)
    else:
        sub('fill', FILL_MAP)
    sub('stroke', STROKE_MAP)
    tag = re.sub(rf'font-family="(Inter|Fraunces)(, {SYM})?"', lambda f: f'font-family="{"Jost" if f.group(1) == "Inter" else "Poiret One"}, {SYM}"', tag)
    tag = re.sub(r'rx="(8|10|12)"', 'rx="1"', tag)
    return tag

def recolor_svgs(html):
    def fix(svg):
        s = re.sub(r'<(rect|text|tspan|path|circle|line|polygon|g|svg|marker)\b[^>]*>', recolor_tag, svg.group(0))
        return s
    return re.sub(r'<svg viewBox.*?</svg>', fix, html, flags=re.S)

def recolor_inline(html):
    for a, b in INLINE_MAP.items():
        html = html.replace(f'style="color:{a}"', f'style="color:{b}"')
    html = html.replace('style="border-left-color: var(--blue)"', '')
    return html

# ---------------------------------------------------------------- page background, frame, header, footer
HEAD, FOOT, PLACE = 'SEARCH CENTRAL LIVE  ·  DAY {} FIELD GUIDE', 'DAY {} FIELD GUIDE', 'BARCELONA  ·  2026'

def deco_page(pw, ph, n, dayn, author):
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(pw, ph), initialFontName='Josefin-SB')
    gold = (0.69, 0.553, 0.227); goldd = (0.541, 0.427, 0.145); muted = (0.478, 0.435, 0.365)
    c.setFillColorRGB(0.969, 0.945, 0.890); c.rect(0, 0, pw, ph, stroke=0, fill=1)
    c.setStrokeColorRGB(*gold)
    def stepped(m, step, lw):
        c.setLineWidth(lw)
        p = c.beginPath()
        p.moveTo(m + step, m); p.lineTo(pw - m - step, m); p.lineTo(pw - m - step, m + step); p.lineTo(pw - m, m + step)
        p.lineTo(pw - m, ph - m - step); p.lineTo(pw - m - step, ph - m - step); p.lineTo(pw - m - step, ph - m)
        p.lineTo(m + step, ph - m); p.lineTo(m + step, ph - m - step); p.lineTo(m, ph - m - step); p.lineTo(m, m + step)
        p.lineTo(m + step, m + step); p.close()
        c.drawPath(p, stroke=1, fill=0)
    stepped(8 * mm, 5 * mm, 0.7)
    stepped(9.4 * mm, 4.2 * mm, 0.3)
    c.setFillColorRGB(*gold)
    def diamond(x, y, r):
        p = c.beginPath(); p.moveTo(x, y + r); p.lineTo(x + r, y); p.lineTo(x, y - r); p.lineTo(x - r, y); p.close()
        c.drawPath(p, stroke=0, fill=1)
    for x, y in [(8 * mm + 2.5 * mm, 8 * mm + 2.5 * mm), (pw - 10.5 * mm, 10.5 * mm), (10.5 * mm, ph - 10.5 * mm), (pw - 10.5 * mm, ph - 10.5 * mm)]:
        diamond(x, y, 1.3 * mm)
    L, R = 20 * mm, pw - 20 * mm
    # header
    hy = ph - 16.5 * mm
    c.setFont('Josefin-SB', 6.8); c.setFillColorRGB(*goldd)
    c.drawString(L, hy, author.upper(), charSpace=1.6)
    c.setFillColorRGB(*muted)
    t = HEAD.format(dayn)
    tw = pdfmetrics.stringWidth(t, 'Josefin-SB', 6.8) + 1.6 * (len(t) - 1)
    c.drawString(R - tw, hy, t, charSpace=1.6)
    c.setStrokeColorRGB(*gold); c.setLineWidth(0.4)
    ly = hy - 3.2 * mm
    c.line(L, ly, pw / 2 - 4 * mm, ly); c.line(pw / 2 + 4 * mm, ly, R, ly)
    c.setFillColorRGB(*gold); diamond(pw / 2, ly, 1.4 * mm)
    # footer
    fy = 14.5 * mm
    num = f'{n:02d}'
    c.setFont('Limelight', 11); c.setFillColorRGB(*goldd)
    nw = pdfmetrics.stringWidth(num, 'Limelight', 11)
    c.drawString(pw / 2 - nw / 2, fy - 1.3 * mm, num)
    c.setStrokeColorRGB(*gold); c.setLineWidth(0.5)
    c.line(pw / 2 - 26 * mm, fy, pw / 2 - 7 * mm, fy); c.line(pw / 2 + 7 * mm, fy, pw / 2 + 26 * mm, fy)
    c.setFillColorRGB(*gold); diamond(pw / 2 - 27.5 * mm, fy, 0.9 * mm); diamond(pw / 2 + 27.5 * mm, fy, 0.9 * mm)
    c.setFont('Josefin-SB', 6.2); c.setFillColorRGB(*muted)
    c.drawString(L, fy - 0.8 * mm, FOOT.format(dayn), charSpace=1.1)
    t = PLACE
    tw = pdfmetrics.stringWidth(t, 'Josefin-SB', 6.2) + 1.1 * (len(t) - 1)
    c.drawString(R - tw, fy - 0.8 * mm, t, charSpace=1.1)
    c.save(); buf.seek(0)
    return PdfReader(buf).pages[0]

def finish(src, dst, dayn, d, author):
    r = PdfReader(src); w = PdfWriter()
    overlay_fonts({'Josefin-SB': 'josefin-sans-600-normal.ttf', 'Limelight': 'limelight-400-normal.ttf'},
                  [('config.yaml author', 'Josefin-SB', author.upper()), ('header and footer', 'Josefin-SB', HEAD.format(dayn) + FOOT.format(dayn) + PLACE),
                   ('page numbers', 'Limelight', ''.join(f'{i + 1:02d}' for i in range(len(r.pages))))])
    for i, page in enumerate(r.pages):
        if i == 0:
            w.add_page(page); continue
        pw = float(page.mediabox.width); ph = float(page.mediabox.height)
        bg = deco_page(pw, ph, i + 1, dayn, author)
        bg.merge_page(page)
        w.add_page(bg)
    w.add_metadata({'/Title': d['pdf']['deco']['title'], '/Author': author, '/Subject': d['pdf']['deco']['subject']})
    with open(dst, 'wb') as f: w.write(f)

def cover(d, author):
    t = d['title'] if isinstance(d['title'], list) and len(d['title']) == 3 else None
    if not t:
        raise BuildError('days.yaml title must be a list of three cover lines, e.g. [How Google Crawls, in the Age of, AI SEARCH]')
    e = lambda v: escape(str(v), quote=False)
    return COVER.format(art=cover_svg(), orn=orn(), ed=e(d['edition']), t1=e(t[0]), t2=e(t[1]), t3=e(t[2]), sub=e(d['subtitle']),
                        author=e(author), date=e(d['cover_date']).replace(' · ', ' &nbsp;·&nbsp; '))

def replace_cover(html, new):
    """Swap the template's <div class="cover"> block (matched by counting nested divs) for the Art Deco cover."""
    i, depth = html.find('<div class="cover">'), 0
    for m in re.finditer(r'<div\b|</div>', html[max(i, 0):]) if i >= 0 else []:
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            j = i + m.end() + (html[i + m.end():i + m.end() + 1] == '\n')
            return html[:i] + new + html[j:]
    raise BuildError('the template has no complete <div class="cover"> ... </div> block for the Art Deco cover')

def build(day):
    d, author = day_data(day), config()['author']
    html = (BUILD / f'{day}.html').read_text(encoding='utf-8')
    html = html.replace('href="style.css"', 'href="../deco.css"')
    html = replace_cover(html, cover(d, author))
    html = html.replace('<h2 class="title">Contents</h2>', '<h2 class="title">Contents</h2>\n  ' + orn().replace('class="orn"', 'class="orn-line"'))
    bad = unmapped_colours(html)
    if bad:
        raise BuildError('colours the Art Deco style cannot recolour: ' + ', '.join(bad) + '. Use the modern palette listed in _system/pdf/README.md, '
                         'or add the colour to TEXT_MAP, FILL_MAP, STROKE_MAP or INLINE_MAP in build_deco.py.')
    html = recolor_svgs(html)
    html = recolor_inline(html)
    pdf = paginate(html, d, BUILD / '_deco1.html', '_deco')
    tmp, out = BUILD / f'{day}-field-guide-art-deco.pdf', OUT / f'{day}-field-guide-art-deco.pdf'
    finish(pdf, tmp, day.replace('day', ''), d, author)
    check_fonts(tmp)
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tmp, out)
    print('wrote', out)

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'day1')
