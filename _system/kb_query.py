"""Ask the knowledge base from the command line: cited answers from the agent pack, offline, standard library only.

Reads ONLY 60-outputs/agent-pack/ (the files rebuild.bat writes there); every file is opened through pack_file(), which refuses any
path outside that folder. Private claims, raw material and the author's notes are not in the pack, so they cannot be served.
Nothing is written, nothing is sent anywhere, and the same question always gives the same answer.

Usage:  python _system/kb_query.py <command> [options]          JSON (for agents)
        python _system/kb_query.py <command> [options] --text   readable text (for people)

  about                                   version, data through, counts, the citation rules, sessions with no coverage
  search <query> [--kind K] [--day N] [--label L] [--grade G] [--speaker S] [--limit N]
                                          the claims that best answer a question (BM25 over claim text and quote, with the
                                          spellings of the things and glossary terms, typo tolerance); --kind entity, topic,
                                          requirement, fact, myth, quote, angle, term or all searches the maps instead of claims
  entity <id-or-name>                     one thing's card; a misspelt name gives "did you mean"
  neighbours <node-id> [--hops 1|2] [--edge-types a,b] [--node-kinds a,b] [--limit N]
                                          what a node of graph.json is linked to (ent:googlebot, topic:robots-txt, D1-C108, ...)
  claims (--ids A,B | --entity X | --topic T | --session S) [--day N] [--label L] [--grade G] [--speaker S] [--limit N]
  evidence <claim-id>                     sources with URLs, grade, relations both ways, what rests on it, evidence references
  cite <claim-id> [<claim-id> ...]        the citation strings only
  ask                                     a question loop for people (ask.bat runs it)

  --label  slide, stage, docs, press, analysis, or event (= slide,stage); several with commas
  --grade  confirmed, consistent, undocumented, source, n/a, or documented (= confirmed, consistent and docs); several with commas
  --speaker  a proven speaker's name (only claims where the pack proves the name), or google, community, audience, unattributed

Every claim in a result carries `cite`, its citation in the form of AGENTS.md "How to cite" (a person is named only where the pack
proves the speaker), and every result carries `rules`. Exit codes: 0 answered, 1 not found or refused, 2 wrong usage.

The community edition: when the pack's content-library.json says "edition": "community", its facts, myths, story angles and quotes are a
short preview of the media kit. `about` then gives the edition, `search --kind fact|myth|quote|angle|all` adds an `edition_note`, and
`neighbours` on a kit id outside the preview answers that it is not part of this edition (not a crash, not "no thing called").
"""
import argparse, difflib, json, math, os, re, sys, textwrap, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = (ROOT / '60-outputs' / 'agent-pack').resolve()
AUTHOR = 'Ibrahim Anjro'
RULES = ('Cite the claim id for every factual statement, with its cite string. A card, a topic summary, a count and a graph edge are '
         'a map, not a source: cite the claim ids behind them. A slide or stage claim graded undocumented or n/a was said at Search '
         'Central Live, never documented policy. An analysis claim is the author\'s view, never Google\'s. An audience question is never '
         'Google\'s position: cite its answer. Name a person only where said_by is a proven name. If the pack does not cover a '
         'question, say so.')
LABELS = ('slide', 'stage', 'docs', 'press', 'analysis')
GRADES = ('confirmed', 'consistent', 'undocumented', 'source', 'n/a')
GRADE_MEANING = {'confirmed': "Google's documentation states the same thing",
                 'consistent': "Google's documentation supports it without stating it",
                 'undocumented': 'said or shown at the event, not in the documentation',
                 'source': 'the claim is the cited document itself',
                 'n/a': 'nothing to verify (a quotation, framing, an agenda fact, an audience question, an opinion or analysis)'}
LABEL_MEANING = {'slide': 'shown on a slide at Search Central Live', 'stage': 'said on stage at Search Central Live',
                 'docs': "Google's documentation", 'press': 'reported by a third-party publication', 'analysis': "the author's view"}
GROUPS = {'google': 'Google', 'community': 'a community speaker', 'unattributed': 'a speaker', 'audience': 'an audience member'}
KIT_KINDS = {'req': 'requirement', 'fact': 'fact', 'myth': 'myth', 'quote': 'quote', 'angle': 'angle', 'term': 'term'}
MAP_KINDS = ('entity', 'topic', 'requirement', 'fact', 'myth', 'quote', 'angle', 'term')
NODE_ORDER = ('entity', 'topic', 'area', 'requirement', 'fact', 'myth', 'quote', 'angle', 'term', 'source', 'session', 'day', 'claim')
CLAIM_ID = re.compile(r'^D\d+-C\d{3}$', re.I)
PREVIEW_KINDS = ('fact', 'myth', 'quote', 'angle')  # the media kit: a short preview in the community edition
KIT_ID = re.compile(r'^(?:(fact|myth|quote|angle):)?([FMQA])-\d{3}$', re.I)
EDITION_NOTE = ('This is the community edition: its facts, myths, story angles and quotes are a short preview of the media kit, which is not '
                'part of this edition. The claims, topics, things, the developer kit, the wording rules and the glossary are complete: answer '
                'from the claims and cite them.')


class Refused(Exception):
    """A path outside the agent pack."""


class NotFound(Exception):
    def __init__(self, msg, did_you_mean=None):
        super().__init__(msg)
        self.did_you_mean = did_you_mean or []


class Usage(Exception):
    pass


# ---------------------------------------------------------------- the path allowlist: the agent pack and nothing else

def pack_file(rel):
    """The path of a file inside the agent pack. Anything that resolves outside it (.., an absolute path, a link) is refused."""
    rel = str(rel).replace('\\', '/')
    p = (PACK / rel).resolve()
    if p == PACK or PACK not in p.parents:
        raise Refused(f'refused: {rel} is outside the agent pack ({PACK}); kb_query reads only the agent pack')
    if not p.is_file():
        raise NotFound(f'{rel} is not in the agent pack: run rebuild.bat first')
    return p


def read_json(rel):
    with open(pack_file(rel), encoding='utf-8') as f:
        return json.load(f)


