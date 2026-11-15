"""lint.py: text lint over script/ (run by tools/check.py; exit 1 on any error).

  python -X utf8 tools/lint.py [--warn]     errors + a one-line summary; --warn also lists the warnings

Per translated entry (en non-empty, status not "data"):
  - ASCII only, no Japanese left; no `\\` (draws as the yen sign) or backtick (draws as a space); no literal `!R` / `!W`
    (the printer reads them as codes; write {!R} / {!W} only where the JP has them)
  - control codes: the multiset of {p} {s} {g} {!R} {!W} [XX] equals the JP's
  - leading / trailing blanks and blank lines (page breaks) match the JP
  - script archive: the speaker line fits the name tag (tools/windows.json name_tag); body lines fit the dialogue
    budget in px (line 1 / line 2 of each 2-line page, engine.half_widths; {p}/{s} count as name_var px)
  - book / desc archives (script/book, script/desc): lines and px per line within their box (windows.json book,
    desc; the book in the 12-px font, as it is inserted fullwidth); the book's 511-byte buffer is checked by build.py
  - ROM strings: encoded bytes <= max unless the string has pointers (build.py relocates it then); px within every windows.json box whose `categories`
    include one of the string's record tables (tools/fields.py TABLES: item_list, battle_name, ...)
  - archive paragraphs: a stub last line (< 6 chars) in a multi-line paragraph fails, unless the id is in
    script/keep_stub.txt (batches.py wrap re-wraps balanced to avoid them)
Per untranslated entry (non-empty jp, empty en, status not "data"): fails unless its id is in script/keep_jp.txt
(`id<TAB>reason`).
Warnings (summary count; --warn lists them): none at present.
"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import engine  # noqa: E402
import extract  # noqa: E402
import fields  # noqa: E402
import sjis  # noqa: E402

TOKEN = re.compile(r"\{(?:p|s|g|!R|!W)\}|\[[0-9A-F]{2}\]")
JP = re.compile(r"[぀-ヿ一-鿿＀-￯　-〿]")
WINDOWS = json.loads((ROOT / "tools" / "windows.json").read_text(encoding="utf-8"))
_WIDTHS = None


def char_widths():
    """{ascii char: advance px} in the half-width font, from the original ROM (None without a dump)."""
    global _WIDTHS
    if _WIDTHS is None:
        if not extract.ROM.exists():
            return None
        rom = extract.ROM.read_bytes()
        pairs = engine.ascii_pairs(rom)
        hw = engine.half_widths(rom)
        _WIDTHS = {chr(c): hw.get(p, engine.HALF_ADV) for c, p in pairs.items()}
    return _WIDTHS


_WIDTHS12 = None


def char_widths12():
    """{ascii char: advance px} in the 12-px font (fullwidth Latin through the VWF delta table: wide archives)."""
    global _WIDTHS12
    if _WIDTHS12 is None:
        if not extract.ROM.exists():
            return None
        w = engine.widths(extract.ROM.read_bytes())
        _WIDTHS12 = {chr(c): w.get(sjis.encode(sjis.fullwidth(chr(c))), 12) for c in range(0x20, 0x7F)}
    return _WIDTHS12


# script/<dir> -> tools/windows.json box for the archives after the script archive (docs/re/text.md §1b)
BOXES = {"book": "book", "desc": "desc", "place": "place_name", "effect": "effect"}


def lint_box(e, box, errs):
    """A message shown in a fixed box: at most `lines` lines (blank ones count), each within `px` in the box's font;
    blank lines stay where the JP has them (the book: name, 2 blank lines, description)."""
    win = WINDOWS[box]
    widths = {"8": char_widths8, "12": char_widths12}.get(win["font"], char_widths)()
    el, jl = e["en"].split("\n"), e["jp"].split("\n")
    if len(el) > win["lines"]:
        errs.append("%s: %d lines, the %s box holds %d" % (e["id"], len(el), box, win["lines"]))
    blanks = lambda ls: [i for i, s in enumerate(ls) if not s.strip()]  # noqa: E731
    if blanks(el) != blanks(jl):
        errs.append("%s: blank lines must stay where the JP has them (%s)" % (e["id"], blanks(jl)))
    if widths is not None:
        for line in el:
            px = line_px(line, widths)
            if px > win["px"]:
                errs.append("%s: line %r is %d px, the %s box holds %d" % (e["id"], line, px, box, win["px"]))


def line_px(line, widths):
    var = WINDOWS["name_var"]["px"]
    px = 0
    for part in re.split(r"(\{[^}]*\}|\[[0-9A-F]{2}\])", line):
        if part in ("{p}", "{s}"):
            px += var
        elif part == "{g}":
            px += WINDOWS["g_var"]["px"]
        elif part.startswith("{") or part.startswith("["):
            continue
        else:
            px += sum(widths.get(ch, 12) for ch in part)
    return px


def codes(text):
    return collections.Counter(TOKEN.findall(text))


def common(e, errs):
    en, jp = e["en"], e["jp"]
    bare = TOKEN.sub("", en)
    if JP.search(en):
        errs.append("%s: Japanese left in en" % e["id"])
    bad = sorted({ch for ch in bare if not (" " <= ch <= "~" or ch == "\n") or ch in "\\`"})
    if bad:
        errs.append("%s: characters the font can't draw: %r" % (e["id"], "".join(bad)))
    if "!R" in bare or "!W" in bare:
        errs.append("%s: literal !R / !W (a printer code); reword" % e["id"])
    if codes(en) != codes(jp):
        errs.append("%s: control codes differ: jp %s en %s" % (e["id"], dict(codes(jp)), dict(codes(en))))
    lead = lambda s: len(s) - len(s.lstrip(" 　\n"))  # noqa: E731
    trail = lambda s: len(s) - len(s.rstrip(" 　\n"))  # noqa: E731
    if bool(lead(jp)) != bool(lead(en)) or bool(trail(jp)) != bool(trail(en)):
        errs.append("%s: leading/trailing blanks differ from the JP" % e["id"])


def lint_archive(e, widths, errs, warns):
    en, jp = e["en"], e["jp"]
    el, jl = en.split("\n"), jp.split("\n")
    if (el[0] == "{p}") != (jl[0] == "{p}") or (el[0] == "{s}") != (jl[0] == "{s}"):
        errs.append("%s: speaker line must stay %s" % (e["id"], jl[0]))
    if len(sjis.encode(el[0])) > WINDOWS["name_tag"]["bytes"]:
        errs.append("%s: speaker %r over the name tag's %d bytes" % (e["id"], el[0], WINDOWS["name_tag"]["bytes"]))
    if [s for s in jl[1:-1] if not s.strip()] and not [s for s in el[1:-1] if not s.strip()]:
        errs.append("%s: the JP has page breaks (blank lines), the en none" % e["id"])
    body = "\n".join(el[1:])
    for para in body.split("\n\n"):
        lines = para.split("\n")
        for k, line in enumerate(lines):
            if widths is not None:
                budget = WINDOWS["dialogue"]["line1_px" if k % 2 == 0 else "line2_px"]
                px = line_px(line, widths)
                if px > budget:
                    errs.append("%s: line %r is %d px, page line %d holds %d" % (e["id"], line, px, k % 2 + 1, budget))
        if len(lines) > 1 and is_stub(lines[-1]) and e["id"] not in keep("keep_stub.txt"):
            errs.append("%s: stub last line %r (re-wrap or reword; keep-list: script/keep_stub.txt)" % (e["id"], lines[-1]))


STUB = 6  # a paragraph's last line under this many characters is a stub


def is_stub(line):
    """{p} / {s} / {g} draw a name or value, never a stub on their own: they count as STUB characters."""
    return len(re.sub(r"\{(?:p|s|g)\}", "x" * STUB, line).strip()) < STUB


_KEEP = {}


def keep(name):
    """Ids in script/<name>: `id<TAB>reason` lines, `#` comments (keep_jp.txt, keep_stub.txt)."""
    if name not in _KEEP:
        path = ROOT / "script" / name
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        _KEEP[name] = {l.split("\t")[0].strip() for l in lines if l.strip() and not l.startswith("#")}
    return _KEEP[name]


_WIDTHS8 = None


def char_widths8():
    """{ascii char: advance px} in the 8x8 menu font (8-px VWF)."""
    global _WIDTHS8
    if _WIDTHS8 is None:
        if not extract.ROM.exists():
            return None
        rom = extract.ROM.read_bytes()
        pairs = engine.ascii_pairs(rom)
        w8 = engine.eight_widths(rom)
        _WIDTHS8 = {chr(c): w8.get(p, engine.EIGHT_ADV) for c, p in pairs.items()}
    return _WIDTHS8


def rom_boxes(e):
    """windows.json boxes whose `categories` (tools/fields.py TABLES) include one of this ROM string's tables."""
    cats = set(fields.category(e))
    return [k for k, w in WINDOWS.items() if isinstance(w, dict) and cats & set(w.get("categories", ()))]


