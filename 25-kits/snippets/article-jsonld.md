# Article markup with images, dates and authors

Render one block per article on the server from the article's own fields: the headline, the visible lead image in 1x1, 4x3 and 16x9 versions, both dates with a UTC offset, and each author as a Person with a `url` to a real author page. Google does not require it for Top Stories but highly recommends it for all articles.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "How to care for an oak dining table",
  "image": [
    "https://www.example.com/img/oak-care-1x1.webp",
    "https://www.example.com/img/oak-care-4x3.webp",
    "https://www.example.com/img/oak-care-16x9.webp"
  ],
  "datePublished": "2026-10-02T08:00:00+02:00",
  "dateModified": "2026-10-02T09:20:00+02:00",
  "author": [
    {
      "@type": "Person",
      "name": "Jane Doe",
      "url": "https://www.example.com/authors/jane-doe/"
    },
    {
      "@type": "Person",
      "name": "John Roe",
      "url": "https://www.example.com/authors/john-roe/"
    }
  ]
}
</script>
```

For a paywalled article, add `isAccessibleForFree` and a `hasPart` element whose `cssSelector` names the section behind the paywall (the class must match the page's HTML).

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "How to care for an oak dining table",
  "datePublished": "2026-10-02T08:00:00+02:00",
  "isAccessibleForFree": false,
  "hasPart": {
    "@type": "WebPageElement",
    "isAccessibleForFree": false,
    "cssSelector": ".paywall"
  }
}
</script>
```
