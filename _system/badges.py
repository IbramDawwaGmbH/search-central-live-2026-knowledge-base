"""Status badges for the READMEs: small two-part SVG pills drawn from the build's numbers, in one of the two styles.

    from badges import render
    files = render(stats)                       # Art Deco: {'version.svg': '<svg ...', 'days.svg': ..., ...}
    files = render(stats, style='deep-dive')    # the same badges in the Deep Dive style

`stats` keys (all required):
    version          'v2.1.0'                      the version heading at the top of CHANGELOG.md
    data_through     '2026-10-01'                  ISO date of the last day with data
    days_done        2                             event days with data
    days_total       3                             event days in all
    claims           960                           public claims (private ones never count)
    docs_backed_pct  64                            % of public slide and stage claims graded confirmed or consistent,
                                                   among those graded confirmed, consistent or undocumented
    topics, sources  78, 129                       public topics and sources
    requirements     108                           developer kit requirements
    facts            74                            media kit facts
Optional:
    edition          'community'                   the community edition: media-kit.svg reads "full edition on request" instead of
                                                   counting the preview's facts ('full', the default, counts them)

Every badge is 20 px high and carries a <title> and an aria-label.
    art-deco (default)  an onyx label (cream capitals) and a gold value (onyx text), a gold hairline round the whole pill
                        and a small diamond on the seam; privacy.svg has a light-gold value.
    deep-dive           a fully rounded pill: a deep indigo label (white capitals) and an ocean-blue value (white text),
                        a soft blue hairline and a small glossy bubble on the seam; privacy.svg has a pale-blue value
                        (deep blue text). Every text/background pair reaches WCAG AA (4.5:1).
The build passes the default style from _system/theme.yaml (theme.default_style()): Deep Dive, so the README badges are the
Deep Dive pills. render()'s own default stays art-deco, and the Art Deco output never changes.
The build writes the result to 60-outputs/badges/; the badge files are never edited by hand. Text is measured with a fixed
table of Verdana advance widths (font units, 2048 per em, from Verdana's hmtx table) and pinned with textLength, so the
output is byte-identical for the same numbers on every machine and the text fits whichever of the listed fonts the viewer has.
Run `python _system/badges.py DIR [STYLE]` to write a sample set into DIR (STYLE: art-deco, deep-dive, or all for both;
without STYLE, the default style of _system/theme.yaml, which is deep-dive).
"""
import datetime, re
from html import escape

__all__ = ['render', 'STYLES']

ONYX, CREAM, GOLD, GOLD_L = '#1a1712', '#f7f1e3', '#b08d3a', '#d9c08a'
FONT = 'Verdana,DejaVu Sans,sans-serif'
HEIGHT = 20
LABEL_SIZE, VALUE_SIZE = 10, 11    # px: the label is set in capitals with tracking, the value at the usual badge size
TRACK = 1.1                        # px of extra space between the label's letters
PAD = 8                            # px between a text and the badge's outer edge
SEAM = 10.5                        # px between a text and the seam, which carries the diamond
UPM = 2048

STYLES = ('art-deco', 'deep-dive')
# Deep Dive: indigo label, ocean-blue value, a soft blue hairline and a glossy bubble on the seam (colours from the theme palette)
DD_LABEL, DD_VALUE, DD_VALUE_L, DD_TEXT, DD_TEXT_L = '#28307a', '#2563d6', '#d6e5fc', '#ffffff', '#1d4bb8'
DD_RIM, DD_BUBBLE_HI, DD_BUBBLE_LO = '#5b8ae8', '#9cc2ff', '#2f6fe0'

# Verdana advance widths in font units; anything not listed counts as the widest common letter (W), so text never overflows.
_W = dict(zip(' !"#$%&\'()*+,-./0123456789:;<=>?@', [720, 806, 940, 1676, 1302, 2204, 1488, 550, 930, 930, 1302, 1676, 745, 930, 745, 930]
              + [1302] * 10 + [930, 930, 1676, 1676, 1676, 1117, 2048]))
_W.update(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ', [1400, 1404, 1430, 1578, 1295, 1177, 1588, 1539, 862, 931, 1419, 1140, 1726, 1532, 1612, 1235,
                                              1612, 1424, 1400, 1262, 1499, 1400, 2025, 1403, 1260, 1403]))
