# Image sitemap

Image sitemaps list, under each page's `<loc>`, the images that page uses, which helps Google find images that are loaded by JavaScript or are otherwise hard to discover. Only `image:image` and `image:loc` are used (caption, title, geo location and license tags are deprecated); up to 1,000 images per page.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>https://www.example.com/chairs/oak-dining-chair</loc>
    <image:image>
      <image:loc>https://www.example.com/img/oak-chair-1200.webp</image:loc>
    </image:image>
    <image:image>
      <image:loc>https://www.example.com/img/oak-chair-side-1200.webp</image:loc>
    </image:image>
  </url>
</urlset>
```
