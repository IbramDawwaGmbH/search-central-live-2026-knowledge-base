# Automated check that Back leaves the page

A Playwright test opens each template from another page, interacts with it the way users do (many history hijacks wait for a key press, a scroll or a timer), presses Back once and expects to be on the previous page again. Run it in CI for every template and after adding any ad, engagement or recommendation script.

```js
// back-button.spec.js: npm i -D @playwright/test, then npx playwright test
const { test, expect } = require('@playwright/test');

const START = 'https://www.example.com/'; // stands in for the page the user came from, such as a search results page
const PAGES = [
  'https://www.example.com/blog/oak-table-care/',
  'https://www.example.com/chairs/oak-dining-chair',
];

for (const url of PAGES) {
  test(`one Back press leaves ${url}`, async ({ page }) => {
    await page.goto(START);
    await page.goto(url);
    await page.keyboard.press('End'); // a real user input that also scrolls to the bottom
    await page.waitForTimeout(5000);  // give delayed scripts time to run
    await page.goBack();
    await expect(page).toHaveURL(START);
  });
}
```

Then search the built bundles for history calls outside the router and review each one.

```bash
grep -rnE "history\.(pushState|replaceState)|addEventListener\(.popstate" dist/
```
