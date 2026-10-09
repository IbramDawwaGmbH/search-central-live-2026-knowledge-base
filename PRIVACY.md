[Knowledge base](README.md) / **Privacy**

# What is private and what is shared

**This knowledge base is built so its shared parts hold paraphrases, short quotations and links to Google's public documentation only: no slide photos, recordings or transcripts.**

<p align="center"><img src="_system/brand/divider.svg" width="600" alt="Section divider"></p>

## <img src="_system/brand/icons/lock.svg" width="24" height="24" alt=""> Never shared, never committed to git

| Folder | Why |
| --- | --- |
| [`00-raw/`](00-raw/README.md) | Slide photos, video clips, raw transcripts, handwritten notes |
| [`10-sources/`](10-sources/README.md) | Cleaned transcripts, slide transcriptions, photo previews, the reconstructed agenda |
| [`70-private/`](70-private/README.md) | Notes about my own sites and employer, and claims marked private |
| `_system/**/_build/` | Temporary build files |

These are listed in `.gitignore`, which also ignores photos, recordings, subtitles and archives anywhere in the folder, and loose photos or text files at the top level. `save-version.bat` checks every new file before committing and stops for anything that looks like a photo, recording, presentation, spreadsheet or transcript.

> [!IMPORTANT]
> Back the private folders up yourself; git does not track them.

## <img src="_system/brand/icons/anchor.svg" width="24" height="24" alt=""> Rules for the shared parts

| Rule | In practice |
| --- | --- |
| **Paraphrase** | A claim is a paraphrase in my words. The `quote` field holds a short direct quotation (at most 25 words) only where the exact wording matters. |
| **Redraw, never photograph** | Short code examples and diagrams redrawn from slides appear in the PDFs as teaching material. No slide photo is ever embedded. |
| **Our own artwork** | The Deep Dive look and the Diver bot are drawn from scratch in code (`_system/ocean_art.py`): no Google logo or mascot, no copy of the event's artwork, no photo of a person. Photos of the event's style stay in `00-raw/` as private reference. |
| **No named bad examples** | Companies shown on stage as examples of broken sites are not named in claims. |
| **Nothing about other attendees** | No names, badges or faces. One Day 2 photo that shows another attendee's badge is on the exclusion list (`EXCLUDED` in `_system/build_kb.py`): it is left out of every output and the build refuses it as evidence. |
| **`private: true`** | A claim that should not be shared gets `private: true`. The build leaves it out of every output and lists it in `70-private/private-claims.md`. A misspelled or repeated `private` key is a build error, so a typo cannot publish a private claim. |
| **My own work stays out** | Nothing about my own sites, clients or employer goes into `20-claims/`. It goes in `70-private/`. |

## <img src="_system/brand/icons/compass.svg" width="24" height="24" alt=""> Personal details that are in the repository on purpose

> [!NOTE]
> - `_system/pdf/config.yaml` holds my WhatsApp number and LinkedIn link, which are printed on the PDFs' contact page, on purpose.
> - `_system/edition.yaml` holds the company, contact, Impressum and privacy-policy links and LinkedIn shown in this community edition, and the address of the live web edition.
> - The commit carries my name and the company address info@ibramdawwa-gmbh.de.

## <img src="_system/brand/icons/bubble.svg" width="24" height="24" alt=""> Private claims

> [!NOTE]
> This community edition holds no private claims. Claims marked `private: true` in the full edition (talk framing, filler and one uncertain reading) were left out of its data files, so the files hold only what the outputs show. The mechanism stays: a claim marked `private: true` never reaches a generated output, and the build lists it in `70-private/`.

<p align="center"><img src="_system/brand/divider.svg" width="600" alt="Section divider"></p>

<p align="center"><sub><a href="README.md">Knowledge base</a> · <a href="CHANGELOG.md">Changelog</a> · <a href="_system/README.md">System</a></sub></p>
