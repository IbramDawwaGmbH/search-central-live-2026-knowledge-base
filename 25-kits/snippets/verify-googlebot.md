# Verify that a request really comes from Googlebot

Before a firewall, CDN or bot-protection rule blocks or challenges a "Googlebot" request, verify it: the user-agent string alone can be faked. In WAF rules, prefer matching the IP against the ranges Google publishes as common-crawlers.json and special-crawlers.json on its page on verifying its crawlers; for log analysis, a reverse DNS lookup followed by a forward lookup works too. Never allowlist a whole googleusercontent.com host: Google Cloud customer VMs resolve there too, and only *.gae.googleusercontent.com belongs to Google's user-triggered fetchers, which are not Googlebot.

```bash
# 1. Reverse DNS: Googlebot and Google's other common crawlers resolve to crawl-*.googlebot.com
#    or geo-crawl-*.geo.googlebot.com; special-case crawlers to rate-limited-proxy-*.google.com.
#    A host such as 81.59.117.34.bc.googleusercontent.com is a Google Cloud customer, not Googlebot.
host 66.249.66.1
# -> 1.66.249.66.in-addr.arpa domain name pointer crawl-66-249-66-1.googlebot.com.

# 2. Forward DNS: that host name must resolve back to the same IP
host crawl-66-249-66-1.googlebot.com
# -> crawl-66-249-66-1.googlebot.com has address 66.249.66.1
```

The published IP ranges are easier to keep in sync with WAF and CDN allowlists than DNS lookups:

```bash
# Common crawlers (Googlebot and others) and special-case crawlers; refresh the lists regularly
curl -s https://developers.google.com/static/crawling/ipranges/common-crawlers.json
curl -s https://developers.google.com/static/crawling/ipranges/special-crawlers.json
```
