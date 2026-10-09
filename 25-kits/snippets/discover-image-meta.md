# Large-image preview and lead image for Discover

Allow large image previews and name a large, relevant lead image (at least 1,200 px wide, 16x9, not the logo and not text-heavy) in the head of every article template; the same image belongs in the Article markup's `image` list.

```html
<head>
  <meta name="robots" content="max-snippet:-1, max-image-preview:large">
  <meta property="og:image" content="https://www.example.com/img/oak-care-16x9.webp">
  <meta property="og:image:width" content="1600">
  <meta property="og:image:height" content="900">
  <meta property="og:image:alt" content="Hand applying oil to an oak table top">
</head>
```
