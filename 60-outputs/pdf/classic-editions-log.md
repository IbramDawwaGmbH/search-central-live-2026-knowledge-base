[Knowledge base](../../README.md) / [60-outputs](../README.md) / [pdf](README.md) / **Classic editions log**

# Classic editions log

**The Art Deco and modern field guides are frozen at their v2.4.0 content. Only the Deep Dive edition is kept current. This log lists, day by day, what the Deep Dive edition and the knowledge base now have that the classic editions do not.**

<p align="center"><img src="../../_system/brand/divider.svg" width="600" alt="Section divider"></p>

## <img src="../../_system/brand/icons/anchor.svg" width="24" height="24" alt=""> The rule

From v2.5.0 on, `rebuild.bat` rebuilds only the Deep Dive edition. Deep Dive is the main edition. The Art Deco and modern PDFs stay exactly as they were released in v2.4.0: the files in this folder and their copies in the web edition are byte-identical to that release. Everything that is not a styled PDF is updated as usual: the claims, topics, session pages, kits, maps, agent pack and web edition.

| Edition | Files | Content as of | Day 1 | Day 2 | Day 3 |
| --- | --- | --- | ---: | ---: | ---: |
| **Deep Dive**<br><sub>the main edition, kept current</sub> | [`day1`](day1-field-guide-deep-dive.pdf) · [`day2`](day2-field-guide-deep-dive.pdf) · [`day3`](day3-field-guide-deep-dive.pdf) `-field-guide-deep-dive.pdf` | v2.7.0 | 34 pages | 35 pages | 33 pages |
| **Art Deco**<br><sub>classic edition</sub> | [`day1`](day1-field-guide-art-deco.pdf) · [`day2`](day2-field-guide-art-deco.pdf) · [`day3`](day3-field-guide-art-deco.pdf) `-field-guide-art-deco.pdf` | v2.4.0 | 21 pages | 32 pages | 33 pages |
| **Modern**<br><sub>classic edition</sub> | [`day1`](day1-field-guide-modern.pdf) · [`day2`](day2-field-guide-modern.pdf) · [`day3`](day3-field-guide-modern.pdf) `-field-guide-modern.pdf` | v2.4.0 | 21 pages | 32 pages | 33 pages |

> [!NOTE]
> **What changed after v2.4.0.** A second attendee recorded most of Day 1 and Day 2 and shared the recording with the author. v2.5.0 cross-matched it with the knowledge base. The result: 496 new claims, corrections to existing claims and session records, and proven speaker names. The Day 1 and Day 2 Deep Dive guides carry these changes, and the classic editions do not. The recording itself stays private, like every other recording. After v2.6.0 a review of the open items corrected or hedged a few Day 2 and Day 3 claims (an uncertain word, a disputed figure, a quote that the two recordings word differently), so the Day 3 Deep Dive guide now differs from its classic editions in two places as well. v2.7.0 adds six audio recordings of Day 1 sessions, also shared with the author and transcribed on the author's computer: 53 new Day 1 claims, corrections and quotes checked against the audio, and a Day 1 Deep Dive guide of 34 pages. The audio files stay private as well.

Claim IDs below are the public IDs in [`claims.jsonl`](../agent-pack/claims.jsonl). Every claim has its own card on the [claims page](../site/claims.html) of the web edition. IDs are never renumbered, so an ID cited by a classic edition still points to the same claim, in its corrected wording.

<p align="center"><img src="../../_system/brand/divider.svg" width="600" alt="Section divider"></p>

## <img src="../../_system/brand/icons/fish.svg" width="24" height="24" alt=""> Day 1 · Crawling

The classic Day 1 guide was written from slide photos and the author's notes alone. Six sessions had no coverage: Lightning sessions A, B and C, "What would you do?", the Q&A and the wrap-up. The second recording (v2.5.0) covers most of the day, and six audio recordings (v2.7.0) cover the opening keynote, Lightning A, the two crawling talks, the robots.txt talk with the first talk of Lightning B, and most of the Q&A. Where the audio and the second recording disagree, the audio wins. Five of those six sessions now have coverage (Lightning B one talk only; "What would you do?" still none), and the robots.txt talk now has a transcript. The Deep Dive guide grew from 21 to 34 pages (31 in v2.5.0), with two new sections (the community lightning talks and the Q&A), a rewritten robots.txt section, 12 key takeaways instead of 10, and 19 audit checks instead of 12. It cites 336 more claims and lists 91 sources instead of 33.

### New claims by session

