"""Privacy guard run by save-version.bat (and setup-git.bat) before `git add -A`.

Lists what `git add -A --dry-run` would add and flags every NEW path that looks like raw material:
an image (except the README artwork written by _system/brand/make_brand.py: lower-case kebab-case PNGs of at most 1 MB
directly in _system/brand/ (the banners), in _system/brand/covers/ (the field guide covers) or in _system/brand/social/ (the
web edition's share image, and its copy in 60-outputs/site/assets/social/); the README icons in
_system/brand/icons/ and the README illustrations in _system/brand/illustrations/ are SVG text and never flagged; the web
edition's 1-minute tour, exactly the four paths of PUBLISHED_MEDIA, is not flagged either), audio, video, transcript, archive, presentation or spreadsheet
file, a PDF outside 60-outputs/pdf/ and 60-outputs/site/downloads/, a CSV outside 50-maps/ (except the developer kit's
requirements.csv), a camera/WhatsApp/transcript file name, a large file, or a file outside the shared folders and the known top-level files.

Exit codes: 0 nothing suspicious, 3 suspicious paths listed (the caller asks the user to type YES), 2 error.
Usage:  python _system/tools/check_commit.py [--root REPO]
"""
import argparse, re, subprocess, sys
from pathlib import Path

SHARED = ('20-claims/', '25-kits/', '30-topics/', '40-sessions/', '50-maps/', '60-outputs/', '_system/', '.github/workflows/')
ROOT_FILES = {'.gitattributes', '.gitignore', 'CHANGELOG.md', 'PRIVACY.md', 'README.md', 'requirements.txt',
              'install-tools.bat', 'setup-git.bat', 'rebuild.bat', 'save-version.bat', 'ingest.bat', 'ask.bat',
              'LICENSE', 'LICENSE-CONTENT.md', 'NOTICE.md', 'METHOD.md', 'CONTRIBUTING.md',
              '00-raw/README.md', '10-sources/README.md', '70-private/README.md'}
# the web edition's 1-minute tour (made for it, never a recording of the event): its source pair and the site's copies, exactly these
PUBLISHED_MEDIA = {'_system/brand/video/tour.mp4', '_system/brand/video/tour-poster.jpg',
                   '60-outputs/site/assets/video/tour.mp4', '60-outputs/site/assets/video/tour-poster.jpg'}
# the copy of the share image (_system/brand/social/og-image.png) in the web edition, exactly this path
SITE_SOCIAL = '60-outputs/site/assets/social/og-image.png'
KINDS = {
    'image': 'heic heif jpg jpeg png gif webp tif tiff bmp dng raw avif',
    'audio': 'm4a mp3 wav aac ogg oga opus flac amr wma aiff',
    'video': 'mov mp4 m4v avi mkv webm 3gp wmv mts',
    'transcript': 'txt vtt srt sbv docx doc rtf odt pages',
    'archive': 'zip 7z rar tar gz tgz bz2 xz',
    'presentation': 'pptx ppt pptm potx pps ppsx key odp',
    'spreadsheet': 'xlsx xls xlsm ods numbers tsv',
}
EXT = {e: k for k, v in KINDS.items() for e in v.split()}
# where generated PDFs and CSVs belong; anywhere else a new one is flagged (a speaker's deck, an attendee list)
ALLOWED = {'pdf': ('60-outputs/pdf/', '60-outputs/site/downloads/'), 'csv': ('50-maps/', '60-outputs/dev/requirements.csv', '60-outputs/site/downloads/requirements.csv')}
NAME = re.compile(r'^(IMG|VID|PXL|DSC|MVIMG)_\d|^WhatsApp|^Screenshot|^Recording|^Aufnahme|(?<![a-z])trans[ck]ri|^t\d\d[a-z]?[-_ .]', re.I)
BIG = 25 * 1024 * 1024
# the README artwork rendered by _system/brand/make_brand.py: a lower-case PNG directly in _system/brand/ (the banners) or in
# _system/brand/covers/ (page 1 of each field guide), at most 1 MB. The icons in _system/brand/icons/ and the README illustrations in
# _system/brand/illustrations/ (<slug>-light.svg, <slug>-dark.svg) are SVG, which is never flagged.
BRAND_IMAGE = re.compile(r'_system/brand/(?:covers/|social/)?[a-z0-9]+(?:-[a-z0-9]+)*\.png')
BRAND_MAX = 1024 * 1024


def git(root, *args):
    r = subprocess.run(['git', '-c', 'core.quotepath=false', *args], cwd=root, capture_output=True)
    if r.returncode:
        sys.stderr.write(r.stderr.decode('utf-8', 'replace'))
        raise SystemExit(2)
    return r.stdout.decode('utf-8', 'replace')


def brand_image(root, path):
    """True for a README banner in _system/brand/, a cover in _system/brand/covers/, the share image in _system/brand/social/ or
    its copy in the web edition (not a photo dropped there: lower-case kebab name, PNG, small)."""
    if not (BRAND_IMAGE.fullmatch(path) or path == SITE_SOCIAL):
        return False
    try:
        return (root / path).stat().st_size <= BRAND_MAX
    except OSError:
        return True    # not on disk (a path in a test): the name alone decides


def reasons(root, path):
    if path in ROOT_FILES: return []
    out, name = [], path.rsplit('/', 1)[-1]
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if ext in EXT and not brand_image(root, path) and path not in PUBLISHED_MEDIA: out.append(f'{EXT[ext]} file')
    if ext in ALLOWED and not path.startswith(ALLOWED[ext]): out.append(f'{ext.upper()} outside {" and ".join(ALLOWED[ext])}')
    if NAME.search(name): out.append('named like a photo, chat file, recording or transcript')
    if '/' not in path: out.append('loose file at the top level')
    elif not path.startswith(SHARED): out.append('outside the shared folders')
    try:
        if (root / path).stat().st_size > BIG: out.append('larger than 25 MB')
    except OSError:
        pass
    return out


def main():
    sys.stdout.reconfigure(errors='replace')
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
    root = Path(ap.parse_args().root)
    head = subprocess.run(['git', 'rev-parse', '-q', '--verify', 'HEAD'], cwd=root, capture_output=True).returncode == 0
    committed = set(git(root, 'ls-tree', '-r', '-z', '--name-only', 'HEAD').split('\0')) if head else set()
    lines = git(root, 'add', '-A', '--dry-run').splitlines()
    # files staged earlier (by hand or by a run whose commit failed) are not in the dry run: check them too
    lines += [f"add '{p}'" for p in git(root, 'diff', '--cached', '--name-only', '-z').split('\0') if p]
    added, changed, removed, flagged, seen = [], [], [], [], set()
    for line in lines:
        m = re.fullmatch(r"(add|remove) '(.*)'", line)
        if not m or m[2] in seen: continue
        op, path = m.groups()
        seen.add(path)
        if op == 'remove': removed.append(path)
        elif path in committed: changed.append(path)
        else:
            added.append(path)
            why = reasons(root, path)
            if why: flagged.append((path, why))
    print(f'Privacy check: {len(added)} new, {len(changed)} changed, {len(removed)} deleted file(s).')
    if not flagged:
        print('No new file looks like a photo, recording, transcript or other raw material.')
        return 0
    print()
    print('STOP. These new files look like private raw material (keep raw files in 00-raw\\):')
    for path, why in flagged:
        print(f'  {path}   [{", ".join(why)}]')
    print()
    print('Move them into 00-raw\\, 10-sources\\ or 70-private\\ (or delete them) and run this again.')
    return 3


if __name__ == '__main__':
    sys.exit(main())
