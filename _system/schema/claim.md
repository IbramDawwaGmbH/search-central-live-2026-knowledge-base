# The claim record (schema v2)

A claim is one statement from the event, small enough to be true or false on its own. Claims live in `20-claims/dayN.yaml`, a YAML list. `python _system/build_kb.py --check` validates everything below without writing a file; the normal build validates first and stops before it deletes or writes anything.

```yaml
- id: D2-C014                 # D<day>-C<3 digits>. Day = the N of dayN.yaml = the day of session s. Never reuse or renumber.
  s: D2-S03                   # session ID from sessions.yaml. D2-S00 = "Day 2, session not recorded".
  label: stage                # slide | stage | docs | press | analysis
  who: Martin Splitt          # slide/stage only: a speaker of the session, audience, or unknown
  ev: T:t03:14                # evidence (see below): string or list
  ver: undocumented           # confirmed | consistent | undocumented | source | n/a
  src: [robots-spec]          # keys from sources.yaml, always a list
  topics: [canonicalization]  # one or more topic IDs from topics.yaml, always a list
  text: "One-sentence paraphrase in plain English."
  quote: "Exact words, at most 25."     # optional, only where the wording itself matters
  quote_checked: true         # optional: the quote was checked against the slide photo or the audio
  rel: [{type: repeats, to: D1-C111}]   # optional links to earlier public claims
  private: true               # optional, YAML boolean. Keeps the claim out of every shared output.
```

Only these 13 keys are allowed. Any other key (for example a misspelled `privat`) is an error, and so is a key written twice in one claim (YAML itself would silently keep the second value, so `private: true, ..., private: false` would publish the claim). A typo can never publish a private claim. Repeated keys are an error in every YAML file of the knowledge base, not only in claims. Every value must have the type shown: `label`, `ver` and the items of `src` and `topics` are single words, and an item listed twice in `src` or `topics` is an error.

## Labels

| Label | Meaning | Who is speaking | `ver` |
| --- | --- | --- | --- |
| `slide` | Shown on screen | Google, or a community speaker | confirmed, consistent, undocumented or n/a |
| `stage` | Said on stage, from notes or a transcript | `who`, or the session speaker(s) | confirmed, consistent, undocumented or n/a |
| `docs` | Google's own published documentation | Google, in writing (publisher of the source) | `source` |
| `press` | A third-party publication reporting what Google or a Googler said (e.g. Search Engine Journal) | The publication | `source` |
| `analysis` | The author's interpretation or advice | Ibrahim Anjro | `n/a` |

## Verification

| Value | Use when | Needs |
| --- | --- | --- |
| `confirmed` | The documentation states the same thing | at least one `src` with `kind: google` |
| `consistent` | The documentation supports it without stating it directly | at least one `src` with `kind: google` |
| `undocumented` | Said or shown at the event, and not in the documentation | a deliberate search of the docs |
| `source` | The claim is the cited document: `docs` (Google sources only) and `press` (at least one `kind: press` source) | `src` |
| `n/a` | Nothing to verify: a quotation, framing, an agenda fact, an audience question, an opinion, analysis | |

A technical fact shown or said by Google is never `n/a`: check it and grade it confirmed, consistent or undocumented. A press article never makes a claim `confirmed` or `consistent`; cite it next to a Google source, or grade the claim `undocumented`.

## Who said it

- `who` is optional on `slide` and `stage` claims and not allowed on the other labels. It must be one of the session's speakers (the `speaker` field of sessions.yaml, a string or a list), `audience` or `unknown`.
- In a `D<day>-S00` session ("session not recorded") there is no speaker list, so `who` may be any name (or `audience` or `unknown`): `who: Gary Illyes` on a point whose session was not noted. That name is exported as `speaker`.
- A `stage` claim in a session that lists more than one speaker must have `who`. Use `unknown` rather than guessing.
- Audience questions: `who: audience`, label `stage` (or `slide` if the question was shown), `ver: n/a`, text starting "An audience member asked...". The answer is its own claim with `rel: [{type: answers, to: <question id>}]`. A question and its premises are never Google's position.

