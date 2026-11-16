"""Story-pass chapter files (references/translation.md §Review, story pass).

    python -X utf8 tools/story.py [--out work/qa/story/chapters]

Writes one file per chapter of docs/synopsis.md §Chapters (archive files in story order): every dialogue entry as
`>> id | speaker | JP` then `   EN: ...`, with the speaker line split off both sides. Then:
    python -X utf8 $SKILL/scripts/qa_gate.py init work/qa/story/manifest.tsv work/qa/story/chapters --glob "*.txt"
    JOBS=3 sh tools/story_review.sh            (read-only codex, one call per chapter)
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def chapters():
    """[(name, title, [file numbers])] from the `- chNN fAA-fBB: title` lines of docs/synopsis.md."""
    out = []
    with open(os.path.join(ROOT, 'docs', 'synopsis.md'), encoding='utf-8') as f:
        for line in f:
            m = re.match(r'- (ch\d\d) f(\d\d)-f(\d\d): (.+)', line)
            if m:
                out.append((m.group(1), m.group(4).strip(), list(range(int(m.group(2)), int(m.group(3)) + 1))))
    return out


def speakers():
    """id -> speaker from the translation batches (work/tl/bNNN.tsv column 2)."""
    sp = {}
    for p in glob.glob(os.path.join(ROOT, 'work', 'tl', 'b*.tsv')):
        if p.endswith('.out.tsv'):
            continue
        with open(p, encoding='utf-8') as f:
            for line in f:
                c = line.rstrip('\n').split('\t')
                if len(c) >= 2:
                    sp[c[0]] = c[1]
    return sp


def split(text, speaker):
    """Drop the speaker line (first line) when the batch says the entry has one."""
    lines = (text or '').split('\n')
    if speaker and len(lines) > 1:
        lines = lines[1:]
    return ' / '.join(l for l in lines if l.strip())


def verdicts(rep, round_name):
    """Write verdicts/<round>_<ch>.tsv from each report's Assessment; print each report's Critical/Important part."""
    vdir = os.path.join(ROOT, 'work', 'qa', 'story', 'verdicts')
    os.makedirs(vdir, exist_ok=True)
    bad = 0
    for p in sorted(glob.glob(os.path.join(rep, 'ch*.txt'))):
        ch = os.path.basename(p)[:-4]
        text = open(p, encoding='utf-8').read()
        m = re.search(r'#+\s*Assessment\s*\n+\s*[`*]*(ok|issue)\b[`*]*\s*[-:–—]*\s*(.*)', text, re.I)
        if not m:
            print(f'{ch}: no Assessment found')
            bad += 1
            continue
        word, note = m.group(1).lower(), m.group(2).strip()
        with open(os.path.join(vdir, f'{round_name}_{ch}.tsv'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'{ch}\t{word}\t{note}\n')
        mi = re.search(r'#+\s*Minor', text, re.I)
        major = text[:mi.start()] if mi else text
        print(f'== {ch}: {word} - {note}')
        if word == 'issue':
            print(major.split('Issues', 1)[-1].strip())
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=os.path.join(ROOT, 'work', 'qa', 'story', 'chapters'))
    ap.add_argument('--verdicts', metavar='REPORTS', nargs='?', const=os.path.join(ROOT, 'work', 'qa', 'story', 'reports'),
                    help='parse story_review.sh reports into verdict files instead of writing chapters')
    ap.add_argument('--round', default='r1', help='verdict file prefix (later rounds sort after earlier ones)')
    a = ap.parse_args()
    if a.verdicts:
        sys.exit(1 if verdicts(a.verdicts, a.round) else 0)
    chs = chapters()
    if not chs:
        sys.exit('no `- chNN fAA-fBB: title` lines in docs/synopsis.md')
    sp = speakers()
    os.makedirs(a.out, exist_ok=True)
    seen = set()
    for name, title, files in chs:
        rows = [f'# {name}: {title} (archive files f{files[0]:02d}-f{files[-1]:02d}, story order)', '']
        for n in files:
            seen.add(n)
            with open(os.path.join(ROOT, 'script', 'archive', f'f{n:02d}.json'), encoding='utf-8') as f:
                for e in json.load(f):
                    s = sp.get(e['id'], '')
                    has = bool(s) and s != '-'
                    en = e.get('en') or ''
                    # the shipped tag (en's first line, from tools/speakers.tsv at merge), not the batch's old one
                    if has and '\n' in en:
                        s = en.split('\n', 1)[0]
                    rows.append(f">> {e['id']} | {s if has else '-'} | {split(e['jp'], has)}")
                    rows.append(f"   EN: {split(e.get('en') or '', has)}")
        with open(os.path.join(a.out, name + '.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(rows) + '\n')
        print(name, len(rows) // 2 - 1, 'entries')
    left = sorted(set(int(os.path.basename(p)[1:3]) for p in glob.glob(os.path.join(ROOT, 'script', 'archive', 'f*.json'))) - seen)
    if left:
        sys.exit(f'archive files in no chapter: {left}')


if __name__ == '__main__':
    main()
