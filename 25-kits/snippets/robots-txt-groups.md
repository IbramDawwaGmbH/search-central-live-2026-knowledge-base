# Complete robots.txt groups for named crawlers

A crawler obeys only the most specific group that names it and ignores the `*` group, so groups are not additive: a named group must repeat every shared rule that should still apply to that crawler. One group can name several crawlers, and Google combines all groups that name the same user agent into one.

```text
# WRONG: the googlebot group replaces the * group instead of adding to it,
# so Googlebot may crawl /goats/ and /cows/ and only /dogs/ is closed to it
User-agent: *
Disallow: /goats/
Disallow: /cows/

User-agent: googlebot
Disallow: /dogs/
```

Right: the shared rules sit in the `*` group, and the named group repeats them before adding its own. To open /staging/preview/ to Googlebot while the rest of /staging/ stays closed to it, the Googlebot group needs both the disallow and the allow; an allow in the `*` group, or a Googlebot group with only the allow, does not do it.

```text
# Shared rules for every crawler without a group of its own
User-agent: *
Disallow: /goats/
Disallow: /cows/
Disallow: /staging/

# Googlebot: the shared rules again, plus its own
User-agent: googlebot
Disallow: /goats/
Disallow: /cows/
Disallow: /dogs/
Disallow: /staging/
Allow: /staging/preview/

# Several crawlers can share one group: stack their user-agent lines with nothing in between
User-agent: bingbot
User-agent: applebot
Disallow: /goats/
Disallow: /cows/
Disallow: /staging/

Sitemap: https://www.example.com/sitemap.xml
```
