"""Unticked docs/polish.md lines grouped by id, with each id's batch, JP and current English (from work/tl).

    python -X utf8 tools/polish_ids.py [--all]

Read-only: helps write a fixes TSV for tools/apply_fixes.py. --all includes ticked lines too.
"""
import argparse
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tl():
    jp, en, form = {}, {}, {}
    for p in sorted(glob.glob(os.path.join(ROOT, 'work', 'tl', 'b*.tsv'))):
        b = os.path.basename(p).split('.')[0]
        out = p.endswith('.out.tsv')
        with open(p, encoding='utf-8') as f:
            for line in f:
                c = line.rstrip('\n').split('\t')
                if out and len(c) >= 2:
                    en[c[0]] = (b, c[1])
                elif not out and len(c) >= 5:
                    jp[c[0]] = (c[1], c[2], c[3], c[4])
    return jp, en


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--all', action='store_true')
    a = ap.parse_args()
    jp, en = tl()
    by = {}
    with open(os.path.join(ROOT, 'docs', 'polish.md'), encoding='utf-8') as f:
        for line in f:
            m = re.match(r'- \[( |x)\] (\S+) (?:\((b\d+)\) )?- (.*)', line)
            if m and (a.all or m.group(1) == ' '):
                by.setdefault(m.group(2), []).append(m.group(4))
    for i, notes in by.items():
        sp, form, lim, j = jp.get(i, ('?', '?', '?', '?'))
        b, e = en.get(i, ('?', '?'))
        print(f'== {i} [{b} {sp} {form} | {lim}]\nJP: {j}\nEN: {e}')
        for n in notes:
            s = n.split('Suggested: ', 1)
            print('  * ' + s[0].strip() + ('\n    > ' + s[1] if len(s) > 1 else ''))
    print(len(by), 'ids')


if __name__ == '__main__':
    main()
