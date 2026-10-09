# Crawlable links versus links Google cannot rely on

Google extracts links from `<a>` elements with an `href` that holds a real URL, both from the server HTML and from the rendered page. Click handlers, `javascript:` URLs, `routerLink` without `href`, `href` on other elements and `#` routes are not dependable.

```html
<!-- Crawlable: <a> with a real relative or absolute URL -->
<a href="/chairs/">Chairs</a>
<a href="https://www.example.com/chairs/oak-dining-chair">Oak dining chair</a>

<!-- Crawlable and still client-side routed: keep the href, intercept the click in JavaScript -->
<a href="/chairs/" data-link>Chairs</a>

<!-- Not dependable: do not use for anything that should be discovered -->
<a onclick="goTo('/chairs/')">Chairs</a>
<a routerLink="/chairs/">Chairs</a>
<a href="javascript:goTo('chairs')">Chairs</a>
<a href="#/chairs">Chairs</a>
<span data-href="/chairs/" onclick="location.href=this.dataset.href">Chairs</span>
<button type="button" onclick="location.href='/chairs/'">Chairs</button>
```
