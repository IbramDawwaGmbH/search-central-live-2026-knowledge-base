# Indexable, responsive image with a modern-format fallback

Google extracts images from `<img src>`; a `<picture>` element counts only through the `<img>` inside it, and CSS background images are not extracted. Serve AVIF or WebP through `<source>` elements, keep a widely supported file in the `img src`, describe the image in `alt` and put a caption or explanatory text next to it.

```html
<figure>
  <picture>
    <source type="image/avif"
            srcset="/img/oak-chair-800.avif 800w, /img/oak-chair-1600.avif 1600w"
            sizes="(max-width: 800px) 100vw, 800px">
    <source type="image/webp"
            srcset="/img/oak-chair-800.webp 800w, /img/oak-chair-1600.webp 1600w"
            sizes="(max-width: 800px) 100vw, 800px">
    <img src="/img/oak-chair-800.jpg"
         srcset="/img/oak-chair-800.jpg 800w, /img/oak-chair-1600.jpg 1600w"
         sizes="(max-width: 800px) 100vw, 800px"
         alt="Oak dining chair with a woven paper-cord seat, seen from the front"
         width="800" height="600" loading="lazy">
  </picture>
  <figcaption>The oak dining chair in a natural oak finish, seat height 45 cm.</figcaption>
</figure>

<!-- Not indexable as an image: keep CSS backgrounds for decoration only -->
<div class="hero" style="background-image: url('/img/oak-chair-hero.jpg')"></div>
```