_W.update(zip('abcdefghijklmnopqrstuvwxyz', [1230, 1276, 1067, 1276, 1220, 720, 1276, 1296, 562, 705, 1212, 562, 1992, 1296, 1243, 1276,
                                              1276, 874, 1067, 807, 1296, 1212, 1676, 1212, 1212, 1076]))
_W.update({'[': 930, '\\': 930, ']': 930, '^': 1676, '_': 1302, '`': 1302, '{': 1300, '|': 930, '}': 1300, '~': 1676,
           '·': 745, '–': 1302, '—': 2048, '’': 550, '…': 1676, '×': 1676})
_FALLBACK = 2025

MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
MONTHS_LONG = 'January February March April May June July August September October November December'.split()


def text_width(s, size, track=0.0):
    """Width in px of `s` set in Verdana at `size` px, with `track` px added between letters."""
    return sum(_W.get(c, _FALLBACK) for c in s) * size / UPM + track * max(len(s) - 1, 0)


def _num(n):
    return f'{n:,}'


def _plural(n, one, many):
    return f'{_num(n)} {one if n == 1 else many}'


def _date(iso, long=False):
    """'2026-10-01' -> '1 Oct 2026' (or '1 October 2026'); anything but a real calendar date is an error."""
    try:
        if not isinstance(iso, str) or not re.fullmatch(r'\d{4}-\d\d-\d\d', iso):
            raise ValueError
        d = datetime.date.fromisoformat(iso)
    except ValueError:
        raise ValueError(f'badges: data_through must be an ISO date such as 2026-10-01, not {iso!r}') from None
    return f'{d.day} {(MONTHS_LONG if long else MONTHS)[d.month - 1]} {d.year}'


def _f(v):
    """A coordinate with at most two decimals and no trailing zeros, so the SVG text is stable."""
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def badge(slug, label, value, title, value_bg=GOLD):
    """One badge: onyx label on the left, `value` on `value_bg` on the right, a gold hairline round the whole pill and a
    small light-gold diamond on the seam (the divider's motif)."""
    label = label.upper()
    lt, vt = text_width(label, LABEL_SIZE, TRACK), text_width(value, VALUE_SIZE)
    lw = round(PAD + lt + SEAM)
    vw = round(SEAM + vt + PAD)
    w = lw + vw
    t = escape(title, quote=True)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{HEIGHT}" viewBox="0 0 {w} {HEIGHT}" role="img" aria-label="{t}">'
            f'<title>{escape(title, quote=False)}</title>'
            f'<clipPath id="{slug}-r"><rect width="{w}" height="{HEIGHT}" rx="3"/></clipPath>'
            f'<g clip-path="url(#{slug}-r)"><rect width="{lw}" height="{HEIGHT}" fill="{ONYX}"/>'
            f'<rect x="{lw}" width="{vw}" height="{HEIGHT}" fill="{value_bg}"/></g>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{HEIGHT - 1}" rx="2.5" fill="none" stroke="{GOLD}"/>'
            f'<path d="M{lw} 6.4L{_f(lw + 3.6)} 10L{lw} 13.6L{_f(lw - 3.6)} 10Z" fill="{ONYX}" stroke="{GOLD_L}" stroke-width="0.9"/>'
            f'<g font-family="{FONT}" text-anchor="middle" text-rendering="geometricPrecision">'
            f'<text x="{_f(PAD + lt / 2)}" y="13.6" font-size="{LABEL_SIZE}" fill="{CREAM}" textLength="{_f(lt)}" lengthAdjust="spacing">{escape(label, quote=False)}</text>'
            f'<text x="{_f(lw + SEAM + vt / 2)}" y="14" font-size="{VALUE_SIZE}" fill="{ONYX}" textLength="{_f(vt)}" lengthAdjust="spacing">{escape(value, quote=False)}</text>'
            '</g></svg>\n')


