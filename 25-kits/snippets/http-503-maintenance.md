# Planned maintenance with 503 (robots.txt stays available)

During a short outage every page answers 503 Service Unavailable, never a 200 "we'll be back" page and never a 404. Keep it to a day or two, and keep serving robots.txt normally: a 5xx on robots.txt stops crawling of the whole site.

```http
HTTP/1.1 503 Service Unavailable
Content-Type: text/html; charset=utf-8
Retry-After: 3600
Cache-Control: no-store
```

```nginx
server {
    listen 443 ssl;
    server_name www.example.com;
    ssl_certificate     /etc/ssl/www.example.com.crt;
    ssl_certificate_key /etc/ssl/www.example.com.key;

    error_page 503 /maintenance.html;

    location = /maintenance.html {
        root /var/www/static;
        internal;
        # add_header here replaces server-level add_header lines: repeat HSTS or CSP if you set them
        add_header Retry-After 3600 always;
        add_header Cache-Control "no-store" always;
    }

    # robots.txt keeps answering 200 during maintenance
    location = /robots.txt {
        root /var/www/static;
    }

    location / {
        return 503;
    }
}
```
