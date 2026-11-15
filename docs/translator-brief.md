# Translator brief - Legend of Dynamic Goushouden: Houkai no Rondo (GBA, 2002)

You translate part of the Japanese script of this Go Nagai crossover RPG into English for a fan patch. Heroes from
Cutie Honey, Devilman, Mazinger Z, Getter Robo, Dororon Enma-kun, Violence Jack and more meet when a black moon
merges their worlds; the player `{p}` and his girlfriend `{s}` travel with them. Tone: lively shonen manga, gags
and Go Nagai crudeness intact.
Work only on the batches named in your dispatch, one at a time in the order given, each to a passing check before
the next. Do all translation yourself; do not dispatch subagents. Edit nothing but your own `.out.tsv` files.

## Read first
1. `docs/style-reference.md` - character voices and approved example pairs. Match this voice.
2. `build/terms_<batch>.txt` - binding glossary rows for this batch (full table in `glossary.md` if you need more).
3. `docs/synopsis.md` - premise, routes, who is who. Don't give a later reveal away.

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`. A line break inside a message is written `\n`; a blank line
(`\n\n`) is a new page. Lines are in story order: use neighbours for context.
- form `dlg`: dialogue. The speaker column is the name tag (already English; `{p}` = player, `{s}` = girlfriend);
  the tag is added by the tool, so translate only the body. Write sentences: the tool word-wraps each page to the
  box (~40 characters a line, 2 lines show at a time, longer pages scroll). Keep each `\n\n` page break where the
  JP has one; drop the JP's single `\n` line breaks (they were only the JP wrap) except in choice lists
  (`はい\nいいえ\n` -> `Yes\nNo\n`, one option per line, keep a trailing `\n` if the JP has one).
- form `book` / `desc` / `effect` / `place` / `rom:...`: fixed boxes, NOT wrapped by the tool. Keep the JP's line
  structure (same number of lines, blank lines where the JP has them) and fit the limit column (px per line in
  the game's variable-width font: about 6 px a character for dialogue/book letters, 5-8 px in the 8-px menu font;
  `bytes` = ASCII characters). `rom:` strings are names and menu words: the category says where they show
  (skill_name = skill, enemy_name = enemy, char_name / char_short = character names, rec18 = items/equipment,
  item_desc_rom = item description, map_name = map name, misc = menu/system words).
- Measure before writing: `python -X utf8 tools/batches.py fit "text" --form dlg` (or `--form rom`) prints px per
  line.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: straight quotes, `...`; no tabs inside the
English, no Japanese or fullwidth characters, no backslash except the `\n` escape, no backtick, no `\uXXXX`.
Copy every control code exactly: `{p}` `{s}` (names), `{g}` (obtained item name or amount), `{!R}`...`{!W}`
(phone / radio voice), `[XX]` (two hex digits).

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root and fix every reported id until it prints
OK. Over-limit lines in fixed boxes: rephrase (keep the meaning; never abbreviate a name or term), and if it truly
can't fit, keep the meaning and report `LONG: id`.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese
  doesn't state; don't summarise or skip. Adapt wordplay so the joke still lands (no translator notes).
- Keep the speaker audible. JP register markers carry voice and must turn into English devices, not vanish:
  old men's じゃ/のう/わし ("eh?", "my boy", "I say"), rough men's ぜ/ねぇ/っス ("ain't", "ya", "dammit", clipped
  grammar), feminine かしら/わよ/のね ("I wonder...", "you know"), villains' 貴様/～め ("you wretch", "fools").
  A line any speaker could have said is a mistake.
- Names and terms exactly as in the glossary; official English names of the source manga/anime where they exist
  (Koji Kabuto, Baron Ashura, Dr. Hell, Sirene, Kekko Kamen), else Hepburn without macrons, given name first.
- Honorifics kept, hyphenated, after names that have them in JP: 明君 -> Akira-kun, 美樹ちゃん -> Miki-chan,
  ハニーさん -> Honey-san, 〜様 -> -sama, 〜先生 -> -sensei. Not on common nouns (おじいさん = "old man/grandpa").
  The check enforces this for known names.
- Punctuation: 「」 -> "...", 『』 -> '...', … -> ..., ！？ -> ?! or !?, ～ -> stretch the word ("Kyaaa!").
- No suffix glued to `{g}` or `{p}` (no "{g}s", "{p}'s" is fine), no a/an right before `{g}`.
- Sound effects: punchy English or romanised onomatopoeia ("KABOOM!", "Rumble rumble...").

## Consistency
Never edit `glossary.md`, `tools/speakers.tsv` or anything under `tools/`. For a recurring name or term not in the
glossary, pick a form, use it consistently, and report it.

## Report (reply with only this, short)
Per batch: id count and OK; then only these lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