def lint_rom(e, errs):
    off = int(e["id"][1:], 16)
    text = sjis.fullwidth(e["en"]) if off in extract.FULLWIDTH else e["en"]
    n = len(sjis.encode(text))
    if n > e["max"] and not e.get("ptrs"):  # with pointers, build.py relocates it (insert_rom_strings)
        errs.append("%s: %d bytes, room for %d and no pointer to relocate it" % (e["id"], n, e["max"]))
    for box in rom_boxes(e):
        win = WINDOWS[box]
        widths = {"8": char_widths8, "12": char_widths12}.get(win.get("font"), char_widths)()
        if widths is not None:
            px = line_px(e["en"], widths)
            if px > win["px"]:
                errs.append("%s: %r is %d px, the %s field holds %d" % (e["id"], e["en"], px, box, win["px"]))


def check_entry(e, part, errs, warns):
    """Every rule on one translated entry; part = its script/ subdirectory (archive, book, rom, ...)."""
    common(e, errs)
    if part == "archive":
        lint_archive(e, char_widths(), errs, warns)
    elif part in BOXES:
        lint_box(e, BOXES[part], errs)
    elif "max" in e and e["id"].startswith("r"):
        lint_rom(e, errs)


def run(show_warn=False):
    widths = char_widths()
    errs, warns = [], []
    done = todo = 0
    for path in sorted((ROOT / "script").glob("*/*.json")):
        for e in json.loads(path.read_text(encoding="utf-8")):
            if e.get("status") == "data" or not e["jp"].strip():
                continue
            if not e["en"]:
                todo += 1
                if e["id"] not in keep("keep_jp.txt"):
                    errs.append("%s: Japanese with no English (translate it, or list it in script/keep_jp.txt with "
                                "the reason)" % e["id"])
                continue
            done += 1
            check_entry(e, path.parent.name, errs, warns)
    for m in errs:
        print("ERROR", m)
    if show_warn:
        for m in warns:
            print("warn ", m)
    print("lint: %d translated, %d to do, %d errors, %d warnings%s" % (
        done, todo, len(errs), len(warns), "" if widths else " (no ROM: widths not checked)"))
    return not errs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--warn", action="store_true")
    sys.exit(0 if run(ap.parse_args().warn) else 1)


if __name__ == "__main__":
    main()
