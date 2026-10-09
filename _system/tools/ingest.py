"""Copy a day's raw material into 00-raw/dayN/ untouched, make JPEG previews and index capture times.

Usage:  python _system/tools/ingest.py SOURCE [SOURCE ...] --day N [--dry-run]
        (ingest.bat does this when a folder is dragged onto it)

SOURCE is a folder (searched recursively) or a file. Nothing in SOURCE is changed.
- Copies (shutil.copy2) into 00-raw/dayN/{slides, video, audio, transcripts, other}/ under the original name.
  A file that is already there with the same content is skipped; a DIFFERENT file with the same name is never
  overwritten and is reported as a name clash.
- Writes 1600 px JPEG previews of HEIC/HEIF/JPEG/PNG images into 10-sources/dayN/slides-jpg/<name>.jpg with
  Windows' own decoder (heic2jpg.ps1, WPF). Existing previews are kept.
- Writes 10-sources/dayN/media.yaml: every file under 00-raw/dayN/ with kind, capture time (photo EXIF
  DateTimeOriginal + OffsetTimeOriginal, video/audio mvhd), size, duration and a suggested session
  (the last session of that day in 20-claims/sessions.yaml starting at or before the capture time).
- Excluded photos (EXCLUDED in _system/build_kb.py) are copied untouched like the rest, but get no preview and no index entry.
- A file that cannot be read or copied (locked, card removed) is reported as COPY FAILED; the others are still copied
  and the index is still written.
Running it again changes nothing that is already in place. Exit code: 0 ok, 1 finished with problems, 2 stopped.
"""
import argparse, hashlib, os, re, shutil, struct, subprocess, sys, tempfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(TOOLS.parent))
try:
    import yaml
    from PIL import Image
    from build_kb import EXCLUDED_RE, load_yaml  # the knowledge base's YAML loader (a repeated key is an error) and exclusion list
except Exception as ex:  # a missing package or a broken build_kb.py: stop before anything is copied
    print(f'STOPPED: {type(ex).__name__}: {ex}. Run install-tools.bat, then try again.')
    sys.exit(2)

FOLDERS = {'slides': 'heic heif jpg jpeg png gif webp tif tiff bmp dng avif',
           'video': 'mov mp4 m4v avi mkv webm 3gp',
           'audio': 'm4a mp3 wav aac ogg opus flac amr wma',
           'transcripts': 'txt vtt srt docx md'}
FOLDER = {'.' + e: k for k, v in FOLDERS.items() for e in v.split()}
KIND = {'slides': 'image', 'video': 'video', 'audio': 'audio', 'transcripts': 'transcript', 'other': 'other'}
PREVIEW = {'.heic', '.heif', '.jpg', '.jpeg', '.png'}
MP4 = {'.mov', '.mp4', '.m4v', '.m4a', '.3gp'}
SKIP = {'thumbs.db', 'desktop.ini', '.ds_store'}
EPOCH_1904 = datetime(1904, 1, 1, tzinfo=timezone.utc)
HEADER = """\
# Media index of 00-raw/day{day}/ (PRIVATE: 10-sources/ is never shared). Written by _system/tools/ingest.py;
# run it again instead of editing this file.
# taken: capture time read from the file (photos: EXIF DateTimeOriginal with its UTC offset; videos and
#   recordings: the mvhd atom, shown in the offset of the recording or of the photos). Missing when unknown.
# suggested_session: only a GUESS, the last session of the day in 20-claims/sessions.yaml that starts at or
#   before the capture time. Check it against the photo before citing the file in a claim.
"""


def skip(p):
    n = p.name.lower()
    return n in SKIP or n.startswith(('.', '~$')) or n.endswith('.part')


def files_in(path):
    if path.is_file():
        return [path]
    return sorted((p for p in path.rglob('*') if p.is_file() and not skip(p)), key=lambda p: str(p).lower())


