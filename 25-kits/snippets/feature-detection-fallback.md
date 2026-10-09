# Feature detection with a fallback for unsupported or permission-based APIs

Google's renderer does not grant permission prompts (location, payments, camera) and does not run WebGL well. Render the indexable content first and treat such features as optional enhancements behind feature detection.

```html
<main>
  <h1>Our stores</h1>
  <ul id="stores">
    <li>Barcelona, Carrer Example 1</li>
    <li>Madrid, Calle Example 2</li>
  </ul>
  <button type="button" id="near-me" hidden>Sort by distance</button>
  <canvas class="hero-effect" width="1200" height="400"></canvas>
</main>

<script>
  // Location: optional, only after a user click; the full list is already in the page
  if ('geolocation' in navigator) {
    const button = document.getElementById('near-me');
    button.hidden = false;
    button.addEventListener('click', () => {
      navigator.geolocation.getCurrentPosition(
        (position) => sortStoresByDistance(position.coords),
        () => {} // declined or unavailable: keep the default order
      );
    });
  }

  function sortStoresByDistance(coords) {
    console.log('Sort stores near', coords.latitude, coords.longitude);
  }

  // WebGL: decoration only; without it the server-rendered text and images stay as they are
  const canvas = document.querySelector('canvas.hero-effect');
  const gl = canvas.getContext('webgl');
  if (gl) {
    gl.clearColor(0.1, 0.3, 0.5, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT);
  } else {
    canvas.remove();
  }
</script>
```
