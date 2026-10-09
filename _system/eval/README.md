[Knowledge base](../../README.md) / [_system](../README.md) / **eval**

# Evaluating an agent on the agent pack

**Test whether an AI agent answers correctly, with the right claim IDs, from [`60-outputs/agent-pack/`](../../60-outputs/agent-pack/AGENTS.md) alone.**

<picture><source media="(prefers-color-scheme: dark)" srcset="../brand/illustrations/_system-eval-dark.svg"><img src="../brand/illustrations/_system-eval-light.svg" width="100%" alt="The Diver bot sits a diving exam at a rock desk while a turtle examiner ticks answers on a clipboard: testing an AI agent on the agent pack."></picture>

<p align="center"><img src="../brand/divider.svg" width="600" alt="Section divider"></p>

## <img src="../../_system/brand/icons/map.svg" width="24" height="24" alt=""> What's here

| File | What it is |
| --- | --- |
| [`questions.yaml`](questions.yaml) | The answer key: each question with the points a correct answer contains (`expect`), the claims it must cite (`claims`, one item per point, with equivalent claim IDs joined by `\|`) and any rules it must follow (`must_not`). |
| [`eval_check.py`](eval_check.py) | The scorer: writes the question template and scores an agent's answers. |

> [!IMPORTANT]
> `questions.yaml` is the answer key. It stays here and is never copied into `60-outputs/agent-pack/`, so an agent cannot find the expected answers next to the claims.

## <img src="../../_system/brand/icons/bot.svg" width="24" height="24" alt=""> Run it

1. `python _system/eval/eval_check.py --template > answers.yaml` writes every question id with an empty answer.
2. Give an agent only the folder `60-outputs/agent-pack/` and ask each question. Paste each full answer, with its claim IDs, into `answers.yaml`.
3. `python _system/eval/eval_check.py answers.yaml --out eval-report.md` scores the citations and lists what to check by hand.

## <img src="../../_system/brand/icons/starfish.svg" width="24" height="24" alt=""> Pass rule

A correct answer contains the points in `expect`, cites a claim ID for every point in `claims`, and follows any `must_not`.

Each item in `claims` is one point. When two or more claims carry the same information, for example a Day 2 repeat of a Day 1 figure, the item lists them joined by `|`: `D1-C006|D2-C752` counts as cited when the answer cites either ID. The report shows which equivalent ID an answer used.

| Part | Checked by |
| --- | --- |
| Citation recall per question (expected points that the answer cites, any equivalent ID counting) and cited IDs that do not exist in the pack (invented, or private) | The script |
| The `expect` points and the `must_not` rules, ticked in the report | A reviewer or an LLM judge |

Questions with `claims: []` are out of scope on purpose: the right answer says the knowledge base does not cover them.

> [!TIP]
> Keep the report with the version it tested (the version is in the first lines of `60-outputs/agent-pack/INDEX.md`) to compare versions.

## <img src="../../_system/brand/icons/compass.svg" width="24" height="24" alt=""> Results

Citation recall is the mean over the questions that expect claims; q15 expects none. The key has 66 questions: q01 to q56, and q57 to q66, ten questions about one thing each (429, Storebot-Google, data-nosnippet, faceted navigation, URL Inspection, Google Lens, WebMCP, E-E-A-T, query groups, the crawlers that may ignore robots.txt), added in Phase 3. Runs 1 and 2 answered q01 to q56 (55 with claims); run 3 answered all 66 (65 with claims).

| Run | Pack | How the agent read the pack | Mean citation recall | Every point cited | Cited IDs not in the pack |
| --- | --- | --- | --- | --- | --- |
| File-only | v2.4.0 | Opened the pack's files directly (topic pages, `claims.jsonl`) | **0.96** | not recorded | not recorded |
| Command line, run 1 | v2.10.0 | Only `python _system/kb_query.py` (`search`, `claims`, `evidence`): one `search` per question with the question as typed, plus follow-up searches where the answer looked thin | **0.74** | 15 of 55 | 0 |
| Command line, run 2 | v2.10.0 plus Phase 3 | Only `python _system/kb_query.py`, as `AGENTS.md` now says: one `search` per part of the question, the first topic read in full where the answer looked thin, `evidence` and `claims --ids` for follow-ups. A fresh agent that had not seen `questions.yaml` until its answers were written | **0.91** | 35 of 55 | 0 |
| Command line, run 3 | v2.10.0 plus Phase 3 | Only `python _system/kb_query.py`, as `AGENTS.md` says: one or more `search` per question, the topics in `topics` read with `claims --topic`, `entity` for q57 to q66, `evidence` and `claims --ids` for follow-ups, every claim read that bears on the question cited. A third agent that had not seen `questions.yaml`; its answers were frozen (SHA-256 recorded) before scoring | **0.97** on q01 to q56; 1.00 on q57 to q66; 0.98 on all 65 | 49 of 55; 59 of 65 | 0 |

