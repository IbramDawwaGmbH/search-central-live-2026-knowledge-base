[Knowledge base](../../README.md) / [60-outputs](../README.md) / **pdf**

# Field guides

**The printable field guide of each event day. Deep Dive is the main edition and the one kept current. The classic Art Deco and modern editions are frozen at their v2.4.0 content, and [the classic editions log](classic-editions-log.md) lists what they lack.**

<picture><source media="(prefers-color-scheme: dark)" srcset="../../_system/brand/illustrations/60-outputs-pdf-dark.svg"><img src="../../_system/brand/illustrations/60-outputs-pdf-light.svg" width="100%" alt="Open field guides glide through the water like a flock of rays while the Diver bot sits on a rock reading one: the printable field guides."></picture>

<p align="center"><img src="../../_system/brand/divider.svg" width="600" alt="Section divider"></p>

<p align="center">
  <a href="day1-field-guide-deep-dive.pdf"><img src="../../_system/brand/covers/day1-deep-dive.png" width="220" alt="Cover of the Day 1 field guide, Deep Dive edition: How Google Crawls in the Age of AI Search, in white and yellow on deep-blue water under a wavy surface, with reef fish, seaweed and coral, and the Diver bot swimming above the seabed."></a>
  &nbsp;
  <a href="day2-field-guide-deep-dive.pdf"><img src="../../_system/brand/covers/day2-deep-dive.png" width="220" alt="Cover of the Day 2 field guide, Deep Dive edition: How Google Indexes in the Age of AI Search, in white and yellow on deep-blue water under a wavy surface, with a school of fish, seaweed and coral, and the Diver bot sitting on the seabed reading its field guide."></a>
  &nbsp;
  <a href="day3-field-guide-deep-dive.pdf"><img src="../../_system/brand/covers/day3-deep-dive.png" width="220" alt="Cover of the Day 3 field guide, Deep Dive edition: How Google Serves in the Age of AI Search, in white and yellow on deep-blue water under a wavy surface, with reef fish, seaweed and coral, and the Diver bot standing on the seabed, pointing at the reef."></a>
  <br>
  <sub>The Deep Dive covers of the three days. Click one to open the guide.</sub>
</p>

## <img src="../../_system/brand/icons/map.svg" width="24" height="24" alt=""> What's here

| Day | Deep Dive<br><sub>current (v2.7.0)</sub> | Art Deco<br><sub>classic edition, content as of v2.4.0</sub> | Modern<br><sub>classic edition, content as of v2.4.0</sub> |
| --- | --- | --- | --- |
| **Day 1 · Crawling**<br><sub>Wed 30 September 2026</sub> | [**`day1-field-guide-deep-dive.pdf`**](day1-field-guide-deep-dive.pdf)<br><sub>34 pages, with the robots.txt talk, the community talks and the Q&A</sub> | [`day1-field-guide-art-deco.pdf`](day1-field-guide-art-deco.pdf)<br><sub>21 pages</sub> | [`day1-field-guide-modern.pdf`](day1-field-guide-modern.pdf)<br><sub>21 pages</sub> |
| **Day 2 · Indexing**<br><sub>Thu 1 October 2026</sub> | [**`day2-field-guide-deep-dive.pdf`**](day2-field-guide-deep-dive.pdf)<br><sub>35 pages</sub> | [`day2-field-guide-art-deco.pdf`](day2-field-guide-art-deco.pdf)<br><sub>32 pages</sub> | [`day2-field-guide-modern.pdf`](day2-field-guide-modern.pdf)<br><sub>32 pages</sub> |
| **Day 3 · Serving**<br><sub>Fri 2 October 2026</sub> | [**`day3-field-guide-deep-dive.pdf`**](day3-field-guide-deep-dive.pdf)<br><sub>33 pages</sub> | [`day3-field-guide-art-deco.pdf`](day3-field-guide-art-deco.pdf)<br><sub>33 pages</sub> | [`day3-field-guide-modern.pdf`](day3-field-guide-modern.pdf)<br><sub>33 pages</sub> |

