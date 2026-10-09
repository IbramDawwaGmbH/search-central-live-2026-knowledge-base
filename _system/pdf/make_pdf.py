"""Build a day's field guide PDF.

Usage:  python make_pdf.py day1            (the default style named in _system/theme.yaml: art-deco -> deco, deep-dive -> ocean)
        python make_pdf.py day1 deco       (Art Deco edition)
        python make_pdf.py day1 modern     (clean modern style)
        python make_pdf.py day1 ocean      (Deep Dive edition; "deep-dive" works too)
        python make_pdf.py day1 both       (deco and modern)
        python make_pdf.py day1 all        (deco, modern and ocean)

Needs: playwright (with Chromium), pypdf, pdfplumber, reportlab, qrcode, pyyaml.
Reads  dayN.template.html, days.yaml, config.yaml and the agent pack (60-outputs/agent-pack, written by
_system/build_kb.py); writes to 60-outputs/pdf/. See README.md in this folder.
"""
import json, re, sys, traceback
from html import escape
import qrcode, qrcode.image.svg
from common import HERE, ROOT, BUILD, BuildError, config, day_data
import build, build_deco, build_ocean
sys.dont_write_bytecode = True
sys.path.append(str(HERE.parent))
from build_kb import EXCLUDED_RE  # photos that never appear in a shared output (the site also ships these PDFs)
from theme import ThemeError, default_style, pdf_style

PACK = ROOT / '60-outputs' / 'agent-pack'
COVERAGE = {'slides': '<b>Slides</b> captured', 'one-slide': '<b>One slide</b> captured', 'transcript': '<b>Transcript</b>',
            'video': '<b>Video</b>', 'notes': '<b>Notes</b> only', 'none': 'Not covered'}
NB = '\u00a0'  # a no-break space: an agenda coverage item or a source date never breaks across lines

def coverage(cov):
    """Coverage labels joined with " · ", each kept on one line; with several values "captured" is left out."""
    return ' · '.join((COVERAGE[c].replace(' captured', '') if len(cov) > 1 else COVERAGE[c]).replace(' ', NB) for c in cov)

MONTHS = 'January February March April May June July August September October November December'.split()
e = lambda v: escape(str(v), quote=False)

def qr(url):
    s = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=1).to_string(encoding='unicode')
    s = re.sub(r'<\?xml[^>]*>', '', s)
    return re.sub(r'width="[^"]*mm" height="[^"]*mm" ', '', s)

def pack(name):
    p = PACK / name
    if not p.exists():
        raise BuildError(f'{p.relative_to(ROOT)} not found. Run _system/build_kb.py first.')
    t = p.read_text(encoding='utf-8')
    return [json.loads(x) for x in t.splitlines() if x.strip()] if name.endswith('.jsonl') else json.loads(t)

def names(xs):
    return ' and '.join(xs) if len(xs) < 3 else ', '.join(xs[:-1]) + ' and ' + xs[-1]

def agenda(dayn):
    d = next((x for x in pack('sessions.json')['days'] if x['day'] == dayn), None)
    rows = []
    for s in (d or {}).get('sessions') or []:
        if s['id'].endswith('-S00') or s.get('kind') in ('break', 'unrecorded'):
            continue
        cov = s.get('coverage') or ['none']
        cov = [cov] if isinstance(cov, str) else cov
        bad = [c for c in cov if c not in COVERAGE]
        if bad:
            raise BuildError(f"{s['id']}: unknown coverage {bad}; allowed: {', '.join(COVERAGE)}")
        dot = '' if set(cov) & {'slides', 'one-slide', 'transcript', 'video'} else ' l' if 'notes' in cov else ' n'
        who = ', '.join(x for x in (names(s.get('speakers') or []), s.get('role')) if x)
        rows.append(f'    <div class="r"><span class="time">{e(s["time"])}</span><span class="dot{dot}"></span><span class="title">{e(s["title"])}'
                    + (f'<span class="who">{e(who)}</span>' if who else '') + f'</span><span class="cov">{coverage(cov)}</span></div>')
    if not rows:
        raise BuildError(f'sessions.json has no sessions for day {dayn}: fill 20-claims/sessions.yaml and run _system/build_kb.py')
    return '\n'.join(rows)

