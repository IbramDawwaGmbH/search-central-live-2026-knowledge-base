"""Shared by make_pdf.py, build.py, build_deco.py and build_ocean.py: config, per-day data, rendering, page numbers, font checks."""
import asyncio, logging, re, unicodedata
from pathlib import Path
import pdfplumber, yaml
from playwright.async_api import async_playwright
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
FONTS, BUILD, OUT = HERE / 'fonts', HERE / '_build', ROOT / '60-outputs' / 'pdf'
PAGE_KEY = re.compile(r'\{\{(P(?:TK|SRC|\d{2}))\}\}')
logging.getLogger('pdfminer').setLevel(logging.ERROR)

class BuildError(Exception):
    pass

def load_yaml(name):
    return yaml.safe_load((HERE / name).read_text(encoding='utf-8'))

def need(d, keys, where):
    """Stop with one message listing every missing key (dotted keys reach into nested mappings)."""
    def get(k):
        v = d
        for part in k.split('.'):
            v = v.get(part) if isinstance(v, dict) else None
        return v
    missing = [k for k in keys if get(k) in (None, '', [], {})]
    if missing:
        raise BuildError(f'{where} is missing: ' + ', '.join(missing))
    return d

def config():
    return need(load_yaml('config.yaml'), ['author', 'title_line', 'whatsapp', 'linkedin_url'], '_system/pdf/config.yaml')

def day_data(day):
    days = load_yaml('days.yaml') or {}
    if day not in days:
        raise BuildError(f"_system/pdf/days.yaml has no '{day}' entry. Copy the day1 block, rename it to {day} and fill it in.")
    return need(days[day], ['edition', 'title', 'subtitle', 'cover_date', 'footer', 'pdf.deco.title', 'pdf.deco.subject', 'pdf.modern.title',
                            'pdf.modern.subject', 'pdf.ocean.title', 'pdf.ocean.subject', 'pages', 'photos'], f'days.yaml {day}')

async def _render(html_path, pdf_path):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto(html_path.as_uri())
        await pg.wait_for_timeout(400)
        await pg.evaluate('document.fonts.ready')
        await pg.pdf(path=str(pdf_path), format='A4', print_background=True, prefer_css_page_size=True)
        await b.close()

def render(html_path, pdf_path):
    asyncio.run(_render(html_path, pdf_path))

def find_pages(pdf_path, marks):
    """Page number of the first page after cover and contents whose text contains each needle (a needle may wrap across lines)."""
    flat = lambda s: re.sub(r'\s+', ' ', s).lower()
    with pdfplumber.open(pdf_path) as pdf:
        texts = [flat(pg.extract_text() or '') for pg in pdf.pages]
    found = {k: next((i + 1 for i, t in enumerate(texts) if i >= 2 and flat(n) in t), None) for k, n in marks.items()}
    return {k: v for k, v in found.items() if v}, len(texts)

def paginate(html, d, tmp, stem):
    """Render once with 00 page numbers, find every {{PTK}} / {{Pnn}} / {{PSRC}} page, fill them in, render again."""
    marks = {}
    for k in dict.fromkeys(PAGE_KEY.findall(html)):
        marks[k] = f'Section {k[1:]}' if k[1:].isdigit() else (d.get('pages') or {}).get(k)
        if not marks[k]:
            raise BuildError(f'the template uses {{{{{k}}}}} but days.yaml has no pages: {k}: <visible text on that page>')
    tmp.write_text(PAGE_KEY.sub('00', html), encoding='utf-8')
    render(tmp, BUILD / f'{stem}1.pdf')
    found, n = find_pages(BUILD / f'{stem}1.pdf', marks)
    print('pages', n, found)
    missing = [f'{{{{{k}}}}} ("{marks[k]}")' for k in marks if k not in found]
    if missing:
        raise BuildError('page markers whose text is not in the PDF: ' + ', '.join(missing))
    html = PAGE_KEY.sub(lambda m: f'{found[m.group(1)]:02d}', html)
    left = sorted(set(re.findall(r'\{\{[^{}]*\}\}', html)))
    if left:
        raise BuildError('unfilled placeholders: ' + ', '.join(left))
    tmp.write_text(html, encoding='utf-8')
    render(tmp, BUILD / f'{stem}2.pdf')
    return BUILD / f'{stem}2.pdf'

def pdf_fonts(path):
    """{font name: [pages]} for every font a page or form XObject uses."""
    out = {}
    def walk(res, pno, seen):
        res = res.get_object() if res else {}
        for f in (res.get('/Font') or {}).values():
            f = f.get_object()
            names = [f.get('/BaseFont')] + [x.get_object().get('/BaseFont') for x in f.get('/DescendantFonts') or []]
            fd = f['/FontDescriptor'].get_object() if '/FontDescriptor' in f else {}
            if f.get('/Subtype') == '/Type3':  # Skia draws synthetic bold/italic as Type3; the descriptor names the family
                names = [f"{fd.get('/FontFamily') or fd.get('/FontName') or 'unnamed'} (Type3)"]
            for nm in [x for x in names if x] or ['(unnamed font)']:
                out.setdefault(re.sub(r'^/([A-Z]{6}\+)?', '', str(nm)), set()).add(pno)
        for x in (res.get('/XObject') or {}).values():
            x = x.get_object()
            if x.get('/Subtype') == '/Form' and id(x) not in seen:
                seen.add(id(x)); walk(x.get('/Resources'), pno, seen)
    for i, p in enumerate(PdfReader(path).pages):
        walk(p.get('/Resources'), i + 1, set())
    return {k: sorted(v) for k, v in out.items()}

def check_fonts(path):
    """Fail when the PDF uses a font that is not in fonts/ (a system fallback such as Arial, Times, Segoe UI Symbol, DejaVu)."""
    norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
    bundled = {norm(re.sub(r'(-(latin-ext|latin|symbols|math))?-\d{3}-(normal|italic)$', '', f.stem)) for f in FONTS.iterdir() if f.suffix in ('.woff2', '.ttf')}
    fonts = pdf_fonts(path)
    bad = {k: v for k, v in fonts.items() if not any(norm(k).startswith(b) for b in bundled)}
    print('fonts:', ', '.join(sorted(fonts)))
    if bad:
        raise BuildError('fonts that are not bundled in _system/pdf/fonts: ' + '; '.join(f'{k} (pages {", ".join(map(str, v))})' for k, v in sorted(bad.items()))
                         + '. A character is missing from the bundled fonts: see fonts/LICENSES.md.')

def overlay_fonts(fonts, texts):
    """Register the reportlab fonts {name: file in fonts/} of the running header and footer, and fail when one of them lacks a
    character of texts [(where, font name, text)]: reportlab would leave it out of the page without a warning."""
    for n, f in fonts.items():
        pdfmetrics.registerFont(TTFont(n, str(FONTS / f)))
    bad = {}
    for where, n, s in texts:
        have = pdfmetrics.getFont(n).face.charToGlyph
        for ch in dict.fromkeys(s):
            if ord(ch) not in have:
                bad.setdefault((where, fonts[n]), []).append(f'U+{ord(ch):04X} {unicodedata.name(ch, "(unnamed)")}')
    if bad:
        raise BuildError('the running header/footer cannot draw these characters: ' + '; '.join(
            f'{w} needs {", ".join(cs)}, which fonts/{f} does not have' for (w, f), cs in bad.items())
            + '. Write the text without them, or rebuild the .ttf with fonts/make_ttf.py from a subset that has them (see fonts/LICENSES.md).')
