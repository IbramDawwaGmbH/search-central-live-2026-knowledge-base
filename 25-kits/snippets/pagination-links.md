# Paginated listing with crawlable page links

Each page of a series has its own URL (`?page=n`), its own self-referencing canonical and plain `<a href>` links to the next page and back to the first page; the pages may share one title and description, so a page number in the title is optional. Do not canonicalise page 2 and later to page 1, and do not put page numbers in `#` fragments; Google no longer uses `rel=next`/`rel=prev`.

```html
<!-- https://www.example.com/chairs/?page=2 -->
<head>
  <title>Chairs, page 2 | Example Shop</title> <!-- the page number is optional -->
  <link rel="canonical" href="https://www.example.com/chairs/?page=2">
</head>
<body>
  <main>
    <h1>Chairs</h1>
    <ul>
      <li><a href="/chairs/oak-dining-chair">Oak dining chair</a></li>
      <li><a href="/chairs/beech-stool">Beech stool</a></li>
    </ul>
    <nav aria-label="Pagination">
      <a href="/chairs/">1</a>
      <a href="/chairs/?page=2" aria-current="page">2</a>
      <a href="/chairs/?page=3">3</a>
      <a href="/chairs/?page=3">Next page</a>
    </nav>
  </main>
</body>
```
