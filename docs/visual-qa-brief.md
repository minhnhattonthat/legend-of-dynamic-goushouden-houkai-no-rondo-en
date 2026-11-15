# Visual-QA reviewer brief - Legend of Dynamic Goushouden: Houkai no Rondo (GBA)

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything:
no edits to the repo, no git, no subagents. Under Orca there are no nested workers, so the controller runs this
brief through `tools/vqa.sh` (`codex exec -s read-only`, one call per chunk); the verdict lines come back as your
final message and the script writes them to `work/qa/verdicts/<chunk>.tsv`.

## Inputs
- A chunk: one `id<TAB>path` line per sheet, attached as images in that order. Look at every one; none may be
  skipped.
- Each sheet is one warp scene (`tools/debug/scenes.txt`, or `map_NNN` from `tools/debug/maps.tsv`): the English
  build's final frame on the **left**, the original Japanese ROM's on the **right**, both at 2x.
- `glossary.md` for names.

## Judge (left half only; the right half is the reference)
An `issue` is any of:
- Japanese text still visible on the left where it is text a player reads (not a logo: the 豪翔伝 logo stays);
- text overflowing a box, clipped by a frame, or running off screen;
- text off-centre where the original centres it: an option in its box, a label, a banner;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a one-word last line;
- an empty box where the original shows text;
- a name that differs from `glossary.md`.

Standing non-bugs (`ok`):
- text still typing out, a box mid-fade or mid-scroll, a cursor mid-blink; the two halves caught at slightly
  different moments (the English build's text pages differ in length);
- a map or scene still loading after a warp, a black or identical frame on both sides;
- anything that looks the same in the original (right half);
- the leftover debug menus (デバックＭＥＮＵ and its sub-menus, map/BGM/SE test lists) are developer screens: Japanese
  there is `ok` unless the scene is a real game screen reached through them;
- graphics-text rows still listed as to do in `docs/re/graphics.md` (menu captions S1, battle UI S4, lettering S5,
  shop signs S7) are known: mark them `issue` only with the note `gfx S<n>` so they are not lost, nothing more.
- "(C)" for the copyright sign on the title is intended.

## Verdicts
Your final message is the verdict list and nothing else, one line per sheet in the chunk, in order:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which part of the screen, which text, what is wrong).