def read_jsonl(rel):
    with open(pack_file(rel), encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------------------------------------------------------- text: the same fold() as the build and the web edition

SPELL = {'ł': 'l', 'đ': 'd', 'ð': 'd', 'ø': 'o', 'ı': 'i', 'ß': 'ss', 'æ': 'ae', 'œ': 'oe', 'þ': 'th', 'ς': 'σ'}


def fold(s):
    s = str(s or '')
    if s.isascii(): return s.lower()  # the same result, without the per-character work
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(SPELL.get(ch, ch) for ch in s if not unicodedata.category(ch).startswith('M'))


def words(s):
    return re.findall(r'[^\W_]+', fold(s))


def norm_key(s):  # the key of an alias in links.json
    return ' '.join(words(s))


def trigrams(w):
    w = f' {w} '
    return {w[i:i + 3] for i in range(len(w) - 2)}


def stem(w):
    """A light English suffix strip, used only to find the other forms of a question word in the index (detect, detects, detected;
    crawl, crawled, crawling). It never changes what is indexed or shown."""
    if len(w) <= 4 or not w.isalpha(): return w
    for suf, rep in (('ations', 'ate'), ('ation', 'ate'), ('ies', 'y'), ('ied', 'y'), ('ing', ''), ('ed', ''), ('es', ''), ('s', '')):
        if w.endswith(suf) and len(w) - len(suf) >= 3 and not w.endswith('ss'):
            w = w[:-len(suf)] + rep
            break
    return w[:-1] if len(w) > 3 and w.endswith('e') else w


FORM_WEIGHT = 0.6  # another form of a question word counts a little less than the word as typed (measured on the eval, see _system/eval)


QUESTION_WORDS = frozenset('a an the what whats which who whom how why when where does do did is are was were be been being about say says '
                           'said saying tell me us of to in on at for and or with it its this that these those there any can could should '
                           'would will i we you my our your s google googles googlers googler know explain mean means'.split())
EVERYDAY = frozenset('allow discover lens trends chrome'.split())  # names of things that are also everyday words in a question
K1, B = 1.2, 0.75
FIELD_WEIGHT = {'text': 1.0, 'quote': 0.6, 'ent': 0.8, 'topic': 0.3}  # the plan's 10, 6, 8, 3 as ratios


class Index:
    """BM25F in memory: per field length normalisation, field weights, one posting list per term."""

    def __init__(self, docs, weights):
        self.ids = [d for d, _ in docs]
        n, avg = len(docs), {}
        for f in weights:
            avg[f] = (sum(len(fields.get(f, ())) for _, fields in docs) / n) if n else 1.0
        post = defaultdict(dict)
        for i, (_, fields) in enumerate(docs):
            acc = {}
            for f, toks in fields.items():
                if not toks: continue
                c = weights[f] / (1 - B + B * len(toks) / (avg[f] or 1.0))
                for t in toks: acc[t] = acc.get(t, 0.0) + c
            for t, v in acc.items(): post[t][i] = v
        self.post, self.df = post, {t: len(p) for t, p in post.items()}
        self.n = n
        self.vocab = {t: self.df[t] for t in self.df if not t.startswith('\x01')}

    def idf(self, t):
        df = self.df.get(t, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def score(self, terms):
        """terms: [(term, weight)]. Returns {doc index: score}."""
        out = defaultdict(float)
        for t, wt in terms:
            p = self.post.get(t)
            if not p: continue
            idf = self.idf(t) * wt
            for i, tf in p.items(): out[i] += idf * tf / (K1 + tf)
        return out


# ---------------------------------------------------------------- the pack, loaded lazily

class KB:
    def __init__(self):
        self._c = {}

    def _get(self, key, fn):
        if key not in self._c: self._c[key] = fn()
        return self._c[key]

    @property
    def claims(self):
        return self._get('claims', lambda: {c['id']: c for c in read_jsonl('claims.jsonl')})

    @property
    def order(self):  # claim id -> position in claims.jsonl (day, then file order), the deterministic tie-break
        return self._get('order', lambda: {cid: i for i, cid in enumerate(self.claims)})

    @property
    def links(self):
        return self._get('links', lambda: read_json('links.json'))

    @property
    def ents(self):
        return self._get('ents', lambda: read_json('entities.json'))

    @property
    def ent(self):
        return self._get('ent', lambda: {x['id']: x for x in self.ents['entities']})

    @property
    def topics(self):
        def load():
            T = read_json('topics.json')
            return {t['id']: dict(t, area=a['id'], area_title=a['title']) for a in T['areas'] for t in a['topics']}, T
        return self._get('topics', load)[0]

    @property
    def sessions(self):
        def load():
            S = read_json('sessions.json')
            return {s['id']: dict(s, day=d['day'], date=d['date']) for d in S['days'] for s in d['sessions']}, S
        return self._get('sessions', load)[0]

    @property
    def sessions_raw(self):
        self.sessions
        return self._c['sessions'][1]

    @property
    def sources(self):
        return self._get('sources', lambda: read_json('sources.json'))

    @property
    def edition(self):  # 'community' when content-library.json says so; the full edition's library has no `edition` key
        def load():
            try:
                lib = read_json('content-library.json')
            except (NotFound, Refused, ValueError):
                return 'full'
            return lib.get('edition', 'full') if isinstance(lib, dict) else 'full'
        return self._get('edition', load)

    @property
    def graph(self):
        def load():
            G = read_json('graph.json')
            nodes = {n['id']: n for n in G['nodes']}
            adj = defaultdict(list)
            for e in G['edges']:
                adj[e['from']].append((e, 'out', e['to']))
                adj[e['to']].append((e, 'in', e['from']))
            return {'raw': G, 'nodes': nodes, 'adj': adj}
        return self._get('graph', load)

    # -------- who said it, and the citation

    def speaker(self, cid):
        return self.links['speakers']['claims'].get(cid) or {}

    def said_by(self, c):
        """A proven name, or Google, a community speaker, a speaker, an audience member; the publisher(s); the author."""
        if c['label'] == 'analysis': return AUTHOR
        if c['label'] in ('docs', 'press'): return ', '.join(dict.fromkeys(s['publisher'] for s in c['sources']))
        s = self.speaker(c['id'])
        return s.get('name') or GROUPS.get(s.get('group'), 'a speaker')

    def cite(self, cid):
        c = self.claims[cid]
        if c['label'] == 'analysis': return f"[{cid}, analysis, {AUTHOR}]"
        if c['label'] in ('docs', 'press'):
            url = c['sources'][0]['url'] if c['sources'] else ''
            return f"[{cid}, {c['label']}, {self.said_by(c)}, {url}]"
        return f"[{cid}, {c['label']}, {self.said_by(c)}, Day {c['day']}]"

    def item_name(self, nid):
        if nid.startswith('ent:'):
            x = self.ent.get(nid[4:])
            return x['name'] if x else None
        if nid.startswith('topic:'):
            t = self.topics.get(nid[6:])
            return t['title'] if t else None
        it = self.links['items'].get(nid)
        return it['name'] if it else None

    # -------- search indexes

    @property
    def claim_index(self):
        def build():
            docs = []
            terms_of = defaultdict(list)
            for nid, it in self.links['items'].items():
                if nid.startswith('term:'):
                    for cid in it['claims']: terms_of[cid].append(nid)
            spell = {'ent:' + x['id']: words(' '.join([x['name']] + x['aliases'])) + ['\x01ent:' + x['id']] for x in self.ents['entities']}
            spell.update({t: words(it['name']) + ['\x01' + t] for t, it in self.links['items'].items() if t.startswith('term:')})
            ttl = {t['id']: words(t['title']) for t in self.topics.values()}
            for cid, c in self.claims.items():
                ent = []
                for m in c.get('mentions', []): ent += spell.get('ent:' + m['entity'], [])
                for t in terms_of.get(cid, []): ent += spell[t]
                docs.append((cid, {'text': words(c['text']), 'quote': words(c.get('quote') or ''), 'ent': ent,
                                   'topic': [w for t in c['topics'] for w in ttl.get(t, [])]}))
            return Index(docs, FIELD_WEIGHT)
        return self._get('claim_index', build)

    @property
    def map_index(self):
        def build():
            docs = []
            for x in self.ents['entities']:
                docs.append(('ent:' + x['id'], {'text': words(' '.join([x['name']] + x['aliases'])) + ['\x01ent:' + x['id']],
                                                'quote': words(x['summary'] or ''), 'ent': [], 'topic': []}))
            for t in self.topics.values():
                docs.append(('topic:' + t['id'], {'text': words(t['title']), 'quote': words(t['summary']), 'ent': [], 'topic': []}))
            for nid in sorted(self.links['items']):
                it = self.links['items'][nid]
                docs.append((nid, {'text': words(it['name']) + (['\x01' + nid] if nid.startswith('term:') else []),
                                   'quote': [], 'ent': [], 'topic': []}))
            return Index(docs, FIELD_WEIGHT)
        return self._get('map_index', build)

    @property
    def aliases(self):
        """norm_key(spelling) -> sorted node ids (ent:, term:), and the keys that need the spelling's capitals in a question."""
        def build():
            A = defaultdict(set)
            caps = defaultdict(set)  # key -> capitalised exact spellings (Allow, Discover, Lens)
            loose = set()            # keys some case-insensitive spelling also produces
            for k, ids in self.links['aliases'].items():
                A[k].update(ids)
                if any(i.startswith('term:') for i in ids) and not EVERYDAY & set(k.split()): loose.add(k)  # a glossary spelling: any case
            for x in self.ents['entities']:
                for s in [x['name'], *x['aliases']]: A[norm_key(s)].add('ent:' + x['id'])
                A[norm_key(x['id'].replace('-', ' '))].add('ent:' + x['id'])
                for m in x['match']:
                    k = norm_key(m['s'])
                    A[k].add('ent:' + x['id'])
                    if m['exact'] and (re.fullmatch(r'[A-Z][a-z]+', m['s']) or (' ' in k and EVERYDAY & set(k.split()))): caps[k].add(m['s'])
                    elif not m['exact'] and m['in'] is None: loose.add(k)
            low, cap = Counter(), Counter()  # how the claims write the word: lower case (a common word) or capitalised (a name)
            for c in self.claims.values():
                for w in re.findall(r'\b[A-Za-z]+\b', c['text']): (low if w.islower() else cap)[w.lower()] += 1
            strict = {k: v for k, v in caps.items() if k not in loose and (' ' in k or k in EVERYDAY or low[k] >= cap[k])}
            return {k: sorted(v) for k, v in A.items() if k}, strict
        return self._get('aliases', build)


# ---------------------------------------------------------------- views of a claim

def claim_brief(kb, cid, score=None):
    c = kb.claims[cid]
    v = {'id': cid, 'cite': kb.cite(cid), 'label': c['label'], 'verification': c['verification'], 'day': c['day'],
         'said_by': kb.said_by(c), 'text': c['text']}
    if c.get('quote'): v['quote'] = c['quote']
    if score is not None: v['score'] = round(score, 3)
    return v


def claim_full(kb, cid, score=None):
    c = kb.claims[cid]
    v = claim_brief(kb, cid, score)
    v.update({'session_id': c['session_id'], 'session': c['session'], 'topics': c['topics'],
              'sources': [{'key': s['key'], 'title': s['title'], 'url': s['url']} for s in c['sources']],
              'mentions': [m['entity'] for m in c.get('mentions', [])], 'used_by': c.get('used_by', []),
              'relations': c.get('relations', []), 'related_from': c.get('related_from', [])})
    if 'quote' in v: v['quote_checked'] = c.get('quote_checked') is True
    return v


def kind_of(nid):
    p = nid.split(':', 1)[0]
    return {'ent': 'entity', 'topic': 'topic'}.get(p) or KIT_KINDS.get(p) or p


def map_item(kb, nid, score=None):
    k = kind_of(nid)
    if k == 'entity':
        x = kb.ent[nid[4:]]
        v = {'id': nid, 'kind': 'entity', 'entity_kind': x['kind'], 'name': x['name'], 'summary': x['summary'],
             'file': f"entities/{x['id']}.md", 'claims': x['claims']}
    elif k == 'topic':
        t = kb.topics[nid[6:]]
        v = {'id': nid, 'kind': 'topic', 'name': t['title'], 'summary': t['summary'], 'file': f"topics/{t['id']}.md",
             'claims': t.get('cites') or [], 'claims_note': 'the claims its summary is based on'}
    else:
        it = kb.links['items'][nid]
        v = {'id': nid, 'kind': k, 'name': it['name'], 'file': it['file'], 'claims': it['claims']}
    if score is not None: v['score'] = round(score, 3)
    return v


# ---------------------------------------------------------------- filters

def split_list(v):
    return [x.strip() for x in re.split(r'[,\s]+', v or '') if x.strip()]


def parse_filters(kb, a):
    F = {}
    if getattr(a, 'label', None):
        ls = set()
        for x in split_list(a.label.lower()):
            if x == 'event': ls |= {'slide', 'stage'}
            elif x in LABELS: ls.add(x)
            else: raise Usage(f"--label {x}: use one of {', '.join(LABELS)} or event")
        F['label'] = ls
    if getattr(a, 'grade', None):
        gs = set()
        for x in split_list(a.grade.lower()):
            if x in ('na', 'n-a', 'none'): x = 'n/a'
            if x == 'documented': gs |= {'confirmed', 'consistent', '+docs'}
            elif x in GRADES: gs.add(x)
            else: raise Usage(f"--grade {x}: use one of {', '.join(GRADES)} or documented")
        F['grade'] = gs
    if getattr(a, 'day', None) is not None:
        try:
            F['day'] = {int(x) for x in split_list(str(a.day))}
        except ValueError:
            raise Usage(f'--day {a.day}: use a day number, for example 2 (several with commas)')
    if getattr(a, 'speaker', None):
        F['speaker'] = resolve_speaker(kb, a.speaker)
    return F


def resolve_speaker(kb, s):
    k = fold(s).strip()
    groups = {'google': 'google', 'googler': 'google', 'community': 'community', 'a community speaker': 'community',
              'audience': 'audience', 'unattributed': 'unattributed'}
    if k in groups: return ('group', groups[k])
    names = [x['name'] for x in kb.links['speakers']['names']]
    hit = [n for n in names if fold(n) == k] or [n for n in names if k and k in fold(n)]
    if len(hit) == 1: return ('name', hit[0])
    if len(hit) > 1: raise Usage(f"--speaker {s} matches {', '.join(hit)}: give the full name")
    raise NotFound(f"--speaker {s}: not a proven speaker. A person is named only where the pack proves it; the proven names are: "
                   f"{', '.join(names)}; or use google, community, audience")


def passes(kb, cid, F):
    c = kb.claims[cid]
    if 'label' in F and c['label'] not in F['label']: return False
    if 'grade' in F and not (c['verification'] in F['grade'] or ('+docs' in F['grade'] and c['label'] == 'docs')): return False
    if 'day' in F and c['day'] not in F['day']: return False
    if 'speaker' in F:
        how, v = F['speaker']
        if c['label'] not in ('slide', 'stage'): return False
        sp = kb.speaker(cid)
        if (how == 'name' and sp.get('name') != v) or (how == 'group' and sp.get('group') != v): return False
    return True


def filters_used(F):
    out = {}
    for k, v in F.items():
        if k == 'speaker': out[k] = v[1]
        elif isinstance(v, set): out[k] = sorted(str(x).replace('+docs', 'docs') for x in v)
    return out


# ---------------------------------------------------------------- search

def find_aliases(kb, toks, raw, skipped=None):
    """Spellings of things and glossary terms in the question, longest first, left to right: [(spelling, [node ids])]. A thing whose
    name is also an everyday word (Allow, Discover) counts only when the question writes it with its capitals or is only that name;
    the ids of such a skipped spelling are added to `skipped`."""
    A, strict = kb.aliases
    content = [t for t in toks if t not in QUESTION_WORDS]
    out, i = [], 0
    while i < len(toks):
        for n in range(min(6, len(toks) - i), 0, -1):
            k = ' '.join(toks[i:i + n])
            if k in A and not (n == 1 and k in QUESTION_WORDS):
                if k in strict and not any(s in raw for s in strict[k]) and content != [w for w in k.split() if w not in QUESTION_WORDS]:
                    if skipped is not None: skipped.update(A[k])
                    continue
                out.append((k, A[k])); i += n
                break
        else:
            i += 1
    return out


def osa(a, b, cap):
    """Damerau-Levenshtein distance (optimal string alignment), or cap + 1 once it is certainly larger than cap."""
    if abs(len(a) - len(b)) > cap: return cap + 1
    prev2, prev = None, list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]: cur[j] = min(cur[j], prev2[j - 2] + 1)
        if min(cur) > cap: return cap + 1
        prev2, prev = prev, cur
    return prev[-1]


def correct(index, toks):
    """Typo and prefix tolerance, used when a question finds fewer than 3 claims. A word of 4+ letters the index does not know
    becomes its closest known word (Damerau-Levenshtein distance 1, 2 from 8 letters, or close trigrams), the most frequent first;
    a word of 3+ letters also matches, at a lower score, the words it starts. Returns (words, extra prefix terms, {typed: shown})."""
    V = index.vocab
    if not hasattr(index, 'tri'):
        tri = defaultdict(list)
        for w in V:
            for g in trigrams(w): tri[g].append(w)
        index.tri = tri
    fixed, extra, notes = [], [], {}
    for t in toks:
        if t in QUESTION_WORDS or len(t) < 3 or t.isdigit():
            fixed.append(t); continue
        w = t
        if t not in V and len(t) >= 4:
            g, cap = trigrams(t), (1 if len(t) < 8 else 2)
            best = None
            for c, shared in Counter(x for gg in g for x in index.tri.get(gg, ())).items():
                dice = 2 * shared / (len(g) + len(trigrams(c)))
                d = osa(t, c, cap)
                if d > cap and dice < 0.6: continue
                key = (min(d, cap + 1), -round(dice, 6), -V[c], c)
                if best is None or key < best[0]: best = (key, c)
            if best: w = best[1]; notes[t] = w
        fixed.append(w)
        pre = sorted((x for x in V if x.startswith(w) and x != w), key=lambda x: (-V[x], x))[:5]
        extra += [(x, 0.5) for x in pre]
        if pre and t not in notes: notes[t] = w + '*'
    return fixed, extra, notes


def run_search(kb, query, F, kind='claim', limit=10):
    raw = query or ''
    toks = words(raw)
    if not toks: raise Usage('search needs a question or some words')
    index = kb.claim_index if kind == 'claim' else kb.map_index

    skipped = set()

    def terms_for(tk):
        found = find_aliases(kb, tk, raw, skipped)
        content = [t for t in tk if t not in QUESTION_WORDS] or tk
        terms = [(t, 1.0) for t in content]
        if not hasattr(index, 'forms'):
            forms = defaultdict(list)
            for w in sorted(index.vocab): forms[stem(w)].append(w)
            index.forms = forms
        terms += [(w, FORM_WEIGHT) for t in dict.fromkeys(content) for w in index.forms.get(stem(t), ()) if w != t]
        for _, ids in found:
            terms += [('\x01' + nid, 1.0) for nid in ids]
        return terms, found

    def hits(terms):
        sc = index.score(terms)
        out = []
        for i, s in sc.items():
            nid = index.ids[i]
            if kind == 'claim':
                if not passes(kb, nid, F): continue
            elif kind != 'all' and kind_of(nid) != kind:
                continue
            out.append((nid, s))
        rank = kb.order if kind == 'claim' else {}
        out.sort(key=lambda x: (-round(x[1], 9), rank.get(x[0], 0), x[0]))
        return out

    terms, found = terms_for(toks)
    res, note, typed = hits(terms), None, None
    if len(res) < 3:
        fixed, extra, notes = correct(index, toks)
        if notes:
            t2, f2 = terms_for(fixed)
            r2 = hits(t2 + extra)
            if len(r2) > len(res):
                res, found = r2, f2
                shown = ' '.join(notes.get(t, t) for t in toks)
                note = f'Showing results for "{shown}" (you typed "{raw.strip()}")'
                typed = {k: v for k, v in sorted(notes.items())}
    things = []
    for _, ids in found:
        for nid in ids:
            if nid.startswith('ent:') and nid not in things: things.append(nid)
            if nid.startswith('term:'):  # a glossary term: the things it defines
                for x in kb.ents['entities']:
                    if x.get('glossary') == nid[5:] and 'ent:' + x['id'] not in things: things.append('ent:' + x['id'])
    if not things and kind == 'claim':  # no spelling of a thing in the question: the thing most of the top claims mention
        skip = {i[4:] for i in skipped if i.startswith('ent:')}  # an everyday word (discover, allow) is not the thing's name here
        n = Counter(m['entity'] for cid, _ in res[:10] for m in kb.claims[cid].get('mentions', []) if m['entity'] not in skip)
        top = sorted(n.items(), key=lambda x: (-x[1], x[0]))
        if top and top[0][1] >= 2: things = ['ent:' + top[0][0]]
    out = {'query': raw, 'kind': kind}
    preview = kind in PREVIEW_KINDS + ('all',) and kb.edition == 'community'
    if preview: out['edition_note'] = EDITION_NOTE
    if note: out['note'], out['corrected'] = note, typed
    if F: out['filters'] = filters_used(F)
    out['matched'] = [{'spelling': k, 'ids': ids} for k, ids in found]
    out['things'] = [thing_brief(kb, nid[4:]) for nid in things[:3]]
    if kind == 'claim' and res:  # the topics the best claims belong to: `claims --topic` reads all of one, for a question with several parts
        tc = Counter(t for cid, _ in res[:max(limit, 12)] for t in kb.claims[cid]['topics'] if t in kb.topics)
        out['topics'] = [{'id': 'topic:' + t, 'title': kb.topics[t]['title'], 'in_results': n,
                          'claims': sum(1 for c in kb.claims.values() if t in c['topics']), 'more': f'claims --topic {t}'}
                         for t, n in sorted(tc.items(), key=lambda x: (-x[1], x[0]))[:3]]
    out['total'] = len(res)
    out['results'] = [(claim_brief(kb, nid, s) if kind == 'claim' else map_item(kb, nid, s)) for nid, s in res[:limit]]
    if not res and preview and kind != 'all':
        out['answer'] = ('Nothing in the media kit preview matches. The full media kit is not part of this community edition: search the claims '
                         'instead (search without --kind) and cite them.')
    elif not res: out['answer'] = 'The pack has no claim that matches. Say that the knowledge base does not cover it.'
    out['rules'] = RULES
    return out


def thing_brief(kb, eid):
    x = kb.ent[eid]
    return {'id': 'ent:' + eid, 'kind': x['kind'], 'name': x['name'], 'aliases': x['aliases'], 'summary': x['summary'],
            'claims': len(x['claims']), 'tally': x['tally'], 'file': f'entities/{eid}.md'}


# ---------------------------------------------------------------- entity

def resolve_entity(kb, q):
    """An entity id from an id, a name, a spelling, a glossary term, or (fuzzy) a near miss. Returns (id, note)."""
    s = str(q).strip()
    if s.lower().startswith('ent:'): s = s[4:]
    if s in kb.ent: return s, None
    if s.lower() in kb.ent: return s.lower(), None
    A, _ = kb.aliases
    k = norm_key(s)
    ids = A.get(k, [])
    ents = [i[4:] for i in ids if i.startswith('ent:')]
    if not ents:
        for i in ids:
            if i.startswith('term:'):
                ents += [x['id'] for x in kb.ents['entities'] if x.get('glossary') == i[5:]]
    if len(ents) == 1: return ents[0], None
    if len(ents) > 1:
        raise NotFound(f'"{q}" names several things: ' + ', '.join(ents), [{'id': 'ent:' + e, 'name': kb.ent[e]['name']} for e in ents])
    # fuzzy: every spelling of every thing, by similarity
    spell = {}
    for kk, ii in A.items():
        for i in ii:
            if i.startswith('ent:'): spell.setdefault(kk, set()).add(i[4:])
    g = trigrams(k)
    scored = []
    for kk, es in spell.items():
        r = difflib.SequenceMatcher(None, k, kk).ratio()
        d = 2 * len(g & trigrams(kk)) / (len(g) + len(trigrams(kk)))
        pre = 0.9 if len(k) >= 3 and kk.startswith(k) else 0
        sc = max(r, d, pre)
        for e in es: scored.append((sc, e, kk))
    best = {}
    for sc, e, kk in sorted(scored, key=lambda x: (-x[0], x[1], x[2])):
        if e not in best: best[e] = (sc, kk)
    ranked = sorted(best.items(), key=lambda x: (-x[1][0], x[0]))
    if ranked and ranked[0][1][0] >= 0.8 and (len(ranked) == 1 or ranked[0][1][0] - ranked[1][1][0] >= 0.05):
        e = ranked[0][0]
        return e, f'Showing {kb.ent[e]["name"]} (you typed "{q}")'
    dym = [{'id': 'ent:' + e, 'name': kb.ent[e]['name'], 'spelling': kk} for e, (sc, kk) in ranked[:5] if sc >= 0.5]
    raise NotFound(f'No thing called "{q}" in the pack.' + (' Did you mean: ' + ', '.join(d['name'] for d in dym) + '?' if dym else
                   ' Try search instead.'), dym)


def run_entity(kb, q):
    eid, note = resolve_entity(kb, q)
    x = kb.ent[eid]
    cl = x['claims']
    groups = {'documentation': [], 'event_undocumented': [], 'event_documented': [], 'event_not_checked': [], 'press': [], 'analysis': []}
    for cid in sorted(cl, key=lambda c: kb.order[c]):
        c = kb.claims[cid]
        if c['label'] == 'docs': g = 'documentation'
        elif c['label'] in ('press', 'analysis'): g = c['label']
        elif c['verification'] == 'undocumented': g = 'event_undocumented'
        elif c['verification'] in ('confirmed', 'consistent'): g = 'event_documented'
        else: g = 'event_not_checked'
        groups[g].append(claim_brief(kb, cid))
    src = kb.sources
    card = {
        'id': 'ent:' + eid, 'kind': x['kind'], 'name': x['name'], 'aliases': x['aliases'], 'summary': x['summary'],
        'glossary': ('term:' + x['glossary']) if x.get('glossary') else None, 'definition': x.get('definition'),
        'file': f'entities/{eid}.md',
        'topics': [{'id': 'topic:' + t, 'title': kb.topics[t]['title'], 'file': f'topics/{t}.md'} for t in x['topics'] if t in kb.topics],
        'docs': [{'key': k, 'title': src[k]['title'], 'url': src[k]['url'], 'checked': src[k]['checked']} for k in x['docs'] if k in src],
        'tally': x['tally'],
        'rel': [dict(r, name=kb.ent[r['to']]['name'], cite=[kb.cite(c) for c in r['claims']]) for r in x['rel'] if r['to'] in kb.ent],
        'rel_from': [dict(r, name=kb.ent[r['from']]['name'], cite=[kb.cite(c) for c in r['claims']])
                     for r in x['rel_from'] if r.get('from') in kb.ent],
        'co_mentioned': [{'id': 'ent:' + m['id'], 'name': kb.ent[m['id']]['name'], 'count': m['count'], 'claims': m['claims']}
                         for m in x['co_mentioned'] if m['id'] in kb.ent],
        'featured_in': [{'id': 'topic:' + f['id'], 'title': kb.topics[f['id']]['title'], 'count': f['count']}
                        for f in x['featured_in'] if f['id'] in kb.topics],
        'items': [dict(i, kind=kind_of(i['id']), name=kb.item_name(i['id'])) for i in x['items']],
        'claims': groups,
    }
    out = {'entity': card}
    if note: out['note'] = note
    out['about'] = ('A card is a map, not a source: cite the claim ids it lists. Claims are grouped: Google\'s documentation; '
                    'said or shown at the event and not in the documentation; at the event and backed by it; at the event with '
                    'nothing to verify; press; the author\'s analysis.')
    out['rules'] = RULES
    return out


# ---------------------------------------------------------------- neighbours

def resolve_node(kb, q):
    G = kb.graph['nodes']
    s = str(q).strip()
    if s in G: return s
    if CLAIM_ID.match(s) and 'claim:' + s.upper() in G: return 'claim:' + s.upper()
    if ':' in s:
        p, rest = s.split(':', 1)
        if p.lower() == 'claim' and 'claim:' + rest.upper() in G: return 'claim:' + rest.upper()
        if p.lower() in ('ent', 'entity'):
            return 'ent:' + resolve_entity(kb, rest)[0]
    for p in ('topic', 'session', 'area', 'source', 'req', 'fact', 'myth', 'quote', 'angle', 'term', 'day'):
        for cand in (f'{p}:{s}', f'{p}:{s.upper()}', f'{p}:{s.lower()}'):
            if cand in G: return cand
    if KIT_ID.match(s) and kb.edition == 'community':  # a fact, myth, quote or angle of the full media kit
        keep = [n for n in sorted(G) if n.split(':', 1)[0] in PREVIEW_KINDS]
        raise NotFound(f'{s} is not part of this community edition: the media kit here is a short preview ({", ".join(keep)}). '
                       'Search the claims instead (search "your question") and cite them.')
    return 'ent:' + resolve_entity(kb, s)[0]


def node_view(kb, nid):
    n = kb.graph['nodes'][nid]
    v = {'id': nid, 'kind': n['kind'], 'name': n['name']}
    if n.get('url'): v['url'] = n['url']
    if n['kind'] == 'claim':
        cid = nid[6:]
        v.update({'label': n.get('label'), 'verification': n.get('ver'), 'day': n.get('day'), 'cite': kb.cite(cid)})
    if n.get('entity_kind'): v['entity_kind'] = n['entity_kind']
    return v


def run_neighbours(kb, q, hops=1, edge_types=None, node_kinds=None, limit=100):
    start = resolve_node(kb, q)
    adj, raw = kb.graph['adj'], kb.graph['raw']
    et = set(split_list(edge_types)) if edge_types else None
    nk = set(split_list(node_kinds)) if node_kinds else None
    if et:
        bad = et - set(raw['edge_types'])
        if bad: raise Usage(f"--edge-types {', '.join(sorted(bad))}: use {', '.join(sorted(raw['edge_types']))}")
    if nk:
        alias = {'ent': 'entity', 'req': 'requirement'}
        nk = {alias.get(k, k) for k in nk}
        bad = nk - set(raw['node_kinds'])
        if bad: raise Usage(f"--node-kinds {', '.join(sorted(bad))}: use {', '.join(sorted(raw['node_kinds']))}")
    if hops not in (1, 2): raise Usage('--hops is 1 or 2')
    seen, ring, frontier, edges = {start: 0}, {}, [start], []
    for h in (1, 2)[:hops]:
        nxt = []
        for a in frontier:
            for e, d, b in sorted(adj.get(a, []), key=lambda x: (x[0]['type'], x[2], x[1])):
                if et and e['type'] not in et: continue
                if b not in seen:
                    seen[b] = h; nxt.append(b)
                if seen[b] == h:
                    edges.append((h, e, d, a, b))
        frontier = sorted(set(nxt))
    nodes = [b for b, h in seen.items() if h > 0 and (not nk or kb.graph['nodes'][b]['kind'] in nk)]

    def weight(b):
        return max((e.get('count') or 1) for h, e, d, a, bb in edges if bb == b)
    korder = {k: i for i, k in enumerate(NODE_ORDER)}
    nodes.sort(key=lambda b: (seen[b], korder.get(kb.graph['nodes'][b]['kind'], 99), -weight(b), b))
    shown = set(nodes[:limit])
    out_edges = []
    for h, e, d, a, b in edges:
        if b not in shown: continue
        ed = {'from': e['from'], 'to': e['to'], 'type': e['type']}
        for k in ('count', 'via', 'field', 'own', 'claims'):
            if k in e: ed[k] = e[k]
        out_edges.append(ed)
    by_kind = Counter(kb.graph['nodes'][b]['kind'] for b in nodes)
    return {'node': node_view(kb, start), 'hops': hops, 'filters': {'edge_types': sorted(et) if et else None, 'node_kinds': sorted(nk) if nk else None},
            'total': len(nodes), 'by_kind': dict(sorted(by_kind.items())),
            'neighbours': [dict(node_view(kb, b), hop=seen[b]) for b in nodes[:limit]], 'edges': out_edges,
            'about': 'A node or an edge is a map, never a source: cite the claim ids behind it (a claim node carries its cite; a co-mentioned or factual edge lists its claims).',
            'rules': RULES}


# ---------------------------------------------------------------- claims, evidence, cite

def claim_id(kb, s):
    s = str(s).strip().strip(',;[]')
    if s.lower().startswith('claim:'): s = s[6:]
    s = s.upper()
    if not CLAIM_ID.match(s): raise Usage(f'{s}: a claim id looks like D1-C108')
    if s not in kb.claims:
        raise NotFound(f'{s} is not in the pack: it does not exist or it is private (private claims are never served)')
    return s


def run_claims(kb, a):
    F = parse_filters(kb, a)
    sel = [x for x in ('ids', 'entity', 'topic', 'session') if getattr(a, x, None)]
    if len(sel) != 1: raise Usage('claims needs exactly one of --ids, --entity, --topic, --session')
    how, note, missing = sel[0], None, []
    if how == 'ids':
        ids = []
        for s in split_list(a.ids):
            try: ids.append(claim_id(kb, s))
            except NotFound: missing.append(s.upper())
        scope = {'ids': ids}
    elif how == 'entity':
        eid, note = resolve_entity(kb, a.entity)
        ids, scope = list(kb.ent[eid]['claims']), {'entity': 'ent:' + eid}
    elif how == 'topic':
        t = a.topic[6:] if a.topic.startswith('topic:') else a.topic
        if t not in kb.topics:
            close = difflib.get_close_matches(t, list(kb.topics), 5, 0.5)
            hit = [k for k, v in kb.topics.items() if norm_key(v['title']) == norm_key(a.topic)]
            if len(hit) == 1: t = hit[0]
            else: raise NotFound(f'no topic {a.topic}', [{'id': 'topic:' + c, 'title': kb.topics[c]['title']} for c in close])
        ids, scope = [c for c in kb.claims if t in kb.claims[c]['topics']], {'topic': 'topic:' + t}
    else:
        s = a.session[8:] if a.session.startswith('session:') else a.session
        s = s.upper()
        if s not in kb.sessions: raise NotFound(f'no session {a.session}', difflib.get_close_matches(s, list(kb.sessions), 5, 0.6))
        ids, scope = [c for c in kb.claims if kb.claims[c]['session_id'] == s], {'session': 'session:' + s}
        if not ids and kb.sessions[s]['claim_count'] == 0:
            note = 'Nothing was captured in this session, so the pack cannot say what was said there.'
    if how != 'ids': ids = sorted(ids, key=lambda c: kb.order[c])
    ids = [c for c in ids if passes(kb, c, F)]
    out = {'scope': scope}
    if F: out['filters'] = filters_used(F)
    if note: out['note'] = note
    if missing: out['missing'] = missing; out['missing_note'] = 'not in the pack: they do not exist or are private'
    lim = a.limit if a.limit is not None else (len(ids) if how == 'ids' else 50)
    out.update({'total': len(ids), 'shown': min(lim, len(ids)), 'claims': [claim_full(kb, c) for c in ids[:lim]], 'rules': RULES})
    return out


def run_evidence(kb, q):
    cid = claim_id(kb, q)
    c = kb.claims[cid]
    rel = []
    for r in c.get('relations', []):
        if r['to'] in kb.claims: rel.append(dict(claim_brief(kb, r['to']), type=r['type'], direction=f"this claim {r['type']} it"))
    for r in c.get('related_from', []):
        if r['from'] in kb.claims: rel.append(dict(claim_brief(kb, r['from']), type=r['type'], direction=f"it {r['type']} this claim"))
    v = claim_full(kb, cid)
    v['sources'] = c['sources']
    v['label_meaning'] = LABEL_MEANING[c['label']]
    v['verification_meaning'] = GRADE_MEANING.get(c['verification'], '')
    if c['label'] in ('docs', 'press', 'analysis'):
        v['day_note'] = 'day and session only say which session this claim annotates; it was not said there'
    if c.get('who') == 'audience':
        v['audience_note'] = 'an audience question: never Google\'s position; cite the claim that answers it'
    out = {'claim': v,
           'relations': rel,
           'used_by': [{'id': i, 'kind': kind_of(i), 'name': kb.item_name(i), 'file': kb.links['items'].get(i, {}).get('file')}
                       for i in c.get('used_by', [])],
           'mentions': [dict(m, name=kb.ent[m['entity']]['name'] if m['entity'] in kb.ent else None) for m in c.get('mentions', [])],
           'topics': [{'id': 'topic:' + t, 'title': kb.topics[t]['title'], 'file': f'topics/{t}.md'} for t in c['topics'] if t in kb.topics],
           'evidence_refs': c.get('evidence', []),
           'evidence_note': 'Private evidence references (photo stems, notes, T:<transcript>:<paragraph>): they tell a reviewer where to '
                            'look; the evidence itself is not in this pack.',
           'rules': RULES}
    return out


def run_cite(kb, ids):
    if not ids: raise Usage('cite needs one or more claim ids')
    got, missing = {}, []
    for s in [x for i in ids for x in split_list(i)]:
        try:
            cid = claim_id(kb, s); got[cid] = kb.cite(cid)
        except NotFound:
            missing.append(s.upper())
    out = {'cite': got}
    if missing: out['missing'] = missing; out['missing_note'] = 'not in the pack: they do not exist or are private'
    if len(got) > 1: out['combined'] = '[' + '; '.join(v[1:-1] for v in got.values()) + ']'
    out['rules'] = RULES
    return out


def run_about(kb):
    S = kb.sessions_raw
    by_label = Counter(c['label'] for c in kb.claims.values())
    by_day = Counter(c['day'] for c in kb.claims.values())
    by_ver = Counter(c['verification'] for c in kb.claims.values())
    items = Counter(kind_of(i) for i in kb.links['items'])
    row = lambda s: {'id': s['id'], 'day': s['day'], 'time': s['time'], 'title': s['title'], 'speakers': s['speakers'], 'note': s.get('note')}
    real = [s for s in kb.sessions.values() if s['kind'] not in ('break', 'unrecorded') and not s['id'].endswith('-S00')]
    nocov = [row(s) for s in real if 'none' in s['coverage']]  # the INDEX.md list: nothing was captured
    noclaims = [row(s) for s in real if 'none' not in s['coverage'] and s['claim_count'] == 0]
    head = {'name': S['event']['name'], 'event': S['event'], 'version': S['version'], 'data_through': S['data_through']}
    if kb.edition == 'community': head.update(edition='community', edition_note=EDITION_NOTE)
    return {**head,
            'pack': str(PACK),
            'counts': {'claims': len(kb.claims), 'by_label': dict(sorted(by_label.items())), 'by_day': {str(k): v for k, v in sorted(by_day.items())},
                       'by_verification': dict(sorted(by_ver.items())), 'topics': len(kb.topics), 'sessions': len(kb.sessions),
                       'sources': len(kb.sources), 'things': len(kb.ent), 'kit_items': dict(sorted(items.items()))},
            'sessions_with_no_coverage': nocov,
            'sessions_without_claims': noclaims,
            'coverage_note': 'Check these before saying what was or was not said in a session: with no coverage nothing was captured; '
                             'without claims something was captured (see note) but nothing citable.',
            'citation_form': {'slide, stage': '[id, label, speaker, Day N]  (speaker: a proven name, else Google, a community speaker, a speaker, an audience member)',
                              'docs, press': '[id, label, publisher, url]', 'analysis': f'[id, analysis, {AUTHOR}]',
                              'several': '[id, label, ...; id, label, ...]'},
            'labels': LABEL_MEANING, 'verification': GRADE_MEANING,
            'commands': ['about', 'search <query>', 'entity <id-or-name>', 'neighbours <node-id>', 'claims --ids|--entity|--topic|--session',
                         'evidence <claim-id>', 'cite <claim-id>...'],
            'read_first': 'AGENTS.md', 'rules': RULES}


# ---------------------------------------------------------------- readable text

class Ink:
    def __init__(self, on):
        self.on = on

    def __call__(self, code, s):
        return f'\x1b[{code}m{s}\x1b[0m' if self.on else s


def term_width():
    try:
        cols = os.get_terminal_size().columns if sys.stdout.isatty() else 100
    except OSError:  # NUL and some redirections claim to be a terminal
        cols = 100
    return max(60, min(110, cols - 2))


WIDTH = 98


def wrap(s, indent='     ', width=None):
    width = width or WIDTH
    return textwrap.fill(' '.join(str(s).split()), width=width, initial_indent=indent, subsequent_indent=indent)


def grade_word(c):
    v = c.get('verification')
    if c.get('label') in ('slide', 'stage'):
        return {'undocumented': 'not in Google docs', 'confirmed': 'confirmed by Google docs', 'consistent': 'consistent with Google docs',
                'n/a': 'not checked against the docs'}.get(v, v)
    return {'docs': "Google's documentation", 'press': 'press report', 'analysis': "author's view"}.get(c.get('label'), v)


def text_claims(ink, cs, numbered=True):
    out = []
    for i, c in enumerate(cs, 1):
        head = (f'{i:>2}. ' if numbered else '  - ') + ink('1;36', c['cite']) + ink('2', f"  ({grade_word(c)})")
        out.append(head)
        out.append(wrap(c['text']))
        if c.get('quote'): out.append(wrap(f"Quote: “{c['quote']}”"))
    return out


def text_thing(ink, kb, t, full=False):
    x = kb.ent[t['id'][4:]]
    out = [ink('1;34', f"== {x['name']} ==") + ink('2', f"  {x['kind']}" + (f"; also: {', '.join(x['aliases'])}" if x['aliases'] else ''))]
    out.append(wrap(x['summary'], '   '))
    ta = x['tally']
    ev = ta['event']
    out.append(wrap(f"{len(x['claims'])} claims: {ta['docs']} documentation, {sum(ev.values())} at the event "
                    f"({ev['undocumented']} not in Google docs, {ev['confirmed'] + ev['consistent']} backed by them, {ev['n/a']} not checked), "
                    f"{ta['press']} press, {ta['analysis']} analysis.", '   '))
    if x['docs']:
        out.append('   Google pages: ' + '; '.join(kb.sources[k]['title'] for k in x['docs'][:3] if k in kb.sources))
    reqs = [i['id'][4:] for i in x['items'] if i['id'].startswith('req:')]
    if reqs: out.append(wrap('Developer requirements: ' + ', '.join(reqs[:8]) + (' ...' if len(reqs) > 8 else ''), '   '))
    if x['co_mentioned']:
        out.append(wrap('Connected: ' + ', '.join(f"{kb.ent[m['id']]['name']} ({m['count']})" for m in x['co_mentioned'][:6] if m['id'] in kb.ent), '   '))
    if x['topics']: out.append('   Topic page: ' + ', '.join(f'topics/{t_}.md' for t_ in x['topics']))
    out.append(ink('2', f"   Card: 60-outputs/agent-pack/entities/{x['id']}.md  (a map: cite the claims, not the card)"))
    return out


def to_text(kb, cmd, r, ink, rules=True):
    L = []
    if r.get('note'): L.append(ink('33', r['note']))
    if r.get('edition_note'): L.append(ink('33', wrap(r['edition_note'], '')))
    if cmd == 'search':
        for t in r['things'][:1]: L += text_thing(ink, kb, t) + ['']
        if r['kind'] == 'claim':
            L.append(ink('1', f"Top claims ({min(len(r['results']), r['total'])} of {r['total']})") if r['results'] else r.get('answer', ''))
            L += text_claims(ink, r['results'])
            if r.get('topics'):
                L.append(ink('2', wrap('More on this: ' + '; '.join(f"{t['title']}: {t['more']} ({t['claims']} claims)" for t in r['topics']), '')))
        else:
            for i, m in enumerate(r['results'], 1):
                L.append(f"{i:>2}. {ink('1;36', m['id'])}  {m['name']}  ({m['file']})")
                if m.get('claims'): L.append(wrap('Claims: ' + ', '.join(m['claims'][:12]) + (' ...' if len(m['claims']) > 12 else '')))
            if not r['results']: L.append(r['answer'] if r.get('edition_note') and r.get('answer') else 'Nothing matches.')
    elif cmd == 'entity':
        e = r['entity']
        L += text_thing(ink, kb, e) + ['']
        names = {'documentation': "Google's documentation", 'event_undocumented': 'Said or shown at the event, not in Google docs',
                 'event_documented': 'Said or shown at the event, backed by Google docs', 'event_not_checked': 'Said or shown at the event, nothing to verify',
                 'press': 'Press', 'analysis': "The author's analysis"}
        for g, cs in e['claims'].items():
            if cs: L += [ink('1', f'{names[g]} ({len(cs)})')] + text_claims(ink, cs, False) + ['']
    elif cmd == 'neighbours':
        n = r['node']
        L.append(ink('1;34', f"{n['id']}  {n['name']}") + f"  ({r['total']} neighbours within {r['hops']} hop(s): "
                 + ', '.join(f'{v} {k}' for k, v in r['by_kind'].items()) + ')')
        for v in r['neighbours']:
            L.append(f"  {v['hop']}  {v['kind']:<11} {ink('36', v['id'])}  " + ((v['cite'] + ' ' + v['name'][:60]) if v.get('cite') else v['name'][:90]))
    elif cmd == 'claims':
        L.append(ink('1', f"{r['shown']} of {r['total']} claims") + f"  {json.dumps(r['scope'], ensure_ascii=False)}")
        L += text_claims(ink, r['claims'])
        if r.get('missing'): L.append(ink('33', f"Not in the pack (missing or private): {', '.join(r['missing'])}"))
    elif cmd == 'evidence':
        c = r['claim']
        L += text_claims(ink, [c], False)
        L.append(wrap(f"Who: {c['label_meaning']}; {c['said_by']}. Grade: {c['verification']} ({c['verification_meaning']}).", '     '))
        L.append(wrap(f"Session: {c['session_id']} {c['session']} (claims --session {c['session_id']} lists the whole talk in order)"))
        if c.get('day_note'): L.append(wrap(c['day_note']))
        if c.get('audience_note'): L.append(wrap(c['audience_note']))
        for s in c['sources']: L.append(f"     Source: {s['title']} ({s['publisher']}, checked {s['checked']}) {s['url']}")
        for x in r['relations']: L.append(wrap(f"{x['direction']}: {x['cite']} {x['text']}"))
        if r['used_by']: L.append(wrap('Rests on it: ' + '; '.join(f"{u['id']} {u['name']}" for u in r['used_by'])))
        if r['mentions']: L.append(wrap('Things: ' + ', '.join(m['name'] or m['entity'] for m in r['mentions'])))
        if r['evidence_refs']: L.append(wrap('Evidence references (private, not in the pack): ' + ', '.join(r['evidence_refs'])))
    elif cmd == 'cite':
        L += list(r['cite'].values())
        if r.get('combined'): L.append(r['combined'])
        if r.get('missing'): L.append(ink('33', f"Not in the pack (missing or private): {', '.join(r['missing'])}"))
    elif cmd == 'about':
        L.append(ink('1;34', f"{r['name']}") + f" knowledge base {r['version']}, data through {r['data_through']}")
        c = r['counts']
        L.append(f"{c['claims']} claims ({', '.join(f'{v} {k}' for k, v in c['by_label'].items())}), {c['topics']} topics, "
                 f"{c['sessions']} sessions, {c['sources']} sources, {c['things']} things")
        L.append('Sessions with no coverage: ' + '; '.join(f"{s['id']} {s['title']}" for s in r['sessions_with_no_coverage']))
        L += [f'Cite {k}: {v}' for k, v in r['citation_form'].items()]
    L += ['', ink('2', wrap('Rules: ' + r['rules'], ''))] if rules else []
    return '\n'.join(L)


# ---------------------------------------------------------------- the question loop (ask.bat)

def ask_loop(kb, first=None, ink=None):
    ink = ink or Ink(False)
    print(ink('1;36', '~~~ Deep Dive: ask the knowledge base ~~~'))
    print('Search Central Live Deep Dive Europe 2026. Offline: answers come only from 60-outputs\\agent-pack.')
    print('Type a question, a thing (429, GSC, hreflang) or a claim id (D1-C108). Press Enter on an empty line to quit.')
    print(ink('2', wrap('How to use what you read: ' + RULES, '')))
    try:
        kb.claim_index  # load once; every answer after this is instant
    except (Refused, NotFound) as e:
        print(ink('31', str(e))); return 1
    q = first
    while True:
        if q is None:
            try:
                q = input('\n' + ink('1;36', 'Question> '))
            except (EOFError, KeyboardInterrupt):
                print(); return 0
        q = (q or '').strip()
        if not q or q.lower() in ('q', 'quit', 'exit', 'bye'): return 0
        try:
            if CLAIM_ID.match(q):
                print(to_text(kb, 'evidence', run_evidence(kb, q), ink, rules=False))
            else:
                r = run_search(kb, q, {}, 'claim', 5)
                print(to_text(kb, 'search', r, ink, rules=False))
        except (NotFound, Usage) as e:
            print(ink('33', str(e)))
        q = None


# ---------------------------------------------------------------- command line

def parser():
    p = argparse.ArgumentParser(prog='kb_query.py', description='Cited answers from the agent pack (offline, read-only).',
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split('\n\n', 1)[1])
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('about', help='version, counts, citation rules, sessions with no coverage')

    def filters(sp):
        sp.add_argument('--day', help='1, 2 or 3 (several with commas)')
        sp.add_argument('--label', help='slide, stage, docs, press, analysis, event')
        sp.add_argument('--grade', help='confirmed, consistent, undocumented, source, n/a, documented')
        sp.add_argument('--speaker', help='a proven speaker, or google, community, audience, unattributed')
        sp.add_argument('--limit', type=int)
    s = sub.add_parser('search', help='the claims that best answer a question')
    s.add_argument('query', nargs='+')
    s.add_argument('--kind', default='claim', choices=('claim', 'all') + MAP_KINDS)
    filters(s)
    e = sub.add_parser('entity', help="one thing's card")
    e.add_argument('name', nargs='+')
    n = sub.add_parser('neighbours', aliases=['neighbors'], help='what a node of graph.json links to')
    n.add_argument('node', nargs='+')
    n.add_argument('--hops', type=int, default=1)
    n.add_argument('--edge-types')
    n.add_argument('--node-kinds')
    n.add_argument('--limit', type=int, default=100)
    c = sub.add_parser('claims', help='claims by ids, thing, topic or session')
    c.add_argument('--ids')
    c.add_argument('--entity')
    c.add_argument('--topic')
    c.add_argument('--session')
    filters(c)
    v = sub.add_parser('evidence', help='everything the pack holds about one claim')
    v.add_argument('id')
    t = sub.add_parser('cite', help='citation strings')
    t.add_argument('ids', nargs='+')
    a = sub.add_parser('ask', help='a question loop for people (ask.bat)')
    a.add_argument('question', nargs='*')
    return p


def run(argv, kb=None):
    """Runs one command. Returns (exit code, command, result dict). kb can be reused between calls."""
    kb = kb or KB()
    a = parser().parse_args(argv)
    cmd = 'neighbours' if a.cmd == 'neighbors' else a.cmd
    try:
        if cmd == 'about': r = run_about(kb)
        elif cmd == 'search':
            F = parse_filters(kb, a)
            r = run_search(kb, ' '.join(a.query), F, a.kind, a.limit if a.limit is not None else 10)
        elif cmd == 'entity': r = run_entity(kb, ' '.join(a.name))
        elif cmd == 'neighbours': r = run_neighbours(kb, ' '.join(a.node), a.hops, a.edge_types, a.node_kinds, a.limit)
        elif cmd == 'claims': r = run_claims(kb, a)
        elif cmd == 'evidence': r = run_evidence(kb, a.id)
        elif cmd == 'cite': r = run_cite(kb, a.ids)
        else: return 0, cmd, None
        return 0, cmd, r
    except Refused as x:
        return 1, cmd, {'error': str(x), 'refused': True, 'rules': RULES}
    except NotFound as x:
        r = {'error': str(x), 'rules': RULES}
        if x.did_you_mean: r['did_you_mean'] = x.did_you_mean
        return 1, cmd, r
    except Usage as x:
        return 2, cmd, {'error': str(x), 'rules': RULES}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    kb = KB()
    as_text = '--text' in argv
    argv = [x for x in argv if x not in ('--text', '--json')]
    for st in (sys.stdout, sys.stderr):
        try: st.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError): pass
    color = sys.stdout.isatty() and not os.environ.get('NO_COLOR')
    if color and os.name == 'nt': os.system('')
    ink = Ink(color)
    global WIDTH
    WIDTH = term_width()
    if not argv:
        parser().print_help(); return 2
    if argv[0] == 'ask':
        a = parser().parse_args(argv)
        return ask_loop(kb, ' '.join(a.question) or None, ink)
    code, cmd, r = run(argv, kb)
    if as_text:
        if 'error' in r:
            dym = r.get('did_you_mean') or []
            more = ', '.join((d.get('name') or d.get('title') or d.get('id', '')) if isinstance(d, dict) else str(d) for d in dym)
            print(ink('31', r['error']) + (f'\nDid you mean: {more}' if dym and 'Did you mean' not in r['error'] else ''))
        else:
            print(to_text(kb, cmd, r, ink))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.stdout.flush()
    return code


if __name__ == '__main__':
    try:
        code = main()
        sys.stdout.flush()
        sys.exit(code)
    except OSError as e:  # the reader stopped early (| head): not an error
        if not isinstance(e, BrokenPipeError) and e.errno not in (22, 32): raise
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)
