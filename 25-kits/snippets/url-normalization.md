# Redirect URL variants to the one URL the application expects

Build the expected URL from the route and the parameters the page really uses, in a fixed order, and answer any other spelling with one 301. Generate internal links with the same function so the site never links to a variant. The example is Express middleware; lowercasing the path assumes the site's routes are all lowercase.

```js
const ORIGIN = 'https://www.example.com';
// Parameters each route actually uses, in the order they must appear.
const PARAMS = { '/chairs': ['colour', 'page'], '/search': ['q'] };

function expectedUrl(pathname, searchParams) {
  let path = pathname.toLowerCase().replace(/\/{2,}/g, '/');
  if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
  const kept = new URLSearchParams();
  for (const name of PARAMS[path] || []) {
    const value = searchParams.get(name);
    if (value) kept.set(name, value); // unused and empty parameters are dropped
  }
  const query = kept.toString();      // spaces always come out as +
  return path + (query ? '?' + query : '');
}

app.set('trust proxy', true);         // so req.protocol is right behind a CDN or load balancer
app.use((req, res, next) => {
  const requested = new URL(ORIGIN + req.originalUrl); // not new URL(path, base): '//x' would parse as a host
  const expected = expectedUrl(requested.pathname, requested.searchParams);
  const wrongOrigin = req.protocol !== 'https' || req.hostname !== 'www.example.com';
  if (wrongOrigin || expected !== requested.pathname + requested.search) {
    return res.redirect(301, ORIGIN + expected); // one hop, straight to the final URL
  }
  next();
});
```
