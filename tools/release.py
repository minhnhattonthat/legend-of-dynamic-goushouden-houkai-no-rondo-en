"""Release: every gate, then the patch and the zip (references/pipeline.md §Release). Stops at the first failure.

    python -X utf8 tools/release.py [--version 1.1] [--force] [--skip-build]

Steps: build -> check.py -> smoke (cold boot) -> jp_left.py -> qa_gate.py check on every work/qa/**/manifest.tsv
(visual tour with its build hash, story pass) -> textcover.py over the coverage logs (gathered into
work/qa/cover_release) -> no unticked line in docs/polish.md -> no template placeholder in README.md -> debug
tool off in the build -> bps.py make (re-applies and compares) -> apply to a clean copy of the original and compare
again -> release/Goushouden_EN_vX.Y.zip holding the patch and README.txt only.

Never publishes: `gh release create` is the owner's call. Refuses to overwrite an existing version's files without
--force. The playable ROM stays in build/.
"""
import argparse
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from skill import SKILL  # noqa: E402

PY = [sys.executable, '-X', 'utf8']
ROM = os.path.join(ROOT, 'rom', 'Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba')
BUILT = os.path.join(ROOT, 'build', 'goushouden_en.gba')
STRINGS = os.path.join(ROOT, 'build', 'goushouden_en.strings.tsv')
# Coverage logs (Phase 8): the full tour, every dialogue message, every ROM string and every small-archive message
# forced through the game's own printers. The phase 9 text edits grew the archive, which moved the book / desc /
# effect / place messages and the 86 non-waived relocated ROM strings written after it (dialogue ids and in-place
# ROM strings kept their addresses): forcearc_s19 and forcestr_s19 re-force exactly those on the final build.
# A later text change that moves addresses needs the same reruns (compare build/*.strings.tsv before and after).
# v1.1 (issue #1 blank-line fix) moved them again: forcearc_v11 (book, desc, place) and forcestr_v11 (64 strings).
COVER_DIRS = ['tour_en3', 'msgview', 'forcestr', 'forcearc_s19', 'forcestr_s19', 'forcearc_v11', 'forcestr_v11']
# Debug tool off: tools/debug/dbgmenu.lua redirects main()'s BL at 0x7E48A to the debug menu at run time only; the
# release build must keep the retail BL (bl 0x0807E2F4).
DEBUG_BL = (0x7E48A, bytes([0xFF, 0xF7, 0x33, 0xFF]))
PLACEHOLDER = re.compile(r'<(?:Game title|platform|publisher|year|repo|file|size|sha1|game|ext)>|<[A-Z][a-z]+ ?/')


def run(name, cmd, **kw):
    print(f'== {name}: {" ".join(os.path.relpath(c, ROOT) if os.path.isabs(c) else c for c in cmd)}', flush=True)
    r = subprocess.run(cmd, cwd=ROOT, **kw)
    if r.returncode:
        sys.exit(f'release stopped: {name} exited {r.returncode}')


def fail(msg):
    sys.exit(f'release stopped: {msg}')


def hashes(path):
    data = open(path, 'rb').read()
    return {'size': len(data), 'crc32': f'{zlib.crc32(data):08X}', 'md5': hashlib.md5(data).hexdigest(),
            'sha1': hashlib.sha1(data).hexdigest()}


