# Check every hop of a redirect chain against robots.txt

Robots.txt is checked for every URL in a redirect chain, and crawling stops at the first blocked hop, while Search Console shows the block on the first URL. This script follows server-side redirects one hop at a time, with Googlebot's user agent and with a browser's, and tests each hop against its own host's robots.txt. It needs `pip install requests protego` (Protego is an open-source robots.txt parser with Google-style wildcard and longest-match rules; confirm a doubtful result with Google's own parser, github.com/google/robotstxt). Meta refresh and JavaScript redirects are not followed: check those with URL Inspection's live test.

```python
# check_chain.py  -  usage: python check_chain.py https://www.example.com/page [more URLs]
import sys
from urllib.parse import urljoin, urlsplit

import requests
from protego import Protego

AGENTS = {
    "googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "browser": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
}
TOKEN = "Googlebot"  # the robots.txt token the rules are tested for
_robots = {}


def robots_for(url):
    parts = urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin not in _robots:
        r = requests.get(origin + "/robots.txt", headers={"User-Agent": AGENTS["googlebot"]}, timeout=10)
        if r.status_code == 200:
            text = r.text
        elif 400 <= r.status_code < 500 and r.status_code != 429:
            text = ""  # 4xx (except 429): Google crawls as if there were no robots.txt
        else:
            text = "User-agent: *\nDisallow: /"  # 5xx or 429: Google stops crawling the host for now
        _robots[origin] = Protego.parse(text)
    return _robots[origin]


def check(url, agent, max_hops=10):
    print(f"[{agent}]")
    for hop in range(max_hops + 1):
        allowed = robots_for(url).can_fetch(url, TOKEN)
        print(f"  {hop}: {'allowed' if allowed else 'BLOCKED by robots.txt'}  {url}")
        if not allowed:
            print("     crawling stops here; Search Console reports the first URL of the chain as blocked")
            return
        r = requests.get(url, headers={"User-Agent": AGENTS[agent]}, allow_redirects=False, timeout=10)
        location = r.headers.get("Location")
        if r.status_code in (301, 302, 303, 307, 308) and location:
            url = urljoin(url, location)
        else:
            print(f"     final status {r.status_code}")
            return
    print(f"     more than {max_hops} redirect hops")


if __name__ == "__main__":
    for start in sys.argv[1:]:
        for agent in AGENTS:  # different chains for the two user agents point to cloaking
            check(start, agent)
```
