# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

All of D1-D7 came with the one-shot run brief from the owner (Orca coordinator), as standing answers for every game.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-15 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner's standing answer. |
| D2 | 2026-11-15 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-11-15 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-15 | Abbreviations | engine work first (default), abbreviate | Engine work first (skill default; not overridden). |
| D5 | 2026-11-15 | Graphics text left in Japanese | none (default), list | Translate all (titles, menus, banners, cards); keep the original Japanese logo only if it has no official English version. |
| D6 | 2026-11-15 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through every checkpoint without asking. |
| D7 | 2026-11-15 | Existing saves / savestates | user's saves, none | None provided; build the debug tool as usual. |
| D8 | 2026-11-16 | Names wider than their menu field after relocation (D4 last resort; pre-approved run, worker's call) | widen fields (move the HP gauge / count column / DP column: the item list is two fixed columns), tight kerning (letters touch), a smaller font, short forms | Short forms, listed with the field in `script/short_forms.tsv` (glossary check accepts exactly those) and `work/qa/review/fixes5.tsv`: Initial. Surname for rec18 person names (item list 69 px), natural short names for char_short (48 px) and skills (72 px), e.g. "King Enma", "G.Tomahawk" (the JP's own Ｇ・トマホーク). Full names stay in dialogue and wherever no narrow field shows them. Bytes no longer limit anything with a pointer: build.py relocates it. |
