# How I graded 2,228 claims against Google's docs

I spent three days at Search Central Live Deep Dive Europe 2026 in Barcelona, from 30 September to 2 October 2026. The days covered crawling, indexing and serving. I wanted to know which of what I heard is Google's documented position and which was only said on stage, so I turned everything into small statements and checked each one against Google's own documentation. This is how, and where it falls short.

## What I captured

I captured the slides, my own notes and my own recordings of the talks. Recordings shared with me later filled the gaps: a second attendee's recording of most of Day 1 and Day 2, and six audio recordings of Day 1 sessions, which I transcribed on my own computer with a local speech-to-text model, so none of that audio was uploaded anywhere.

I cleaned every transcript against the slides. Misheard words were repaired to the real terms (hreflang, JSON-LD, SpamBrain, Storebot-Google, query fan-out), and jokes, banter and housekeeping were dropped. Every correction was logged, and every paragraph was numbered so a claim can point to the exact passage. Where two recordings disagreed, the claim says so. The photos, recordings and transcripts stay private: the shared knowledge base holds paraphrases, short quotations and links to Google's public documentation only.

## What a claim is

A claim is one statement in my own words, about one thing. It has a permanent ID such as `D1-C054` (Day 1, claim 54), which is never reused or renumbered. It records the session, who is speaking, the evidence (a slide or a numbered transcript paragraph), its topics and a grade, and a quotation of up to 25 words only where the exact wording matters.

There are 2,228 public claims across 62 sessions and 96 topics, checked against 242 sources: 230 Google pages and 12 press reports. Every topic page, map, kit, field guide and the web edition is generated from them.

## The five labels

Every claim says who is speaking:

- **Slide**: shown on screen, by Google or a community speaker (291 claims).
- **Stage**: said on stage, from my notes, a transcript or a recording (1,409).
- **Docs**: Google's own published documentation (269).
- **Press**: a third-party report of what Google or a Googler said (5).
- **Analysis**: my interpretation or advice, never Google's position (254).

The labels keep apart what Google said, what Google wrote and what I think.

## The grades, and how a claim is checked

Only slide and stage claims are graded. For each one, I looked for the Google page that covers the point (Search Central documentation, Search Console Help, Merchant Center Help, Google's blogs), read the live page, and gave the claim one of four grades:

| Grade | Means | Slide and stage claims |
| --- | --- | ---: |
| Confirmed | The documentation states the same thing | 326 |
| Consistent | The documentation supports it without stating it directly | 558 |
| Undocumented | Said or shown at the event, but not in the documentation | 433 |
| n/a | Nothing to verify: a quotation, framing, an agenda fact, an audience question, an opinion | 383 |

A technical fact shown or said by Google is never n/a. The page becomes a source with the date I checked it (2 to 4 October 2026), and the passage often becomes a docs claim of its own, so a reader sees both sides together. Docs and press claims are graded `source`: they are the document.

Of the 1,317 slide and stage claims that could be checked, 884, or 67%, are confirmed or consistent. The other third, 433 claims, is undocumented. For Google's own speakers alone it is 357 of 1,139, about 31%.

Where the event and the documentation pull in different directions, a differences ledger of 20 rows gives both sides and what I would follow.

## What "undocumented" means, and why it matters

Undocumented does not mean wrong. It means that, when I checked, the point was not in Google's documentation. It may be new, an example, a rule of thumb, an internal figure or a speaker's own view. A slide saying that 94% of frequent LLM users are also frequent users of Google Search is a good example: newsworthy, said by Google, and found in none of its documentation.

These claims are the most valuable part of the knowledge base, because you could not have read them before, and the most fragile. So they carry a rule: quote them as "said at Search Central Live", never as Google's documented policy, and never write "Google confirms". The developer kit and the agent pack follow the same rule.

## The build checks

The build checks everything before it writes anything, and stops on an error:

- **Validation.** Unknown or repeated fields, wrong types, bad dates, duplicate IDs, and any topic, kit item or test question that cites a missing claim.
- **Private claims.** A claim marked private never reaches a shared output, and a misspelled private flag is an error.
- **25-word quotations.** A longer quotation stops the build.
- **Proven names only.** A speaker is named only where a title slide, a self-introduction or an on-stage hand-over, matched to the official speaker list, proves it. Otherwise the claim says Google, a community speaker or a speaker. Audience members are never named.
- **The same result every time.** A rebuild without data changes gives byte-identical files, and regression tests check the build, the links and the web edition.

## Testing it on an agent

Much of this will be read by AI agents, so I tested one. An answer key of 66 questions is kept outside the agent pack. A fresh agent that had not seen it answered every question with the command-line query tool alone, and its answers were frozen before scoring. Its mean citation recall was 0.97 on the first 56 questions and 1.00 on the last ten, and it cited no ID that does not exist in the pack: nothing invented, nothing private. Two caveats: the same agent also ticked the content checks, so that part is less independent, and seven of its answers stated a stage-only point without saying that it is not in the documentation.

## The limits

- **One event.** Six sessions have no coverage, others only in part: one attendee's record, filled in with shared recordings.
- **Data through 2 October 2026.** Later announcements are not in it.
- **Documentation changes.** A grade is true of the page on the day I checked it: check the linked page before relying on anything time-sensitive.
- **Speech-to-text is imperfect.** A word that could not be repaired is marked unclear, and no claim rests on it. Where a reading stays uncertain, the claim says so.
- **Paraphrase is interpretation.** A claim is my wording. The quotation, the evidence and the grade let you judge it yourself.

## If you want this for your own material

The method works on any material that should be checked against a source of truth: conference notes, internal guidelines, or a website's pages against Google's documentation. If your team would like it applied to its own material, [Ibram & Dawwa GmbH](https://ibramdawwa.de/contact) is happy to talk.

*Ibrahim Anjro. This write-up is part of the knowledge base's content, under CC BY-NC 4.0 (see `LICENSE-CONTENT.md`).*
