"""Tests for _system/build_kb.py, the developer and content kits (_system/kits.py, 25-kits/), the README badges
(_system/badges.py) and generated folder READMEs, the links between claims and kit items (graph.json, links.json), the things of 20-claims/entities.yaml and their cards, the web edition
(_system/site) and its search, the Reef map (the explorer of the graph), ingest (_system/tools/ingest.py, ingest.bat),
the ledgers (numbers registry, differences ledger, question bank) and the query layer (_system/kb_query.py, ask.bat),
the commit privacy guard, eval_check, the PDF builders' text helpers (Art Deco and Deep Dive palettes, style names, agenda coverage,
source dates), the default style (_system/theme.yaml, theme.py), the Diver bot (_system/ocean_art.py) and the brand file names.
Plain Python, no pytest.

Usage:  python _system/tests/run_tests.py [--keep] [-k name]
Builds small fixture repositories in a temp folder (never touches this repository), checks that every failure the audits
found (RC-01 to RC-13 included) is caught or rendered safely, then builds a copy of the real data twice and checks it is
clean, byte-identical and schema-valid, and that its web edition loads with no console error. Needs pyyaml and jsonschema;
uses Playwright for the browser checks when it is installed. The ingest.bat and file-lock tests run on Windows only.
"""
import contextlib, csv, ctypes, hashlib, html, importlib, importlib.util, io, json, os, re, shutil, subprocess, sys, tempfile, textwrap, traceback
import xml.etree.ElementTree as ET
from pathlib import Path
import yaml

sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[2]
TMP = Path(tempfile.mkdtemp(prefix='kb-tests-'))
SHARED = ['30-topics', '40-sessions', '50-maps', '60-outputs/agent-pack', '60-outputs/dev', '60-outputs/content', '60-outputs/badges']
SHARED_FILES = ['60-outputs/README.md']  # generated files outside the generated folders
CODE = ('_system/build_kb.py', '_system/kits.py', '_system/badges.py', '_system/theme.py', '_system/theme.yaml',
        '_system/ocean_art.py', '_system/edition.py')  # the build, its default style and its edition reader: copied into every fixture and real-data copy
# The edition of this checkout (_system/edition.yaml). Fixtures never get the file, so they build the full edition; real-data copies
# get it (copy_real), so their expectations follow the edition: 'community' on the community branch, 'full' on main.
EDITION_YAML = '_system/edition.yaml'
EDITION = (yaml.safe_load((REPO / EDITION_YAML).read_text(encoding='utf-8')) or {}).get('edition', 'full') if (REPO / EDITION_YAML).exists() else 'full'
COMMUNITY = EDITION == 'community'
BADGES = ('version', 'days', 'claims', 'docs-backed', 'topics', 'sources', 'dev-kit', 'media-kit', 'privacy')

FIX = {
    'CHANGELOG.md': '# Changelog\n\n## Unreleased\n- nothing\n\n## v9.9.9 — test\n- fixture\n\n## v9.9.8\n',
    '20-claims/sessions.yaml': '''
        event: {name: Test Event, city: Testville, dates: 2026-09-30 to 2026-10-01}
        days:
          - day: 1
            date: 2026-09-30
            theme: Crawling
            sessions:
              - {id: D1-S01, time: "10:00", title: "Crawl talk", speaker: "Gary Illyes", coverage: slides}
              - {id: D1-S02, time: "11:00", title: "Q&A", speaker: [Gary Illyes, Cherry Prommawin], coverage: [notes, transcript], kind: qa}
              - {id: D1-S03, time: "12:00", title: "Lightning", speaker: "", coverage: none, kind: lightning}
              - {id: D1-S00, time: "", title: "Day 1, session not recorded", speaker: "", coverage: notes}
          - day: 2
            date: 2026-10-01
            theme: Indexing
            sessions:
              - {id: D2-S01, time: "09:30", title: "Indexing talk", speaker: [Martin Splitt, John Mueller], role: "Search Advocates", coverage: [transcript, slides]}
          - day: 3
            date: 2026-10-02
            theme: Serving
            sessions: []
        ''',
    '20-claims/topics.yaml': '''
        areas:
          - id: crawling
            title: Crawling
            blurb: How Google crawls.
            topics:
              - id: crawl-budget
                title: Crawl budget
                summary: "Crawl budget is rate limit plus demand (D1-C001). Author's view: most sites need not worry."
                cites: [D1-C001, D1-C003]
                do: ["Check crawl stats (see D1-C001 to D1-C002)."]
                related: [canonical]
          - id: indexing
            title: Indexing
            blurb: How Google indexes.
            topics:
              - id: canonical
                title: Canonicals
                summary: Google picks one URL to keep.
                related: [crawl-budget]
              - id: empty-topic
                title: Nothing yet
                summary: No claims yet.
        ''',
    '20-claims/sources.yaml': '''
        crawl-guide: {title: Crawl budget guide, url: "https://developers.google.com/crawling/docs/crawl-budget", publisher: Google, checked: 2026-10-01}
        sej: {title: Press article, url: "https://example.com/a", publisher: Search Engine Journal, checked: 2026-10-01, kind: press}
        ''',
    '20-claims/day1.yaml': '''
        - {id: D1-C001, s: D1-S01, label: slide, ev: IMG_0001, ver: confirmed, src: [crawl-guide], topics: [crawl-budget],
           text: "Crawl budget is crawl rate limit plus crawl demand.", quote: "Crawl Budget = Crawl Rate Limit & Crawl Demand", quote_checked: true}
        - {id: D1-C002, s: D1-S02, label: stage, who: audience, ev: "T:t02:3", ver: n/a, topics: [crawl-budget],
           text: "An audience member asked whether small sites need to worry about crawl budget."}
        - {id: D1-C003, s: D1-S02, label: stage, who: Gary Illyes, ev: "T 00:01:02-00:01:30", ver: consistent, src: [crawl-guide, sej], topics: [crawl-budget],
           text: "Gary Illyes answered that sites under a million pages rarely need to.", rel: [{type: answers, to: D1-C002}]}
        - {id: D1-C004, s: D1-S00, label: press, ev: "", ver: source, src: [sej], topics: [canonical],
           text: "A press report says Google can handle multiple URLs to the same content."}
        - {id: D1-C005, s: D1-S01, label: analysis, ev: "", ver: n/a, topics: [crawl-budget],
           text: "Most sites should spend effort on quality, not crawl budget."}
        - {id: D1-C006, s: D1-S01, label: docs, ev: "", ver: source, src: [crawl-guide], topics: [crawl-budget],
           text: "The documentation lists crawl capacity limit and crawl demand."}
        - {id: D1-C007, s: D1-S00, label: stage, ev: notes, ver: undocumented, topics: [crawl-budget],
           text: "SECRETPRIVATEMARKER remark about my own site.", private: true}
        ''',
    '20-claims/day2.yaml': '''
        - {id: D2-C001, s: D2-S01, label: stage, who: Martin Splitt, ev: "video:IMG_0002", ver: undocumented, topics: [canonical, crawl-budget],
           text: "Martin Splitt repeated that crawl budget is rate limit plus demand.", rel: [{type: repeats, to: D1-C001}]}
        - {id: D2-C002, s: D2-S01, label: slide, ev: [IMG_0003, IMG_0004], ver: n/a, topics: [canonical],
           text: "A slide showed a canonical link element in the head.", rel: [{type: extends, to: D1-C004}]}
        ''',
    '25-kits/dev-requirements.yaml': '''
        areas:
          - id: crawling
            title: Crawling
            intro: |
              How Google crawls.
              Second line of the intro.
            requirements:
              - id: DEV-CRA-01
                level: MUST
                title: Keep crawl capacity healthy
                why: Crawl budget is crawl rate limit plus crawl demand.
                how: |
                  Watch the Crawl Stats report every week.
                  - answer 503 when the server is overloaded
                  - never answer 200 for an error page
                test: Open the Crawl Stats report in Search Console and run `curl -I https://www.example.com/`.
                snippet: canonical-link
                claims: [D1-C001, D1-C006]
                docs: [crawl-guide]
                status: documented
              - id: DEV-CRA-02
                level: AVOID
                title: Block crawling to save budget
                why: "Said at Search Central Live, not in Google's documentation: crawl budget is rate limit plus demand."
                how: Leave robots.txt open for the pages you want crawled.
                test: Read robots.txt.
                claims: [D2-C001]
                status: event-only
              - id: DEV-CRA-03
                level: SHOULD
                title: Point duplicates to one canonical URL
                why: Google picks one URL to keep.
                how: Add a canonical link element to every duplicate.
                test: Check the Google-selected canonical in URL Inspection.
                claims: [D1-C003]
                docs: [crawl-guide]
                status: documented
        ''',
    '25-kits/snippets/canonical-link.md': '''
        # Canonical link element

        One canonical link in the head of every duplicate.

        ```html
        <link rel="canonical" href="https://www.example.com/page">
        <script type="application/ld+json">{"@context": "https://schema.org", "@type": "WebPage"}</script>
        ```
        ''',
    '25-kits/content.yaml': '''
        wording_rules:
          - "Documented points: write them as Google's position and link the page."
          - "Event-only points: write \\"said at Search Central Live\\"."
        facts:
          - {id: F-001, statement: "Crawl budget is crawl rate limit plus crawl demand.", claims: [D1-C001, D1-C006], status: documented, use: headline}
          - {id: F-002, statement: "Martin Splitt repeated the crawl budget formula on Day 2.", claims: [D2-C001], status: event-only, use: context}
        myths:
          - {id: M-001, myth: "Every small site must manage its crawl budget.", fact: "Sites under a million pages rarely need to.", claims: [D1-C003], status: documented}
        quotes:
          - {id: Q-001, claim: D1-C001}
        angles:
          - id: A-001
            title: Crawl budget in two parts
            audience: [technical SEOs]
            formats: [linkedin, article]
            hook: Two parts, one budget.
            points:
              - {text: The formula on the slide., claims: [D1-C001]}
              - {text: Said again on Day 2., claims: [D2-C001]}
            caution: The Day 2 repeat is not documented.
            cta: Check your crawl stats.
        glossary:
          - {term: Crawl budget, definition: How much Google crawls a site., claims: [D1-C001, D1-C006]}
          - {term: canonical URL, definition: The URL Google keeps from a group of duplicates., claims: [D1-C003]}
        ''',
    '_system/eval/questions.yaml': '- {id: q01, q: "What is crawl budget?", expect: ["Rate plus demand."], claims: [D1-C001, D2-C001]}\n',
}

# The differences ledger of the fixture (knowledge graph phase 3): one good row; BAD below breaks it one way at a time.
DIFF_FILE = '25-kits/differences.yaml'
DIFF_FIX = '''differences:
  - id: DIF-01
    title: Whether the crawl budget formula is documented
    event: [D2-C001]
    docs: [D1-C006]
    analysis: [D1-C005]
    follow: Follow the crawl budget guide, which lists crawl capacity limit and crawl demand.
'''


def diff_bad(old, new):
    assert old in DIFF_FIX, old
    return DIFF_FIX.replace(old, new, 1)


# Every scenario from the audit (build B4-B11, readiness R2/R7/R8/R15, privacy P2) plus the new v2 rules.
# (name, file, old text, new text, expected error text)
BAD = [
    ('duplicate session id across days', '20-claims/sessions.yaml', '- {id: D2-S01,', '- {id: D1-S01, time: "13:00", title: "Copy", speaker: "", coverage: none}\n      - {id: D2-S01,', 'duplicate session id'),
    ('duplicate session id within a day', '20-claims/sessions.yaml', '- {id: D2-S01,', '- {id: D2-S01, time: "13:00", title: "Copy", speaker: "", coverage: none}\n      - {id: D2-S01,', 'D2-S01 (day 2): duplicate session id'),
    ('session id day digit', '20-claims/sessions.yaml', '{id: D2-S01,', '{id: D3-S01,', 'the id says day 3 but the session is listed under day 2'),
    ('duplicate topic id', '20-claims/topics.yaml', '- id: empty-topic', '- id: crawl-budget\n        title: Robots in indexing\n        summary: x\n      - id: empty-topic', 'id "crawl-budget" is used 2 times'),
    ('topic id equal to area id', '20-claims/topics.yaml', '- id: empty-topic', '- id: indexing', 'id "indexing" is used 2 times'),
    ('topic id not kebab-case', '20-claims/topics.yaml', '- id: empty-topic', '- id: Empty_Topic', 'must be lowercase kebab-case'),
    ('missing session time', '20-claims/sessions.yaml', '{id: D1-S01, time: "10:00", ', '{id: D1-S01, ', 'missing key "time"'),
    ('missing session speaker', '20-claims/sessions.yaml', ', speaker: "Gary Illyes", coverage: slides}', ', coverage: slides}', 'missing key "speaker"'),
    ('missing session coverage', '20-claims/sessions.yaml', ', speaker: "Gary Illyes", coverage: slides}', ', speaker: "Gary Illyes"}', 'missing key "coverage"'),
    ('sessions left empty', '20-claims/sessions.yaml', '    sessions: []', '    sessions:', 'sessions must be a list'),
    ('bad coverage value', '20-claims/sessions.yaml', 'coverage: slides}', 'coverage: photos}', 'coverage must be one of'),
    ('unquoted time 10:00', '20-claims/sessions.yaml', 'time: "09:30"', 'time: 10:00', 'time must be quoted, e.g. time: "10:00"'),
    ('string src', '20-claims/day1.yaml', 'src: [crawl-guide], topics: [crawl-budget],\n   text: "Crawl budget is', 'src: crawl-guide, topics: [crawl-budget],\n   text: "Crawl budget is', 'src must be a list, e.g. [robots-spec]'),
    ('string topics', '20-claims/day1.yaml', 'topics: [canonical],\n   text: "A press', 'topics: canonical,\n   text: "A press', 'topics must be a list'),
    ('misspelled private key', '20-claims/day1.yaml', 'private: true', 'privat: true', 'unknown key "privat" (did you mean "private"?)'),
    ('private not boolean', '20-claims/day1.yaml', 'private: true', 'private: "no"', 'private must be true or false'),
    ('claim id day vs file', '20-claims/day2.yaml', 'id: D2-C002', 'id: D3-C002', 'the id says day 3 but the claim is in day2.yaml'),
    ('claim id day vs session', '20-claims/day1.yaml', '{id: D1-C005, s: D1-S01', '{id: D1-C005, s: D2-S01', 'session D2-S01 is on day 2'),
    ('duplicate claim id', '20-claims/day1.yaml', 'id: D1-C006', 'id: D1-C005', 'D1-C005: duplicate id'),
    ('quote too long', '20-claims/day1.yaml', 'quote: "Crawl Budget = Crawl Rate Limit & Crawl Demand"',
     'quote: "' + ' '.join(['word'] * 26) + '"', 'quote has 26 words; at most 25'),
    ('unknown rel target', '20-claims/day2.yaml', 'to: D1-C001}', 'to: D9-C999}', 'rel points to D9-C999, which does not exist'),
    ('rel to private claim', '20-claims/day2.yaml', 'to: D1-C001}', 'to: D1-C007}', 'which is private'),
    ('bad rel type', '20-claims/day2.yaml', 'type: repeats', 'type: echoes', 'rel type echoes must be one of'),
    ('stage claim without who in panel', '20-claims/day1.yaml', 'who: Gary Illyes, ', '', 'needs who: <name>, audience or unknown'),
    ('who not a speaker', '20-claims/day1.yaml', 'who: Gary Illyes', 'who: John Mueller', 'who "John Mueller" is not a speaker of D1-S02'),
    ('who on analysis', '20-claims/day1.yaml', '{id: D1-C005, s: D1-S01, label: analysis,', '{id: D1-C005, s: D1-S01, label: analysis, who: Gary Illyes,', 'who is only for slide and stage claims'),
    ('press without press source', '20-claims/day1.yaml', 'src: [sej], topics: [canonical]', 'src: [crawl-guide], topics: [canonical]', 'press claims cite at least one source with kind: press'),
    ('docs citing press', '20-claims/day1.yaml', 'label: docs, ev: "", ver: source, src: [crawl-guide]', 'label: docs, ev: "", ver: source, src: [sej]', 'docs claims cite only Google sources'),
    ('consistent on press only', '20-claims/day1.yaml', 'src: [crawl-guide, sej]', 'src: [sej]', 'needs at least one Google source'),
    ('source on a slide', '20-claims/day1.yaml', 'ver: confirmed, src: [crawl-guide]', 'ver: source, src: [crawl-guide]', 'ver source is only for docs and press claims'),
    ('analysis not n/a', '20-claims/day1.yaml', 'label: analysis, ev: "", ver: n/a', 'label: analysis, ev: "", ver: undocumented', 'analysis claims use ver: n/a'),
    ('bad source kind', '20-claims/sources.yaml', 'kind: press}', 'kind: blog}', 'kind must be google or press'),
    ('topic cites unknown claim', '20-claims/topics.yaml', 'cites: [D1-C001, D1-C003]', 'cites: [D1-C001, D1-C099]', 'cites D1-C099, which does not exist'),
    ('topic cites private claim', '20-claims/topics.yaml', 'cites: [D1-C001, D1-C003]', 'cites: [D1-C007]', 'cites D1-C007, which is private'),
    ('summary mentions private claim', '20-claims/topics.yaml', 'plus demand (D1-C001)', 'plus demand (D1-C007)', 'summary: mentions D1-C007, which is private'),
    ('claim text mentions missing id', '20-claims/day1.yaml', 'quality, not crawl budget.', 'quality, not crawl budget (see D1-C098).', 'mentions D1-C098, which does not exist'),
    ('eval cites missing claim', '_system/eval/questions.yaml', 'D2-C001]', 'D2-C009]', 'eval q01: mentions D2-C009, which does not exist'),
    ('related topic unknown', '20-claims/topics.yaml', 'related: [crawl-budget]', 'related: [crawl-budgets]', 'unknown related topic crawl-budgets'),
    ('unknown session key', '20-claims/sessions.yaml', 'coverage: none, kind: lightning}', 'coverage: none, knd: lightning}', 'unknown key "knd" (did you mean "kind"?)'),
    ('claims file is a mapping', '20-claims/day2.yaml', None, 'claims:\n  - {id: D2-C001}\n', 'must be a YAML list of claims'),
    ('YAML syntax error', '20-claims/day2.yaml', None, '- {id: D2-C001, text: "unclosed\n', 'YAML error'),
    ('claims file badly named', '20-claims/day2-draft.yaml', None, '[]\n', 'claim files must be named dayN.yaml'),
    # RC-01: a key written twice is an error in every YAML file, with file, line and key (PyYAML keeps the last value silently)
    ('repeated private key', '20-claims/day1.yaml', 'private: true}', 'private: true, private: false}', 'day1.yaml: line 14: D1-C007: key "private" appears twice'),
    ('repeated key in a source', '20-claims/sources.yaml', 'publisher: Google, checked: 2026-10-01}', 'publisher: Google, checked: 2026-10-01, publisher: Other}', 'sources.yaml: line 1: key "publisher" appears twice'),
    ('repeated source key', '20-claims/sources.yaml', 'sej: {', 'crawl-guide: {title: X, url: "https://example.com/x", publisher: X, checked: 2026-10-01}\nsej: {', 'sources.yaml: line 2: key "crawl-guide" appears twice'),
    ('repeated key in a session', '20-claims/sessions.yaml', 'coverage: none, kind: lightning}', 'coverage: none, kind: lightning, kind: talk}', 'sessions.yaml: line 9: D1-S03: key "kind" appears twice'),
    ('repeated key in a topic', '20-claims/topics.yaml', 'title: Canonicals\n', 'title: Canonicals\n        title: Canonical URLs\n', 'topics.yaml: line 18: canonical: key "title" appears twice'),
    ('repeated key in an eval question', '_system/eval/questions.yaml', 'claims: [D1-C001, D2-C001]}', 'claims: [D1-C001, D2-C001], q: "Again?"}', 'questions.yaml: line 1: q01: key "q" appears twice'),
    # RC-03: the excluded photo can never be cited or named in anything public
    ('excluded photo as evidence', '20-claims/day2.yaml', 'ev: [IMG_0003, IMG_0004]', 'ev: [IMG_0003, IMG_4692]', 'D2-C002: evidence IMG_4692 is an excluded photo'),
    ('excluded photo in a comma list', '20-claims/day1.yaml', 'ev: IMG_0001,', 'ev: "IMG_0001, img_4692",', 'D1-C001: evidence img_4692 is an excluded photo'),
    ('excluded photo as video evidence', '20-claims/day2.yaml', 'video:IMG_0002', 'video:IMG_4692', 'D2-C001: evidence video:IMG_4692 is an excluded photo'),
    ('excluded photo cited by a private claim', '20-claims/day1.yaml', 'label: stage, ev: notes, ver: undocumented', 'label: stage, ev: IMG_4692, ver: undocumented', 'D1-C007: evidence IMG_4692 is an excluded photo'),
    ('excluded photo named in claim text', '20-claims/day1.yaml', 'quality, not crawl budget."', 'quality, not crawl budget (see IMG_4692)."', 'D1-C005: names IMG_4692'),
    ('excluded photo named in a topic', '20-claims/topics.yaml', 'summary: Google picks one URL to keep.', 'summary: Google picks one URL to keep (IMG_4692.HEIC).', 'topic canonical: names IMG_4692'),
    ('excluded photo named in a session note', '20-claims/sessions.yaml', 'title: "Day 1, session not recorded",', 'title: "Day 1, session not recorded", note: "see IMG_4692",', 'session D1-S00 (day 1): names IMG_4692'),
    # RC-04: real calendar dates only; a YAML date error is reported, never a traceback
    ('impossible date', '20-claims/sources.yaml', 'publisher: Google, checked: 2026-10-01}', 'publisher: Google, checked: 2026-09-31}', 'sources.yaml: line 1: 2026-09-31 is not a real date'),
    ('impossible quoted date', '20-claims/sources.yaml', 'publisher: Google, checked: 2026-10-01}', 'publisher: Google, checked: "2026-09-31"}', "source crawl-guide: checked must be a real date written YYYY-MM-DD (found '2026-09-31')"),
    ('source date with a time', '20-claims/sources.yaml', 'publisher: Google, checked: 2026-10-01}', 'publisher: Google, checked: 2026-10-02 10:00:00}', 'source crawl-guide: checked must be a real date'),
    ('day date with a time', '20-claims/sessions.yaml', 'date: 2026-09-30\n', 'date: 2026-09-30 09:00:00\n', 'sessions.yaml day 1: date must be a real date'),
    ('impossible day date', '20-claims/sessions.yaml', 'date: 2026-09-30\n', 'date: "2026-02-30"\n', 'sessions.yaml day 1: date must be a real date'),
    # RC-07: a list or mapping where a word is expected is an error, never a TypeError
    ('label is a list', '20-claims/day1.yaml', '{id: D1-C005, s: D1-S01, label: analysis,', '{id: D1-C005, s: D1-S01, label: [analysis],', 'D1-C005: label must be one word'),
    ('ver is a mapping', '20-claims/day1.yaml', 'label: analysis, ev: "", ver: n/a', 'label: analysis, ev: "", ver: {a: 1}', 'D1-C005: ver must be one word'),
    ('src item is a mapping', '20-claims/day1.yaml', 'src: [crawl-guide], topics: [crawl-budget],\n   text: "Crawl budget is', 'src: [{a: 1}], topics: [crawl-budget],\n   text: "Crawl budget is', 'D1-C001: every src item must be a source key'),
    ('topics item is a mapping', '20-claims/day1.yaml', 'topics: [canonical],\n   text: "A press', 'topics: [{a: 1}],\n   text: "A press', 'D1-C004: every topics item must be a topic id'),
    ('rel type is a list', '20-claims/day2.yaml', 'type: repeats', 'type: [repeats]', 'D2-C001: rel type and to must be single words'),
    ('rel to is a list', '20-claims/day2.yaml', 'to: D1-C001}', 'to: [D1-C001]}', 'D2-C001: rel type and to must be single words'),
    ('related item is a list', '20-claims/topics.yaml', 'related: [crawl-budget]', 'related: [[crawl-budget]]', 'topic canonical: every related item must be a string'),
    ('source title is a list', '20-claims/sources.yaml', 'title: Press article', 'title: [Press article]', 'source sej: title must be a string'),
    # RC-08: source URLs are http(s) only
    ('javascript source url', '20-claims/sources.yaml', 'url: "https://example.com/a"', 'url: "javascript:alert(document.domain)"', 'source sej: url must start with http:// or https://'),
    ('relative source url', '20-claims/sources.yaml', 'url: "https://example.com/a"', 'url: "//example.com/a"', 'source sej: url must start with http:// or https://'),
    # RC-10: an item listed twice would be counted and rendered twice
    ('topic listed twice in a claim', '20-claims/day1.yaml', 'topics: [canonical],\n   text: "A press', 'topics: [canonical, canonical],\n   text: "A press', 'D1-C004: topics lists canonical 2 times'),
    ('source listed twice in a claim', '20-claims/day1.yaml', 'src: [crawl-guide, sej]', 'src: [crawl-guide, sej, crawl-guide]', 'D1-C003: src lists crawl-guide 2 times'),
    ('cites lists a claim twice', '20-claims/topics.yaml', 'cites: [D1-C001, D1-C003]', 'cites: [D1-C001, D1-C003, D1-C001]', 'topic crawl-budget: cites lists D1-C001 2 times'),
    ('related lists a topic twice', '20-claims/topics.yaml', 'related: [canonical]', 'related: [canonical, canonical]', 'topic crawl-budget: related lists canonical 2 times'),
    ('do lists an item twice', '20-claims/topics.yaml', 'do: ["Check crawl stats (see D1-C001 to D1-C002)."]',
     'do: ["Check crawl stats (see D1-C001 to D1-C002).", "Check crawl stats (see D1-C001 to D1-C002)."]', 'topic crawl-budget: do lists Check crawl stats'),
    ('rel listed twice', '20-claims/day2.yaml', 'rel: [{type: repeats, to: D1-C001}]', 'rel: [{type: repeats, to: D1-C001}, {type: repeats, to: D1-C001}]', 'D2-C001: rel lists {type: repeats, to: D1-C001} 2 times'),
    # lead decisions: kind poster is valid, other kinds are not; who in a recorded session must be one of its speakers
    ('unknown session kind', '20-claims/sessions.yaml', 'coverage: none, kind: lightning}', 'coverage: none, kind: keynote}', 'kind must be one of talk, lightning, panel, qa, poster, break'),
    # the developer and content kits (25-kits/): ids, levels, statuses, cited claims, docs keys, snippets, names
    ('kit requirement id format', '25-kits/dev-requirements.yaml', 'id: DEV-CRA-01', 'id: DEV-CRAWL-1', 'requirement DEV-CRAWL-1: id must look like DEV-REN-01'),
    ('kit cites a private claim', '25-kits/dev-requirements.yaml', 'claims: [D1-C001, D1-C006]', 'claims: [D1-C001, D1-C007]', 'requirement DEV-CRA-01: cites D1-C007, which is private'),
    ('kit cites a missing claim', '25-kits/dev-requirements.yaml', 'claims: [D2-C001]', 'claims: [D2-C009]', 'requirement DEV-CRA-02: cites D2-C009, which does not exist'),
    ('kit unknown docs key', '25-kits/dev-requirements.yaml', 'claims: [D1-C003]\n        docs: [crawl-guide]', 'claims: [D1-C003]\n        docs: [crawl-guidee]', 'requirement DEV-CRA-03: unknown docs key crawl-guidee'),
    ('kit docs key is a press source', '25-kits/dev-requirements.yaml', 'claims: [D1-C003]\n        docs: [crawl-guide]', 'claims: [D1-C003]\n        docs: [crawl-guide, sej]', 'requirement DEV-CRA-03: docs key sej is a press source'),
    ('kit duplicate requirement id', '25-kits/dev-requirements.yaml', 'id: DEV-CRA-03', 'id: DEV-CRA-01', 'id DEV-CRA-01 is used 2 times (duplicate requirement id)'),
    ('kit missing snippet', '25-kits/dev-requirements.yaml', 'snippet: canonical-link', 'snippet: canonical-tag', "requirement DEV-CRA-01: snippet 'canonical-tag' has no file 25-kits/snippets/canonical-tag.md"),
    ('kit bad level', '25-kits/dev-requirements.yaml', 'level: SHOULD', 'level: RECOMMENDED', "requirement DEV-CRA-03: level must be one of MUST, SHOULD, MAY, AVOID, found 'RECOMMENDED'"),
    ('kit bad status', '25-kits/dev-requirements.yaml', 'status: event-only', 'status: rumour', "requirement DEV-CRA-02: status must be documented or event-only, found 'rumour'"),
    ('kit documented without docs', '25-kits/dev-requirements.yaml', 'claims: [D1-C003]\n        docs: [crawl-guide]\n', 'claims: [D1-C003]\n', 'requirement DEV-CRA-03: status documented needs at least one Google page in docs'),
    ('kit event-only without the event wording', '25-kits/dev-requirements.yaml', 'why: "Said at Search Central Live, not in Google\'s documentation: crawl', 'why: "Google says: crawl',
     'requirement DEV-CRA-02: event-only: write "said at Search Central Live" in why'),
    ('kit event-only on analysis only', '25-kits/dev-requirements.yaml', 'claims: [D2-C001]', 'claims: [D1-C005]', 'requirement DEV-CRA-02: status event-only needs at least one slide or stage claim'),
    ('kit claims not a list', '25-kits/dev-requirements.yaml', 'claims: [D2-C001]', 'claims: D2-C001', 'requirement DEV-CRA-02: claims must be a list of claim ids'),
    ('kit unknown key', '25-kits/dev-requirements.yaml', 'level: MUST', 'level: MUST\n        priority: high', 'requirement DEV-CRA-01: unknown key "priority"'),
    ('kit repeated key', '25-kits/dev-requirements.yaml', 'level: MUST', 'level: MUST\n        level: MAY', 'DEV-CRA-01: key "level" appears twice'),
    ('kit area id not kebab-case', '25-kits/dev-requirements.yaml', '- id: crawling', '- id: Crawling_Basics', 'dev area Crawling_Basics: id must be lowercase kebab-case'),
    ('kit invalid JSON-LD in a snippet', '25-kits/snippets/canonical-link.md', '"@type": "WebPage"}', '"@type": "WebPage",}', '25-kits/snippets/canonical-link.md code block 1: the JSON is not valid'),
    ('kit snippet fence never closed', '25-kits/snippets/canonical-link.md', '```html', 'html:', '25-kits/snippets/canonical-link.md: the code block opened with ``` is never closed'),
    ('kit snippet file name', '25-kits/snippets/Canonical Link.md', None, '# x\n\n```html\n<p>x</p>\n```\n', '25-kits/snippets/Canonical Link.md: the file name must be a lowercase kebab-case key'),
    ('kit fact cites a missing claim', '25-kits/content.yaml', 'claims: [D1-C001, D1-C006], status: documented, use: headline', 'claims: [D1-C099], status: documented, use: headline', 'fact F-001: cites D1-C099, which does not exist'),
    ('kit fact documented on event claims only', '25-kits/content.yaml', 'claims: [D2-C001], status: event-only', 'claims: [D2-C001], status: documented',
     'fact F-002: status documented, but none of its claims is confirmed, consistent or a docs claim'),
    ('kit fact bad use', '25-kits/content.yaml', 'use: headline', 'use: tweet', "fact F-001: use must be one of stat, headline, context, found 'tweet'"),
    ('kit fact id format', '25-kits/content.yaml', 'id: F-002', 'id: F-2', 'fact F-2: id must look like F-001'),
    ('kit duplicate fact id', '25-kits/content.yaml', 'id: F-002', 'id: F-001', '25-kits/content.yaml: facts lists F-001 2 times'),
    ('kit quote without quote', '25-kits/content.yaml', 'claim: D1-C001}', 'claim: D1-C005}', 'quote Q-001: claim D1-C005 has no quote'),
    ('kit quote of a private claim', '25-kits/content.yaml', 'claim: D1-C001}', 'claim: D1-C007}', 'quote Q-001: claim D1-C007 is private'),
    ('kit unknown format', '25-kits/content.yaml', 'formats: [linkedin, article]', 'formats: [linkedin, tiktok]', "angle A-001: format 'tiktok' must be one of"),
    ('kit names an unproven speaker', '25-kits/content.yaml', 'claims: [D2-C001], status: event-only', 'claims: [D2-C002], status: event-only', 'fact F-002: names Martin Splitt, but none of its claims is proven'),
    ('kit names an inferred speaker', '20-claims/sessions.yaml', 'role: "Search Advocates"', 'role: "Search Advocates (speaker inferred)"', 'fact F-002: names Martin Splitt, but none of its claims is proven'),
    ('kit says community speaker on Google claims', '25-kits/content.yaml', 'caution: The Day 2 repeat is not documented.', "caution: The Day 2 repeat was a community speaker's.",
     'angle A-001: says "community speaker", but none of its claims is a slide or stage claim credited to a community speaker'),
    ('kit text range hits private claim', '25-kits/content.yaml', 'hook: Two parts, one budget.', 'hook: Two parts, one budget (D1-C005 to D1-C007).', 'angle A-001: mentions D1-C007, which is private'),
    ('excluded photo named in a kit', '25-kits/content.yaml', 'cta: Check your crawl stats.', 'cta: Check your crawl stats (IMG_4692).', 'angle A-001: names IMG_4692'),
    ('excluded photo named in a snippet', '25-kits/snippets/canonical-link.md', 'One canonical link', 'See IMG_4692. One canonical link', '25-kits/snippets/canonical-link.md: names IMG_4692'),
    ('kit duplicate glossary term', '25-kits/content.yaml', 'term: canonical URL', 'term: Crawl Budget', 'glossary lists crawl budget 2 times (terms must be unique)'),
    ('kit content file empty', '25-kits/content.yaml', None, '', '25-kits/content.yaml: must be a mapping'),
    # a list where a word is expected is an error, never a TypeError
    ('kit level is a list', '25-kits/dev-requirements.yaml', 'level: SHOULD', 'level: [SHOULD]', "requirement DEV-CRA-03: level must be one of MUST, SHOULD, MAY, AVOID, found ['SHOULD']"),
    ('kit status is a list', '25-kits/dev-requirements.yaml', 'status: event-only', 'status: [event-only]', "requirement DEV-CRA-02: status must be documented or event-only, found ['event-only']"),
    ('kit fact use is a list', '25-kits/content.yaml', 'use: headline', 'use: [headline]', "fact F-001: use must be one of stat, headline, context, found ['headline']"),
    ('kit quote claim is a list', '25-kits/content.yaml', 'claim: D1-C001}', 'claim: [D1-C001]}', "quote Q-001: claim ['D1-C001'] does not exist"),
    ('kit caution is a list', '25-kits/content.yaml', 'caution: The Day 2 repeat is not documented.', 'caution: [x]', 'angle A-001: caution must be a string'),
    # the differences ledger (25-kits/differences.yaml): every row cites public claims of the right kind, and Google's side is a Google page
    ('ledger cites a private claim', DIFF_FILE, None, diff_bad('event: [D2-C001]', 'event: [D2-C001, D1-C007]'), 'difference DIF-01: cites D1-C007, which is private'),
    ('ledger cites a missing claim', DIFF_FILE, None, diff_bad('docs: [D1-C006]', 'docs: [D1-C099]'), 'difference DIF-01: cites D1-C099, which does not exist'),
    ('ledger event is a press claim', DIFF_FILE, None, diff_bad('event: [D2-C001]', 'event: [D1-C004]'),
     'difference DIF-01: event lists D1-C004, which is a press claim; event takes a slide or stage claim'),
    ('ledger event is an audience question', DIFF_FILE, None, diff_bad('event: [D2-C001]', 'event: [D1-C002]'), 'difference DIF-01: event lists D1-C002, an audience question'),
    ('ledger docs is a slide claim', DIFF_FILE, None, diff_bad('docs: [D1-C006]', 'docs: [D2-C002]'), 'difference DIF-01: docs lists D2-C002, which is a slide claim'),
    ('ledger analysis is a stage claim', DIFF_FILE, None, diff_bad('analysis: [D1-C005]', 'analysis: [D1-C003]'), 'difference DIF-01: analysis lists D1-C003, which is a stage claim'),
    ('ledger page is a press source', DIFF_FILE, None, diff_bad('docs: [D1-C006]', 'docs: [D1-C006]\n    pages: [sej]'), 'difference DIF-01: pages key sej is a press source'),
    ('ledger without the documented side', DIFF_FILE, None, diff_bad('docs: [D1-C006]', 'docs: []'), "difference DIF-01: needs Google's side"),
    ('ledger claim in two lists', DIFF_FILE, None, diff_bad('analysis: [D1-C005]', 'analysis: [D1-C005, D2-C001]'),
     'difference DIF-01: D2-C001 is listed in more than one of event, docs and analysis'),
    ('ledger duplicate row id', DIFF_FILE, None, DIFF_FIX + DIFF_FIX.split('\n', 1)[1], '25-kits/differences.yaml: id DIF-01 is used 2 times'),
    ('ledger row id format', DIFF_FILE, None, diff_bad('id: DIF-01', 'id: DIF-1'), 'difference DIF-1: id must look like DIF-01'),
    ('ledger follow names the excluded photo', DIFF_FILE, None, diff_bad('crawl demand.', 'crawl demand (IMG_4692).'), 'difference DIF-01: names IMG_4692'),
    ('ledger follow mentions a private claim', DIFF_FILE, None, diff_bad('crawl demand.', 'crawl demand (D1-C007).'), 'difference DIF-01: mentions D1-C007, which is private'),
]


