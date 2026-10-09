# Tabs and accordions whose content is in the DOM from the start

Googlebot does not click, so content fetched only when a tab is clicked never exists for it. Ship every panel in the HTML and only hide the inactive ones with the `hidden` attribute or CSS: hidden content in the DOM can be indexed, absent content cannot.

```html
<div class="tabs">
  <div role="tablist" aria-label="Product details">
    <button type="button" role="tab" id="tab-specs" aria-controls="panel-specs" aria-selected="true">Specifications</button>
    <button type="button" role="tab" id="tab-care" aria-controls="panel-care" aria-selected="false">Care</button>
  </div>
  <section role="tabpanel" id="panel-specs" aria-labelledby="tab-specs">
    <p>Seat height 45 cm, solid oak frame, paper-cord seat.</p>
  </section>
  <section role="tabpanel" id="panel-care" aria-labelledby="tab-care" hidden>
    <p>Wipe with a damp cloth; re-oil the frame once a year.</p>
  </section>
</div>

<!-- Avoid: tab.onclick = () => fetch('/api/specs') ... content that exists only after a click -->

<script>
  const tabs = document.querySelectorAll('[role="tab"]');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((other) => {
        const selected = other === tab;
        other.setAttribute('aria-selected', String(selected));
        document.getElementById(other.getAttribute('aria-controls')).hidden = !selected;
      });
    });
  });
</script>
```