def badge_deep(slug, label, value, title, light=False):
    """One Deep Dive badge: a fully rounded pill, indigo label on the left, `value` on ocean blue (or pale blue when `light`)
    on the right, a soft blue hairline round the pill and a small glossy bubble with a highlight on the seam."""
    label = label.upper()
    lt, vt = text_width(label, LABEL_SIZE, TRACK), text_width(value, VALUE_SIZE)
    lw = round(PAD + 2 + lt + SEAM)
    vw = round(SEAM + vt + PAD + 2)
    w = lw + vw
    t = escape(title, quote=True)
    r = HEIGHT / 2
    vbg, vfg = (DD_VALUE_L, DD_TEXT_L) if light else (DD_VALUE, DD_TEXT)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{HEIGHT}" viewBox="0 0 {w} {HEIGHT}" role="img" aria-label="{t}">'
            f'<title>{escape(title, quote=False)}</title>'
            f'<defs><clipPath id="{slug}-r"><rect width="{w}" height="{HEIGHT}" rx="{_f(r)}"/></clipPath>'
            f'<radialGradient id="{slug}-b" cx=".38" cy=".32" r=".75"><stop offset="0" stop-color="{DD_BUBBLE_HI}"/>'
            f'<stop offset="1" stop-color="{DD_BUBBLE_LO}"/></radialGradient></defs>'
            f'<g clip-path="url(#{slug}-r)"><rect width="{lw}" height="{HEIGHT}" fill="{DD_LABEL}"/>'
            f'<rect x="{lw}" width="{vw}" height="{HEIGHT}" fill="{vbg}"/></g>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{HEIGHT - 1}" rx="{_f(r - .5)}" fill="none" stroke="{DD_RIM}" stroke-opacity="0.55"/>'
            f'<circle cx="{lw}" cy="10" r="4.2" fill="url(#{slug}-b)" stroke="#ffffff" stroke-width="1.1"/>'
            f'<path d="M{_f(lw - 2.4)} 8.9A2.5 2.5 0 0 1 {_f(lw - .5)} 7.6" fill="none" stroke="#ffffff" stroke-width="0.9" stroke-linecap="round"/>'
            f'<g font-family="{FONT}" text-anchor="middle" text-rendering="geometricPrecision">'
            f'<text x="{_f(PAD + 2 + lt / 2)}" y="13.6" font-size="{LABEL_SIZE}" fill="{DD_TEXT}" textLength="{_f(lt)}" lengthAdjust="spacing">{escape(label, quote=False)}</text>'
            f'<text x="{_f(lw + SEAM + vt / 2)}" y="14" font-size="{VALUE_SIZE}" fill="{vfg}" textLength="{_f(vt)}" lengthAdjust="spacing">{escape(value, quote=False)}</text>'
            '</g></svg>\n')


def _int(stats, key):
    if key not in stats:
        raise ValueError(f'badges: stats[{key!r}] is missing')
    v = stats[key]
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise ValueError(f'badges: stats[{key!r}] must be a whole number of 0 or more, not {v!r}')
    return v


def render(stats, style='art-deco'):
    """File name -> SVG text for every README badge in `style` (art-deco or deep-dive). Raises ValueError on a missing or
    malformed number, or on an unknown style."""
    if style not in STYLES:
        raise ValueError(f'badges: style must be one of {", ".join(STYLES)}, not {style!r}')
    if not isinstance(stats, dict):
        raise ValueError('badges: stats must be a dict')
    version = stats.get('version')
    if not isinstance(version, str) or not re.fullmatch(r'v\d+\.\d+\.\d+', version):
        raise ValueError(f'badges: stats["version"] must look like v2.1.0, not {version!r}')
    n = {k: _int(stats, k) for k in ('days_done', 'days_total', 'claims', 'docs_backed_pct', 'topics', 'sources', 'requirements', 'facts')}
    if n['days_total'] < 1 or n['days_done'] > n['days_total']:
        raise ValueError(f'badges: days_done ({n["days_done"]}) must be between 0 and days_total ({n["days_total"]}), and days_total at least 1')
    if n['docs_backed_pct'] > 100:
        raise ValueError(f'badges: docs_backed_pct must be 0 to 100, not {n["docs_backed_pct"]}')
    through, through_long = _date(stats.get('data_through')), _date(stats.get('data_through'), long=True)
    pct = n['docs_backed_pct']
    specs = [
        ('version', 'version', f'{version} · data through {through}', f'Version: knowledge base {version}, data through {through_long}'),
        ('days', 'event days', f'{n["days_done"]} of {n["days_total"]} covered',
         f'Event days: {n["days_done"]} of {n["days_total"]} covered'),
        ('claims', 'claims', f'{_num(n["claims"])} public', f'Claims: {_plural(n["claims"], "public claim", "public claims")}'),
        ('docs-backed', 'docs-backed', f'{pct}% of graded claims',
         f'Docs-backed: {pct}% of the public slide and stage claims graded against Google’s documentation are confirmed or consistent'),
        ('topics', 'topics', _num(n['topics']), f'Topics: {_plural(n["topics"], "topic", "topics")}'),
        ('sources', 'sources', _num(n['sources']), f'Sources: {_plural(n["sources"], "source", "sources")}'),
        ('dev-kit', 'developer kit', _plural(n['requirements'], 'requirement', 'requirements'),
         f'Developer kit: {_plural(n["requirements"], "requirement", "requirements")}'),
        ('media-kit', 'media kit', _plural(n['facts'], 'fact', 'facts'), f'Media kit: {_plural(n["facts"], "fact", "facts")}'),
    ]
    edition = stats.get('edition', 'full')
    if edition not in ('full', 'community'):
        raise ValueError(f'badges: stats["edition"] must be full or community, not {edition!r}')
    if edition == 'community':  # the community edition holds a preview of the media kit: the badge says where the full kit is
        specs[-1] = ('media-kit', 'media kit', 'full edition on request',
                     'Media kit: full edition on request; this community edition holds a short preview')
    privacy = ('privacy', 'privacy', 'private material excluded',
               'Privacy: photos, recordings, transcripts and private notes never enter git, '
               'and claims marked private never reach a generated output')
    if style == 'deep-dive':
        out = {f'{slug}.svg': badge_deep(slug, label, value, title) for slug, label, value, title in specs}
        out['privacy.svg'] = badge_deep(*privacy, light=True)
        return out
    out = {f'{slug}.svg': badge(slug, label, value, title) for slug, label, value, title in specs}
    out['privacy.svg'] = badge(*privacy, GOLD_L)
    return out


