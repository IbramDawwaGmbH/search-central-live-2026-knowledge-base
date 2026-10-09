# robots.txt that keeps cart and checkout open for Storebot-Google

A crawler follows only the most specific group that names it, so Storebot-Google, Google Shopping's crawler, uses its own group and ignores `*`. Repeat the general rules there but leave cart and checkout open, so it can verify prices, shipping and availability; every other crawler still stays out of them.

```text
# https://www.example.com/robots.txt
User-agent: *
Disallow: /search?
Disallow: /cart/
Disallow: /checkout/
Disallow: /api/
Allow: /api/products/

# Google Shopping's crawler: same rules, but cart and checkout stay crawlable
User-agent: Storebot-Google
Disallow: /search?
Disallow: /api/
Allow: /api/products/

Sitemap: https://www.example.com/sitemap.xml
```
