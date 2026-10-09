# Robots meta tags for common page types

Put robots rules in the `<head>` of the HTML the server sends, one variant per page type below; never add, change or remove them with JavaScript. A `noindex` only works if the URL is not disallowed in robots.txt, because Google has to fetch the page to see it.

```html
<!-- Indexable templates: allow full-length snippets and large image and video previews -->
<meta name="robots" content="max-snippet:-1, max-image-preview:large, max-video-preview:-1">

<!-- Keep a page out of Search (internal admin, thin or temporary pages) -->
<meta name="robots" content="noindex">

<!-- The same rule for Google only -->
<meta name="googlebot" content="noindex">

<!-- Time-limited page (event, offer, job ad): drop it from results after the end date -->
<meta name="robots" content="unavailable_after: 2026-12-31T23:59:59+01:00">
```
