# X-Robots-Tag header for PDFs, images and other non-HTML files

Files that cannot carry a meta tag get their robots rules as an HTTP response header. The same rules as the meta tag apply (`noindex`, `nosnippet`, `max-snippet`...), and the URL must stay crawlable for Google to see the header.

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
X-Robots-Tag: noindex
```

```nginx
# Inside the server block: office documents out of the index.
# An add_header in a location replaces every add_header set at server level for those responses:
# repeat your HSTS and CSP lines in each such location (or use the headers-more module).
location ~* \.(pdf|docx?|xlsx?)$ {
    add_header X-Robots-Tag "noindex" always;
    add_header Strict-Transport-Security "max-age=31536000" always;  # repeated from the server block
}

# Images that must not appear in Google Images (they still display on your pages)
location ^~ /internal-images/ {
    add_header X-Robots-Tag "noindex" always;
    add_header Strict-Transport-Security "max-age=31536000" always;  # repeated from the server block
}
```

```apache
<FilesMatch "\.(pdf|docx?|xlsx?)$">
  Header set X-Robots-Tag "noindex"
</FilesMatch>
```
