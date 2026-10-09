# Lazy loading that works without scrolling

Googlebot does not scroll; it renders with a very tall viewport. Use native `loading="lazy"` for images and iframes, and load list chunks with an IntersectionObserver on a sentinel element, never with a `scroll` event listener. The plain `<a href>` links to the paginated URLs stay in the page whatever the script does, so the rendered HTML always links to the next page.

```html
<!-- Images and iframes: native lazy loading, real src in the HTML -->
<img src="/img/oak-chair-800.webp" alt="Oak dining chair with a woven paper-cord seat" width="800" height="600" loading="lazy">

<!-- Lists: page 1 of /chairs/, a sentinel for the observer, and pagination links the script never removes -->
<ul id="products">
  <li><a href="/chairs/oak-dining-chair">Oak dining chair</a></li>
</ul>
<div id="load-more-sentinel" style="height: 1px"></div>
<nav aria-label="Pagination">
  <a href="/chairs/" aria-current="page">1</a>
  <a href="/chairs/?page=2">2</a>
  <a href="/chairs/?page=3">3</a>
  <a href="/chairs/?page=2">Next page</a>
</nav>

<!-- Avoid: window.addEventListener('scroll', loadMoreProducts) never runs for Googlebot -->

<script>
  const list = document.getElementById('products');
  const sentinel = document.getElementById('load-more-sentinel');
  let next = '/chairs/?page=2'; // written by the server: the next page's URL, empty on the last page

  const observer = new IntersectionObserver(async ([entry]) => {
    if (!entry.isIntersecting || !next) return;
    observer.unobserve(sentinel);
    const url = new URL(next, location.href);
    const res = await fetch('/fragments' + url.pathname + url.search); // returns the <li> items of that page
    if (!res.ok) { observer.disconnect(); return; } // keep the links; never insert an error page
    list.insertAdjacentHTML('beforeend', await res.text());
    history.replaceState({}, '', url.pathname + url.search); // the URL follows the chunk once it is in place
    next = res.headers.get('X-Next-Page') || ''; // e.g. "/chairs/?page=3", absent on the last page
    if (next) observer.observe(sentinel); else observer.disconnect();
  });

  if (next) observer.observe(sentinel);
</script>
```