## Links between claims (`rel`)

A list of `{type, to}`. `to` must be an existing public claim. Put the link on the later claim.

| Type | Use when the claim... |
| --- | --- |
| `repeats` | says again what an earlier claim said (another session or day) |
| `extends` | adds detail or scope to an earlier claim |
| `contradicts` | says the opposite of an earlier claim |
| `updates` | replaces an earlier claim with newer information (a changed figure or policy) |
| `answers` | answers an audience question |

The build shows "Repeats D1-C111" on topic and session pages, the reverse ("Repeated by D2-C014") on the earlier claim, every link in `50-maps/across-days.md`, and `relations` / `related_from` in `claims.jsonl`. Add an `analysis` claim only when there is interpretation to add.

## Evidence (`ev`)

A string or a list of strings. Recognised forms (anything else is a warning):

| Form | Example | Points to |
| --- | --- | --- |
| photo stem | `IMG_4669` (several may be comma-separated: `"IMG_4659, IMG_4660"`) | a file of that name, any extension, under `00-raw/dayN/` |
| `notes` | `notes` | the author's notes, `00-raw/dayN/notes.md` |
| `agenda` | `agenda` | the agenda photo |
| `T:<stem>:<paragraph>` | `T:t06:14` | paragraph 14 of the cleaned transcript `10-sources/dayN/clean/t06.md` |
| `T hh:mm:ss[-hh:mm:ss]` | `T 00:14:32-00:15:10` | a timestamped transcript, time from the start of the recording |
| `video:<stem>` | `video:IMG_4718` | a video clip under `00-raw/dayN/` |

