import random, math, io, shutil, sys
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from common import BUILD, OUT, config, day_data, paginate, check_fonts, overlay_fonts

def cover_art():
    W, H = 794, 1123
    rnd = random.Random(7)
    # nodes concentrated in lower-right, sparse elsewhere
    nodes = []
    while len(nodes) < 58:
        x = rnd.uniform(-40, W + 40); y = rnd.uniform(380, H + 40)
        # density bias toward lower right
        bias = (x / W) * 0.6 + ((y - 380) / (H - 380)) * 0.6
        if rnd.random() < bias:
            if all(math.hypot(x - a, y - b) > 52 for a, b in nodes):
                nodes.append((x, y))
    edges = set()
    for i, (x, y) in enumerate(nodes):
        d = sorted(((math.hypot(x - a, y - b), j) for j, (a, b) in enumerate(nodes) if j != i))
        for _, j in d[:3]:
            edges.add(tuple(sorted((i, j))))
    # a highlighted crawl path
    adj = {i: set() for i in range(len(nodes))}
    for i, j in edges: adj[i].add(j); adj[j].add(i)
    start = min(range(len(nodes)), key=lambda k: math.hypot(nodes[k][0]-260, nodes[k][1]-560))
    path_nodes = [start]
    while len(path_nodes) < 7:
        cur = path_nodes[-1]
        nxt = [k for k in adj[cur] if k not in path_nodes and nodes[k][0] > nodes[cur][0] - 10 and nodes[k][1] < 900]
        if not nxt: break
        path_nodes.append(min(nxt, key=lambda k: abs(nodes[k][1]-nodes[cur][1]) - 0.5*(nodes[k][0]-nodes[cur][0])))
    accent = {k: c for k, c in zip(path_nodes, ['#4f7cff','#4f7cff','#22c08a','#4f7cff','#22c08a','#4f7cff','#22c08a'])}
    for k, c in [(5,'#a98bff'),(27,'#f5b84b')]:
        if k not in accent: accent[k] = c
    parts = [f'<svg class="art" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">',
             '<defs><radialGradient id="g1" cx="80%" cy="78%" r="60%"><stop offset="0" stop-color="#2457e6" stop-opacity="0.55"/><stop offset="1" stop-color="#0b1a33" stop-opacity="0"/></radialGradient>'
             '<radialGradient id="g2" cx="10%" cy="0%" r="55%"><stop offset="0" stop-color="#1c3f8f" stop-opacity="0.6"/><stop offset="1" stop-color="#0b1a33" stop-opacity="0"/></radialGradient>'
             '<linearGradient id="pl" x1="0" x2="1"><stop offset="0" stop-color="#4f7cff"/><stop offset="1" stop-color="#22c08a"/></linearGradient></defs>',
             f'<rect width="{W}" height="{H}" fill="#0b1a33"/>',
             f'<rect width="{W}" height="{H}" fill="url(#g2)"/>',
             f'<rect width="{W}" height="{H}" fill="url(#g1)"/>']
    # dot grid
    for gx in range(24, W, 28):
        for gy in range(24, H, 28):
            parts.append(f'<circle cx="{gx}" cy="{gy}" r="0.9" fill="#ffffff" fill-opacity="0.06"/>')
    for i, j in edges:
        (x1, y1), (x2, y2) = nodes[i], nodes[j]
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#8fb3ff" stroke-opacity="0.16" stroke-width="1"/>')
    for a, b in zip(path_nodes, path_nodes[1:]):
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="url(#pl)" stroke-opacity="0.85" stroke-width="2"/>')
    for i, (x, y) in enumerate(nodes):
        if i in accent:
            c = accent[i]
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="{c}" fill-opacity="0.12"/>')
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{c}"/>')
        else:
            r = 2.2 + (i % 3)
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#c9d4ea" fill-opacity="0.55"/>')
    parts.append('</svg>')
    return ''.join(parts)

def overlay(src, dst, dayn, d, author):
    r = PdfReader(src); w = PdfWriter()
    day, place = f'·   Day {dayn} Field Guide', 'Search Central Live Deep Dive Europe 2026  ·  Barcelona'
    overlay_fonts({'Inter': 'inter-400-normal.ttf', 'Inter-SemiBold': 'inter-600-normal.ttf', 'Fraunces': 'fraunces-500-normal.ttf'},
                  [('config.yaml author', 'Inter-SemiBold', author), ('days.yaml footer', 'Inter', d['footer']), ('header', 'Inter', day + place),
                   ('page numbers', 'Fraunces', ''.join(f'{i + 1:02d}' for i in range(len(r.pages))))])
    for i, page in enumerate(r.pages):
        if i > 0:
            pw = float(page.mediabox.width); ph = float(page.mediabox.height)
            buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(pw, ph), initialFontName='Inter')
            L, R = 18 * mm, pw - 18 * mm
            top = ph - 12.5 * mm
            c.setFont('Inter-SemiBold', 7.6); c.setFillColorRGB(0.059, 0.114, 0.2)
            c.drawString(L, top, author)
            nw = pdfmetrics.stringWidth(author, 'Inter-SemiBold', 7.6)
            c.setFont('Inter', 7.6); c.setFillColorRGB(0.4, 0.44, 0.52)
            c.drawString(L + nw + 5, top, day)
            c.drawRightString(R, top, place)
            c.setStrokeColorRGB(0.894, 0.906, 0.925); c.setLineWidth(0.5)
            c.line(L, top - 3.2 * mm, R, top - 3.2 * mm)
            # footer
            fy = 10 * mm
            c.setFont('Inter', 7.2); c.setFillColorRGB(0.4, 0.44, 0.52)
            c.drawString(L, fy, d['footer'])
            c.setFont('Fraunces', 9); c.setFillColorRGB(0.141, 0.341, 0.902)
            c.drawRightString(R, fy, f'{i + 1:02d}')
            c.save(); buf.seek(0)
            page.merge_page(PdfReader(buf).pages[0])
        w.add_page(page)
    w.add_metadata({'/Title': d['pdf']['modern']['title'], '/Author': author, '/Subject': d['pdf']['modern']['subject']})
    with open(dst, 'wb') as f: w.write(f)

def build(day):
    d, author = day_data(day), config()['author']
    html = (BUILD / f'{day}.html').read_text(encoding='utf-8')
    html = html.replace('href="style.css"', 'href="../style.css"').replace('{{COVER_ART}}', cover_art())
    pdf = paginate(html, d, BUILD / '_pass1.html', '_pass')
    tmp, out = BUILD / f'{day}-field-guide-modern.pdf', OUT / f'{day}-field-guide-modern.pdf'
    overlay(pdf, tmp, day.replace('day', ''), d, author)
    check_fonts(tmp)
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tmp, out)
    print('wrote', out)

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'day1')
