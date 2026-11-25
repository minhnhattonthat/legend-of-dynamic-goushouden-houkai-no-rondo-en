"""Translation batches (docs/translator-brief.md): split untranslated text, check translator output, merge it back.

    python -X utf8 tools/batches.py split [--size 3500]   work/tl/bNNN.tsv and build/terms_bNNN.txt for untranslated JP
    python -X utf8 tools/batches.py check [bNNN ...]      a batch's .out.tsv; with no batch, all shipped English (for check.py)
    python -X utf8 tools/batches.py merge bNNN ... [--overwrite]   check, then write the English into script/
    python -X utf8 tools/batches.py fit "English body" [--form dlg]   wrap and measure one line, as check/merge will

Copied from the skill's assets/batches.py; the ADAPTER section is this game's (script/*/*.json, tools/lint.py rules).
Batch TSV: id, speaker, form, limit, JP. Output: work/tl/bNNN.out.tsv, id<TAB>English, every id once, same order.
In both, a line break is written as the two characters \\n (a blank line, \\n\\n, is a page break).
Dialogue (form dlg): the batch holds the message body only; the speaker line comes from tools/speakers.tsv at merge,
and each paragraph is word-wrapped to the dialogue box (lint.py budgets), so translators write sentences, not lines.
"""
import functools
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
TL = ROOT / "work/tl"
SCRIPT = ROOT / "script"
GLOSSARY = ROOT / "glossary.md"
SPEAKERS = ROOT / "tools/speakers.tsv"
MAX_ENTRIES = 150

# ---- ADAPTER: this game's text format ----
import fields  # noqa: E402
import lint  # noqa: E402

TOKEN = lint.TOKEN  # {p} {s} {g} {!R} {!W} [XX]: must survive translation
FREE = set()
VARIABLE = r"\{g\}"  # a value the game draws (item name / amount)
HONORIFICS = {"さん": "-san", "くん": "-kun", "君": "-kun", "ちゃん": "-chan", "様": "-sama", "先生": "-sensei"}
SKIP_PARTS = {"test"}  # data only


def speakers():
    """{JP name tag: EN name tag} from tools/speakers.tsv; {p} / {s} stand for themselves."""
    out = {"{p}": "{p}", "{s}": "{s}", "": ""}  # an empty first line: no name tag
    if SPEAKERS.exists():
        for line in SPEAKERS.read_text(encoding="utf-8").splitlines():
            if "\t" in line and not line.startswith("#"):
                jp, en = line.split("\t")[:2]
                out[jp] = en
    return out


def docs():
    """(path, part, entries) per script file; part is the subdirectory (archive, rom, book, desc, effect, place)."""
    for path in sorted(SCRIPT.glob("*/*.json")):
        if path.parent.name in SKIP_PARTS:
            continue
        yield path, path.parent.name, json.loads(path.read_text(encoding="utf-8"))


def needs_english(entry):
    """Empty JP isn't "untranslated"; data records and the sprite-drawn SFX names (phase 8) aren't batched."""
    return (bool(entry.get("jp", "").strip()) and not entry.get("en") and entry.get("status") != "data"
            and not entry["id"].startswith("x"))


def group_of(entry):
    return entry.get("dup") or entry["id"]


def form_of(part, entry):
    if part == "archive":
        return "dlg"
    if part == "rom":
        return "rom:" + ",".join(fields.category(entry) or ["misc"])
    return part


def limit_label(part, entry):
    if part == "archive":
        return "dlg %d/%d px a line, wrapped by the tool" % (lint.WINDOWS["dialogue"]["line1_px"],
                                                            lint.WINDOWS["dialogue"]["line2_px"])
    if part in lint.BOXES:
        w = lint.WINDOWS[lint.BOXES[part]]
        return "%d px x %d lines" % (w["px"], w["lines"])
    boxes = lint.rom_boxes(entry)
    px = min((lint.WINDOWS[b]["px"] for b in boxes), default=None)
    return "%d bytes" % entry["max"] + (", %d px" % px if px else "")


def jp_shown(part, entry):
    """What the translator sees: the archive message without its speaker line."""
    return entry["jp"].split("\n", 1)[1] if part == "archive" and "\n" in entry["jp"] else entry["jp"]