def gather_cover(dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    n = 0
    for d in COVER_DIRS:
        src = os.path.join(ROOT, 'work', 'qa', d)
        logs = glob.glob(os.path.join(src, '**', 'log.txt'), recursive=True)
        if not logs:
            fail(f'no coverage logs under work/qa/{d}')
        for p in logs:
            out = os.path.join(dst, d, os.path.relpath(p, src))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copyfile(p, out)
            n += 1
    print(f'   {n} logs gathered into {os.path.relpath(dst, ROOT)}')


def readme_txt(version, base, patched, patch_name, patch_sha1):
    return f"""Legend of Dynamic Goushouden: Houkai no Rondo - English translation v{version}
==========================================================================

Unofficial English fan translation of the Game Boy Advance RPG "Legend of Dynamic Goushouden: Houkai no Rondo"
(Banpresto, 2003). Dialogue, menus, items, skills, battle and system messages, the character book, the ending
credits and the graphics with text are in English (the 豪翔伝 title logo is kept). Names can be entered in kana or
English letters.

How to patch
------------
You need your own dump of the Japanese cartridge. This zip holds no game data and no patched ROM; do not ask for
or share one.

Base ROM: Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba (No-Intro)
  Size   {base['size']} bytes
  CRC32  {base['crc32']}
  MD5    {base['md5']}
  SHA-1  {base['sha1']}

Apply {patch_name} with any BPS patcher (Floating IPS, Rom Patcher JS at https://www.marcrobledo.com/RomPatcher.js/,
beat). The patcher checks the base ROM's checksum and refuses a different dump.

Patched ROM: {patched['size']} bytes (16 MiB), CRC32 {patched['crc32']}, SHA-1 {patched['sha1']}
Patch SHA-1: {patch_sha1}

Notes
-----
- Tested in Mesen 2.2.1 with the official GBA BIOS. Save type SRAM.
- Start from a cold boot. Savestates made with the Japanese game or another patch version carry the old code and
  text; in-game saves (SRAM) carry over.
- Known issues: none known. Report bugs (a savestate helps most) at
  https://github.com/minhnhattonthat/legend-of-dynamic-goushouden-houkai-no-rondo-en/issues

Credits
-------
Translation, tools and hacking: minhnhattonthat, with extensive AI assistance (Claude by Anthropic; OpenAI Codex
for review). Original game (c) Banpresto / Dynamic Planning. This is an unofficial fan work, not affiliated with
them.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', default='1.1')
    ap.add_argument('--force', action='store_true', help='overwrite this version\'s existing release files')
    ap.add_argument('--skip-build', action='store_true', help='use build/ as it is (the gates still run on it)')
    a = ap.parse_args()

    rel = os.path.join(ROOT, 'release')
    patch_name = f'Goushouden_EN_v{a.version}.bps'
    patch = os.path.join(rel, patch_name)
    zpath = os.path.join(rel, f'Goushouden_EN_v{a.version}.zip')
    if not a.force and (os.path.exists(patch) or os.path.exists(zpath)):
        fail(f'release/ already holds v{a.version}; pass --force to overwrite or bump --version')

    if not a.skip_build:
        run('build', PY + ['build.py'])
    run('check', PY + ['tools/check.py'])
    run('smoke', PY + [os.path.join(SKILL, 'scripts', 'emu.py'), BUILT, '--out', 'work/qa/release_smoke',
                       '--route', 'tools/routes/boot.txt', '--smoke'])
    run('jp_left', PY + [os.path.join(SKILL, 'scripts', 'jp_left.py'), BUILT, '--sjis', '--gba-ptrs',
                         '--known', 'tools/jp_known.txt'])

    gate = os.path.join(SKILL, 'scripts', 'qa_gate.py')
    mans = sorted(glob.glob(os.path.join(ROOT, 'work', 'qa', '**', 'manifest.tsv'), recursive=True))
    if not any(m.endswith(os.path.join('story', 'manifest.tsv')) for m in mans):
        fail('no story-pass manifest (work/qa/story/manifest.tsv)')
    for m in mans:
        vdir = os.path.join(os.path.dirname(m), 'verdicts')
        extra = ['--build', BUILT] if os.path.exists(m.replace('.tsv', '.build')) or os.path.exists(m + '.build') \
            else []
        run(f'qa_gate {os.path.relpath(m, ROOT)}', PY + [gate, 'check', m, vdir] + extra)

    cover = os.path.join(ROOT, 'work', 'qa', 'cover_release')
    gather_cover(cover)
    run('textcover', PY + [os.path.join(SKILL, 'scripts', 'textcover.py'), cover, STRINGS,
                           '--waive', 'docs/text_unshown.tsv'], stdout=subprocess.DEVNULL)

    with open(os.path.join(ROOT, 'docs', 'polish.md'), encoding='utf-8') as f:
        open_lines = [l for l in f if l.startswith('- [ ]')]
    if open_lines:
        fail(f'docs/polish.md has {len(open_lines)} unticked lines')
    with open(os.path.join(ROOT, 'README.md'), encoding='utf-8') as f:
        ph = sorted(set(PLACEHOLDER.findall(f.read())))
    if ph:
        fail(f'README.md still has template placeholders: {ph}')
    data = open(BUILT, 'rb').read()
    off, bl = DEBUG_BL
    if data[off:off + 4] != bl:
        fail(f'debug boot hook active in the build: {data[off:off + 4].hex()} at 0x{off:X}')
    print('== polish, README, debug off: ok')

    os.makedirs(rel, exist_ok=True)
    run('bps make', PY + ['tools/bps.py', 'make', ROM, BUILT, patch])
    check = os.path.join(rel, 'reapply_check.gba')
    run('bps apply', PY + ['tools/bps.py', 'apply', ROM, patch, check])
    same = open(check, 'rb').read() == data
    os.remove(check)
    if not same:
        fail('patch applied to the original does not give build/goushouden_en.gba')
    base, patched = hashes(ROM), hashes(BUILT)
    with open(os.path.join(ROOT, 'rom.sha1'), encoding='utf-8') as f:
        if base['sha1'] not in f.read():
            fail('rom/ dump differs from rom.sha1')
    psha = hashlib.sha1(open(patch, 'rb').read()).hexdigest()
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(patch, patch_name)
        z.writestr('README.txt', readme_txt(a.version, base, patched, patch_name, psha).replace('\n', '\r\n'))
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
    if sorted(names) != sorted([patch_name, 'README.txt']):
        fail(f'zip holds {names}')
    print(f'release ok: {os.path.relpath(zpath, ROOT)} ({os.path.getsize(zpath)} bytes)\n'
          f'  patch {patch_name} sha1 {psha}\n  patched ROM crc32 {patched["crc32"]} sha1 {patched["sha1"]}\n'
          f'  not published: `gh release create` is the owner\'s call')


if __name__ == '__main__':
    main()
