# Fonts bundled with the PDF builder

Every font here is licensed under the **SIL Open Font License 1.1 (OFL-1.1)**, which allows bundling and embedding in PDFs.
Licence text: https://openfontlicense.org (each fontsource package also ships it as `LICENSE`).

All `.woff2` files are unmodified [fontsource](https://fontsource.org) 5.3.0 files, downloaded from
`https://cdn.jsdelivr.net/npm/@fontsource/<family>@5.3.0/files/<file>`; the source URL of each file is that pattern with its own
family and file name. The five `.ttf` files are used only by reportlab for the running header and footer. Each one is generated
from two of the `.woff2` files above (the `latin` and `latin-ext` subsets of the same family and weight, merged into one TrueType
font, layout tables dropped) by `make_ttf.py` in this folder, so the header and footer cover Latin-1 and Latin Extended-A with
the same glyphs as the body text. Run `python _system/pdf/fonts/make_ttf.py` after replacing one of those `.woff2` files.

| Family (CSS name) | Files | Copyright (from the package `LICENSE`) | Package |
|---|---|---|---|
| Inter (`Inter`) | `inter-latin-{400,500,600,700}-normal.woff2`, `inter-latin-ext-{400,500,600,700}-normal.woff2`, `inter-400-normal.ttf`, `inter-600-normal.ttf` | The Inter Project Authors | https://cdn.jsdelivr.net/npm/@fontsource/inter@5.3.0/ |
| Fraunces (`Fraunces`) | `fraunces-latin-{400,500,600}-normal.woff2`, `fraunces-latin-400-italic.woff2`, `fraunces-latin-ext-{400,500,600}-normal.woff2`, `fraunces-latin-ext-400-italic.woff2`, `fraunces-500-normal.ttf` | The Fraunces Project Authors | https://cdn.jsdelivr.net/npm/@fontsource/fraunces@5.3.0/ |
| Figtree (`Figtree`) | `figtree-latin-{400,500,600,700,800}-normal.woff2`, `figtree-latin-400-italic.woff2`, `figtree-latin-ext-{400,500,600,700,800}-normal.woff2`, `figtree-latin-ext-400-italic.woff2` | The Figtree Project Authors (https://github.com/erikdkennedy/figtree) | https://cdn.jsdelivr.net/npm/@fontsource/figtree/ (see the Figtree section below) |
| JetBrains Mono (`JetBrains Mono`) | `jetbrains-mono-latin-{400,500}-normal.woff2`, `jetbrains-mono-latin-ext-{400,500}-normal.woff2` | The JetBrains Mono Project Authors | https://cdn.jsdelivr.net/npm/@fontsource/jetbrains-mono@5.3.0/ |
| Josefin Sans (`Josefin`) | `josefin-sans-latin-{400,600,700}-normal.woff2`, `josefin-sans-latin-ext-{400,600,700}-normal.woff2`, `josefin-sans-600-normal.ttf` | The Josefin Sans Project Authors | https://cdn.jsdelivr.net/npm/@fontsource/josefin-sans@5.3.0/ |
| Jost (`Jost`) | `jost-latin-{400,500,600,700}-normal.woff2`, `jost-latin-ext-{400,500,600,700}-normal.woff2` | The Jost Project Authors | https://cdn.jsdelivr.net/npm/@fontsource/jost@5.3.0/ |
| Poiret One (`Poiret One`) | `poiret-one-latin-400-normal.woff2`, `poiret-one-latin-ext-400-normal.woff2` | The Poiret One Project Authors | https://cdn.jsdelivr.net/npm/@fontsource/poiret-one@5.3.0/ |
| Limelight (`Limelight`) | `limelight-latin-400-normal.woff2`, `limelight-latin-ext-400-normal.woff2`, `limelight-400-normal.ttf` | Sorkin Type Co | https://cdn.jsdelivr.net/npm/@fontsource/limelight@5.3.0/ |
| Italiana (`Italiana`) | `italiana-latin-400-normal.woff2` (fontsource has no latin-ext subset; accented letters fall back to Poiret One) | Santiago Orozco | https://cdn.jsdelivr.net/npm/@fontsource/italiana@5.3.0/ |
| Noto Sans Math (part of `Noto Symbols`) | `noto-sans-math-latin-400-normal.woff2` (despite the name, fontsource ships the whole font in this file) | Google LLC | https://cdn.jsdelivr.net/npm/@fontsource/noto-sans-math@5.3.0/ |
| Noto Sans Symbols 2 (part of `Noto Symbols`) | `noto-sans-symbols-2-symbols-400-normal.woff2` | The Noto Project Authors | https://cdn.jsdelivr.net/npm/@fontsource/noto-sans-symbols-2@5.3.0/ |

## How the fallbacks work

- **latin-ext** files are declared as extra `@font-face` rules of the same family with a `unicode-range`, so accented names
  (Ł, Š, ő, ğ, …) stay in the same typeface. Chromium loads them only when such a character is on the page.
- **`Noto Symbols`** is one CSS family made of two files: Noto Sans Math for arrows and math signs (U+2190–22FF, U+27C0–27FF,
  U+2900–2AFF: → ← ↑ ↓ ⇒ ≤ ≥ ≈ ≠) and Noto Sans Symbols 2 for check marks, crosses and other dingbats (U+2300–24FF,
  U+25A0–27BF, U+2B00–2BFF: ✓ ✔ ✕ ✗ ★). It is the last entry of every font stack in `ocean.css`, `deco.css` and `style.css`, of every SVG
  `font-family` attribute in the templates, of the Inter/Fraunces → Figtree swap in `build_ocean.py` and of the
  Inter/Fraunces → Jost/Poiret One swap in `build_deco.py`.
  (Noto Sans Symbols 2 alone has no basic arrows or math signs. DejaVu Sans would cover everything in one file but is not
  bundled on purpose: it is the usual Linux system fallback, and bundling it would hide that fallback from the font check.)

## Header and footer check

Before drawing, the builders check every character of the running header and footer (author name from `config.yaml`, `footer`
from `days.yaml`, page numbers) against the `.ttf` that draws it, and stop with the character's code and name when it is missing.
reportlab would otherwise leave the character out without a warning. The `.ttf` files cover Latin-1 and Latin Extended-A
(Polish, Czech, Hungarian, Turkish and other European names); for anything else, add the fontsource subset that has the
characters to `make_ttf.py` and rebuild the `.ttf` files.

## Font check

After each build, `common.check_fonts` lists the fonts embedded in the PDF and fails when a name does not start with one of
the families above (for example ArialMT, TimesNewRomanPSMT, SegoeUISymbol, DejaVuSans, LiberationSans, MicrosoftYaHei).
That means the text contains a character that none of these fonts has. Rewrite the character, or add a fontsource subset that
covers it, declare it in both stylesheets, and add a row here. Names ending in `(Type3)` are Chromium's synthetic bold of a
bundled family and are allowed.

## Figtree (Deep Dive edition)

Figtree is the typeface of the Deep Dive edition (PDF, web edition, brand images); JetBrains Mono stays the code face.
The files are unmodified fontsource files of the `@fontsource/figtree` package, named like the other families
(the package version was not recorded when they were downloaded). Full licence text, as shipped with the package:

```text
Copyright 2022 The Figtree Project Authors (https://github.com/erikdkennedy/figtree) Figtree-Italic[wght].ttf: Copyright 2022 The Figtree Project Authors (https://github.com/erikdkennedy/figtree)

This Font Software is licensed under the SIL Open Font License, Version 1.1.
This license is copied below, and is also available with a FAQ at:
http://scripts.sil.org/OFL


-----------------------------------------------------------
SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007
-----------------------------------------------------------

PREAMBLE
The goals of the Open Font License (OFL) are to stimulate worldwide
development of collaborative font projects, to support the font creation
efforts of academic and linguistic communities, and to provide a free and
open framework in which fonts may be shared and improved in partnership
with others.

The OFL allows the licensed fonts to be used, studied, modified and
redistributed freely as long as they are not sold by themselves. The
fonts, including any derivative works, can be bundled, embedded,
redistributed and/or sold with any software provided that any reserved
names are not used by derivative works. The fonts and derivatives,
however, cannot be released under any other type of license. The
requirement for fonts to remain under this license does not apply
to any document created using the fonts or their derivatives.

DEFINITIONS
"Font Software" refers to the set of files released by the Copyright
Holder(s) under this license and clearly marked as such. This may
include source files, build scripts and documentation.

"Reserved Font Name" refers to any names specified as such after the
copyright statement(s).

"Original Version" refers to the collection of Font Software components as
distributed by the Copyright Holder(s).

"Modified Version" refers to any derivative made by adding to, deleting,
or substituting -- in part or in whole -- any of the components of the
Original Version, by changing formats or by porting the Font Software to a
new environment.

"Author" refers to any designer, engineer, programmer, technical
writer or other person who contributed to the Font Software.

PERMISSION & CONDITIONS
Permission is hereby granted, free of charge, to any person obtaining
a copy of the Font Software, to use, study, copy, merge, embed, modify,
redistribute, and sell modified and unmodified copies of the Font
Software, subject to the following conditions:

1) Neither the Font Software nor any of its individual components,
in Original or Modified Versions, may be sold by itself.

2) Original or Modified Versions of the Font Software may be bundled,
redistributed and/or sold with any software, provided that each copy
contains the above copyright notice and this license. These can be
included either as stand-alone text files, human-readable headers or
in the appropriate machine-readable metadata fields within text or
binary files as long as those fields can be easily viewed by the user.

3) No Modified Version of the Font Software may use the Reserved Font
Name(s) unless explicit written permission is granted by the corresponding
Copyright Holder. This restriction only applies to the primary font name as
presented to the users.

4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font
Software shall not be used to promote, endorse or advertise any
Modified Version, except to acknowledge the contribution(s) of the
Copyright Holder(s) and the Author(s) or with their explicit written
permission.

5) The Font Software, modified or unmodified, in part or in whole,
must be distributed entirely under this license, and must not be
distributed under any other license. The requirement for fonts to
remain under this license does not apply to any document created
using the Font Software.

TERMINATION
This license becomes null and void if any of the above conditions are
not met.

DISCLAIMER
THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE
COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL
DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM
OTHER DEALINGS IN THE FONT SOFTWARE.
```
