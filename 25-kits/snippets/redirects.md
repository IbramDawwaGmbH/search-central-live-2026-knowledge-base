# Permanent redirects to one host, one protocol, one hop

Send `http://` and the other host name to the preferred HTTPS host with a single 301, and send moved pages straight to their final URL (301 or 308). Keep migration redirects in place long term; avoid chains, meta refresh and JavaScript redirects for permanent moves.

```nginx
# http:// on both host names -> https://www. in one hop
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://www.example.com$request_uri;
}

# https:// on the bare domain -> https://www.
server {
    listen 443 ssl;
    server_name example.com;
    ssl_certificate     /etc/ssl/example.com.crt;
    ssl_certificate_key /etc/ssl/example.com.key;
    return 301 https://www.example.com$request_uri;
}

server {
    listen 443 ssl;
    http2 on;  # nginx 1.25.1+; older versions use "listen 443 ssl http2;"
    server_name www.example.com;
    ssl_certificate     /etc/ssl/www.example.com.crt;
    ssl_certificate_key /etc/ssl/www.example.com.key;

    # Moved pages: permanent and straight to the final URL
    location = /old-chairs/ {
        return 301 https://www.example.com/chairs/;
    }
    location ^~ /shop/chairs/ {
        rewrite ^/shop/chairs/(.*)$ https://www.example.com/chairs/$1 permanent;
    }

    root /var/www/example;
}
```
