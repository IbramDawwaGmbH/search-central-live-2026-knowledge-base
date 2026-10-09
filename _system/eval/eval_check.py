"""Score an agent's answers against the eval answer key (_system/eval/questions.yaml).

Usage:  python _system/eval/eval_check.py --template > answers.yaml     questions to give the agent, answers left empty
        python _system/eval/eval_check.py answers.yaml [--out report.md]

answers.yaml maps question ids to answer text ({q01: "...", q02: "..."}); a JSON object, or a list of {id, answer}, works too.
Scored by script: citation recall per question (the points in `claims` that the answer cites) and cited IDs that are not in
the agent pack (invented). Each `claims` item is one point: a claim ID, or equivalent IDs joined by | (D1-C006|D2-C752), and the
point counts as cited when the answer cites any one of them. Listed for a reviewer or an LLM judge: the `expect` points and `must_not` rules.
Pass rule (from questions.yaml): contains the expect points, cites a claim ID for every point in claims, follows any must_not.
"""
import json, re, sys
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CID = re.compile(r'\bD\d+-C\d{3}\b')
POINT = re.compile(r'D\d+-C\d{3}(?:\s*\|\s*D\d+-C\d{3})*')  # one expected point: a claim ID, or equivalent IDs joined by |
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
from build_kb import load_yaml  # the knowledge base's YAML loader: a key repeated in one entry is an error


def read(p):
    try:
        return load_yaml(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError, yaml.YAMLError) as e:
        sys.exit(f'{p}: cannot be read: {" ".join(str(e).split())}')


def load_answers(p):
    data = read(p)
    if isinstance(data, list): data = {x.get('id'): x.get('answer', '') for x in data if isinstance(x, dict)}
    if not isinstance(data, dict): sys.exit(f'{p}: expected a mapping of question id to answer text')
    return {str(k): '' if v is None else str(v) for k, v in data.items()}


def points(q, where):
    """The question's expected points, each a list of equivalent claim IDs. An ID may stand in one point only."""
    want = q.get('claims') or []
    if not isinstance(want, list): sys.exit(f'{where}: {q["id"]}: claims must be a list')
    out, seen = [], set()
    for x in want:
        if not isinstance(x, str) or not POINT.fullmatch(x.strip()):
            sys.exit(f'{where}: {q["id"]}: claims item {x!r} must be a claim ID, or equivalent IDs joined by | (D1-C006|D2-C752)')
        alts = [a.strip() for a in x.split('|')]
        for a in alts:
            if a in seen: sys.exit(f'{where}: {q["id"]}: {a} is listed twice in claims; an ID may stand in one point only')
            seen.add(a)
        out.append(alts)
    return out


def main(argv):
    qpath = Path(argv[argv.index('--questions') + 1]) if '--questions' in argv else HERE / 'questions.yaml'
    pack = Path(argv[argv.index('--pack') + 1]) if '--pack' in argv else ROOT / '60-outputs' / 'agent-pack'
    qs = read(qpath)
    if not isinstance(qs, list) or not all(isinstance(q, dict) and 'id' in q and 'q' in q for q in qs): sys.exit(f'{qpath}: must be a list of questions with id and q')
    want_of = {q['id']: points(q, qpath) for q in qs}
    if '--template' in argv:
        out = ['# Give each question to the agent (with the agent pack only) and paste its full answer, citations included.',
               '# Then score: python _system/eval/eval_check.py answers.yaml --out eval-report.md (citation recall per expected point;',
               '# a point the key lists with equivalent claim IDs counts as cited when the answer cites any one of them).']
        out += [f'{q["id"]}: ""   # {q["q"]}' for q in qs]
        sys.stdout.reconfigure(encoding='utf-8')
        print('\n'.join(out))
        return
    args = [a for i, a in enumerate(argv) if not a.startswith('--') and (i == 0 or argv[i - 1] not in ('--questions', '--pack', '--out'))]
    if not args: sys.exit(__doc__)
    answers = load_answers(args[0])
    known = set()
    if (pack / 'claims.jsonl').exists():
        known = {json.loads(l)['id'] for l in (pack / 'claims.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
    rep, recalls, full, invented_all = ['# Eval report', '', f'Questions: `{qpath.name}` · answers: `{Path(args[0]).name}`' + (f' · pack: {len(known)} claims' if known else ' · pack not found, invented IDs not checked'), ''], [], 0, 0
    for q in qs:
        a = answers.get(q['id'])
        want = want_of[q['id']]
        cited = sorted(set(CID.findall(a or '')))
        invented = [x for x in cited if known and x not in known]
        invented_all += len(invented)
        rep += [f"## {q['id']}: {q['q']}", '']
        if a is None or not a.strip():
            rep += ['**No answer.** Citation recall 0.', '']
            if want: recalls.append(0.0)
            continue
        if want:
            hit = [p for p in want if any(x in cited for x in p)]
            r = len(hit) / len(want)
            recalls.append(r); full += r == 1
            missing = [' or '.join(p) for p in want if p not in hit]
            rep.append(f"Citation recall: **{len(hit)}/{len(want)}** points" + (f" (missing: {'; '.join(missing)})" if r < 1 else ' (all cited)'))
            alt = [f"{' or '.join(p)} (cited: {', '.join(x for x in p if x in cited)})" for p in want if len(p) > 1 and p in hit]
            if alt: rep.append(f"Points with equivalent IDs: {'; '.join(alt)}")
        else:
            rep.append('Citation recall: n/a (no claims expected; the answer should say the knowledge base does not cover this).')
        if cited: rep.append(f"Cited: {', '.join(cited)}")
        if invented: rep.append(f"**Not in the agent pack (invented or private):** {', '.join(invented)}")
        rep += ['', 'Check by hand: the answer contains']
        rep += [f'- [ ] {x}' for x in q.get('expect', [])]
        if q.get('must_not'): rep += ['', 'and does not'] + [f'- [ ] {x}' for x in q['must_not']]
        rep += ['', '<details><summary>Answer</summary>', '', a.strip(), '', '</details>', '']
    mean = sum(recalls) / len(recalls) if recalls else 0
    summary = [f'**Summary:** mean citation recall {mean:.2f} over {len(recalls)} questions with expected claims; '
               f'{full} with every expected point cited; {invented_all} cited IDs not in the pack. '
               'A point the key lists with equivalent IDs (A|B) counts as cited when the answer cites any one of them. '
               'A question passes only when its citations are complete and a reviewer ticks every expect and must_not box.', '']
    text = '\n'.join(rep[:4] + summary + rep[4:]) + '\n'
    if '--out' in argv: Path(argv[argv.index('--out') + 1]).write_text(text, encoding='utf-8', newline='\n')
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        print(text)
    print(f'mean citation recall {mean:.2f}; {full}/{len(recalls)} complete; {invented_all} invented IDs', file=sys.stderr)


if __name__ == '__main__':
    main(sys.argv[1:])