def sources(dayn, claims, extra):
    """The day's cited sources as <li> rows, and the newest 'checked' date among them (e.g. '1 October 2026')."""
    reg = pack('sources.json')
    unknown = [k for k in extra if k not in reg]
    if unknown:
        raise BuildError(f'days.yaml sources_extra keys missing from sources.json: {", ".join(unknown)}')
    used = {s['key'] for c in claims.values() if c['day'] == dayn for s in c['sources']} | set(extra)
    if used - set(reg):
        raise BuildError(f'claims cite sources missing from sources.json: {", ".join(sorted(used - set(reg)))}. Rebuild the KB.')
    if not used:
        raise BuildError(f'no public claim of day {dayn} cites a source, so {{{{SOURCES}}}} would be empty')
    date = lambda t: re.sub(r'\b(\d{1,2}) ([A-Z][a-z]+) (\d{4})\b', lambda m: NB.join(m.groups()) if m[2] in MONTHS else m[0], t)
    rows = [f'    <li><a href="{escape(v["url"])}">{date(e(v["title"]))}</a> <span>— {date(e(v["publisher"]))}</span></li>' for k, v in reg.items() if k in used]
    y, m, dd = map(int, max(str(reg[k]['checked']) for k in used).split('-'))
    return '\n'.join(rows), f'{dd} {MONTHS[m - 1]} {y}'

def check_claims(html, claims):
    bad = sorted({i for m in re.findall(r'data-claims="([^"]*)"', html) for i in m.split() if i not in claims})
    if bad:
        raise BuildError('data-claims cites ids that are not public claims in claims.jsonl (unknown or private): ' + ', '.join(bad))

def prepare(day):
    """Fill every non-page placeholder of dayN.template.html and write _build/dayN.html."""
    d, cfg = day_data(day), config()
    dayn = int(re.sub(r'\D', '', day) or 0)
    tpl = HERE / f'{day}.template.html'
    if not tpl.exists():
        raise BuildError(f'{tpl.name} not found in _system/pdf/')
    html = tpl.read_text(encoding='utf-8')
    claims = {c['id']: c for c in pack('claims.jsonl')} if 'data-claims=' in html or '{{SOURCES}}' in html else {}
    check_claims(html, claims)
    digits = re.sub(r'\D', '', cfg['whatsapp'])
    li = cfg['linkedin_url']
    li_text = re.sub(r'^(www|[a-z]{2})\.(?=[^/]+\.[^/.]+/)', '', re.sub(r'^https?://', '', li)).rstrip('/')
    fill = {'AUTHOR': e(cfg['author']), 'TITLE_LINE': e(cfg['title_line']), 'PHONE': e(cfg['whatsapp']),
            'WA_URL': f'https://wa.me/{digits}', 'LI_URL': escape(li), 'LI_TEXT': e(li_text),
            'QR': qr(f'https://wa.me/{digits}'), 'QRLI': qr(li), 'SUBTITLE': e(d['subtitle']), 'COVER_DATE': e(d['cover_date']),
            'PHOTOS': e(d['photos'])}
    if '{{AGENDA}}' in html: fill['AGENDA'] = agenda(dayn)
    if '{{SOURCES}}' in html or '{{CHECKED}}' in html:
        claims = claims or {c['id']: c for c in pack('claims.jsonl')}
        fill['SOURCES'], checked = sources(dayn, claims, d.get('sources_extra') or [])
        fill['CHECKED'] = e(d.get('sources_checked') or checked)
    for k, v in fill.items():
        html = html.replace('{{' + k + '}}', v)
    leak = EXCLUDED_RE.search(html + json.dumps([d, cfg], ensure_ascii=False, default=str))
    if leak:
        raise BuildError(f'{leak[0]} is an excluded photo (EXCLUDED in _system/build_kb.py): remove it from {tpl.name}, days.yaml or config.yaml')
    BUILD.mkdir(exist_ok=True)
    (BUILD / f'{day}.html').write_text(html, encoding='utf-8', newline='\n')

STYLES = {'deco': ['deco'], 'modern': ['modern'], 'ocean': ['ocean'], 'deep-dive': ['ocean'], 'both': ['deco', 'modern'],
          'all': ['deco', 'modern', 'ocean']}
BUILDERS = {'deco': build_deco, 'modern': build, 'ocean': build_ocean}

def main():
    day = sys.argv[1] if len(sys.argv) > 1 else 'day1'
    if len(sys.argv) > 2:
        style = sys.argv[2]
    else:
        try:
            style = pdf_style(default_style())
        except ThemeError as x:
            sys.exit(f'ERROR: {x}')
    styles = STYLES.get(style)
    if not styles:
        sys.exit(f'Unknown style {style!r}. Use deco, modern, ocean (or deep-dive), both or all.')
    try:
        prepare(day)
    except BuildError as x:
        sys.exit(f'ERROR: {x}')
    failed = []
    for st in styles:
        print(f'--- {day} {st}')
        try:
            BUILDERS[st].build(day)
        except PermissionError as x:
            failed.append(f'{st}: cannot write {x.filename}. Is the PDF open in a viewer? Close it and run again.')
        except BuildError as x:
            failed.append(f'{st}: {x}')
        except Exception as x:
            traceback.print_exc()
            failed.append(f'{st}: {type(x).__name__}: {x}')
    if failed:
        print('\nPDF BUILD FAILED for ' + ', '.join(f.split(':')[0] for f in failed) + ':')
        for f in failed:
            print('  ' + f)
        sys.exit(1)

if __name__ == '__main__':
    main()
