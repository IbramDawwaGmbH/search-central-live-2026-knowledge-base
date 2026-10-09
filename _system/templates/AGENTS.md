# Instructions for AI agents using this knowledge base

This folder is a knowledge base built from Search Central Live Deep Dive Europe 2026 (Barcelona, 30 September to 2 October 2026), written and verified by Ibrahim Anjro. It is an independent attendee resource, not an official Google publication. The first lines of `INDEX.md` give its version and the last day it covers ("data through").

<!-- edition: community -->
**Community edition.** This pack holds everything the knowledge base has except the full media kit: every public claim, topic, session, source and thing, the developer kit, the differences ledger and the graph. `content-library.json` keeps the wording rules, the glossary and a short preview of the media kit (three facts, two myths, one story angle and two quotes); the rest of the media kit, the numbers registry and the question bank are not part of this edition. Every answer can still be built from the claims: cite them as below.

<!-- edition: end -->
## What is here

| File | Use it for |
| --- | --- |
| `INDEX.md` | Start here: version, data-through date, files, sessions with no coverage, every topic with its summary. |
| `topics/<topic-id>.md` | The answer on one topic: summary, actions, where it was discussed per day, the claims behind it, sources. |
| `sessions/<session-id>-*.md` | What was captured in one session, in order, with audience questions and their answers together. |
| `claims.jsonl` | Every claim as one JSON object per line. Best for search, filtering and exact wording. |
| `claims.schema.json` | JSON Schema (2020-12) for one line of `claims.jsonl`. |
| `topics.json` | Areas and topics as data: summary, the claims it is based on (`cites`), actions, related topics, claim ids, sessions and days. |
| `sessions.json` | Days and sessions as data: time, speakers, role, kind, coverage, note, claim count, topics. |
| `sources.json` | Every cited document: title, URL, publisher, kind (`google` or `press`) and the date it was checked. |
| `dev-requirements.json` | The developer kit: requirements for SEO-friendly sites by area (level, why, how, test, status), code snippets, and the claims and Google pages behind each requirement. |
<!-- edition: full -->
| `content-library.json` | The content kit: wording rules, facts, myths, story angles, quotes and glossary, with the claim texts, labels, verification, credit lines and source URLs resolved. |
<!-- edition: community -->
| `content-library.json` | The open part of the content kit: the wording rules, the glossary and a short preview of the media kit (facts, myths, a story angle and quotes), with the claim texts, labels, verification, credit lines and source URLs resolved. Its `edition` is `community` and its `note` says what is left out. |
<!-- edition: end -->
| `graph.json` | Every link that exists in this pack as one graph: `nodes` and `edges` (see "Links and the graph"). Walk it instead of scanning `claims.jsonl`. |
| `links.json` | The same links as lookup tables: what rests on each claim, the kit items per topic, the claims per source by grade, the spellings of glossary terms and things, and the speaker each claim is proven to be by. |
| `entities.json` | The things the event talked about (products, features, crawlers, reports, directives, status codes, standards, metrics, concepts, updates, tools): one card each with everything linked to it (see "Things"). |
| `entities/<id>.md` | The same cards as short Markdown pages. |
| `differences.json` | The differences ledger: where what was said or shown at the event differs from Google's documentation, with the claims on both sides and what to follow (see "Ledgers"). |
<!-- edition: full -->
| `numbers.json` | The numbers registry: every stat fact of the content kit with the figures it states, its scoped wording, status, credit and claims, and the claims with a figure no fact cites yet. |
| `question-bank.json` | The question bank: the audience questions with the answers given, and for each thing "What did Google say about it?" with its top documented and event-only claims. |
<!-- edition: end -->

## How to answer from it

If you can run commands in the knowledge base's folder (a shell agent), ask it with `python _system/kb_query.py` first: one command returns the claims that answer a question, each with its citation (see "Ask it from the command line"). The steps below are the same walk by hand.

1. Find the topic in `INDEX.md`, then read its page in `topics/`. For a question about one thing (Googlebot, the 429 status code, X-Robots-Tag, Search Console), open its card first: `entities/<id>.md` or `entities.json` (the list is under "Things" in `INDEX.md`). For precise wording, a number, a speaker or a day, search `claims.jsonl`.
2. Cite the claim ID (for example `D1-C094`) for every factual statement you take from here. A topic summary is backed by the IDs listed after "Based on:"; cite those, not the summary.
3. Sentences that start with "Author's view:" and every `analysis` claim are the author's interpretation. Never attribute them to Google.
4. If the knowledge base does not cover a question, say so. Check "Sessions with no coverage" in `INDEX.md` before saying what was or was not said in a session. Do not fill a gap from general knowledge without marking it as outside this base.
5. Documentation changes. Each source carries a `checked` date. For anything time-sensitive, tell the user to re-check the linked page.

