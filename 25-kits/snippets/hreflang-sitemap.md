# hreflang in an XML sitemap

The sitemap method is equivalent to link elements and suits large sites or templates that cannot change the `<head>`. Use it instead of, not on top of, the HTML or HTTP-header method; every `<url>` lists all versions, itself included.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://www.example.com/en/chairs/</loc>
    <xhtml:link rel="alternate" hreflang="en" href="https://www.example.com/en/chairs/"/>
    <xhtml:link rel="alternate" hreflang="de-DE" href="https://www.example.com/de-de/stuehle/"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="https://www.example.com/"/>
  </url>
  <url>
    <loc>https://www.example.com/de-de/stuehle/</loc>
    <xhtml:link rel="alternate" hreflang="en" href="https://www.example.com/en/chairs/"/>
    <xhtml:link rel="alternate" hreflang="de-DE" href="https://www.example.com/de-de/stuehle/"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="https://www.example.com/"/>
  </url>
</urlset>
```