A photo on the exclusion list (`EXCLUDED` in `_system/build_kb.py`: a photo showing another attendee's personal data) must never be cited: naming it in `ev` is an error, and so is naming it anywhere in a public claim, a topic, a session, a source or a kit file in `25-kits/`. After writing, the build scans every shared output for it and fails if it finds it. `ingest.py` copies such a photo into `00-raw/` untouched but makes no preview and no index entry for it.

When `00-raw/dayN/` exists on this machine, the build warns about photo stems with no matching file; when `10-sources/dayN/` exists, it warns about `T:` references to a missing cleaned transcript. These are warnings, never errors, because the private folders are absent on clones. Evidence references are exported in `claims.jsonl`; the evidence itself never is.

## Rules

1. One idea per claim. If the sentence needs "and" between two facts, split it.
2. Write `text` so it makes sense with no context, on a single line. Name the thing; avoid "this" and "it". Questions start with "An audience member asked...".
3. Keep speaker opinion and your own opinion apart. Advice goes in an `analysis` claim.
4. A number needs its scope (US only, since launch, last six months) inside the text.
5. With a transcript, put the reference in `ev` (`T:<stem>:<paragraph>`). Add `quote` only when the exact wording itself matters, at most 25 words, and paraphrase everything else in `text`. Quote from the cleaned transcript, faithful to what was said, and set `quote_checked: true` once checked against the audio or the slide.
6. Nothing about your own sites or employer. That belongs in `70-private/`, or in a claim with `private: true`.
7. Companies shown on stage as negative examples are described generically ("a large German banking group"), not named.
8. Never reuse or renumber an ID. To split a claim, keep the old ID for one half and give the other half the next free ID.
9. Quotes are counted with `re.findall(r"[^\W_][\w'’-]*", quote)`: punctuation-only tokens such as a dash do not count.

## Sessions (`20-claims/sessions.yaml`)

`event: {name, city, dates}` and `days: [{day, date, theme, sessions: [...]}]`. A day with no sessions yet has `sessions: []`.

| Key | Rule |
| --- | --- |
| `id` | `D<day>-S<2 digits>`, unique across all days, day digit = the day block. `D<day>-S00` = "session not recorded". |
| `time` | A quoted `"HH:MM"`, or `""`. Unquoted, YAML reads 10:00 as the number 600. |
| `title` | The agenda title. |
| `speaker` | A string or a list of names; `""` when not known. |
| `coverage` | One of `slides`, `notes`, `transcript`, `one-slide`, `video`, `none`, or a list of them. |
| `role` | Optional, printed after the speaker ("Search Advocate"). |
| `kind` | Optional: `talk` (default), `lightning`, `panel`, `qa`, `poster`, `break`. The PDF agenda leaves out `break` sessions and `D<day>-S00`. |
| `note` | Optional, one line. |

## Topics (`20-claims/topics.yaml`) and sources (`20-claims/sources.yaml`)

- `areas: [{id, title, blurb, topics: [{id, title, summary, do?, related?, cites?}]}]`. Area and topic IDs are lowercase kebab-case and unique across the whole file. `cites` lists the claim IDs that back the summary (they must exist and be public). `do`, `related` and `cites` are lists of strings with no item listed twice. A sentence of a summary that rests only on analysis claims starts with "Author's view:".
- `key: {title, url, publisher, checked, kind?}`. `kind` is `google` (default) or `press`. `url` starts with `http://` or `https://`. `checked` is the date the page was last read: a real calendar date written YYYY-MM-DD (`2026-09-31` and a date with a time are errors). Titles match the live page's H1.
- Every claim ID written in claim text, topic summaries and `do` items, `_system/eval/questions.yaml` and the kit files in `25-kits/` must exist and be public. "D1-C010 to D1-C014" counts as the whole range.

## Counting

- "Raised in N sessions" (`event_sessions` in `topics.json`, the mention matrix, the mindmap fill, "raised most often") counts only `slide` and `stage` claims and never counts `D<day>-S00`.
- `event_days` counts the days of every `slide` and `stage` claim, `D<day>-S00` included: the day of a point from an unrecorded session is known.

## Things (`20-claims/entities.yaml`)

The things the event talked about (products, features, crawlers, reports, directives, status codes, standards, metrics, concepts, updates, tools) live in one hand-written file next to the claims. The claim record above does not change: a claim is never edited to name a thing. The build finds each thing in the public claims by its name and spellings, and derives everything else from those matches (`mentions` on `claims.jsonl`, `entities.json`, the cards in `60-outputs/agent-pack/entities/`, `graph.json`, the kit items' `entities`, the "Things" sections, `50-maps/entity-index.md`). The file is optional: without it there are no things.

```yaml
entities:
  - id: google-search-console    # kebab-case, unique across things, topic ids and area ids; never reused
    kind: product                # product | feature | crawler | report | directive | status-code | standard | metric | concept | update | tool
    name: Search Console         # display name; also matched as a plain spelling (see below)
    aliases:                     # optional: other spellings
      - Google Search Console    # plain: case-insensitive
      - {s: GSC, exact: true}    # exact: case-sensitive (acronyms, and words only ever written one way)
    summary: "Google's free tool that reports how a site does in Search."   # one line, plain text
    glossary: Search Console     # optional: the term of 25-kits/content.yaml that defines it, written exactly
    docs: [gsc-help-home]        # optional: sources.yaml keys of the Google pages it is documented in (kind google)
    topics: [search-console-features]   # optional: home topics; the card links to them for the narrative
    rel:                         # optional: relations to other things (`to` is a thing id)
      - {type: part-of, to: google-search}                        # structural: is-a, part-of; no claims needed
      - {type: measured-by, to: crawl-stats, claims: [D1-C140]}   # factual: uses, affects, measured-by, applies-to; claims required
    pin: [D3-C412]               # optional: claims about it that never write one of its spellings
    unpin: [D2-C301]             # optional: matches that are wrong
  - id: crawl-stats
    kind: report
    name: Crawl stats
    aliases:
      - Crawl stats report
      - {s: crawl stats, in: [search-console-features, crawl-budget]}   # scoped: only in claims filed under one of these topics
    summary: The Search Console report of how Google crawls a site.
```

Only the keys shown are allowed, in a thing and in an alias (`s`, `in`, `exact`; `in` and `exact` may be combined). `id`, `kind`, `name` and `summary` are required.

### How a thing is found in a claim

- The claim's `text` and then its `quote` are searched, as exported (one line). The words that matched are kept as `via`, exactly as the claim writes them; a claim mentions a thing once however often it names it.
- A plain spelling matches case-insensitively, after the same folding as the web edition's search (accents dropped, `ß` = `ss` and so on). An `exact` spelling matches case-sensitively. A scoped spelling (`in`) matches only in claims filed under one of its topics.
- The `name` is matched as a plain spelling, unless one of the aliases spells it (ignoring case and accents): then that alias sets how it is matched. So `name: INP` with `aliases: [{s: INP, exact: true}]` matches "INP" only in capitals.
- A spelling matches whole words only: no letter, digit or hyphen may touch it. "noindex" is not found in "noindexing", "Googlebot" not in "Googlebot-Image", and "robots.txt" is matched as written.
- A match that lies inside a longer match of another thing does not count: "Rich Results Test" is a mention of the tool, not of rich results.
- `unpin` removes the match on a claim; `pin` adds a claim whose words never use a spelling (its mention has `field: pin` and no `via`).
- Only public claims are matched. Nothing about a thing is ever matched in a private claim.
- The result is the derived `mentions` field of every claim in `claims.jsonl` (its last key): `[{"entity": <thing id>, "via": <the words as written>, "field": "text" | "quote" | "pin"}]`, sorted by thing id, `[]` when none, and `via` null exactly for a pin. Like `used_by`, it is never written by hand.

### What the build checks (errors stop the build; nothing is written)

- `id` kebab-case and unique, and not a topic or area id; `kind` in the list; `name` and `summary` non-empty; no unknown key; no key twice in one entry.
- No spelling (name or alias, after folding) belongs to two things. One thing may list a spelling in two modes, such as `{s: Allow, exact: true}` everywhere and `{s: allow, in: [robots-txt]}` in its topics; the same spelling twice in one mode is a warning. A spelling under 3 characters needs `exact: true`.
- **Stop list.** A plain spelling that is one of the 200 most frequent words of the public claims ("product", "crawl", "googlebot", "hreflang" ...) is refused unless it is scoped (`in`) or `exact`. `python _system/build_kb.py --check --stoplist` prints the list.
- `glossary` is a term of `25-kits/content.yaml` (one term may define several things: *nosnippet and data-nosnippet*); `docs` are `sources.yaml` keys of Google pages; `topics` and every `in` are topic ids; `rel.to` is another thing.
- `rel` types: `is-a`, `part-of` (structural); `uses`, `affects`, `measured-by`, `applies-to` (factual: `claims` is required, and every claim listed must exist, be public and mention **both** things, by spelling, scope or pin). `documented-in` is written as `docs`, never as `rel`.
- `pin` and `unpin` list existing public claims; a claim cannot be in both. A private claim anywhere in the file is an error.
- The excluded photos and the names of people (the speakers of `sessions.yaml`) must not appear in a thing: things are never people.
- Warnings (the build still runs): a thing no public claim mentions; a `pin` the claim did not need; an `unpin` that changes nothing (for example a match inside a longer match of another thing, which never counts anyway).

### Reviewing the matches

The build writes `50-maps/entity-index.md`: every thing with its counts, every spelling with the number of claims it matched, a fixed sample of 100 mentions (picked by a hash of claim id and thing id, so every build picks the same) and every mention with the words that matched. Fewer than 5 wrong mentions in the sample is the bar. After a rebuild, `git diff 50-maps/entity-index.md` shows exactly which mentions came and went, and the build prints a note when a spelling newly matches more than 20 claims. A wrong mention: make the spelling a phrase, scope it, or `unpin` the claim. A missed one: add a spelling or `pin` the claim.
