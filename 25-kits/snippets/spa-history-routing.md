# Single-page app routing with the History API instead of #/ routes

Every view gets a real path in a real `<a href>`; JavaScript intercepts the click, updates the address with `pushState` and renders the view, so users skip full reloads while Google can follow the links. The server must answer a direct request for each path with the full page (ideally server-rendered) and unknown paths with 404. The not-found view is a route of its own, so a shell served with 404 renders it instead of redirecting again.

```html
<nav>
  <a href="/" data-link>Home</a>
  <a href="/chairs/" data-link>Chairs</a>
  <a href="/tables/" data-link>Tables</a>
</nav>
<main id="app"></main>

<script>
  const routes = {
    '/': () => '<h1>Example Shop</h1>',
    '/chairs/': () => '<h1>Chairs</h1>',
    '/tables/': () => '<h1>Tables</h1>',
    '/not-found': () => '<h1>Page not found</h1>', // the server answers this URL with 404
  };

  function renderRoute(path) {
    const view = routes[path];
    if (!view) {
      // Unknown route on a 200 URL: go to the URL the server answers with 404 (once; never loop)
      if (path !== '/not-found') window.location.replace('/not-found');
      return;
    }
    document.getElementById('app').innerHTML = view();
  }

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[data-link]');
    if (!link || link.origin !== location.origin) return;
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    history.pushState({}, '', link.pathname + link.search);
    renderRoute(link.pathname);
  });

  window.addEventListener('popstate', () => renderRoute(location.pathname));
  renderRoute(location.pathname);
</script>
```
