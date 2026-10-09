# Fonts of the web edition

Every font here is licensed under the **SIL Open Font License 1.1 (OFL-1.1)**: https://openfontlicense.org

The `.woff2` files are unmodified [fontsource](https://fontsource.org) 5.3.0 files, the same files as in `_system/pdf/fonts/`
(see `_system/pdf/fonts/LICENSES.md` for each source URL). `latin` covers Latin-1; `latin-ext` (Ł, Š, ń, ő ...) is declared in
`site.css` with a `unicode-range`, so a browser loads it only when such a letter is on the page.

| Family | Files | Copyright |
| --- | --- | --- |
| Jost | `jost-latin-{400,500,600}-normal.woff2`, `jost-latin-ext-{400,500,600}-normal.woff2` | The Jost Project Authors |
| Josefin Sans | `josefin-sans-latin-{400,600,700}-normal.woff2`, `josefin-sans-latin-ext-{400,600,700}-normal.woff2` | The Josefin Sans Project Authors |
| Poiret One | `poiret-one-latin-400-normal.woff2`, `poiret-one-latin-ext-400-normal.woff2` | The Poiret One Project Authors |
| Limelight | `limelight-latin-400-normal.woff2`, `limelight-latin-ext-400-normal.woff2` | Sorkin Type Co |
| Figtree | `figtree-latin-{400,500,600,700,800}-normal.woff2`, `figtree-latin-400-italic.woff2`, `figtree-latin-ext-{400,500,600,700,800}-normal.woff2`, `figtree-latin-ext-400-italic.woff2` | The Figtree Project Authors |
| JetBrains Mono | `jetbrains-mono-latin-{400,500}-normal.woff2`, `jetbrains-mono-latin-ext-{400,500}-normal.woff2` | The JetBrains Mono Project Authors |

## Figtree (Deep Dive edition)

Figtree is the typeface of the Deep Dive edition (PDF, web edition, brand images); JetBrains Mono stays the code face.
The files are unmodified fontsource files of the `@fontsource/figtree` package, named like the other families
(the package version was not recorded when they were downloaded). Same files as in `_system/pdf/fonts/`. Full licence text, as shipped with the package:

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
