# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| (none) | text fonts are the game's own ASCII glyphs (VWF widths only, `tools/engine.py`) | - | - | dialogue, menus | - |
| fonts/Silkscreen-Regular.ttf | github.com/google/fonts ofl/silkscreen (main, 2026-11-16) | OFL 1.1 (fonts/Silkscreen-OFL.txt) | yes, as rendered glyphs | title: LEGEND OF DYNAMIC, HOUKAI NO RONDO (8 px, its native size, no AA) | - |
| fonts/Cinzel[wght].ttf | github.com/google/fonts ofl/cinzel (main, 2026-11-16) | OFL 1.1 (fonts/Cinzel-OFL.txt) | yes, as rendered glyphs | title subtitle "Rondo of Ruin" (Bold, 12 px, no AA) | - |
| fonts/PressStart2P-Regular.ttf | github.com/google/fonts ofl/pressstart2p (main, 2026-11-16) | OFL 1.1 (fonts/PressStart2P-OFL.txt; Reserved Font Name, unmodified file) | yes, as rendered glyphs | screen-title pills and the shop/money plates (8 px, its native size, no AA): `tools/gfxlabel.py` class `head` | - |
| fonts/Bangers-Regular.ttf | github.com/google/fonts ofl/bangers (main, 2026-11-16) | OFL 1.1 (fonts/Bangers-OFL.txt) | yes, as rendered glyphs | battle SFX cut-in letters A-Z ! (32x32 OBJ glyphs, 22 px caps widened 1.4x, no AA): `tools/gfx_sfx.py` | - |
| tools/pixfont.py | drawn for this project (2026-11-16) | own work, no restriction | yes | menu tabs, buttons, column heads, battle commands (6-px bold caps) and a 3x5 set for tight labels: classes `small`, `btn`, `tiny` | - |