def greedy(words, first, budgets, widths, shrink=0):
    """Greedy word wrap; line i (counted from `first`) gets budgets[i % 2] - shrink px."""
    out, cur = [], ""
    for w in words:
        trial = (cur + " " + w) if cur else w
        if cur and lint.line_px(trial, widths) > budgets[(first + len(out)) % 2] - shrink:
            out.append(cur)
            cur = w
        else:
            cur = trial
    out.append(cur)
    return out


def wrap(body):
    """Word-wrap each paragraph of a dialogue body to the box: line budgets alternate line1/line2 px (2-line pages);
    a \\n the translator wrote is kept as a forced break. A paragraph whose last line would be a stub (lint.STUB)
    is re-wrapped balanced: the smallest uniform narrowing that keeps the line count and lengthens the last line."""
    widths = lint.char_widths()
    if widths is None:
        return body
    budgets = (lint.WINDOWS["dialogue"]["line1_px"], lint.WINDOWS["dialogue"]["line2_px"])
    paras = []
    for para in body.split("\n\n"):
        out = []
        forced = para.split("\n")
        for k, seg in enumerate(forced):
            lines = greedy(seg.split(" "), len(out), budgets, widths)
            if k == len(forced) - 1 and len(lines) > 1 and lint.is_stub(lines[-1]):
                for shrink in range(1, min(budgets)):
                    trial = greedy(seg.split(" "), len(out), budgets, widths, shrink)
                    if len(trial) != len(lines):
                        break
                    if not lint.is_stub(trial[-1]):
                        lines = trial
                        break
            out += lines
        paras.append(out)
    # The box has 2 rows and a blank line is an empty row, not a page break (issue #1; the JP only puts one after a
    # page's odd line): a paragraph that already fills its last page is followed by no blank, else the next page
    # would open on the bottom row.
    text = ""
    for k, out in enumerate(paras):
        if k:
            text += "\n\n" if len(paras[k - 1]) % 2 else "\n"
        text += "\n".join(out)
    return text


def final_en(part, entry, en):
    """The English as stored in script/: the dialogue speaker line from tools/speakers.tsv, body wrapped."""
    en = en.replace("\\n", "\n")
    if part != "archive":
        # the JP's edge blanks are layout (file-write tools strip a trailing space): restore one ASCII space
        jp = entry["jp"]
        if jp[:1] in (" ", "　") and en[:1] != " ":
            en = " " + en
        if jp[-1:] in (" ", "　") and en[-1:] != " ":
            en = en + " "
        return en
    if "\n" not in entry["jp"]:
        return en
    tag = entry["jp"].split("\n", 1)[0]
    return speakers().get(tag, "\x00missing speaker " + tag) + "\n" + wrap(en)


def width_problems(part, entry, en):
    errs, warns = [], []
    full = final_en(part, entry, en)
    if "\x00missing speaker" in full:
        return ["speaker %r has no line in tools/speakers.tsv" % entry["jp"].split("\n")[0]]
    lint.check_entry(dict(entry, en=full), part, errs, warns)
    return [m.split(": ", 1)[-1] for m in errs]


def encodable(char):
    return " " <= char <= "~" and char not in "\\`"
# ---- end of ADAPTER ----


@functools.lru_cache(maxsize=None)
def rx(pattern):
    """Compiled once: the glossary, Avoid and honorific patterns outnumber re's own 512-entry cache, and recompiling
    them made a full check take ~5 min."""
    return re.compile(pattern)


def kind(char):
    if "぀" <= char <= "ゟ":
        return "hiragana"
    if "゠" <= char <= "ヿ":
        return "katakana"
    if "一" <= char <= "鿿" or char == "々":
        return "kanji"
    return "other"


def has_term(jp, term):
    """term occurs as a whole kana or kanji run: ミン isn't in タイミング, くも isn't in ぼくも."""
    for m in rx(re.escape(term)).finditer(jp):
        a, b = m.start(), m.end()
        if (a == 0 or kind(jp[a - 1]) != kind(term[0])) and (b == len(jp) or kind(jp[b]) != kind(term[-1])):
            return True
    return False


def glossary():
    """[(JP forms, EN forms, avoid forms)] from glossary.md's | JP | EN | max | notes | Avoid | tables."""
    rows = []
    if not GLOSSARY.exists():
        return rows
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2 and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-: "):
            avoid = [x.strip() for x in cells[4].split("/") if x.strip()] if len(cells) > 4 else []
            rows.append(([x.strip() for x in cells[0].split("/")], [x.strip() for x in cells[1].split("/")], avoid))
    return rows


_SHORT = None


