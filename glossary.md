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
| 幻城 | Mirage Castle | | | Phantom Castle |
| 死神警察 | Reaper Police | | 署 -> Reaper Police HQ | Death Police / Shinigami Police |
| 震災とりで | Quake Fort | | | |
| 暗黒寺 | Dark Temple | | | |
| 戸来村 | Herai Village | | | |
| 間身井薬局 / マミー薬局 | Mamii Pharmacy | | | |
| 魔王の城 | Demon King's Castle | | | |
| 妖怪屋敷 | Yokai Mansion | | | |
| 科学都市 | Science City | | | |
| 迷いの森 | Lost Forest | | | |
| 聖チャペル学園 | St. Chapel Academy | | | |
| 蓮沼 | Hasunuma | | | |
| 早乙女研究所 | Saotome Lab | | | |
| 日本アルプス | Japanese Alps | | | |
| ハレンチ学園 | Harenchi Gakuen | | | |
| 地獄別荘 | Hell Villa | | | |
| 関東地獄地震 | Kanto Hellquake | | | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| デーモン / デーモン族 | Demon / Demon race | | Devilman's Demons, capitalised | |
| ハチュウ人類 | Reptilian | | Getter's Dinosaur Empire people | |
| メカザウルス | Mechasaurus | | | |
| ボスボロット | Boss Borot | | | |
| アフロダイＡ | Aphrodite A | | | |
| ジェットスクランダー | Jet Scrander | | | |
| ミケーネ | Mykene | | | |
| バードス | Bardos | | | |
| 超合金Ｚ | Super Alloy Z | | | |
| ゲッター線 | Getter Rays | | | |
| ゲットマシン | Getter Machines | | | |
| 空中元素固定装置 | Airborne Element Fixer | | Honey's device | |
| あしゅら軍団 | Ashura Corps | | | |
| 鉄十字軍団 | Iron Cross Corps | | | |
| 次元神グレイド / 次元獣グレイド | Dimension God Grade / Dimension Beast Grade | | | |
| アイアンカイザー | Iron Kaiser | | | |
| シャフト博士 | Dr. Shaft | | | |
| 悪馬尻 | Abashiri | | the Abashiri family | |
| アソート | party | | "joined the party" | |
| 状態異常 | ailment | | Stone/Freeze/Charm/Confuse/Blind/Poison/Curse; 戦闘不能 KO | |
| 悪魔 | demon / devil | | | |
| 鬼獄界 | Kigoku World | | Shutendoji's world of oni | |
| 鬼仏衆 | Kibutsu Clan | | oni descendants hunting Jiro | |
| 次元牢獄 | Dimension Prison | | | |
| 破壊の月 | Moon of destruction | | {s}'s role for Grade; keep the quotes the JP has | |
| 再生の太陽 | Sun of rebirth | | {p}'s role for Grade | |
| 予知一族 | Precog Clan | | Herai Village prophets (Maria) | |
| 妖怪パトロール | Yokai Patrol | | Enma-kun's team | |
| 地獄門 | Hell Gate | | | |
| 不死団 | Immortal Corps | | Susano-oh's psychic radicals | |
| 黒い魔物 | black fiend | | the revived "Ma" remains | |
| 九龍 | Kuryu | | Kuryu Valley / Kuryu Castle (Miroku) | |
| 真田忍者 | Sanada ninja | | | |

## Decisions from earlier batches
- 魔王 alone = the Demon King (Grade). 魔王ダンテ = Demon Lord Dante (keeps the two apart).
- 魔 (Susano-oh's evil energy) = "Ma" in quotes where the JP has 「魔」.
- 家早 / 果扨 families (Iyahaya Nanyu): Nanyu Iyahaya, Sayoko Iyahaya; Doshita / Nijija Hatesa. Nanyu's tic
  イヤハヤ なんとも stays romanised ("Iyahaya... nantomo...") because it is his name pun.
- 女蛮子 = Banji Suke ("Sukeban"; he introduces himself as 姓はスケ 名はバンジ); 蛮千代 = Banchiyo Suke.
- 身堂竜馬 = Ryoma Shindo (matches the name tag). 鬼谷 = Onitani in dialogue (name tag), item/enemy data has Kitani.
- Go Nagai cameo keeps his でガス tic as ", gasu"; Chapeau-jii's ジャジャ as ", jaja".
- ハチの巣入道 = Beehive Nyudo in dialogue (name tag); the 9-char enemy field abbreviates it.
