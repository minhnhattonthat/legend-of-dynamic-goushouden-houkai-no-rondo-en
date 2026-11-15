# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| (none) | text fonts are the game's own ASCII glyphs (VWF widths only, `tools/engine.py`) | - | - | dialogue, menus | - |
| fonts/Silkscreen-Regular.ttf | github.com/google/fonts ofl/silkscreen (main, 2026-11-16) | OFL 1.1 (fonts/Silkscreen-OFL.txt) | yes, as rendered glyphs | title: LEGEND OF DYNAMIC, HOUKAI NO RONDO (8 px, its native size, no AA) | - |
| fonts/Cinzel[wght].ttf | github.com/google/fonts ofl/cinzel (main, 2026-11-16) | OFL 1.1 (fonts/Cinzel-OFL.txt) | yes, as rendered glyphs | title subtitle "Rondo of Ruin" (Bold, 12 px, no AA) | - |
