"""Seed list for 20-claims/entities.yaml (knowledge-graph plan, B3 step 1): candidate things with measured alias frequencies.

Reads the public claims (20-claims/day*.yaml), topics.yaml, sources.yaml and the kits (25-kits/content.yaml glossary,
25-kits/dev-requirements.yaml), and writes one YAML report OUTSIDE the repository (the plan keeps it out of git):

  stoplist     the 200 most frequent folded words of the public claim texts and quotes (the build refuses a plain alias that
               equals one of them unless it is scoped or exact)
  candidates   one entry per proposed thing (seed_kind: glossary, or the patterned kind it was found as), from two seeds:
                 glossary   the 125 glossary terms, each with its own claims and the spellings kits.term_aliases() gives it
                 pattern    patterned kinds found in public claim text: HTTP status codes (a 3-digit code near "status",
                            "error", "code", "response" or "server", and 1xx-5xx classes), robots and meta directives, crawlers
                            and user agents (*bot names, Google-* tokens), Search Console reports ("... report"), standards
                            and RFCs, Google products and features (a seed list plus "Google X" phrases)
               For every proposed alias: hits case-insensitive on folded text (ci) and case-sensitive on the raw text (cs),
               both on word boundaries (?<![\\w-])alias(?![\\w-]) as the build matches; whether the alias is a stop word; the
               topics of the matching claims (most frequent first); five example claim ids. Per candidate: the union of claims
               (ci), source keys whose title contains a name, requirement ids resting on a matching claim, and the rule of
               thumb (3+ mentions and a documentation source or a requirement).
  unseeded     capitalised multi-word phrases with 3+ case-sensitive mentions that no candidate alias covers

Nothing here writes to the repository and the build never reads the report: a person (or agent) chooses entities from it and
writes them into 20-claims/entities.yaml by hand. Deterministic: no clock, everything sorted.

Usage:  python _system/tools/entity_candidates.py --out <path outside the repo>/entity-candidates.yaml [--root REPO]
        python _system/tools/entity_candidates.py --alias "crawl stats" --alias "Crawl stats" [--cs]   print hits and examples
Needs:  pyyaml (loads _system/build_kb.py for fold() and the strict YAML loader).
"""
import argparse, importlib.util, re, sys
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]

# ---------------------------------------------------------------- seeds for the patterned kinds (literal spellings as written)
DIRECTIVES = ('noindex', 'nofollow', 'noarchive', 'nosnippet', 'max-snippet', 'max-image-preview', 'max-video-preview', 'notranslate',
              'noimageindex', 'unavailable_after', 'indexifembedded', 'data-nosnippet', 'Disallow', 'Allow', 'crawl-delay', 'Crawl-delay',
              'User-agent', 'rel=canonical', 'rel="canonical"', 'canonical', 'hreflang', 'x-default', 'X-Robots-Tag', 'robots meta tag',
              'meta robots', 'rel=nofollow', 'rel="nofollow"', 'ugc', 'sponsored', 'nositelinkssearchbox', 'Vary', 'ETag', 'If-Modified-Since',
              'Last-Modified', 'Cache-Control', 'Retry-After', 'Content-Type', 'Accept-Encoding', 'robots.txt', 'Sitemap', 'sitemap')
CRAWLER_RE = re.compile(r'(?<![\w-])((?:[A-Z][A-Za-z]*)?[Bb]ot(?:-[A-Z][\w]*)*|Google-[A-Z][\w-]*|GoogleOther[\w-]*|Storebot-Google|'
                        r'Googlebot[\w-]*|AdsBot[\w-]*|Mediapartners-Google|APIs-Google|FeedFetcher-Google|Google-InspectionTool|'
                        r'CCBot|GPTBot|ClaudeBot|PerplexityBot|Bingbot|bingbot|Applebot[\w-]*|OAI-SearchBot|ChatGPT-User)(?![\w-])')