# Illustrative numbers for the self-test only (roughly the v2.1.0 data); the real badges get theirs from the build.
SAMPLE = {'version': 'v2.1.0', 'data_through': '2026-10-01', 'days_done': 2, 'days_total': 3, 'claims': 960, 'docs_backed_pct': 64,
          'topics': 78, 'sources': 129, 'requirements': 108, 'facts': 74}

if __name__ == '__main__':
    import sys
    from pathlib import Path
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] not in STYLES + ('all',)):
        raise SystemExit('Usage: python _system/badges.py DIR [STYLE]   (writes a sample set of badges into DIR; STYLE is '
                         f'{", ".join(STYLES)} or all, default: the style in _system/theme.yaml; all writes one subfolder per style)')
    out = Path(sys.argv[1])
    if len(sys.argv) == 3:
        which = sys.argv[2]
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from theme import default_style
        which = default_style()
    try:
        render(SAMPLE, 'ocean')
    except ValueError:
        pass
    else:
        raise SystemExit('render accepted an unknown style')
    for style in STYLES if which == 'all' else (which,):
        files = render(SAMPLE, style)
        assert files == render(dict(SAMPLE), style=style), 'render is not deterministic'
        assert files == render({**SAMPLE, 'edition': 'full'}, style), 'edition full must draw the same badges as no edition'
        comm = render({**SAMPLE, 'edition': 'community'}, style)
        assert 'full edition on request' in comm['media-kit.svg'] and {k: v for k, v in comm.items() if k != 'media-kit.svg'} == \
            {k: v for k, v in files.items() if k != 'media-kit.svg'}, 'the community edition changes the media-kit badge only'
        assert sorted(files) == sorted(f'{n}.svg' for n in ('version', 'days', 'claims', 'docs-backed', 'topics', 'sources',
                                                             'dev-kit', 'media-kit', 'privacy')), sorted(files)
        for bad in ({**SAMPLE, 'claims': -1}, {**SAMPLE, 'data_through': '1 Oct'}, {**SAMPLE, 'data_through': '2026-02-30'},
                    {**SAMPLE, 'days_done': 4}, {**SAMPLE, 'version': '2.1'}, {**SAMPLE, 'docs_backed_pct': 101}, {**SAMPLE, 'topics': True},
                    {**SAMPLE, 'edition': 'lite'}):
            try:
                render(bad, style)
            except ValueError:
                pass
            else:
                raise SystemExit(f'render accepted bad stats: {bad}')
        dest = out / style if which == 'all' else out
        dest.mkdir(parents=True, exist_ok=True)
        for name, svg in files.items():
            assert svg.count('<title>') == 1 and 'style=' not in svg and 'http' not in svg.replace('http://www.w3.org/2000/svg', ''), name
            (dest / name).write_bytes(svg.encode('utf-8'))
        print(f'OK: {len(files)} sample {style} badges in {dest.resolve()}')
