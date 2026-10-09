# XML sitemap with canonical URLs and real lastmod dates

List only canonical, indexable URLs that answer 200 (no redirects, no noindex, no parameters you canonicalise away), with a `lastmod` that changes only for significant updates (the main content, structured data or links), never for footer, copyright or timestamp changes; Google uses `lastmod` only when it is consistently accurate. Split large sites with a sitemap index (at most 50,000 URLs or 50 MB uncompressed per file), reference it in robots.txt and submit it in Search Console.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://www.example.com/sitemaps/products-1.xml</loc>
    <lastmod>2026-09-30T06:00:00+00:00</lastmod>
  </sitemap>
</sitemapindex>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.example.com/chairs/oak-dining-chair</loc>
    <lastmod>2026-09-28T10:15:00+00:00</lastmod>
  </url>
  <url>
    <loc>https://www.example.com/chairs/beech-stool</loc>
    <lastmod>2026-09-12T08:00:00+00:00</lastmod>
  </url>
</urlset>
```