CRAWLERS = ('Googlebot', 'Googlebot-Image', 'Googlebot-Video', 'Googlebot-News', 'Googlebot Smartphone', 'Googlebot Desktop', 'Google-Extended',
            'GoogleOther', 'Storebot-Google', 'AdsBot', 'Google-InspectionTool', 'Google-CloudVertexBot', 'GPTBot', 'CCBot', 'ClaudeBot',
            'Bingbot', 'Applebot', 'user agent', 'user-agent', 'special-case crawlers', 'user-triggered fetchers', 'common crawlers')
REPORT_RE = re.compile(r'(?<![\w-])((?:[A-Z][\w-]*|[a-z][\w-]*)(?: (?:[A-Za-z][\w-]*)){0,3}) report(?:s)?(?![\w-])')
REPORTS = ('Crawl stats', 'Crawl Stats', 'Page indexing', 'URL Inspection', 'URL inspection', 'Performance report', 'Insights',
           'Search Console Insights', 'Core Web Vitals report', 'Manual actions', 'Security issues', 'Links report', 'Removals',
           'Merchant listings', 'Product snippets', 'rich result report', 'Video indexing', 'Sitemaps report', 'robots.txt report',
           'Generative AI performance report', 'generative AI performance', 'Search appearance', 'Discover report', 'News report',
           'Shopping tab listings', 'HTTPS report', 'Breadcrumbs', 'Change of Address', 'Change of address')
STANDARDS = ('RFC 9309', 'RFC 9110', 'RFC 9111', 'RFC', 'HTTP/1.1', 'HTTP/2', 'HTTP/3', 'QUIC', 'HTTPS', 'TLS', 'schema.org', 'Schema.org',
             'JSON-LD', 'Microdata', 'RDFa', 'llms.txt', 'Robots Exclusion Protocol', 'REP', 'sitemaps protocol', 'XML sitemap',
             'IndexNow', 'WebMCP', 'MCP', 'Model Context Protocol', 'Open Graph', 'AMP', 'IPv6', 'Brotli', 'gzip', 'HTML', 'CSS', 'JavaScript',
             'Unicode', 'UTF-8', 'ISO 639-1', 'ISO 3166-1', 'robots.txt', 'ads.txt', 'security.txt', 'WebP', 'AVIF', 'srcset', 'lazy-loading',
             'Agent2Agent', 'A2A', 'Universal Commerce Protocol', 'UCP', 'Agent Payments Protocol', 'AP2')
GOOGLE = ('Search Console', 'Google Search Console', 'GSC', 'Merchant Center', 'Google Merchant Center', 'Google Trends', 'Trends', 'Discover',
          'Google Discover', 'Gemini', 'Chrome', 'Chrome UX Report', 'CrUX', 'PageSpeed Insights', 'Lighthouse', 'Search Labs', 'AI Mode',
          'AI Overviews', 'AI Overview', 'Web Guide', 'Search profiles', 'Preferred sources', 'People Also Ask', 'Top stories', 'Google News',
          'Google Lens', 'Lens', 'Circle to Search', 'YouTube', 'Google Images', 'Google Maps', 'Business Profile', 'Google Business Profile',
          'Knowledge Graph', 'Knowledge Panel', 'knowledge panel', 'featured snippet', 'featured snippets', 'rich results', 'rich result',
          'sitelinks', 'Rich Results Test', 'Schema Markup Validator', 'Google Analytics', 'GA4', 'Looker Studio', 'BigQuery', 'Search Console API',
          'URL Inspection API', 'Indexing API', 'Google Ads', 'Vertex AI', 'Google Cloud', 'Gemini apps', 'Google Images', 'Shopping',
          'Google Shopping', 'Shopping Graph', 'Things to know', 'Perspectives', 'Search Central', 'Search Central Live', 'Search Off the Record',
          'Trends Explore', 'Trending now', 'Google Trends API', 'Agent Mode', 'Project Mariner', 'Deep Search', 'Search Live', 'AI Max',
          'universal search', 'BERT', 'RankBrain', 'MUM', 'PageRank', 'SpamBrain', 'Caffeine', 'Hummingbird', 'Panda', 'Penguin', 'Florida',
          'helpful content update', 'helpful content system', 'core update', 'core updates', 'spam update', 'spam updates', 'site reputation abuse',
          'Safe Browsing', 'Search Quality Rater Guidelines', 'quality rater guidelines', 'E-E-A-T', 'EEAT', 'Core Web Vitals', 'INP', 'LCP',
          'CLS', 'Interaction to Next Paint', 'Largest Contentful Paint', 'Cumulative Layout Shift', 'TTFB', 'crawl budget', 'crawl rate',
          'crawl demand', 'crawl capacity', 'query fan-out', 'fan-out', 'grounding', 'soft 404', 'duplicate content', 'canonicalization',
          'canonicalisation', 'faceted navigation', 'site move', 'structured data', 'tokenization', 'tokenisation', 'chunking', 'embeddings',
          'passage ranking', 'mobile-first indexing', 'hostload', 'Preferred Sources', 'Web Guide', 'Search generative AI control',
          'nosnippet', 'Search Generative Experience', 'SGE', 'AI Studio', 'NotebookLM', 'Google Search', 'Googlebot')
