[Knowledge base](README.md) / **Contributing**

# Contributing to the community edition

**Corrections, ideas and tools built on top of this knowledge base are all welcome. Every merged pull request is credited: GitHub lists you among the repository's contributors.**

<p align="center"><img src="_system/brand/divider.svg" width="600" alt="Section divider"></p>

## <img src="_system/brand/icons/compass.svg" width="24" height="24" alt=""> Ways to help

| You want to | Do this |
| --- | --- |
| **Report a wrong claim, grade or link** | Open an [issue](https://github.com/IbramDawwaGmbH/search-central-live-2026-knowledge-base/issues) with the claim ID (such as `D1-C054`), what is wrong and, if you have it, a link to the Google documentation that shows it. |
| **Fix the code, the developer kit or the docs** | Send a pull request. *Making a change* below shows how. |
| **Build a tool on top** | Open an issue first and describe the tool. *Building tools on top* below shows where to start. |
| **Share an idea** | Open an issue. Rough ideas are fine. |

Claims are checked against the slides and recordings, which stay private. That is why a correction to a claim works best as an issue: I check it against the evidence and change the claim myself.

## <img src="_system/brand/icons/bot.svg" width="24" height="24" alt=""> Building tools on top

This is a knowledge base, not an MCP server (yet). It is ready to build on, and tools like these would help the whole community:

- an **MCP server**, so AI assistants can search the claims directly;
- **integrations and plugins** for editors, content systems and SEO tools;
- your own idea: open an issue and describe it.

Start from the agent pack: [`60-outputs/agent-pack/`](60-outputs/agent-pack/AGENTS.md) holds every claim, topic, session, source and link as JSON, and its `AGENTS.md` tells an agent how to use them. [`_system/kb_query.py`](_system/kb_query.py) already searches it and cites a source for every answer, offline and with Python's standard library only.

Open an issue before you start, so we can agree on where the tool lives: in this repository, or in your own with a link from here.

## <img src="_system/brand/icons/code.svg" width="24" height="24" alt=""> Making a change

1. **Change the sources, never the generated folders.** Claims live in [`20-claims/`](20-claims/README.md) (the field rules are in [`_system/schema/claim.md`](_system/schema/claim.md)), the developer kit in [`25-kits/`](25-kits/README.md) and the code in [`_system/`](_system/README.md). `30-topics/`, `40-sessions/`, `50-maps/` and `60-outputs/` are rebuilt from them.
2. **Rebuild:** `python _system/build_kb.py`, then `python _system/site/build_site.py`. You don't need to rebuild the PDFs; I do that before a release.
3. **Run the tests:** `python _system/tests/run_tests.py`.
4. **Run the privacy guard:** `python _system/tools/check_commit.py` lists anything that looks like a photo, recording or transcript before you commit.
5. **Commit the rebuilt files with your change.** No output depends on the clock, so the diff shows exactly what your change did.

You need Python 3.10 or newer and the packages in [`requirements.txt`](requirements.txt). On Windows, `rebuild.bat` runs the whole build; for macOS and Linux, see [the build guide](_system/README.md).

## <img src="_system/brand/icons/anchor.svg" width="24" height="24" alt=""> Rules for every contribution

- **Privacy first.** Follow [`PRIVACY.md`](PRIVACY.md): no slide photos, recordings or transcripts, no names of other attendees and no companies named as bad examples.
- **Paraphrase.** A claim is a paraphrase in your own words. Quote at most 25 words, and only where the exact wording matters.
- **Claim IDs are permanent.** Never reuse or renumber one.
- **The media kit is not part of this edition,** so changes to it can't be taken here.
- **Independent.** This knowledge base is not affiliated with or endorsed by Google, and nothing you add should suggest otherwise.
- **Licence.** Your contribution is published under the same licence as the part it changes; [`LICENSE-CONTENT.md`](LICENSE-CONTENT.md) shows which part has which.
- **Be kind.** Question the claims, not the people.

## <img src="_system/brand/icons/coral.svg" width="24" height="24" alt=""> Talk first

Want to talk before you start, or build something bigger together? Get in touch through [Ibram & Dawwa GmbH](https://ibramdawwa.de/contact) or on [LinkedIn](https://de.linkedin.com/in/ibrahem-angro).
