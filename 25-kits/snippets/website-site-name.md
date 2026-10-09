# WebSite markup for the preferred site name

Put one `WebSite` block on the home page of each domain or subdomain (not a subdirectory) that should have its own site name in Google's results. `url` is the canonical home page; `alternateName` is an optional fallback such as an acronym.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Example Shop",
  "alternateName": "ExShop",
  "url": "https://www.example.com/"
}
</script>
```
