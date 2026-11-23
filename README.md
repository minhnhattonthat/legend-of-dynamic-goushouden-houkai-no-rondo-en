# Legend of Dynamic Goushouden: Houkai no Rondo English translation

Unofficial English fan translation of **Legend of Dynamic Goushouden: Houkai no Rondo** (Game Boy Advance,
Banpresto, 2003), the Go Nagai crossover RPG: the source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Dialogue / story (both routes, side towns) | Translated |
| Menus, items, skills, enemies, battle and system messages, character book | Translated |
| Title screen, menu labels, battle sound effects, other graphics with text | Translated (the 豪翔伝 logo is kept: it has no official English version) |
| Name entry | Translated tabs (HIRA / KATA / ABC): names can be entered in kana or English letters |
| Ending credits | Translated |

Known issues: none known; see [Issues](../../issues).

## Base ROM

`Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba` (No-Intro), 8,388,608 bytes

| Hash | Value |
|---|---|
| CRC32 | `67F18F8E` |
| MD5 | `35eb30c1013b72df8ec4a71a1fc1acff` |
| SHA-1 | `8a037eff3a44b1667ec5e81ca8c1ff03537366b2` |

The patched ROM (v1.1) is 16 MiB (the English text needs the extra space), CRC32 `DA83E446`, SHA-1
`e1c26fb02e87f8abbe33d9d3f2c6118f2f6d05c0`. Tested in Mesen 2.2.1 (GBA, with the official
BIOS). Start from a cold boot: savestates made with another version of the patch carry its old code and text.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, QA, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.codex/agents/`, `.opencode/agents/` | Subagent types (translator, reviewer, visual QA, playtester, graphics) for Codex and opencode; Claude Code gets them from the plugin. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/legend-of-dynamic-goushouden-houkai-no-rondo-en
cd legend-of-dynamic-goushouden-houkai-no-rondo-en
# copy your dump to: rom/Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba
#   (8388608 bytes, SHA-1 8a037eff3a44b1667ec5e81ca8c1ff03537366b2; the build refuses any other dump, see rom.sha1)
python -X utf8 build.py                                # -> build/goushouden_en.gba
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Banpresto's and is included only so
the translation can be checked against it. Legend of Dynamic Goushouden: Houkai no Rondo is (c) Banpresto / Dynamic
Planning; this project is not affiliated with them. Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic, with OpenAI Codex as reviewer).
Corrections are very welcome.
