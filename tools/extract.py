"""extract.py: the game's text <-> script/ JSON (phase 4).

  python -X utf8 tools/extract.py dump            write missing script/ files from the original ROM
  python -X utf8 tools/extract.py dump --force    rewrite all; keeps en/status/notes of every id whose jp is
                                                  unchanged (the extractor's status "data" wins) and lists ids
                                                  whose jp changed under an existing en (status requeue)
  python -X utf8 tools/extract.py stats           entries, translated counts per file

script/archive/fNN.json  one per script-archive file (54): one entry per used slot,
    {"id": "05.12", "msg": [message ids], "jp", "en", "status", "notes"}; id = file.slot, msg = the message ids
    (archive id map) that reach the slot. The slot's bytes are encode(text) + 00.
script/{book,desc,effect,place,test}/fNN.json  the five archives after it (archive.ARCHIVES), same fields; ids
    carry the archive's prefix (B00.12 book, D desc, E effect, P place, T test = unused, status data).
script/rom/PPPPPP.json   plain ROM strings by 4 KiB page, {"id": "r0CD95C", "ptrs": [pointer sites], "max", ...}
script/rom/sfx.json      onomatopoeia record names, {"id": "x0D9D44", "rec": record offset, "max", ...}
    max = bytes the text may take in place (00 excluded). status "data" = not text (format strings, magic, file
    names); it is never translated. Text form: tools/sjis.py.

Loaders for build.py: archive_texts(), rom_texts().
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import archive  # noqa: E402
import romstr  # noqa: E402
import sjis  # noqa: E402

SCRIPT = ROOT / "script"
ROM = ROOT / "rom" / "Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba"
JP = re.compile(r"[ぁ-ヿ一-鿿！-～　-〿]")  # kana, kanji, full-width forms
CARRY = ("en", "status", "notes")
# ROM strings the game reads two bytes per char: insert as fullwidth (sjis.fullwidth), budget = max // 2 chars.
# 0D18BC / 0D18C4: default hero / heroine names (ASCII there blanked the name tag and the box, phase 5)
FULLWIDTH = {0x0D18BC, 0x0D18C4}


def message_ids(rom):
    """{message number (file * 100 + slot): [message ids]} from the script archive's id map."""
    return archive.message_ids(rom)


def archive_entries(rom):
    """-> {file name: [entries]} for the script archive and the five after it (archive.ARCHIVES)."""
    out = {}
    for spec in archive.ARCHIVES:
        ids = archive.message_ids(rom, spec.base)
        unused = not spec.sites
        for fi, f in enumerate(archive.read(rom, spec.base).files):
            ents = []
            for si, s in enumerate(archive.split_file(f.raw)):
                if s is None:
                    continue
                if not s.endswith(b"\0") or b"\0" in s[:-1]:
                    raise ValueError("%s file %d slot %d: not one 00-terminated string" % (spec.name, fi, si))
                ents.append({"id": "%s%02d.%02d" % (spec.prefix, fi, si), "msg": ids.get(fi * 100 + si, []),
                             "jp": sjis.decode(s[:-1]), "en": "", "status": "data" if unused else "",
                             "notes": "no pointer to this archive: unused (guess)" if unused else ""})
            out["%s/f%02d.json" % (spec.dir, fi)] = ents
    return out


def rom_strings(rom):
    """-> [(start, end, sites)] for the plain strings the game points at inside the text ranges."""
    ptrs = romstr.pointers(rom)
    return [(s, e, sites) for s, e, _, sites in romstr.scan(rom, ptrs)
            if sites and any(lo <= s < hi for lo, hi in romstr.TEXT_RANGES)]


