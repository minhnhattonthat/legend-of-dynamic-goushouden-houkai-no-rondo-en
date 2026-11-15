# Glossary - Legend of Dynamic Goushouden: Houkai no Rondo

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
`tools/batches.py check` enforces the tables: a JP term in a line needs one of its EN forms (`/` separates
alternatives) and no Avoid spelling. Name tags (speaker lines) come from `tools/speakers.tsv`, not from translators.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Enma-kun, Akira-kun, Honey-san, Princess Yukiko-sama only where JP has 様).
  Name order: Western (given name first). The check enforces -san/-kun/-chan/-sama/-sensei after known names.
- Romanisation source: official English names where they exist (Seven Seas / Discotek / anime subtitles), else
  Hepburn without macrons (Fudo, Jubei, Goki).
- Credits: English.
- Register: a Go Nagai crossover. Lively, punchy shonen-manga English: heroes casual and brash, villains theatrical,
  old men and demons archaic where the JP is (じゃ/のう/わし -> "I say", "my boy", "eh?"). Gags stay gags, crude
  jokes stay crude (it is Go Nagai), no censoring.
- Sound effects in dialogue: romanised and punchy English onomatopoeia (ドカーン -> "KABOOM!", ゴゴゴ -> "Rumble...").
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening.

## Style rules
- Punctuation map: 「」 -> "...", 『』 -> '...', … / ・・・ -> ..., ！？ -> ?!, ～ (long vowel) -> drop or stretch
  the word ("Kyaaa!"), ＆ -> &, full-width digits -> ASCII digits.
- Stutters: "う うん" -> "Y-yeah". Ellipsis lines "…！" -> "...!".
- ASCII only. No backslash (draws as yen), no backtick, no curly quotes, no em dash (use "--" sparingly or "...").
- Voices: see docs/style-reference.md.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 如月ハニー / ハニー | Honey | | Honey Kisaragi (Cutie Honey). Lead of route A. Cheerful, confident, a bit flirty | |
| キューティーハニー | Cutie Honey | | her transformed form | |
| 不動明 | Akira | | Akira Fudo (Devilman). Lead of route B. Kind, earnest; tough once Devilman | |
| デビルマン | Devilman | | | |
| 飛鳥了 | Ryo | | Ryo Asuka. Cool, aloof, calls Akira by name | |
| 早見青児 / 青児 | Seiji | | Seiji Hayami (Cutie Honey). Cocky reporter type | |
| 団兵衛 | Danbei | | Danbei Hayami, Seiji's father, old-man speech | |
| 如月博士 | Dr. Kisaragi | | Honey's father | |
| シスター・ジル | Sister Jill | | Panther Claw boss (Cutie Honey) | |
| パンサークロー | Panther Claw | | | |
| えん魔くん / えん魔 | Enma | | Enma-kun (Dororon Enma-kun); write "Enma-kun" where JP has くん | |
| 閻魔大王 | Great King Enma | | | |
| 雪子姫 | Princess Yukiko | | | |
| シャッポじい | Chapeau-jii | | talking hat, old-man speech | |
| カパエル | Kapaeru | | kappa-frog, ends lines with "kero"-style croak if JP does | |
| 兜甲児 / 甲児 | Koji | | Koji Kabuto (Mazinger Z). Hot-blooded | |
| マジンガーＺ / マジンガーZ | Mazinger Z | | | |
| 兜十蔵 | Juzo Kabuto | | | |
| 弓教授 | Professor Yumi | | | |
| 弓さやか / さやか | Sayaka | | Sayaka Yumi | |
| ボス | Boss | | Mazinger's Boss; with Mucha and Nuke | |
| ドクター・ヘル | Dr. Hell | | | |
| あしゅら男爵 / あしゅら | Ashura | | Baron Ashura | |
| ブロッケン伯爵 | Count Brocken | | | |
| 機械獣 | Mechanical Beast | | | |
| 光子力研究所 | Photon Power Laboratory / Photon Power Lab | | | |
| 早乙女博士 | Dr. Saotome | | Getter Robo | |
| リョウ | Ryo | | Ryoma Nagare (Getter); JP uses the nickname | |
| 隼人 | Hayato | | Hayato Jin | |
| 武蔵 | Musashi | | Musashi Tomoe, country-boy speech | |
| ゲッターロボ / ゲッター | Getter Robo / Getter | | | |
| 恐竜帝国 | Dinosaur Empire | | | |
| 子郎 | Jiro | | Jiro Shutendo (Shutendoji) | |
| 朱紗 | Shusha | | Shingo Shusha (Susano-oh) | |
| 凄ノ王 | Susano-oh | | | |
| ジャック | Jack | | Violence Jack | |
| スラムキング | Slum King | | | |
| けっこう仮面 | Kekko Kamen | | | |
| ダンテ | Dante | | Mao Dante | |
| 宇津木涼 | Ryo Utsugi | | | |
| シレーヌ | Sirene | | | |
| 美樹 | Miki | | | |
| ゼノン | Zennon | | | |
| 十兵衛 | Jubei | | Jubei Yagyu (Harenchi Gakuen) | |
| ヒゲゴジラ | Higegodzilla | | | |
| グレイド | Grade | | | |
| 美勒 | Miroku | | | |
| 永井豪 | Go Nagai | | | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 始まりの丘 | Hill of Beginnings | | the meeting point in the prologue | |
| 関東 | Kanto | | | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| デーモン / デーモン族 | Demon / Demon race | | Devilman's Demons, capitalised | |
| 悪魔 | demon / devil | | | |

## Decisions from earlier batches
- (none yet)
