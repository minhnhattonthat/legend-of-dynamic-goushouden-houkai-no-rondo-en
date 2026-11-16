# Synopsis (for translators and reviewers)

Built from the extracted script (speaker counts per file, the prologue read in full) and the source series. The
script decides the wording; this file only says who is who and where the story goes. Extend it as batches reveal
more (controller only).

## Premise
A Go Nagai crossover RPG (Dynamic Pro). The player character `{p}` (a boy, first person 僕 "I", gentle, a little
timid) and his girlfriend `{s}` (first person あたし, bossy, quick-tempered, sweet underneath) are on a date in a
park when a **black moon** swells in the sky ("When the black moon shines, let us meet" arrives as an e-mail on
the phones of everyone it summons). An earthquake, and the **Dimension Chain** (次元連鎖) begins "again": worlds of
different Go Nagai manga collide. They wake on the **Hill of Beginnings** (始まりの丘) beside Akira Fudo and Honey
Kisaragi, who are both called away by phone (Ryo Asuka to the left path, Dr. Kisaragi to the right). The party splits
into **Team Akira** and **Team Honey**, agreeing to meet back on the hill.

## Files (script/archive fNN; one batch is roughly one file, in story order inside a file)
- f00-f01: prologue, the team split, system messages (`{g}` = item / amount obtained).
- Honey route (approx. f01-f36): Dr. Kisaragi's lab, Panther Claw and Sister Jill; Seiji and Danbei Hayami;
  Ryoma / Mondo; Violence Jack's Kanto; Harenchi Gakuen (Jubei, Yamagishi, Higegodzilla); Dororon Enma-kun (Enma,
  Great King Enma, Chapeau-jii, Kapaeru, Princess Yukiko); Mazinger Z (Koji, Professor Yumi, Sayaka, Boss, Dr. Hell,
  Baron Ashura's male/female halves); Shutendoji (Jiro, the Kibutsu Clan, Goki, Onitani); Susano-oh (Shusha,
  Shinichi, Uryu, Maria, Mitsurugi, Yukishiro); the Immortal Corps; Grade (a recurring enemy); Kekko Kamen; Mao
  Dante; Dr. Pochi / Iron Kaiser comedy; Slum King and Slum Queen.
- Akira route (approx. f37-f50): Akira and Ryo, Ryu Takuma, Jack, the Abashiri-family style gangs (Kikunosuke,
  Naojiro), Getter Robo (Dr. Saotome, Ryo / Hayato / Musashi, the Reptilians of the Dinosaur Empire and Emperor
  Gore), Devilman's Sirene, Miki; Miroku and a Mysterious Man behind events.
- f51-f53: side towns and inns, optional NPCs.
- Book (script/book): the in-game encyclopedia of characters and their source manga / creators.

## Chapters (story pass: `tools/story.py` reads these lines; archive files in message order, which follows the story
only roughly: event scripts of one area sit together, side events interleave)
- ch01 f00-f02: Prologue, the team split, Dr. Kisaragi's lab, Ryoma and Mondo
- ch02 f03-f05: Violence Jack's Kanto, Seiji, Harenchi Gakuen (Jubei, Yamagishi)
- ch03 f06-f08: Dororon Enma-kun, Jiro and the Kibutsu Clan
- ch04 f09-f10: Mazinger Z (Koji, Professor Yumi, Baron Ashura)
- ch05 f11-f13: Shutendoji's village, the Immortal Corps, Shusha and Mitsurugi
- ch06 f14-f17: Susano-oh (Shusha, Shinichi, Uryu, Maria)
- ch07 f18-f20: Detective comedy (Iboji, Tamatama), Sister Jill, Shinichi and Shusha
- ch08 f21-f24: Grade, Dr. Hell, Professor Yumi's lab
- ch09 f25-f29: Riots, the masked ???, Grade again, regrouping with Akira
- ch10 f30-f32: Miroku, Kedaman and Dorano, Kekko Kamen
- ch11 f33-f36: Dr. Pochi and Iron Kaiser, Mao Dante, Sister Jill's end, Slum King and Queen
- ch12 f37-f41: Akira route: Akira and Ryo, Ryu Takuma, Jack, Kikunosuke and Naojiro
- ch13 f42-f44: Getter Robo (Dr. Saotome, Ryo, Hayato, Musashi)
- ch14 f45-f47: Sirene and Miki, the Dinosaur Empire
- ch15 f48-f50: Finale: the ??? man, Miroku
- ch16 f51-f53: Side towns, inns, optional NPCs

## Who is who (voice in docs/style-reference.md)
- Honey Kisaragi: android heroine of Cutie Honey, boarding-school girl, bright and confident ("Honey Flash!").
- Akira Fudo: gentle boy who becomes Devilman; Ryo Asuka his cool, commanding best friend (the late Devilman
  reveal about Ryo must not be spoiled by early lines).
- Koji Kabuto (Mazinger Z pilot), Dr. Saotome (Getter Robo), Enma-kun (demon-hunting kid), Jiro (Shutendoji),
  Shusha (Susano-oh): they join or cross paths with the parties.
- The phone calls use `{!R}...{!W}` (transceiver voice); keep them where the JP has them.
