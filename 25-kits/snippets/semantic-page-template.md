# Page template with a clearly delimited main content area

Everything indexing depends on (title, description, canonical, robots rules, main text, links) is in the server HTML. Header, navigation and footer are separated from one `<main>` element that holds the title, headings, opening text and media, because Google weighs words by where they appear and treats the main content as the most important part.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Oak dining chair with woven seat | Example Shop</title>
  <meta name="description" content="Solid oak dining chair with a hand-woven paper-cord seat. Seat height 45 cm, delivered assembled.">
  <link rel="canonical" href="https://www.example.com/chairs/oak-dining-chair">
  <meta name="robots" content="max-snippet:-1, max-image-preview:large">
</head>
<body>
  <header>
    <a href="/">Example Shop</a>
    <nav aria-label="Main">
      <a href="/chairs/">Chairs</a>
      <a href="/tables/">Tables</a>
    </nav>
  </header>

  <main>
    <article>
      <h1>Oak dining chair with woven seat</h1>
      <p>A solid oak dining chair with a hand-woven paper-cord seat, made for everyday family meals.</p>
      <figure>
        <img src="/img/oak-chair-1200.webp" alt="Oak dining chair with a woven paper-cord seat, seen from the front" width="1200" height="900">
        <figcaption>Natural oak finish, seat height 45 cm.</figcaption>
      </figure>
      <h2>Dimensions and materials</h2>
      <p>Width 46 cm, depth 52 cm, height 80 cm. <strong>Solid European oak</strong>, paper-cord seat.</p>
    </article>
  </main>

  <footer>
    <nav aria-label="Footer">
      <a href="/delivery/">Delivery</a>
      <a href="/returns/">Returns</a>
      <a href="/contact/">Contact</a>
    </nav>
  </footer>
</body>
</html>
```