STATUS_CTX = re.compile(r'status|error|code|response|server|redirect|serv(?:e|es|ed|ing)|return', re.I)
CLASS_RE = re.compile(r'(?<![\w-])([1-5]xx)(?![\w-])', re.I)
CODE_RE = re.compile(r'(?<![\w.,/-])([1-5][0-5]\d)(?![\w.,%/-])')
RFC_RE = re.compile(r'(?<![\w-])(RFC ?\d{3,5})(?![\w-])')
HEADER_RE = re.compile(r'(?<![\w-])(X-[A-Z][\w-]+)(?![\w-])')
RELVAL_RE = re.compile(r'(?<![\w-])rel=["“]?([a-z-]+)')
GOOGLE_RE = re.compile(r'(?<![\w-])(Google [A-Z][\w-]+(?: [A-Z][\w-]+)?)(?![\w-])')
CAPS_RE = re.compile(r'(?<![\w-])([A-Z][\w.-]*(?: (?:of |to |the |and )?[A-Z][\w.-]*)+)(?![\w-])')


def build_kb(root):
    spec = importlib.util.spec_from_file_location('kb_build', root / '_system' / 'build_kb.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load(root, bk):
    C = root / '20-claims'
    rd = lambda p: bk.load_yaml(p.read_text(encoding='utf-8'))
    claims = []
    for f in sorted(C.glob('day*.yaml'), key=lambda p: int(re.sub(r'\D', '', p.stem) or 0)):
        claims += [c for c in rd(f) or [] if c.get('private') is not True]
    topics = [t['id'] for a in rd(C / 'topics.yaml')['areas'] for t in a['topics']]
    sources = rd(C / 'sources.yaml')
    content = rd(root / '25-kits' / 'content.yaml')
    reqs = [r for a in rd(root / '25-kits' / 'dev-requirements.yaml')['areas'] for r in a['requirements']]
    return claims, topics, sources, content, reqs


class Corpus:
    def __init__(self, claims, bk):
        self.bk = bk
        self.claims = sorted(claims, key=lambda c: c['id'])
        self.raw = {c['id']: (bk.nt(c.get('text') or ''), bk.nt(c.get('quote') or '')) for c in self.claims}
        self.fold = {k: (bk.fold(a), bk.fold(b)) for k, (a, b) in self.raw.items()}
        self.topics = {c['id']: list(c.get('topics') or []) for c in self.claims}
        self.cache = {}

    def hits(self, alias, cs=False, scope=None):
        """Claim ids where alias appears on (?<![\\w-]) (?![\\w-]) boundaries in text or quote; cs: raw text, case-sensitive."""
        key = (alias, cs, tuple(scope or ()))
        if key in self.cache: return self.cache[key]
        a = alias if cs else self.bk.fold(alias)
        rx = re.compile(r'(?<![\w-])' + re.escape(a) + r'(?![\w-])')
        src = self.raw if cs else self.fold
        out = [cid for cid, fields in src.items() if (not scope or set(scope) & set(self.topics[cid])) and any(rx.search(f) for f in fields)]
        self.cache[key] = out
        return out

    def stoplist(self, n=200):
        cnt = Counter(w for a, b in self.fold.values() for w in re.findall(r'[^\W_]+', a + ' ' + b))
        return [w for w, _ in sorted(cnt.items(), key=lambda x: (-x[1], x[0]))[:n]]

    def scan(self, rx, group=1, ctx=None):
        cnt = Counter()
        for cid, fields in self.raw.items():
            seen = set()
            for f in fields:
                for m in rx.finditer(f):
                    if ctx and not ctx.search(f[max(0, m.start() - 45):m.end() + 45]): continue
                    seen.add(m[group])
            cnt.update(seen)
        return cnt


def alias_rec(cp, a, stop):
    ci, cs = cp.hits(a), cp.hits(a, cs=True)
    tp = Counter(t for x in ci for t in cp.topics[x])
    rec = {'alias': a, 'ci': len(ci), 'cs': len(cs)}
    if cp.bk.fold(a) in stop: rec['stop_word'] = True
    if len(a) < 3: rec['needs_exact'] = True
    rec['topics'] = [f'{t} {n}' for t, n in sorted(tp.items(), key=lambda x: (-x[1], x[0]))[:4]]
    rec['examples'] = ci[:5]
    return rec, set(ci)


def candidate(cp, name, kind, seed, aliases, stop, sources, req_by_claim, own_claims=()):
    recs, union = [], set(own_claims)
    for a in dict.fromkeys(aliases):
        r, s = alias_rec(cp, a, stop)
        recs.append(r)
        union |= s
    names = {cp.bk.fold(a) for a in aliases if len(a) >= 3}
    docs = sorted(k for k, s in sources.items() if any(re.search(r'(?<![\w-])' + re.escape(n) + r'(?![\w-])', cp.bk.fold(s.get('title', ''))) for n in names))
    reqs = sorted({r for x in union for r in req_by_claim.get(x, ())})
    out = {'name': name, 'seed_kind': kind, 'seed': seed, 'mentions': len(union), 'aliases': recs}
    if own_claims: out['glossary_claims'] = list(own_claims)
    out['docs'] = docs[:8]
    out['requirements'] = reqs[:12]
    out['rule_of_thumb'] = len(union) >= 3 and bool(docs or reqs)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default=str(ROOT))
    ap.add_argument('--out', help='where to write entity-candidates.yaml (outside the repository)')
    ap.add_argument('--alias', action='append', help='print the hits of one alias (repeatable) instead of writing the report')
    ap.add_argument('--cs', action='store_true', help='with --alias: case-sensitive on the raw text')
    ap.add_argument('--in', dest='scope', help='with --alias: comma-separated topic ids the claim must carry')
    ap.add_argument('--show', type=int, default=8, help='with --alias: how many matching claims to print')
    a = ap.parse_args()
    root = Path(a.root).resolve()
    bk = build_kb(root)
    claims, topics, sources, content, reqs = load(root, bk)
    cp = Corpus(claims, bk)

    if a.alias:
        scope = [t for t in (a.scope or '').split(',') if t]
        for al in a.alias:
            ids = cp.hits(al, cs=a.cs, scope=scope)
            print(f'{al!r} cs={a.cs} in={scope or "-"}: {len(ids)} claims')
            for cid in ids[:a.show]:
                t = cp.raw[cid][0]
                f = cp.bk.fold(t) if not a.cs else t
                m = re.search(r'(?<![\w-])' + re.escape(al if a.cs else bk.fold(al)) + r'(?![\w-])', f)
                i = m.start() if m else 0
                print(f'   {cid}: ...{t[max(0, i - 60):i + 80]}...')
        return 0

    if not a.out: ap.error('--out is required (a path outside the repository) unless --alias is given')
    out = Path(a.out).resolve()
    if root in out.parents: ap.error('--out must be outside the repository: the candidate report never enters git')

    stop = cp.stoplist()
    stopset = set(stop)
    req_by_claim = {}
    for r in reqs:
        for x in r.get('claims', []): req_by_claim.setdefault(x, set()).add(r['id'])

    cands = []
    # glossary seed
    spec = importlib.util.spec_from_file_location('kb_kits', root / '_system' / 'kits.py')
    kits = importlib.util.module_from_spec(spec); spec.loader.exec_module(kits)
    for g in content['glossary']:
        al = kits.term_aliases(g['term'], bk)
        cands.append(candidate(cp, bk.nt(g['term']), 'glossary', 'glossary', al, stopset, sources, req_by_claim, g.get('claims', [])))

    # patterned seeds
    codes = cp.scan(CODE_RE, ctx=STATUS_CTX)
    classes = cp.scan(CLASS_RE)
    for code, n in sorted(codes.items()):
        if n >= 1: cands.append(candidate(cp, code, 'status-code', f'pattern: 3-digit code near status words ({n})', [code], stopset, sources, req_by_claim))
    for cl in sorted({c.lower() for c in classes}):
        cands.append(candidate(cp, cl, 'status-code', 'pattern: status class', [cl], stopset, sources, req_by_claim))
    for d in DIRECTIVES:
        cands.append(candidate(cp, d, 'directive', 'pattern: robots/meta directive or header seed', [d], stopset, sources, req_by_claim))
    for h, n in sorted(cp.scan(HEADER_RE).items()):
        cands.append(candidate(cp, h, 'directive', f'pattern: X-* header ({n})', [h], stopset, sources, req_by_claim))
    for v, n in sorted(cp.scan(RELVAL_RE).items()):
        cands.append(candidate(cp, f'rel={v}', 'directive', f'pattern: rel= value ({n})', [f'rel={v}', f'rel="{v}"', v], stopset, sources, req_by_claim))
    crawl = cp.scan(CRAWLER_RE)
    for c in sorted(set(CRAWLERS) | {k for k, n in crawl.items() if n >= 1}):
        cands.append(candidate(cp, c, 'crawler', 'pattern: crawler / user agent', [c], stopset, sources, req_by_claim))
    rep = cp.scan(REPORT_RE)
    for r in sorted(set(REPORTS) | {k for k, n in rep.items() if n >= 2}):
        cands.append(candidate(cp, r, 'report', 'pattern: Search Console report', [r, f'{r} report'] if not r.endswith('report') else [r], stopset, sources, req_by_claim))
    for s_ in sorted(set(STANDARDS) | set(cp.scan(RFC_RE))):
        cands.append(candidate(cp, s_, 'standard', 'pattern: standard / RFC', [s_], stopset, sources, req_by_claim))
    gp = cp.scan(GOOGLE_RE)
    for g in sorted(set(GOOGLE) | {k for k, n in gp.items() if n >= 3}):
        cands.append(candidate(cp, g, 'google', 'pattern: Google product / feature / concept seed', [g], stopset, sources, req_by_claim))

    covered = {bk.fold(r['alias']) for c in cands for r in c['aliases']}
    caps = cp.scan(CAPS_RE)
    unseeded = [f'{k} {n}' for k, n in sorted(caps.items(), key=lambda x: (-x[1], x[0])) if n >= 3 and bk.fold(k) not in covered][:300]

    cands.sort(key=lambda c: (c['seed_kind'], -c['mentions'], c['name']))
    doc = {'note': 'Generated by _system/tools/entity_candidates.py. Not part of the knowledge base; choose entities from it by hand.',
           'public_claims': len(cp.claims), 'stoplist': stop, 'candidates': cands, 'unseeded_capitalised_phrases': unseeded}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=140), encoding='utf-8')
    print(f'{len(cands)} candidates ({sum(c["rule_of_thumb"] for c in cands)} pass the rule of thumb), {len(unseeded)} unseeded phrases -> {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