def digest(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def same(a, b):
    return a.stat().st_size == b.stat().st_size and digest(a) == digest(b)


def why(ex):
    return getattr(ex, 'strerror', None) or str(ex) or type(ex).__name__


def tz(text):
    m = re.fullmatch(r'([+-])(\d\d):?(\d\d)', str(text).strip('\x00 '))
    if not m:
        return None
    d = timedelta(hours=int(m[2]), minutes=int(m[3]))
    return timezone(-d if m[1] == '-' else d)


def exif(path):
    """(capture datetime or None, EXIF orientation) from the Exif/TIFF block inside a HEIC, JPEG or PNG."""
    with open(path, 'rb') as f:
        data = f.read(32 << 20)
    starts = []
    for pats, skip_ in (((b'Exif\x00\x00MM\x00*', b'Exif\x00\x00II*\x00'), 6), ((b'MM\x00*', b'II*\x00'), 0)):
        for pat in pats:
            i = data.find(pat)
            while i >= 0 and len(starts) < 12:
                starts.append(i + skip_)
                i = data.find(pat, i + 1)
        if starts:
            break
    for i in sorted(set(starts)):
        ex = Image.Exif()
        try:
            ex.load(b'Exif\x00\x00' + data[i:i + (1 << 20)])
            sub = ex.get_ifd(0x8769)
            t = datetime.strptime(str(sub.get(36867) or ex.get(306) or '').strip('\x00 '), '%Y:%m:%d %H:%M:%S')
        except Exception:
            continue
        off = tz(sub.get(36881) or sub.get(36880) or '')
        return (t.replace(tzinfo=off) if off else t), int(ex.get(274) or 1)
    return None, 1


def boxes(f, start, end):
    pos = start
    while pos + 8 <= end:
        f.seek(pos)
        size, typ = struct.unpack('>I4s', f.read(8))
        head = 8
        if size == 1:
            size, head = struct.unpack('>Q', f.read(8))[0], 16
        elif size == 0:
            size = end - pos
        if size < head or pos + size > end:
            return
        yield typ, pos + head, pos + size
        pos += size


def movie(path):
    """(creation time in UTC, duration in seconds, UTC offset of an Apple creationdate) from a MOV/MP4/M4A."""
    created = dur = off = None
    with open(path, 'rb') as f:
        end = f.seek(0, 2)
        for typ, s, e in boxes(f, 0, end):
            if typ != b'moov':
                continue
            for t2, s2, e2 in boxes(f, s, e):
                if t2 == b'mvhd':
                    f.seek(s2)
                    b = f.read(min(e2 - s2, 64))
                    c, _, scale, d = struct.unpack('>QQIQ', b[4:32]) if b[0] == 1 else struct.unpack('>IIII', b[4:20])
                    created = EPOCH_1904 + timedelta(seconds=c) if c else None
                    dur = round(d / scale, 1) if scale else None
                elif t2 == b'meta' and e2 - s2 < (1 << 20):
                    f.seek(s2)
                    m = re.search(rb'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d([+-]\d\d:?\d\d)', f.read(e2 - s2))
                    off = tz(m[1].decode()) if m else None
            break
    return created, dur, off


def load_day(root, day):
    """(date of the day or None, [(minutes since midnight, session id)], error or None) from 20-claims/sessions.yaml."""
    try:
        doc = load_yaml((root / '20-claims' / 'sessions.yaml').read_text(encoding='utf-8')) or {}
    except FileNotFoundError:
        return None, [], None
    except (OSError, ValueError, yaml.YAMLError) as ex:
        return None, [], f'20-claims/sessions.yaml cannot be read, so no session is suggested: {" ".join(str(ex).split())}'
    for d in (doc.get('days') or []) if isinstance(doc, dict) else []:
        if not isinstance(d, dict) or d.get('day') != day:
            continue
        starts = []
        for s in d.get('sessions') or []:
            if not isinstance(s, dict) or not isinstance(s.get('id'), str):
                continue
            t = s.get('time')
            if isinstance(t, int) and not isinstance(t, bool):  # an unquoted 10:00 is read by YAML as 600 minutes
                starts.append((t, s['id']))
            elif isinstance(t, str) and re.fullmatch(r'\d{1,2}:\d\d', t.strip()):
                h, m = t.strip().split(':')
                starts.append((int(h) * 60 + int(m), s['id']))
        return str(d.get('date') or '') or None, sorted(starts), None
    return None, [], None


def suggest(taken, date, starts):
    if not taken or not date or not starts or taken.date().isoformat() != date:
        return None
    minute = taken.hour * 60 + taken.minute
    best = [sid for start, sid in starts if start <= minute]
    return best[-1] if best else None


def previews(jobs):
    """Run heic2jpg.ps1 once for [(source, destination, orientation)]; returns {destination: error or None}."""
    if not jobs:
        return {}
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='\n', suffix='.tsv', delete=False) as t:
        t.write(''.join(f'{s}\t{d}\t{o}\n' for s, d, o in jobs))
    try:
        r = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File',
                            str(TOOLS / 'heic2jpg.ps1'), '-List', t.name], capture_output=True)
    except OSError as e:
        return {str(d): f'PowerShell could not start: {e}' for _, d, _ in jobs}
    finally:
        os.unlink(t.name)
    done = {}
    for line in r.stdout.decode('utf-8', 'replace').splitlines():
        parts = line.split('\t')
        if parts[0] == 'ok' and len(parts) > 1:
            done[parts[1]] = None
        elif parts[0] == 'ERR' and len(parts) > 2:
            done[parts[1]] = parts[2]
    out = {}
    for s, d, _ in jobs:
        if str(d) in done and Path(d).exists():
            out[str(d)] = None
        else:
            out[str(d)] = done.get(str(s)) or r.stderr.decode('utf-8', 'replace').strip()[-300:] or 'no preview written'
    return out


