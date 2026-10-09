# One rel=canonical per page, pointing straight at the final URL

Exactly one absolute canonical in the server-sent `<head>`, self-referencing on the preferred URL and identical on its duplicates (tracking parameters, sort orders, print views). The target must answer 200, be indexable, not redirect and be in the same language. Non-HTML files can declare it in an HTTP `Link` header.

```html
<!-- On https://www.example.com/chairs/oak-dining-chair
     and on https://www.example.com/chairs/oak-dining-chair?utm_source=newsletter -->
<head>
  <link rel="canonical" href="https://www.example.com/chairs/oak-dining-chair">
</head>
```

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Link: <https://www.example.com/guides/chair-care.pdf>; rel="canonical"
```