## Who is speaking: the label

| `label` | Meaning | How to present it |
| --- | --- | --- |
| `slide` | Shown on screen at the event | "Shown on a slide at Search Central Live" (by Google, or by a community speaker in a lightning session) |
| `stage` | Said on stage, from the author's notes or a transcript | "Said on stage by", then the speaker's name |
| `docs` | Google's own published documentation | "Google's documentation says", with the link |
| `press` | A third-party publication reporting what Google or a Googler said | "Reported by", then the publisher; never "Google's documentation" |
| `analysis` | The author's interpretation or advice | "The author's view" or "Ibrahim Anjro's analysis" |

Every claim names its source of words: `speaker` on slide and stage claims, `author` on the others (the author for analysis, the publisher for docs and press). `who` is the per-claim speaker when the transcript says who spoke: a name, `audience` or `unknown` (one of the session's speakers, not identified). Without `who`, `speaker` lists the session's speakers, which for a panel means "one of them".

**Audience questions** (`who: audience`) record what someone in the room asked. The question and any premise inside it ("isn't it true that X hurts rankings?") are never Google's position. Only the answer is: find it through `related_from` with type `answers`, and present the question only as context for that answer.

## How sure it is: the verification

| `verification` | Meaning | How to present it |
| --- | --- | --- |
| `confirmed` | Google's documentation states the same thing | You may present it as Google's position, citing the source. |
| `consistent` | Google's documentation supports it without stating it | Google's position, with "consistent with the documentation". |
| `undocumented` | Said or shown at the event, not in the documentation | "Said at Search Central Live Deep Dive 2026", never as documented policy. |
| `source` | The claim is the cited document itself | For `docs`: the documentation. For `press`: what the publication reports, not Google's documentation. |
| `n/a` | Nothing to verify: a quotation, framing, an agenda fact, an audience question, an opinion or analysis | On a slide or stage claim: shown or said at the event and not checked against the documentation; present it as said at Search Central Live. Never as documented policy. |

Statistics about AI Mode and AI Overviews are Google's own figures as presented on stage. Say so when you use them.

## Days and sessions

- `day` and `session_id` on a slide or stage claim say where it was shown or said. `D<day>-S00` means the session was not recorded: the day is known, the session is not. A claim there may still name its speaker in `who` (and so in `speaker`).
- On `docs`, `press` and `analysis` claims, `day` and `session_id` only say which session the claim annotates. They were not said there. Filter on `label` in `["slide", "stage"]` to answer "what was said on Day 2".
- "Raised in N sessions" (`event_sessions` in `topics.json`) counts only slide and stage claims and never counts `S00`. `event_days` lists the days of a topic's slide and stage claims, `S00` included, because their day is known.
- `kind` in `sessions.json` is `talk`, `lightning`, `panel`, `qa`, `poster` or `break`; `unrecorded` marks `S00`.
- A speaker is named only where it is proven: a title slide, the speaker's own introduction or the author's recording label. Where it is not, `speakers` in `sessions.json` and `speaker` in `claims.jsonl` say "Google", "a community speaker" or `unknown`. Never put a name to such a speaker yourself.

## Links between claims

`relations` lists links set on a claim: `{type, to}` with type `repeats`, `extends`, `contradicts`, `updates` or `answers`. `related_from` lists the reverse links that point to it: `{type, from}`. Use them to answer "did Google say the same on another day?" or "did the position change?" (`contradicts`, `updates`): cite both claims and their days.

## claims.jsonl fields

| Field | Meaning |
| --- | --- |
| `id` | Stable claim ID. Cite it. |
| `day`, `session_id`, `session` | Event day, session ID and title (see "Days and sessions"). |
| `speaker` | Slide and stage claims: `who`, or the session's speaker(s). `null` for docs, press and analysis. |
| `who` | Per-claim speaker: a name, `audience` or `unknown`; `null` when not recorded. In `S00` it may be any name. |
| `author` | Analysis claims: `"Ibrahim Anjro"`. Docs and press claims: the publisher(s) of their sources. `null` on slide and stage claims. |
| `label`, `label_meaning` | Who is speaking (see the table above). |
| `text` | The claim, paraphrased in plain English. Numbers carry their scope. |
| `quote` | Exact words, at most 25, only where the wording matters; `""` when there is none. Quote it exactly or not at all. |
| `quote_checked` | `true` once the quote was checked against the slide photo or the audio. Prefer checked quotes when quoting. |
| `verification` | How the claim stands against Google's documentation (see the table above). |
| `topics` | Topic IDs (see `topics.json`). |
| `sources` | Cited documents: `key`, `title`, `url`, `publisher`, `kind` (`google` or `press`), `checked` date. |
| `evidence` | Private evidence references (photo file stems, `notes`, `T:<transcript>:<paragraph>`, timestamps). They tell a reviewer where to look; the evidence itself is not in this pack. |
| `relations`, `related_from` | Links to and from other claims (see above). |
| `used_by` | Derived by the build: the kit items that rest on this claim, as graph ids (`req:DEV-SRV-01`, `fact:F-012`, `myth:M-003`, `quote:Q-088`, `angle:A-007`, `term:<glossary term id>`). `[]` when none. |
| `mentions` | Derived by the build: the things this claim names, `{entity, via, field}`, sorted by `entity` (an id of `entities.json`). `via` is the words as written in the claim's `text` or `quote` (`field`); `field: "pin"` with `via: null` means the claim was linked to the thing by hand because it names it without one of its spellings. `[]` when none. |

## How to cite

Put the claim ID in square brackets after the statement it supports, followed by the `label` and who is speaking, all taken from `claims.jsonl`:

- Slide and stage claims: `[id, label, speaker, Day N]`, with `day` from the claim. For `speaker`, name a person only where `links.json` proves it (`speakers.claims.<id>.name`); otherwise write the claim's credit group: Google, a community speaker, a speaker or an audience member. The `speaker` field of `claims.jsonl` can hold the session's speaker for a claim no one is proven to have said, so do not copy it from there. This is the form the `cite` strings of the cards and of `kb_query.py` use.
  - Googlebot does not process the non-standard crawl-delay rule, so the rule saves no crawl budget [D1-C108, slide, Google, Day 1].
  - The notranslate robots rule tells Google not to offer a translation of the page in search results [D2-C093, stage, John Mueller, Day 2].
- Docs and press claims: `[id, label, author, url]`, with the `url` of the source in `sources` that backs the statement. Leave out the day: it only says which session the claim annotates.
  - Google's documentation says Googlebot supports only the user-agent, allow, disallow and sitemap fields in robots.txt, so crawl-delay is ignored [D1-C084, docs, Google, https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec].
- Analysis claims: `[id, analysis, Ibrahim Anjro]`, presented as the author's view, never as Google's.
  - In the author's view, slow indexing on a smaller site is almost always a demand problem, meaning quality, not a capacity problem [D1-C098, analysis, Ibrahim Anjro].

When several claims back one statement, separate them with semicolons inside one pair of brackets: Googlebot ignores crawl-delay [D1-C108, slide, Google, Day 1; D1-C084, docs, Google, https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec]. Quote only from `quote`, exactly, in quotation marks.

## Developer and content kits

`dev-requirements.json` and `content-library.json` turn the claims into work for two teams. They are built from `25-kits/` and use only public claims; each item lists its claims with their text, label, verification, credit line and sources already resolved.

- **Developers** (`dev-requirements.json`): `areas[].requirements[]` with `level` (`MUST`, `SHOULD`, `MAY`, or `AVOID`, which means must not), `why`, `how`, `test`, `status`, `snippet` (a key of `snippets[]`, or `null`), `claims` and `docs` (the Google pages). Use `test` as the acceptance criterion when you write a ticket.
<!-- edition: full -->
- **Content teams** (`content-library.json`): `wording_rules` (follow them), `facts` (`use`: `stat`, `headline` or `context`), `myths`, `quotes`, `angles` (each point has its own `status`) and `glossary`.
<!-- edition: community -->
- **Content teams** (`content-library.json`): `wording_rules` (follow them) and `glossary`, both complete, and a short preview of the media kit in `facts` (`use`: `stat`, `headline` or `context`), `myths`, `quotes` and `angles` (each point has its own `status`). The full media kit is not part of this community edition, so do not present the preview as the whole kit: for anything beyond it, answer from the claims and cite them.
<!-- edition: end -->
- `status: documented` means a cited Google page states or supports the item: you may present it as Google's position. `status: event-only` means it was said or shown at the event and is not in Google's documentation: write "said at Search Central Live", never "Google confirms". An angle point with `status: mixed` (Partly documented) rests on documented claims and on event claims the documentation does not back: check each claim and present the undocumented part as said at Search Central Live. Follow an angle's `caution` where there is one.
- Credit what was said with the claim's `credit` ("Google at Search Central Live Deep Dive Europe 2026 (Day 2)", "a community speaker at ..."). A credit of "a speaker at ..." means the pack does not record whether a Googler or a community speaker said it: write "said at the event", never "Google said". Name a person only where `speaker` is not `null`: it is set only when the speaker is proven. Who said it matters less than what was said and how well it is documented.

## Links and the graph

`graph.json` puts the links that already exist in this pack into one walkable graph. Nothing in it is new information: every edge comes from a claim's own fields, `topics.json`, `sessions.json` or a kit item's cited claims and pages.

- `nodes`: `{id, kind, name, url}`. An id is `<kind>:<id>`: `claim:D1-C108`, `topic:robots-txt`, `area:crawling`, `session:D1-S07`, `day:1`, `source:<key of sources.json>`, `req:DEV-SRV-01`, `fact:F-012`, `myth:M-003`, `quote:Q-088`, `angle:A-007`, `term:<id of a glossary term in content-library.json>`. `url` is the pack file that holds the node (a source: its own URL). A claim node also carries `label`, `ver` and `day`.
- `edges`: `{from, to, type}`. `about` claim → topic; `in` claim → session and topic → area; `on` session → day; `cites` claim → source and topic → claim (the claims its summary is based on); `related` topic → topic; `repeats`, `extends`, `contradicts`, `updates`, `answers` claim → claim (from the later claim, as in `relations`); `rests-on` kit item → claim; `documented-in` requirement → source. `edge_types` lists each type with its ends and count.
- Typical walks: "which requirements rest on what was said about robots.txt": topic → the claims `about` it → the items with `rests-on` edges to those claims (or `topic_items` in `links.json`). "What backs this source": `links.json` `sources.<key>.claims`, grouped by verification.

- Things add `ent:<id>` nodes (with `entity_kind`) and these edges: `mentions` claim → thing (with `via` and `field`, or `field: "pin"`); `about` kit item → thing (`count`: how many of its claims mention it; `own`: its own words name it); `defines` glossary term → thing; `features` topic → thing (`count`); `co-mentioned` thing → thing (`count` and the `claims` that mention both; written once, from the smaller id); `documented-in` thing → source; and the relations written by hand: `is-a` and `part-of` (structural), `uses`, `affects`, `measured-by` and `applies-to` (factual: each carries the `claims` that say it).
- More walks: "which developer requirements rest on X-Robots-Tag": the thing's card (`items`), or the claims with a `mentions` edge to `ent:<id>`, then the `rests-on` edges that end at them. "What is Googlebot connected to": its card's `co_mentioned` and `rel`, or its `co-mentioned` edges.

A node or an edge is a map, never a source. Cite the claim ids behind it, as "How to cite" says, and take the label, verification and speaker from `claims.jsonl`.

`links.json` also holds `aliases` (the spellings of each glossary term, keyed in lower case with accents and punctuation removed) and `speakers`: for each slide and stage claim, the credit group (`google`, `community`, `unattributed`, `audience`) and a `name` only where the speaker is proven. To answer "what did a named person say", use only claims whose `speakers.claims.<id>.name` is that person; never infer a name from `speaker` alone.

## Things

A thing is something the event talked about: a product (Search Console), a feature (AI Mode), a crawler (Googlebot), a report, a directive (noindex), a status code (429), a standard, a metric, a concept, an update or a tool. The list is hand-written in the knowledge base; the build finds each thing in the public claims by its name and spellings and derives everything else from those matches. People are never things: to answer "what did a named person say", use the speaker rule under "Links and the graph".

- `entities.json`: `entities[]`, each with `id`, `kind`, `name`, `aliases` (other spellings), `match` (every spelling it is found by: `s`, `exact` for a case-sensitive match, `in` for the topics it is limited to, and `claims` it matched), `summary`, `glossary` (the glossary term id that defines it) and `definition`, `docs` (keys of `sources.json`: Google pages it is documented in), `topics` (its home topics: read them for the narrative), `rel` and `rel_from` (relations to and from other things; a factual one lists its `claims`), `claims` (every public claim that mentions it), `tally` (those claims by label, and the slide and stage ones by verification), `cite` (the citation of each claim), `co_mentioned` (the things named in the same claims, with `count` and `claims`), `featured_in` (topics whose claims mention it, with `count`) and `items` (the kit items about it: `id`, `count` of their claims that mention it, `own` when their own words name it). `topic_entities` and `session_entities` list the things of each topic and session, most mentioned first.
- `entities/<id>.md`: the same card in Markdown: what it is, the Google pages and docs claims, what was shown or said at the event (not in Google's documentation first), press and analysis, the requirements and content items about it, and the things connected to it.
- Kit items in `dev-requirements.json` and `content-library.json` carry `entities`: `[{id, count, own}]`, the things the item is about (its own words name it, or at least two of its claims do; half of them when it rests on fewer than four). A glossary term also carries `defines`: the things it defines (`[]` when none).
- A card, a count and a relation are a map, not a source. Cite the claim ids they list. The `cite` strings follow "How to cite", with one difference that keeps attribution safe: a slide or stage claim names a person only where the speaker is proven (the `speaker` of `content-library.json`); otherwise it says Google, a community speaker, a speaker or an audience member.
- A mention means the claim's words name the thing, not that the claim is mainly about it. Read the claim before you rely on it.

<!-- edition: full -->
## Ledgers: differences, numbers, questions

Three files gather what an answer most often needs to get right. Every claim in them is a full claim record (text, label, verification, credit, sources) with its `cite`, and every claim id is public. They are built from the kits and the claims; nothing in them is new information.
<!-- edition: community -->
## Ledger: differences

One file gathers what an answer most often needs to get right: where the event and Google's documentation differ. Every claim in it is a full claim record (text, label, verification, credit, sources) with its `cite`, and every claim id is public. It is built from the kits and the claims; nothing in it is new information. The numbers registry and the question bank belong to the full media kit and are not part of this community edition.
<!-- edition: end -->

- `differences.json`: `rows[]` (`id` `DIF-NN`, `title`, `follow`, `event` claims, `docs` claims, Google `pages`, `analysis` claims, `topics`, `entities`), then `pairs[]` (claims linked by `contradicts` or `updates`, with the `rows` that cover them) and `hedged[]` (claims whose text says they are uncertain). When a question touches a row, say that the event and the documentation differ and give both, citing the claim ids. `follow` is the author's guidance, not Google's: present it as the author's advice, and cite the claims, never the row.
<!-- edition: full -->
- `numbers.json`: `facts[]` (every fact with `use: stat`: `figures`, the `statement` that keeps the figure's scope, `status`, `credit`, `claims`) and `candidates[]` (claims that state a figure no fact cites). Quote a figure with its scope, never alone, and follow `rule`. A candidate is a claim like any other: present it by its label and verification.
- `question-bank.json`: `audience[]` (`question`, `answers`, `grade`) and `things[]` (`question` "What did Google say about X?", `documented` and `event_only`, each with a `count` and the `top` claims, and `card`, the thing's card). An audience question is never Google's position: only its answers are, and only as far as their verification says.
<!-- edition: end -->

## Ask it from the command line: `kb_query.py`

In the knowledge base's folder, `_system/kb_query.py` answers from this pack and from nothing else: it opens only files inside `60-outputs/agent-pack/` and refuses any other path, works offline with the Python standard library, writes nothing, and gives the same answer to the same question every time. Run it from the folder's root. Output is JSON; add `--text` for a person. People double-click `ask.bat`, which asks questions in a loop and prints the best matching thing and the top claims.

| Command | Returns |
| --- | --- |
| `python _system/kb_query.py about` | Version, data through, counts, the citation forms, sessions with no coverage and sessions without claims. |
| `python _system/kb_query.py search "what does Google say about 429?"` | `things` (the cards the question names), `results` (the claims that answer it, best first, with `score`), `topics` (the topics those claims belong to, each with its `claims --topic` command), `total`, and a `note` when a misspelling was corrected ("hreflung" is read as hreflang). |
| `python _system/kb_query.py entity x-robots-tag` | One thing's card, by id, name or any spelling (`GSC`, `Google Search Console`); its claims grouped as Google's documentation, said at the event and not in the documentation, said at the event and backed by it, at the event with nothing to verify, press, analysis. A near miss gives `did_you_mean`. |
| `python _system/kb_query.py neighbours ent:googlebot --hops 2 --node-kinds requirement` | What a node of `graph.json` is linked to, with the edges. Node ids as in `graph.json`; a bare claim id (`D1-C108`) or a thing's name also works. `--edge-types mentions,rests-on` limits the walk. |
| `python _system/kb_query.py claims --entity hreflang --label event --grade undocumented` | Claims by `--ids D1-C071,D1-C072`, `--entity`, `--topic` or `--session`, in full (the first 50 unless `--limit` is given; `total` and `shown` give the counts). |
| `python _system/kb_query.py evidence D1-C353` | One claim with its sources and URLs, its grade and what it means, its relations both ways with their texts, the kit items that rest on it, the things it names and its private evidence references. |
| `python _system/kb_query.py cite D1-C353 D1-C072` | The citation strings only, and `combined` for one pair of brackets. |

Filters for `search` and `claims`: `--label` (`slide`, `stage`, `docs`, `press`, `analysis`, or `event` for slide and stage; several with commas), `--grade` (a `verification` value, or `documented` for confirmed, consistent and docs), `--day`, `--limit`, and `--speaker`, which takes only a proven name (the names in `links.json` `speakers.names`) or `google`, `community`, `audience`. A name that is not proven is refused, so the filter never puts a name to an unproven speaker. `search --kind requirement` (or `entity`, `topic`, `fact`, `myth`, `quote`, `angle`, `term`, `all`) searches the maps instead of the claims; each map result lists the claim ids to cite.
<!-- edition: community -->

In this community edition, `search --kind fact`, `myth`, `quote` and `angle` (and `all`) search the media kit preview only, and the result carries an `edition_note` that says so; `neighbours` on a fact, myth, quote or angle outside the preview answers that it is not part of this edition. `about` gives the `edition` too.
<!-- edition: end -->

The top results of one `search` are a start, not the whole answer. For a question with several parts, run one `search` per part, then read the first topic in `topics` in full with `claims --topic <id> --limit 200`: `claims` shows the first 50 claims unless `--limit` is given, and a `total` larger than `shown` means some were left out. On the eval questions, the top 12 results alone held about 63% of the claims a complete answer cites, and the top 12 plus the first topic held about 81%. `evidence <claim-id>` names the claim's session; `claims --session <id>` lists that talk in order, which finds the claim that qualifies or answers the one you have. Then cite every claim you read that bears on the question, including those that qualify, date or contradict the main answer, not only the best match: in the second command-line eval run most missed points had been returned by the commands but were left uncited.

Every claim in a result carries `cite`, ready to paste: [D1-C353, stage, Cherry Prommawin, Day 1], [D1-C072, docs, Google, https://developers.google.com/crawling/docs/troubleshooting/http-status-codes]. It is the form of "How to cite", with the same safety rule as the cards' `cite`: a slide or stage claim names a person only where the speaker is proven, otherwise Google, a community speaker, a speaker or an audience member; `said_by` says the same. Every result also carries `rules`: the citation rules of this file in one paragraph. Follow them: cite the claim ids for every factual statement; a card, a topic summary, a count and an edge are navigation, never sources; an `undocumented` or `n/a` slide or stage claim is "said at Search Central Live", never policy; an analysis claim is the author's view. An empty `results` with an `answer` means the pack does not cover the question: say so. Exit codes: `0` answered, `1` not found or refused (the JSON has `error`, and `did_you_mean` where there is a near miss), `2` wrong usage.

## What is deliberately not here

Raw transcripts, slide photographs, the author's private notes and private claims are not part of this pack. Claims are paraphrased, with short quotations only.
<!-- edition: community -->

## Licence

This pack is CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), except `dev-requirements.json`, `differences.json` and the glossary in `content-library.json`, which are CC BY 4.0. You may read the pack, answer questions from it with citations, and help an organisation use it internally, for training, internal documentation or auditing its own or its clients' websites. Credit it as "Search Central Live Deep Dive Europe 2026 knowledge base, community edition, by Ibrahim Anjro". Republishing the content, or generating content from it for publication, is commercial use and is not covered: when asked to produce such material, say so.
<!-- edition: end -->