def rom_entries(rom):
    out = {}
    for s, e, sites in rom_strings(rom):
        jp = sjis.decode(rom[s:e])
        span = [why for lo, hi, why in romstr.DATA_SPANS if lo <= s < hi]
        status, notes = ("data", span[0]) if span else ("", "") if JP.search(jp) else ("data", "ASCII only")
        out.setdefault("rom/%06X.json" % (s & ~0xFFF), []).append({
            "id": "r%06X" % s, "ptrs": ["%06X" % p for p in sites], "max": romstr.slot_room(rom, s, e) - 1,
            "jp": jp, "en": "", "status": status, "notes": notes})
    field = romstr.SFX_TABLE[4]
    sfx = []
    for o, name in romstr.sfx_records(rom):
        if name:
            sfx.append({"id": "x%06X" % o, "rec": "%06X" % (o - romstr.SFX_TABLE[3]), "max": field - 1,
                        "jp": sjis.decode(name), "en": "", "status": "",
                        "notes": "drawn as sprites through the kana lookup at 0x0D9C58 (guess): graphics work"})
    out["rom/sfx.json"] = sfx
    return out


def all_entries(rom):
    out = archive_entries(rom)
    out.update(rom_entries(rom))
    return out


def load(name):
    return json.loads((SCRIPT / name).read_text(encoding="utf-8"))


def save(name, ents):
    path = SCRIPT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ents, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def dump(rom, force=False):
    written, kept, requeue = 0, 0, []
    for name, ents in all_entries(rom).items():
        path = SCRIPT / name
        if path.exists() and not force:
            kept += 1
            continue
        if path.exists():
            old = {e["id"]: e for e in load(name)}
            for e in ents:
                o = old.get(e["id"])
                if not o:
                    continue
                if o["jp"] == e["jp"]:
                    if e["status"] == "data":  # the extractor's non-text ruling wins; keep any en for review
                        e["en"] = o.get("en", "")
                        continue
                    for k in CARRY:
                        e[k] = o.get(k) or e[k]
                elif o.get("en"):
                    e["notes"] = ("jp changed; old en: " + o["en"] + " " + o.get("notes", "")).strip()
                    e["status"] = "requeue"
                    requeue.append(e["id"])
        save(name, ents)
        written += 1
    print("wrote %d files, kept %d existing" % (written, kept))
    if requeue:
        print("jp changed under an existing translation (status requeue): " + " ".join(requeue))


def script_files():
    return sorted(p.relative_to(SCRIPT).as_posix() for p in SCRIPT.rglob("*.json"))


def translated(e):
    return bool(e.get("en")) and e.get("status") != "data"


def text_of(e, jp=False):
    return e["en"] if translated(e) and not jp else e["jp"]


def archive_texts(jp=False, name="script"):
    """-> {file index: {slot: text}} from script/<dir of archive `name`> (en where translated, else jp;
    jp=True: all jp)."""
    d = archive.BY_NAME[name].dir
    out = {}
    for fname in script_files():
        m = re.fullmatch(r"%s/f(\d+)\.json" % d, fname)
        if m:
            out[int(m[1])] = {int(e["id"].split(".")[1]): text_of(e, jp) for e in load(fname)}
    return out


def rom_texts(jp=False):
    """-> [(offset, max, text, translated)] for every plain ROM string and record name."""
    out = []
    for name in script_files():
        if name.startswith("rom/"):
            for e in load(name):
                out.append((int(e["id"][1:], 16), e["max"], text_of(e, jp), translated(e) and not jp))
    return out


def rom_ptrs():
    """{string offset: [pointer word offsets]} for every plain ROM string (romstr's sites, as extracted)."""
    out = {}
    for name in script_files():
        if name.startswith("rom/"):
            for e in load(name):
                out[int(e["id"][1:], 16)] = [int(p, 16) for p in e.get("ptrs", ())]
    return out


def stats():
    tot = done = 0
    for name in script_files():
        ents = load(name)
        n = sum(1 for e in ents if e["status"] != "data")
        d = sum(1 for e in ents if e["status"] != "data" and e["en"])
        tot, done = tot + n, done + d
        print("%-22s %5d entries %5d translated" % (name, n, d))
    print("total %d, translated %d" % (tot, done))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["dump", "stats"])
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.cmd == "dump":
        dump(ROM.read_bytes(), args.force)
    else:
        stats()


if __name__ == "__main__":
    main()