def short_forms():
    """{id: English} from script/short_forms.tsv: fields too narrow for the glossary form (D8); the glossary
    check accepts exactly that English for that id."""
    global _SHORT
    if _SHORT is None:
        path = ROOT / "script" / "short_forms.tsv"
        rows = [l.split("\t") for l in path.read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#")] if path.exists() else []
        _SHORT = {r[0]: r[1] for r in rows}
    return _SHORT


def names():
    """JP person names an honorific can follow: glossary rows plus name tags."""
    out = {j for jps, _, _ in glossary() for j in jps if j and kind(j[-1]) in ("kanji", "katakana")}
    return out | {k for k in speakers() if k and not k.startswith("{")}


def problems(part, entry, en, terms, people):
    """Every rule, on one line of English (escaped \\n breaks)."""
    jp = jp_shown(part, entry)
    if not en.strip():
        return ["empty English"]
    out = []
    plain = TOKEN.sub("", en.replace("\\n", "\n"))
    if bad := sorted({c for c in plain if not encodable(c) and c != "\n"}):
        out.append(f"unencodable characters {bad}")
    if re.search(r"\\u[0-9a-fA-F]{4}", en) or "\t" in en:
        out.append("escape sequence or tab in the English")
    want = Counter(t for t in TOKEN.findall(jp) if t not in FREE)
    have = Counter(t for t in TOKEN.findall(en) if t not in FREE)
    if want != have and entry.get("id") not in lint.CODES_OK:
        out.append(f"control codes differ: JP {dict(want)} EN {dict(have)}")
    if re.search(VARIABLE + r"(st|nd|rd|th)\b", en):
        out.append('ordinal suffix after a variable (write "No. {g}")')
    jp_plain = TOKEN.sub("", jp).replace("\\n", "").replace("\n", "")
    flat = re.sub(r"\s+", " ", en.replace("\\n", " ")).lower()  # a term may break across lines
    short = short_forms().get(entry["id"]) == en
    for jps, ens, avoid in terms:  # a D8 short form skips the required term, never the Avoid list
        if not short and any(has_term(jp_plain, j) for j in jps) and not any(e.lower() in flat for e in ens):
            out.append(f"glossary: {jps[0]} -> {ens[0]}")
        out += [f"glossary Avoid: {a}" for a in avoid if rx(rf"\b{re.escape(a)}\b").search(en)]
    for name in people:
        for jp_form, en_form in HONORIFICS.items():
            # 君達 / 君たち after a name is "you all" ("僕は 不動明\n君達は"), not -kun
            if name + jp_form not in jp_plain:
                continue
            hit = rx(re.escape(name + jp_form) + r"(?!達|たち)").search(jp_plain)
            if hit and en_form.lower() not in en.lower():
                out.append(f"honorific {name}{jp_form} needs {en_form}")
    return out + width_problems(part, entry, en)


def index():
    return {e["id"]: (part, e) for _, part, entries in docs() for e in entries}


def read_tsv(path):
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def existing():
    return sorted(TL.glob("b[0-9][0-9][0-9].tsv"))


def split(size):
    """Numbers on from the last batch and leaves out ids already batched, so a repeat run can't duplicate work.
    A batch never spans two script files (dialogue stays in story order, one archive file per batch or two)."""
    TL.mkdir(parents=True, exist_ok=True)
    (ROOT / "build").mkdir(exist_ok=True)
    taken = {r[0] for p in existing() for r in read_tsv(p)}
    n = max((int(p.stem[1:]) for p in existing()), default=0)
    spk = speakers()
    batches = []
    for path, part, entries in docs():
        groups = {}
        for e in entries:
            if needs_english(e) and e["id"] not in taken:
                groups.setdefault(group_of(e), []).append((part, e))
        cur, chars = [], 0
        for group in groups.values():
            c = sum(len(TOKEN.sub("", e["jp"])) for _, e in group)
            if cur and (chars + c > size or len(cur) + len(group) > MAX_ENTRIES):
                batches.append(cur)
                cur, chars = [], 0
            cur += group
            chars += c
        if cur:
            batches.append(cur)
    terms = glossary()
    for batch in batches:
        n += 1
        name = f"b{n:03d}"
        path = TL / f"{name}.tsv"
        if path.exists():
            sys.exit(f"{path} already exists")
        rows = []
        for part, e in batch:
            tag = e["jp"].split("\n", 1)[0] if part == "archive" else ""
            who = spk.get(tag, tag) if tag else ""
            jp = jp_shown(part, e).replace("\n", "\\n")
            rows.append(f"{e['id']}\t{who}\t{form_of(part, e)}\t{limit_label(part, e)}\t{jp}")
        path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        jps = " ".join(TOKEN.sub("", e["jp"]) for _, e in batch)
        used = [(j, ens[0]) for jpl, ens, _ in terms for j in jpl if has_term(jps, j)]
        (ROOT / f"build/terms_{name}.txt").write_text("".join(f"{j}\t{e}\n" for j, e in used)
                                                      or "(no glossary terms in this batch)\n", encoding="utf-8", newline="\n")
    print(f"{len(batches)} new batches in {TL}, {len(taken)} ids already batched")


def check_batch(batch, entries, terms, people):
    want = [r[0] for r in read_tsv(TL / f"{batch}.tsv")]
    rows = [(r[0], "\t".join(r[1:])) for r in read_tsv(TL / f"{batch}.out.tsv")]
    bad = []
    if [r[0] for r in rows] != want:
        got = [r[0] for r in rows]
        dup = sorted(i for i, c in Counter(got).items() if c > 1)
        bad.append(f"ids differ: missing {sorted(set(want) - set(got))[:8]} extra {sorted(set(got) - set(want))[:8]} "
                   f"duplicate {dup[:8]} (order must match too)")
    new = {}
    for eid, en in rows:
        if eid in entries:
            part, e = entries[eid]
            bad += [f"{eid}: {p}: {en!r}" for p in problems(part, e, en, terms, people)]
            new[eid] = final_en(part, e, en)
    return bad, new


def merge(new, overwrite):
    """Refuses to replace different English unless told to, before anything is written."""
    if not overwrite:
        for _, _, entries in docs():
            for e in entries:
                if e["id"] in new and e.get("en") and e["en"] != new[e["id"]]:
                    sys.exit(f"{e['id']} would lose {e['en']!r}: pass --overwrite if that is meant")
    changed = 0
    for path, _, entries in docs():
        touched = False
        for e in entries:
            if e["id"] in new and e.get("en") != new[e["id"]]:
                e["en"], e["status"] = new[e["id"]], "done"
                touched = True
                changed += 1
        if touched:
            path.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"merged: {changed} entries changed")


