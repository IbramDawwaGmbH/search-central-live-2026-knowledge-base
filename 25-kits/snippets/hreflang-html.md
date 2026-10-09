# hreflang link elements: complete, reciprocal, self-referencing

Every language version of a page carries the identical block in its `<head>`, including a line for itself and an `x-default` for the fallback, ideally a language selector page. URLs are fully qualified; codes are an ISO 639-1 language, an optional ISO 15924 script (zh-Hant, zh-Hans-CN) and an optional ISO 3166-1 Alpha-2 region.

```html
<!-- The same block in the <head> of every language version listed here; the x-default target is a language selector page -->
<link rel="alternate" hreflang="en" href="https://www.example.com/en/chairs/">
<link rel="alternate" hreflang="en-GB" href="https://www.example.com/en-gb/chairs/">
<link rel="alternate" hreflang="de-DE" href="https://www.example.com/de-de/stuehle/">
<link rel="alternate" hreflang="de-AT" href="https://www.example.com/de-at/stuehle/">
<link rel="alternate" hreflang="de-CH" href="https://www.example.com/de-ch/stuehle/">
<link rel="alternate" hreflang="sv-SE" href="https://www.example.com/sv-se/stolar/">
<link rel="alternate" hreflang="zh-Hant" href="https://www.example.com/zh-hant/chairs/">
<link rel="alternate" hreflang="x-default" href="https://www.example.com/chairs/choose-language/">

<!-- Wrong values seen in the wild: "se", "dk", "cz" (country codes, not languages: use sv, da, cs),
     "en-UK" (use en-GB), "de-SW" (use de-CH), "en-EU" (no such region), "GB" (a region alone).
     A script subtag is valid: "zh-Hant", "zh-Hans-CN" (language, script, region in that order) -->
```
