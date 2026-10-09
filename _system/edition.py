"""Which edition the build makes: the full edition (main branch) or the community edition (community branch).

Read from _system/edition.yaml. Without the file, or with "edition: full", it is the full edition, so the main branch
builds exactly as before. Used by build_kb.py, kits.py, kb_query.py (through the pack) and site/build_site.py.

The web addresses of the published community edition (site_url, repo_url, contact_url, impressum_url, privacy_url) are
optional: each one left out is '' and whatever uses it is simply not written. Only the web edition reads them (canonical
links, social previews, sitemap.xml, 404.html, the footer's Impressum, Privacy and licence links); the full edition never.
"""
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
EDITIONS = ('full', 'community')
URLS = ('site_url', 'repo_url', 'contact_url', 'impressum_url', 'privacy_url')  # where the community edition is published, and its legal pages


def load(root=None):
    """The edition settings as a dict: edition ('full' or 'community'), author, linkedin, company {name, url}, full_kit, and the
    web addresses of URLS ('' when not set; site_url always ends in '/', repo_url never does)."""
    base = Path(root) / '_system' if root else HERE
    f = base / 'edition.yaml'
    d = (yaml.safe_load(f.read_text(encoding='utf-8')) or {}) if f.exists() else {}
    ed = d.get('edition', 'full')
    if ed not in EDITIONS:
        raise SystemExit(f'ERROR: _system/edition.yaml: edition must be one of {", ".join(EDITIONS)}, not {ed!r}')
    company = d.get('company') or {}
    urls = {k: str(d.get(k) or '').strip() for k in URLS}
    if urls['site_url'] and not urls['site_url'].endswith('/'): urls['site_url'] += '/'
    urls['repo_url'] = urls['repo_url'].rstrip('/')
    return {'edition': ed, 'author': d.get('author', ''), 'linkedin': d.get('linkedin', ''),
            'company': {'name': company.get('name', ''), 'url': company.get('url', '')},
            'full_kit': d.get('full_kit') or {}, **urls}


def community(root=None):
    return load(root)['edition'] == 'community'