> [!IMPORTANT]
> **Only the Deep Dive edition is kept current.** v2.5.0 added a second attendee's recording of Day 1 and Day 2: 497 new claims, corrected claims and proven speaker names. The Day 1 and Day 2 Deep Dive guides carry them. v2.7.0 added six audio recordings of Day 1 sessions (the keynote, Lightning A, the crawling talks, the robots.txt talk with the start of Lightning B, and the Q&A): 53 new claims, corrections and quotes checked against the audio, in the Day 1 Deep Dive guide only. The Art Deco and modern guides stay byte-identical to v2.4.0, and **[`classic-editions-log.md`](classic-editions-log.md)** lists, day by day, every section, paragraph and correction they lack. Day 3's classic guides lack only two small corrections made after v2.6.0 (the 200-second minimum and a hedged word).

GitHub shows a preview of each PDF; use its download button for the file itself. The [web edition](../site/index.html) carries its own copies in `60-outputs/site/downloads/`, refreshed by every rebuild.

This page and the classic editions log are hand-written (the PDFs are generated): add a day's row when its guide is built, and log a Deep Dive change in the classic editions log.

## <img src="../../_system/brand/icons/book.svg" width="24" height="24" alt=""> Inside a guide

A cover and contents page, the day's key takeaways, the day at a glance (its agenda, generated from the session data), the content sections, a help and contact page, and the sources, generated from the sources the day's claims cite. Statements carry their source label (Slide, Stage, Docs, Press or Analysis), and the template can tie each one to the claims it rests on; the build stops if a guide cites a claim that does not exist or is private.

| Edition | The look |
| --- | --- |
| **Deep Dive**<br><sub>the main edition</sub> | Every page is a white card over sunlit water, between a wavy surface and a seabed with reef fish, seaweed and coral. Sections open with a glossy numbered bubble; the Diver bot, our own robot snorkel diver, is on the cover and the contact page, and quiet reef vignettes (some with the bot) fill large empty spaces at the ends of pages. Set in Figtree. |
| **Art Deco**<br><sub>classic edition, content as of v2.4.0</sub> | Gold and onyx: stepped frames, sunburst rays and ornamental rules, set in Poiret One, Josefin Sans and Jost. |
| **Modern**<br><sub>classic edition, content as of v2.4.0</sub> | A plain, light layout for quick printing. |

## <img src="../../_system/brand/icons/anchor.svg" width="24" height="24" alt=""> How they are made

Generated by [`_system/pdf/make_pdf.py`](../../_system/pdf/make_pdf.py) from the day's hand-written `_system/pdf/dayN.template.html`, `_system/pdf/days.yaml` and the agent pack. `rebuild.bat` runs it for every day that has a template, for the Deep Dive edition only (`ocean`). It never rewrites the classic editions. To refresh one on purpose, build it by hand with `make_pdf.py dayN deco` or `make_pdf.py dayN modern`, then update the classic editions log. **Do not edit the PDFs:** change the template or the claims and run `rebuild.bat` (or `rebuild.bat dayN` for one day). Two builds of the same input give byte-identical PDFs. The full guide to the PDF system is [`_system/pdf/README.md`](../../_system/pdf/README.md).

> [!NOTE]
> No slide photo is ever embedded: code examples and diagrams are redrawn from the slides as teaching material. The contact page prints the author's WhatsApp number and LinkedIn link on purpose (set in `_system/pdf/config.yaml`). See [`PRIVACY.md`](../../PRIVACY.md).

<p align="center"><img src="../../_system/brand/divider.svg" width="600" alt="Section divider"></p>

<p align="center"><sub>← <a href="../README.md">60-outputs</a> · <a href="../dev/README.md">Developer kit</a> →</sub></p>