405 new Day 1 claims; the classic edition has none of them. (v2.5.0 added 353; one point the event host made, the three-day plan, was later removed at the owner's request. v2.7.0 added 53 from the audio recordings, D1-C495 to D1-C547; one of them, D1-C495, is private.) The table also shows the session records whose speaker, role or coverage changed. A speaker is named only with proof: a self-introduction, an on-stage hand-over or back-reference, matched to the official speaker list.

| Session | New claims | Speaker and coverage in the classic edition | Now |
| --- | ---: | --- | --- |
| `D1-S01` Welcome and opening keynotes | 44 | Google Search leadership; coverage: slides | Lino Cattaruzzi; role President, Google Iberia; coverage: slides, transcript |
| `D1-S02` What's new in the world of Search | 19 | Google; coverage: slides | Gary Illyes; role Search Relations; coverage: transcript, slides |
| `D1-S03` How Search works and where's AI? | 26 | Google, Gary Illyes; coverage: slides | Cherry Prommawin, Gary Illyes; role Search Relations; coverage: transcript, slides |
| `D1-S04` Lightning session A: Automation and AI | 98 | Community speakers; coverage: none | James Powley, Rafael Kovashikawa, Kira Breuer, Carlos Ortega, Thiago Pojda, other community speakers; coverage: transcript |
| `D1-S05` How crawling works | 28 | Google; coverage: slides | Cherry Prommawin, Gary Illyes; role Search Relations; coverage: slides, transcript |
| `D1-S06` How crawling errors affect Search | 30 | Google; coverage: notes | Cherry Prommawin, Gary Illyes; role Search Relations; coverage: notes, transcript |
| `D1-S07` How Google interprets robots.txt | 23 | Google; coverage: slides | Google; coverage: slides, transcript |
| `D1-S08` Lightning session B: Robots.txt | 5 | Community speakers; coverage: none | Dave Smart, other community speakers; coverage: transcript |
| `D1-S10` How Google thinks about crawl budget | 26 | role Search Advocate; coverage: slides | role Search Relations; coverage: slides, transcript |
| `D1-S11` Lightning session C: Crawling | 23 | Community speakers; coverage: none | Tobias Schwarz, Jovana Avramovic; coverage: transcript |
| `D1-S12` Q&A | 83 | Google panel; coverage: none | John Mueller, Gary Illyes; role Search Relations; coverage: transcript |
| `D1-S13` Daily wrap-up | — | coverage: none | coverage: transcript |
| **Total** | **405** | | |

### Corrected claims

The classic edition was built from the wording on the left. Where it quotes or paraphrases one of these claims, the Deep Dive edition follows the right-hand column.

| Claim | The classic edition and v2.4.0 said | Now | Why |
| --- | --- | --- | --- |
| `D1-C001` | The keynote opened with a slide quoting Elizabeth Reid (VP, Search) saying Search is never a solved problem because the internet and the world keep changing. | The keynote showed a slide quoting Elizabeth Reid (VP, Search) saying Search is never a solved problem because the internet and the world keep changing. | The slide was shown during the keynote, not at its opening. |
| `D1-C059` | Google Search leadership told the audience to focus on the user ('UEO'). | The opening keynote closed with the advice to think about UEO, user engine optimisation, next to SEO and GEO: focus on the user and the rest will follow. | The recording gives the expansion of UEO and ties it to the close of the opening keynote. |
| `D1-C046` | An audience question asked whether Google can distinguish between AI-written and human-written content. | A Google slide headed 'Your Question' raised whether Google can distinguish between AI-written and human-written content, presented on stage as the question this topic usually prompts rather than one asked live. | No one in the room asked it: it was Google's own "Your Question" slide. |
| `D1-C070` | Soft 404s were named as a crawl problem alongside DNS and firewall issues. | Soft 404s were named as a crawl problem alongside DNS and firewall issues, and described as one of the biggest problems on the internet right now for crawling and showing up in Search. | The speaker ranked soft 404s among the biggest current problems. |
| `D1-C017` | The average AI Mode query is about 3 times the length of a traditional search (another slide said 2–3 times). | The average AI Mode query is about 3 times the length of a traditional search (the opening keynote's slide and its speaker said two to three times). | v2.7.0: the audio has the two-to-three-times figure said aloud in the keynote while that slide was on screen. |
| `D1-C114` | Adopting 'load more' style pagination is risky because it is complex and mistakes are costly. Check the server logs and implement it carefully. | A Google panelist called pagination one of the trickiest things in web development and said switching to infinite scroll or a load-more button is risky, depending on what you want to achieve, because Googlebot does not click buttons. Quote (checked against the audio): "the infinite scrolling or load more thing is kind of dangerous, depending on what you want to achieve". | v2.7.0: the audio places the point in the Q&A. "Check the server logs" is not in that passage, so it was dropped. |
| `D1-C107` | The nofollow rule can consume crawl budget. | The nofollow rule can still consume crawl budget: Google does not crawl through the nofollow link itself, but it still crawls the linked page when it finds that page through other links. | The recording gives the reason why nofollow can still cost crawl budget. |

**Claims moved to another session** (any text change is in the table above):

- `D1-C009`, `D1-C010`, `D1-C011`, `D1-C012`, `D1-C013`, `D1-C014`, `D1-C015`: D1-S02 → D1-S01.
- `D1-C059`: D1-S00 → D1-S01.
- `D1-C035`, `D1-C049`: D1-S03 → D1-S02.
- `D1-C120`: D1-S00 → D1-S12.
- `D1-C114`: D1-S00 → D1-S12 (proposed in v2.5.0, applied in v2.7.0 from the audio of the Q&A).

**Speaker field (`who`) on existing claims:**

- "Google" became Gary Illyes: 1 claim (D1-C035).
- "audience" dropped, because it was a Google slide, not a question from the room: 1 claim (D1-C046).
- speaker set to Gary Illyes: 5 claims (D1-C069, D1-C070, D1-C063, D1-C064, D1-C065).
- "Google" dropped, because the session now has a proven speaker: 18 claims (D1-C036, D1-C037, D1-C038, D1-C039, D1-C040, D1-C041, D1-C042, D1-C043, D1-C044, D1-C045, D1-C047, D1-C050, D1-C051, D1-C054, D1-C055, D1-C056, D1-C057, D1-C058).
- speaker set to Lino Cattaruzzi: 1 claim (D1-C059).
- speaker set to "unknown" (no proof of who said it) after the session move: 1 claim (D1-C114).

**Session kept (v2.7.0):** `D1-C087`, `D1-C088`, `D1-C123` stay in D1-S07. The slide with the unknown line between two user-agent lines (IMG_4665) has a time stamp a few minutes into Lightning session B, but the audio of Google's robots.txt talk reads out the same example and the same value ("all-access=yes"), which outweighs the camera time. D1-C087 and D1-C123 gain that passage of the talk as evidence; the kits and the guide still call it a Google slide.

**Made public in v2.7.0:** `D1-C089`. The robots.txt talk pointed to the robots.txt file of thebestfriedchickenever.com to show why comments are useful. The claim was private while the address was unconfirmed. The text does not say who owns the site.

**Corrections to claims first added in v2.5.0** (v2.7.0, from the audio). The classic edition has none of these claims; where the Deep Dive guide printed the old wording, the v2.7.0 list below says so.

- Opening keynote: D1-C173 ("herbicide", not "treatment").
- Lightning session A: D1-C271 (the llms.txt study heard as Ahrefs', almost 40,000 sites, 97% with no hits), D1-C272 ("cloaking" is an uncertain word), D1-C277 (H3 to H5, not H2), D1-C282 (WebMCP testable through browser flags), D1-C288 (Google's AMP project named), D1-C294 (study heard as Peec AI's; the unclear "80-87%" dropped), D1-C308, D1-C311 (content generation is something none of the talks featured). Quotes worded as in the audio: D1-C235, D1-C240, D1-C243, D1-C244.
- Crawling talks: D1-C362 ("AI features" dropped), D1-C364 (429 or 503 responses injected on the network path), D1-C365 (403 responses, "authentication required"); the D1-C335 quote shortened to the words both recordings share.
- Q&A: D1-C427 (hedge removed), D1-C432 (scope of the crawler exemption; its reason is a best reading), D1-C436, D1-C438 (sports sites), D1-C439 ("useful to users", not "popular"), D1-C444, D1-C445 (redirects cost crawl budget at first, then leave a clean slate), D1-C446 (calendar parameters), D1-C449 (a panelist expected AI reporting, without a timeline or a promise), D1-C452 (data would have to be grouped), D1-C453 (PageSpeed Insights and Lighthouse), D1-C458, D1-C464 (vibe-coded tools), D1-C465, D1-C474 and D1-C475 (a sitemap has no sweet spot), D1-C479 (both old URLs got one target path), D1-C490, D1-C492 (John Mueller named), D1-C493 ("an abrupt step down", not "very sharp"). Quotes worded as in the audio: D1-C423, D1-C456, D1-C458, D1-C489, D1-C491.
- Speaker field: "unknown" became Kira Breuer on 11 claims (D1-C253 to D1-C263), Carlos Ortega on 15 claims (D1-C270 to D1-C284) and Thiago Pojda on 12 claims (D1-C285 to D1-C296), each proven on stage and matched to the official speaker list. For Kira Breuer the hand-over was heard as "Kiran"; her self-description (an SEO manager at a local agency in Cologne) matches her entry on the list, the same first-name rule as for the other lightning speakers.
- 20 quotes are now marked as checked against the audio.

### What the Deep Dive edition adds, section by section

The first list covers v2.5.0 (the second recording), the second v2.7.0 (the audio recordings). Read them in that order: v2.7.0 changes some v2.5.0 lines again.

<details>
<summary><b>Open the v2.5.0 list for Day 1</b>: every new or changed section, paragraph, table and checklist item, with the claims it cites</summary>

#### Whole guide
- New template `<style>` block (as Day 2/3): no-wrap `.nw`/`.no`, `text-wrap: pretty`, tighter contents rows, `li` kept on one page.
- Cover (modern cover only): edition date 2 October 2026 -> 3 October 2026.
- `days.yaml` day1: subtitle adds "plus the community talks and the Q&A" (printed on the Deep Dive cover); `sources_checked` 2 October 2026 -> 3 October 2026.
- Contents: 13 -> 15 rows (two new sections; old 09-11 renumbered 11-13), tightened rows; descriptions of rows 01, 02, 05, 06, 08, 13 and Sources rewritten.
- Labels legend: Stage now "Said on stage, from my notes or a recording"; new line explaining the "(not in docs)" marker, which the
  guide now uses for undocumented stage/slide points.
- Sources page: lead adds "a second attendee's recording of most of the day"; list style `padding-left:8mm`; the generated list grows
  from 33 to 78 entries (2 pages).

#### Key takeaways (10 -> 12 items)
- Item 4 (llms.txt) now also cites Gary Illyes's Q&A answer: D1-C054 D1-C061 D1-C454.
- Item 5 reworded "One crawling platform serves Google's products; Googlebot is one client of it": D1-C066 D1-C091 D1-C342.
- NEW item 7 "Login walls and paywalls read as 404" (auth demands and 402 dropped; CDN captcha with 200 = soft 404): D1-C365 D1-C366 D1-C367.
- NEW item 11 "AI Mode doesn't mean more Googlebot" (no extra crawling for AI Mode; crawl rate doesn't raise rankings): D1-C388 D1-C391 D1-C392.
- Items 1 and 9 shortened (same claims).

#### Section 01 · Day 1 at a glance
- Lead adds "Community lightning talks and a Q&A ran in between."
- NEW coverage note under the agenda: this edition adds a second attendee's recording; still not covered: Lightning session B and
  "What would you do?"; the robots.txt talk from slides only.
- The generated agenda now shows the proven speakers and coverage from sessions.yaml (D1-S01 Lino Cattaruzzi; D1-S02 Gary Illyes;
  D1-S03/S05/S06 Cherry Prommawin and Gary Illyes; D1-S04 James Powley, Rafael Kovashikawa and other community speakers;
  D1-S10 role "Search Relations"; D1-S11 Tobias Schwarz and Jovana Avramovic; D1-S12 John Mueller and Gary Illyes; transcript coverage).

#### Section 02 · The state of Search
- CORRECTION (D1-C001): quote byline "Elizabeth Reid, VP, Search — opening slide" -> "— quoted on a keynote slide".
- NEW stage paragraph, Lino Cattaruzzi's keynote: "Google Search now is AI search", intelligent search box = biggest change in 25 years,
  text/speech/images, AI Overviews and AI Mode as one experience: D1-C149 D1-C150 D1-C151 D1-C152 D1-C189.
- NEW h3 "The ground rules: Google doesn't sell rankings" (Honest Results Policy): D1-C143 D1-C144 D1-C178 D1-C179 D1-C180.
- "The numbers Google showed": note rewritten (two rows from slides, a last row said on stage); NEW stat row: 1B+ AI Mode monthly
  users (D1-C169), 2.5B AI search users = AI Overviews monthly per I/O 2026 (D1-C165 D1-C181), 1B+ clicks/week from AI responses
  (D1-C156), 1.5B Lens users monthly (D1-C190 D1-C191).
- NEW stage paragraph: billions of clicks to the open web daily; 77% decide faster; 18-24 year olds ask more (last two not in docs):
  D1-C154 D1-C174 D1-C166.
- Search Agents paragraph extended: plain-language request -> alert, launched globally a day or two before (not in docs), press report
  of the 28 September rollout: D1-C022 D1-C194 D1-C192 D1-C193 (second slide example "government shutdown" dropped for space).
- NEW stage paragraph after the principles table: principle 4 "created by humans or by AI ... high quality" and the closing "UEO":
  D1-C175 D1-C059 (applies the D1-C059 correction: UEO now tied to the keynote, who Lino Cattaruzzi; principles D1-C010 to C014 are
  keynote claims after the session move).
- Analysis callout (D1-C015) shortened, same point.

#### Section 03 · New publisher controls
- Generative AI performance report paragraph: NEW stage sentence, reporting starts with impressions only and may expand: D1-C196.

#### Section 04 · How Search works, and where AI sits
- NEW stage paragraph under the matrix: AI features have extra processes but the bulk is the same as Search: D1-C208.
- NEW h3 + table "The pipeline, step by step" (Cherry Prommawin): discovery D1-C201 D1-C202; crawling D1-C203; indexing D1-C204
  D1-C206 D1-C207 D1-C205; index selection D1-C211 D1-C212 D1-C213; serving D1-C214 D1-C215 D1-C216 D1-C222 D1-C223.
- NEW paragraph after the AI cards: "Did you mean" ~2001-2002, RankBrain ~2015-2016, MUM Everest example, analysis on dates:
  D1-C209 D1-C217 D1-C218 D1-C219.
- "Good SEO is good GEO": Gary Illyes paragraph extended with "Search engine R.I.P." (10 Nov 1997) and "SEO is not dead":
  D1-C049 D1-C197 D1-C198 (D1-C049 now a D1-S02 claim after the session move; text unchanged).
- Docs paragraph: NEW stage sentence, fan-out is "just ten different searches that fire in the background": D1-C225.
- CORRECTION (D1-C046): callout heading "Audience question · ..." -> "Google's "Your question" slide · ...", and the slide paragraph now
  says Gary Illyes presented it as the question the topic usually prompts, not one asked in the room (D1-C047 D1-C046).
- NEW stage paragraph in the callout: "We care more about the quality of the content than how it was created"; human-created
  "or at least edited and reviewed" (not in docs): D1-C210 D1-C221.
- NEW h3 "Searching with images": Lens as the answer to reverse image search (D1-C188 D1-C190), images broken into vectors
  (D1-C224), transformers remark with analysis (D1-C199 D1-C200).

#### Section 05 · How crawling works
- Kicker "Section 05" -> "Section 05 · Cherry Prommawin and Gary Illyes".
- NEW h3 "Googlebot is just an HTTP client": D1-C322 D1-C338 D1-C323; hundreds of crawlers, one infrastructure, docs "dozens",
  analysis on verifying unknown user agents: D1-C324 D1-C326 D1-C325 D1-C342 D1-C344 D1-C138; docs 2MB fetch limit: D1-C136.
- NEW h3 "How the scheduler decides": D1-C336 D1-C337 (links and sitemaps), D1-C332 (change frequency), D1-C331 (spammy URLs),
  D1-C334 D1-C335 (team priorities, Gemini tokens).
- NEW paragraph: Crawl Stats "most valuable tool", logs "the real thing": D1-C339 D1-C340 D1-C341.
- NEW h3 + table "Who reads robots.txt, and who doesn't" (said in the crawling talk, a lightning talk and the Q&A): D1-C329,
  D1-C330 D1-C343, D1-C434 D1-C273, D1-C435 D1-C436, D1-C428 D1-C429; closing stage paragraph on agents and carts: D1-C437.
- (The slide claims D1-C063 to C065 now carry who Gary Illyes; the template text did not need a change.)

#### Section 06 · Crawl errors
- CORRECTION (D1-C069, D1-C070): opening stage paragraph now names Gary Illyes and says soft 404s are "one of the biggest problems on
  the internet right now for crawling and for showing up in Search" (was: "Soft 404s were also raised").
- NEW h3 + table "Status codes, class by class" (Cherry Prommawin): 1xx D1-C345 D1-C346; 2xx D1-C347 D1-C320 D1-C348;
  3xx D1-C349 D1-C350; 4xx D1-C351 D1-C352 D1-C353; 5xx D1-C354. NEW docs line: up to 10 redirect hops: D1-C370.
- NEW h3 "Login walls, paywalls and pay-per-crawl": D1-C365 D1-C366 (quote "402 will just mean 404 to us"); analysis callout D1-C372.
- NEW h3 "DNS, networks and CDNs": D1-C357 D1-C358 D1-C362; D1-C359 D1-C361; D1-C364 D1-C367 D1-C371; D1-C360 D1-C363.

#### Section 07 · robots.txt, read the way Google reads it
- No change (the talk was not recorded). Contents description unchanged in substance.

#### Section 08 · Crawl budget
- CORRECTION (D1-S10 role): kicker "Cherry Prommawin, Search Advocate" -> "Cherry Prommawin, Search Relations".
- Opening stage paragraph adds the formal definition: D1-C096 D1-C373.
- NEW list under the formula figure: hostload per host, not per site (D1-C374 D1-C376); site-wide quality for demand (not in docs)
  with analysis (D1-C377 D1-C420).
- Path-inheritance slide paragraph gets a "(not in docs)" marker (D1-C094, undocumented).
- "Who needs to care": NEW paragraph answering "is crawl budget still a priority in 2026?" with analysis: D1-C380 D1-C381 D1-C382.
- "What burns it": slide paragraph adds the stage point on infinite URL spaces (calendars): D1-C099 D1-C378.
- "How to manage it" card 04 adds the kinds of useless content: D1-C103 D1-C109 D1-C379.
- CORRECTION (D1-C107): nofollow row "The catch" now explains that Google doesn't crawl through the nofollow link itself but crawls
  the target when found through other links or sitemaps (D1-C107 D1-C127).
- NEW paragraph "Status codes don't all cost the same" with analysis: D1-C383 D1-C384 D1-C385 D1-C419 D1-C386.
- NEW callout "Questions sent in before the event": AI Mode and crawling (D1-C387 D1-C388 D1-C389); crawl frequency and rankings
  (D1-C390 D1-C391 D1-C392); how to check in Crawl Stats (D1-C393 D1-C394 D1-C396 D1-C395).

#### Section 09 · Lightning talks from the community (NEW section, D1-S04 and D1-S11)
- Lead: close to 200 submissions, community views: D1-C227 D1-C228.
- Session A cards: James Powley, AI that applies your rules (D1-C229 D1-C232 D1-C233 D1-C234 D1-C235); Rafael Kovashikawa, LLM errors
  on search data (D1-C239 D1-C243 D1-C244 D1-C247 D1-C242 D1-C264); a community demo, LLM fix loop for structured data (D1-C250
  D1-C252 D1-C251 D1-C265 D1-C269); a community speaker, automating monthly reports (D1-C253 D1-C255 D1-C256 D1-C259 D1-C260 D1-C263
  D1-C266 D1-C267).
- "Preparing sites for humans and AI agents": D1-C270 D1-C274 D1-C131; figure "Agent readiness in three layers" (D1-C284 D1-C275
  D1-C277 D1-C278 D1-C279 D1-C276 D1-C281 D1-C283); list: ARIA (D1-C279 D1-C280), WebMCP (D1-C283 D1-C282 D1-C316), markdown copies
  and llms.txt (D1-C272 D1-C271), schema for agents + analysis (D1-C276 D1-C315), headings docs + analysis (D1-C313 D1-C314).
- "GEO: its numbers and its myths": D1-C286 D1-C287; D1-C289 D1-C290; D1-C291 D1-C293; D1-C294 D1-C295; D1-C296 (contradicts Google's view).
- "AI search as a funnel" table: D1-C299 D1-C300 D1-C302 D1-C303 D1-C304 D1-C305 D1-C306 D1-C307 D1-C309 D1-C310.
- Session close by a Google host: D1-C311 D1-C312.
- Session C cards: Tobias Schwarz, similar URLs (D1-C397 D1-C398 D1-C399 D1-C400 D1-C401 D1-C403 D1-C404 D1-C405 D1-C421);
  Jovana Avramovic, technical SEO in AI search (D1-C406 D1-C408 D1-C409 D1-C412 D1-C413 D1-C414 D1-C415 D1-C417 D1-C418).
- Table "Five kinds of similar URLs" (kinds from D1-C399; the example URLs are illustrative) and a stage note on hardening (D1-C402).

#### Section 10 · The Q&A (NEW section, D1-S12, John Mueller and Gary Illyes)
Twelve question cards (answers name a speaker only where the claim's who does; otherwise "a panelist" or "Google"):
- AI vs search crawling, and can GEO hurt classic search: D1-C422 D1-C423 D1-C424 D1-C425 D1-C426.
- llms.txt and cats.txt: D1-C453 D1-C454 D1-C455 D1-C456 D1-C457 D1-C460 D1-C471 D1-C472 D1-C473.
- Huge real-time sites: D1-C438 D1-C439 D1-C440.
- Crawl waste in logs: D1-C441 D1-C442 D1-C443 D1-C444 D1-C445 D1-C446 D1-C447.
- New articles crawled within minutes: D1-C465 D1-C466 D1-C467 D1-C468 D1-C469 D1-C470 D1-C492.
- Demand or capacity drop: D1-C493 D1-C494.
- Search Console AI reporting: D1-C448 D1-C449 D1-C450 D1-C451 D1-C452.
- Crawl stats in the API, and asking for features in volume: D1-C461 D1-C462 D1-C463 D1-C464 D1-C120 (D1-C120 moved here from
  "From the floor", following its session move D1-S00 -> D1-S12).
- Migrations and sitemaps: D1-C476 D1-C477 D1-C478 D1-C479 D1-C480 D1-C474 D1-C475.
- Separate AI user agents, Google-Extended, default-deny: D1-C481 D1-C482 D1-C483 D1-C484 D1-C485 D1-C486 D1-C488 D1-C489.
- Paginated pages replaced by load-more: D1-C490 D1-C491.
- Crawlers beyond robots.txt, research-crawler best practices: D1-C427 D1-C431 D1-C432 D1-C433.

#### Section 11 · From the floor (was Section 09)
- Kicker/number renumbered; lead now "points that neither my notes nor the recording tie to a session".
- REMOVED card "Getting Google to build something" (D1-C120): now in the Q&A (session moved to D1-S12).
- Pagination card adds the Q&A answer (no crawlable links -> further pages unseen): D1-C114 D1-C115 D1-C491 (D1-C114 stays a D1-S00
  claim; its move was deferred).
- NEW card "Rich results": D1-C122 D1-C265.

#### Section 12 · Audit checklist (was Section 10)
- Twelve -> sixteen checks; lead and contents updated.
- Changed: "Maintenance, rate limits and bot challenges return 503 or 429, never a 200 error or captcha page": D1-C078 D1-C367.
- NEW: verified Googlebot never gets 401/402/403 (D1-C365 D1-C366 D1-C372); URL variants redirect to one expected URL (D1-C445
  D1-C403 D1-C404); load-more lists keep crawlable links (D1-C491 D1-C115); publish-to-first-crawl time tracked (D1-C467 D1-C492).

#### Section 13 · Help complete this guide (was Section 11)
- Gaps list: now the robots.txt talk (slides only), Lightning session B, "What would you do?" and the opening minutes of the crawl
  budget talk (Lightning A, Lightning C and the Q&A are covered).
- Second card "Coming next / An agent-ready version" replaced by "The full knowledge base / Every Day 1 point, in the web edition"
  (nearly 500 points), as on Day 3; contact line "...or to get the web edition".

</details>

<details>
<summary><b>Open the v2.7.0 list for Day 1</b>: what the six audio recordings changed in the Deep Dive guide (31 -> 34 pages)</summary>

#### Whole guide
- 31 -> 34 pages. Section 07 grew from 2 to 4 pages (Google's talk and Lightning B), Section 10 from 2 to 3 pages (Q&A additions).
- `days.yaml` day1: `sources_checked` 3 October 2026 -> 4 October 2026.
- Contents: row 07 "Google's talk and quiz, the group traps, redirect chains (Lightning B)"; row 10 "AI crawlers, llms.txt, demand and
  capacity, migrations, load-more"; row 11 "Duplicate content, images, accessibility, rich results"; row 12 "Nineteen checks".
- Sources page: lead adds "six audio recordings"; the generated list grows from 78 to 91 entries (still 2 pages).

#### Key takeaways
- Item 7 (login walls): "a 403 or a 402, both on the rise": D1-C365 D1-C509.
- Item 8 (one group): "Groups don't add up": D1-C533 D1-C526.

#### Section 01 · Day 1 at a glance
- Coverage note: the second recording plus six audio recordings, "where they disagree, the audio wins"; still not covered:
  "What would you do?" and the rest of Lightning B.
- Generated agenda: D1-S04 adds Kira Breuer, Carlos Ortega and Thiago Pojda; D1-S07 slides and transcript; D1-S08 Dave Smart, transcript.

#### Section 02 · The state of Search
- Lino Cattaruzzi paragraph: NEW YouTube passed Netflix as the number one streaming service (D1-C497), with analysis: cite Nielsen's
  US watch time, nothing published backs "around the world" (D1-C498).

#### Section 05 · How crawling works
- Scheduler bullet: quote corrected to "the number of tokens is actually more important" (D1-C335).

#### Section 06 · Crawl errors
- CORRECTION (D1-C365): login walls paragraph says "more 403 responses ... described as 'authentication required'"; NEW: 402
  responses are an even more recent uptick (D1-C509).
- CORRECTION (D1-C362): DNS bullet "removed from Search and, with it, from every feature that depends on Search" ("AI included" dropped).
- CORRECTION (D1-C364): CDN bullet "injecting 429 or 503 responses on the way between Google and your site".
- "How to find these errors": soft 404s in the page indexing report, Crawl Stats for other crawl issues: D1-C508 D1-C368.

#### Section 07 · robots.txt, read the way Google reads it (rewritten; kicker "How Google interprets robots.txt · Lightning session B")
- Lead: robots.txt has only three rules: D1-C516.
- NEW h3 "What robots.txt is, and what it isn't": 1994 and Martijn Koster, Google since 1996, RFC 9309, access not use:
  D1-C510 D1-C511 D1-C512 D1-C513.
- NEW cards: not a security measure (D1-C514); three rules, one place (D1-C515 D1-C516 D1-C517); comments and
  thebestfriedchickenever.com (D1-C518 D1-C089).
- NEW paragraph: robots.txt is "extremely forgiving" (D1-C525), with analysis on the misspellings the open-source parser accepts (D1-C532).
- The slide puzzle is unchanged (D1-C079 to C083, D1-C086); NEW paragraph with the talk's own walk-through: D1-C520 D1-C521.
- NEW h3 "Groups: one per crawler, never added together": D1-C519 D1-C527; quiz answer (D1-C531); docs (D1-C080).
- "The group-closing trap" renamed "The unknown-line trap": NEW stage paragraph on the 50-50 split while writing RFC 9309 (D1-C526).
  The slide paragraph, figure and caption are unchanged: a later slide of Google's talk (D1-C087 D1-C123, which stay in D1-S07;
  the talk's audio reads out the same example). Analysis callout unchanged (D1-C088 D1-C084).
- Google-Extended: card replaced by a docs paragraph (D1-C086) and a NEW stage and analysis paragraph: directory or whole-site
  opt-out, Applebot-Extended, and the "first" claim corrected by GPTBot (August 2023) against Google-Extended (28 September 2023):
  D1-C522 D1-C524 D1-C523.
- NEW h3 "The robots.txt report": version history, open-source parser, CDN changes, cloaked files: D1-C528 D1-C529 D1-C530 D1-C140.
- NEW h3 "Lightning session B: when a redirect meets a blocked URL" (Dave Smart): groups are not additive (D1-C533); NEW figure
  "Blocked by a URL you never see" (illustrative paths); the chain is checked hop by hop and reported on the first URL
  (D1-C534 D1-C535); every kind of redirect (D1-C536); what to do (D1-C537).

#### Section 09 · Lightning talks from the community
- Automating monthly reports card: "A community speaker" -> "Kira Breuer" (named, D1-C253 to D1-C263).
- Rafael Kovashikawa card: quotes "not let the model grade its own homework" and "If there is no receipt, there is no
  reimbursement." (D1-C243 D1-C244, checked); NEW Pascal's makers of false windows: LLMs "sometimes don't aim for the most accurate
  figures" (D1-C500).
- Structured-data demo card: NEW URL and code modes (D1-C501), keyword rules (D1-C503), empty name and price of zero (D1-C502),
  hedged as a largely unintelligible recording; docs: D1-C506 D1-C507.
- "Preparing sites for humans and AI agents · Carlos Ortega" (named, D1-C270 to D1-C284); CORRECTION (D1-C282) WebMCP
  "testable through browser flags".
- CORRECTION (D1-C272, D1-C271): markdown copies, "cloaking" hedged as an uncertain word; the llms.txt study heard as Ahrefs',
  97% of almost 40,000 sites; NEW analysis with Ahrefs' published figures (D1-C505).
- "GEO: its numbers and its myths · Thiago Pojda" (named, D1-C286 to D1-C296); the unchecked D1-C287 quote replaced by a paraphrase.
- CORRECTION (D1-C294): the 43% study "heard as Peec AI's", no "80-87%"; NEW analysis: in Peec AI's study the 43% is a share of
  fan-out searches (D1-C504).
- CORRECTION (D1-C311): closing host paragraph, content generation is something none of the talks featured.

#### Section 10 · The Q&A
- Lead: now checked against two audio recordings of most of the panel.
- AI crawlers card: quote "my feeling is a lot of the AI crawlers are still a bit stupid." (D1-C423).
- llms.txt card: CORRECTION (D1-C453) title adds PageSpeed Insights; quote "Just because maybe something will change ..."
  (D1-C456); NEW "it's designed for allegedly intelligent systems" (D1-C458).
- Real-time sites card: "such as sports sites" (D1-C438); CORRECTION (D1-C439) "useful to users" replaces "popular"; NEW crawl
  demand from Search, Ads or other products, capped by capacity (D1-C538).
- Crawl waste card: redirects cost crawl budget at first, then a clean slate (D1-C445); "calendar parameters" (D1-C446); NEW
  handled at the web server, an Apache rule or module (D1-C539).
- News card: CORRECTION (D1-C465) retitled to the question as asked; NEW "two hours is probably not great" (D1-C543); John Mueller
  named for the discovery and refresh split (D1-C492); NEW half of crawling goes to discovery (D1-C544).
- Demand vs capacity card: NEW question with the 100-million-page framing (D1-C545); CORRECTION (D1-C493) "most of the time an
  abrupt step down" replaces "very sharp"; NEW hostload 10 -> 5 (D1-C546); NEW analysis on connections (D1-C547).
- Search Console AI card: CORRECTION (D1-C449, D1-C452) a panelist expected more AI reporting, without a timeline or a promise;
  data would have to be grouped to protect privacy.
- API card: CORRECTION (D1-C464) vibe-coded tools as the reason.
- Migration card: NEW sitemaps are not the main tool (D1-C540); CORRECTION (D1-C479) both old URLs got one target path; NEW
  JavaScript was used, whether for the redirects or for the mapping is not fully clear (D1-C541), with analysis: use server-side
  301 or 308 redirects (D1-C542); CORRECTION (D1-C474, D1-C475) "a sitemap has no sweet spot".
- Load-more card: D1-C114 moved here from "From the floor": the question (D1-C490), "kind of dangerous, depending on what you want
  to achieve" and "Googlebot is not running around clicking on buttons" (D1-C114 D1-C491, checked quotes); docs D1-C115.
- Crawler-behaviour card: CORRECTION (D1-C432) the exemption and its reason, a best reading of the recording (D1-C427 no longer
  flagged as unclear).

#### Section 11 · From the floor
- Pagination card removed (D1-C114 is now in the Q&A; "adopt carefully, check your logs" dropped). Five cards remain.

#### Section 12 · Audit checklist (16 -> 19 checks)
- Changed: each crawler gets the rules you expect, "and groups don't add up" (D1-C533).
- NEW: no secret path in robots.txt, private areas behind authentication (D1-C514).
- NEW: the robots.txt report's version history shows no change you didn't make (D1-C528 D1-C529).
- NEW: every URL reported as blocked by robots.txt has its redirect chain tested (D1-C534 D1-C537).

#### Section 13 · Help complete this guide
- Gaps list: the robots.txt talk and Lightning B removed; now the rest of Lightning B, "What would you do?" and the opening
  minutes of the crawl budget talk. "More than 540" points (was "nearly 500").

</details>

### In the knowledge base, but in neither edition

These new points are on the session and topic pages, in the kits, the agent pack and the web edition, but did not fit in the printed guide:

- Keynote colour (D1-C142, C145-C148, C153, C155, C157-C164, C167, C168, C170-C173, C176, C177), D1-C182-C187, D1-C195 (D1-C185
  SUV example was drafted, then dropped for space), D1-C220, D1-C226, D1-C230 D1-C231 D1-C236-C238 D1-C240 D1-C241 D1-C245 D1-C246
  D1-C248 D1-C249 D1-C254 D1-C257 D1-C258 D1-C261 D1-C262 D1-C268 D1-C285 D1-C288 D1-C292 D1-C297 D1-C298 D1-C301 D1-C308,
  D1-C317-C319 D1-C321 D1-C327 D1-C328 D1-C333, D1-C355 D1-C356 D1-C369, D1-C375, D1-C407 D1-C410 D1-C411 D1-C416,
  D1-C430 (drafted, dropped for space), D1-C459, D1-C487, and the older D1-C137 D1-C139 D1-C141.
- v2.7.0: D1-C496 and D1-C499 (keynote). D1-C140, D1-C368 and D1-C458 from the earlier list are now in the Deep Dive guide.

<p align="center"><img src="../../_system/brand/divider.svg" width="600" alt="Section divider"></p>

## <img src="../../_system/brand/icons/coral.svg" width="24" height="24" alt=""> Day 2 · Indexing

The classic Day 2 guide was written from the author's own 12 transcripts and 64 photos. For Day 2 the second recording is an independent second transcript. It filled gaps: the welcome Q&A, the end of the robots meta talk, the part on main content, Lightning sessions E and F, the end of the video talk and the poster topics. It also settled words the first transcript had marked as uncertain. The Deep Dive guide grew from 32 to 35 pages, with 14 key takeaways instead of 12, 17 checklist items instead of 15 and 15 rows of undocumented points instead of 13. It cites 135 more claims and lists 122 sources instead of 115.

v2.7.0 changed no Day 2 claim text: D2-C025, D2-C050 and D2-C884 only gained links to new Day 1 claims.

### New claims by session

145 new Day 2 claims; the classic edition has none of them. (v2.5.0 added 144; the open-items review after v2.6.0 added the analysis D2-C982.) The table also shows the session records whose speaker, role or coverage changed. A speaker is named only with proof: a self-introduction, an on-stage hand-over or back-reference, matched to the official speaker list.

| Session | New claims | Speaker and coverage in the classic edition | Now |
| --- | ---: | --- | --- |
| `D2-S02` Welcome to indexing day! | 12 | Google; coverage: slides | Gary Illyes, Cherry Prommawin; role Search Relations; coverage: transcript, slides |
| `D2-S03` How is HTML interpreted | — | Google | Cherry Prommawin; role Search Relations |
| `D2-S04` Controlling indexing | 6 | unchanged | unchanged |
| `D2-S05` Lightning session D: Rendering and JavaScript | 5 | Erin Sparling, Sören Bendig, a community speaker, Natalia Venditto | Erin Sparling, Sören Bendig, Rebecca Yu, Natalia Venditto |
| `D2-S07` Understanding what's on a page | 12 | unchanged | unchanged |
| `D2-S08` Handling web duplication | — | Google | John Mueller; role Search Relations Team Lead |
| `D2-S09` Lightning session E: Managing Duplicates and Site Moves | 43 | Tobias Schwarz; role CTO and Founder, Audisto | Tobias Schwarz, Martyna Ağanoğlu, David Carrasco Pamies |
| `D2-S12` What is Structured Data and why we need it on the internet. | — | Google | Ryan Levering; role Software Engineer |
| `D2-S13` Using images to your advantage and Engaging Search users with videos | 30 | unchanged | unchanged |
| `D2-S14` Lightning session F: Media | 15 | Community speakers; coverage: none | a community speaker, Patrick Domanico; coverage: transcript |
| `D2-S15` Focusing on Internationalisation and Localisation | 3 | unchanged | unchanged |
| `D2-S16` Lightning session G: Internationalisation | 16 | unchanged | unchanged |
| `D2-S17` Poster session H: Indexing | 3 | coverage: none | coverage: transcript |
| **Total** | **145** | | |

### Corrected claims

The classic edition was built from the wording on the left. Where it quotes or paraphrases one of these claims, the Deep Dive edition follows the right-hand column.

| Claim | The classic edition and v2.4.0 said | Now | Why |
| --- | --- | --- | --- |
| `D2-C117` | AI Overviews and AI Mode typically do not ground their answers by reading pages live, unlike Gemini when a user asks about a specific page, Google appeared to say (the key word is unclear in the recording). | AI Overviews and AI Mode typically do not ground their answers by reading pages live, unlike Gemini when a user asks about a specific page, Google said. | The unclear word ("live grounding") is clear in the second recording. |
| `D2-C821` | John Mueller suspected that if robots meta tags were reinvented today, the page-level nofollow rule would probably not be part of them (the negation is unclear in the recording). | John Mueller suspected that if robots meta tags were reinvented today, the page-level nofollow rule would probably not be part of them. | The negation, unclear before, is clear in the second recording. |
| `D2-C212` | In the speaker's product page example, three of the mistakes combine: product links in non-crawlable markup (apparently onclick handlers; the word is unclear in the recording) keep the product detail pages hidden, the product API is blocked in robots.txt, and some content waits for a user interaction. | In the speaker's product page example, three of the mistakes combine: product links behind onclick handlers keep the product detail pages hidden, the product API is blocked in robots.txt, and some content waits for a user interaction. | Both recordings have "on click". |
| `D2-C213` | A page that renders empty for Google, such as a client-side product page hit by these mistakes, ends up treated as a soft 404 even though users see a full page. | A page that renders empty for Google, such as a client-side product page hit by these mistakes, is seen as thin content and ends up treated as a soft 404 even though users see a full page. | Both recordings have the thin-content step. |
| `D2-C146` | On a retail brand's page, the rendered version promised a 50% discount for a newsletter sign-up while the non-rendered version showed 10%, a mismatch that can hurt customer satisfaction. | On a retail brand's page, the rendered version promised a bigger discount for a newsletter sign-up than the non-rendered version that was served, a mismatch that can hurt customer satisfaction; the two recordings disagree on the figure the rendered page promised. | The two recordings disagree on the figure (50% in one, 15% in the other), and no slide exists. v2.5.0 printed both figures; after v2.6.0 the figures were removed from the claim. |
| `D2-C217` | Natalia Venditto opened by recalling a remark made earlier at the event that everyone can write a standard, and said that is what the Web Fragments work is trying to do. | Natalia Venditto opened by saying that Gary had said earlier at the event that everyone can write a standard, and that this is what the Web Fragments work is trying to do. | Both recordings have her crediting the remark to Gary. |
| `D2-C135` | After Google's opener, Lightning session D had three community talks: rendering and JavaScript execution blind spots (Sören Bendig), debugging JavaScript rendering for Search (a community speaker) and virtualizing the browser (Natalia Venditto). | After Google's opener, Lightning session D had three community talks: rendering and JavaScript execution blind spots (Sören Bendig), debugging JavaScript rendering for Search (Rebecca Yu) and virtualizing the browser (Natalia Venditto). | The speaker introduced herself by name. |
| `D2-C279` | Erin Sparling recommended polyfills to keep a site compatible with Google's rendering engine where it lacks a browser feature. | Erin Sparling recommended differential serving and polyfills to keep a site compatible with Google's rendering engine where it lacks a browser feature. | The second recording has "differential serving and polyfills", as in Google's docs. |
| `D2-C267` | When the JavaScript is not accessible to Googlebot, Google cannot render the client-side DOM that the page builds asynchronously, so only parts of the page may be present. | When the JavaScript is not accessible to Googlebot, Google cannot render the client-side DOM that the page builds asynchronously, so parts of the page may be present while the main content is absent. | The second recording completes the sentence the first broke off. |
| `D2-C323` | When tokenizing for Search, Google attaches metadata to each token for use in ranking, such as whether the word appeared in the header or in the main content (tagged 'centerpiece' on the slide), in bold or in the title; Gary Illyes said he was not showing all of the metadata. | When tokenizing for Search, Google attaches metadata to each token for use in ranking, such as whether the word appeared in the header or in the main content (tagged 'centerpiece' on the slide), in bold or in a heading; Gary Illyes said he was not showing all of the metadata. | Both recordings have "in a heading"; the third item differs between them, so it is left out. |
| `D2-C325` | Tokenization for AI models such as Gemini, in training and in inference, differs from tokenization for Search, although Gary Illyes qualified this with 'or mostly'. Quote: "The tokenization for LLM training and inference, say when interacting with Gemini, is different than what it is for Search. Or mostly." | The same paraphrase, without the quote. | The two recordings word the quote differently ("LLM training" or "AI model training"), so it was dropped after v2.6.0; the paraphrase already says "AI models". |
| `D2-C825` | Gary Illyes added that text cut into chunks of 100 or 200 words may already have lost its meaning at that size. | Gary Illyes added that, once chunk size is thought of in millions of tokens as Gemini's context window allows, chunking has perhaps lost its meaning anyway. | A new reading of the sentence (the owner is asked to confirm it). |
| `D2-C340` | Google's soft 404 detection tells the page chrome, such as navigation and footer, apart from the main content by analysing the visual hierarchy of the page's text. | Google's soft 404 detection tells the page chrome, such as navigation and footer, apart from the main content by analysing the page's visual hierarchy alongside its text. | Small wording fix from the second recording. |
| `D2-C351` | Google treats a site migration as deduplication across sites, in which the old and the new domain are declared to be the same, so deduplication also helps Google handle migrations. | Google treats a site migration as deduplication across sites, in which the site owner says the old and the new domain are the same and that Google should pick the new domain, so deduplication also helps Google handle migrations. | The second recording completes the sentence ("pick my new domain"). |
| `D2-C382` | When localized pages are clustered, Google tries to use hreflang alternates, and the speaker called hreflang really helpful for same-language, different-country content. | When localized pages are clustered, Google tries to use hreflang alternates; the speaker's short version of the advice was to use hreflang, which he called really helpful for same-language, different-country content. | The short advice is to use hreflang. |
| `D2-C542` | Gary Illyes said one supported image format, heard as AVIF (the reading is uncertain), currently has hiccups and Google may have problems ingesting it, although it should technically be supported. | Gary Illyes said the AVIF image format currently has hiccups and Google may have problems ingesting it, although it should technically be supported. | AVIF is clear in the second recording. |
| `D2-C545` | If the AVIF reading is right, serve AVIF only through source elements inside picture and keep a WebP or JPEG file in the img src, which is the URL Google extracts, even though Google's documentation lists AVIF as supported; then check in Google Images that key images appear. | While the AVIF ingestion hiccup Gary Illyes mentioned lasts, serve AVIF only through source elements inside picture and keep a WebP or JPEG file in the img src, which is the URL Google extracts, even though Google's documentation lists AVIF as supported; then check in Google Images that key images appear. | The AVIF condition is resolved (see D2-C542). |
| `D2-C466` | Markup can state a date as a full ISO 8601 value, which disambiguates a visible date that Google might otherwise read wrongly; this matters wherever the date must be exactly right. | Markup can state a date as a full ISO 8601 value, which disambiguates a visible date whose local time zone Google might not detect correctly; this matters for event extraction and wherever the date must be exactly right. | The second recording has the time zone and event extraction. |
| `D2-C477` | As far as the speaker knows, in most of Google's main AI uses a page's schema.org markup is not tokenized and put directly into the model's context; the data is first sorted and checked before it is passed on as grounding context. | As far as the speaker knows, in most of Google's main AI uses a page's schema.org markup is not turned into text and put directly into the model's context; the data is first sorted out, checked for quality and indexed before it is passed on as grounding context. | The second recording has the indexing step. |
| `D2-C512` | Schema.org added support for RDF lists, a way to express ordered values, because RDF triples are not ordered by nature. | Schema.org added support for RDF lists and sets, which give a way to express ordered values, because RDF triples are not ordered by nature. | The second recording has "lists and sets". |
| `D2-C547` | Gary Illyes said over 219 million people in Southeast Asia consume content on or through YouTube daily (the daily scope is as heard and unverified). | Gary Illyes said over 219 million people in Southeast Asia consume content on or through YouTube daily (the daily scope was heard in two independent recordings but is not verified). | Heard in both recordings; still not verified against a source. |
| `D2-C613` | According to the speaker, shoppers in Europe and the US pay a lot of attention to promotions when deciding to buy (no source for this was captured), one of the cultural factors localisation should take into account. | According to the speaker, shoppers in Europe and the US pay a lot of attention to promotions and discounts when deciding to buy (no source for this was captured), one of the cultural factors localisation should take into account. | The second factor is clear in the second recording. |
| `D2-C614` | According to consumer data shown on a slide in the talk (source not captured), US consumers judge product quality more by user feedback and reviews, while for European shoppers brand reputation seems to weigh more (the verb is an uncertain reading of the recording). | According to consumer data shown on a slide in the talk (source not captured), US consumers judge product quality more by user feedback and reviews, while European shoppers seem to look more at brand reputation. | The verb is clear in the second recording. |
| `D2-C644` | Arabic and Persian contain letters that look identical to users but are different characters to software, with different Unicode code points. | Arabic and Persian contain letters that look identical to users but are different characters to software, with different Unicode code points; the example given was the letter ye, which has an Arabic and a Persian form. | The second recording names the example letter. |
| `D2-C646` | Lookalike Arabic and Persian character variants cause problems for data analysis and keyword research: data for one term can be split across the variants, which makes keyword research less accurate (that the data is what becomes fragmented is an uncertain reading of the recording). | Lookalike Arabic and Persian character variants cause problems for data analysis and keyword research: data for one term can be split across the variants, which makes keyword research less accurate. | The hedge is no longer needed. |

**Made public:** `D2-C821`, `D2-C117`, `D2-C247`, `D2-C248`, `D2-C249`. These claims were private only because a word was unclear in the first recording. The second recording settles that word, so the hedge was removed and the claims are now published.

**Deleted after v2.6.0:** `D2-C016` and `D2-C743` (jokes), `D2-C060`, `D2-C225` and `D2-C723` (duplicates of D2-C059, D2-C224 and D2-C677). All five were private, so no edition ever printed them; their IDs are retired and never reused.

**Speaker field (`who`) on existing claims:**

- "a community speaker" became Rebecca Yu: 37 claims (D2-C166, D2-C167, D2-C168, D2-C170, D2-C171, D2-C173, D2-C174, D2-C175, D2-C176, D2-C177, D2-C180, D2-C181, D2-C182, D2-C183, D2-C184, D2-C185, D2-C186, D2-C187, D2-C190, D2-C191, D2-C194, D2-C195, D2-C196, D2-C197, D2-C198, D2-C199, D2-C201, D2-C202, D2-C204, D2-C205, D2-C207, D2-C209, D2-C211, D2-C212, D2-C213, D2-C214, D2-C215).
- "Google" dropped, because the session now has a proven speaker: 20 claims (D2-C024, D2-C025, D2-C026, D2-C027, D2-C028, D2-C030, D2-C031, D2-C032, D2-C033, D2-C034, D2-C036, D2-C037, D2-C038, D2-C039, D2-C040, D2-C041, D2-C042, D2-C046, D2-C048, D2-C049).

### What the Deep Dive edition adds, section by section

<details>
<summary><b>Open the full list for Day 2</b>: every new or changed section, paragraph, table and checklist item, with the claims it cites</summary>

#### Whole guide
- Cover (modern cover only): edition date 2 October 2026 -> 3 October 2026.
- `days.yaml` day2: subtitle adds "plus the community talks on site moves and media" (printed on the Deep Dive cover);
  `sources_checked` 2 October 2026 -> 3 October 2026.
- Contents: same 15 sections; descriptions changed for Key takeaways ("fourteen things"), 03, 06 ("Clusters, canonical selection,
  canonical graphs, two site moves"), 07 ("Why markup matters, images, video, AI images, two media talks"), 08 ("hreflang code
  mistakes, localisation, non-Latin scripts, posters") and 13 ("Seventeen checks").
- Labels legend: Stage now "Said on stage, from my recordings or a second attendee's".
- Sources page: lead adds "and a second attendee's recording of most of the day"; list line-height 1.2 -> 1.15 and the closing
  note's top margin 8mm -> 4mm (layout only); the generated list grows from 115 to 122 entries.

#### Key takeaways (12 -> 14 items)
- NEW item 12 "A video needs a watch page and a visible player" (Gary Illyes: no watch page or below the fold = not indexed; docs:
  player at load): D2-C916 D2-C924 D2-C942 D2-C944.
- NEW item 13 "Consolidate by intent; never redirect to the homepage" (removed URLs get 404 or 410): D2-C881 D2-C883 D2-C911.
- Items 1, 5 shortened to one line (same claims).

#### Section 01 · Day 2 at a glance
- Lead adds "Community lightning talks ran in between"; "about 800 points" -> "nearly 1,000 points".
- NEW coverage note under the agenda: a second attendee's recording filled in the welcome Q&A, the end of the robots meta talk, the
  part on main content, Lightning sessions E and F and the end of the video talk; still not covered: Lightning J, "What would you
  do?", the Q&A and the wrap-up; of Poster session H only the topics.
- The generated agenda now shows the proven speakers and coverage from sessions.yaml: D2-S02 Gary Illyes and Cherry Prommawin
  (Search Relations); D2-S03 Cherry Prommawin; D2-S05 Rebecca Yu (was "a community speaker"); D2-S08 John Mueller (Search Relations
  Team Lead); D2-S09 adds Martyna Ağanoğlu and David Carrasco Pamies; D2-S12 Ryan Levering (Software Engineer); D2-S14 "a community
  speaker and Patrick Domanico" with transcript coverage (was not covered); D2-S17 transcript coverage (was not covered).

#### Section 02 · From HTML to extracted elements
- Kicker adds "· Cherry Prommawin" (D2-S03 speaker change).
- h3 "Four questions answered on the welcome slides" -> "Four questions from the welcome Q&A", with a NEW intro line: answered on
  slides, then on stage, by Gary Illyes and Cherry Prommawin (D2-C820 D2-C838).
- Card robots.txt and noindex: NEW stage sentence, a national tax authority blocking its key PDFs still gets their URLs shown (the
  example not in docs): D2-C844.
- Card HTML sitemaps: NEW stage quote "if you want to make one, knock yourself out": D2-C838.
- Card Out of stock: NEW stage contrast, a rare watch battery is worth the wait, a cheese is simply swapped (not in docs): D2-C841.
- Card Sitemaps: NEW stage quote "you can include it in robots.txt. No problem whatsoever." and the trade-off that anyone can then
  see the sitemap: D2-C842 D2-C843.
- (A fifth, spoken-only question on sloppy migrations, D2-C839 D2-C840, was drafted and dropped for space.)

#### Section 03 · Controlling indexing
- Rules table, nofollow row: adds that Mueller doubted the rule would exist if the tags were reinvented today: D2-C821 (claim made
  public in v2.5.0; the negation is confirmed by the second recording).
- "Robots rules, JavaScript and AI crawlers": NEW stage paragraph, robots meta rules only work if robots.txt lets Google fetch the
  page; a blocked page's URL can still be indexed, its content not: D2-C850 D2-C851.
- Paragraph on JavaScript-added rules rewritten: NEW stage quote "we won't even process the JavaScript" when the HTML has noindex,
  and the advice to put robots meta tags in the HTML exactly as intended (JavaScript only where nothing else is possible, as in a
  JavaScript web app); docs: Google says it *may* skip rendering on a noindex page; analysis: never serve a noindex that a script is
  meant to lift: D2-C106 D2-C108 D2-C852 D2-C853 D2-C107 D2-C854 D2-C855 (the old analysis "Ship robots rules in the server
  HTML", D2-C109, is still cited in the checklist).

#### Section 04 · Rendering and JavaScript
- Gemini paragraph adds: AI Overviews and AI Mode typically don't read pages live to ground their answers: D2-C117 (made public in
  v2.5.0; its hedge was removed after the second recording).
- CORRECTION (D2-C279): JavaScript problems table, fix cell "polyfills" -> "differential serving and polyfills".
- CORRECTION (D2-C146): blind-spots table, "a 50% newsletter discount in one version, 10% in the other" -> "a bigger newsletter
  discount in the rendered version than in the HTML the server sent (the two recordings differ on the figures)" (v2.5.0 printed
  "10% in one version and a bigger one in the other (50% or 15%)"; the figures were removed after v2.6.0).
- Paragraph after the blind-spots table: NEW stage points, one site rendered HTML tags into its meta description, which search
  engines would ignore; check rendering at scale with a modern crawler, not only in DevTools: D2-C142 D2-C858 D2-C860.
- CORRECTION (D2-S05 speaker): h4 "Debugging rendering for Search · community speaker" -> "· Rebecca Yu, JAKALA" (the claims of that
  talk now carry who: Rebecca Yu).
- Web Fragments paragraph: NEW stage sentence, she recommended server-rendering the fragments; an app reframed that way is fully
  indexable (not in docs): D2-C247 D2-C249 (both made public in v2.5.0).

#### Section 05 · Understanding what's on a page
- "The main content carries the weight": NEW stage paragraph with Gary Illyes's definition ("Main content is any part of the page
  that directly helps the page achieve its purpose"), what can be main content (images, videos, a tool, user-generated content,
  comments, tab content, every heading and the visible title), navigation and header as content the site doesn't particularly care
  about, and "It's the main content that we consider for ranking.": D2-C861 D2-C862 D2-C863 D2-C864 D2-C865 D2-C866 D2-C867 D2-C868.
- NEW docs paragraph: the Search Quality Rater Guidelines give the same definition; tabs, reviews and comments are main or
  supplementary content depending on the page's purpose: D2-C870 D2-C871.
- CORRECTION (D2-C323): token metadata "in bold or in the title" -> "in bold or in a heading".
- CORRECTION (D2-C325): the stage quote "The tokenization for LLM training and inference, say when interacting with Gemini, is
  different than what it is for Search. Or mostly." -> the paraphrase "Tokenization for AI models such as Gemini, in training and in
  inference, differs from tokenization for Search, 'or mostly'" (the two recordings word the quote differently).
- CORRECTION (D2-C825) in "The chunking myth": "text cut that small may already have lost its meaning" -> "thought of in millions of
  tokens, chunking has perhaps lost its meaning anyway"; NEW: Illyes also put the context window at 900,000 to a million (D2-C869);
  NEW analysis: Google's long-context docs say 1 million tokens or more, plan with one million as the floor (D2-C872).

#### Section 06 · Duplicates and canonicals
- Kicker adds "· John Mueller" (D2-S08 speaker change).
- CORRECTION (D2-S08 speaker, D2-C351): opening paragraph "Google's speaker gave two reasons" -> "John Mueller gave two reasons";
  the migration sentence adds "the owner says the old and the new domain are the same, and that Google should pick the new one".
- Canonical-graphs table, "Several canonicals on one page": adds "or ignores the tags completely": D2-C873.
- NEW h3 "Merging two competing sites · Martyna Ağanoğlu, Loando" (Lightning session E, talk 2):
  - context and three goals: D2-C874 D2-C875 D2-C876 D2-C877;
  - NEW figure "Keep, merge or remove" (2,000+ URLs scored, keep / merge / remove, ~100 URLs, about 95% fewer; old URLs 301 only to
    a same-intent page): D2-C878 D2-C879 D2-C880 D2-C881 D2-C882 D2-C883;
  - process paragraph (penalty check, no homepage redirects, sitemaps, change of address, internal links, merged analytics, experts
    introduced, daily Search Console checks) + docs: D2-C878 D2-C882 D2-C883 D2-C884 D2-C885 D2-C887 D2-C888 D2-C912;
  - results (traffic up from day one; revenue +100% month over month, speaker's figure, period not stated) + docs (no redirects to
    an irrelevant page; 404 or 410) + analysis (the code matters less; crawl budget hardly the gain at ~2,000 URLs): D2-C889 D2-C890
    D2-C911 D2-C913 D2-C914.
- NEW h3 "A migration after an acquisition · David Carrasco Pamies, Magnify" (Lightning session E, talk 3):
  - quote "I think there are no complex migrations. There are complex people.": D2-C893;
  - NEW one-row table of four kinds (absorb, keep apart, merge, plug in): D2-C894;
  - redirect map as the one document, 7,000+ URLs without a decision, prioritise by business value, ask support, sales and other
    teams: D2-C895 D2-C896 D2-C897 D2-C898 D2-C900;
  - freeze the inventory; 200s prove only that URLs work; test route, answer and lead; own baseline: D2-C902 D2-C903 D2-C904 D2-C905;
  - NEW code block "One row of a redirect map" (fields from the talk; values illustrative): D2-C899 D2-C904;
  - 304-day median recovery from an unnamed study, act at once; analysis vs Google's site move guide: D2-C906 D2-C907 D2-C915.

#### Section 07 · Feature extraction: structured data, images, video
- Kicker "Finding the gold nuggets: structured data, media, and more!" -> "Finding the gold nuggets · Lightning session F".
- CORRECTION (D2-S12 speaker): "A Google engineer who works on data ingestion" -> "Ryan Levering, a Google software engineer who
  works on data ingestion".
- CORRECTION (D2-C466): Extra content card, "full ISO dates" -> "full ISO dates (Google may misread a visible date's time zone)".
- CORRECTION (D2-C477): "Raw schema.org is generally not put straight into a model's context" adds "it is sorted, checked and indexed
  first".
- CORRECTION (D2-C542): Formats row, "one, heard as AVIF (an uncertain reading), has ingestion hiccups" -> "AVIF currently has
  ingestion hiccups".
- Video row rewritten: without a watch page, or below the fold, a video isn't indexed (the fold part not in docs); a video container
  in the HTML plus JSON-LD; docs: only watch-page videos are eligible, player on the page at load, not behind a click: D2-C553
  D2-C556 D2-C916 D2-C918 D2-C924 D2-C551 D2-C554 D2-C942.
- NEW h4 + list "The rest of the video talk": thumbnails and video speed, CDN (D2-C917 D2-C919 D2-C920); MP4 and standard codecs
  (D2-C921 D2-C922 D2-C923); video sitemaps, surrounding text, people talking about the video (D2-C925 D2-C926 D2-C927 D2-C929);
  YouTube or Vimeo (D2-C928); analysis on the first viewport (D2-C944).
- NEW h4 + list "Robots rules for images and video": media indexer, Googlebot-Image and Googlebot-Video, disallowed files
  (D2-C930 D2-C931 D2-C932); blocked videos never shown by bare URL (D2-C933); noimageindex also stops videos + analysis
  (D2-C934 D2-C935 D2-C945).
- NEW h4 + list "AI-generated images": owner's call, shown when users look for them, diffusion models garble text (the 2025 timeline
  example), check and regenerate (D2-C937 D2-C938 D2-C939 D2-C940 D2-C941); docs on IPTC trainedAlgorithmicMedia and C2PA (D2-C943).
- NEW h3 "Lightning session F: two community talks on media" (D2-S14):
  - card "LLM alt text that missed the point" (a community speaker): D2-C946 D2-C947 D2-C948 D2-C949 D2-C950 D2-C951 D2-C952, docs D2-C462;
  - card "Prompt journalism" (Patrick Domanico, dentsu): D2-C953 D2-C954 D2-C955 D2-C956 D2-C957 D2-C958 D2-C959 D2-C960.

#### Section 08 · Language, country and hreflang
- Kicker "Internationalisation and localisation · Lightning session G" -> "Internationalisation · Lightning session G · Posters".
- Opening paragraph adds: working out localised pages and target countries is one of the complex tasks of indexing: D2-C961.
- NEW stage paragraph under "hreflang code mistakes": wrong codes are a very frequent mistake, especially in Europe: D2-C962.
- Country targeting paragraph: NEW analysis, a second recording heard "IP address" for the strongest signal; the docs back the
  ccTLD: D2-C982.
- Lightning G card 2 renamed "Lookalike letters in non-Latin scripts" -> "Non-Latin scripts: letters, direction, keyboards":
  CORRECTION (D2-C644, D2-C646) adds the Arabic and Persian ye example and drops the "partly an uncertain reading" hedge; NEW:
  mixed right-to-left and left-to-right titles, product names and URLs (D2-C963 D2-C964), Persian queries typed in Latin letters
  (D2-C965) with docs on Hindi (D2-C981).
- NEW paragraph: bought links still visibly sway competitive Persian, Turkish and Arabic results (presenter's observation, not in
  docs); Google treats bought links as spam; the October 2023 update + docs + analysis that it names neither Persian nor link spam:
  D2-C967 D2-C968 D2-C977 D2-C978 D2-C979.
- NEW paragraph: cross-lingual retrieval in AI answers to Persian queries, features launching language by language (docs: site
  names in all languages in September 2023), fewer Persian link opportunities, market maturity: D2-C972 D2-C971 D2-C980 D2-C969
  D2-C970 D2-C973.
- NEW h3 "Poster session H": why posters, the topic list, one poster by a Googler: D2-C974 D2-C975 D2-C976.

#### Section 12 · What changed since Day 1
- Row "robots.txt and noindex", Day 2 cell adds: an important URL may be indexed without its content; robots meta rules need a
  fetchable page: D2-C846 D2-C850.
- NEW row "Opting out": Day 1 D1-C329 (robots.txt is how owners opt out) / Day 2 D2-C848 (Google strongly believes owners should be
  able to opt out, for legal reasons or crawl budget).
- Row "Soft 404s", Day 2 cell adds: after a migration, 200s prove only that URLs work: D2-C903.

#### Section 13 · Day 2 action checklist (15 -> 17 checks)
- Lead "Fifteen" -> "Seventeen"; group "Duplicates and canonicals" -> "Duplicates, canonicals and site moves".
- NEW: every moved URL has an approved same-intent destination; removed URLs return 404 or 410, never the homepage: D2-C895 D2-C883 D2-C911.
- NEW: watch pages load the player in the first viewport without a click, and carry no noimageindex: D2-C944 D2-C945.

#### Section 14 · Said on stage, not in Google's docs (13 -> 15 rows)
- NEW: a video below the fold is not indexed (Gary Illyes) + analysis: D2-C924 D2-C944.
- NEW: noimageindex also stops videos; a blocked video never shows as a bare URL (Gary Illyes): D2-C935 D2-C933.

#### Section 15 · Help complete this guide
- Gaps list: was Lightning E (site moves), Lightning F (Media), Poster H and Lightning J, "What would you do?", the Q&A and wrap-up;
  now "A second attendee's recording filled most of the first edition's gaps": Lightning J, "What would you do?", Poster H beyond
  the topics, the Q&A and the wrap-up.
- Card 2: "all of Day 2's points, about 800" -> "nearly 1,000".

</details>

### In the knowledge base, but in neither edition

These new points are on the session and topic pages, in the kits, the agent pack and the web edition, but did not fit in the printed guide:

- D2-C839 D2-C840 (fifth welcome question, sloppy migrations: drafted, dropped for space), D2-C845, D2-C847, D2-C849, D2-C856,
  D2-C857, D2-C859, D2-C886, D2-C891, D2-C892, D2-C901, D2-C908, D2-C909, D2-C910, D2-C936 (repeats D2-C089), D2-C966.
- Corrected claims cited in the guide whose wording there needed no change: D2-C340 (the text already says the model reads layout),
  D2-C382 (the card already quotes "We try to use hreflang alternates"), D2-C545 (the analysis text no longer depended on the AVIF
  hedge once D2-C542 was fixed), plus every D2-S03 claim whose who "Google" was dropped (D2-C024 to D2-C049: the kicker now names
  Cherry Prommawin).
- Corrected claims not cited in the guide: D2-C135, D2-C212, D2-C213, D2-C217, D2-C248, D2-C267, D2-C512, D2-C547, D2-C613, D2-C614.

<p align="center"><img src="../../_system/brand/divider.svg" width="600" alt="Section divider"></p>

## <img src="../../_system/brand/icons/seaweed.svg" width="24" height="24" alt=""> Day 3 · Serving

Until v2.6.0 all three Day 3 editions had the same content. v2.5.0 changed no Day 3 claim text: 26 Day 3 claims only gained links to the new Day 1 and Day 2 claims they repeat or extend. After v2.6.0 the open-items review corrected or hedged seven Day 3 claims, and the Deep Dive guide changed in two places. It still has 33 pages and cites the same claims; the classic editions have neither change. v2.7.0 only linked D3-C617, D3-C624 and D3-C667 to new Day 1 claims.

### Corrected claims

| Claim | The classic edition and v2.4.0 said | Now | Why |
| --- | --- | --- | --- |
| `D3-C631` | Google estimated that meta annotations, such as robots meta tags, are processed in typically 45 to 90 minutes, with a minimum of 200s (unit not stated on the slide) and an end point of 1 to 4 days. | ... with a minimum of 200 seconds (about three minutes) and an end point of 1 to 4 days. | On the slide (IMG_4833) the "200s" marker sits under the Seconds column. |
| `D3-C131` | Google's quality talk said quality is one of the most important ranking signals, although Google uses hundreds of ranking signals. | The same, ending "(the word 'quality' is a repaired speech-to-text reading)". | One recording; the key word is a repaired reading, and the slides IMG_4800 and IMG_4801 do not show it. Hedged like D3-C130. |
| `D3-C585` | Consumers boosted by AI in their purchase decisions were still a small group in October 2026, but the group is growing as more people start using AI. | The same, ending "(the word 'boosted' is an uncertain reading at this point of the recording)". | An uncertain reading in the one recording; the slide IMG_4830 does not show the word. |
| `D3-C644` | A site move can take up to about a year because Google's slowest signal is recalculated only about once a year. | Gary Illyes said a site move can take up to about a year in the worst case, because Google's slowest signal is recalculated only about once a year (some words of this passage are uncertain readings). | One recording, no slide, and several words of the passage are uncertain readings. |
| `D3-C645` | Keep migration redirects in place for at least a year and judge a site move after one to three months, not days: Google said its slowest signal needs about a year to be recalculated. | ... not days: Google's speaker said its slowest signal needs about a year to be recalculated (a partly uncertain passage of the recording), and Google's site move guide says to keep redirects generally at least one year. | Follows the D3-C644 hedge and adds the documented rule. |

**Evidence only:** `D3-C628` and `D3-C629` (the rendering queue clears within weeks, by Google's logs) now also cite the slide IMG_4833, whose Rendering row ends at "days/weeks"; their wording is unchanged.

### What the Deep Dive edition changes, section by section

- Section 04 · What quality means to Google: the stage paragraph on quality as a ranking signal adds "("quality" is a repaired speech-to-text reading)": D3-C131 D3-C130.
- Section 11 · How long Google's processes take: CORRECTION (D3-C631) in the caption of the "Fifteen processes on one time scale" figure, "The meta-annotation minimum reads "200s" with no unit stated" -> "The meta-annotation minimum, "200s" under the slide's Seconds column, is 200 seconds (about three minutes)".
- Corrected claims cited in the guide whose wording there needed no change: D3-C585 (the guide says "a small but growing group" without the word "boosted"), D3-C645 (the guide says only "keep redirects a year"), D3-C628 and D3-C629.
- Corrected claim not cited in the guide: D3-C644.

<p align="center"><img src="../../_system/brand/divider.svg" width="600" alt="Section divider"></p>

## <img src="../../_system/brand/icons/compass.svg" width="24" height="24" alt=""> Bringing a classic edition up to date

`rebuild.bat` never rewrites the classic PDFs. To refresh one on purpose, build it by hand: `python _system/pdf/make_pdf.py day1 deco` (Art Deco) or `python _system/pdf/make_pdf.py day1 modern`. Then run `rebuild.bat` so the web edition copies the new file. Finally, remove that day and edition from this log, or mark it as current. The classic builders and stylesheets still work: see [`_system/pdf/README.md`](../../_system/pdf/README.md). A Deep Dive change that should not reach the classic editions only needs an entry here.

<p align="center"><img src="../../_system/brand/divider.svg" width="600" alt="Section divider"></p>

<p align="center"><sub>← <a href="README.md">Field guides</a> · <a href="../dev/README.md">Developer kit</a> →</sub></p>