def fit(text, form):
    widths = lint.char_widths()
    out = wrap(text.replace("\\n", "\n")) if form == "dlg" else text.replace("\\n", "\n")
    for line in out.split("\n"):
        print("%4d px | %s" % (lint.line_px(line, widths) if widths else -1, line))


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "split":
        return split(int(args[args.index("--size") + 1]) if "--size" in args else 3500)
    if cmd == "fit":
        return fit(args[0], args[args.index("--form") + 1] if "--form" in args else "dlg")
    overwrite = "--overwrite" in args
    partial = "--partial" in args  # merge: write the ids that pass, leave failing ones untranslated (LONG names)
    batch_names = [a for a in args if a not in ("--overwrite", "--partial")]
    entries, terms, people = index(), glossary(), names()
    if cmd == "check" and not batch_names:
        bad = []
        for i, (part, e) in entries.items():
            if e.get("en") and needs_english(dict(e, en="")):
                body = e["en"].split("\n", 1)[1] if part == "archive" and "\n" in e["en"] else e["en"]
                bad += [f"{i}: {p}" for p in problems(part, e, body.replace("\n", "\\n"), terms, people)
                        if not p.startswith("line ")]
        print(f"{len(entries)} entries, {len(bad)} problems")
        print("\n".join(bad[:200]))
        return 1 if bad else 0
    if cmd not in ("check", "merge") or not batch_names:
        sys.exit(__doc__)
    new, failed = {}, 0
    for batch in batch_names:
        bad, rows = check_batch(batch, entries, terms, people)
        if partial and cmd == "merge" and not any(b.startswith("ids differ") for b in bad):
            failing = {b.split(":", 1)[0] for b in bad}
            rows = {k: v for k, v in rows.items() if k not in failing}
            print(f"{batch}: partial, {len(failing)} ids left out: {' '.join(sorted(failing))}")
            bad = []
        new.update(rows)
        failed += bool(bad)
        print(f"{batch}: " + ("OK" if not bad else f"{len(bad)} problems"))
        for line in bad:
            print("  " + line)
    if failed:
        return 1
    if cmd == "merge":
        merge(new, overwrite)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
