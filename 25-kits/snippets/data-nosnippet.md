# data-nosnippet for one detail instead of the whole snippet

`data-nosnippet` keeps a specific passage out of search snippets (and so out of the snippet-based inputs of AI features) while the page can still rank for it. It works only on `span`, `div` and `section`, must be in the server HTML (not toggled by JavaScript) and needs valid, closed markup: an unclosed element can hide the rest of the page.

```html
<p>
  Call our workshop on <span data-nosnippet>+1 555-0100</span> for a repair quote.
</p>

<section data-nosnippet>
  <h2>Member prices</h2>
  <p>Log in to see your personal discount.</p>
</section>
```
