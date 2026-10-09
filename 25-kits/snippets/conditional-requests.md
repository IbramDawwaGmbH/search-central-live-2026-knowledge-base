# ETag and 304 Not Modified for crawlers

Send a validator (ETag, which Google's crawling team prefers, or Last-Modified) and answer a matching conditional request with 304 and no body, so unchanged pages cost almost nothing to recrawl. Express does this for you when it sends the body, but its ETag hashes the whole response: if the HTML embeds a CSP nonce, a CSRF token or a timestamp, compute the ETag from the content data instead (for example a hash of the product record and the template version) and set it with `res.set('ETag', ...)`.

```http
GET /chairs/oak-dining-chair HTTP/1.1
Host: www.example.com
If-None-Match: "a3f9c2e1"

HTTP/1.1 304 Not Modified
ETag: "a3f9c2e1"
Cache-Control: no-cache
```

```js
// Express: strong ETags, and an automatic 304 when If-None-Match matches
const express = require('express');
const app = express();
app.set('etag', 'strong');

app.get('/chairs/:slug', async (req, res) => {
  const html = await renderChairPage(req.params.slug); // your server-side renderer
  res.set('Cache-Control', 'no-cache'); // may be stored, but must be revalidated
  res.type('html').send(html); // res.send() compares the ETag and answers 304 when fresh
});

// Pages with a per-request nonce or CSRF token: an ETag from the data, not from the body
const crypto = require('crypto');
const TEMPLATE_VERSION = '2026-10-02';
app.get('/products/:slug', async (req, res) => {
  const product = await loadProduct(req.params.slug); // your data access
  const etag = '"' + crypto.createHash('sha256').update(JSON.stringify(product) + TEMPLATE_VERSION).digest('hex').slice(0, 16) + '"';
  res.set('ETag', etag);
  res.set('Cache-Control', 'no-cache');
  if (req.fresh) return res.status(304).end(); // If-None-Match matches the data ETag
  res.type('html').send(renderProductPage(product, res.locals.cspNonce));
});
```