def main():
    sys.stdout.reconfigure(errors='replace')
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('sources', nargs='+', type=lambda x: Path(x.strip().strip('"').strip()))
    ap.add_argument('--day', type=int, required=True)
    ap.add_argument('--dry-run', action='store_true', help='show what would happen, change nothing')
    ap.add_argument('--root', type=Path, default=TOOLS.parents[1], help='knowledge base folder (default: this one)')
    a = ap.parse_args()
    root, day, dry = a.root.resolve(), a.day, a.dry_run
    if not 1 <= day <= 99:
        sys.exit(print('The day must be a number such as 2.') or 2)
    raw, src10 = root / '00-raw' / f'day{day}', root / '10-sources' / f'day{day}'
    jpg, index = src10 / 'slides-jpg', src10 / 'media.yaml'
    for s in a.sources:
        s = s.resolve()
        if not s.exists():
            sys.exit(print(f'Not found: {s}') or 2)
        if s in (root / '00-raw').parents or s == root / '00-raw' or s == root / '10-sources' or root / '10-sources' in s.parents:
            sys.exit(print(f'{s} is (part of) the knowledge base. Drag the folder with the new material instead.') or 2)
    if (root / '.git').exists() and shutil.which('git'):
        probe = [f'00-raw/day{day}/slides/IMG_0000.HEIC', f'00-raw/day{day}/transcripts/t.txt',
                 f'10-sources/day{day}/media.yaml', f'10-sources/day{day}/slides-jpg/IMG_0000.jpg']
        r = subprocess.run(['git', 'check-ignore', '--no-index', *probe], cwd=root, capture_output=True, text=True)
        missing = set(probe) - set(r.stdout.split())
        if missing:
            sys.exit(print('STOP: git would not ignore ' + ', '.join(sorted(missing)) +
                           '. Fix .gitignore before copying private material.') or 2)

    existing = defaultdict(list)
    if raw.exists():
        for p in files_in(raw):
            existing[p.name.lower()].append(p)
    planned, copies, problems = {}, [], []
    n_same = n_inplace = 0
    print(f'Day {day}: {"dry run, nothing is changed. Target" if dry else "importing into"} {raw}')
    for s in a.sources:
        for f in files_in(s.resolve()):
            if raw in f.parents:
                n_inplace += 1
                continue
            folder = FOLDER.get(f.suffix.lower(), 'other')
            dest = raw / folder / f.name
            key = f.name.lower()
            try:
                if any(same(p, f) for p in existing.get(key, [])) or (key in planned and same(planned[key], f)):
                    n_same += 1
                    continue
            except OSError as ex:
                problems.append(f'COPY FAILED (cannot read it, not copied): {f}: {why(ex)}')
                continue
            if existing.get(key):
                problems.append(f'NAME CLASH (not copied): {f}  differs from  {existing[key][0].relative_to(root).as_posix()}')
                continue
            if key in planned:
                problems.append(f'NAME CLASH (not copied): {f}  differs from  {planned[key]} (same name, both new)')
                continue
            planned[key] = f
            copies.append((f, dest))
    n_copied = 0
    for f, dest in copies:
        print(f'  {"would copy" if dry else "copy"}  {f.name}  ->  {dest.relative_to(root).as_posix()}')
        if dry:
            continue
        part = dest.with_name(dest.name + '.part')
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, part)
            os.replace(part, dest)
            if dest.stat().st_size != f.stat().st_size:
                problems.append(f'COPY CHECK FAILED: {dest} has a different size than {f}')
            n_copied += 1
        except OSError as ex:
            problems.append(f'COPY FAILED (not copied): {f}: {why(ex)}')
            try:
                part.unlink(missing_ok=True)
            except OSError as ex2:
                problems.append(f'LEFTOVER: could not delete {part}: {why(ex2)}')
    print(f'{len(copies) if dry else n_copied} file(s) {"to copy" if dry else "copied"}, {n_same} skipped because the same file is already '
          f'there (or was given twice), {n_inplace} already inside 00-raw/day{day}/.')

    # Index everything that is (or after this run will be) under 00-raw/dayN/.
    items = {p.relative_to(raw).as_posix(): p for p in (files_in(raw) if raw.exists() else [])}
    if dry:
        items.update({d.relative_to(raw).as_posix(): f for f, d in copies})
    date, starts, err = load_day(root, day)
    entries, jobs, stems, warnings = [], [], {}, [err] if err else []
    for rel in sorted(items, key=str.lower):
        p = items[rel]
        ext = p.suffix.lower()
        if EXCLUDED_RE.search(p.stem):
            old = jpg / (p.stem + '.jpg')
            warnings.append(f'{rel} is an excluded photo: kept in 00-raw/day{day}/, but not indexed and no preview made.'
                            + (f' Delete the old preview {old.relative_to(root).as_posix()} by hand.' if old.exists() else ''))
            continue
        folder = rel.split('/')[0] if '/' in rel else ''
        kind = KIND.get(folder) or KIND[FOLDER.get(ext, 'other')]
        e, orient = {'file': rel, 'kind': kind}, 1
        try:
            if ext in PREVIEW or kind == 'image':
                taken, orient = exif(p)
                e['taken'] = taken
            if ext in MP4:
                created, dur, off = movie(p)
                e['taken'], e['duration'], e['_off'] = created, dur, off
        except Exception as ex:
            problems.append(f'UNREADABLE: {rel}: {ex}')
        try:
            e['size'] = p.stat().st_size
        except OSError as ex:
            problems.append(f'UNREADABLE: {rel}: {why(ex)}')
        if ext in PREVIEW:
            out = jpg / (p.stem + '.jpg')
            if stems.setdefault(out.name.lower(), rel) != rel:
                problems.append(f'PREVIEW NAME TAKEN: {rel} would also become {out.name}; no preview made for it')
            else:
                e['preview'] = out.relative_to(root).as_posix()
                if not out.exists():
                    jobs.append((p, out, 1 if ext in ('.heic', '.heif') else orient))  # the HEIF decoder rotates by itself
        entries.append(e)
    offsets = Counter(e['taken'].utcoffset() for e in entries
                      if isinstance(e.get('taken'), datetime) and e['taken'].tzinfo and '_off' not in e)
    photo_off = timezone(offsets.most_common(1)[0][0]) if offsets else None
    for e in entries:
        if '_off' in e:
            off = e.pop('_off') or photo_off
            if e.get('taken') and off:
                e['taken'] = e['taken'].astimezone(off)
            elif e.get('taken'):
                e['taken_note'] = 'UTC; local offset unknown'
        if isinstance(e.get('taken'), datetime) and date and e['taken'].date().isoformat() != date:
            warnings.append(f'{e["file"]} was captured on {e["taken"].date()}, but day {day} is {date}. Right day?')
        s = suggest(e.get('taken'), date, starts) if 'taken_note' not in e else None
        if s:
            e['suggested_session'] = s
        if isinstance(e.get('taken'), datetime):
            e['taken'] = e['taken'].isoformat()
    entries = [{k: v for k, v in e.items() if v is not None} for e in entries]

    if dry:
        print(f'{len(jobs)} preview(s) to make in {jpg.relative_to(root).as_posix()}/.')
        for e in entries:
            if e['kind'] in ('image', 'video', 'audio'):
                print(f'  {e["file"]:<44} {e.get("taken", "no capture time"):<26} {e.get("suggested_session", "")}')
    else:
        made, rel_of = previews(jobs), {str(d): s.relative_to(raw).as_posix() for s, d, _ in jobs}
        for d, err in made.items():
            if err:
                problems.append(f'PREVIEW FAILED: {rel_of[d]}: {err}')
        for e in entries:
            if 'preview' in e and not (root / e['preview']).exists():
                del e['preview']
        print(f'{sum(1 for v in made.values() if v is None)} preview(s) made in {jpg.relative_to(root).as_posix()}/.')
        doc = {'day': day, 'date': date, 'files': entries}
        text = HEADER.format(day=day) + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=200)
        old = index.read_text(encoding='utf-8') if index.exists() else None
        if old != text:
            src10.mkdir(parents=True, exist_ok=True)
            with open(index, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
        print(f'{index.relative_to(root).as_posix()}: {len(entries)} file(s), {"unchanged" if old == text else "written"}.')
    if warnings:
        print(f'\n{len(warnings)} warning(s):')
        print('\n'.join('  ' + w for w in warnings))
    if problems:
        print(f'\n{len(problems)} problem(s):')
        print('\n'.join('  ' + p for p in problems))
        return 1
    return 0


def run():
    try:
        return main()
    except KeyboardInterrupt:
        print('\nSTOPPED: interrupted.')
    except Exception as ex:  # anything unexpected: a short message and exit code 2, never a misleading "done"
        print(f'\nSTOPPED by an unexpected error: {type(ex).__name__}: {" ".join(str(ex).split())}')
    return 2


if __name__ == '__main__':
    sys.exit(run())
