# robots.txt with crawl controls and a rendering carve-out

Disallow only URLs that should never be crawled (internal search, cart and checkout actions, filter parameters), keep every script, style and API path that pages need for rendering crawlable, and list the sitemap. Google reads only `user-agent`, `allow`, `disallow` and `sitemap`; each host (www, api, cdn) needs its own file at its root. Robots.txt is public, so never list secret paths in it.

```text
# https://www.example.com/robots.txt
User-agent: *
# Internal search results and cart/checkout actions (adapt to your URL patterns)
Disallow: /search?
Disallow: /cart/
Disallow: /checkout/
# (Shops in Google Shopping: give Storebot-Google its own group that leaves cart and checkout open.
#  A named group replaces this * group for that crawler, so repeat in it every rule that should still apply.)
# Filter and sort parameters of faceted navigation, as the first parameter (?) or a later one (&);
# /*?*size= would also block ?pagesize= and /*?*color= would block ?bgcolor=
Disallow: /*?color=
Disallow: /*&color=
Disallow: /*?size=
Disallow: /*&size=
Disallow: /*?sort=
Disallow: /*&sort=
# API: blocked in general, but the endpoints pages render from stay crawlable
# (the longer, more specific Allow rule wins)
Disallow: /api/
Allow: /api/products/
Allow: /api/reviews/
# Never disallow /static/, /assets/ or other JS and CSS folders

# Optional: keep content out of Gemini training and grounding (no effect on Google Search)
User-agent: Google-Extended
Disallow: /

Sitemap: https://www.example.com/sitemap.xml
```