def make_fixture(name, edits=(), site=False, tools=False):
    root = TMP / name
    if root.exists(): shutil.rmtree(root)
    for rel, txt in FIX.items(): w(root / rel, textwrap.dedent(txt).lstrip())
    (root / '_system' / 'templates').mkdir(parents=True)
    for f in CODE:
        if (REPO / f).exists(): shutil.copy(REPO / f, root / f)  # a missing badges.py is reported by the build itself
    for f in (REPO / '_system' / 'templates').iterdir(): shutil.copy(f, root / '_system' / 'templates' / f.name)
    if site: shutil.copytree(REPO / '_system' / 'site', root / '_system' / 'site', ignore=shutil.ignore_patterns('__pycache__'))
    if tools:
        shutil.copytree(REPO / '_system' / 'tools', root / '_system' / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy(REPO / '_system' / 'eval' / 'eval_check.py', root / '_system' / 'eval' / 'eval_check.py')
        shutil.copy(REPO / 'ingest.bat', root / 'ingest.bat')
    for rel, old, new in edits:
        p = root / rel
        if old is None: w(p, new); continue
        t = p.read_text(encoding='utf-8')
        assert old in t, f'fixture edit not applicable: {old!r} in {rel}'
        w(p, t.replace(old, new, 1))
    return root


def w(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8', newline='\n')


def run_py(root, script, *args, **kw):
    r = subprocess.run([sys.executable, str(root / script), *args], cwd=root, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', env=dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1'), **kw)
    return r.returncode, r.stdout + r.stderr


def build(root, *args):
    return run_py(root, '_system/build_kb.py', *args)


def build_site(root):
    return run_py(root, '_system/site/build_site.py')


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def shared_files(root):
    return sorted([p for d in SHARED for p in (root / d).rglob('*') if p.is_file()] + [root / f for f in SHARED_FILES if (root / f).is_file()])


def built_edition(root):
    """The edition of a built tree, as its agent pack says (content-library.json "edition"; the full edition writes none)."""
    f = root / '60-outputs' / 'agent-pack' / 'content-library.json'
    return (json.loads(f.read_text(encoding='utf-8')).get('edition') or 'full') if f.exists() else 'full'


def tree_hash(root, dirs=SHARED + ['70-private']):
    out = {}
    for d in dirs:
        for p in sorted((root / d).rglob('*')):
            if p.is_file(): out[p.relative_to(root).as_posix()] = hashlib.sha1(p.read_bytes()).hexdigest()
    for f in SHARED_FILES:
        if (root / f).is_file(): out[f] = hashlib.sha1((root / f).read_bytes()).hexdigest()
    return out


def shared_text(root):
    return {p.relative_to(root).as_posix(): p.read_text(encoding='utf-8') for p in shared_files(root)}


GENERATED_TAGS = re.compile(r'<br><sub>|</sub>|<!-- GENERATED by _system/build_kb\.py\. Do not edit; change 20-claims/ and rebuild\. -->'
                            r'|<!-- GENERATED by _system/kits\.py from 25-kits/\. Do not edit; change 25-kits/ and rebuild\. -->')
FENCED = re.compile(r'^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$', re.M | re.S)  # fenced code: literal text in CommonMark
# The only HTML a generated README may hold, written here independently of build_kb.py: whole lines of the divider, the
# centring around the navigation and the badge row of 60-outputs/README.md (the nine badges with their fixed alt texts), and
# the <sub> that opens the navigation line (its Markdown is still scanned).
README_HTML_LINES = {f'<p align="center"><img src="{up}_system/brand/divider.svg" width="600" alt="Section divider"></p>' for up in ('../', '../../')} \
    | {'<div align="center">', '</div>'}
BADGE_ALT = {'version': 'Version and the date the data runs to', 'days': 'Event days covered so far', 'claims': 'Number of public claims',
             'docs-backed': "Share of graded slide and stage claims that Google's documentation confirms or supports", 'topics': 'Number of topics',
             'sources': 'Number of sources', 'dev-kit': 'Developer kit: number of requirements', 'media-kit': 'Media kit: number of facts',
             'privacy': 'Privacy: private material excluded'}
BADGE_ALT_COMMUNITY = {'media-kit': 'Media kit: full edition on request'}  # the community edition's badge says the full kit is on request
BADGE_IMG = r'<img src="badges/([a-z-]+)\.svg" alt="([^"<>]*)">'
# the header illustration of a generated README: its own card from _system/brand/illustrations/ (the slug must match the README's
# folder: readme_problems checks that), the dark card for GitHub's dark theme, and a plain-text alt (no quote, tag or entity)
ART_SLUGS = {'30-topics', '40-sessions', '50-maps', '60-outputs', '60-outputs-content', '60-outputs-dev'} | {f'30-topics-{a}' for a in (
    'ai-features', 'community', 'content-and-media', 'crawling', 'how-search-works', 'index-and-signals', 'indexing', 'international',
    'publisher-controls', 'rendering-javascript', 'search-console', 'search-landscape', 'search-trends', 'serving-ranking')}
PICTURE_LINE = re.compile(r'<picture><source media="\(prefers-color-scheme: dark\)" srcset="((?:\.\./)+)_system/brand/illustrations/([a-z0-9-]+)-dark\.svg">'
                          r'<img src="\1_system/brand/illustrations/\2-light\.svg" width="100%" alt="([A-Z][^"<>&]{20,300})"></picture>')
BADGE_LINE = re.compile(rf'<p align="center">{BADGE_IMG}(?:(?: |<br>){BADGE_IMG})*</p>')


def static_html(line):
    """The line with its fixed README HTML taken out: '' for a whole fixed line (a badge row only with known badges and their own
    alt texts, a header illustration only of a known card with a plain alt text), the rest of a navigation line after its opening
    <sub> (the closing </sub> is allowed anyway), else the line."""
    if line in README_HTML_LINES or (BADGE_LINE.fullmatch(line) and all(alt in (BADGE_ALT.get(n), BADGE_ALT_COMMUNITY.get(n)) for n, alt in re.findall(BADGE_IMG, line))): return ''
    m = PICTURE_LINE.fullmatch(line)
    if m and m[2] in ART_SLUGS: return ''
    return line[len('<sub>'):] if line.startswith('<sub>') and line.endswith('</sub>') else line


def raw_html(md_text):
    """Every '<' a CommonMark renderer could read as the start of raw HTML or an autolink, apart from the tags the build
    writes itself. Reads inline text left to right as CommonMark does: a backslash escapes the next character, a backtick
    run opens a code span only when a later run of exactly the same length closes it (code spans may cross lines inside a
    paragraph, so each paragraph and each line is scanned), a '<' met before a backtick wins over it. Front matter is skipped,
    and so is the fixed README HTML (static_html)."""
    if md_text.startswith('---\n'): md_text = md_text.split('\n---\n', 1)[-1]
    md_text = '\n'.join(static_html(l) for l in FENCED.sub('', md_text).split('\n'))
    found = []
    for para in re.split(r'\n[ \t]*\n', md_text):
        for seg in [para] + para.split('\n'):
            i = 0
            while i < len(seg):
                ch = seg[i]
                if ch == '\\': i += 2; continue
                if ch == '`':
                    j = i
                    while j < len(seg) and seg[j] == '`': j += 1
                    m = re.compile(rf'(?<!`){"`" * (j - i)}(?!`)').search(seg, j)
                    i = m.end() if m else j
                    continue
                if ch == '<':
                    g = GENERATED_TAGS.match(seg, i)
                    if g: i = g.end(); continue
                    if re.match(r'<[A-Za-z!/?]', seg[i:i + 2]): found.append(seg[i:i + 40])
                i += 1
    return found


def mindmap_data(root):
    html = (root / '50-maps' / 'mindmap.html').read_text(encoding='utf-8')
    m = re.search(r'const DATA = (.*?);\nconst NS', html, re.S)
    assert m, 'DATA line not found in mindmap.html'
    return html, json.loads(m[1])


def check_mindmap_browser(path):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return 'skipped (Playwright not installed)'
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        try:
            for width in (1280, 390):
                pg = b.new_page(viewport={'width': width, 'height': 800})
                errs = []
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.goto(Path(path).resolve().as_uri())
                r = pg.evaluate("() => ({data: typeof DATA === 'object' && DATA !== null, svg: document.querySelectorAll('#map svg').length,"
                                " img: document.querySelectorAll('body img').length, sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,"
                                " chips: [...document.querySelectorAll('#days button')].map(b => b.textContent)})")
                assert r['data'] and r['svg'] == 1 and not r['img'] and not errs, f'mindmap broken at {width}px: {r} {errs}'
                assert r['sw'] <= r['cw'], f'horizontal page overflow at {width}px: {r}'
                assert r['chips'][0] == 'All' and all(x.startswith('Day ') for x in r['chips'][1:]), r['chips']
        finally:
            b.close()
    return 'ok'


# ---------------------------------------------------------------- tests
def test_fixture_builds_clean():
    root = make_fixture('clean')
    code, out = build(root)
    assert code == 0, out
    assert 'ERROR' not in out and 'v9.9.9' in out and 'data through 2026-10-01 (Day 2)' in out, out


def test_validation_errors_stop_before_writing():
    failures = []
    for name, rel, old, new, expect in BAD:
        root = make_fixture('bad-' + re.sub(r'\W+', '-', name), [(rel, old, new)])
        for d in SHARED: w(root / d / 'SENTINEL.txt', 'keep')
        code, out = build(root)
        problems = []
        if code == 0: problems.append('build passed')
        if expect not in out: problems.append(f'missing message {expect!r}')
        if 'Traceback' in out: problems.append('crashed with a traceback')
        if any(not (root / d / 'SENTINEL.txt').exists() for d in SHARED): problems.append('generated folders were touched')
        if problems: failures.append(f'{name}: {"; ".join(problems)}\n    output: {out.strip()[:400]}')
        shutil.rmtree(root, ignore_errors=True)
    assert not failures, '\n  '.join([''] + failures)


def test_string_src_reports_once():
    root = make_fixture('src-once', [BAD[[b[0] for b in BAD].index('string src')][1:4]])
    code, out = build(root)
    assert code != 0 and out.count('src must be a list') == 1 and 'unknown source c' not in out, out


def test_check_mode_writes_nothing():
    root = make_fixture('check')
    code, out = build(root, '--check')
    assert code == 0 and 'Nothing was written' in out, out
    assert not any((root / d).exists() for d in SHARED), 'files written in --check mode'


BYPASS = ['Use the ` key; then <img src=x onerror=alert(1)> is shown',            # RC-12: a stray backtick paired with an inserted one
          '<img alt="<" onerror=alert(2)> and <a href="`">x</a>`',                  # a '<' inside a tag, a tag holding a backtick
          '``a ` b`` <i>x</i>`<b>`<svg onload=alert(3)>``', '\\`<img src=y onerror=alert(4)>`', 'ends with a backslash \\']


def test_html_in_text_is_safe():
    nasty = 'Googlebot ignores anything after <!-- in inline <script> blocks; JS in </script><img src=x onerror=alert(1)> is fine & <b>bold</b> stays text.'
    root = make_fixture('html', [('20-claims/day1.yaml', 'text: "Crawl budget is crawl rate limit plus crawl demand."', 'text: ' + json.dumps(nasty)),
                                 ('20-claims/day1.yaml', 'text: "Most sites should spend effort on quality, not crawl budget."',
                                  'text: ' + json.dumps('Multi-line claim about <meta name="robots" content="noindex">,\nsecond line of the same claim.\n')),
                                 ('20-claims/day1.yaml', 'text: "The documentation lists crawl capacity limit and crawl demand."', 'text: ' + json.dumps(BYPASS[0])),
                                 ('20-claims/day1.yaml', 'text: "An audience member asked whether small sites need to worry about crawl budget."', 'text: ' + json.dumps(BYPASS[1])),
                                 ('20-claims/day2.yaml', 'text: "A slide showed a canonical link element in the head."', 'text: ' + json.dumps(BYPASS[2])),
                                 ('20-claims/sessions.yaml', 'title: "Crawl talk"', 'title: ' + json.dumps(BYPASS[3])),
                                 ('20-claims/topics.yaml', 'title: Canonicals', 'title: ' + json.dumps(BYPASS[4]))])
    code, out = build(root)
    assert code == 0, out
    assert 'spans several lines' in out, 'no warning for a multi-line text'
    html, data = mindmap_data(root)
    texts = [c['text'] for a in data['areas'] for t in a['topics'] for c in t['claims']]
    assert nasty in texts, 'claim text did not survive the JSON round trip'
    assert 'Multi-line claim about <meta name="robots" content="noindex">, second line of the same claim.' in texts, 'multi-line text not joined'
    script = html.split('const DATA = ', 1)[1]
    assert '</script' not in script.split('\n', 1)[0] and '<!--' not in script.split('\n', 1)[0], 'raw </script> or <!-- inside the inline JSON'
    n_tpl = (REPO / '_system' / 'templates' / 'mindmap.template.html').read_text(encoding='utf-8').lower().count('</script>')
    assert html.lower().count('</script>') == n_tpl, f'{html.lower().count("</script>")} closing script tags, the template has {n_tpl}'
    page = (root / '30-topics' / 'crawling' / 'crawl-budget.md').read_text(encoding='utf-8')
    for frag in ('&lt;!-- in inline `<script>` blocks; JS in `</script>`&lt;img src=x onerror=alert(1)> is fine', '`<b>`bold`</b>`',
                 '`<meta name="robots" content="noindex">`', 'Use the \\` key; then `<img src=x onerror=alert(1)>` is shown',
                 '&lt;img alt="&lt;" onerror=alert(2)> and &lt;a href="`">x</a>`'):
        assert frag in page, f'{frag} not rendered safely:\n{page}'
    n_md = 0
    for rel, txt in shared_text(root).items():
        if rel.endswith('.md'): n_md += 1; assert not raw_html(txt), f'{rel}: raw HTML left in Markdown: {raw_html(txt)[:3]}'
    assert n_md > 10
    mm = (root / '50-maps' / 'mindmap.markmap.md').read_text(encoding='utf-8')
    assert not raw_html(mm) and '\nsecond line' not in mm
    print('    browser check:', check_mindmap_browser(root / '50-maps' / 'mindmap.html'))


def test_markdown_escaping_follows_commonmark():  # RC-12
    bk = load_module(REPO / '_system' / 'build_kb.py', 'bk_md')
    want = {'Use the ` key; then <img src=x onerror=alert(1)> is shown': 'Use the \\` key; then `<img src=x onerror=alert(1)>` is shown',
            '`<b>` stays code': '`<b>` stays code', '``a ` b`` <i>': '``a ` b`` `<i>`', '\\<i> and \\` tick': '\\<i> and \\` tick',
            'ends with \\': 'ends with \\\\', '<img alt="<" onerror=alert(2)>': '&lt;img alt="&lt;" onerror=alert(2)>',
            'a < b and c > d': 'a &lt; b and c > d', 'x ```y`` z': 'x \\`\\`\\`y\\`\\` z', '<a href="`">': '&lt;a href="\\`">',
            '`x`<b>': '`x`&lt;b>', '<b>`x`': '&lt;b>`x`', 'plain text, 100% fine': 'plain text, 100% fine'}
    bad = [(s, bk.md(s), x) for s, x in want.items() if bk.md(s) != x]
    assert not bad, bad
    vectors = BYPASS + ['<!-- c -->', '<?php x ?>', '<![CDATA[x]]>', '<https://example.com>', '<a@b.co>', '``<i>``<b>', '`<i>`<b>`', '<b>```']
    for v in vectors:
        o = bk.md(v)
        for ctx in (o, f'`D1-C001` **[Slide]** {o}', f'- [{o}](x.md) · `D1-C002` {o}', f'- **[Slide]** {o}\n  > "{o}"\n  <br><sub>`D1-C001` · {o}</sub>'):
            assert not raw_html(ctx), (v, ctx, raw_html(ctx))


def test_v2_rendering_and_pack():
    import jsonschema
    root = make_fixture('render')
    code, out = build(root)
    assert code == 0, out
    P = root / '60-outputs' / 'agent-pack'
    rows = [json.loads(l) for l in (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines()]
    schema = json.loads((P / 'claims.schema.json').read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator.check_schema(schema)
    v = jsonschema.Draft202012Validator(schema)
    for r in rows: assert not list(v.iter_errors(r)), (r['id'], [e.message for e in v.iter_errors(r)])
    by = {r['id']: r for r in rows}
    assert 'D1-C007' not in by
    assert list(rows[0]) == ['id', 'day', 'session_id', 'session', 'speaker', 'who', 'author', 'label', 'label_meaning', 'text', 'quote', 'quote_checked',
                             'verification', 'topics', 'sources', 'evidence', 'relations', 'related_from', 'used_by', 'mentions']
    assert by['D1-C001']['speaker'] == 'Gary Illyes' and by['D1-C001']['quote_checked'] is True and by['D1-C001']['evidence'] == ['IMG_0001']
    assert by['D1-C002']['speaker'] == 'audience' and by['D1-C002']['who'] == 'audience'
    assert by['D1-C003']['relations'] == [{'type': 'answers', 'to': 'D1-C002'}] and by['D1-C002']['related_from'] == [{'type': 'answers', 'from': 'D1-C003'}]
    assert by['D1-C004']['speaker'] is None and by['D1-C004']['author'] == 'Search Engine Journal' and by['D1-C004']['label_meaning'] == 'reported by third-party press' and by['D1-C004']['sources'][0]['kind'] == 'press'
    assert by['D1-C005']['speaker'] is None and by['D1-C005']['author'] == 'Ibrahim Anjro' and by['D1-C006']['author'] == 'Google' and by['D1-C001']['author'] is None
    assert by['D2-C002']['evidence'] == ['IMG_0003', 'IMG_0004'] and by['D2-C001']['evidence'] == ['video:IMG_0002']
    tj = json.loads((P / 'topics.json').read_text(encoding='utf-8'))
    cb = tj['areas'][0]['topics'][0]
    assert tj['version'] == 'v9.9.9' and tj['data_through'] == '2026-10-01'
    assert list(cb) == ['id', 'title', 'summary', 'cites', 'do', 'related', 'claim_ids', 'sessions', 'days', 'event_sessions', 'event_days']
    assert cb['event_sessions'] == ['D1-S01', 'D1-S02', 'D2-S01'] and cb['event_days'] == [1, 2] and cb['cites'] == ['D1-C001', 'D1-C003']
    canon = tj['areas'][1]['topics'][0]
    assert canon['sessions'] == ['D1-S00', 'D2-S01'] and canon['event_sessions'] == ['D2-S01'], canon
    sj = json.loads((P / 'sessions.json').read_text(encoding='utf-8'))
    s00 = [s for s in sj['days'][0]['sessions'] if s['id'] == 'D1-S00'][0]
    d2 = sj['days'][1]['sessions'][0]
    assert s00['kind'] == 'unrecorded' and d2['speakers'] == ['Martin Splitt', 'John Mueller'] and d2['coverage'] == ['transcript', 'slides'] and d2['role'] == 'Search Advocates'
    assert len(sj['days']) == 3 and sj['days'][2]['sessions'] == []
    src = json.loads((P / 'sources.json').read_text(encoding='utf-8'))
    assert src['sej']['kind'] == 'press' and src['crawl-guide']['kind'] == 'google'
    assert not (P / 'eval-questions.yaml').exists() and not any('questions' in p.name for p in P.rglob('*'))
    ix = (P / 'INDEX.md').read_text(encoding='utf-8')
    assert 'Version v9.9.9 · data through 2026-10-01 (Day 2)' in ix and '`D1-S03`' in ix and 'Based on: D1-C001, D1-C003.' in ix and 'claims.schema.json' in ix
    T = root / '30-topics'
    page = (T / 'crawling' / 'crawl-budget.md').read_text(encoding='utf-8')
    fm = yaml.safe_load(page.split('---')[1])
    assert fm['last_discussed'] == '2026-10-01' and fm['event_days'] == [1, 2] and 'updated' not in fm
    assert 'Based on: `D1-C001`, `D1-C003`.' in page
    assert '## Where it was discussed' in page and '**Day 2** (2026-10-01, Indexing): [Indexing talk](../../40-sessions/day2/D2-S01-indexing-talk.md) (1 claim)' in page
    assert 'Repeated by [D2-C001](../../40-sessions/day2/D2-S01-indexing-talk.md)' in page
    assert 'Answers [D1-C002](../../40-sessions/day1/D1-S02-q-a.md)' in page
    assert '(audience member)' in page and '(Gary Illyes)' in page
    assert '`D1-C005` · Ibrahim Anjro (author) · annotates Day 1, Crawl talk' in page
    canon_page = (T / 'indexing' / 'canonical.md').read_text(encoding='utf-8')
    assert '## What the press reported' in canon_page and 'is the press report' in canon_page and 'Search Engine Journal · annotates Day 1' in canon_page
    assert '(Martin Splitt)' in canon_page and 'Extended by [D2-C002]' in canon_page
    qa = (root / '40-sessions' / 'day1' / 'D1-S02-q-a.md').read_text(encoding='utf-8')
    assert re.search(r'- \*\*\[Stage\]\*\* An audience member asked.*\n.*\n\n?  - \*\*\[Stage\]\*\* Gary Illyes answered', qa), 'Q&A answer not nested under its question'
    assert '· qa · coverage: notes, transcript' in qa and 'Gary Illyes, Cherry Prommawin' in qa
    pk = (P / 'topics' / 'crawl-budget.md').read_text(encoding='utf-8')
    assert '](../sessions/D2-S01-indexing-talk.md)' in pk and '](canonical.md)' in pk and '30-topics' not in pk and '40-sessions' not in pk
    ps = (P / 'sessions' / 'D1-S02-q-a.md').read_text(encoding='utf-8')
    assert '](../topics/crawl-budget.md)' in ps and '30-topics' not in ps
    M = root / '50-maps'
    mx = (M / 'mention-matrix.md').read_text(encoding='utf-8')
    assert '## Across days' in mx and '## Day 1 — Crawling (2026-09-30)' in mx and '## Day 2 — Indexing (2026-10-01)' in mx
    assert '| Crawl budget | 3 | 1 | 2 | 3 | 4 | 6 |' in mx, mx
    assert '| Canonicals |  | 2 | 1 | 1 | 2 | 3 |' in mx, mx
    vr = (M / 'verification-report.md').read_text(encoding='utf-8')
    assert '## All days' in vr and '## Day 1 — Crawling' in vr and '## Day 2 — Indexing' in vr
    ad = (M / 'across-days.md').read_text(encoding='utf-8')
    for k in ('## Repeats (1)', '## Extends (1)', '## Answers (1)', 'Martin Splitt repeated', 'Crawl budget is crawl rate limit'):
        assert k in ad, k
    html, data = mindmap_data(root)
    assert data['version'] == 'v9.9.9' and data['data_through'] == '2026-10-01 (Day 2)' and [d['day'] for d in data['days']] == [1, 2, 3]
    assert data['days'][2]['claims'] == 0 and 'Built' not in html
    for rel, txt in shared_text(root).items():
        assert 'SECRETPRIVATEMARKER' not in txt and 'D1-C007' not in txt, f'private claim leaked into {rel}'
    assert 'SECRETPRIVATEMARKER' in (root / '70-private' / 'private-claims.md').read_text(encoding='utf-8')
    for p in (root / d for d in SHARED):
        for f in p.rglob('*'):
            if f.is_file(): assert b'\r' not in f.read_bytes(), f'CR in {f}'


def test_backlinks_and_graph_json():  # knowledge graph phase 0: used_by equals the kits' lists, every graph.json edge resolves, aliases, speakers
    root = make_fixture('graph')
    code, out = build(root)
    assert code == 0, out
    P = root / '60-outputs' / 'agent-pack'
    rows = [json.loads(l) for l in (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines()]
    dj, lib = (json.loads((P / f).read_text(encoding='utf-8')) for f in ('dev-requirements.json', 'content-library.json'))
    links, graph = (json.loads((P / f).read_text(encoding='utf-8')) for f in ('links.json', 'graph.json'))
    # what rests on each claim, counted straight from the kits
    want = {}
    for a in dj['areas']:
        for r in a['requirements']: want[f"req:{r['id']}"] = [c['id'] for c in r['claims']]
    for k, p in (('facts', 'fact'), ('myths', 'myth')):
        for x in lib[k]: want[f"{p}:{x['id']}"] = [c['id'] for c in x['claims']]
    for x in lib['quotes']: want[f"quote:{x['id']}"] = [x['claim']]
    for x in lib['angles']: want[f"angle:{x['id']}"] = list(dict.fromkeys(c['id'] for p in x['points'] for c in p['claims']))
    for x in lib['glossary']: want[f"term:{x['id']}"] = [c['id'] for c in x['claims']]
    assert set(want) == set(links['items']), sorted(set(want) ^ set(links['items']))
    for r in rows:
        assert sorted(r['used_by']) == sorted(n for n, cs in want.items() if r['id'] in cs), r['id']
        assert r['used_by'] == links['used_by'].get(r['id'], []), r['id']
    assert links['used_by']['D1-C001'] == ['req:DEV-CRA-01', 'fact:F-001', 'quote:Q-001', 'angle:A-001', 'term:crawl-budget'], links['used_by']['D1-C001']
    # kit items carry topics from their claims; the CSV has the column
    assert dj['areas'][0]['requirements'][0]['topics'] == ['crawl-budget'] and lib['glossary'][0]['id'] == 'canonical-url'
    rows_csv = list(csv.DictReader(io.StringIO((root / '60-outputs' / 'dev' / 'requirements.csv').read_text(encoding='utf-8'), newline='')))
    assert rows_csv[0]['topics'] == 'crawl-budget' and list(rows_csv[0])[9:12] == ['claims', 'topics', 'docs']
    # the graph: every end a node, sorted, no private claim, kinds and types as documented
    ids = [n['id'] for n in graph['nodes']]
    assert ids == sorted(ids) and len(ids) == len(set(ids))
    E = [(e['from'], e['type'], e['to']) for e in graph['edges']]
    assert E == sorted(E) and len(E) == len(set(E)) and all(f in set(ids) and t in set(ids) for f, _, t in E)
    assert 'claim:D1-C007' not in ids and 'D1-C007' not in json.dumps(links)
    assert ('claim:D1-C003', 'answers', 'claim:D1-C002') in E and ('topic:crawl-budget', 'cites', 'claim:D1-C001') in E
    assert ('req:DEV-CRA-01', 'rests-on', 'claim:D1-C001') in E and ('req:DEV-CRA-01', 'documented-in', 'source:crawl-guide') in E
    assert ('session:D2-S01', 'on', 'day:2') in E and ('topic:crawl-budget', 'in', 'area:crawling') in E
    for t, e in graph['edge_types'].items(): assert e['count'] == sum(1 for x in E if x[1] == t) > 0, t
    assert set(links['topic_items']) == {t['id'] for a in json.loads((P / 'topics.json').read_text(encoding='utf-8'))['areas'] for t in a['topics']}
    # sources by grade, aliases, speaker filter (proven names only)
    assert links['sources']['crawl-guide'] == {'claims': {'source': ['D1-C006'], 'confirmed': ['D1-C001'], 'consistent': ['D1-C003']}, 'requirements': ['req:DEV-CRA-01', 'req:DEV-CRA-03']}, links['sources']['crawl-guide']
    assert links['aliases']['crawl budget'] == ['term:crawl-budget'] and links['aliases']['canonical url'] == ['term:canonical-url']
    names = {c['speaker'] for x in lib['facts'] + lib['myths'] + lib['glossary'] for c in x['claims'] if c['speaker']}
    assert {n['name'] for n in links['speakers']['names']} <= {r['speaker'] for r in rows if r['speaker']} and 'Martin Splitt' in {n['name'] for n in links['speakers']['names']}, links['speakers']
    assert names <= {n['name'] for n in links['speakers']['names']}
    assert set(links['speakers']['claims']) == {r['id'] for r in rows if r['label'] in ('slide', 'stage')}
    # the Markdown backlinks
    page = (root / '30-topics' / 'crawling' / 'crawl-budget.md').read_text(encoding='utf-8')
    assert '## Built on these claims' in page and '- Requirement `DEV-CRA-01`: Keep crawl capacity healthy' in page and '- Glossary term *Crawl budget*' in page
    assert 'Used by `DEV-CRA-01`, `F-001`, `Q-001`, `A-001`, the glossary term *Crawl budget*' in page
    ix = (P / 'INDEX.md').read_text(encoding='utf-8')
    assert '## The graph' in ix and '[`graph.json`](graph.json)' in ix and '`rests-on`' in ix and '## Links and the graph' in (P / 'AGENTS.md').read_text(encoding='utf-8')
    # a glossary term whose id would clash with another's is refused before anything is written
    root = make_fixture('graph-clash', [('25-kits/content.yaml', '- {term: canonical URL,', '- {term: Crawl-budget, definition: Same id., claims: [D1-C001]}\n  - {term: canonical URL,')])
    code, out = build(root, '--check')
    assert code != 0 and 'share the id term:crawl-budget' in out and 'Traceback' not in out, out
    # the Python fold is the web edition's
    kb = load_module(root / '_system' / 'build_kb.py', 'kb_fold')
    assert kb.norm_key('Łukasz Straße — Crème-brûlée!') == 'lukasz strasse creme brulee' and kb.node_slug('Discovered – currently not indexed') == 'discovered-currently-not-indexed'
    # graph.json and links.json are byte-identical on a rebuild in place and in another folder
    root = make_fixture('graph')
    P = root / '60-outputs' / 'agent-pack'
    assert build(root)[0] == 0
    first = {f: (P / f).read_bytes() for f in ('graph.json', 'links.json')}
    assert build(root)[0] == 0 and {f: (P / f).read_bytes() for f in first} == first, 'a rebuild changes graph.json or links.json'
    other = make_fixture('graph-b')
    assert build(other)[0] == 0
    assert {f: (other / '60-outputs' / 'agent-pack' / f).read_bytes() for f in first} == first, 'graph.json or links.json depends on the folder'
    assert all(b'\r' not in v for v in first.values())


# ---------------------------------------------------------------- knowledge graph phase 1: things (20-claims/entities.yaml)
ENT_FIX = '''
entities:
  - id: crawl-budget-metric
    kind: metric
    name: crawl budget
    summary: How much Google crawls a site.
    glossary: Crawl budget
    docs: [crawl-guide]
    topics: [crawl-budget]
    rel:
      - {type: affects, to: crawl-demand-metric, claims: [D1-C001]}
    pin: [D1-C003]
  - id: crawl-demand-metric
    kind: metric
    name: crawl demand
    summary: How much Google wants to crawl a site.
    rel:
      - {type: part-of, to: crawl-budget-metric}
  - id: canonical-link
    kind: directive
    name: canonical link element
    aliases: [{s: canonical link, in: [canonical]}]
    summary: The link element that names the preferred URL.
  - id: url-inspection
    kind: tool
    name: URL Inspection
    summary: The Search Console tool that shows how Google sees one URL.
'''
ENT_FILE = '20-claims/entities.yaml'


def ent_fixture(name, *edits):
    return make_fixture(name, [(ENT_FILE, None, ENT_FIX)] + [(ENT_FILE, o, n) for o, n in edits])


def ent_build_fails(name, old, new, want):  # one bad entry: a clear error, no traceback, and nothing written
    root = ent_fixture('ent-bad', (old, new))
    for d in ('30-topics', '60-outputs/agent-pack'): w(root / d / 'SENTINEL.txt', 'keep')
    code, out = build(root)
    assert code != 0 and want in out and 'Traceback' not in out, f'{name}: {out[-600:]}'
    P = root / '60-outputs' / 'agent-pack'
    assert (P / 'SENTINEL.txt').exists() and not (P / 'entities.json').exists(), f'{name}: outputs were touched'


def test_entities_validate_and_match():  # knowledge graph phase 1: matching, via, scope, pin, derived links; each bad entry a clear error
    root = ent_fixture('ent')
    code, out = build(root)
    assert code == 0, out
    assert 'WARNING: entity url-inspection: no public claim mentions it' in out and 'OK: things: 4 things' in out, out
    P = root / '60-outputs' / 'agent-pack'
    rows = {r['id']: r for r in map(json.loads, (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines())}
    assert rows['D1-C001']['mentions'] == [{'entity': 'crawl-budget-metric', 'via': 'Crawl budget', 'field': 'text'},
                                           {'entity': 'crawl-demand-metric', 'via': 'crawl demand', 'field': 'text'}], rows['D1-C001']['mentions']
    assert rows['D1-C003']['mentions'] == [{'entity': 'crawl-budget-metric', 'via': None, 'field': 'pin'}]
    assert rows['D2-C002']['mentions'] == [{'entity': 'canonical-link', 'via': 'canonical link element', 'field': 'text'}]
    for r in rows.values():  # every via is the claim's own words
        for m in r['mentions']: assert m['field'] == 'pin' or m['via'] in r[m['field']], (r['id'], m)
    E = json.loads((P / 'entities.json').read_text(encoding='utf-8'))
    cb = next(x for x in E['entities'] if x['id'] == 'crawl-budget-metric')
    assert cb['glossary'] == 'crawl-budget' and cb['docs'] == ['crawl-guide'] and cb['rel_from'] == [{'type': 'part-of', 'from': 'crawl-demand-metric', 'claims': []}]
    assert cb['co_mentioned'][0]['id'] == 'crawl-demand-metric' and 'D1-C001' in cb['co_mentioned'][0]['claims']
    assert cb['cite']['D1-C001'] == '[D1-C001, slide, Google, Day 1]' and cb['cite']['D1-C003'] == '[D1-C003, stage, Gary Illyes, Day 1]' \
        and next(x for x in E['entities'] if x['id'] == 'crawl-demand-metric')['cite']['D1-C006'].startswith('[D1-C006, docs, Google, https://')
    assert E['topic_entities']['crawl-budget'][0]['id'] == 'crawl-budget-metric' and E['topic_entities']['empty-topic'] == []
    g = json.loads((P / 'graph.json').read_text(encoding='utf-8'))
    ids = {n['id'] for n in g['nodes']}
    ed = {(e['from'], e['type'], e['to']): e for e in g['edges']}
    assert all(f in ids and t in ids for f, _, t in ed)
    assert ed[('claim:D1-C001', 'mentions', 'ent:crawl-budget-metric')]['via'] == 'Crawl budget'
    assert ed[('claim:D1-C003', 'mentions', 'ent:crawl-budget-metric')] == {'from': 'claim:D1-C003', 'to': 'ent:crawl-budget-metric', 'type': 'mentions', 'field': 'pin'}
    assert ed[('ent:crawl-budget-metric', 'affects', 'ent:crawl-demand-metric')]['claims'] == ['D1-C001']
    assert ('ent:crawl-demand-metric', 'part-of', 'ent:crawl-budget-metric') in ed and ('term:crawl-budget', 'defines', 'ent:crawl-budget-metric') in ed
    assert ('ent:crawl-budget-metric', 'documented-in', 'source:crawl-guide') in ed and ('topic:crawl-budget', 'features', 'ent:crawl-budget-metric') in ed
    assert ed[('ent:crawl-budget-metric', 'co-mentioned', 'ent:crawl-demand-metric')]['count'] >= 1
    lib = json.loads((P / 'content-library.json').read_text(encoding='utf-8'))
    f1 = next(f for f in lib['facts'] if f['id'] == 'F-001')
    assert {e['id'] for e in f1['entities']} == {'crawl-budget-metric', 'crawl-demand-metric'} and all(e['own'] for e in f1['entities']), f1['entities']
    assert next(t for t in lib['glossary'] if t['id'] == 'crawl-budget')['defines'] == ['crawl-budget-metric']
    rows_csv = list(csv.DictReader(io.StringIO((root / '60-outputs' / 'dev' / 'requirements.csv').read_text(encoding='utf-8'), newline='')))
    assert list(rows_csv[0])[-1] == 'entities' and 'crawl-budget-metric' in rows_csv[0]['entities']
    card = (P / 'entities' / 'crawl-budget-metric.md').read_text(encoding='utf-8')
    assert '](../topics/crawl-budget.md) tells the story' in card and '`[D1-C001, slide, Google, Day 1]`' in card and 'most sites need not worry' not in card
    assert '## Things in this topic' in (root / '30-topics' / 'crawling' / 'crawl-budget.md').read_text(encoding='utf-8')
    ix = (root / '50-maps' / 'entity-index.md').read_text(encoding='utf-8')
    assert '## Precision sample' in ix and '## Every mention' in ix and '`url-inspection`' in ix and '## Things no claim mentions' in ix
    assert '## Things' in (P / 'INDEX.md').read_text(encoding='utf-8') and '(entity-index.md)' in (root / '50-maps' / 'README.md').read_text(encoding='utf-8')
    # no entities.yaml: no things, and the build is otherwise unchanged
    plain = make_fixture('ent-none')
    assert build(plain)[0] == 0 and 'No things yet' in (plain / '50-maps' / 'entity-index.md').read_text(encoding='utf-8')
    assert all(r['mentions'] == [] for r in map(json.loads, (plain / '60-outputs' / 'agent-pack' / 'claims.jsonl').read_text(encoding='utf-8').splitlines()))
    # each bad entry is a clear error and nothing is written
    for args in [('collision', 'name: URL Inspection', 'name: URL Inspection\n    aliases: [crawl demand]', 'is also a name or alias of crawl-demand-metric'),
                 ('stop word', 'name: URL Inspection', 'name: budget', 'is a common word'),
                 ('short alias', 'name: URL Inspection', 'name: URL Inspection\n    aliases: [UI]', 'fewer than 3 characters'),
                 ('rel to nothing', 'to: crawl-budget-metric}', 'to: nowhere}', 'rel part-of points to nowhere'),
                 ('factual rel without claims', '{type: part-of, to: crawl-budget-metric}', '{type: uses, to: crawl-budget-metric}', 'is a factual relation'),
                 ('rel claim not mentioning both', 'claims: [D1-C001]}', 'claims: [D2-C002]}', 'does not mention both things'),
                 ('topic id', 'id: url-inspection', 'id: canonical', 'is already a topic id'),
                 ('unknown key', 'kind: tool', 'kind: tool\n    colour: red', 'unknown key "colour"'),
                 ('unknown glossary term', 'glossary: Crawl budget', 'glossary: Crawl budgets', 'is not a term of 25-kits/content.yaml')]:
        ent_build_fails(*args)


def test_entities_never_leak_private():  # a private claim, an excluded photo or a person in entities.yaml stops the build; a private claim is never matched
    for args in [('pin of a private claim', 'pin: [D1-C003]', 'pin: [D1-C007]', 'pin lists D1-C007, which is private'),
                 ('private claim as rel evidence', 'claims: [D1-C001]}', 'claims: [D1-C007]}', 'D1-C007'),
                 ('excluded photo', 'summary: How much Google crawls a site.', 'summary: See IMG_4692.', 'names IMG_4692'),
                 ('excluded photo as an alias', 'name: URL Inspection', 'name: URL Inspection\n    aliases: [IMG_4692 slide]', 'names IMG_4692'),
                 ('person', 'summary: How much Google crawls a site.', 'summary: What Gary Illyes calls it.', 'things are never people'),
                 ('person as a thing', 'name: URL Inspection', 'name: Martin Splitt', 'things are never people')]:
        ent_build_fails(*args)
    # a spelling that only a private claim writes matches nothing, and the private claim reaches no output
    root = ent_fixture('ent-private', ('name: URL Inspection', 'name: URL Inspection\n    aliases: [remark about my own site]'))
    code, out = build(root)
    assert code == 0 and 'WARNING: entity url-inspection: no public claim mentions it' in out, out
    for rel, txt in shared_text(root).items():
        assert 'D1-C007' not in txt and 'SECRETPRIVATEMARKER' not in txt and 'IMG_4692' not in txt, rel


def test_entity_outputs_deterministic():  # the entity outputs are byte-identical on a rebuild and in another folder
    roots = [ent_fixture('ent-det-a'), ent_fixture('ent-det-b')]
    files = ('60-outputs/agent-pack/entities.json', '60-outputs/agent-pack/graph.json', '60-outputs/agent-pack/claims.jsonl', '50-maps/entity-index.md',
             '60-outputs/agent-pack/entities/crawl-budget-metric.md', '60-outputs/agent-pack/links.json')
    got = []
    for r in roots:
        assert build(r)[0] == 0
        first, h = {f: (r / f).read_bytes() for f in files}, tree_hash(r)
        assert build(r)[0] == 0 and {f: (r / f).read_bytes() for f in files} == first and tree_hash(r) == h
        got.append(first)
    assert got[0] == got[1] and all(b'\r' not in v for v in got[0].values())


SAMPLE_ROW = re.compile(r'^\| (\d+) \| \[`(D\d+-C\d{3})`\]\([^)]*\) \| `([a-z0-9-]+)` \| (.*?) \| (.*) \| \|$', re.M)


def precision_sample(root):  # the rows of the precision sample in 50-maps/entity-index.md, and the hashes of the 100 that claims.jsonl should give
    ix = (root / '50-maps' / 'entity-index.md').read_text(encoding='utf-8')
    rows = SAMPLE_ROW.findall(ix.split('## Precision sample', 1)[1].split('\n## ', 1)[0])
    P = root / '60-outputs' / 'agent-pack'
    ms = [(r['id'], m) for r in map(json.loads, (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines()) for m in r['mentions'] if m['field'] != 'pin']
    want = sorted(hashlib.sha1(f"{c} {m['entity']}".encode()).hexdigest() for c, m in ms)[:100]
    return rows, want, len(ms)


def test_entity_precision_sample():  # the sample is fixed by a hash of claim id and thing id, so the recorded review can be repeated
    root = ent_fixture('ent-sample')
    assert build(root)[0] == 0
    rows, want, n = precision_sample(root)
    assert len(rows) == len(want) == min(100, n) and rows, rows
    assert {hashlib.sha1(f'{c} {e}'.encode()).hexdigest() for _, c, e, _, _ in rows} == set(want)
    # the real data: 100 rows, and the review of that sample recorded in the latest changelog entry ("N wrong in 100", N under 5)
    root = real_copy('real-sample')
    rows, want, n = precision_sample(root)
    assert len(rows) == 100 and {hashlib.sha1(f'{c} {e}'.encode()).hexdigest() for _, c, e, _, _ in rows} == set(want), len(rows)
    top = (REPO / 'CHANGELOG.md').read_text(encoding='utf-8').split('\n## v', 2)[1]
    m = re.search(r'\b(\d+) wrong in 100\b', top)
    assert m and int(m[1]) < 5, 'the latest CHANGELOG entry must record the precision review of the sample: "N wrong in 100" with N under 5'


def test_evidence_warnings_never_fail():
    root = make_fixture('ev', [('20-claims/day2.yaml', 'ev: [IMG_0003, IMG_0004]', 'ev: [IMG_0003, "slide 4?"]')])
    w(root / '00-raw' / 'day1' / 'slides' / 'IMG_0001.HEIC', 'x')
    w(root / '00-raw' / 'day2' / 'video' / 'IMG_0002.MOV', 'x')
    w(root / '10-sources' / 'day1' / 'clean' / 'other.md', 'x')
    code, out = build(root)
    assert code == 0, out
    assert 'WARNING: D2-C002: evidence IMG_0003: no file named IMG_0003.* under 00-raw/day2/' in out, out
    assert 'unrecognised evidence "slide 4?"' in out and 'no 10-sources/day1/clean/t02.md' in out, out
    assert 'IMG_0001' not in out and 'IMG_0002' not in out, out


def test_deterministic_and_clock_free():
    for f in CODE:
        src = (REPO / f).read_text(encoding='utf-8') if (REPO / f).exists() else ''  # a missing badges.py fails every build
        assert not re.search(r'date\.today|datetime\.now|time\.time\(|utcnow|localtime', src), f'{f} reads the clock'
    a, b = make_fixture('det-a'), make_fixture('det-b')
    assert build(a)[0] == 0 and build(b)[0] == 0
    h1 = tree_hash(a)
    assert build(a)[0] == 0
    assert tree_hash(a) == h1, 'second build in the same folder differs'
    assert tree_hash(b) == h1, 'build in another folder differs'


# ---------------------------------------------------------------- RC-01, RC-03: one YAML loader and the excluded photo everywhere
def test_post_build_scan_catches_excluded_photo():
    root = make_fixture('scan')
    tpl = root / '_system' / 'templates' / 'AGENTS.md'
    w(tpl, tpl.read_text(encoding='utf-8') + '\nSee img_4692.heic.\n')
    code, out = build(root)
    assert code != 0 and 'ERROR: 60-outputs/agent-pack/AGENTS.md names an excluded photo' in out and 'Traceback' not in out, out
    w(tpl, tpl.read_text(encoding='utf-8').replace('img_4692', 'IMG_46920'))
    code, out = build(root)
    assert code == 0, 'IMG_46920 is a different photo:\n' + out


def test_excluded_lists_match():
    get = lambda f: re.search(r"^EXCLUDED = (\(.*?\))", (REPO / f).read_text(encoding='utf-8'), re.M)[1]
    assert get('_system/build_kb.py') == get('_system/site/build_site.py') and 'IMG_4692' in get('_system/build_kb.py')


def test_unreadable_file_is_reported_alone():
    root = make_fixture('dup-check', [('20-claims/sessions.yaml', 'theme: Crawling\n', 'theme: Crawling\n    theme: Again\n')])
    code, out = build(root, '--check')
    errs = [l for l in out.splitlines() if l.startswith('ERROR')]
    assert code != 0 and errs == ['ERROR: 20-claims/sessions.yaml: line 6: key "theme" appears twice in one entry (first on line 5); keep one'], out
    assert not (root / '60-outputs' / 'agent-pack').exists()


# ---------------------------------------------------------------- Day 2 review: shared wording, S00 labels, uncovered sessions, long paths
def test_kb_wording_s00_labels_and_uncovered_sessions():
    root = make_fixture('wording', [
        ('20-claims/sessions.yaml', '      - {id: D1-S00,', '      - {id: D1-S04, time: "12:30", title: "Lunch", speaker: "", coverage: none, kind: break}\n      - {id: D1-S00,'),
        ('20-claims/sessions.yaml', 'coverage: [transcript, slides]}\n', 'coverage: [transcript, slides]}\n      - {id: D2-S00, time: "", title: "Day 2, session not recorded", speaker: "", coverage: none}\n')])
    code, out = build(root)
    assert code == 0, out
    txt = shared_text(root)
    twice = [rel for rel, t in txt.items() if re.search(r'Day (\d+), Day \1, session not recorded', t)]
    assert not twice, f'S00 shows its day twice in {twice}'
    assert '(annotates Day 1, session not recorded)' in txt['50-maps/across-days.md']
    mx, vr = txt['50-maps/mention-matrix.md'], txt['50-maps/verification-report.md']
    assert 'Google raised' not in mx and 'Google kept returning' not in mx and 'by Google or a community speaker' in mx, 'the matrix credits every slide and stage claim to Google'
    assert "Google's own figures" not in vr and 'by Google or a community speaker' in vr
    assert not [rel for rel, t in txt.items() if 'What Google showed and said' in t], 'topic pages credit community talks to Google'
    nocov = txt['60-outputs/agent-pack/INDEX.md'].split('## Sessions with no coverage')[1].split('\n## ')[0]
    assert '`D1-S03`' in nocov and '`D1-S04`' not in nocov and '`D2-S00`' not in nocov, 'breaks and S00 listed as uncovered sessions:\n' + nocov


def test_long_output_paths_stop_the_build_before_deleting():  # a Windows path of 260+ characters failed halfway through fresh()
    bk = load_module(REPO / '_system' / 'build_kb.py', 'bk_long')
    root = make_fixture('longpath')
    kb, E, _ = bk.load(root)
    assert not E and not bk.long_paths(root, kb), 'a short root has no long paths'
    deep = bk.long_paths(Path('C:/') / ('x' * 230), kb)
    assert deep and all(len(p) >= 260 for p in deep) and any('agent-pack' in p for p in deep), deep[:2]
    if sys.platform != 'win32': return
    assert build(root)[0] == 0
    before = tree_hash(root)
    bk.long_paths, bk.windows_long_paths_enabled = (lambda r, k, limit=260: ['C:/' + 'x' * 300]), (lambda: False)
    out = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')  # main() reconfigures stdout, which a StringIO cannot do
    try:
        with contextlib.redirect_stdout(out): bk.main(['--root', str(root)])
        raise AssertionError('the build went on with a 300-character output path')
    except SystemExit as x:
        out.flush()
        printed = out.buffer.getvalue().decode('utf-8')
        assert 'Nothing was written' in str(x) and 'ERROR: 1 output path(s) would reach the Windows limit' in printed, (x, printed)
    assert tree_hash(root) == before, 'outputs were deleted or written before the path check'


# ---------------------------------------------------------------- Day 2 review: PDF builders (Art Deco palette, agenda coverage, source dates)
def pdf_module(name):
    sys.path.insert(0, str(REPO / '_system' / 'pdf'))
    try:
        return importlib.import_module(name)
    finally:
        sys.path.remove(str(REPO / '_system' / 'pdf'))


def test_deco_recolours_every_template_colour():
    try:
        bd = pdf_module('build_deco')
    except ImportError as x:
        print(f'    skipped ({x})'); return
    for f in sorted((REPO / '_system' / 'pdf').glob('day*.template.html')):
        assert not bd.unmapped_colours(f.read_text(encoding='utf-8')), (f.name, bd.unmapped_colours(f.read_text(encoding='utf-8')))
    leaked = ('<svg viewBox="0 0 9 9"><path d="M0 0" stroke="#bcd0ff"/><rect stroke="#b86e00"/><path fill="#c8372d"/><circle fill="#c8372d"/>'
              '<path fill="#0b8a5f"/><path fill="#b86e00"/></svg><div style="color:#c8372d">x</div>')
    assert not bd.unmapped_colours(leaked), bd.unmapped_colours(leaked)
    out = bd.recolor_inline(bd.recolor_svgs(leaked)).lower()
    assert not [c for c in ('#bcd0ff', '#b86e00', '#c8372d', '#0b8a5f') if c in out], 'modern colours left in the Art Deco edition: ' + out
    bad = '<svg viewBox="0 0 9 9"><rect fill="#123456"/><ellipse fill="#2457e6"/></svg><b style="color:#abcdef">x</b>'
    assert bd.unmapped_colours(bad) == ['<ellipse fill="#2457e6">', '<rect fill="#123456">', 'style="color:#abcdef"'], bd.unmapped_colours(bad)


def test_pdf_agenda_coverage_and_source_dates_never_break_inside():
    try:
        mp = pdf_module('make_pdf')
    except ImportError as x:
        print(f'    skipped ({x})'); return
    nb = '\u00a0'
    data = {'sessions.json': {'days': [{'day': 2, 'sessions': [
                {'id': 'D2-S01', 'time': '10:00', 'title': 'One', 'speakers': ['A'], 'role': None, 'kind': 'talk', 'coverage': ['slides']},
                {'id': 'D2-S02', 'time': '11:00', 'title': 'Two', 'speakers': ['B'], 'role': None, 'kind': 'talk', 'coverage': ['transcript', 'one-slide', 'video']}]}]},
            'sources.json': {'blog': {'title': 'A post (8 May 2018)', 'url': 'https://example.com/a', 'publisher': 'Search Central blog (1 September 2006)',
                                      'kind': 'google', 'checked': '2026-10-01'}}}
    old = mp.pack
    mp.pack = lambda name: data[name]
    try:
        rows = mp.agenda(2).splitlines()
        rows_src, _ = mp.sources(2, {'D2-C001': {'day': 2, 'sources': [{'key': 'blog'}]}}, [])
    finally:
        mp.pack = old
    cov = [re.search(r'<span class="cov">(.*?)</span></div>', r)[1] for r in rows]
    assert cov[0] == f'<b>Slides</b>{nb}captured', cov[0]
    assert cov[1] == f'<b>Transcript</b> · <b>One{nb}slide</b> · <b>Video</b>', cov[1]
    assert all(' ' not in item for c in cov for item in c.split(' · ')), cov
    assert f'(8{nb}May{nb}2018)' in rows_src and f'(1{nb}September{nb}2006)' in rows_src, rows_src


def ingest(root, *args):
    return run_py(root, '_system/tools/ingest.py', *args, '--root', str(root))


def test_ingest_and_eval_use_the_strict_loader():
    root = make_fixture('ing-yaml', [('20-claims/sessions.yaml', 'theme: Crawling\n', 'theme: Crawling\n    theme: Again\n')], tools=True)
    src = TMP / 'ing-yaml-src'
    w(src / 'note.txt', 'x')
    code, out = ingest(root, str(src), '--day', '1')
    assert code == 0 and 'sessions.yaml cannot be read' in out and 'key "theme" appears twice' in out and 'Traceback' not in out, out
    q = root / '_system' / 'eval' / 'questions.yaml'
    w(q, '- {id: q01, q: "What?", q: "Again?", claims: []}\n')
    code, out = run_py(root, '_system/eval/eval_check.py', '--template')
    assert code != 0 and 'key "q" appears twice' in out and 'Traceback' not in out, out
    w(q, '- {id: q01, q: "What?", claims: []}\n')
    code, out = run_py(root, '_system/eval/eval_check.py', '--template')
    assert code == 0 and 'q01' in out, out


def test_eval_accepts_equivalent_claims():  # a claims item 'A|B' is one point, cited when the answer cites A or B
    root = make_fixture('eval-alt', tools=True)
    q, ans = root / '_system' / 'eval' / 'questions.yaml', root / 'answers.yaml'
    w(q, '- {id: q01, q: "What is crawl budget?", expect: ["Rate plus demand."], claims: [D1-C001|D2-C001, D1-C003]}\n'
         '- {id: q02, q: "Canonical?", claims: [D1-C003 | D1-C004]}\n')
    code, out = build(root, '--check')
    assert code == 0 and 'eval' not in out, out
    for bad, msg in (('D1-C001|D2-C009', 'eval q01: mentions D2-C009, which does not exist'), ('D1-C001|D1-C007', 'eval q01: mentions D1-C007, which is private')):
        w(q, f'- {{id: q01, q: "What?", claims: [{bad}]}}\n')
        code, out = build(root, '--check')
        assert code != 0 and msg in out, (bad, out)
    w(q, '- {id: q01, q: "What is crawl budget?", expect: ["Rate plus demand."], claims: [D1-C001|D2-C001, D1-C003]}\n'
         '- {id: q02, q: "Canonical?", claims: [D1-C003 | D1-C004]}\n')
    code, out = run_py(root, '_system/eval/eval_check.py', '--template')
    assert code == 0 and 'q01: ""' in out and 'q02: ""' in out and 'any one of them' in out, out
    w(ans, 'q01: "Rate limit plus demand [D2-C001]; one URL is kept [D1-C003]."\nq02: "A press article [D1-C005]."\n')
    code, out = run_py(root, '_system/eval/eval_check.py', str(ans))
    assert code == 0 and 'Citation recall: **2/2** points (all cited)' in out, out
    assert 'Points with equivalent IDs: D1-C001 or D2-C001 (cited: D2-C001)' in out, out
    assert 'Citation recall: **0/1** points (missing: D1-C003 or D1-C004)' in out, out
    assert 'mean citation recall 0.50; 1/2 complete' in out and 'every expected point cited' in out, out
    for bad, msg in (('D1-C001|D1-C003, D1-C003', 'D1-C003 is listed twice in claims'), ('D1-C001 or D2-C001', "claims item 'D1-C001 or D2-C001' must be a claim ID"),
                     ('D1-C001|', "claims item 'D1-C001|' must be a claim ID")):
        w(q, f'- {{id: q01, q: "What?", claims: [{bad}]}}\n')
        code, out = run_py(root, '_system/eval/eval_check.py', '--template')
        assert code != 0 and msg in out and 'Traceback' not in out, (bad, out)


def test_ingest_skips_excluded_photo():
    root = make_fixture('ing-excl', tools=True)
    src = TMP / 'ing-excl-src'
    w(src / 'IMG_4692.HEIC', 'badge')
    w(src / 'talk.txt', 'transcript')
    w(root / '10-sources' / 'day1' / 'slides-jpg' / 'IMG_4692.jpg', 'old preview')
    code, out = ingest(root, str(src), '--day', '1')
    assert code == 0, out
    assert (root / '00-raw' / 'day1' / 'slides' / 'IMG_4692.HEIC').exists() and (root / '00-raw' / 'day1' / 'transcripts' / 'talk.txt').exists()
    idx = (root / '10-sources' / 'day1' / 'media.yaml').read_text(encoding='utf-8')
    assert 'IMG_4692' not in idx and 'transcripts/talk.txt' in idx, idx
    assert 'slides/IMG_4692.HEIC is an excluded photo' in out and 'Delete the old preview 10-sources/day1/slides-jpg/IMG_4692.jpg' in out, out


def test_ingest_name_clash_and_twins():
    root = make_fixture('ing-clash', tools=True)
    a, b = TMP / 'ing-clash-a', TMP / 'ing-clash-b'
    w(a / 'x.txt', 'one'); w(b / 'x.txt', 'two'); w(a / 'y.txt', 'same'); w(b / 'y.txt', 'same')
    code, out = ingest(root, str(a), str(b), '--day', '1')
    assert code == 1 and 'NAME CLASH (not copied):' in out and 'same name, both new' in out and '2 file(s) copied, 1 skipped' in out, out
    w(b / 'x.txt', 'three')
    code, out = ingest(root, str(a), str(b), '--day', '1')
    assert code == 1 and 'differs from  00-raw/day1/transcripts/x.txt' in out and '0 file(s) copied, 3 skipped' in out, out


# ---------------------------------------------------------------- RC-02, RC-05: ingest robustness and ingest.bat
def lock(path):  # open with no sharing, as a program holding the file would (Windows)
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.CreateFileW.restype = ctypes.c_void_p
    k32.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    h = k32.CreateFileW(str(path), 0x80000000, 0, None, 3, 0x80, None)
    assert h not in (None, ctypes.c_void_p(-1).value), 'could not lock the test file'
    return lambda: k32.CloseHandle(ctypes.c_void_p(h))


def test_ingest_survives_a_locked_file():
    if os.name != 'nt': print('    skipped (Windows only)'); return
    root = make_fixture('ing-lock', tools=True)
    src = TMP / 'ing-lock-src'
    for n in ('t10.txt', 't11.txt', 't12.txt'): w(src / n, n * 1000)
    unlock = lock(src / 't11.txt')
    try:
        code, out = ingest(root, str(src), '--day', '1')
    finally:
        unlock()
    raw = root / '00-raw' / 'day1' / 'transcripts'
    assert code == 1 and 'COPY FAILED (not copied):' in out and 't11.txt' in out and 'Traceback' not in out, out
    assert (raw / 't10.txt').exists() and (raw / 't12.txt').exists() and not (raw / 't11.txt').exists(), out
    assert not list(root.rglob('*.part')), 'a .part file was left behind'
    idx = (root / '10-sources' / 'day1' / 'media.yaml').read_text(encoding='utf-8')
    assert 'transcripts/t10.txt' in idx and 'transcripts/t12.txt' in idx, 'the index was not written after a failed copy'
    code, out = ingest(root, str(src), '--day', '1')
    assert code == 0 and (raw / 't11.txt').exists() and '1 file(s) copied, 2 skipped' in out, out


def test_ingest_stops_cleanly_and_ingest_bat_says_so():
    root = make_fixture('ing-stop', tools=True)
    src = TMP / 'ing-stop-src'
    w(src / 't30.txt', 'x')
    (root / '10-sources' / 'day1' / 'media.yaml').mkdir(parents=True)  # the index cannot be read or written
    code, out = ingest(root, str(src), '--day', '1')
    assert code == 2 and 'STOPPED by an unexpected error' in out and 'Traceback' not in out, out
    if os.name != 'nt': print('    ingest.bat part skipped (Windows only)'); return
    w(src / 't31.txt', 'y')
    code, out = run_bat(root, [str(src)], '1\nY\n')
    assert code == 2 and 'The import STOPPED part way' in out and 'Done.' not in out and 'Finished' not in out, out


def run_bat(root, args, answers):
    ans = TMP / 'answers.txt'
    ans.write_bytes(answers.replace('\n', '\r\n').encode('utf-8'))  # set /p reads a redirected file line by line only with CRLF
    line = f'cmd /d /c ""{root / "ingest.bat"}"' + ''.join(f' "{a}"' for a in args) + '"'
    with open(ans, 'rb') as fin:
        r = subprocess.run(line, stdin=fin, capture_output=True, env=dict(os.environ, KB_NOPAUSE='1', KB_PYTHON=sys.executable, PYTHONIOENCODING='utf-8'))
    return r.returncode, (r.stdout + r.stderr).decode('utf-8', 'replace')


def test_ingest_bat_accepts_a_trailing_backslash():
    if os.name != 'nt': print('    skipped (Windows only)'); return
    root = make_fixture('ing-bs', tools=True)
    src = TMP / 'ing-bs-src' / 'drop zone'
    w(src / 't40.txt', 'x')
    code, out = run_bat(root, [str(src) + '\\'], '1\nN\n')  # dragged folder or drive root, e.g. E:\
    assert code == 0 and 'would copy  t40.txt' in out and 'arguments are required' not in out and 'Nothing was copied.' in out, out
    code, out = run_bat(root, [], f'"{src}\\"\n1\nN\n')  # double-click, then a pasted path ending in a backslash
    assert code == 0 and 'would copy  t40.txt' in out and 'arguments are required' not in out, out
    code, out = run_bat(root, [str(src)], '1\nY\n')
    assert code == 0 and 'Done. The files are in 00-raw' in out and (root / '00-raw' / 'day1' / 'transcripts' / 't40.txt').exists(), out


# ---------------------------------------------------------------- RC-13: commit privacy guard
def test_check_commit_flags_decks_sheets_and_pdfs():
    cc = load_module(REPO / '_system' / 'tools' / 'check_commit.py', 'cc')
    flagged = ['60-outputs/Google-crawling-deck.pptx', '20-claims/day2-slides.pdf', '_system/keynote.key', '60-outputs/attendees.xlsx',
               '60-outputs/content/Day 2 transcript.pdf', '60-outputs/content/day2_transcript.md', '30-topics/notes-Transcription.md',
               '60-outputs/site/attendees.csv', '60-outputs/pdf/slides.odp', '60-outputs/content/list.ods', '60-outputs/dev/attendees.csv',
               '60-outputs/site/downloads/attendees.csv', '25-kits/IMG_4692.md']
    clean = ['60-outputs/pdf/day1-field-guide-modern.pdf', '60-outputs/site/downloads/day1-field-guide-modern.pdf', '50-maps/mention-matrix.csv',
             '60-outputs/site/index.html', '30-topics/crawling/robots-txt.md', '_system/tools/check_commit.py', '25-kits/content.yaml',
             '25-kits/snippets/robots-txt.md', '60-outputs/dev/requirements.csv', '60-outputs/site/downloads/requirements.csv']
    bad = [p for p in flagged if not cc.reasons(TMP, p)] + [(p, cc.reasons(TMP, p)) for p in clean if cc.reasons(TMP, p)]
    assert not bad, bad


# ---------------------------------------------------------------- web edition: RC-09, RC-11 and the lead decisions
SITE_EDITS = [
    ('20-claims/sessions.yaml', 'title: "Lightning", speaker: ""', 'title: "Lightning", speaker: "مریم رضایی"'),
    ('20-claims/sessions.yaml', '      - {id: D1-S00,', '      - {id: D1-S04, time: "12:30", title: "Posters", speaker: "Łukasz Šimek", coverage: one-slide, kind: poster}\n      - {id: D1-S00,'),
    ('20-claims/day1.yaml', '- {id: D1-C003,', '- {id: D1-C009, s: D1-S02, label: stage, who: audience, ev: "T:t02:5", ver: n/a, topics: [crawl-budget],\n'
     '   text: "An audience member asked whether large sites need to worry about crawl budget."}\n- {id: D1-C003,'),
    ('20-claims/day1.yaml', 'rel: [{type: answers, to: D1-C002}]', 'rel: [{type: answers, to: D1-C002}, {type: answers, to: D1-C009}]'),
    ('20-claims/day1.yaml', 'private: true}\n', 'private: true}\n'
     '- {id: D1-C008, s: D1-S04, label: slide, ev: notes, ver: n/a, topics: [crawl-budget], text: "Łukasz Šimek greeted the room with Dzień dobry and a poster titled سئو."}\n'
     '- {id: D1-C010, s: D1-S02, label: slide, ev: IMG_0005, ver: n/a, topics: [crawl-budget], text: "A slide answered that small sites rarely need to worry.", rel: [{type: answers, to: D1-C002}]}\n'
     '- {id: D1-C011, s: D1-S00, label: stage, who: Gary Illyes, ev: notes, ver: undocumented, topics: [canonical], text: "Gary Illyes said Google picks one URL to keep."}\n')]
_SITE = {}


def site_fixture():
    if 'root' not in _SITE:
        root = make_fixture('site', SITE_EDITS, site=True)
        w(root / '60-outputs' / 'pdf' / 'day1-field-guide-modern.pdf', '%PDF-1.4\n%fixture\n')
        code, out = build(root)
        assert code == 0, out
        code, out = build_site(root)
        assert code == 0, out
        _SITE['root'] = root
    return _SITE['root']


def test_site_answer_shown_once_under_earliest_question():  # RC-11
    root = site_fixture()
    h = (root / '60-outputs' / 'site' / 'sessions' / 'D1-S02.html').read_text(encoding='utf-8')
    assert h.count('id="D1-C003"') == 1 and h.count('id="D1-C010"') == 1, 'an answer is rendered more than once'
    assert 'aria-labelledby="g-slide"' not in h, 'the slide answer was also rendered in its own group'
    assert 'id="g-stage">Said on stage <span class="count">4</span>' in h, 'the stage group should count its 4 cards'
    q1, a1, a2, q2 = (h.index(f'id="{x}"') for x in ('D1-C002', 'D1-C003', 'D1-C010', 'D1-C009'))
    assert q1 < a1 < a2 < q2, 'answers are not under the earliest question'
    second = re.search(r'<article[^>]*id="D1-C009".*?</article>', h, re.S)[0]
    assert 'Answered by</span> <a class="cid" href="../claims.html#D1-C003">' in second, 'the second question lost its link to the answer'
    md = next((root / '40-sessions' / 'day1').glob('D1-S02-*.md')).read_text(encoding='utf-8')
    assert md.count('Gary Illyes answered') == 1


def test_site_s00_speaker_poster_and_downloads():  # lead decisions
    root = site_fixture()
    P, O = root / '60-outputs' / 'agent-pack', root / '60-outputs' / 'site'
    rows = {r['id']: r for r in map(json.loads, (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines())}
    assert rows['D1-C011']['who'] == 'Gary Illyes' and rows['D1-C011']['speaker'] == 'Gary Illyes'
    tj = json.loads((P / 'topics.json').read_text(encoding='utf-8'))
    canon = [t for a in tj['areas'] for t in a['topics'] if t['id'] == 'canonical'][0]
    assert canon['event_days'] == [1, 2] and canon['event_sessions'] == ['D2-S01'], canon
    tp = (O / 'topics' / 'canonical.html').read_text(encoding='utf-8')
    assert 'raised in 1 session · said or shown on Day 1 and Day 2' in tp, 'topic facts do not follow event_days/event_sessions'
    assert '<span class="k">Speaker</span> Gary Illyes' in re.search(r'<article[^>]*id="D1-C011".*?</article>', (O / 'claims.html').read_text(encoding='utf-8'), re.S)[0]
    sj = json.loads((P / 'sessions.json').read_text(encoding='utf-8'))
    assert [s['kind'] for s in sj['days'][0]['sessions'] if s['id'] == 'D1-S04'] == ['poster']
    assert 'kind-poster">Poster</span>' in (O / 'days' / 'day-1.html').read_text(encoding='utf-8') and (O / 'sessions' / 'D1-S04.html').exists()
    ix = (O / 'index.html').read_text(encoding='utf-8')
    assert 'href="downloads/day1-field-guide-modern.pdf"' in ix and '../pdf/' not in ix
    assert (O / 'downloads' / 'day1-field-guide-modern.pdf').read_bytes() == (root / '60-outputs' / 'pdf' / 'day1-field-guide-modern.pdf').read_bytes()


# ---------------------------------------------------------------- v2.5.0: only Deep Dive is rebuilt; the classic editions are frozen and logged
def test_rebuild_bat_builds_only_the_deep_dive_edition():
    raw = (REPO / 'rebuild.bat').read_bytes()
    assert b'\n' not in raw.replace(b'\r\n', b''), 'rebuild.bat must keep CRLF line endings'
    t = raw.decode('ascii')
    calls = re.findall(r'^call :pdfstyle %~1 (\w+)\r$', t, re.M)
    assert calls == ['ocean'], f'rebuild.bat must build the Deep Dive edition only, it calls {calls}'
    for want in ('make_pdf.py day2 deco', 'make_pdf.py day2 modern', 'classic-editions-log.md', 'v2.4.0'):
        assert want in t, f'rebuild.bat does not document {want!r}'


def test_site_labels_the_frozen_classic_editions_and_lists_their_log():
    root = make_fixture('site-classic', site=True)
    P = root / '60-outputs' / 'pdf'
    for ed in ('deep-dive', 'art-deco', 'modern'): w(P / f'day1-field-guide-{ed}.pdf', f'%PDF-1.4\n%{ed}\n')
    for step in (build, build_site):
        code, out = step(root)
        assert code == 0, out
    O = root / '60-outputs' / 'site'
    ix = (O / 'index.html').read_text(encoding='utf-8')
    names = re.findall(r'<span class="dl-t">(Day 1 field guide[^<]*)</span>', ix)
    assert names == ['Day 1 field guide · Deep Dive', 'Day 1 field guide · Art Deco (classic edition, content as of v2.4.0)',
                     'Day 1 field guide · Modern (classic edition, content as of v2.4.0)'], names
    assert 'classic-editions-log.md' not in ix and not (O / 'downloads' / 'classic-editions-log.md').exists(), 'no log, nothing to list'
    assert 'what they lack' not in (root / '60-outputs' / 'README.md').read_text(encoding='utf-8'), 'the outputs README links a log that does not exist'
    w(P / 'classic-editions-log.md', '# Classic editions log\n\n<p align="center"><img src="../../_system/brand/divider.svg" width="600" alt="Section divider"></p>\n\n'
      '## <img src="../../_system/brand/icons/fish.svg" width="24" height="24" alt=""> Day 1\n\n'
      'See the [field guides](README.md), <a href="../dev/README.md">the kit</a> and [Google](https://developers.google.com/search).\n')
    for step in (build, build_site):
        code, out = step(root)
        assert code == 0, out
    ix = (O / 'index.html').read_text(encoding='utf-8')
    assert 'href="downloads/classic-editions-log.md"' in ix and '../pdf/' not in ix
    got = (O / 'downloads' / 'classic-editions-log.md').read_text(encoding='utf-8')  # a plain copy: no images, no relative links
    assert got == '# Classic editions log\n\n## Day 1\n\nSee the field guides, the kit and [Google](https://developers.google.com/search).\n', got
    assert '([what they lack](pdf/classic-editions-log.md))' in (root / '60-outputs' / 'README.md').read_text(encoding='utf-8')
    assert not readme_problems(root), readme_problems(root)


def test_site_topics_raised_wording_and_s00_labels():  # Day 2 review: OSM-02, OSM-03, OSM-07
    O = site_fixture() / '60-outputs' / 'site'
    day1 = (O / 'days' / 'day-1.html').read_text(encoding='utf-8')
    box = re.search(r'Topics raised most</p><ul class="toplist n">(.*?)</ul>', day1, re.S)[1]
    # slide and stage claims of Day 1 outside S00: crawl-budget in D1-S01, S02 and S04, six claims; canonical only in S00 and a press note
    assert 'crawl-budget.html">Crawl budget</a> <span class="n">3 sessions · 6 claims</span>' in box and 'canonical.html' not in box, box
    pages = {p.name: p.read_text(encoding='utf-8') for p in O.rglob('*.html')}
    twice = [n for n, t in pages.items() if re.search(r'Day (\d+) · (<a [^>]*>)?Day \1, session not recorded', t)]
    assert not twice, f'S00 shows its day twice on {twice}'
    assert 'Day 1 · session not recorded</a>' in pages['canonical.html'] and '">session not recorded</a>' in pages['across-days.html']
    google = [(n, s) for n, t in pages.items() for s in ('Shown by Google on a slide', 'said or shown by Google at the event', 'What Google said or showed',
                                                         'Topics Google returned to', 'technical claim Google made') if s in t]
    assert not google, f'community speakers credited to Google: {google}'


def tamper(name, rel, fn):
    root = TMP / name
    if root.exists(): shutil.rmtree(root)
    shutil.copytree(site_fixture(), root)
    p = root / '60-outputs' / 'agent-pack' / rel
    p.write_text(fn(p.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
    return build_site(root)


def test_site_is_strict_about_counts_dates_and_speakers():
    def topic(fn):
        def go(txt):
            d = json.loads(txt)
            fn([t for a in d['areas'] for t in a['topics'] if t['id'] == 'canonical'][0])
            return json.dumps(d)
        return go
    cases = [('t-days', 'topics.json', topic(lambda t: t.update(event_days=[2])), 'event_days must list the days of its slide and stage claims, S00 included'),
             ('t-days-extra', 'topics.json', topic(lambda t: t.update(event_days=[1, 2, 3])), 'event_days must list'),
             ('t-sess', 'topics.json', topic(lambda t: t.update(event_sessions=['D1-S00', 'D2-S01'])), 'event_sessions must list the sessions of its slide and stage claims, without S00'),
             ('t-date', 'sources.json', lambda x: x.replace('"checked": "2026-10-01"', '"checked": "2026-09-31"', 1), 'checked must be a real date'),
             ('t-day', 'sessions.json', lambda x: x.replace('"date": "2026-09-30"', '"date": "2026-02-30"', 1), 'bad date 2026-02-30'),
             ('t-who', 'claims.jsonl', lambda x: x.replace('"who": "Martin Splitt"', '"who": "Somebody Else"', 1), 'who "Somebody Else" is not a speaker of D2-S01'),
             ('t-speaker', 'claims.jsonl', lambda x: x.replace('"speaker": "Gary Illyes", "who": "Gary Illyes"', '"speaker": "Google", "who": "Gary Illyes"', 1), 'speaker must be who'),
             ('t-kind', 'sessions.json', lambda x: x.replace('"kind": "poster"', '"kind": "keynote"', 1), 'unknown kind keynote'),
             ('t-kit-claim', 'content-library.json', lambda x: x.replace('"id": "D1-C001"', '"id": "D1-C007"', 1), 'claim D1-C007 is not a public claim of claims.jsonl'),
             ('t-kit-text', 'dev-requirements.json', lambda x: x.replace('"text": "Crawl budget is crawl rate limit', '"text": "Edited: crawl budget is crawl rate limit', 1), 'claim D1-C001 differs from claims.jsonl'),
             ('t-kit-level', 'dev-requirements.json', lambda x: x.replace('"level": "MUST"', '"level": "HIGH"', 1), 'unknown level HIGH')]
    bad = []
    for name, rel, fn, expect in cases:
        code, out = tamper('site-' + name, rel, fn)
        if code == 0 or expect not in out or 'Traceback' in out: bad.append(f'{name}: {out.strip()[-300:]}')
    assert not bad, '\n  '.join([''] + bad)


def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    return sync_playwright


def test_site_search_is_unicode_aware():  # RC-09
    pw_ = browser()
    if not pw_: print('    skipped (Playwright not installed)'); return
    root = site_fixture()
    url = (root / '60-outputs' / 'site' / 'search.html').as_uri()
    with pw_() as pw:
        b = pw.chromium.launch()
        try:
            pg = b.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            pg.goto(url)
            def q(text):
                pg.fill('#q', text)
                pg.press('#q', 'Enter')
                return pg.evaluate("() => ({status: document.getElementById('search-status').textContent, n: document.querySelectorAll('#results li').length,"
                                   " marks: [...document.querySelectorAll('#results mark')].map(m => m.textContent)})")
            res = {x: q(x) for x in ('Lukasz', 'Łukasz', 'ŁUKASZ šimek', 'مریم', 'سئو', 'dzien', 'Dzień', 'poster', '???', '')}
            q('Łukasz')  # accented names are drawn with the latin-ext subset of the same typeface
            ext = pg.evaluate("async () => { await document.fonts.ready; return [...document.fonts].filter(f => f.status === 'loaded' &&"
                              " /U\\+100-2BA/i.test(f.unicodeRange)).map(f => f.family) }")
        finally:
            b.close()
    bad = []
    for x in ('Lukasz', 'Łukasz', 'ŁUKASZ šimek'):
        if not res[x]['n'] or 'Łukasz' not in res[x]['marks']: bad.append((x, res[x]))
    if 'Šimek' not in res['ŁUKASZ šimek']['marks']: bad.append(('Šimek mark', res['ŁUKASZ šimek']))
    if not res['مریم']['n'] or '1 session' not in res['مریم']['status']: bad.append(('مریم', res['مریم']))
    if not res['سئو']['n'] or 'سئو' not in res['سئو']['marks']: bad.append(('سئو', res['سئو']))
    for x in ('dzien', 'Dzień'):
        if 'Dzień' not in res[x]['marks']: bad.append((x, res[x]))
    if 'Nothing to search for in “???”' not in res['???']['status'] or res['???']['n']: bad.append(('???', res['???']))
    if 'Type a word' not in res['']['status']: bad.append(('empty', res['']))
    if not any(f in ('Jost', 'Figtree') for f in ext): bad.append(('latin-ext font not loaded', ext))  # Jost in Art Deco, Figtree in Deep Dive
    assert not bad and not errs, (bad, errs)


def crawl_site(site):
    """Open every page of a built site; return the console errors, page errors and failed local requests."""
    pw_ = browser()
    if not pw_: return None
    errs = []
    with pw_() as pw:
        b = pw.chromium.launch()
        try:
            pg = b.new_page()
            pg.on('pageerror', lambda e: errs.append(f'{pg.url}: {e}'))
            pg.on('console', lambda m: errs.append(f'{pg.url}: {m.text}') if m.type == 'error' else None)
            pg.on('requestfailed', lambda r: errs.append(f'{pg.url}: failed {r.url}'))
            pages = sorted(site.rglob('*.html'))
            # 404.html (published community edition) resolves its files from site_url, its <base>: serve them from this build
            nf = site / '404.html'
            m = nf.exists() and re.search(r'<base href="([^"]+)">', nf.read_text(encoding='utf-8'))
            if m:
                su = html.unescape(m[1])
                pg.route(su + '**', lambda r: r.fulfill(path=str(site / re.split(r'[?#]', r.request.url[len(su):])[0])))
            for p in pages: pg.goto(p.as_uri())
            pg.goto((site / 'search.html').as_uri())
            pg.fill('#q', 'robots')
            pg.press('#q', 'Enter')
            n = pg.evaluate("() => document.querySelectorAll('#results li').length")
            if not n: errs.append('search for robots found nothing')
        finally:
            b.close()
    return len(pages), errs


def test_real_data():
    import jsonschema
    root = TMP / 'real'
    if root.exists(): shutil.rmtree(root)
    copy_real(root, ('20-claims', '25-kits', '_system/templates', '_system/eval'), ('CHANGELOG.md',) + CODE)
    code, out = build(root)
    assert code == 0, 'the real data does not build:\n' + out
    print('    ' + out.strip().splitlines()[-1] if out.strip() else '')
    h1 = tree_hash(root)
    assert build(root)[0] == 0 and tree_hash(root) == h1, 'two builds of the real data differ'
    P = root / '60-outputs' / 'agent-pack'
    v = jsonschema.Draft202012Validator(json.loads((P / 'claims.schema.json').read_text(encoding='utf-8')))
    rows = [json.loads(l) for l in (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines()]
    bad = [(r['id'], e.message) for r in rows for e in v.iter_errors(r)]
    assert not bad, bad[:5]
    private = [c['id'] for f in sorted((root / '20-claims').glob('day*.yaml')) for c in yaml.safe_load(f.read_text(encoding='utf-8')) or [] if c.get('private')]
    for rel, txt in shared_text(root).items():
        for cid in private: assert cid not in txt, f'private {cid} in {rel}'
    mindmap_data(root)
    print('    browser check:', check_mindmap_browser(root / '50-maps' / 'mindmap.html'))
    assert not (P / 'eval-questions.yaml').exists()
    assert not build(root, '--check')[0] and not raw_html_any(root), raw_html_any(root)[:3]


def raw_html_any(root):
    return [(rel, x) for rel, txt in shared_text(root).items() if rel.endswith('.md') for x in raw_html(txt)]


def test_real_site():  # the web edition of the real data builds and loads with no console error
    root = TMP / 'real-site'
    if root.exists(): shutil.rmtree(root)
    copy_real(root, ('20-claims', '25-kits', '_system/templates', '_system/eval', '_system/site'),
              ['CHANGELOG.md', *CODE] + [p.relative_to(REPO).as_posix() for p in (REPO / '60-outputs' / 'pdf').glob('*.pdf')])
    copy_site_extras(root)
    code, out = build(root)
    assert code == 0, out
    code, out = build_site(root)
    assert code == 0, out
    print('    ' + out.strip().splitlines()[-1])
    site = root / '60-outputs' / 'site'
    for p in (REPO / '60-outputs' / 'pdf').glob('*.pdf'): assert (site / 'downloads' / p.name).exists(), p.name
    # empty states carry the diver bot (Deep Dive shows it, Art Deco hides the box)
    for f in site.glob('days/*.html'):
        h = f.read_text(encoding='utf-8')
        if 'Not yet available</p><p>' in h: assert '<div class="callout empty-note" data-pose="wave"><span class="bot-art" aria-hidden="true"></span>' in h, f.name
    for f in site.glob('sessions/*.html'):
        h = f.read_text(encoding='utf-8')
        if 'No claims were captured' in h: assert 'class="empty-note" data-pose="read"' in h, f.name
    deep_dive_only(root)
    res = crawl_site(site)
    if res is None: print('    browser check: skipped (Playwright not installed)'); return
    n, errs = res
    assert not errs, errs[:5]
    print(f'    browser check: {n} pages, 0 console errors')
    bad = header_overlap(site)
    assert not bad, f'the site title runs under the Menu button: {bad}'

SWITCH = re.compile(r'data-style-set|style-switch|class="ss-|id="styles"|data-s="|kb-style|data-deep=|data-deco=|link\[rel=icon\]')


def deep_dive_only(root):
    """The web edition, the mindmap and the Reef map show the build's style only (theme.yaml: deep-dive): no switch to another
    style in any page, nothing that reads or writes a style choice in the browser, and the tab icon of Deep Dive. site.js only
    clears a choice an older version kept."""
    site = root / '60-outputs' / 'site'
    want = load_module(root / '_system' / 'theme.py', 'theme_dd').default_style()
    assert want == 'deep-dive', f'the real data builds in {want}: _system/theme.yaml must say deep-dive'
    pages = sorted(site.rglob('*.html')) + [root / '50-maps' / 'mindmap.html', root / '50-maps' / 'graph.html']
    bad = []
    for p in pages:
        h, rel = p.read_text(encoding='utf-8'), p.relative_to(root).as_posix()
        icons = re.findall(r'<link rel="icon"[^>]*>', h)
        if SWITCH.search(h): bad.append(f'{rel}: {SWITCH.search(h)[0]}')
        if '<html lang="en" data-style="deep-dive">' not in h: bad.append(f'{rel}: not built in Deep Dive')
        if len(icons) != 1 or not ('icon-deep-dive.svg' in icons[0] or 'diverbot-head' in icons[0]): bad.append(f'{rel}: tab icon {icons[0][:90] if icons else None}')
    js, css = (site / 'assets' / 'site.js').read_text(encoding='utf-8'), (site / 'assets' / 'site.css').read_text(encoding='utf-8')
    if [l for l in js.splitlines() if 'kb-style' in l and 'removeItem(' not in l] or 'data-style-set' in js or "setAttribute('data-style'" in js: bad.append('site.js still reads or sets a style')
    if re.search(r'\.style-switch|\.ss-[a-z]', css): bad.append('site.css still styles the switch')
    assert not bad, '\n  '.join([''] + bad[:10])


def real_site_root():  # the web edition of the real data: test_real_site's build when it ran in this session, else a fresh one
    root = TMP / 'real-site'
    if (root / '60-outputs' / 'site' / 'search.html').exists(): return root
    if root.exists(): shutil.rmtree(root)
    copy_real(root, ('20-claims', '25-kits', '_system/templates', '_system/eval', '_system/site'), ['CHANGELOG.md', *CODE])
    copy_site_extras(root)
    code, out = build(root)
    assert code == 0, out
    code, out = build_site(root)
    assert code == 0, out
    return root


DD_ASSETS = ('fish-school', 'trail', 'fish-yellow', 'fish-red', 'fish-yellow-anim', 'fish-red-anim', 'fish-cross', 'seabed-anim', 'bot-hero-anim', 'bot-read-anim',
             'bot-point-anim', 'bot-wave-anim', 'bot-peek-anim', 'q-bubble', 'blow-bubble')
DD_HEAD = ('<span class="dd-rays" aria-hidden="true"></span><span class="dd-plankton" aria-hidden="true"><i></i><i></i></span>'
           '<span class="dd-crossing" aria-hidden="true"><i></i></span>')
DD_REEF = re.compile(r'<span class="dd-reef" aria-hidden="true"><i class="dd-fish dd-f-school" data-box="[\d. ]+"></i><i class="dd-trail"></i>'
                     r'<i class="dd-fish dd-f-yellow" data-box="[\d. ]+"></i><i class="dd-fish dd-f-red" data-box="[\d. ]+"></i></span><div class="wrap">')
# where a fish is drawn on screen: its data-box (in the reef's 300x150 units) scaled into the reef's rendered box, as the page's own hit test does
DD_FISH = """() => { const reef = document.querySelector('.page-head > .dd-reef'), r = reef.getBoundingClientRect(), s = Math.min(r.width / 300, r.height / 150);
  return Object.fromEntries([...reef.querySelectorAll('.dd-fish')].map(f => { const b = f.dataset.box.split(' ').map(Number);
    return [f.className.split('dd-f-')[1], [r.left + (r.width - 300 * s) / 2 + (b[0] + b[2] / 2) * s, r.top + (r.height - 150 * s) / 2 + (b[1] + b[3] / 2) * s]]; })); }"""


def dd_pages(site):  # the pages the motion tests open: home, a topic, about (the bot in the head), search (empty, results, nothing found), an empty state
    empty = next(f'sessions/{f.name}' for f in sorted(site.glob('sessions/*.html')) if 'empty-note" data-pose=' in f.read_text(encoding='utf-8'))
    return ['index.html', 'topics/robots-txt.html', 'about.html', 'search.html', 'search.html?q=robots', 'search.html?q=zzqx', empty]


def dd_url(site, page):
    path, _, q = page.partition('?')
    return (site / path).as_uri() + ('?' + q if q else '')


def test_deep_dive_motion_files_markup_and_reduced_motion():  # the Deep Dive motion: its art, its markup, and a still page for a reader who asks for reduced motion
    root = real_site_root()
    site = root / '60-outputs' / 'site'
    A = site / 'assets' / 'ocean'
    missing = [f'{n}{d}.svg' for n in DD_ASSETS for d in ('', '-dark') if not (A / f'{n}{d}.svg').exists()]
    assert not missing and (A / 'accent.svg').exists() and (A / 'seabed.svg').exists(), missing
    # the reef layers are the accent picture split in four, each in the accent's own 300x150 box; the moving art is the same art at rest
    for d in ('', '-dark'):
        acc = (A / f'accent{d}.svg').read_text(encoding='utf-8')
        body = lambda t: t[t.index('>', t.index('<svg')) + 1:t.rindex('</svg>')]
        assert body(acc) == ''.join(body((A / f'{n}{d}.svg').read_text(encoding='utf-8')) for n in ('fish-school', 'trail', 'fish-yellow', 'fish-red')), f'accent{d}.svg != its four layers'
        for n in ('fish-school', 'trail', 'fish-yellow', 'fish-red', 'fish-yellow-anim', 'fish-red-anim'): assert 'viewBox="0 0 300 150"' in (A / f'{n}{d}.svg').read_text(encoding='utf-8'), n + d
        for n in ('seabed', 'bot-read', 'bot-hero', 'bot-peek'):
            moving = (A / f'{n}-anim{d}.svg').read_text(encoding='utf-8')
            assert '@keyframes' in moving and 'prefers-reduced-motion' in moving and '@keyframes' not in (A / f'{n}{d}.svg').read_text(encoding='utf-8'), n + d
    before = {p.name: p.read_bytes() for p in A.iterdir()}
    code, out = build_site(root)
    assert code == 0, out
    assert {p.name: p.read_bytes() for p in A.iterdir()} == before, 'the ocean art differs on a rebuild'
    # every page head: rays, plankton and the crossing school first; the reef fish only where the head has no bot (the bot stays)
    bad, heads, reefs = [], 0, 0
    for p in sorted(site.rglob('*.html')):
        h, rel = p.read_text(encoding='utf-8'), p.relative_to(site).as_posix()
        for m in re.finditer(r'<header class="(page-head[^"]*)">', h):
            heads += 1
            rest = h[m.end():m.end() + 900]
            if not rest.startswith(DD_HEAD): bad.append(f'{rel}: page head without its motion layers')
            elif 'has-bot' in m[1]:
                if not rest[len(DD_HEAD):].startswith('<div class="wrap">'): bad.append(f'{rel}: reef fish next to the bot')
            elif DD_REEF.match(rest, len(DD_HEAD)): reefs += 1
            else: bad.append(f'{rel}: page head without the reef fish')
        if '<footer class="foot">' in h and '<footer class="foot"><span class="dd-plankton" aria-hidden="true"><i></i><i></i></span>' not in h: bad.append(f'{rel}: footer without plankton')
        if h.count('<span class="bot-art" aria-hidden="true"></span>') != h.count('<span class="bot-art" aria-hidden="true"></span><span class="dd-q" aria-hidden="true"></span>'): bad.append(f'{rel}: a bot without its question bubble')
        if re.search(r'<span class="dd-[^"]*"(?![^>]*aria-hidden="true")', h): bad.append(f'{rel}: a dd- layer that is not aria-hidden')
    assert not bad and heads and reefs, '\n  '.join([''] + bad[:10])
    hero = (site / 'index.html').read_text(encoding='utf-8')
    assert '<span class="dd-plankton" aria-hidden="true"><i></i><i></i></span><span class="hero-bot"' in hero and hero.count('dd-rays') == hero.count('<header class="page-head'), 'the hero draws its own rays'
    figures = re.findall(r'<dd>(.*?)</dd>', hero[hero.index('<dl class="stats">'):hero.index('</dl>', hero.index('<dl class="stats">'))])
    pw_ = browser()
    if not pw_: print('    browser check: skipped (Playwright not installed)'); return
    errs = []
    with pw_() as pw:
        b = pw.chromium.launch()
        try:
            for scheme in ('light', 'dark'):
                ctx = b.new_context(viewport={'width': 1280, 'height': 900}, color_scheme=scheme, reduced_motion='reduce')
                pg = ctx.new_page()
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                for page in dd_pages(site):
                    pg.goto(dd_url(site, page))
                    pg.wait_for_timeout(250)
                    r = pg.evaluate("""() => { const cs = (s, p) => { const e = document.querySelector(s); return e ? getComputedStyle(e, p) : null; };
                        return {anims: document.getAnimations().map(a => a.animationName || 'a transition'), seabed: cs('.foot', '::before').backgroundImage,
                          bots: [...document.querySelectorAll('.bot-art, .foot-bot, .hero-bot')].map(e => getComputedStyle(e).backgroundImage).concat(
                            [...document.querySelectorAll('.page-head.has-bot')].map(e => getComputedStyle(e, '::after').backgroundImage)),
                          fish: [...document.querySelectorAll('.dd-reef > i')].map(e => getComputedStyle(e).backgroundImage),
                          shown: [...document.querySelectorAll('.dd-rays, .dd-plankton, .dd-crossing, .dd-q, .dd-blow')].filter(e => getComputedStyle(e).display != 'none').length,
                          figures: [...document.querySelectorAll('.stats dd')].map(d => d.innerHTML) }; }""")
                    where = f'{scheme} {page}'
                    if r['anims']: errs.append(f'{where}: animations run with reduced motion: {r["anims"][:4]}')
                    if 'seabed.svg' not in r['seabed'] and 'seabed-dark.svg' not in r['seabed']: errs.append(f'{where}: footer art {r["seabed"][-40:]}')
                    if any('-anim' in x for x in r['bots'] + r['fish']): errs.append(f'{where}: a moving picture with reduced motion')
                    if r['shown']: errs.append(f'{where}: {r["shown"]} rays, plankton or bubbles shown with reduced motion')
                    if page == 'index.html' and r['figures'] != figures: errs.append(f'{where}: the figures moved: {r["figures"]} (built: {figures})')
                    if page == 'search.html':  # a click on a fish does nothing
                        f = pg.evaluate(DD_FISH)
                        pg.mouse.click(*f['yellow'])
                        pg.wait_for_timeout(200)
                        if pg.evaluate("document.querySelectorAll('.dd-dart, .dd-back').length + document.getAnimations().length"): errs.append(f'{where}: a fish moved on click')
                ctx.close()
        finally:
            b.close()
    assert not errs, '\n  '.join([''] + errs[:10])
    print(f'    {len(DD_ASSETS) * 2} motion files, {heads} page heads ({reefs} with reef fish); {len(dd_pages(site))} pages still with reduced motion, light and dark')


def test_deep_dive_motion_runs():  # the Deep Dive motion with no preference: it runs, counts up to the exact figures, the fish dart and come back, no sideways scroll
    root = real_site_root()
    site = root / '60-outputs' / 'site'
    pw_ = browser()
    if not pw_: print('    browser check: skipped (Playwright not installed)'); return
    errs = []
    with pw_() as pw:
        b = pw.chromium.launch()
        try:
            for scheme in ('light', 'dark'):
                ctx = b.new_context(viewport={'width': 1280, 'height': 900}, color_scheme=scheme, reduced_motion='no-preference')
                pg = ctx.new_page()
                pg.on('pageerror', lambda e: errs.append(f'{scheme} {pg.url}: {e}'))
                pg.on('console', lambda m: errs.append(f'{scheme} {pg.url}: {m.text}') if m.type == 'error' else None)
                for page in dd_pages(site):
                    pg.goto(dd_url(site, page))
                    pg.wait_for_timeout(700)
                    r = pg.evaluate("""() => ({anims: [...new Set(document.getAnimations().map(a => a.animationName))],
                        seabed: getComputedStyle(document.querySelector('.foot'), '::before').backgroundImage,
                        plankton: [...document.querySelectorAll('.page-head > .dd-plankton, .hero > .dd-plankton, .foot > .dd-plankton')].map(e => getComputedStyle(e).display),
                        puzzled: !!document.querySelector('#search-guide.dd-puzzled:not([hidden])'),
                        guide: (g => g ? {shown: !g.hidden, pose: g.dataset.pose} : null)(document.getElementById('search-guide'))})""")
                    want = {'dd-roll', 'dd-bot-rock'} | ({'dd-ray-sway', 'dd-cross'} if page != 'index.html' else {'dd-bob'})
                    if page == 'topics/robots-txt.html' or page.startswith('search'): want |= {'dd-swim-yellow', 'dd-swim-red', 'dd-swim-school', 'dd-trail'}
                    if page == 'about.html': want.add('dd-bot-stand')
                    if page.startswith('sessions/') or page.endswith('zzqx'): want |= {'dd-q-pop', 'dd-q-float'}  # (the one-off tilt may be over by now)
                    if scheme == 'dark': want |= {'dd-plankton-a', 'dd-plankton-b', 'dd-twinkle'}
                    if want - set(r['anims']): errs.append(f'{scheme} {page}: missing {sorted(want - set(r["anims"]))}')
                    if 'seabed-anim' not in r['seabed']: errs.append(f'{scheme} {page}: footer seabed {r["seabed"][-40:]}')
                    if r['plankton'] != (['block'] if scheme == 'dark' else ['none']) * len(r['plankton']) or len(r['plankton']) < 2: errs.append(f'{scheme} {page}: plankton {r["plankton"]}')
                    if page.endswith('zzqx') and not r['puzzled']: errs.append(f'{scheme}: the search bot is not puzzled when nothing matches')
                    if page.startswith('search') and not page.endswith('zzqx') and '?q=' in page and r['guide'] != {'shown': True, 'pose': 'read'}:
                        errs.append(f'{scheme} {page}: the search bot is not shown above the results ({r["guide"]})')
                # a page change by link and back (view transitions) leaves no error, also to and from the two maps
                pg.goto(dd_url(site, 'index.html'))
                for link in ('.site-nav a[href$="topics.html"]', '.site-nav a[href$="graph.html"]', '.downloads a[href="mindmap.html"]'):
                    pg.click(link)
                    pg.wait_for_load_state('load')
                    pg.wait_for_timeout(400)
                    pg.go_back()
                    pg.wait_for_load_state('load')
                    pg.wait_for_timeout(400)
                    if not pg.url.endswith('index.html'): errs.append(f'back from {link} went to {pg.url}')
                ctx.close()
            # the home figures count up once they are seen, and end as exactly the original markup
            ctx = b.new_context(viewport={'width': 1280, 'height': 560}, reduced_motion='no-preference')
            pg = ctx.new_page()
            pg.goto(dd_url(site, 'index.html'))
            figs = "() => [...document.querySelectorAll('.stats dd')].map(d => d.innerHTML)"
            orig = pg.evaluate(figs)
            pg.evaluate("document.querySelector('.stats').scrollIntoView({block: 'center'})")
            pg.wait_for_timeout(350)
            mid, labels = pg.evaluate(figs), pg.evaluate("() => [...document.querySelectorAll('.stats dd')].map(d => d.getAttribute('aria-label'))")
            pg.wait_for_timeout(1700)
            end = pg.evaluate(figs)
            if not orig or end != orig or mid == orig or labels[0] != orig[0]: errs.append(f'count-up: {orig} -> {mid} {labels} -> {end}')
            # a click on a fish sends it darting off; it comes back a few seconds later; a click on the heading moves nothing
            pg.set_viewport_size({'width': 1280, 'height': 900})
            pg.goto(dd_url(site, 'search.html'))
            f = pg.evaluate(DD_FISH)
            cls = "() => [...document.querySelectorAll('.dd-reef > i')].map(i => i.className.replace(/dd-fish |dd-f-|dd-trail/g, '').trim()).join(',')"
            h1 = pg.evaluate("(() => { const r = document.querySelector('.page-head h1').getBoundingClientRect(); return [r.left + 12, r.top + r.height / 2]; })()")
            pg.mouse.click(*h1)
            if 'dd-' in pg.evaluate(cls): errs.append('a click on the heading moved a fish')
            for name in ('yellow', 'red', 'school'):
                at = pg.evaluate(f"document.elementFromPoint({f[name][0]}, {f[name][1]}).className")
                if at != 'dd-reef': errs.append(f'the {name} fish is under {at!r}, not clickable')
            pg.mouse.click(*f['yellow'])
            seq = [pg.evaluate(cls)]
            for _ in range(12):
                pg.wait_for_timeout(500)
                seq.append(pg.evaluate(cls))
            if 'school,,yellow dd-dart,red' not in seq or 'school,,yellow dd-back,red' not in seq or seq[-1] != 'school,,yellow,red': errs.append(f'fish click: {seq}')
            ctx.close()
            # no sideways scroll with the motion on, phone to wide screen
            for wd in (320, 375, 1280, 1680):
                ctx = b.new_context(viewport={'width': wd, 'height': 800}, color_scheme='dark', reduced_motion='no-preference')
                pg = ctx.new_page()
                for page in dd_pages(site):
                    pg.goto(dd_url(site, page))
                    pg.wait_for_timeout(150)
                    sw = pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
                    if sw: errs.append(f'{wd}px {page}: scrolls sideways by {sw}px')
                ctx.close()
        finally:
            b.close()
    assert not errs, '\n  '.join([''] + errs[:10])
    print(f'    {len(dd_pages(site))} pages moving in light and dark, the count-up, a fish click, 4 widths')


def real_proven_names():
    """claim id -> the proven speaker of every public slide and stage claim, straight from 20-claims/ through kits.proven()."""
    K = load_module(REPO / '_system' / 'kits.py', 'kits_proven')
    S = {s['id']: s for d in yaml.safe_load((REPO / '20-claims' / 'sessions.yaml').read_text(encoding='utf-8'))['days'] for s in d['sessions'] or []}
    claims = [c for f in sorted((REPO / '20-claims').glob('day*.yaml')) for c in yaml.safe_load(f.read_text(encoding='utf-8')) or [] if not c.get('private')]
    return {c['id']: K.proven(c, S) for c in claims if c['label'] in ('slide', 'stage')}


def test_search_scope_speaker_filter_typos():  # knowledge graph phase 0 on the real data: backlinks on every claim card, typos, aliases, scope order, speaker filter
    root = real_site_root()
    P, site = root / '60-outputs' / 'agent-pack', root / '60-outputs' / 'site'
    rows = [json.loads(l) for l in (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines()]
    links, graph = (json.loads((P / f).read_text(encoding='utf-8')) for f in ('links.json', 'graph.json'))
    # what rests on a claim, as the kits list it, and every graph edge resolving
    rests = {}
    for n, it in links['items'].items():
        for c in it['claims']: rests.setdefault(c, set()).add(n)
    assert all(set(r['used_by']) == rests.get(r['id'], set()) and len(r['used_by']) == len(rests.get(r['id'], ())) for r in rows)
    ids = {n['id'] for n in graph['nodes']}
    assert all(e['from'] in ids and e['to'] in ids for e in graph['edges']) and len(ids) == len(graph['nodes'])
    assert sum(1 for e in graph['edges'] if e['type'] == 'rests-on') == sum(len(r['used_by']) for r in rows)
    # every claim card of claims.html shows its "Used by" line with one link per kit item, and none where nothing rests on the claim
    page = (site / 'claims.html').read_text(encoding='utf-8')
    cards = dict(re.findall(r'<article class="claim [^"]*" id="(D\d+-C\d{3})"[^>]*>(.*?)</article>', page, re.S))
    assert set(cards) == {r['id'] for r in rows}, 'claims.html does not show every public claim'
    bad = []
    for r in rows:
        m = re.search(r'<p class="used-by">(.*?)</p>', cards[r['id']], re.S)
        got = re.findall(r'<a class="[^"]*" href="[^"#]*#([^"]+)"', m[1]) if m else []
        want = [('term-' if n.startswith('term:') else '') + n.split(':', 1)[1] for n in r['used_by']]
        if got != want: bad.append((r['id'], got, want))
    assert not bad, bad[:5]
    pw_ = browser()
    if not pw_: print('    browser check: skipped (Playwright not installed)'); return
    proven = real_proven_names()
    with pw_() as pw:
        b = pw.chromium.launch()
        try:
            pg = b.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            pg.goto((site / 'search.html').as_uri())
            def q(text):
                pg.fill('#q', text)
                pg.press('#q', 'Enter')
                return pg.evaluate("""() => { const n = document.getElementById('search-note');
                    return {status: document.getElementById('search-status').textContent, note: n.hidden ? '' : n.textContent,
                            heads: [...document.querySelectorAll('#results .res-h')].map(h => h.firstChild.textContent),
                            first: [...document.querySelectorAll('#results .res-list')].map(u => (u.querySelector('li .res-t, li .claim-text') || {}).textContent),
                            claims: [...document.querySelectorAll('#results .res-list.cl .claim-head a.cid')].map(a => a.textContent)} }""")
            typo = q('hreflung')
            pg.click('#search-note .linkish')
            literal = pg.evaluate("() => [document.getElementById('search-status').textContent, document.getElementById('search-note').hidden]")
            noindex, gsc, canon = q('noindex'), q('GSC'), q('canon')
            opts = pg.evaluate("() => [...document.querySelectorAll('#f-speaker option')].map(o => o.value).filter(Boolean)")
            q('crawl budget')
            pg.select_option('#f-speaker', 'n:Gary Illyes')
            gary = pg.evaluate("() => [...document.querySelectorAll('#results .res-list.cl .claim-head a.cid')].map(a => a.textContent)")
            pg.select_option('#f-speaker', 'g:audience')
            q('crawl')
            audience = pg.evaluate("() => [...document.querySelectorAll('#results .res-list.cl .claim-head a.cid')].map(a => a.textContent)")
        finally:
            b.close()
    # "hreflung": the note, the corrected results, and the way back to the literal word
    assert 'Showing results for hreflang' in typo['note'] and 'you typed hreflung' in typo['note'], typo
    assert typo['heads'] and typo['claims'] and 'hreflang' in typo['first'][0].lower(), typo
    assert literal[0].startswith('No results') and literal[1], literal
    # "noindex": the thing, then the glossary term, the requirements above the claims
    H = noindex['heads']
    assert H[:2] == ['Things', 'Glossary'] and noindex['first'][:2] == ['noindex', 'noindex'] and 'Developer requirements' in H and 'Claims' in H, noindex  # phase 1: the thing first
    assert H.index('Developer requirements') < H.index('Claims') and H.index('Glossary') < H.index('Claims'), H
    assert 'GSC = Google Search Console, Search Console' in gsc['note'] and gsc['claims'], gsc  # the hand alias, printed as spelled
    assert canon['claims'] and any('canonical' in (x or '').lower() for x in canon['first']), canon  # a word start matches
    # the speaker filter offers only names kits.proven() proves, and only the four groups
    names = {o[2:] for o in opts if o.startswith('n:')}
    assert names == {n for n in proven.values() if n}, sorted(names ^ {n for n in proven.values() if n})
    assert {o for o in opts if not o.startswith('n:')} <= {'g:google', 'g:community', 'g:unattributed', 'g:audience'}, opts
    assert gary and all(proven.get(c) == 'Gary Illyes' for c in gary), gary
    who = {r['id']: r['who'] for r in rows}
    assert audience and all(who[c] == 'audience' for c in audience), audience
    assert not errs, errs[:5]
    print(f'    {len(names)} proven names in the speaker filter; "crawl budget" by Gary Illyes: {len(gary)} claims')


def page_text(h):  # the visible words of an HTML page, unescaped, one space between them
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)\b.*?</\1>', ' ', h, flags=re.S))).split())


def test_site_entity_pages():  # knowledge graph phase 1 on the real data: mentions, relations, cards, privacy, links, search
    root = real_site_root()
    P, site = root / '60-outputs' / 'agent-pack', root / '60-outputs' / 'site'
    rows = {r['id']: r for r in map(json.loads, (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines())}
    E = json.loads((P / 'entities.json').read_text(encoding='utf-8'))
    ents = {x['id']: x for x in E['entities']}
    assert 70 <= len(ents) <= 90 and sum(len(x['claims']) for x in ents.values()) > 1500, len(ents)
    # every mention's via is written in its claim; a pin has none
    ment = {}
    for r in rows.values():
        for m in r['mentions']:
            assert (m['field'] == 'pin' and m['via'] is None) or (m['field'] in ('text', 'quote') and m['via'] and m['via'] in (r[m['field']] or '')), (r['id'], m)
            ment.setdefault(m['entity'], set()).add(r['id'])
    assert {k: set(x['claims']) for k, x in ents.items() if x['claims']} == ment
    # every factual relation cites public claims that mention both ends; structural ones cite none
    factual = 0
    for k, x in ents.items():
        for r in x['rel']:
            if r['type'] in ('is-a', 'part-of'): assert r['claims'] == [], (k, r); continue
            factual += 1
            assert r['claims'] and all(c in rows and {k, r['to']} <= {m['entity'] for m in rows[c]['mentions']} for c in r['claims']), (k, r)
    assert factual >= 20, factual
    # no private claim, excluded photo or unproven name: cite strings name a person only where kits.proven() does
    private = [c['id'] for f in sorted((REPO / '20-claims').glob('day*.yaml')) for c in yaml.safe_load(f.read_text(encoding='utf-8')) or [] if c.get('private')]
    outs = [P / 'entities.json', root / '50-maps' / 'entity-index.md', site / 'entities.html', site / 'assets' / 'search-data.js'] \
        + sorted((P / 'entities').glob('*.md')) + sorted((site / 'entities').glob('*.html'))
    for p in outs:
        t = p.read_text(encoding='utf-8')
        bad = [c for c in private if c in t] + (['IMG_4692'] if 'img_4692' in t.lower() else [])
        assert not bad, f'{p.relative_to(root)}: {bad}'
    proven = real_proven_names()
    generic = {'Google', 'a community speaker', 'a speaker', 'an audience member'}
    for k, x in ents.items():
        for c, s in x['cite'].items():
            r = rows[c]
            if r['label'] not in ('slide', 'stage'): continue
            who = s.strip('[]').split(', ')[2]
            assert who == proven.get(c) or (who in generic and (r['who'] != 'audience' or who == 'an audience member')), (k, c, s)
    K = load_module(REPO / '_system' / 'kits.py', 'kits_people')  # the people the build knows: session speakers and every named `who`
    S = {s['id']: s for d in yaml.safe_load((REPO / '20-claims' / 'sessions.yaml').read_text(encoding='utf-8'))['days'] for s in d['sessions'] or []}
    people = K.people(S)[0] | {r['who'] for r in rows.values() if K.person(r['who'])} | {n for n in proven.values() if n}
    for x in ents.values():
        blob = ' '.join([x['name'], x['summary']] + x['aliases'] + [m['s'] for m in x['match']])
        named = [n for n in people if re.search(r'(?<!\w)' + re.escape(n) + r'(?!\w)', blob)]
        assert not named, (x['id'], named)
    # a card with home topics links to them and does not repeat their summaries (site and pack)
    topics = {t['id']: t for a in json.loads((P / 'topics.json').read_text(encoding='utf-8'))['areas'] for t in a['topics']}
    homed = [x for x in ents.values() if x['topics']]
    assert len(homed) >= 30, len(homed)
    for x in homed:
        h = (site / 'entities' / f"{x['id']}.html").read_text(encoding='utf-8')
        md_ = (P / 'entities' / f"{x['id']}.md").read_text(encoding='utf-8')
        for t in x['topics']:
            assert f'href="../topics/{t}.html"' in h and f'(../topics/{t}.md)' in md_, (x['id'], t)
            head = ' '.join(topics[t]['summary'].split())[:80]
            assert head not in page_text(h) and head not in ' '.join(md_.split()), (x['id'], t, head)
    # every link of the index and the cards resolves, anchors included (a link to the Reef map names a node of its data: graph.html#ent:googlebot)
    nodes = {n['i'] for n in graph_data(site / 'assets' / 'graph-data.js')['nodes']} if (site / 'assets' / 'graph-data.js').exists() else set()
    ids_of = {}
    def anchors(p):
        if p not in ids_of: ids_of[p] = set(re.findall(r'\sid="([^"]+)"', p.read_text(encoding='utf-8')))
        return ids_of[p]
    broken, n_links = [], 0
    for p in [site / 'entities.html'] + sorted((site / 'entities').glob('*.html')):
        for href in re.findall(r'\shref="([^"]+)"', p.read_text(encoding='utf-8')):
            if re.match(r'[a-z]+:', href): continue
            n_links += 1
            path, _, frag = html.unescape(href).partition('#')
            tgt = (p.parent / path).resolve() if path else p
            if tgt.name == 'graph.html' and tgt.is_file():
                if frag and frag not in nodes: broken.append((p.name, href))
                continue
            if not tgt.is_file() or (frag and frag not in anchors(tgt)): broken.append((p.name, href))
    assert not broken, broken[:10]
    idx = (site / 'entities.html').read_text(encoding='utf-8')
    assert all(f'href="entities/{k}.html"' in idx for k in ents), 'the things index does not link every card'
    pw_ = browser()
    if not pw_: print('    browser check: skipped (Playwright not installed)'); return
    sample = ['google-search-console', 'http-429', 'googlebot'] + sorted(ents)[::45][:2]
    with pw_() as pw:
        b = pw.chromium.launch()
        try:
            errs = []
            for width in (1280, 375):
                pg = b.new_page(viewport={'width': width, 'height': 800})
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                for rel in ['entities.html'] + [f'entities/{k}.html' for k in sample]:
                    pg.goto((site / rel).as_uri())
                    r = pg.evaluate("() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, h1: document.querySelector('h1').textContent})")
                    assert r['sw'] <= r['cw'], f'{rel} scrolls sideways at {width}px: {r}'
                pg.close()
            pg = b.new_page()
            pg.goto((site / 'search.html').as_uri())
            def first_thing(text):
                pg.fill('#q', text)
                pg.press('#q', 'Enter')
                return pg.evaluate("""() => { const u = document.querySelector('#results .res-list');
                    return [document.querySelector('#results .res-h').firstChild.textContent, u.querySelector('li a.res-t').getAttribute('href'), u.querySelector('li a.res-t').textContent] }""")
            gsc, four29 = first_thing('GSC'), first_thing('429')
        finally:
            b.close()
    assert not errs, errs[:5]
    assert gsc == ['Things', 'entities/google-search-console.html', 'Search Console'], gsc
    assert four29 == ['Things', 'entities/http-429.html', '429'], four29
    print(f'    {len(ents)} things, {sum(len(v) for v in ment.values())} mentions, {factual} factual relations, {n_links} card links resolve')


def graph_data(path):  # window.KB_GRAPH of assets/graph-data.js (or of 50-maps/graph.html, where it is inline)
    t = Path(path).read_text(encoding='utf-8')
    m = re.search(r'window\.KB_GRAPH = (\{.*?\});(?:\n|</script>)', t, re.S)
    assert m, f'no window.KB_GRAPH in {path}'
    return json.loads(m[1])


KIT_PAGES = {'dev/index.html': 'req:', 'content/facts.html': 'fact:', 'content/myths.html': 'myth:', 'content/quotes.html': 'quote:', 'content/angles.html': 'angle:',
             'content/glossary.html': 'term:'}
PREVIEW_KIND = {'F': 'fact:', 'M': 'myth:', 'Q': 'quote:', 'A': 'angle:'}  # community edition: content/index.html#F-012 is the card of a preview item


def card_neighbours(h):  # what a thing's card lists around it (things, topics, claims, kit items, documents), as Reef map node ids or URLs
    sec = lambda name: ''.join(re.findall(rf'<section aria-labelledby="{name}"[^>]*>(.*?)</section>', h, re.S))
    con, built, docs = sec('connected'), sec('built'), sec('docs')
    head = h.split('<main', 1)[1].split('</header>', 1)[0]
    gloss = h.split('gloss-c', 1)[1].split('</div>', 1)[0] if 'gloss-c' in h else ''
    kit = {(KIT_PAGES.get(p) or PREVIEW_KIND[i[0]]) + (i[5:] if i.startswith('term-') else i) for p, i in re.findall(r'href="\.\./((?:dev|content)/[a-z]+\.html)#([^"]+)"', built + gloss)}
    srcs = docs.split('<ul class="srcs big">', 1)[1].split('</ul>', 1)[0] if 'srcs big' in docs else ''
    return {'ent': {'ent:' + k for k in re.findall(r'href="\.\./entities/([a-z0-9-]+)\.html"', con)},
            'topic': {'topic:' + t for t in re.findall(r'href="\.\./topics/([a-z0-9-]+)\.html"', con + head)},
            'claim': {'claim:' + c for c in re.findall(r'claims\.html#(D\d+-C\d{3})"', h)},
            'kit': kit, 'source': {html.unescape(u) for u in re.findall(r'<a class="ext" href="([^"]+)"', srcs)}}


PANEL_NB = """() => { const out = {ent: [], topic: [], claim: [], kit: [], source: []};
  for (const li of document.querySelectorAll('#panel li[data-id]')) { const id = li.dataset.id, k = id.split(':')[0];
    if (k === 'source') out.source.push(li.querySelector('a.out').getAttribute('href')); else (out[k] || out.kit).push(id); }
  return out; }"""
OFFLINE = re.compile(r'<(script|link(?! rel="canonical")|img|iframe)\b[^>]*\b(src|href)\s*=\s*["\']?(https?:)?//|\bfetch\(|type=["\']module|\bimport\(')  # a canonical link names the page, it loads nothing


def test_reef_map():  # knowledge graph phase 2 on the real data: the explorer from file://, recentre, back, panel = card, filters, keyboard, search; since v2.12.0 pan, zoom, drag, menu, expand, pin, trail, living layout, touch
    root = real_site_root()
    site, P = root / '60-outputs' / 'site', root / '60-outputs' / 'agent-pack'
    page, maps = site / 'graph.html', root / '50-maps' / 'graph.html'
    assert page.exists() and maps.exists() and (site / 'assets' / 'graph-data.js').exists()
    G, G2 = graph_data(site / 'assets' / 'graph-data.js'), graph_data(maps)
    assert G == G2, 'the copy in 50-maps carries different data'
    gj = json.loads((P / 'graph.json').read_text(encoding='utf-8'))
    want = [n['id'] for n in gj['nodes'] if n['kind'] in ('entity', 'topic', 'requirement', 'fact', 'myth', 'quote', 'angle', 'term', 'source', 'claim')]
    assert [n['i'] for n in G['nodes']] == want and G['start'] == 'ent:googlebot'
    assert all(0 <= a < len(want) and 0 <= b < len(want) for a, b, *_ in G['edges'])
    h, hm = page.read_text(encoding='utf-8'), maps.read_text(encoding='utf-8')
    assert '<script src="assets/graph-data.js"></script>' in h and '<script src=' not in hm
    code = re.sub(r'<script>window\.KB_GRAPH = .*?</script>', '', hm, flags=re.S)  # the page itself, not the claims it carries (a claim may quote fetch())
    assert not OFFLINE.search(h) and not OFFLINE.search(code), 'the Reef map must not fetch, use modules or load external files'
    private = [c['id'] for f in sorted((REPO / '20-claims').glob('day*.yaml')) for c in yaml.safe_load(f.read_text(encoding='utf-8')) or [] if c.get('private')]
    blob = (site / 'assets' / 'graph-data.js').read_text(encoding='utf-8')
    assert not [c for c in private if c in blob] and 'img_4692' not in blob.lower()
    # links: the site menu, every card, the topics, the mindmap (both ways)
    ents = sorted(x['id'] for x in json.loads((P / 'entities.json').read_text(encoding='utf-8'))['entities'])
    assert 'href="graph.html"><span class="nm-dd">Reef map</span><span class="nm-deco">Graph</span></a>' in (site / 'index.html').read_text(encoding='utf-8')
    cards = {k: (site / 'entities' / f'{k}.html').read_text(encoding='utf-8') for k in ents}
    assert all(f'href="../graph.html#ent:{k}"' in cards[k] and 'Open in Reef map' in cards[k] for k in ents)
    assert 'href="../graph.html#topic:robots-txt"' in (site / 'topics' / 'robots-txt.html').read_text(encoding='utf-8')
    mm = (site / 'mindmap.html').read_text(encoding='utf-8')
    assert 'href="graph.html"' in mm and 'graph.html#topic:' in mm and 'href="mindmap.html"' in h and 'mindmap.html#topic:' in h
    pw_ = browser()
    if not pw_: print('    browser check: skipped (Playwright not installed)'); return
    bad = []
    centre_is = 'n => document.querySelector("#map .nd.centre").dataset.i === n'
    with pw_() as pw:
        b = pw.chromium.launch()
        try:
            # Deep Dive only (the build's style, from theme.yaml): a style an older version kept in the browser changes nothing
            style = load_module(root / '_system' / 'theme.py', 'theme_reef').default_style()
            for (wd, ht), scheme in (((1440, 900), 'light'), ((1280, 800), 'dark'), ((390, 844), 'light'), ((390, 844), 'dark')):
                ctx = b.new_context(viewport={'width': wd, 'height': ht}, color_scheme=scheme)
                pg, errs, at = ctx.new_page(), [], f'{wd}px {scheme} {style}'
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                pg.on('requestfailed', lambda r: errs.append('failed ' + r.url))
                pg.goto(page.as_uri())
                pg.evaluate("localStorage.setItem('kb-style', 'art-deco')")  # the choice an older version kept
                pg.goto(page.as_uri() + '#ent:googlebot')
                pg.reload()
                r = pg.evaluate("""() => ({h2: document.querySelector('#panel h2').textContent, nodes: document.querySelectorAll('#map .nd').length,
                    style: document.documentElement.dataset.style, sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
                    name: getComputedStyle(document.querySelector('header h1 .nm-dd')).display})""")
                if r['h2'] != 'Googlebot' or r['nodes'] < 20 or r['style'] != style: bad.append(f'{at}: does not open on #ent:googlebot: {r}')
                if r['sw'] > r['cw']: bad.append(f'{at}: the page scrolls sideways {r}')
                if (r['name'] != 'none') != (style == 'deep-dive'): bad.append(f'{at}: the name is not "Reef map" in Deep Dive and "Graph" in Art Deco')
                settled(pg)
                v0 = pg.evaluate(VIEW)
                pg.click('[data-z="0"]')
                pg.wait_for_timeout(500)
                if any(abs(a - c) > .5 for a, c in zip(pg.evaluate(VIEW), v0)): bad.append(f'{at}: Fit does not give the view the map opened with: {v0} -> {pg.evaluate(VIEW)}')
                # recentre on a click, and the back button returns
                tgt = pg.locator('#map .nd.k-entity:not(.centre)').first
                j = tgt.get_attribute('data-i')
                tgt.click()
                pg.wait_for_function(centre_is, arg=j)
                h1 = pg.evaluate('location.hash')
                pg.go_back()
                pg.wait_for_function('() => location.hash === "#ent:googlebot" && document.querySelector("#panel h2").textContent === "Googlebot"')
                if h1 == '#ent:googlebot' or not h1.startswith('#ent:'): bad.append(f'{at}: a click did not recentre: {h1}')
                # keyboard: the centre comes first, Tab and the arrows walk the nodes, Enter recentres and keeps the focus in the map
                pg.focus('#map .nd.centre')
                pg.keyboard.press('Tab')
                k1 = pg.evaluate("document.activeElement.closest('#map .nd') ? document.activeElement.dataset.i || document.activeElement.dataset.b : null")
                pg.keyboard.press('ArrowRight')
                k2 = pg.evaluate("document.activeElement.closest('#map .nd') ? document.activeElement.dataset.i || document.activeElement.dataset.b : null")
                if not k1 or not k2 or k1 == k2: bad.append(f'{at}: Tab and arrow keys do not walk the nodes: {k1}, {k2}')
                pg.keyboard.press('ArrowLeft')
                pg.keyboard.press('Enter')
                pg.wait_for_function(centre_is, arg=k1)
                if not pg.evaluate("document.activeElement.classList.contains('centre')"): bad.append(f'{at}: after Enter the focus is not on the new centre')
                pg.go_back()
                pg.wait_for_function('() => location.hash === "#ent:googlebot"')
                if errs: bad.append(f'{at}: console errors {errs[:3]}')
                ctx.close()
            # filters, hop depth, the claims bubble, search, reduced motion, determinism
            ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
            pg, errs = ctx.new_page(), []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            pg.goto(page.as_uri() + '#ent:googlebot')
            count = lambda sel: pg.evaluate(f"document.querySelectorAll('{sel}').length")
            layout = "[...document.querySelectorAll('#map .nd')].map(g => g.getAttribute('transform')).join('|')"
            if pg.evaluate("document.querySelector('#map svg').getAttribute('class')"): bad.append('reduced motion: the map still animates')
            pg.click('#live', force=True)
            if not pg.evaluate("document.getElementById('live').disabled") or pg.evaluate("document.getElementById('map').dataset.sim") != 'off':
                bad.append('reduced motion: the living layout can still be switched on')
            settled(pg)
            first, view = pg.evaluate(layout), pg.evaluate(VIEW)
            pg.reload()
            settled(pg)
            if pg.evaluate(layout) != first or pg.evaluate(VIEW) != view: bad.append('the layout differs between two loads')
            pg.uncheck('#kinds input[value=entity]')
            if count('#map .nd.k-entity:not(.centre)'): bad.append('the Things filter does not hide things')
            pg.check('#kinds input[value=entity]')
            n1 = count('#map .nd')
            pg.click('[data-hop="2"]')
            if not count('#map .nd.r2') or count('#map .nd') <= n1: bad.append('2 hops draws no second ring')
            pg.click('[data-hop="1"]')
            n_claims = len([e for e in gj['edges'] if e['type'] == 'mentions' and e['to'] == 'ent:googlebot'])
            pg.locator('#map .nd.bundle[data-b="claim"]').click()
            if count('#map .nd.k-claim') != n_claims: bad.append(f'the claims bubble does not open the {n_claims} claims: {count("#map .nd.k-claim")}')
            pg.fill('#q', 'GSC')
            pg.press('#q', 'Enter')
            pg.wait_for_function('() => location.hash === "#ent:google-search-console"')
            pg.fill('#q', 'hreflung')
            if 'Showing results for' not in pg.locator('#hits').text_content(): bad.append('search does not correct hreflung')
            pg.fill('#q', '')
            # a big node stays readable: a "+ more" bubble adds at most a dozen of its kind, and "Show fewer" folds them back
            n0 = count('#map .nd.k-entity:not(.centre)')
            pg.locator('#map .nd.bundle[data-b="entity"][data-less="0"]').click()
            n1 = count('#map .nd.k-entity:not(.centre)')
            if not 0 < n1 - n0 <= 12 or count('#map .nd.bundle[data-b="entity"][data-less="1"]') != 1: bad.append(f'Search Console: "+ more" shows {n0} then {n1} things')
            pg.locator('#map .nd.bundle[data-b="entity"][data-less="1"]').click()
            if count('#map .nd.k-entity:not(.centre)') != n0: bad.append('Search Console: "Show fewer" does not fold the things back')
            # the side panel lists the same neighbours as the card, for every thing
            for k in ents:
                pg.evaluate(f"location.hash = '#ent:{k}'")
                pg.wait_for_function(f"() => document.querySelector('#panel li[data-id], #panel .note') && location.hash === '#ent:{k}' && "
                                     f"document.querySelector('#map .nd.centre').dataset.i === String({want.index('ent:' + k)})")
                got = {x: set(v) for x, v in pg.evaluate(PANEL_NB).items()}
                exp = card_neighbours(cards[k])
                diff = {x: (sorted(got[x] - exp[x])[:3], sorted(exp[x] - got[x])[:3]) for x in got if got[x] != exp[x]}
                if diff: bad.append(f'{k}: the side panel and the card differ: {diff}')
            # the mindmap opens on a topic from the map, and the copy in 50-maps works on its own
            pg.goto((site / 'mindmap.html').as_uri() + '#topic:robots-txt')
            if pg.locator('#panel h2').text_content() != pg.evaluate("DATA.areas.flatMap(a => a.topics).find(t => t.id === 'robots-txt').title"):
                bad.append('the mindmap does not open on #topic:robots-txt')
            if not pg.evaluate("document.querySelectorAll('#panel ul.things a[href^=\"graph.html#ent:\"]').length"):
                bad.append('the mindmap topic panel does not list its things with links into the map')
            pg.goto(maps.as_uri() + '#topic:robots-txt')
            if pg.evaluate("document.getElementById('home').getAttribute('href')") != '../60-outputs/site/index.html' or \
                    not pg.evaluate("document.querySelector('#panel .acts a').getAttribute('href')").startswith('../60-outputs/site/topics/'):
                bad.append('50-maps/graph.html does not link to the web edition')
            if errs: bad.append(f'console errors {errs[:3]}')
            ctx.close()
            bad += reef_mouse(b, page) + reef_touch(b, page)
        finally:
            b.close()
    assert not bad, '\n  '.join([''] + bad[:20])
    print(f'    {len(G["nodes"])} nodes, {len(G["edges"])} edges; {len(ents)} side panels equal their cards; mouse, keyboard and touch checked')


# v2.12.0: moving around the Reef map. VIEW is the map's pan and zoom [tx, ty, k]; EMPTY a point of the map with no bubble or link under it
VIEW = r"(() => /translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)\)/.exec(document.querySelector('#map .vp').getAttribute('transform')).slice(1).map(Number))()"
EMPTY = """() => { const r = document.getElementById('map').getBoundingClientRect(), svg = document.querySelector('#map svg');
  for (let y = r.top + 40; y < Math.min(r.bottom, innerHeight) - 30; y += 7) for (let x = r.left + 30; x < r.right - 30; x += 7) {
    const e = document.elementFromPoint(x, y); if (e === svg) return [x, y]; } return null; }"""
LABEL_CLASH = """() => { const ts = [...document.querySelectorAll('#map .nd text.t')].map(t => t.getBoundingClientRect()); let n = 0;
  for (let i = 0; i < ts.length; i++) for (let k = i + 1; k < ts.length; k++) { const a = ts[i], b = ts[k];
    if (a.right > b.left + 1 && b.right > a.left + 1 && a.bottom > b.top + 2 && b.bottom > a.top + 2) n++; } return n; }"""


def settled(pg):  # the web edition's fonts are in and the map has fitted itself to the box they leave it
    pg.wait_for_function("document.fonts.status === 'loaded'")
    pg.wait_for_timeout(120)


def reef_page(b, page, **kw):
    ctx = b.new_context(**kw)
    pg, errs = ctx.new_page(), []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto(page.as_uri() + '#ent:googlebot')
    pg.wait_for_timeout(900)  # the pop-in is over
    settled(pg)
    return ctx, pg, errs


def mid(pg, sel):
    bb = pg.locator(sel).first.bounding_box()
    return bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2


def reef_mouse(b, page):  # pan, zoom, drag, the preview card, the menu, expand in place, pin, hide, the trail, the living layout
    bad = []
    ctx, pg, errs = reef_page(b, page, viewport={'width': 1440, 'height': 900})
    near = lambda a, c, t=1.5: all(abs(x - y) <= t for x, y in zip(a, c))
    hsh = lambda: pg.evaluate('location.hash')
    count = lambda sel: pg.evaluate(f"document.querySelectorAll('{sel}').length")
    fit = pg.evaluate(VIEW)
    # the wheel zooms round the pointer: the map point under it stays under it; the buttons carry on from there
    m = pg.locator('#map').bounding_box()
    px, py = m['x'] + 300, m['y'] + 260
    under = lambda v: ((px - m['x'] - v[0]) / v[2], (py - m['y'] - v[1]) / v[2])
    pg.mouse.move(px, py)
    pg.mouse.wheel(0, -300)
    pg.wait_for_function(f'() => {VIEW}[2] > {fit[2]} * 1.2')
    v, zl = pg.evaluate(f"[{VIEW}, document.getElementById('zl').textContent]")  # one read: a mouse wheel's zoom glides, and each frame keeps the point still
    if not near(under(v), under(fit), .5): bad.append(f'the wheel does not zoom round the pointer: {fit} -> {v}')
    if zl != f'{round(v[2] * 100)}%': bad.append(f'the zoom level shown is not the zoom of the map: {zl}, {v}')
    pg.wait_for_timeout(400)
    v2 = pg.evaluate(VIEW)
    if not near(under(v2), under(fit), .5) or abs(v2[2] - fit[2] * 1.56831) > .01: bad.append(f'the wheel zoom does not settle round the pointer: {fit} -> {v2}')
    v = v2
    pg.click('[data-z="1"]')
    pg.wait_for_timeout(350)
    if not pg.evaluate(VIEW)[2] > v[2] * 1.2: bad.append('the + button does not zoom in from where the wheel left the map')
    # a double click on the background fits; a drag on the background pans
    pg.mouse.dblclick(*pg.evaluate(EMPTY))
    pg.wait_for_timeout(400)
    if not near(pg.evaluate(VIEW), fit, .5): bad.append(f'a double click on the background does not fit: {pg.evaluate(VIEW)} != {fit}')
    ex, ey = pg.evaluate(EMPTY)
    pg.mouse.move(ex, ey)
    pg.mouse.down()
    for i in range(1, 7): pg.mouse.move(ex + i * 10, ey + i * 7)
    pg.mouse.up()
    pg.wait_for_timeout(100)
    v = pg.evaluate(VIEW)
    if not near(v, [fit[0] + 60, fit[1] + 42, fit[2]]) or hsh() != '#ent:googlebot': bad.append(f'a drag on the background does not pan: {fit} -> {v}, {hsh()}')
    pg.click('[data-z="0"]')
    pg.wait_for_timeout(400)
    # the preview card: on hover (and gone when the pointer leaves), and on keyboard focus
    tgt = '#map .nd.k-entity:not(.centre)'
    name = pg.locator(tgt + ' text.t').first.text_content()
    pg.mouse.move(*mid(pg, tgt + ' .sh'))
    pg.wait_for_timeout(400)
    card = pg.evaluate("[!document.getElementById('peek').hidden, (document.querySelector('#peek .pk-n') || {}).textContent, document.getElementById('peek').textContent]")
    if not card[0] or card[1] != name or 'claim' not in card[2]: bad.append(f'hovering {name} shows no preview card with its name and counts: {card}')
    r = pg.evaluate("(() => { const r = document.getElementById('peek').getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom, innerWidth, innerHeight]; })()")
    if r[0] < 0 or r[1] < 0 or r[2] > r[4] or r[3] > r[5]: bad.append(f'the preview card is off-screen: {r}')
    pg.mouse.move(5, 5)
    pg.wait_for_timeout(100)
    if not pg.evaluate("document.getElementById('peek').hidden"): bad.append('the preview card stays when the pointer leaves')
    pg.focus('#map .nd.centre')
    pg.keyboard.press('Tab')
    pg.wait_for_timeout(100)
    if pg.evaluate("document.getElementById('peek').hidden || document.querySelector('#peek .pk-n').textContent !== document.activeElement.querySelector('text.t').textContent"):
        bad.append('keyboard focus on a bubble shows no preview card')
    # a drag moves a bubble and its links and never recentres; what it pushes makes room; Reset puts it back; a plain click still recentres
    clash = pg.evaluate(LABEL_CLASH)
    t0 = pg.locator(tgt).first.get_attribute('transform')
    x, y = mid(pg, tgt + ' .sh')
    pg.mouse.move(x, y)
    pg.mouse.down()
    for i in range(1, 11):
        pg.mouse.move(x + i * 4, y + i * 9)
        pg.wait_for_timeout(16)
    pg.mouse.up()
    pg.wait_for_timeout(200)
    t1 = pg.locator(tgt).first.get_attribute('transform')
    if t1 == t0 or hsh() != '#ent:googlebot': bad.append(f'a drag did not move the bubble, or recentred: {t0} -> {t1}, {hsh()}')
    if pg.evaluate(LABEL_CLASH) > clash: bad.append(f'after a drag, labels lie on top of each other ({clash} -> {pg.evaluate(LABEL_CLASH)})')
    pg.click('#reset')
    if pg.locator(tgt).first.get_attribute('transform') != t0: bad.append('Reset layout does not put the bubble back')
    j = pg.locator(tgt).first.get_attribute('data-i')
    pg.locator(tgt + ' .sh').first.click()
    pg.wait_for_function('n => document.querySelector("#map .nd.centre").dataset.i === n', arg=j)
    pg.go_back()
    pg.wait_for_function('() => location.hash === "#ent:googlebot"')
    # the menu: right-click, Esc. Expand grows neighbours in place (the centre stays), a grown bubble grows in turn, Collapse folds both;
    # the + on a bubble and the + and - keys do the same; Shift+F10 opens the menu of the focused bubble
    menu = lambda: pg.evaluate("document.getElementById('menu').hidden ? null : [...document.querySelectorAll('#menu [data-act]')].map(b => b.dataset.act)")
    top = '#map .nd.k-topic:not(.centre)'
    pg.locator(top).first.click(button='right')
    acts = menu() or []
    if not {'open', 'centre', 'expand', 'pin', 'hide'} <= set(acts): bad.append(f'the menu of a topic lacks items: {acts}')
    pg.keyboard.press('Escape')
    if menu() is not None: bad.append('Esc does not close the menu')
    pg.locator(top).first.click(button='right')
    pg.click('#menu [data-act=expand]')
    pg.wait_for_timeout(400)
    grown = count('#map .nd.xc')
    if not 0 < grown <= 8 or hsh() != '#ent:googlebot' or 'grown in place' not in pg.locator('#status').text_content(): bad.append(f'Expand grows {grown} bubbles, centre {hsh()}')
    if pg.evaluate(LABEL_CLASH) > clash: bad.append('the bubbles grown in place lie on labels')
    pg.locator('#map .nd.xc.k-entity').first.click(button='right')
    pg.click('#menu [data-act=expand]')
    pg.wait_for_timeout(400)
    if count('#map .nd.xc') <= grown: bad.append('a grown bubble cannot be expanded in turn')
    pg.locator(top).first.click(button='right')
    pg.click('#menu [data-act=collapse]')
    if count('#map .nd.xc'): bad.append('Collapse does not fold back what grew (and what grew from it)')
    pg.focus(top)
    pg.keyboard.press('+')
    n_key = count('#map .nd.xc')
    pg.keyboard.press('Shift+F10')
    if 'collapse' not in (menu() or []): bad.append(f'Shift+F10 does not open the menu of the focused bubble: {menu()}')
    pg.keyboard.press('Escape')
    if not pg.evaluate("document.activeElement.matches('#map .nd.k-topic')"): bad.append('after Esc the focus is not back on the bubble')
    pg.keyboard.press('-')
    if not n_key or count('#map .nd.xc'): bad.append('the + and - keys do not grow and fold a bubble')
    pg.hover(top)
    pg.click(top + ' .xp')
    if not count('#map .nd.xc') or hsh() != '#ent:googlebot': bad.append('the + on a bubble does not grow its neighbours in place')
    pg.locator(top).first.click(button='right')
    pg.click('#menu [data-act=collapse]')
    # Pin keeps a node when recentring, Hide takes one off (and "show" brings it back), Centre here recentres, the trail goes back, Open card opens it
    ids = pg.evaluate(f"[...document.querySelectorAll('{tgt}')].map(g => g.dataset.i)")
    on = lambda i, extra='': f'#map .nd{extra}[data-i="{i}"]'
    pg.locator(on(ids[1])).click(button='right')
    pg.click('#menu [data-act=pin]')
    pg.locator(on(ids[2])).click(button='right')
    pg.click('#menu [data-act=hide]')
    if count(on(ids[2])) or 'hidden by you' not in pg.locator('#status').text_content(): bad.append('Hide does not take the node off the map')
    pg.locator(on(ids[3])).click(button='right')
    pg.click('#menu [data-act=centre]')
    pg.wait_for_function('n => document.querySelector("#map .nd.centre").dataset.i === n', arg=ids[3])
    if not count(on(ids[1], '.pinned')): bad.append('a pinned node is not on the map after recentring')
    pg.locator('#map .nd.k-topic:not(.centre)').first.click()
    pg.wait_for_timeout(300)
    trail = pg.evaluate("[...document.querySelectorAll('#trail a')].map(a => a.getAttribute('href'))")
    if len(trail) < 3 or trail[0] != '#ent:googlebot': bad.append(f'the trail does not list the centres visited: {trail}')
    pg.locator('#trail a').first.click()
    pg.wait_for_function('() => location.hash === "#ent:googlebot" && document.querySelector("#panel h2").textContent === "Googlebot"')
    if pg.evaluate("document.querySelector('#trail a[aria-current]').getAttribute('href')") != '#ent:googlebot': bad.append('the trail does not mark where you are')
    pg.go_back()
    pg.wait_for_function('() => location.hash !== "#ent:googlebot"')
    if pg.evaluate("document.querySelector('#trail a[aria-current]').getAttribute('href')") != pg.evaluate('location.hash'): bad.append('the trail does not follow the back button')
    pg.go_forward()
    pg.wait_for_function('() => location.hash === "#ent:googlebot"')
    if count('#status #unhide'): pg.click('#status #unhide')
    if not count(on(ids[2])): bad.append('"show them" does not bring the hidden node back')
    pg.locator(tgt).first.click(button='right')
    pg.click('#menu [data-act=open]')
    pg.wait_for_url('**/entities/*.html')
    pg.go_back()
    pg.wait_for_function('() => location.hash === "#ent:googlebot" && document.querySelector("#map .nd.centre")')
    # the living layout: off by default, drifts, settles within a few seconds and then asks for no frames at all; off again is the default layout
    pg.reload()
    pg.wait_for_timeout(300)
    layout = "[...document.querySelectorAll('#map .nd')].map(g => g.getAttribute('transform')).join('|')"
    neat = pg.evaluate(layout)
    if pg.evaluate("document.getElementById('map').dataset.sim") != 'off' or pg.get_attribute('#live', 'aria-pressed') != 'false': bad.append('the living layout is not off by default')
    pg.click('#live')
    try: pg.wait_for_function("document.getElementById('map').dataset.sim === 'idle'", timeout=6000)
    except Exception: bad.append('the living layout does not settle within 6 seconds')
    pg.evaluate("(() => { window.__raf = 0; const raf = window.requestAnimationFrame; window.requestAnimationFrame = f => { window.__raf++; return raf(f); }; })()")
    still = pg.evaluate(layout)
    pg.wait_for_timeout(600)
    if pg.evaluate('window.__raf') or pg.evaluate(layout) != still: bad.append(f'the living layout keeps running after it settled ({pg.evaluate("window.__raf")} frames)')
    if still == neat: bad.append('the living layout moved nothing')
    pg.click('#live')
    if pg.evaluate(layout) != neat: bad.append('switching the living layout off does not give the default layout back')
    if errs: bad.append(f'mouse: console errors {errs[:3]}')
    ctx.close()
    return bad


def reef_touch(b, page):  # a phone: a tap previews, a double tap centres, one finger pans, two pinch, a long press opens the menu (touch through CDP)
    bad = []
    ctx, pg, errs = reef_page(b, page, viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True)
    cdp = ctx.new_cdp_session(pg)
    touch = lambda kind, pts: cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in enumerate(pts)]})
    hsh = lambda: pg.evaluate('location.hash')
    pg.touchscreen.tap(*mid(pg, '#map .nd.k-entity:not(.centre) .sh'))
    pg.wait_for_timeout(450)
    if pg.evaluate("document.getElementById('peek').hidden || !document.getElementById('peek').classList.contains('live')") or hsh() != '#ent:googlebot':
        bad.append(f'a tap does not open the preview (or it recentred: {hsh()})')
    pg.touchscreen.tap(*pg.evaluate(EMPTY))
    pg.wait_for_timeout(450)
    if not pg.evaluate("document.getElementById('peek').hidden"): bad.append('a tap on the background does not close the preview')
    v0 = pg.evaluate(VIEW)
    m = pg.locator('#map').bounding_box()
    cx, cy = m['x'] + m['width'] / 2, m['y'] + 200
    touch('touchStart', [(cx - 30, cy), (cx + 30, cy)])
    for i in range(1, 9): touch('touchMove', [(cx - 30 - i * 6, cy), (cx + 30 + i * 6, cy)])
    touch('touchEnd', [])
    pg.wait_for_timeout(200)
    v1 = pg.evaluate(VIEW)
    if not v1[2] > v0[2] * 1.5: bad.append(f'a pinch does not zoom: {v0} -> {v1}')
    pg.click('[data-z="0"]')
    pg.wait_for_timeout(400)
    ex, ey = pg.evaluate(EMPTY)
    v0 = pg.evaluate(VIEW)
    touch('touchStart', [(ex, ey)])
    for i in range(1, 9): touch('touchMove', [(ex + i * 5, ey - i * 8)])
    touch('touchEnd', [])
    pg.wait_for_timeout(500)
    v1 = pg.evaluate(VIEW)
    if abs(v1[0] - v0[0] - 40) > 1.5 or abs(v1[1] - v0[1] + 64) > 1.5 or hsh() != '#ent:googlebot': bad.append(f'one finger does not pan: {v0} -> {v1}, {hsh()}')
    x, y = mid(pg, '#map .nd.k-topic:not(.centre) .sh')
    touch('touchStart', [(x, y)])
    pg.wait_for_timeout(700)
    touch('touchEnd', [])
    pg.wait_for_timeout(450)
    if pg.evaluate("document.getElementById('menu').hidden") or hsh() != '#ent:googlebot': bad.append('a long press does not open the menu')
    pg.keyboard.press('Escape')
    pg.touchscreen.tap(*mid(pg, '#map .nd.k-entity:not(.centre) .sh'))
    pg.wait_for_timeout(450)
    pg.touchscreen.tap(*mid(pg, '#peek [data-act=expand]'))
    pg.wait_for_timeout(600)
    grown = pg.evaluate("document.querySelectorAll('#map .nd.xc').length")
    vis = pg.evaluate("(() => { const m = document.getElementById('map').getBoundingClientRect(), r = document.querySelector('#map .nd.exp .sh').getBoundingClientRect(); return r.top >= m.top && r.bottom <= m.bottom && r.left >= m.left && r.right <= m.right; })()")
    pg.touchscreen.tap(*mid(pg, '#map .nd.exp .sh'))
    pg.wait_for_timeout(450)
    if not grown or not vis or pg.evaluate("document.getElementById('peek').hidden || !document.querySelector('#peek [data-act=collapse]') || !document.querySelectorAll('#map .nd.xc').length"):
        bad.append(f'after Expand on a phone the bubble is out of view ({vis}), or a tap on it does not preview it ({grown} grown)')
    pg.reload()  # what was grown is gone
    pg.wait_for_timeout(900)
    low = pg.evaluate("[...document.querySelectorAll('#map .nd:not(.centre):not(.bundle)')].filter(g => { const r = g.querySelector('.sh').getBoundingClientRect(); return r.top > innerHeight - 200 && r.bottom < innerHeight - 20; }).map(g => g.dataset.i)[0]")
    x, y = mid(pg, f'#map .nd[data-i="{low}"] .sh')
    pg.touchscreen.tap(x, y)
    pg.wait_for_timeout(80)
    pg.touchscreen.tap(x, y)
    try:
        pg.wait_for_function('n => document.querySelector("#map .nd.centre").dataset.i === n', arg=low, timeout=3000)
        pg.go_back()
        pg.wait_for_function('() => location.hash === "#ent:googlebot"')
    except Exception: bad.append('a double tap low on the screen does not centre the bubble (the card of the first tap covers it)')
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(600)
    j = pg.locator('#map .nd.k-entity:not(.centre)').nth(1).get_attribute('data-i')
    x, y = mid(pg, f'#map .nd[data-i="{j}"] .sh')
    pg.touchscreen.tap(x, y)
    pg.wait_for_timeout(80)
    pg.touchscreen.tap(x, y)
    try: pg.wait_for_function('n => document.querySelector("#map .nd.centre").dataset.i === n', arg=j, timeout=3000)
    except Exception: bad.append('a double tap does not centre the bubble')
    if pg.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth'): bad.append('the phone page scrolls sideways')
    if errs: bad.append(f'touch: console errors {errs[:3]}')
    ctx.close()
    return bad

FOLD_CASES = ['Łukasz Straße — Crème-brûlée!', 'ŁUKASZ šimek', 'Dzień', 'Søren Ærø Œuvre Þór', 'İstanbul ıi', 'Martyna Ağanoğlu', 'Alizée Baudez',
              'ΣΟΦΟΣ σοφός', 'مریم سئو', 'Discovered – currently not indexed', 'rel=canonical & X-Robots-Tag', 'robots.txt/llms.txt',
              'E-E-A-T (Experience, Expertise)', 'query fan-out', 'HTTP/2 vs. HTTP/3', '5xx, 429 or 503', 'snake_case_word', 'x²+y³ ½',
              'Ｆｕｌｌｗｉｄｔｈ', 'ﬁnal ﬂow', 'naïve café', '  spaces\tand\nlines  ', '', 'Ǆ ǅ ǆ', 'Ⅻ ⑤', 'ẞ']


def test_fold_python_matches_js():  # knowledge graph phase 0: the build's fold() and the web edition's search fold the same way
    pw_ = browser()
    if not pw_: print('    skipped (Playwright not installed)'); return
    js = (REPO / '_system' / 'site' / 'site.js').read_text(encoding='utf-8')
    src = '\n'.join(re.search(rf'^\s*{pat}.*$', js, re.M)[0] for pat in (r'var SPELL = ', r'function fold\(s\)', r'function norm\(s\)'))
    kb = load_module(REPO / '_system' / 'build_kb.py', 'kb_fold_js')
    site = load_module(REPO / '_system' / 'site' / 'build_site.py', 'site_fold_js')
    with pw_() as pw:
        b = pw.chromium.launch()
        try:
            pg = b.new_page()
            got = pg.evaluate('cases => { ' + src + ' return cases.map(s => [fold(s), norm(s).trim()]); }', FOLD_CASES)
        finally:
            b.close()
    bad = [(s, j, [kb.fold(s), kb.norm_key(s), ' '.join(site.words(s))]) for s, j in zip(FOLD_CASES, got)
           if j != [kb.fold(s), kb.norm_key(s)] or j[1] != ' '.join(site.words(s))]
    assert not bad, bad


def header_overlap(site):
    """Phone widths at which the site title (its text, not its box) reaches the Menu button or the page scrolls sideways."""
    out = []
    with browser()() as pw:
        b = pw.chromium.launch()
        try:
            for width in (320, 360, 375, 390):
                pg = b.new_page(viewport={'width': width, 'height': 700})
                for page in ('index.html', 'days/day-2.html' if (site / 'days' / 'day-2.html').exists() else 'about.html'):
                    pg.goto((site / page).as_uri())
                    r = pg.evaluate("""() => { const m = document.querySelector('.menu-btn').getBoundingClientRect();
                        const right = [...document.querySelectorAll('.brand-t, .brand-k')].flatMap(el => { const g = document.createRange(); g.selectNodeContents(el); return [...g.getClientRects()].map(x => x.right) });
                        return {menu: m.left, text: Math.max(...right), sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth} }""")
                    if r['text'] > r['menu'] or r['sw'] > r['cw']: out.append((width, page, r))
                pg.close()
        finally:
            b.close()
    return out


def copy_real(root, dirs, files):
    """A copy of the real data. It takes the checkout's edition.yaml along, so it builds the edition this checkout builds."""
    for d in dirs: shutil.copytree(REPO / d, root / d, ignore=shutil.ignore_patterns('__pycache__'))
    for f in list(files) + ([EDITION_YAML] if (REPO / EDITION_YAML).exists() else []):
        if f in CODE and not (REPO / f).exists(): continue  # the build reports a missing badges.py itself
        (root / f).parent.mkdir(parents=True, exist_ok=True); shutil.copy(REPO / f, root / f)


SITE_EXTRAS = ('METHOD.md', '_system/brand/video', '_system/brand/social')  # what the community edition's web edition adds when it is there


def copy_site_extras(root):
    """The method write-up, the tour video and its poster, and the share image, as the repository has them: a real-data copy that
    builds the web edition takes them along, so it builds the pages the checkout publishes (the full edition ignores them)."""
    for rel in SITE_EXTRAS:
        src = REPO / rel
        if src.is_dir(): shutil.copytree(src, root / rel, ignore=shutil.ignore_patterns('__pycache__'))
        elif src.is_file(): (root / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(src, root / rel)


def real_copy(name, style=None):  # the real data, built in a fresh copy (style: the default written into its _system/theme.yaml)
    root = TMP / name
    if root.exists(): shutil.rmtree(root)
    copy_real(root, ('20-claims', '25-kits', '_system/templates', '_system/eval'), ('CHANGELOG.md',) + CODE)
    if style: w(root / '_system' / 'theme.yaml', f'default: {style}\n')
    code, out = build(root)
    assert code == 0, out
    return root


def test_agents_guide_citations_match_the_pack():  # OSM-09: the citation examples use public claims with their own label, speaker or author, day and source
    root = real_copy('real-agents')
    P = root / '60-outputs' / 'agent-pack'
    rows = {r['id']: r for r in map(json.loads, (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines())}
    guide = (P / 'AGENTS.md').read_text(encoding='utf-8')
    missing = sorted(set(re.findall(r'\bD\d+-C\d{3}\b', guide)) - rows.keys())
    assert not missing, f'AGENTS.md names claims that are not public claims of the pack: {missing}'
    cites = [[x.strip() for x in c.split(',')] for b in re.findall(r'\[(D\d+-C\d{3},[^\]]*)\]', guide) for c in b.split(';')]
    # a slide or stage claim names a person only where links.json proves it, otherwise its credit group: the form of every cite string
    spk = json.loads((P / 'links.json').read_text(encoding='utf-8'))['speakers']['claims']
    group = {'google': 'Google', 'community': 'a community speaker', 'unattributed': 'a speaker', 'audience': 'an audience member'}
    said = lambda cid: (spk.get(cid) or {}).get('name') or group.get((spk.get(cid) or {}).get('group'), 'a speaker')
    bad = []
    for cid, label, who, *rest in cites:
        r = rows[cid]
        want = ([said(cid), f"Day {r['day']}"] if r['label'] in ('slide', 'stage') else [r['author']]) if label == r['label'] else None
        if want is None or [who] + rest[:len(want) - 1] != want or len(rest) != len(want) - 1 + (label in ('docs', 'press')) \
                or (label in ('docs', 'press') and rest[-1] not in [s['url'] for s in r['sources']]):
            bad.append(f"[{', '.join([cid, label, who] + rest)}] but the pack has label {r['label']}, speaker {said(cid)}, author {r['author']}, day {r['day']}")
    assert not bad, '\n  '.join([''] + bad)
    assert {'slide', 'stage', 'docs', 'analysis'} <= {c[1] for c in cites}, cites
    assert any(c[1] in ('slide', 'stage') and c[2] in group.values() for c in cites), 'no example cites an unproven speaker by its group'


def contrast(a, b):  # WCAG contrast of two CSS rgb() colours
    def lum(c):
        v = [int(x) / 255 for x in re.findall(r'\d+', c)[:3]]
        v = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in v]
        return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]
    x, y = sorted((lum(a), lum(b)))
    return (y + .05) / (x + .05)


MAP_PROBE = """() => { const m = document.getElementById('map'), r = m.getBoundingClientRect(), right = r.left + m.clientLeft + m.clientWidth;
  const box = e => e.getBoundingClientRect(), chip = document.querySelector('#days button[aria-pressed="true"]'), cs = getComputedStyle(chip);
  const clash = [...document.querySelectorAll('#map .node.topic, #map .node.area')].filter(g => { const c = box(g.querySelector('.count'));
    return c.right > right + .5 || [...g.querySelectorAll('text.t')].flatMap(t => t.children.length ? [...t.children] : [t]).some(t => { const b = box(t); return b.right > c.left - 2 && b.bottom > c.top && b.top < c.bottom }) }).map(g => g.textContent);
  const topic = document.querySelector('#map .node.topic text.t'), home = document.getElementById('home');
  return { sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, msw: m.scrollWidth, mcw: m.clientWidth, clash,
    chip: [chip.textContent, chip.matches(':hover'), cs.color, cs.backgroundColor], bg: getComputedStyle(document.body).backgroundColor,
    topic: getComputedStyle(topic).fill, link: getComputedStyle(document.querySelector('#map .link')).stroke,
    home: home && !home.hidden ? home.getAttribute('href') : null, ms: (() => { const t = performance.now(); for (let i = 0; i < 5; i++) render(); return (performance.now() - t) / 5 })() } }"""


DD_PROBE = """() => { const cs = (s, p) => getComputedStyle(document.querySelector(s))[p], tok = n => { const e = document.createElement('i');
  e.style.color = `var(${n})`; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; };
  return { style: document.documentElement.dataset.style, switch: document.querySelectorAll('#styles, [data-s], [data-style-set]').length,
    font: cs('body', 'fontFamily'), link: cs('#map .link', 'stroke'), bg: cs('body', 'backgroundColor'), bg3: tok('--bg3'),
    topic: cs('#map .node.topic:not(.dim) text.t', 'fill'), count: cs('#map .node.topic:not(.dim) .count', 'fill'),
    area: cs('#map .node.area text.t', 'fill'), acount: cs('#map .node.area .count', 'fill'), box: cs('#map .node.area rect.box', 'fill'),
    panel: cs('aside', 'backgroundColor'), body: cs('aside p', 'color'), kicker: cs('aside .k', 'color'),
    h1: cs('header h1', 'color'), bar1: tok('--bar1'), bar2: tok('--bar2'), q: cs('#q', 'color'), qbg: cs('#q', 'backgroundColor') } }"""


def test_mindmap_contrast_layout_dark_mode_and_way_back():  # OSM-05, OSM-06 on the real data (78 topics)
    root = real_copy('real-map')
    page = root / '50-maps' / 'mindmap.html'  # Deep Dive, the default of theme.yaml, with no switch to Art Deco
    deco = real_copy('real-map-deco', 'art-deco') / '50-maps' / 'mindmap.html'  # Art Deco only through theme.yaml and a rebuild
    copy = root / 'shared' / 'site' / 'mindmap.html'  # as the web edition serves it, next to its index.html
    copy.parent.mkdir(parents=True); shutil.copy(page, copy)
    pw = browser()
    if pw is None: print('    browser check: skipped (Playwright not installed)'); return
    bad = []
    with pw() as p:
        b = p.chromium.launch()
        try:
            for (wd, ht) in ((1280, 900), (1366, 900), (390, 844)):
                for scheme in ('light', 'dark'):
                    ctx = b.new_context(viewport={'width': wd, 'height': ht}, color_scheme=scheme)
                    pg, errs, at = ctx.new_page(), [], f'{wd}px {scheme}'
                    pg.on('pageerror', lambda e: errs.append(str(e)))
                    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                    pg.goto(deco.as_uri())  # these checks are the Art Deco look, built with theme.yaml art-deco; Deep Dive is checked below
                    want = load_module(deco.parents[1] / '_system' / 'theme.py', 'theme_map').default_style()
                    if want != 'art-deco' or pg.evaluate("document.documentElement.dataset.style") != want: bad.append(f'{at}: the map does not open in art-deco, the default of its theme.yaml')
                    if 'diverbot' in pg.evaluate("document.querySelector('link[rel=icon]').href"): bad.append(f'{at}: the Art Deco build has the Deep Dive tab icon')
                    pg.locator('#days button', has_text='Day 2').click()
                    pg.locator('#days button', has_text='Day 2').hover()  # OSM-05: the pressed chip under the pointer
                    r = pg.evaluate(MAP_PROBE)
                    if r['sw'] > r['cw']: bad.append(f'{at}: the page scrolls sideways ({r["sw"]} > {r["cw"]})')
                    if r['msw'] > r['mcw'] or r['clash']: bad.append(f'{at}: count labels clipped or overlapping: {r["clash"][:3]} (map {r["msw"]} > {r["mcw"]})')
                    if r['chip'][:2] != ['Day 2', True] or contrast(*r['chip'][2:]) < 4.5: bad.append(f'{at}: pressed chip under the pointer: {r["chip"]}')
                    if (r['bg'], r['topic']) != (('rgb(26, 23, 18)', 'rgb(247, 241, 227)') if scheme == 'dark' else ('rgb(247, 241, 227)', 'rgb(29, 26, 22)')) \
                            or r['link'] != 'rgb(176, 141, 58)': bad.append(f'{at}: palette {r["bg"]}, {r["topic"]}, {r["link"]}')
                    if r['home'] != '../60-outputs/site/index.html': bad.append(f'{at}: link back to the web edition is {r["home"]}')
                    if r['ms'] > 150: bad.append(f'{at}: a redraw takes {r["ms"]:.0f} ms')
                    g = pg.locator('#map .node.topic:not(.dim)').first
                    title = (g.get_attribute('aria-label') or g.locator('text.t').text_content() + ':').rsplit(':', 1)[0]  # keyboard: a topic is a button
                    g.focus(); pg.keyboard.press('Enter')
                    days = pg.evaluate("() => [...document.querySelectorAll('#panel .claim .m')].map(m => (m.textContent.match(/Day \\d+/) || [''])[0])")
                    if pg.locator('#panel h2').text_content() != title or not days or set(days) != {'Day 2'}: bad.append(f'{at}: Enter on {title} showed {days[:3]}')
                    if errs: bad.append(f'{at}: console errors {errs[:3]}')
                    ctx.close()
            for (wd, ht) in ((1280, 900), (390, 844)):  # the Deep Dive style, the build's (theme.yaml): no switch, and a stale 'kb-style' changes nothing
                for scheme in ('light', 'dark'):
                    ctx = b.new_context(viewport={'width': wd, 'height': ht}, color_scheme=scheme)
                    pg, errs, at = ctx.new_page(), [], f'Deep Dive {wd}px {scheme}'
                    pg.on('pageerror', lambda e: errs.append(str(e)))
                    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                    pg.goto(page.as_uri())
                    if 'diverbot-head' not in pg.evaluate("document.querySelector('link[rel=icon]').href"): bad.append(f'{at}: the tab icon is not the Diver bot')
                    pg.evaluate("localStorage.setItem('kb-style', 'art-deco')")  # the choice an older version kept
                    pg.reload()
                    pg.locator('#days button', has_text='Day 2').click()
                    pg.locator('#days button', has_text='Day 2').hover()
                    r, d = pg.evaluate(MAP_PROBE), pg.evaluate(DD_PROBE)
                    if d['style'] != 'deep-dive' or d['switch']: bad.append(f'{at}: not Deep Dive only (a stale kb-style=art-deco in the browser): {d["style"]}, {d["switch"]} switch controls')
                    if r['sw'] > r['cw']: bad.append(f'{at}: the page scrolls sideways ({r["sw"]} > {r["cw"]})')
                    if r['msw'] > r['mcw'] or r['clash']: bad.append(f'{at}: count labels clipped or overlapping: {r["clash"][:3]}')
                    if r['chip'][:2] != ['Day 2', True] or contrast(*r['chip'][2:]) < 4.5: bad.append(f'{at}: pressed chip under the pointer: {r["chip"]}')
                    if 'Figtree' not in d['font'] or d['link'] in ('rgb(176, 141, 58)', r['bg']): bad.append(f'{at}: not the Deep Dive look: {d["font"]}, link {d["link"]}')
                    for name, fg, bgs in (('topic', d['topic'], (d['bg'], d['bg3'])), ('count', d['count'], (d['bg'], d['bg3'])), ('area', d['area'], (d['box'],)),
                                          ('area count', d['acount'], (d['box'],)), ('panel text', d['body'], (d['panel'],)), ('panel kicker', d['kicker'], (d['panel'],)),
                                          ('title', d['h1'], (d['bar1'], d['bar2'])), ('filter', d['q'], (d['qbg'],))):
                        low = [round(contrast(fg, x), 2) for x in bgs if contrast(fg, x) < 4.5]
                        if low: bad.append(f'{at}: {name} {fg} on {bgs}: contrast {low}')
                    g = pg.locator('#map .node.topic:not(.dim)').first
                    g.focus(); pg.keyboard.press('Enter')
                    tags = pg.evaluate("() => [...document.querySelectorAll('#panel .tag')].map(t => [t.textContent, getComputedStyle(t).color, getComputedStyle(t).backgroundColor])")
                    low = sorted({t[0] for t in tags if contrast(t[1], t[2]) < 4.5})
                    if not tags or low: bad.append(f'{at}: label tags below 4.5:1: {low}')
                    if errs: bad.append(f'{at}: console errors {errs[:3]}')
                    ctx.close()
            pg = b.new_page()
            pg.goto(copy.as_uri())
            if pg.evaluate("(document.getElementById('home') || {getAttribute: () => null}).getAttribute('href')") != 'index.html': bad.append('the copy in the web edition does not link to index.html')
        finally:
            b.close()
    assert not bad, '\n  '.join([''] + bad)


# ---------------------------------------------------------------- developer and content kits: 25-kits/ -> 60-outputs/dev, content, agent pack
def test_kits_render():
    kits = load_module(REPO / '_system' / 'kits.py', 'kits_render')
    root = make_fixture('kits')
    code, out = build(root)
    assert code == 0 and 'OK: kits: 3 requirements in 1 area (1 MUST, 1 AVOID), 1 snippet; 2 facts, 1 myth, 1 angle, 1 quote, 2 glossary terms.' in out, out
    D, C, P = (root / '60-outputs' / x for x in ('dev', 'content', 'agent-pack'))
    assert sorted(p.name for p in D.iterdir()) == ['README.md', 'differences.md', 'implementation-guide.md', 'pre-launch-checklist.md', 'requirements.csv', 'snippets.md']
    assert sorted(p.name for p in C.iterdir()) == ['README.md', 'content-library.json', 'fact-sheet.md', 'glossary.md', 'myths-and-facts.md', 'questions.json', 'questions.md',
                                                   'quotes.md', 'story-angles.md']
    rows = list(csv.DictReader(io.StringIO((D / 'requirements.csv').read_text(encoding='utf-8'), newline='')))
    assert [r['id'] for r in rows] == ['DEV-CRA-01', 'DEV-CRA-02', 'DEV-CRA-03'] and list(rows[0])[:4] == ['id', 'area', 'level', 'title'], rows[:1]
    assert rows[0]['claims'] == 'D1-C001; D1-C006' and rows[0]['docs'] == 'https://developers.google.com/crawling/docs/crawl-budget' and rows[1]['status'] == 'event-only'
    assert '\n- answer 503 when the server is overloaded' in rows[0]['how'] and rows[0]['snippet'] == 'Canonical link element'
    cl = (D / 'pre-launch-checklist.md').read_text(encoding='utf-8')
    assert '- [ ] **MUST** `DEV-CRA-01` Keep crawl capacity healthy' in cl and '- [ ] **AVOID** `DEV-CRA-02`' in cl and 'DEV-CRA-03' not in cl and '*(said at Search Central Live)*' in cl
    g = (D / 'implementation-guide.md').read_text(encoding='utf-8')
    anchors = re.findall(r'\(implementation-guide\.md#([^)]+)\)', cl + (D / 'README.md').read_text(encoding='utf-8'))
    heads = {kits.anchor(h) for h in re.findall(r'^#+ (.+)$', g, re.M)}
    assert len(anchors) == 3 and set(anchors) <= heads, (anchors, sorted(heads))
    assert '### DEV-CRA-01 Keep crawl capacity healthy' in g and '```html\n<link rel="canonical"' in g and '- `D1-C001` Shown on a slide, Day 1 (Google), confirmed by Google docs:' in g
    assert "- `D1-C006` Google's documentation (Google):" in g and '[Crawl budget guide](https://developers.google.com/crawling/docs/crawl-budget)' in g
    assert '- `D2-C001` Said on stage, Day 2 (Google), not in Google docs:' in g and '**AVOID** · *Said at Search Central Live*' in g
    assert 'Used by: `DEV-CRA-01`.' in (D / 'snippets.md').read_text(encoding='utf-8')
    assert (C / 'content-library.json').read_bytes() == (P / 'content-library.json').read_bytes()
    lib = json.loads((C / 'content-library.json').read_text(encoding='utf-8'))
    assert list(lib) == ['version', 'data_through', 'event', 'wording_rules', 'statuses', 'facts', 'myths', 'quotes', 'angles', 'glossary'] and lib['version'] == 'v9.9.9'
    q = lib['quotes'][0]
    assert (q['quote'], q['speaker'], q['credit'], q['quote_checked'], q['claim']) == ('Crawl Budget = Crawl Rate Limit & Crawl Demand', None, 'Google at Test Event (Day 1)', True, 'D1-C001'), q
    f2 = lib['facts'][1]['claims'][0]
    assert (f2['speaker'], f2['credit'], f2['verification']) == ('Martin Splitt', 'Google at Test Event (Day 2)', 'undocumented'), f2
    assert lib['facts'][0]['claims'][1]['credit'] == 'Google' and lib['facts'][0]['claims'][1]['speaker'] is None
    assert [p['status'] for p in lib['angles'][0]['points']] == ['documented', 'event-only'] and [t['term'] for t in lib['glossary']] == ['canonical URL', 'Crawl budget']
    dj = json.loads((P / 'dev-requirements.json').read_text(encoding='utf-8'))
    r1 = dj['areas'][0]['requirements'][0]
    assert r1['snippet'] == 'canonical-link' and dj['snippets'][0]['used_by'] == ['DEV-CRA-01'] and dj['snippets'][0]['code'][0]['lang'] == 'html'
    assert [d['key'] for d in r1['docs']] == ['crawl-guide'] and [c['id'] for c in r1['claims']] == ['D1-C001', 'D1-C006'] and dj['areas'][0]['intro'] == 'How Google crawls.\nSecond line of the intro.'
    ix = (P / 'INDEX.md').read_text(encoding='utf-8')
    assert '`dev-requirements.json`' in ix and '`content-library.json`' in ix and 'dev-requirements.json' in (P / 'AGENTS.md').read_text(encoding='utf-8')
    for d in (D, C):
        for f in d.glob('*.md'):  # a README opens with its breadcrumb, then the comment
            txt = f.read_text(encoding='utf-8')
            assert (txt.split('\n')[2] if f.name == 'README.md' else txt).startswith('<!-- GENERATED by _system/kits.py'), f
    st = (C / 'story-angles.md').read_text(encoding='utf-8')
    assert '1. The formula on the slide. *(Documented: `D1-C001`)*' in st and '2. Said again on Day 2. *(Said at Search Central Live: `D2-C001`)*' in st and '**Caution:** The Day 2 repeat' in st
    qm = (C / 'quotes.md').read_text(encoding='utf-8')
    assert '> "Crawl Budget = Crawl Rate Limit & Crawl Demand"' in qm and 'Credit: Google at Test Event (Day 1)\n' in qm and 'Named speaker' not in qm


def test_kits_replace_the_old_briefs():
    root = make_fixture('kits-briefs', [('60-outputs/content/briefs.md', None, '# Content briefs\n\n## 1. One\n\n## 2. Two (D1-C007)\n')])
    code, out = build(root)
    assert code == 0 and 'WARNING: 60-outputs/content/briefs.md (2 briefs) is replaced by the angles of 25-kits/content.yaml (1)' in out, out
    assert not (root / '60-outputs' / 'content' / 'briefs.md').exists() and (root / '60-outputs' / 'content' / 'story-angles.md').exists()


def test_kits_are_required():
    root = make_fixture('kits-missing')
    shutil.rmtree(root / '25-kits')
    code, out = build(root, '--check')
    assert code != 0 and '25-kits/dev-requirements.yaml: file missing' in out and '25-kits/content.yaml: file missing' in out and 'Traceback' not in out, out


def test_kit_credits_and_proven_names():  # who said it: a name only on proof; otherwise "Google" or "a community speaker"
    k = load_module(REPO / '_system' / 'kits.py', 'kits_who')
    S = {'T': {'speaker': 'Gary Illyes'}, 'I': {'speaker': 'John Mueller', 'role': 'Search Relations (speaker inferred)'},
         'L': {'speaker': ['Erin Sparling', 'Sören Bendig', 'a community speaker'], 'kind': 'lightning', 'note': "Rebecca Yu's name inferred from the host."},
         'P': {'speaker': ['Google', 'Gary Illyes'], 'kind': 'panel'}, 'E': {'speaker': 'Erin Sparling'}, 'C': {'speaker': 'Community speakers', 'kind': 'lightning'},
         'Y': {'speaker': ['Rebecca Yu', 'Sören Bendig'], 'kind': 'lightning', 'note': "Rebecca Yu's name inferred from the host."}, 'Z': {'speaker': ''}}
    names, google = k.people(S)
    assert google == {'Gary Illyes', 'John Mueller', 'Erin Sparling'} and names == google | {'Sören Bendig', 'Rebecca Yu'}, (names, google)
    c = lambda s, label='stage', who=None: dict(s=s, label=label, **({'who': who} if who else {}))
    cases = [(c('T'), None, 'Google'), (c('T', who='Gary Illyes'), 'Gary Illyes', 'Google'), (c('I'), None, 'Google'), (c('I', who='John Mueller'), None, 'Google'),
             (c('L', who='Sören Bendig'), 'Sören Bendig', 'a community speaker'), (c('L', who='Erin Sparling'), 'Erin Sparling', 'Google'),
             (c('L', who='a community speaker'), None, 'a community speaker'), (c('L', 'slide'), None, 'a speaker'), (c('C', 'slide'), None, 'a community speaker'),
             (c('Y', who='Rebecca Yu'), None, 'a community speaker'), (c('P'), None, 'Google'), (c('P', who='Google'), None, 'Google'),
             (c('P', who='Gary Illyes'), 'Gary Illyes', 'Google'), (c('T', who='audience'), None, 'an audience member'), (c('T', who='unknown'), None, 'Google'),
             (c('T', 'analysis'), None, 'the author'), (c('Z'), None, 'a speaker'), (c('Z', 'slide'), None, 'a speaker'),
             (c('Z', who='Gary Illyes'), 'Gary Illyes', 'Google'), (c('Z', who='Ann Other'), 'Ann Other', 'a speaker')]
    bad = [(x, k.proven(x, S), k.who_short(x, S, google, {})) for x, name, who in cases if (k.proven(x, S), k.who_short(x, S, google, {})) != (name, who)]
    assert not bad, bad


def test_kit_point_grades():  # an angle point on documented claims plus event claims the docs do not back is "Partly documented"
    k = load_module(REPO / '_system' / 'kits.py', 'kits_grade')
    d, u, n = dict(label='slide', ver='confirmed'), dict(label='stage', ver='undocumented'), dict(label='slide', ver='n/a')
    q, docs, an, pr = dict(label='stage', ver='n/a', who='audience'), dict(label='docs', ver='source'), dict(label='analysis', ver='n/a'), dict(label='press', ver='source')
    got = [k.grade_point(x) for x in ([d], [d, u], [docs, n], [docs, q], [u], [an], [docs, an], [pr], [u, pr])]
    assert got == ['documented', 'mixed', 'mixed', 'documented', 'event-only', 'analysis', 'documented', 'press', 'event-only'], got
    assert k.GRADES['mixed'][0] == 'Partly documented' and {'podcast', 'infographic'} <= set(k.FORMATS)


def test_kit_snippets_are_checked_code():
    k = load_module(REPO / '_system' / 'kits.py', 'kits_snip')
    E, W = [], []
    s = k.parse_snippet('# Two blocks\n\nFirst the tag.\n\n```html\n<meta name="robots" content="noindex">\n```\n\nOr as a header:\n\n````http\nX-Robots-Tag: noindex\n````\n', 'x.md', E, W)
    assert not E and not W and s['title'] == 'Two blocks' and s['text'] == 'First the tag.' and [b['note'] for b in s['code']] == ['', 'Or as a header:'], (E, W, s)
    for src, err in (('# X\n\n```xml\n<urlset><url></urlset>\n```\n', 'the XML is not well-formed'), ('# X\n\n```json\n{"a": 1,}\n```\n', 'the JSON is not valid'),
                     ('# X\n\ntext\n', 'no fenced code block'), ('# X\n\n```html\n\n```\n', 'code block 1: empty')):
        E = []
        k.parse_snippet(src, 'x.md', E, [])
        assert any(err in x for x in E), (src, E)
    assert k.fence('a ``` b') == '````\na ``` b\n````' and k.anchor('DEV-REN-01 Use `<a href>` links, not buttons (SPA)') == 'dev-ren-01-use-a-href-links-not-buttons-spa'


def test_site_kit_pages():  # the two kit sections of the web edition: built, linked, filtered, offline, no console error
    root = site_fixture()
    O = root / '60-outputs' / 'site'
    pages = ['dev/index.html', 'dev/checklist.html', 'dev/snippets.html', 'dev/differences.html'] + [f'content/{x}.html' for x in ('index', 'facts', 'myths', 'angles', 'quotes', 'glossary', 'numbers', 'questions')]
    html = {p: (O / p).read_text(encoding='utf-8') for p in pages}
    ix = (O / 'index.html').read_text(encoding='utf-8')
    assert 'href="dev/index.html">Developers</a>' in ix and 'href="content/index.html">Content</a>' in ix and 'id="kits">Put it to work' in ix
    dev = html['dev/index.html']
    assert dev.count('<article class="req"') == 3 and 'data-level="MUST"' in dev and 'data-status="event-only"' in dev and '&lt;link rel=&quot;canonical&quot;' in dev
    assert 'aria-current="page">Developers</a>' in dev and 'href="../claims.html#D1-C001"' in dev and '<li>answer 503 when the server is overloaded</li>' in dev
    assert html['dev/checklist.html'].count('type="checkbox" value="DEV-') == 2 and 'DEV-CRA-03' not in html['dev/checklist.html']
    for f in ('requirements.csv', 'dev-requirements.json', 'content-library.json'): assert (O / 'downloads' / f).exists(), f
    assert 'href="../downloads/requirements.csv"' in dev and 'href="../downloads/content-library.json"' in html['content/index.html']
    assert 'Speaker</span>' not in html['content/quotes.html'] and 'Google at Test Event (Day 1)' in html['content/quotes.html']
    for p, t in html.items(): assert 'SECRETPRIVATEMARKER' not in t and 'D1-C007' not in t, p
    pw_ = browser()
    if not pw_: print('    browser check: skipped (Playwright not installed)'); return
    bad = []
    with pw_() as pw:
        b = pw.chromium.launch()
        try:
            for w in (1280, 390):
                for scheme in ('light', 'dark'):
                    ctx = b.new_context(viewport={'width': w, 'height': 900}, color_scheme=scheme)
                    pg, errs = ctx.new_page(), []
                    pg.on('pageerror', lambda e: errs.append(str(e)))
                    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                    pg.on('requestfailed', lambda r: errs.append('failed ' + r.url))
                    for p in pages:
                        pg.goto((O / p).as_uri())
                        r = pg.evaluate("() => [document.documentElement.scrollWidth, document.documentElement.clientWidth, document.querySelectorAll('.kit-filter[hidden], .copyable .copy[hidden]').length]")
                        if r[0] > r[1] or r[2]: bad.append(f'{w}px {scheme} {p}: sideways scroll or a control left hidden {r}')
                    if errs: bad.append(f'{w}px {scheme}: {errs[:3]}')
                    ctx.close()
            pg = b.new_page(viewport={'width': 1280, 'height': 900})
            pg.goto((O / 'index.html').as_uri())
            if pg.evaluate("() => document.querySelector('.site-nav ul').getBoundingClientRect().height") > 60: bad.append('the menu wraps onto a second line at 1280px')
            pg.goto((O / 'dev/index.html').as_uri())
            pg.uncheck('.kit-filter input[value=MUST]')
            shown = pg.evaluate("() => [[...document.querySelectorAll('.req')].filter(x => !x.hidden).map(x => x.id), document.querySelector('.filter-n').textContent]")
            if shown != [['DEV-CRA-02', 'DEV-CRA-03'], '2 of 3 requirements shown']: bad.append(f'level filter: {shown}')
            pg.goto((O / 'dev/checklist.html').as_uri())
            pg.check('#checklist input[value=DEV-CRA-02]')
            pg.reload()
            st = pg.evaluate("() => [document.querySelector('#checklist input[value=DEV-CRA-02]').checked, document.getElementById('cl-progress').textContent]")
            if st != [True, '1 of 2 ticked']: bad.append(f'checklist: {st}')
            pg.goto((O / 'content/angles.html').as_uri())
            pg.uncheck('.kit-filter input[value=linkedin]')
            pg.uncheck('.kit-filter input[value=article]')
            if pg.evaluate("() => document.querySelector('.filter-n').textContent") != '0 of 1 angle shown': bad.append('the format filter does not hide the angle')
        finally:
            b.close()
    assert not bad, '\n  '.join([''] + bad)


# ---------------------------------------------------------------- README badges (_system/badges.py) and the generated folder READMEs
GEN_READMES = ['30-topics/README.md', '40-sessions/README.md', '50-maps/README.md', '60-outputs/README.md', '60-outputs/dev/README.md',
               '60-outputs/content/README.md', '60-outputs/agent-pack/INDEX.md']
IN_BUILD = tuple(d + '/' for d in SHARED) + tuple(SHARED_FILES)  # a link into these must resolve in the build itself
CODE_SPAN = re.compile(r'(`+)(?!`).*?(?<!`)\1(?!`)', re.S)


def generated_readmes(root):
    return [root / GEN_READMES[0]] + sorted((root / '30-topics').glob('*/README.md')) + [root / r for r in GEN_READMES[1:]]


def exists_exact(base, rel):
    """rel ('a/b/c', a folder may end in '/') exists under base with exactly this case: Windows is case-blind, GitHub is not."""
    p = base
    for part in [x for x in rel.split('/') if x]:
        if not p.is_dir() or part not in os.listdir(p): return False
        p = p / part
    return True


def outside_code(md_text):
    return CODE_SPAN.sub('', FENCED.sub('', md_text))


def heading_anchors(md_text):  # the ids GitHub gives the headings of a Markdown file
    out = set()
    for h in re.findall(r'^#{1,6} (.+)$', FENCED.sub('', md_text), re.M):
        h = html.unescape(re.sub(r'\\(.)', r'\1', re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', h).replace('`', '').replace('*', '')))
        out.add(re.sub(r'[^\w\- ]', '', h.strip().lower()).replace(' ', '-'))
    return out


def readme_problems(root):
    """Every generated README: the shared pattern (breadcrumb on line 1, generated comment, title, divider, "What's here", generated
    note, centred navigation; INDEX.md of the agent pack keeps its own machine-friendly layout), no HTML but the fixed lines, no style,
    class or script, and every link, image and anchor relative and resolving with exact case: in this build for generated files, in
    the repository for the hand-written ones."""
    bad, web = [], {}
    if built_edition(root) == 'community':  # its media kit README shows the preview with Google's pages, and the company and LinkedIn
        ed = load_module(root / '_system' / 'edition.py', 'edition_readmes').load(root)
        web['60-outputs/content/README.md'] = re.compile(r'https://(developers\.google\.com|support\.google\.com|ai\.google\.dev|blog\.google|www\.youtube\.com)/\S*|'
                                                         + '|'.join(re.escape(u) for u in (ed['company']['url'], ed['linkedin']) if u))
    for p in generated_readmes(root):
        rel = p.relative_to(root).as_posix()
        if not p.exists(): bad.append(f'{rel}: missing'); continue
        txt = p.read_text(encoding='utf-8')
        lines = txt.split('\n')
        if not rel.endswith('INDEX.md'):
            if not re.fullmatch(r'\[Knowledge base\]\((\.\./)+README\.md\)( / \[[^\]]+\]\([^)\s]+\))* / \*\*[^*]+\*\*', lines[0]): bad.append(f'{rel}: line 1 is not the breadcrumb: {lines[0][:90]}')
            if not lines[2].startswith('<!-- GENERATED by _system/') or not lines[4].startswith('# '): bad.append(f'{rel}: no generated comment on line 3 and title on line 5')
            for want in ("\n## What's here\n", '\n> [!NOTE]\n> **Generated** by ', ' and run `rebuild.bat`.', '\n<div align="center">\n\n<sub>', '</sub>\n\n</div>\n'):
                if want not in txt: bad.append(f'{rel}: no {want.strip()!r}')
            if txt.count('_system/brand/divider.svg') != 2 or not txt.rstrip('\n').endswith('</div>'): bad.append(f'{rel}: needs one divider under the lead and one above the closing navigation')
            pics = [(i, PICTURE_LINE.fullmatch(l)) for i, l in enumerate(lines) if l.startswith('<picture>')]
            want = Path(rel).parent.as_posix().replace('/', '-')
            div = next((i for i, l in enumerate(lines) if 'divider.svg' in l), 0)
            if len(pics) != 1 or not pics[0][1] or pics[0][1][2] != want or pics[0][1][1] != '../' * rel.count('/'):
                bad.append(f'{rel}: needs exactly one header illustration, {want}-light.svg / -dark.svg')
            elif not (6 < pics[0][0] < div and lines[pics[0][0] - 1] == '' and lines[pics[0][0] + 1] == '' and pics[0][0] + 2 == div):
                bad.append(f'{rel}: the header illustration belongs between the lead and the first divider')
        if raw_html(txt): bad.append(f'{rel}: raw HTML {raw_html(txt)[:2]}')
        if re.search(r'style\s*=|class\s*=|<\s*script', outside_code(txt), re.I): bad.append(f'{rel}: style=, class= or <script')
        for t in re.findall(r'\]\(([^)\s]+)\)', outside_code(txt)) + re.findall(r'<img [^>]*?src="([^"]*)"', txt) + re.findall(r'srcset="([^"]*)"', txt):
            if rel in web and web[rel].fullmatch(t): continue
            if re.match(r'[A-Za-z][A-Za-z0-9+.-]*:|/', t): bad.append(f'{rel}: {t} is not a relative link'); continue
            path, _, frag = t.partition('#')
            tgt, base = rel, root
            if path:
                tgt = os.path.normpath(os.path.join(os.path.dirname(rel), path)).replace('\\', '/') + ('/' if path.endswith('/') else '')
                base = root if tgt.startswith(IN_BUILD) else REPO
                if tgt.startswith('..'): bad.append(f'{rel}: {t} leaves the repository'); continue
                if not exists_exact(base, tgt): bad.append(f'{rel}: {t} does not resolve' + (' in the repository' if base == REPO else '')); continue
            if frag and tgt.endswith('.md') and frag not in heading_anchors((base / tgt).read_text(encoding='utf-8')): bad.append(f'{rel}: no heading for #{frag} in {tgt}')
    return bad


def test_generated_readmes_follow_the_pattern():
    root = make_fixture('readmes')
    code, out = build(root)
    assert code == 0, out
    bad = readme_problems(root)
    assert not bad, '\n  '.join([''] + bad)
    r = lambda rel: (root / rel).read_text(encoding='utf-8')
    tp, ses, outp, area1, area2 = r('30-topics/README.md'), r('40-sessions/README.md'), r('60-outputs/README.md'), r('30-topics/crawling/README.md'), r('30-topics/indexing/README.md')
    assert tp.startswith('[Knowledge base](../README.md) / **30-topics**\n\n<!-- GENERATED by _system/build_kb.py.') and '\n# Topics\n' in tp
    assert '| [Crawling](crawling/README.md) | 1 | 6 | 1 · 2 | How Google crawls. |' in tp, tp
    assert '| [Crawl budget](crawling/crawl-budget.md) | 6 | 1 · 2 | 3 |' in tp and '| [Nothing yet](indexing/empty-topic.md) | 0 | — | 0 |' in tp, tp
    assert '| [Canonicals](canonical.md) | 3 | 2 | 1 |' in area2 and 'SECRETPRIVATEMARKER' not in tp + area1 + area2
    assert '← [25-kits](../25-kits/README.md) · [40-sessions](../40-sessions/README.md) →' in tp
    assert '\n<sub>[All topics](../README.md) · [Indexing](../indexing/README.md) →</sub>\n' in area1, area1[-300:]
    assert '\n<sub>← [Crawling](../crawling/README.md) · [All topics](../README.md)</sub>\n' in area2, area2[-300:]
    assert area1.startswith('[Knowledge base](../../README.md) / [30-topics](../README.md) / **crawling**\n') and '\n**How Google crawls.**\n' in area1
    assert ('\n**How Google crawls.**\n\n<picture><source media="(prefers-color-scheme: dark)" srcset="../../_system/brand/illustrations/30-topics-crawling-dark.svg">'
            '<img src="../../_system/brand/illustrations/30-topics-crawling-light.svg" width="100%" alt="The Diver bot follows ') in area1, area1[:900]
    assert '\n<picture><source media="(prefers-color-scheme: dark)" srcset="../_system/brand/illustrations/30-topics-dark.svg">' in tp
    assert all(f'illustrations/{s}-dark.svg' in r(f'{d}/README.md') for s, d in (('40-sessions', '40-sessions'), ('50-maps', '50-maps'), ('60-outputs', '60-outputs'),
                                                                                 ('60-outputs-dev', '60-outputs/dev'), ('60-outputs-content', '60-outputs/content')))
    assert '| [Day 3](#day-3--serving) | 2026-10-02 | Serving | 0 | 0 | 0 |' in ses and '## Day 3 · Serving\n\n2026-10-02 · Not added yet.' in ses, ses
    assert '| 11:00 | [Q&A](day1/D1-S02-q-a.md) | Gary Illyes, Cherry Prommawin | Q&A | Notes, Transcript | 2 |' in ses
    assert '| — | [Day 1, session not recorded](day1/D1-S00-day-1-session-not-recorded.md) | — | Not recorded | Notes | 1 |' in ses
    assert '| [Day 1](#day-1--crawling) | 2026-09-30 | Crawling | 3 | 2 | 6 |' in ses and '[PRIVACY.md](../PRIVACY.md)' in ses, ses
    assert '← [50-maps](../50-maps/README.md) · [70-private](../70-private/README.md) →' in outp and '| `claims.svg` | 8 public claims;' in outp, outp
    assert '| `days.svg` | 2 of 3 event days have claims |' in outp and '| `topics.svg` | 3 topics |' in outp and '| `sources.svg` | 2 sources:' in outp
    assert '| `dev-kit.svg` | 3 requirements in the developer kit |' in outp and '| `media-kit.svg` | 2 facts in the media kit |' in outp
    # docs-backed: slide and stage claims graded confirmed (D1-C001), consistent (D1-C003) or undocumented (D2-C001): 2 of 3
    assert '| `docs-backed.svg` | 67% of the slide and stage claims' in outp and '| `version.svg` | v9.9.9, data through 2026-10-01:' in outp
    assert sorted(p.name for p in (root / '60-outputs' / 'badges').iterdir()) == sorted(f'{n}.svg' for n in BADGES)
    assert '\n## Badges\n\n<p align="center"><img src="badges/version.svg" ' in outp and all(f'src="badges/{n}.svg"' in outp for n in BADGES)
    assert not [rel for rel in GEN_READMES if rel != '60-outputs/README.md' and 'badges/' in r(rel)], 'badges belong to 60-outputs/README.md only'
    maps = r('50-maps/README.md')
    for f in ('topic-tree.md', 'mindmap.html', 'mindmap.markmap.md', 'mention-matrix.md', 'mention-matrix.csv', 'verification-report.md', 'across-days.md'):
        assert f'({f})' in maps, f
    ix = r('60-outputs/agent-pack/INDEX.md')
    assert ix.startswith('# Search Central Live Deep Dive Europe 2026 — knowledge base index\n\nVersion v9.9.9 · data through 2026-10-01 (Day 2).') and '_system/brand' not in ix
    for kit, back, nxt in (('dev', 'Field guides', 'Media kit'), ('content', 'Developer kit', 'Agent pack')):
        t = r(f'60-outputs/{kit}/README.md')
        assert t.startswith(f'[Knowledge base](../../README.md) / [60-outputs](../README.md) / **{kit}**\n') and f'← [{back}](' in t and f'[{nxt}](' in t, t[:300]


README_PAYLOAD = '<p align="center" style="color:red" class="x"><img src=x onerror=alert(1)></p>'


def test_readme_html_comes_only_from_the_fixed_lines():
    """Data in a README (area titles and blurbs, themes, speakers, the event name, kit text) is Markdown text, never HTML, and the
    scanner that allows the fixed README lines still catches anything else."""
    root = make_fixture('readme-html', [
        ('20-claims/topics.yaml', 'blurb: How Google crawls.', 'blurb: ' + json.dumps(README_PAYLOAD)),
        ('20-claims/topics.yaml', 'title: Crawling\n    blurb', 'title: ' + json.dumps('<div align="center">') + '\n    blurb'),
        ('20-claims/sessions.yaml', 'theme: Indexing', 'theme: ' + json.dumps('</div><script>alert(1)</script>')),
        ('20-claims/sessions.yaml', 'name: Test Event', 'name: ' + json.dumps('Test <img src=y onerror=alert(2)> Event')),
        ('20-claims/sessions.yaml', 'speaker: "Gary Illyes", coverage: slides}', 'speaker: "Gary Illyes", role: ' + json.dumps('<b style="x">Lead</b>') + ', coverage: slides}'),
        ('25-kits/content.yaml', '"Documented points: write', json.dumps(README_PAYLOAD + ' <div align="center">')[:-1] + ' Documented points: write'),
        ('25-kits/dev-requirements.yaml', 'title: Crawling\n    intro', 'title: ' + json.dumps('<details open class="x">') + '\n    intro')])
    code, out = build(root)
    assert code == 0, out
    bad = readme_problems(root)
    assert not bad and not raw_html_any(root), '\n  '.join([''] + bad) + str(raw_html_any(root)[:3])
    area = (root / '30-topics' / 'crawling' / 'README.md').read_text(encoding='utf-8')
    assert '\n**`<p align="center" style="color:red" class="x">`&lt;img src=x onerror=alert(1)>`</p>`**\n' in area and '\n# `<div align="center">`\n' in area, area[:600]
    assert '`<b style="x">`Lead`</b>`' in (root / '40-sessions' / 'README.md').read_text(encoding='utf-8')
    good = (root / '60-outputs' / 'README.md').read_text(encoding='utf-8')
    assert not raw_html(good)
    div, row = '<p align="center"><img src="../_system/brand/divider.svg" width="600" alt="Section divider"></p>', next(l for l in good.split('\n') if l.startswith('<p align="center"><img src="badges/'))
    pic = next(l for l in good.split('\n') if l.startswith('<picture>'))
    assert PICTURE_LINE.fullmatch(pic) and not raw_html(pic), pic
    for evil in (pic.replace('60-outputs-light', 'evil-light').replace('60-outputs-dark', 'evil-dark'), pic.replace(' alt="The', ' alt="<b>The'),
                 pic.replace(' alt="The', ' onerror="alert(1)" alt="The'), pic.replace('width="100%"', 'width="100%" style="x"'),
                 pic.replace('srcset="../', 'srcset="https://x/../'), pic.replace('-dark.svg', '-light.svg'), pic + '<img src=x>',
                 pic.replace('alt="The Diver', 'alt="the &lt;Diver'), pic.replace('</picture>', '')):
        assert raw_html(good + '\n' + evil + '\n'), f'not caught: {evil}'
    for evil in ('<img src=x onerror=alert(1)>', div + '<b>x</b>', div.replace('600', '601'), '<div align="center" class="x">', row.replace('alt="Number of topics"', 'alt="x"'),
                 row.replace('badges/topics.svg', 'badges/evil.svg'), row.replace('<img src="badges/days.svg"', '<img onerror="alert(1)" src="badges/days.svg"'),
                 row.replace('<br>', '<br><img src=x>'), '<p align="center"></p>', '<sub><img src=x onerror=alert(1)></sub>', 'text <sub>small</sub>',
                 '<sub>[x](y) <b>bold</b></sub>', '<p align="center"><sub>← <a href="../x">x</a></sub></p>'):
        assert raw_html(good + '\n' + evil + '\n'), f'not caught: {evil}'


def badge_module():
    p = REPO / '_system' / 'badges.py'
    assert p.exists(), '_system/badges.py is missing: the build cannot draw the README badges'
    return load_module(p, 'badges_t')


def test_badges_are_valid_deterministic_svg_from_the_data():
    m = badge_module()
    root = real_copy('real-badges')
    bk = load_module(root / '_system' / 'build_kb.py', 'bk_badges')
    kb, E, _ = bk.load(root)
    assert not E, E[:3]
    st, P = kb['badge_stats'], root / '60-outputs' / 'agent-pack'
    rows = [json.loads(l) for l in (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines()]
    ev = [r['verification'] for r in rows if r['label'] in ('slide', 'stage')]
    graded = [v for v in ev if v in ('confirmed', 'consistent', 'undocumented')]
    tj, sj = json.loads((P / 'topics.json').read_text(encoding='utf-8')), json.loads((P / 'sessions.json').read_text(encoding='utf-8'))
    dj, lib = json.loads((P / 'dev-requirements.json').read_text(encoding='utf-8')), json.loads((P / 'content-library.json').read_text(encoding='utf-8'))
    want = {'version': tj['version'], 'data_through': tj['data_through'], 'days_done': len({r['day'] for r in rows}), 'days_total': len(sj['days']),
            'claims': len(rows), 'docs_backed_pct': int(100 * sum(v != 'undocumented' for v in graded) / len(graded) + 0.5), 'topics': sum(len(a['topics']) for a in tj['areas']),
            'sources': len(json.loads((P / 'sources.json').read_text(encoding='utf-8'))), 'requirements': sum(len(a['requirements']) for a in dj['areas']),
            'facts': len(lib['facts']), **({'edition': 'community'} if COMMUNITY else {})}
    assert st == want, (st, want)
    a = m.render(dict(st), style=kb['style'])  # the style of the fixture's theme.yaml
    assert a == m.render(dict(st), style=kb['style']) and sorted(a) == sorted(f'{n}.svg' for n in BADGES), sorted(a)
    for name, svg in a.items():
        el = ET.fromstring(svg.encode('utf-8'))
        title = el.find('{http://www.w3.org/2000/svg}title')
        title = title if title is not None else el.find('title')
        assert el.tag in ('svg', '{http://www.w3.org/2000/svg}svg') and el.get('height') == '20', (name, el.tag, el.get('height'))
        assert title is not None and title.text and title.text.strip(), f'{name}: no accessible <title>'
        assert 'Verdana,DejaVu Sans,sans-serif' in svg and not bk.SVG_UNSAFE.search(svg), name
        assert (root / '60-outputs' / 'badges' / name).read_text(encoding='utf-8') == svg, f'{name} on disk differs from render()'
    assert str(st['claims']) in a['claims.svg'] or f"{st['claims']:,}" in a['claims.svg'], 'the claims badge does not show the number of claims'
    assert st['version'] in a['version.svg'] and re.search(rf"\b{st['docs_backed_pct']}\s?%", a['docs-backed.svg']), 'version or docs-backed share missing'
    assert m.render(dict(st, claims=st['claims'] + 1), style=kb['style'])['claims.svg'] != a['claims.svg'], 'the claims badge does not follow the data'


def test_badge_errors_stop_the_build():
    svg = '<svg xmlns=\\"http://www.w3.org/2000/svg\\" height=\\"20\\"><title>x</title></svg>'
    nine = '{n + ".svg": "%s" for n in ("version days claims docs-backed topics sources dev-kit media-kit privacy".split())}' % svg
    cases = [('missing', None, '_system/badges.py: file missing'),
             ('raises', 'def render(stats):\n    return {"claims.svg": str(stats["nope"])}\n', "_system/badges.py: render() failed: KeyError: 'nope'"),
             ('incomplete', f'def render(stats):\n    return {{"claims.svg": "{svg}"}}\n', '_system/badges.py: render() returned no version.svg'),
             ('script', f'def render(stats):\n    d = {nine}\n    d["claims.svg"] = d["claims.svg"].replace("<title>", "<script>alert(1)</script><title>")\n    return d\n',
              '_system/badges.py: claims.svg holds a script, an event handler or a link to another file'),
             ('remote', f'def render(stats):\n    d = {nine}\n    d["days.svg"] = d["days.svg"].replace("<title>", "<image href=\\"https://example.com/x.png\\"/><title>")\n    return d\n',
              '_system/badges.py: days.svg holds a script, an event handler or a link to another file'),
             ('broken', f'def render(stats):\n    d = {nine}\n    d["topics.svg"] = "<svg><g></svg>"\n    return d\n', '_system/badges.py: topics.svg is not well-formed SVG'),
             ('name', f'def render(stats):\n    d = {nine}\n    d["../x.svg"] = d["claims.svg"]\n    return d\n', "_system/badges.py: '../x.svg' is not a badge file name"),
             ('syntax', 'def render(stats)\n', '_system/badges.py cannot be loaded: SyntaxError')]
    bad = []
    for name, src, expect in cases:
        root = make_fixture('badge-' + name)
        (root / '_system' / 'theme.yaml').unlink()  # these stand-in render(stats) take no style: the original Art Deco default
        if src is None: (root / '_system' / 'badges.py').unlink(missing_ok=True)
        else: w(root / '_system' / 'badges.py', src)
        for d in SHARED: w(root / d / 'SENTINEL.txt', 'keep')
        code, out = build(root)
        if code == 0 or expect not in out or 'Traceback' in out or any(not (root / d / 'SENTINEL.txt').exists() for d in SHARED) or (root / '60-outputs' / 'README.md').exists():
            bad.append(f'{name}: {out.strip()[-300:]}')
    assert not bad, '\n  '.join([''] + bad)


def test_theme_default_sets_the_mindmap_and_badge_style():  # _system/theme.yaml -> <html data-style> of the mindmap, and the badges' style
    m = badge_module()
    plain = make_fixture('theme-none')  # no theme.yaml: the original Art Deco
    (plain / '_system' / 'theme.yaml').unlink()
    assert build(plain)[0] == 0
    assert '<html lang="en" data-style="art-deco">' in (plain / '50-maps' / 'mindmap.html').read_text(encoding='utf-8')
    deco_badges = {p.name: p.read_bytes() for p in (plain / '60-outputs' / 'badges').iterdir()}
    bk = load_module(plain / '_system' / 'build_kb.py', 'bk_theme')
    kb, E, _ = bk.load(plain)
    assert not E and kb['style'] == 'art-deco', E[:3]
    for style, ok in (('art-deco', True), ('deep-dive', True), ('ocean', False), ('', False)):
        root = make_fixture('theme-' + (style or 'empty'))
        shutil.copy(REPO / '_system' / 'theme.py', root / '_system' / 'theme.py')
        w(root / '_system' / 'theme.yaml', f'default: {style}\n')
        for d in SHARED: w(root / d / 'SENTINEL.txt', 'keep')
        code, out = build(root)
        if not ok:
            assert code != 0 and 'theme.yaml' in out and 'art-deco, deep-dive' in out and 'Traceback' not in out, out
            assert all((root / d / 'SENTINEL.txt').exists() for d in SHARED), 'a bad theme.yaml must stop the build before writing'
            continue
        assert code == 0, out
        html = (root / '50-maps' / 'mindmap.html').read_text(encoding='utf-8')
        assert f'<html lang="en" data-style="{style}">' in html and '/*STYLE*/' not in html, f'mindmap style is not {style}'
        got = {p.name: p.read_bytes() for p in (root / '60-outputs' / 'badges').iterdir() if p.suffix == '.svg'}
        if style == 'art-deco':
            assert got == deco_badges, 'theme.yaml art-deco must draw the same badges as before'
        else:
            want = m.render(dict(kb['badge_stats']), style='deep-dive')
            assert got == {k: v.encode('utf-8') for k, v in want.items()} and got != deco_badges, 'the badges do not follow theme.yaml'
    root = make_fixture('theme-no-token', [('_system/templates/mindmap.template.html', ' data-style="/*STYLE*/"', '')])
    code, out = build(root)
    assert code != 0 and 'must contain /*STYLE*/ exactly once' in out, out


def test_real_readmes():  # the real data: every generated README in the pattern, its links resolving, byte-identical on a rebuild
    root = real_copy('real-readmes')
    bad = readme_problems(root)
    assert not bad, '\n  '.join([''] + bad[:20])
    before = {p: p.read_bytes() for p in generated_readmes(root)}
    assert build(root)[0] == 0 and {p: p.read_bytes() for p in generated_readmes(root)} == before, 'a rebuild changed a README'


# ---------------------------------------------------------------- v2.3.0: Deep Dive (theme.yaml, the PDF edition, the Diver bot, brand files)
def test_theme_py_errors_are_clear():
    th = load_module(REPO / '_system' / 'theme.py', 'theme_t')
    d = TMP / 'theme-errors'
    d.mkdir(parents=True, exist_ok=True)
    cases = {'missing.yaml': None, 'bad.yaml': 'default: [art-deco\n', 'nokey.yaml': 'style: art-deco\n', 'list.yaml': '- art-deco\n',
             'typo.yaml': 'default: artdeco\n', 'pdfkey.yaml': 'default: ocean\n', 'empty.yaml': ''}
    for name, text in cases.items():
        if text is not None: w(d / name, text)
        try:
            th.default_style(d / name)
        except th.ThemeError as x:
            msg = str(x)
            assert name in msg, (name, msg)
            if name != 'bad.yaml':
                assert 'art-deco' in msg and 'deep-dive' in msg, (name, msg)
        else:
            raise AssertionError(f'{name}: no ThemeError')
    for style in th.STYLES:
        w(d / 'ok.yaml', f'default: {style}\n')
        assert th.default_style(d / 'ok.yaml') == style
    assert th.pdf_style('art-deco') == 'deco' and th.pdf_style('deep-dive') == 'ocean'
    try:
        th.pdf_style('ocean')
    except th.ThemeError as x:
        assert 'ocean' in str(x) and 'deep-dive' in str(x), x
    else:
        raise AssertionError('pdf_style accepted a PDF key as a theme style')
    assert th.default_style() in th.STYLES  # the real _system/theme.yaml is valid


def test_make_pdf_style_names_and_theme_default():
    try:
        mp = pdf_module('make_pdf')
    except ImportError as x:
        print(f'    skipped ({x})'); return
    assert mp.STYLES['deco'] == ['deco'] and mp.STYLES['modern'] == ['modern'], mp.STYLES
    assert mp.STYLES['ocean'] == mp.STYLES['deep-dive'] == ['ocean'], 'deep-dive must be an alias of ocean'
    assert mp.STYLES['both'] == ['deco', 'modern'], 'both keeps meaning Art Deco and modern'
    assert mp.STYLES['all'] == ['deco', 'modern', 'ocean'], mp.STYLES['all']
    assert set(mp.BUILDERS) == {'deco', 'modern', 'ocean'} and all(s in mp.BUILDERS for v in mp.STYLES.values() for s in v)
    built, old = [], (mp.prepare, mp.BUILDERS, mp.default_style, sys.argv)
    fake = lambda st: type('B', (), {'build': staticmethod(lambda day: built.append((day, st)))})
    mp.prepare, mp.BUILDERS = (lambda day: None), {k: fake(k) for k in mp.BUILDERS}
    try:
        for argv, theme, want in ((['day1'], 'deep-dive', [('day1', 'ocean')]), (['day1'], 'art-deco', [('day1', 'deco')]),
                                  (['day2', 'deep-dive'], 'art-deco', [('day2', 'ocean')]),
                                  (['day2', 'all'], 'art-deco', [('day2', 'deco'), ('day2', 'modern'), ('day2', 'ocean')]),
                                  (['day2', 'both'], 'deep-dive', [('day2', 'deco'), ('day2', 'modern')])):
            built.clear()
            mp.default_style, sys.argv = (lambda t=theme: t), ['make_pdf.py'] + argv
            with contextlib.redirect_stdout(io.StringIO()):
                mp.main()
            assert built == want, (argv, theme, built)

        def bad_theme():
            raise mp.ThemeError("_system/theme.yaml: default is 'x', but it must be one of: art-deco, deep-dive.")
        built.clear()
        for argv, theme, needle in ((['day1', 'oceanic'], (lambda: 'deep-dive'), 'Unknown style'), (['day1'], bad_theme, 'theme.yaml')):
            mp.default_style, sys.argv = theme, ['make_pdf.py'] + argv
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    mp.main()
            except SystemExit as x:
                assert needle in str(x.code) and not built, (argv, x.code, built)
            else:
                raise AssertionError(f'{argv}: no error')
    finally:
        mp.prepare, mp.BUILDERS, mp.default_style, sys.argv = old


def test_ocean_recolours_every_template_colour_and_stops_on_an_unknown_one():
    try:
        bo = pdf_module('build_ocean')
    except ImportError as x:
        print(f'    skipped ({x})'); return
    for f in sorted((REPO / '_system' / 'pdf').glob('day*.template.html')):
        assert not bo.unmapped_colours(f.read_text(encoding='utf-8')), (f.name, bo.unmapped_colours(f.read_text(encoding='utf-8')))
    modern = ('#2457e6', '#0b8a5f', '#c8372d', '#b86e00', '#6d3fd6', '#bcd0ff', '#667085', '#98a2b3')
    leaked = ('<svg viewBox="0 0 9 9"><path d="M0 0" stroke="#bcd0ff"/><rect fill="#2457e6" stroke="#c7cdd8"/><text fill="#2457e6">a</text>'
              '<circle fill="#c8372d"/><path fill="#0b8a5f"/><line stroke="#6d3fd6"/><path fill="#b86e00"/><rect fill="#FFFFFF"/></svg>'
              '<div style="color:#c8372d">x</div><b style="color:#2457e6">y</b>')
    assert not bo.unmapped_colours(leaked), bo.unmapped_colours(leaked)
    out = bo.recolor_inline(bo.recolor_svgs(leaked)).lower()
    assert not [c for c in modern if c in out], 'modern colours left in the Deep Dive edition: ' + out
    assert '<text fill="#2152c4">' in out and '<rect fill="#2f6fe0"' in out and 'style="color:#c2412f"' in out, out
    for table in (bo.TEXT_MAP, bo.FILL_MAP, bo.STROKE_MAP, bo.INLINE_MAP):
        for a, b in table.items():
            assert re.fullmatch(r'#[0-9a-f]{6}', a) and re.fullmatch(r'#[0-9a-f]{6}', b), (a, b)
            assert b not in ('#4285f4', '#ea4335', '#fbbc05', '#34a853'), f'{a} maps to a Google brand colour'
    bad = '<svg viewBox="0 0 9 9"><rect fill="#123456"/><ellipse fill="#2457e6"/></svg><b style="color:#abcdef">x</b>'
    assert bo.unmapped_colours(bad) == ['<ellipse fill="#2457e6">', '<rect fill="#123456">', 'style="color:#abcdef"'], bo.unmapped_colours(bad)
    # build() stops on such a colour before anything is rendered, naming the colour and where to map it
    day = 'day77'
    src = bo.BUILD / f'{day}.html'
    old = (bo.day_data, bo.config, bo.touches, bo.paginate)
    rendered = []
    bo.day_data, bo.config = (lambda d: {}), (lambda: {'author': 'X'})
    bo.touches, bo.paginate = (lambda html, d: html), (lambda *a, **k: rendered.append(a))
    try:
        bo.BUILD.mkdir(exist_ok=True)
        w(src, '<html><body>' + bad + '</body></html>')
        bo.build(day)
    except bo.BuildError as x:
        assert '#123456' in str(x) and 'STROKE_MAP' in str(x) and not rendered, x
    else:
        raise AssertionError('build_ocean.build() did not stop on an unmapped colour')
    finally:
        bo.day_data, bo.config, bo.touches, bo.paginate = old
        src.unlink(missing_ok=True)
    assert not (bo.OUT / f'{day}-field-guide-deep-dive.pdf').exists()


def test_diver_bot_poses_are_deterministic_unique_and_original():
    oa = load_module(REPO / '_system' / 'ocean_art.py', 'oa_bot')
    assert set(oa.BOT_POSES) >= {'swim', 'wave', 'read', 'point', 'peek', 'head'}, oa.BOT_POSES
    google = {h.lower() for h in oa.BOT_FORBIDDEN_HEX}
    assert google == {'#4285f4', '#ea4335', '#fbbc05', '#34a853'}, google
    for pal in (oa.PALETTE, oa.DARK):
        for c in pal.values():
            if isinstance(c, str): assert c.lower() not in google, f'palette uses Google colour {c}'
    seen_ids = set()
    for pose in oa.BOT_POSES:
        for dark in (False, True):
            for size, unit in ((24, 1.0), (120, 1.0), (1200, 0.378)):
                uid = f't-{pose}-{int(dark)}-{size}'
                a = oa.diver_bot(pose, 50, 50, size, uid, dark=dark, unit_px=unit)
                assert a == oa.diver_bot(pose, 50, 50, size, uid, dark=dark, unit_px=unit), f'{pose}: not deterministic'
                assert a.startswith('<g') and a.endswith('</g>'), pose
                assert not [h for h in re.findall(r'#[0-9a-fA-F]{6}\b', a) if h.lower() in google], f'{pose} dark={dark}: Google brand colour'
                ids = re.findall(r'\bid="([^"]+)"', a)
                assert len(ids) == len(set(ids)), f'{pose}: duplicate ids {ids}'
                assert all(i.startswith(uid) for i in ids), f'{pose}: an id without the uid prefix: {ids}'
                assert not (set(ids) & seen_ids), f'{pose}: ids clash across copies'
                seen_ids |= set(ids)
                refs = set(re.findall(r'url\(#([^)]+)\)', a)) | set(re.findall(r'href="#([^"]+)"', a))
                assert refs <= set(ids), f'{pose}: references to missing ids {refs - set(ids)}'
            svg = oa.diver_bot_svg(pose, '48px', f's-{pose}-{int(dark)}', dark=dark, label='Diver bot')
            assert svg == oa.diver_bot_svg(pose, '48px', f's-{pose}-{int(dark)}', dark=dark, label='Diver bot')
            ET.fromstring(svg)  # well-formed
            assert 'role="img"' in svg and 'aria-label="Diver bot"' in svg, pose
    bw, bh = oa.diver_bot_box('swim', 100)
    assert abs(max(bw, bh) - 100) < 1e-6, (bw, bh)
    for pose, lod in (('dance', None), ('wave', 'blurry')):
        try:
            oa.diver_bot(pose, 0, 0, 100, 'x', lod=lod)
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError(f'{pose}, {lod}: accepted')


def test_make_brand_names_follow_the_theme_default():
    mb = load_module(REPO / '_system' / 'brand' / 'make_brand.py', 'mb_t')
    assert mb.names('deep-dive', 'deep-dive') == {'light': 'banner-light.png', 'dark': 'banner-dark.png', 'divider': 'divider.svg', 'palette': 'palette.svg'}
    assert mb.names('art-deco', 'deep-dive') == {'light': 'banner-art-deco-light.png', 'dark': 'banner-art-deco-dark.png',
                                                  'divider': 'divider-art-deco.svg', 'palette': 'palette-art-deco.svg'}
    assert mb.names('art-deco', 'art-deco')['divider'] == 'divider.svg' and mb.names('deep-dive', 'art-deco')['light'] == 'banner-deep-dive-light.png'
    try:
        mb.names('ocean', 'deep-dive')
    except ValueError:
        pass
    else:
        raise AssertionError('names() accepted an unknown style')
    # the real brand folder: theme.yaml's default under the canonical names, the other style under its own name, nothing kept twice
    default = load_module(REPO / '_system' / 'theme.py', 'theme_b').default_style()
    other = next(s for s in mb.STYLES if s != default)
    brand = REPO / '_system' / 'brand'
    svg = {'art-deco': (mb.divider_svg(), mb.palette_svg()), 'deep-dive': (mb.dd_divider_svg(), mb.dd_palette_svg())}
    for style in (default, other):
        n = mb.names(style, default)
        assert [(brand / n[k]).read_text(encoding='utf-8') for k in ('divider', 'palette')] == list(svg[style]), f'{style}: {n["divider"]} or {n["palette"]} is stale'
        assert (brand / n['light']).is_file() and (brand / n['dark']).is_file(), n
    stray = [n for n in mb.names(default, other).values() if (brand / n).exists()]
    assert not stray, f'the default style is also kept under its own name: {stray}'
    assert sorted(p.stem for p in (brand / 'icons').glob('*.svg')) == sorted(mb.ICONS)
    for name in mb.ICONS:
        assert (brand / 'icons' / f'{name}.svg').read_text(encoding='utf-8') == mb.icon_svg(name), f'icons/{name}.svg is stale'
        ET.fromstring(mb.icon_svg(name))
    for day in sorted(p.name[:-len('.template.html')] for p in (REPO / '_system' / 'pdf').glob('day*.template.html')):
        for ed in ('deep-dive', 'art-deco'):
            if (REPO / '60-outputs' / 'pdf' / f'{day}-field-guide-{ed}.pdf').exists():
                assert (brand / 'covers' / f'{day}-{ed}.png').is_file(), f'covers/{day}-{ed}.png missing: run make_brand.py --covers'


def test_check_commit_allows_brand_icons_and_covers():
    cc = load_module(REPO / '_system' / 'tools' / 'check_commit.py', 'cc2')
    clean = ['_system/brand/banner-light.png', '_system/brand/banner-art-deco-dark.png', '_system/brand/covers/day1-deep-dive.png',
             '_system/brand/covers/day2-art-deco.png', '_system/brand/icons/bot.svg', '_system/brand/icons/fish.svg',
             '_system/brand/divider.svg', '_system/brand/palette-art-deco.svg', '_system/ocean_art.py', '_system/theme.yaml',
             '60-outputs/pdf/day1-field-guide-deep-dive.pdf', '60-outputs/site/downloads/day2-field-guide-deep-dive.pdf',
             '60-outputs/site/assets/icon-deep-dive.svg', '_system/brand/illustrations/root-light.svg', '_system/brand/illustrations/_system-pdf-dark.svg',
             '_system/brand/illustrations/30-topics-crawling-light.svg', '_system/brand/make_illustrations.py', '_system/brand/illus_a.py']
    flagged = ['_system/brand/illustrations/IMG_4692.png', '_system/brand/illustrations/root-light.png', '_system/brand/IMG_4692.png', '_system/brand/covers/Photo 01.png', '_system/brand/covers/photo-01.jpg',
               '_system/brand/icons/photo.png', '_system/brand/snapshot-01.jpeg', '_system/brand/covers/sub/day1.png', '_system/brand/Banner.PNG']
    bad = [p for p in flagged if not cc.reasons(TMP, p)] + [(p, cc.reasons(TMP, p)) for p in clean if cc.reasons(TMP, p)]
    assert not bad, bad
    big = TMP / '_system' / 'brand' / 'covers' / 'day9-deep-dive.png'
    big.parent.mkdir(parents=True, exist_ok=True)
    big.write_bytes(b'\0' * (cc.BRAND_MAX + 1))
    assert cc.reasons(TMP, '_system/brand/covers/day9-deep-dive.png'), 'a cover over the size limit must be flagged'



# ---------------------------------------------------------------- v2.6.0: README illustrations (_system/brand/make_illustrations.py)
def test_every_readme_has_its_illustration():
    """Every tracked README shows its own header card (light, and dark for GitHub's dark theme) once, right under its lead (the root
    README under "The three days"), with a real alt text; every card in _system/brand/illustrations/ belongs to a README and is valid,
    small, text-free SVG that make_illustrations.py draws again byte for byte."""
    mi = load_module(REPO / '_system' / 'brand' / 'make_illustrations.py', 'mi_t')
    readmes = mi.tracked_readmes()
    assert len(readmes) >= 31, readmes
    folder = REPO / '_system' / 'brand' / 'illustrations'
    files = {p.name for p in folder.iterdir()} if folder.is_dir() else set()
    want = {f'{s}-{v}.svg' for s in readmes for v in ('light', 'dark')}
    assert files == want, f'missing {sorted(want - files)[:5]}, extra {sorted(files - want)[:5]}: run make_illustrations.py'
    pic = re.compile(r'<picture><source media="\(prefers-color-scheme: dark\)" srcset="([^"]*)"><img src="([^"]*)" width="100%" alt="([^"<>]*)"></picture>')
    bad = []
    for slug, rel in sorted(readmes.items()):
        txt = (REPO / rel).read_text(encoding='utf-8')
        lines = FENCED.sub('', txt).split('\n')  # the brand README shows the markup in a code block
        hits = [(i, pic.fullmatch(l)) for i, l in enumerate(lines) if l.startswith('<picture>') and 'illustrations/' in l]
        if len(hits) != 1 or not hits[0][1]: bad.append(f'{rel}: needs exactly one header illustration line'); continue
        i, m = hits[0]
        up = os.path.relpath(REPO / '_system' / 'brand' / 'illustrations', (REPO / rel).parent).replace('\\', '/')
        if (m[1], m[2]) != (f'{up}/{slug}-dark.svg', f'{up}/{slug}-light.svg'): bad.append(f'{rel}: shows {m[1]} / {m[2]}, not its own card')
        if len(m[3]) < 40 or not m[3][0].isupper() or not m[3].endswith('.'): bad.append(f'{rel}: alt text too thin: {m[3]!r}')
        if lines[i - 1] != '' or lines[i + 1] != '': bad.append(f'{rel}: the picture needs a blank line before and after')
        if slug == 'root':
            if 'The three days' not in lines[i - 2]: bad.append(f'{rel}: the root card belongs under "The three days"')
        else:
            div = next((j for j, l in enumerate(lines) if 'divider.svg' in l), len(lines))
            title = next(j for j, l in enumerate(lines) if l.startswith('# '))
            if not title < i < div or not lines[i - 2].strip(): bad.append(f'{rel}: the picture belongs right under the lead, before the first divider')
    assert not bad, '\n  '.join([''] + bad)
    scenes = mi.load_scenes()
    cards, errs, _ = mi.draw(sorted(readmes), scenes)
    assert not errs, errs[:5]
    assert not [s for s, (_, fn) in scenes.items() if getattr(fn, 'placeholder', False)], 'placeholder scenes left'
    for slug, c in sorted(cards.items()):
        for variant, svg in c.items():
            p = folder / f'{slug}-{variant}.svg'
            data = p.read_bytes()
            assert data == svg.encode('utf-8'), f'{p.name} is not what make_illustrations.py draws: run it again'
            assert len(data) <= mi.MAX_BYTES and b'\r' not in data, p.name
            root = ET.fromstring(data)
            assert root.get('viewBox') == '0 0 880 240', p.name
            tags = {el.tag.split('}')[-1] for el in root.iter()}
            assert not tags & {'text', 'tspan', 'textPath', 'font', 'glyph', 'script', 'image', 'foreignObject', 'style', 'use', 'a'}, (p.name, tags)
            assert not re.search(rb'font-family|font-size|@import|href="(?!#)|url\((?!#)', data), p.name
    cc = load_module(REPO / '_system' / 'tools' / 'check_commit.py', 'cc3')
    assert not [f for f in sorted(files) if cc.reasons(REPO, f'_system/brand/illustrations/{f}')], 'the privacy check flags an illustration'


# ---------------------------------------------------------------- knowledge graph phase 3: the query layer (_system/kb_query.py, ask.bat)

KBQ_PROBE = r'''
import io, json, os, sys, time
seen, events = [], []
def hook(ev, args):
    if ev == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)): seen.append(os.fsdecode(args[0]))
    elif ev in ('os.listdir', 'os.scandir', 'os.walk', 'glob.glob') and args and args[0] is not None: seen.append(os.fsdecode(args[0]))
    elif ev.split('.')[0] in ('socket', 'subprocess', 'urllib', 'http', 'ftplib', 'smtplib', 'webbrowser') or ev in ('os.system', 'os.startfile', 'os.spawn', 'os.exec'):
        events.append(ev)
sys.addaudithook(hook)
sys.path.insert(0, os.path.join(os.getcwd(), '_system'))
import kb_query
out = io.StringIO()
real, sys.stdout = sys.stdout, out
codes, t0 = [], time.perf_counter()
codes.append(kb_query.main(['search', 'what does Google say about 429?']))
first = time.perf_counter() - t0
for argv in (['about'], ['search', 'hreflung', '--text'], ['search', 'canon', '--kind', 'all'], ['entity', 'GSC'], ['entity', 'googlebott'],
             ['neighbours', 'ent:googlebot', '--hops', '2'], ['claims', '--topic', 'robots-txt', '--label', 'event'], ['evidence', 'D1-C108'],
             ['cite', 'D1-C353', 'D1-C072'], ['entity', '../../70-private/canary'], ['search', '../../70-private/canary.md']):
    codes.append(kb_query.main(argv))
sys.stdin = io.StringIO('what does Google say about 429?\nD1-C108\n\n')
codes.append(kb_query.main(['ask']))
refused = []
for p in ('../../70-private/canary.md', os.path.join(os.getcwd(), '70-private', 'canary.md'), '..\\..\\00-raw\\canary.md',
          'entities/../../../10-sources/canary.md', '../../20-claims/day1.yaml', '/etc/hosts', 'C:/Windows/win.ini', ''):
    try:
        kb_query.pack_file(p); refused.append([p, False])
    except kb_query.Refused:
        refused.append([p, True])
    except Exception as e:
        refused.append([p, type(e).__name__])
sys.stdout = real
print(json.dumps({'seen': seen, 'events': events, 'codes': codes, 'first': first, 'refused': refused,
                  'pack': str(kb_query.PACK), 'out': out.getvalue()}))
'''


def kbq_root():  # the built real data with kb_query.py, ask.bat and find_python.cmd beside it, as in the repository
    root = real_site_root()
    for rel in ('_system/kb_query.py', 'ask.bat', '_system/tools/find_python.cmd'):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, root / rel)
    return root


def kbq(root, *args):
    code, out = run_py(root, '_system/kb_query.py', *args)
    try:
        return code, json.loads(out)
    except ValueError:
        raise AssertionError(f'kb_query.py {" ".join(args)} did not print JSON (exit {code}): {out[:600]}')


def test_kb_query_reads_only_the_pack():  # knowledge graph phase 3: the query layer opens nothing outside 60-outputs/agent-pack
    root = kbq_root()
    P = (root / '60-outputs' / 'agent-pack').resolve()
    canary = 'KBQ-CANARY-7f3a'
    for d in ('70-private', '00-raw', '10-sources'):
        (root / d).mkdir(exist_ok=True)
        (root / d / 'canary.md').write_text(f'{canary} D1-C001 robots.txt 429 hreflang\n', encoding='utf-8')
    # standard library only: every import of kb_query.py is a module of the standard library (no pyyaml, no native extras)
    src = (root / '_system' / 'kb_query.py').read_text(encoding='utf-8')
    import ast
    tree = ast.parse(src)
    mods = {a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} |            {n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert mods and mods <= set(sys.stdlib_module_names), f'kb_query.py imports more than the standard library: {sorted(mods - set(sys.stdlib_module_names))}'
    probe = root / 'kbq_probe.py'
    probe.write_text(KBQ_PROBE, encoding='utf-8')
    code, out = run_py(root, 'kbq_probe.py')
    probe.unlink()
    assert code == 0, out[-3000:]
    r = json.loads(out)
    assert Path(r['pack']).resolve() == P, r['pack']
    allowed = [Path(p).resolve() for p in {sys.base_prefix, sys.prefix, sys.exec_prefix}]
    me = (root / '_system' / 'kb_query.py').resolve()
    outside = []
    for s in sorted(set(r['seen'])):
        p = Path(s) if os.path.isabs(s) else root / s
        p = p.resolve()
        if p == P or P in p.parents: continue
        if p in (me, me.parent) or p.parent.name == '__pycache__' and p.parent.parent == me.parent: continue  # importing kb_query lists its folder
        if any(a in p.parents for a in allowed): continue  # the standard library itself
        outside.append(str(p))
    assert not outside, f'kb_query opened files outside the agent pack: {outside}'
    opened = {Path(s).resolve().relative_to(P).as_posix() for s in r['seen'] if Path(s).is_absolute() and P in Path(s).resolve().parents}
    assert {'claims.jsonl', 'links.json', 'entities.json', 'graph.json'} <= opened, opened
    assert not r['events'], f'kb_query must not start processes or touch the network: {sorted(set(r["events"]))}'
    assert all(ok is True for _, ok in r['refused']), f'pack_file must refuse every path outside the pack: {r["refused"]}'
    assert canary not in r['out'] and 'Traceback' not in r['out'], r['out'][-2000:]
    assert r['codes'][:10] == [0] * 10 and r['codes'][-1] == 0, r['codes']  # the canary "names" are simply not found (exit 1)
    assert r['first'] < 1.0, f'"what does Google say about 429?" took {r["first"]:.2f} s from a cold start (the plan: under a second)'
    # private claims are not served: not by id, not in any answer
    private = [c['id'] for f in sorted((REPO / '20-claims').glob('day*.yaml')) for c in yaml.safe_load(f.read_text(encoding='utf-8')) or [] if c.get('private')]
    if private:
        code, res = kbq(root, 'cite', *private)
        assert code == 0 and res['cite'] == {} and sorted(res['missing']) == sorted(private), res
        code, res = kbq(root, 'evidence', private[0])
        assert code == 1 and 'private' in res['error'], res
    leaked = [c for c in private if re.search(rf'\b{c}\b', r['out'])]
    assert not leaked and 'img_4692' not in r['out'].lower(), leaked


def test_kb_query_search_entity_cite():  # knowledge graph phase 3: cited answers, alias and typo tolerance, fuzzy things, citations
    root = kbq_root()
    P = root / '60-outputs' / 'agent-pack'
    rows = {r['id']: r for r in map(json.loads, (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines())}
    E = {x['id']: x for x in json.loads((P / 'entities.json').read_text(encoding='utf-8'))['entities']}
    L = json.loads((P / 'links.json').read_text(encoding='utf-8'))
    kq = load_module(root / '_system' / 'kb_query.py', 'kb_query_test')
    kbm = load_module(REPO / '_system' / 'build_kb.py', 'kb_fold_kbq')
    # the same fold() as the build (and so as the web edition, test_fold_python_matches_js)
    assert [(kq.fold(s), kq.norm_key(s)) for s in FOLD_CASES] == [(kbm.fold(s), kbm.norm_key(s)) for s in FOLD_CASES]
    # citations: identical to the cards' cite (build_kb.claim_cite) for every claim a card lists; a person only where proven
    kb = kq.KB()
    card_cites = {c: v for x in E.values() for c, v in x['cite'].items()}
    assert len(card_cites) > 1000 and not [c for c, v in card_cites.items() if kb.cite(c) != v]
    proven = real_proven_names()
    safe = {'Google', 'a community speaker', 'a speaker', 'an audience member'}
    bad = []
    for cid, r in rows.items():
        parts = [x.strip() for x in kb.cite(cid)[1:-1].split(',')]
        if parts[0] != cid or parts[1] != r['label']: bad.append((cid, parts)); continue
        if r['label'] in ('slide', 'stage'):
            if parts[3] != f"Day {r['day']}" or parts[2] != (proven.get(cid) or parts[2]) or (not proven.get(cid) and parts[2] not in safe): bad.append((cid, parts))
        elif r['label'] in ('docs', 'press'):
            if parts[-1] not in [s['url'] for s in r['sources']]: bad.append((cid, parts))
        elif parts != [cid, 'analysis', 'Ibrahim Anjro']: bad.append((cid, parts))
    assert not bad, bad[:10]
    # the acceptance question: the 429 card first, every claim a 429 claim, each with its cite and the rules
    code, s = kbq(root, 'search', 'what does Google say about 429?')
    assert code == 0 and s['things'] and s['things'][0]['id'] == 'ent:http-429', s.get('things')
    assert s['results'] and {x['id'] for x in s['results']} <= set(E['http-429']['claims']), [x['id'] for x in s['results']]
    assert all(x['cite'] == kb.cite(x['id']) and x['id'] in rows for x in s['results']) and 'claim id' in s['rules']
    code2, s2 = kbq(root, 'search', 'what does Google say about 429?')
    assert s2 == s, 'the same question must give the same answer'
    # the topics of the best claims, each with the command that reads it in full; other forms of a question word match too
    assert s['topics'] and all(t['more'] == 'claims --topic ' + t['id'][6:] and t['claims'] >= t['in_results'] for t in s['topics']), s.get('topics')
    assert kq.stem('detects') == kq.stem('detected') == kq.stem('detect') == 'detect' and kq.stem('429') == '429'
    # aliases, typos, prefixes
    code, s = kbq(root, 'search', 'GSC')
    assert s['things'][0]['id'] == 'ent:google-search-console' and s['total'] >= len(E['google-search-console']['claims']) * 0.9, s['total']
    code, s = kbq(root, 'search', 'hreflung')
    assert 'hreflang' in s.get('note', '') and 'hreflung' in s['note'] and s['things'][0]['id'] == 'ent:hreflang-annotation' and len(s['results']) >= 3, s.get('note')
    code, s = kbq(root, 'search', 'canonica')
    assert s['results'] and any('canonical' in x['text'].lower() for x in s['results']), s
    code, s = kbq(root, 'search', 'zzqxv wqzzv')
    assert code == 0 and s['results'] == [] and s['total'] == 0 and 'does not cover' in s['answer']
    # filters: label, grade, day, and the speaker rule (only a proven name, never an unproven one)
    code, s = kbq(root, 'search', 'crawl budget', '--label', 'event', '--grade', 'undocumented,consistent', '--day', '1', '--limit', '30')
    assert s['results'] and all(rows[x['id']]['label'] in ('slide', 'stage') and rows[x['id']]['verification'] in ('undocumented', 'consistent')
                                and rows[x['id']]['day'] == 1 for x in s['results'])
    name = L['speakers']['names'][0]['name']
    code, s = kbq(root, 'search', 'crawl', '--speaker', name, '--limit', '50')
    assert s['results'] and all(L['speakers']['claims'][x['id']]['name'] == name and x['said_by'] == name for x in s['results'])
    names = {x['name'] for x in L['speakers']['names']}
    sess = json.loads((P / 'sessions.json').read_text(encoding='utf-8'))
    unproven = sorted({n for d in sess['days'] for x in d['sessions'] for n in x['speakers'] if ' ' in n and n not in names and 'speaker' not in n.lower()})
    if unproven:
        code, s = kbq(root, 'search', 'crawl', '--speaker', unproven[0])
        assert code == 1 and 'not a proven speaker' in s['error'], s
    # things: id, name, alias, near miss, ambiguity
    for q, want in (('x-robots-tag', 'x-robots-tag'), ('ent:googlebot', 'googlebot'), ('Google Search Console', 'google-search-console'), ('GSC', 'google-search-console')):
        code, e = kbq(root, 'entity', q)
        assert code == 0 and e['entity']['id'] == 'ent:' + want and 'note' not in e, (q, e.get('error'))
    code, e = kbq(root, 'entity', 'hreflung')
    assert code == 0 and e['entity']['id'] == 'ent:hreflang-annotation' and 'hreflung' in e['note']
    got = sorted(c['id'] for g in e['entity']['claims'].values() for c in g)
    assert got == sorted(E['hreflang-annotation']['claims']) and all(c['cite'] == kb.cite(c['id']) for g in e['entity']['claims'].values() for c in g)
    assert all(c['verification'] == 'undocumented' and c['label'] in ('slide', 'stage') for c in e['entity']['claims']['event_undocumented'])
    code, e = kbq(root, 'entity', 'crawl')
    assert code == 1 and 'Did you mean' in e['error'] and 'ent:crawl-budget-metric' in [d['id'] for d in e['did_you_mean']], e
    code, e = kbq(root, 'entity', 'zzqxv')
    assert code == 1 and 'error' in e and not e.get('did_you_mean')
    # claims, evidence, neighbours, cite
    code, c = kbq(root, 'claims', '--entity', 'http-429')
    assert c['total'] == len(E['http-429']['claims']) and all(x['cite'] == kb.cite(x['id']) for x in c['claims'])
    code, v = kbq(root, 'evidence', 'D1-C108')
    r = rows['D1-C108']
    assert v['claim']['sources'] == r['sources'] and [u['id'] for u in v['used_by']] == r['used_by'] and v['evidence_refs'] == r['evidence']
    assert {x['id'] for x in v['relations']} == {x['to'] for x in r['relations']} | {x['from'] for x in r['related_from']}
    G = json.loads((P / 'graph.json').read_text(encoding='utf-8'))
    ids = {n['id'] for n in G['nodes']}
    code, n = kbq(root, 'neighbours', 'http-429')
    nb = {x['id'] for x in n['neighbours']}
    assert n['node']['id'] == 'ent:http-429' and 'ent:http-4xx' in nb and {f'claim:{c}' for c in E['http-429']['claims']} <= nb
    assert all(e_['from'] in ids and e_['to'] in ids for e_ in n['edges'])
    code, n = kbq(root, 'neighbours', 'ent:http-429', '--hops', '2', '--node-kinds', 'requirement', '--edge-types', 'mentions,rests-on')
    assert n['neighbours'] and all(x['kind'] == 'requirement' and x['hop'] == 2 for x in n['neighbours'])
    code, t = kbq(root, 'cite', 'D1-C353', 'd1-c072', 'D9-C999')
    assert t['cite'] == {'D1-C353': kb.cite('D1-C353'), 'D1-C072': kb.cite('D1-C072')} and t['missing'] == ['D9-C999']
    assert t['combined'] == '[' + kb.cite('D1-C353')[1:-1] + '; ' + kb.cite('D1-C072')[1:-1] + ']'
    code, a = kbq(root, 'about')
    assert a['counts']['claims'] == len(rows) and a['version'] == L['version'] and a['rules']
    ix = (P / 'INDEX.md').read_text(encoding='utf-8')
    assert [x['id'] for x in a['sessions_with_no_coverage']] == re.findall(r'^- `(D\d+-S\d+)`', ix.split('## Sessions with no coverage', 1)[1].split('\n## ', 1)[0], re.M)
    code, out = run_py(root, '_system/kb_query.py', 'search', 'hreflung', '--text')
    assert code == 0 and 'Showing results for' in out and '[D' in out and 'Rules:' in out and not out.lstrip().startswith('{'), out[:500]
    # AGENTS.md tells agents to use it, and its examples are real
    guide = (P / 'AGENTS.md').read_text(encoding='utf-8')
    assert '`kb_query.py`' in guide and all(f'kb_query.py {c}' in guide for c in ('about', 'search', 'entity', 'neighbours', 'claims', 'evidence', 'cite'))
    # ask.bat: CRLF, full paths, UTF-8, and on Windows a real run that answers and quits on an empty line
    bat = (REPO / 'ask.bat').read_bytes()
    assert b'\r\n' in bat and b'\n' not in bat.replace(b'\r\n', b'') and b'"%~dp0_system\\kb_query.py" ask' in bat and b'chcp 65001' in bat
    assert b'call "%~dp0_system\\tools\\find_python.cmd"' in bat
    if os.name == 'nt':
        rr = subprocess.run(['cmd', '/c', str(root / 'ask.bat')], input='what does Google say about 429?\r\n\r\n', capture_output=True,
                            text=True, encoding='utf-8', errors='replace', cwd=root, timeout=60, env=dict(os.environ, KB_PYTHON=sys.executable))
        assert rr.returncode == 0 and 'D1-C072' in rr.stdout and '429' in rr.stdout and 'Traceback' not in rr.stdout + rr.stderr, rr.stdout[-1500:] + rr.stderr


# ---------------------------------------------------------------- knowledge graph phase 3: the ledgers (numbers registry, differences ledger, question bank)
LEDGER_PAGES = ['dev/differences.html', 'content/numbers.html', 'content/questions.html']


def ledger_claims(doc):  # every claim record in a ledger file (anything with an id and a cite)
    out = []
    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get('id'), str) and 'cite' in x: out.append(x)
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(doc)
    return out


def check_ledgers(root):
    """The ledger rules on a built tree: every claim is public and as in claims.jsonl, every stat fact is in the registry, every row cites public claims.
    The community edition has the differences ledger only: the numbers registry and the question bank belong to the full media kit."""
    P = root / '60-outputs' / 'agent-pack'
    rows = {r['id']: r for r in map(json.loads, (P / 'claims.jsonl').read_text(encoding='utf-8').splitlines())}
    community = built_edition(root) == 'community'
    if community:
        there = [x for x in ('60-outputs/agent-pack/numbers.json', '60-outputs/agent-pack/question-bank.json', '50-maps/numbers.md') if (root / x).exists()]
        assert not there, f'the community edition has no numbers registry and no question bank: {there}'
    led = {n: json.loads((P / f'{n}.json').read_text(encoding='utf-8')) for n in (('differences',) if community else ('numbers', 'differences', 'question-bank'))}
    for n, doc in led.items():
        cs = ledger_claims(doc)
        bad = [c['id'] for c in cs if c['id'] not in rows or c['text'] != rows[c['id']]['text'] or not c['cite'].startswith(f"[{c['id']}, {c['label']}, ")]
        assert cs and not bad, f'{n}.json: claims not public or not as in claims.jsonl: {bad[:5]}'
    lib = json.loads((P / 'content-library.json').read_text(encoding='utf-8'))
    stat = [f['id'] for f in lib['facts'] if f['use'] == 'stat']
    if not community:
        assert [f['id'] for f in led['numbers']['facts']] == stat, 'the numbers registry must hold every use: stat fact, in order'
        md = (root / '50-maps' / 'numbers.md').read_text(encoding='utf-8')
        assert all(f'| `{x}` |' in md for x in stat), [x for x in stat if f'| `{x}` |' not in md]
    src = yaml.safe_load((root / '25-kits' / 'differences.yaml').read_text(encoding='utf-8')) if (root / '25-kits' / 'differences.yaml').exists() else {'differences': []}
    D = led['differences']
    assert [r['id'] for r in D['rows']] == [x['id'] for x in src['differences']]
    for x, r in zip(src['differences'], D['rows']):
        assert r['event'] and (r['docs'] or r['pages']), r['id']
        assert [c['id'] for c in r['event']] == x['event'] and [c['id'] for c in r['docs']] == (x.get('docs') or []) and [c['id'] for c in r['analysis']] == x['analysis'], r['id']
        assert all(c['label'] in ('slide', 'stage') for c in r['event']) and all(c['label'] == 'docs' for c in r['docs']) and all(c['label'] == 'analysis' for c in r['analysis']), r['id']
    for d in ('50-maps/differences.md', '60-outputs/dev/differences.md'):
        t = (root / d).read_text(encoding='utf-8')
        assert all(f"### {r['id']} " in t for r in D['rows']), d
    return led


def test_ledgers_render_and_cite_public_claims():  # knowledge graph phase 3 on a fixture: the three ledgers, their kit pages and the private claim kept out
    root = make_fixture('ledgers', [(DIFF_FILE, None, DIFF_FIX), ('25-kits/content.yaml', 'status: documented, use: headline', 'status: documented, use: stat')] + SITE_EDITS, site=True)
    code, out = build(root)
    assert code == 0 and 'OK: ledgers: 1 stat fact' in out and '1 difference' in out, out
    led = check_ledgers(root)
    N, D, Q = led['numbers'], led['differences'], led['question-bank']
    assert N['facts'][0]['id'] == 'F-001' and [c['id'] for c in N['facts'][0]['claims']] == ['D1-C001', 'D1-C006']
    r = D['rows'][0]
    assert (r['id'], [c['id'] for c in r['event']], [c['id'] for c in r['docs']], [c['id'] for c in r['analysis']]) == ('DIF-01', ['D2-C001'], ['D1-C006'], ['D1-C005'])
    assert [p['key'] for p in r['pages']] == ['crawl-guide'], r['pages']
    aq = {q['question']['id']: q for q in Q['audience']}
    assert sorted(aq) == ['D1-C002', 'D1-C009'] and [a['id'] for a in aq['D1-C002']['answers']] == ['D1-C003', 'D1-C010']
    assert aq['D1-C002']['question']['by'] == 'an audience member'
    C = root / '60-outputs' / 'content'
    assert (C / 'questions.json').read_bytes() == (root / '60-outputs' / 'agent-pack' / 'question-bank.json').read_bytes()
    for f in ('50-maps/numbers.md', '50-maps/differences.md', '60-outputs/dev/differences.md', '60-outputs/content/questions.md', '60-outputs/agent-pack/numbers.json',
              '60-outputs/agent-pack/differences.json', '60-outputs/agent-pack/question-bank.json'):
        t = (root / f).read_text(encoding='utf-8')
        assert 'D1-C007' not in t and 'SECRETPRIVATEMARKER' not in t and '\r' not in t, f
    h1 = tree_hash(root)
    assert build(root)[0] == 0 and tree_hash(root) == h1, 'the ledgers differ on a rebuild'
    # the web edition: three pages, linked from the kit pages, with their downloads, checked against claims.jsonl
    code, out = build_site(root)
    assert code == 0, out
    O = root / '60-outputs' / 'site'
    H = {p: (O / p).read_text(encoding='utf-8') for p in LEDGER_PAGES + ['dev/index.html', 'content/index.html', 'verification.html']}
    dif, num, qb = (H[p] for p in LEDGER_PAGES)
    assert 'href="../dev/differences.html"' in H['dev/index.html'] and 'href="../content/numbers.html"' in H['content/index.html'] and 'href="../content/questions.html"' in H['content/index.html']
    assert 'href="dev/differences.html">differences ledger</a>' in H['verification.html']
    assert dif.count('<article class="kcard dif" id="DIF-01">') == 1 and '<td class="g-title">Whether the crawl budget formula is documented</td>' in dif
    assert 'href="../claims.html#D2-C001"' in dif and 'href="../claims.html#D1-C006"' in dif and 'href="../claims.html#D1-C005"' in dif and 'class="on">Developers</a>' in dif
    assert num.count('<article class="kcard copyable num"') == 1 and 'id="F-001"' in num and 'href="../content/facts.html#F-001"' in num
    assert qb.count('<article class="kcard qb"') == 2 and 'id="q-D1-C002"' in qb and 'href="../claims.html#D1-C010"' in qb
    for f in ('differences.json', 'numbers.json', 'question-bank.json'): assert (O / 'downloads' / f).exists(), f
    assert 'href="../downloads/differences.json"' in dif and 'href="../downloads/numbers.json"' in num and 'href="../downloads/question-bank.json"' in qb
    for p, t in H.items(): assert 'D1-C007' not in t and 'SECRETPRIVATEMARKER' not in t, p
    # a tampered ledger stops the web edition: a claim that is not public, and a registry that drops a stat fact
    P = root / '60-outputs' / 'agent-pack'
    keep = {n: (P / n).read_bytes() for n in ('differences.json', 'numbers.json')}
    try:
        d = json.loads(keep['differences.json'])
        d['rows'][0]['event'][0]['id'] = 'D1-C007'
        (P / 'differences.json').write_text(json.dumps(d), encoding='utf-8')
        code, out = build_site(root)
        assert code != 0 and 'differences.json DIF-01: claim D1-C007 is not a public claim of claims.jsonl' in out, out[-500:]
        (P / 'differences.json').write_bytes(keep['differences.json'])
        n = json.loads(keep['numbers.json'])
        n['facts'] = []
        (P / 'numbers.json').write_text(json.dumps(n), encoding='utf-8')
        code, out = build_site(root)
        assert code != 0 and 'numbers.json: the registry must list every stat fact' in out, out[-500:]
    finally:
        for k, v in keep.items(): (P / k).write_bytes(v)


def test_real_ledgers():  # knowledge graph phase 3 on the real data: every stat fact in the registry, every row on public claims, the pages and their links
    root = real_site_root()
    led = check_ledgers(root)
    N, D, Q = led.get('numbers'), led['differences'], led.get('question-bank')  # numbers and question bank: the full edition only
    pages = LEDGER_PAGES[:1] if COMMUNITY else LEDGER_PAGES
    assert 10 <= len(D['rows']) <= 20, f'the plan keeps the differences ledger to 10 to 20 rows, found {len(D["rows"])}'
    assert len({r['id'] for r in D['rows']}) == len(D['rows']) and all(re.fullmatch(r'DIF-\d\d', r['id']) for r in D['rows'])
    private = [c['id'] for f in sorted((REPO / '20-claims').glob('day*.yaml')) for c in yaml.safe_load(f.read_text(encoding='utf-8')) or [] if c.get('private')]
    O = root / '60-outputs' / 'site'
    H = {p: (O / p).read_text(encoding='utf-8') for p in pages}
    assert not COMMUNITY or not [p for p in LEDGER_PAGES[1:] if (O / p).exists()], 'the community edition has no numbers and questions pages'
    for p, t in H.items():
        leaked = [c for c in private if re.search(rf'\b{c}\b', t)]
        assert not leaked and 'img_4692' not in t.lower(), (p, leaked)
    dif = H['dev/differences.html']
    assert dif.count('<article class="kcard dif"') == len(D['rows']) and all(f'id="{r["id"]}"' in dif for r in D['rows'])
    if not COMMUNITY:
        num, qb = H['content/numbers.html'], H['content/questions.html']
        assert num.count('<article class="kcard copyable num"') == len(N['facts']) and all(f'id="{f["id"]}"' in num for f in N['facts'])
        assert qb.count('<article class="kcard qb"') == len(Q['audience']) and qb.count('<li class="qt kcard') == len(Q['things'])
    # every link of the three pages resolves: a file of the site, and an anchor that exists in it
    ids = lambda h: set(re.findall(r'\bid="([^"]+)"', h))
    cache, bad = {}, []
    for p, t in H.items():
        for href in re.findall(r'href="([^"#:]*)(?:#([^"]*))?"', t):
            target, frag = href
            if not target and not frag: continue
            f = (O / p).parent / html.unescape(target) if target else O / p
            if not f.resolve().exists(): bad.append((p, target)); continue
            if frag and f.suffix == '.html':
                cache.setdefault(f, ids(f.read_text(encoding='utf-8')))
                if html.unescape(frag) not in cache[f] and not re.fullmatch(r'(ent|topic|claim|session|source):.+', html.unescape(frag)): bad.append((p, f'{target}#{frag}'))
    assert not bad, bad[:10]
    # a thing's card links its rows of the ledger and its question in the bank
    card = (O / 'entities' / 'http-429.html').read_text(encoding='utf-8')
    rows429 = [r['id'] for r in D['rows'] if any(x['id'] == 'http-429' for x in r['entities'])]
    assert rows429 and all(f'href="../dev/differences.html#{r}"' in card for r in rows429)
    assert ('href="../content/questions.html#t-http-429"' in card) != COMMUNITY, 'a card links its question in the bank in the full edition only'
    pw_ = browser()
    if not pw_: print('    browser check: skipped (Playwright not installed)'); return
    errs = []
    with pw_() as pw:
        b = pw.chromium.launch()
        try:
            for scheme in ('light', 'dark'):
                for wd in (1280, 390):
                    ctx = b.new_context(viewport={'width': wd, 'height': 900}, color_scheme=scheme)
                    pg = ctx.new_page()
                    pg.on('pageerror', lambda e: errs.append(str(e)))
                    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                    for p in pages:
                        pg.goto((O / p).as_uri())
                        r = pg.evaluate("() => [document.documentElement.scrollWidth, document.documentElement.clientWidth, document.documentElement.dataset.style, "
                                        "document.querySelectorAll('.kit-filter[hidden], .copyable .copy[hidden]').length]")
                        if r[0] > r[1] or r[2] != 'deep-dive' or r[3]: errs.append(f'{scheme} {wd}px {p}: sideways scroll, wrong style or a control left hidden {r}')
                    ctx.close()
            if not COMMUNITY:
                pg = b.new_page(viewport={'width': 1280, 'height': 900})
                pg.goto((O / 'content/questions.html').as_uri())
                n = len(Q['things'])
                pg.uncheck('.kit-filter input[value=status-code]')
                got = pg.evaluate("() => [[...document.querySelectorAll('.qt')].filter(x => !x.hidden).length, document.querySelector('.qt-grid .filter-n, .filter-n').textContent]")
                k = sum(t['kind'] == 'status-code' for t in Q['things'])
                if got[0] != n - k or f'{n - k} of {n} things shown' != got[1]: errs.append(f'the kind filter of the question bank: {got}')
        finally:
            b.close()
    assert not errs, errs[:5]
    if COMMUNITY: print(f'    community edition: {len(D["rows"])} differences, no numbers registry or question bank; 1 page in 2 schemes and 2 widths')
    else: print(f'    {len(N["facts"])} stat facts, {len(D["rows"])} differences, {len(Q["audience"])} audience questions and {len(Q["things"])} things; 3 pages in 2 schemes and 2 widths')


# ---------------------------------------------------------------- the community edition (_system/edition.yaml says edition: community)
WALLED_SITE = [f'content/{x}.html' for x in ('facts', 'myths', 'angles', 'quotes', 'numbers', 'questions')]
WALLED_FILES = ['60-outputs/content/' + x for x in ('fact-sheet.md', 'myths-and-facts.md', 'story-angles.md', 'quotes.md', 'questions.md', 'questions.json')] \
    + ['50-maps/numbers.md', '60-outputs/agent-pack/numbers.json', '60-outputs/agent-pack/question-bank.json']
MD_DIRS = ('30-topics', '40-sessions', '50-maps', '60-outputs')


def dead_links(root):
    """Every internal link of a built tree that does not resolve: the web edition's pages (href and src, anchors included; a Reef map
    link names a node of its data) and the URLs of its search index and graph data, and every generated Markdown file (links, images
    and anchors outside code; a link out of the build resolves in the repository, as readme_problems does)."""
    site, bad, ids = root / '60-outputs' / 'site', [], {}
    nodes = {n['i'] for n in graph_data(site / 'assets' / 'graph-data.js')['nodes']}
    def html_ids(f):
        if f not in ids: ids[f] = set(re.findall(r'\b(?:id|name)="([^"]+)"', f.read_text(encoding='utf-8')))
        return ids[f]
    def md_ids(f):
        if f not in ids:
            txt, seen, out = f.read_text(encoding='utf-8'), {}, set()
            for h in re.findall(r'^#{1,6} (.+?)#*\s*$', FENCED.sub('', txt), re.M):
                h = re.sub(r'<[^>]+>', '', re.sub(r'`([^`]*)`', lambda m: m[1].replace('<', '').replace('>', ''), h))
                h = html.unescape(re.sub(r'\\(.)', r'\1', re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', h).replace('*', '')))
                s = re.sub(r'[^\w\- ]', '', h.strip().lower()).replace(' ', '-')
                out.add(s if s not in seen else f'{s}-{seen[s]}'); seen[s] = seen.get(s, 0) + 1
            ids[f] = out | set(re.findall(r'<a (?:id|name)="([^"]+)"', txt))
        return ids[f]
    def check(src, base, ref, md=False):
        if not ref or re.match(r'[A-Za-z][A-Za-z0-9+.-]*:|//', ref): return
        path, _, frag = html.unescape(ref).partition('#')
        f = base / path.split('?')[0] if path else src
        if not f.exists() and md:
            try: f = REPO / os.path.relpath(f, root)
            except ValueError: pass
        f = Path(os.path.normpath(f))
        if not f.exists(): bad.append(f'{src.relative_to(root).as_posix()}: {ref}'); return
        if not frag: return
        if f.name == 'graph.html': ok = frag in nodes or frag in html_ids(f)
        elif f.suffix == '.html': ok = frag in html_ids(f)
        elif f.suffix == '.md': ok = frag in md_ids(f)
        else: ok = True
        if not ok: bad.append(f'{src.relative_to(root).as_posix()}: {ref} (no anchor)')
    for f in sorted(site.rglob('*.html')):
        for ref in re.findall(r'\b(?:href|src)="([^"]*)"', re.sub(r'<script\b[^>]*>.*?</script>', '', f.read_text(encoding='utf-8'), flags=re.S)): check(f, f.parent, ref)
    for f in sorted((site / 'assets').glob('*.js')):
        for ref in set(re.findall(r'"((?:[a-z0-9_-]+/)*[A-Za-z0-9_.-]+\.html(?:#[^"]*)?)"', f.read_text(encoding='utf-8'))): check(f, site, ref)
    for f in sorted(x for d in MD_DIRS for x in (root / d).rglob('*.md') if 'site' not in x.relative_to(root).parts):
        txt = f.read_text(encoding='utf-8')
        body = outside_code(txt)
        for ref in re.findall(r'\]\(<?([^)\s>]+)>?(?:\s+"[^"]*")?\)', body) + re.findall(r'<img [^>]*?src="([^"]*)"', body) + re.findall(r'srcset="([^"]*)"', body):
            check(f, f.parent, ref, md=True)
    return bad


AVOIDED = re.compile('propri' 'etary|commercial ' 'licen', re.I)  # words the community edition never uses, kept split so that git grep finds them nowhere in the branch, this file included
AVOIDED_DOCS = ('README.md', 'LICENSE', 'LICENSE-CONTENT.md', 'NOTICE.md', 'PRIVACY.md', 'METHOD.md', 'CHANGELOG.md', '_system/README.md', '_system/templates/AGENTS.md')


def community_publishing(root, ed, pages):
    """The community edition as it is published: the 1-minute tour on the home page (the one video of the site, never autoplaying),
    the method write-up and the footer's way to it, the footer's licence line, Impressum and Privacy; with site_url the canonical
    address, the social tags and share image, JSON-LD that parses, sitemap.xml and 404.html; and none of the words this edition avoids."""
    O = root / '60-outputs' / 'site'
    rel = lambda f: f.relative_to(O).as_posix()
    texts = {rel(f): f.read_text(encoding='utf-8') for f in pages}
    framed = {p: t for p, t in texts.items() if t.lstrip().startswith('<!doctype html>') and 'class="foot-k"' in t}
    home, about = texts['index.html'], texts['about.html']
    su, repo = ed['site_url'], ed['repo_url']
    # the tour: one video, on the home page, with controls, nothing loaded or played before the reader presses play
    media = sorted(rel(f) for f in O.rglob('*') if f.suffix.lower() in ('.mp4', '.webm', '.mov', '.m4v', '.ogv'))
    src = root / '_system' / 'brand' / 'video'
    assert not [p for p, t in texts.items() if re.search(r'<(video|audio)\b[^>]*\bautoplay', t)], 'a video or sound plays by itself'
    if (src / 'tour.mp4').exists() and (src / 'tour-poster.jpg').exists():
        assert {p: t.count('<video') for p, t in texts.items() if '<video' in t} == {'index.html': 1} and media == ['assets/video/tour.mp4'], media
        assert re.search(r'<section class="tour" id="tour"[^>]*><h2[^>]*>Watch the 1-minute tour</h2>.*?<video controls preload="none" playsinline '
                         r'poster="assets/video/tour-poster\.jpg"[^>]*><source src="assets/video/tour\.mp4" type="video/mp4">', home, re.S), 'no tour section'
        assert all((O / 'assets' / 'video' / n).read_bytes() == (src / n).read_bytes() for n in ('tour.mp4', 'tour-poster.jpg'))
    else: assert not media and 'id="tour"' not in home, media
    # the method write-up: its own page, linked from About, the home page and every page's footer
    md = root / 'METHOD.md'
    m = (O / 'method.html').read_text(encoding='utf-8')
    if md.exists():
        title = re.search(r'^# (.+)$', md.read_text(encoding='utf-8'), re.M)[1].strip()
        assert html.unescape(re.search(r'<h1>(.*?)</h1>', m)[1]) == title and '<table' in m, title
    assert 'href="method.html"' in home and 'href="method.html"' in about
    assert not [p for p, t in framed.items() if not re.search(r'href="(\.\./)*method\.html">How the claims were graded</a>', t)], 'a footer without the method link'
    # the footer's legal line: the licences, linked to LICENSE-CONTENT.md in the repository, Impressum and Privacy; the edition's own links stay its own
    for p, t in framed.items():
        if not repo: assert 'class="foot-legal"' not in t, p; continue
        leg = re.findall(r'<p class="foot-legal">(.*?)</p>', t)
        assert len(leg) == 1 and f'href="{html.escape(repo)}/blob/HEAD/LICENSE-CONTENT.md"' in leg[0], p
        assert '>Content CC BY-NC 4.0 · Developer kit CC BY 4.0 · Code MIT</a>' in leg[0] and not AVOIDED.search(leg[0]), leg[0]
        assert all(f'href="{html.escape(u)}"' in leg[0] for u in (ed['impressum_url'], ed['privacy_url']) if u), leg[0]
    own = [x for x in (su, repo, ed['contact_url'], ed['impressum_url'], ed['privacy_url']) if x]
    wrong = {html.unescape(h) for t in texts.values() for h in re.findall(r'<a class="ext own" href="([^"]*)"', t)}
    wrong = {h for h in wrong if not any(h == x or h.startswith(x.rstrip('/') + '/') for x in own)}
    assert not wrong, wrong
    # published (site_url): every indexable page names its absolute address and shares with the one share image; search and 404 are noindex
    if su:
        img = root / '_system' / 'brand' / 'social' / 'og-image.png'
        meta = lambda t, k: [html.unescape(x) for x in re.findall(rf'<meta (?:property|name)="{k}" content="([^"]*)">', t)]
        bad = []
        for p, t in texts.items():
            canon = [html.unescape(x) for x in re.findall(r'<link rel="canonical" href="([^"]*)">', t)]
            if p in ('search.html', '404.html'):
                want = 'noindex, follow' if p == 'search.html' else 'noindex'
                if canon or meta(t, 'robots') != [want]: bad.append(f'{p}: {canon} {meta(t, "robots")}')
                continue
            url = su + ('' if p == 'index.html' else p)
            if canon != [url] or meta(t, 'og:url') != [url]: bad.append(f'{p}: canonical {canon}, og:url {meta(t, "og:url")}')
            if img.exists() and (meta(t, 'og:image') != [su + 'assets/social/og-image.png'] or meta(t, 'twitter:card') != ['summary_large_image']
                                 or meta(t, 'og:image:width') != ['1200'] or meta(t, 'og:image:height') != ['630'] or not meta(t, 'og:image:alt')): bad.append(f'{p}: share image')
            for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
                try: d = json.loads(b)
                except ValueError as x: bad.append(f'{p}: JSON-LD {x}'); continue
                if d.get('@type') == 'BreadcrumbList' and not (all(i.get('item', su).startswith(su) for i in d['itemListElement'])
                                                               and d['itemListElement'][-1].get('item') == url): bad.append(f'{p}: crumbs')
            if '<nav class="crumbs"' in t and '"@type":"BreadcrumbList"' not in t: bad.append(f'{p}: crumbs without BreadcrumbList')
        assert not bad, bad[:5]
        if img.exists(): assert (O / 'assets' / 'social' / 'og-image.png').read_bytes() == img.read_bytes()
        lds = {d['@type']: d for d in (json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', home, re.S))}
        assert lds['WebSite']['url'] == su and lds['WebSite']['inLanguage'] == 'en' and lds['Organization']['name'] == ed['company']['name'] \
            and lds['Organization']['url'] == ed['company']['url'] and ed['linkedin'] in lds['Organization']['sameAs'], lds
        # sitemap.xml: every indexable page, absolute, the version date of CHANGELOG.md as lastmod
        sm = ET.parse(O / 'sitemap.xml').getroot()
        ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
        locs, lms = [x.text for x in sm.iter(ns + 'loc')], {x.text for x in sm.iter(ns + 'lastmod')}
        want = [su] + sorted(su + p for p in texts if p not in ('index.html', 'search.html', '404.html'))
        vdate = re.search(r'^## v\d+\.\d+\.\d+[^\n]*?(\d{4}-\d\d-\d\d)', (root / 'CHANGELOG.md').read_text(encoding='utf-8'), re.M)[1]
        assert locs == want and lms == {vdate}, (len(locs), len(want), lms)
        # 404.html: served for a missing path at any depth, so it resolves from the site root: a plain <base> (the browser's preload
        # scanner and a reader without JavaScript see it too) before the first address of its head
        nf = texts['404.html']
        head = nf[:nf.index('</head>')]
        tag = f'<base href="{html.escape(su)}">'
        assert nf.count('<base ') == 1 and "createElement('base')" not in nf and 'Page not found' in nf, nf[:600]
        assert tag in head and head.index(tag) < min(head.index(x) for x in ('<link ', '<script')) and 'href="assets/site.css"' in head, head
    else: assert not (O / 'sitemap.xml').exists() and not (O / '404.html').exists()
    # the shared parts are described plainly (paraphrases, short quotations, links to Google's public documentation): AVOIDED appears in nothing published
    gen = [f for d in ('30-topics', '40-sessions', '50-maps', '60-outputs') for f in (root / d).rglob('*') if f.suffix in ('.md', '.html', '.js', '.css', '.json', '.xml', '.csv', '.yaml')]
    assert not [f.relative_to(root).as_posix() for f in gen if AVOIDED.search(f.read_text(encoding='utf-8'))], f'{AVOIDED.pattern!r} is published'
    assert not [d for d in AVOIDED_DOCS if (REPO / d).exists() and AVOIDED.search((REPO / d).read_text(encoding='utf-8'))], f'{AVOIDED.pattern!r} in a document of the repository'


def test_community_edition():  # the community edition of the real data: the media kit walled, its preview and the contact links shown, no dead link
    if not COMMUNITY: print('    skipped (this checkout builds the full edition: no _system/edition.yaml with edition: community)'); return
    root = kbq_root()
    O, P, C = root / '60-outputs' / 'site', root / '60-outputs' / 'agent-pack', root / '60-outputs' / 'content'
    ed = load_module(root / '_system' / 'edition.py', 'edition_test').load(root)
    company, linkedin, fk = ed['company'], ed['linkedin'], ed['full_kit']
    # the walled pages and files are not built; the open ones are
    there = [x for x in WALLED_SITE if (O / x).exists()] + [x for x in WALLED_FILES if (root / x).exists()] \
        + [f'downloads/{x}' for x in ('numbers.json', 'question-bank.json', 'content-library.json') if (O / 'downloads' / x).exists()]
    assert not there, f'the community edition builds media kit files: {there}'
    assert sorted(f.name for f in C.iterdir()) == ['README.md', 'content-library.json', 'glossary.md'], sorted(f.name for f in C.iterdir())
    assert (O / 'content' / 'glossary.html').exists() and all((O / 'dev' / x).exists() for x in ('index.html', 'checklist.html', 'snippets.html', 'differences.html'))
    # the agent pack: the reduced content library, the preview exactly as 25-kits/content.yaml keeps it
    kit = yaml.safe_load((root / '25-kits' / 'content.yaml').read_text(encoding='utf-8'))
    lib = json.loads((P / 'content-library.json').read_text(encoding='utf-8'))
    assert lib['edition'] == 'community' and isinstance(lib['note'], str) and lib['note'] and (C / 'content-library.json').read_bytes() == (P / 'content-library.json').read_bytes()
    preview = {k: [x['id'] for x in kit.get(k) or []] for k in ('facts', 'myths', 'quotes', 'angles')}
    assert {k: [x['id'] for x in lib[k]] for k in preview} == preview and 0 < sum(map(len, preview.values())) <= 10, preview
    assert len(lib['glossary']) == len(kit['glossary']) and lib['wording_rules'] == kit['wording_rules']
    ids = [i for v in preview.values() for i in v]
    # the Content page: the wall, the counts of the full kit, the preview as cards, the note with the two links, the open glossary
    h = (O / 'content' / 'index.html').read_text(encoding='utf-8')
    assert 'The full media kit is not part of this community edition.' in h and f'{fk["facts"]} facts' in h and f'{fk["quotes"]} short quotations' in h, h[:500]
    assert all(f'id="{i}"' in h for i in ids) and h.count('<article class="kcard') == len(ids), ids
    assert 'Want to create content from it, at scale?' in h and re.search(r'href="(\.\./content/)?glossary\.html"', h)
    link = lambda u: f'href="{html.escape(u)}" rel="noopener external" target="_blank"'
    assert link(company['url']) in h and link(linkedin) in h and f'>{html.escape(company["name"])}</a>' in h
    # the Developers page keeps the kit and has the one note on working together; the subpages one quiet line to it; About who made it
    dev = (O / 'dev' / 'index.html').read_text(encoding='utf-8')
    assert dev.count('id="with-us"') == 1 and 'From checklist to an agent that guards every site' in dev and link(linkedin) in dev
    assert dev.count('<article class="req"') == sum(len(a['requirements']) for a in json.loads((P / 'dev-requirements.json').read_text(encoding='utf-8'))['areas'])
    assert all(re.search(r'href="(\.\./dev/)?index\.html#with-us"', (O / 'dev' / x).read_text(encoding='utf-8')) for x in ('checklist.html', 'snippets.html', 'differences.html'))
    about = (O / 'about.html').read_text(encoding='utf-8')
    assert 'id="who"' in about and ed['author'] in about and link(company['url']) in about and 'Open for collaboration on this community version' in about
    # every page: the edition in the masthead, one quiet footer line, and no other web link of the edition than the two of edition.yaml
    pages = sorted(O.rglob('*.html'))
    allowed = {company['url'], linkedin}
    bad = []
    for f in pages:
        t = f.read_text(encoding='utf-8')
        if not t.lstrip().startswith('<!doctype html>') or 'class="foot-k"' not in t: continue  # the copied mindmap and Reef map have their own frame
        rel = f.relative_to(O).as_posix()
        if ' · Community edition<span>' not in t or t.count('<p class="foot-ed">') != 1: bad.append(f'{rel}: no edition in the masthead or no footer line')
        if {html.unescape(u) for u in re.findall(r'<a class="ext contact" href="([^"]*)"', t)} - allowed: bad.append(f'{rel}: a contact link not in edition.yaml')
    assert not bad, bad[:5]
    # search leaves the media kit out; the agent query layer answers kit searches from the preview with a friendly note
    sd = (O / 'assets' / 'search-data.js').read_text(encoding='utf-8')
    data = json.loads(sd[sd.index('=') + 1:].strip().rstrip(';'))
    assert all(data[k] == [] for k in ('facts', 'myths', 'quotes', 'angles')) and len(data['glossary']) == len(kit['glossary']) and data['reqs']
    code, s = kbq(root, 'search', 'crawl budget', '--kind', 'fact')
    assert code == 0 and 'community edition' in s['edition_note'] and {x['id'] for x in s['results']} <= {f'fact:{i}' for i in preview['facts']}, s
    code, s = kbq(root, 'neighbours', 'fact:F-001')
    assert code == 1 and 'not part of this community edition' in s['error'] and 'Traceback' not in json.dumps(s), s
    code, a = kbq(root, 'about')
    assert code == 0 and a['edition'] == 'community' and a['edition_note'], a.get('edition')
    assert 'Community edition' in (P / 'AGENTS.md').read_text(encoding='utf-8')
    community_publishing(root, ed, pages)
    # no dead link anywhere: the web edition, its search and map data, and the generated Markdown
    dead = dead_links(root)
    assert not dead, f'{len(dead)} dead links: {dead[:10]}'
    print(f'    {len(ids)} preview items, {len(pages)} pages, no dead link, contact links {company["url"]} and {linkedin}')


def test_kit_edition_matches_the_build():  # content.yaml's edition and edition.yaml's must agree: a checkout that lost edition.yaml or
    # edition.py stops instead of building the full edition's pages from the community preview, and the full kit never becomes the preview
    kit_ed = lambda ed: ('25-kits/content.yaml', 'wording_rules:', f'edition: {ed}\nwording_rules:')
    community_yaml = ('_system/edition.yaml', None, 'edition: community\nauthor: Test Author\nlinkedin: https://example.org/in/test\n'
                      'company: {name: Test Co, url: "https://example.org"}\n'
                      'full_kit: {facts: 1, myths: 1, angles: 1, quotes: 1, stat_facts: 1, audience_questions: 1}\n')
    for name, edits, msg in (
            ('kit-ed-lost', [kit_ed('community')], "25-kits/content.yaml is the community edition's kit, but this build makes the full edition: "
                                                   'it needs _system/edition.yaml with "edition: community" and _system/edition.py'),
            ('kit-ed-bad', [kit_ed('premium')], "25-kits/content.yaml: edition must be one of full, community, found 'premium'"),
            ('kit-ed-full-kit', [community_yaml], "25-kits/content.yaml is the full edition's kit, but this build makes the community edition")):
        root = make_fixture(name, edits)
        code, out = build(root)
        assert code != 0 and msg in out and 'Nothing was written' in out and 'Traceback' not in out, out[-1500:]
        assert not (root / '60-outputs' / 'content' / 'fact-sheet.md').exists() and not (root / '60-outputs' / 'agent-pack').exists(), name
    code, out = build(make_fixture('kit-ed-full', [kit_ed('full')]), '--check')
    assert code == 0, out[-1500:]


def main(argv):
    tests = [(n, f) for n, f in globals().items() if n.startswith('test_') and callable(f)]
    if '-k' in argv: tests = [(n, f) for n, f in tests if argv[argv.index('-k') + 1] in n]
    failed = 0
    print(f'Fixtures in {TMP}')
    for n, f in tests:
        try:
            f(); print(f'PASS {n}')
        except Exception as e:
            failed += 1
            print(f'FAIL {n}: {e}' if isinstance(e, AssertionError) else f'FAIL {n}:\n{traceback.format_exc()}')
    if '--keep' not in argv: shutil.rmtree(TMP, ignore_errors=True)
    print(f'{len(tests) - failed}/{len(tests)} passed')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main(sys.argv[1:])