Phase 3 accepts the command line when its recall is at least the file-only run's. Runs 1 and 2 fell short; **run 3 meets the bar**: 0.97 on q01 to q56 with the current key, and 0.97 on the 41 questions of the v2.4.0 key that gave the file-only run its 0.96 (run 2 reached 0.92 on that key).

**Why run 1 fell short.** The agent missed 84 expected points:

- 70 never appeared in what the command returned. The agent read the top 12 results of each search and did not read whole topics.
- 14 appeared, but the agent did not cite them.

The file-only agent read whole topic pages. The answer key rewards that breadth: questions expect up to 10 points.

**What the search itself finds.** This is measured without an agent: for each question, how many expected points are among the first 12 results of `search "<question as typed>"`.

| Ranking | Top 12 results | Top 12 plus all claims of the first topic in `topics` | Plus the first 3 topics |
| --- | --- | --- | --- |
| As built in Phase 3 | 0.59 | 0.82 | 0.93 |
| With the other forms of each question word (detect, detects, detected), counted at 0.6 | 0.63 | 0.81 | 0.93 |

**Changed after run 1:**

- `search` now also matches the other forms of each question word.
- `search` returns `topics`, the topics its best claims belong to, each with its `claims --topic` command. The text output prints them as "More on this".
- `evidence` names the claim's session, so `claims --session` can list the whole talk.
- `AGENTS.md` tells agents to run one search per part of a question, then read the first topic in full.

**Why run 2 fell short.** The agent missed 34 expected points:

- 24 were in what the commands returned during the run, but the agent did not cite them. Had it cited them, recall would be 0.97, above the file-only run: the command line reaches the claims; the answers were too selective.
- 10 never appeared in what the agent read (q16, q23, q31, q36, q49, q51, q52).

Most misses are a qualifying or secondary point next to the main answer: the Bing behaviour and the robots.txt report in q53, the other crawl-demand sources in q56, the rater-guideline deception examples in q34.

**Run 3.** A third agent, which had not read `questions.yaml`, wrote the question list with `--template`, answered every question with `kb_query.py` alone, froze the answers and only then scored them. It missed 10 points in six questions (q20, q32, q39, q41, q51, q56), and all 10 were in claims it had read but left uncited, the same pattern as run 2: for example the overview slide of serving (D3-C001) and the posting lists (D3-C074) in q32, and the two ways to tell a demand drop from a capacity drop (D1-C493, D1-C494) in q56. Two caveats: before answering, that agent had read this page, which then named three areas run 2 had missed (q34, q53, q56); and the `expect` and `must_not` boxes were checked by the same agent, which found no answer that contradicts a rule but seven answers (q16, q19, q20, q40, q44, q54, q55) that state a stage-only claim without saying that it is not in Google's documentation. The run also showed that `claims --topic` lists the first 50 claims unless `--limit` is given, so "read the topic in full" missed the end of the 20 of 96 topics that have more; `AGENTS.md` now says to add `--limit 200`. The run 2 and run 3 answers and reports are kept outside the repository by the reviewers; the scores above are what they showed.

## <img src="../../_system/brand/icons/seaweed.svg" width="24" height="24" alt=""> Maintain it

- Question ids (`q01`, `q02`...) never change. Add new questions with the next free id when a day is added.
- `build_kb.py` fails when a claim ID in `questions.yaml`, equivalents included, does not exist or is private, so a split or hidden claim is noticed.
- Add an equivalent with `|` only when the other claim gives the same information as the expected one (a repeat, or a docs claim stating the same point). An ID stands in one point of a question only; `eval_check.py` stops on an ID listed twice or an item it cannot read.

<p align="center"><img src="../brand/divider.svg" width="600" alt="Section divider"></p>

<p align="center"><sub>← <a href="../README.md">_system</a> · <a href="../../60-outputs/agent-pack/AGENTS.md">Agent pack</a> →</sub></p>
