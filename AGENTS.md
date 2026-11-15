# Legend of Dynamic Goushouden: Houkai no Rondo (GBA) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `~/.claude/plugins/marketplaces/retro-translation/skills/translate-retro-game/SKILL.md`; `$SKILL` = the directory holding its SKILL.md, printed by `python tools/skill.py`). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py`        -> build/goushouden_en.gba (checks the dump against `rom.sha1` first; written in phase 3)
- Check:    `python -X utf8 tools/check.py`  (tests + lint; the pre-commit hook runs this; `git config core.hooksPath tools/hooks` once per clone)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/goushouden_en.gba --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 $SKILL/scripts/emu.py build/goushouden_en.gba --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 900 --sheet` (scenes: `tools/debug/scenes.txt` + `map_NNN` from `tools/debug/maps.tsv`; never ask the user to play to a scene)
- Warp all: `python -X utf8 tools/debug/warp_all.py [ROM] [--only RE] [--states]` (one shot per scene in `work/qa/warp_all/shots/`; `--states` regenerates `work/states/<scene>.mss`)
- Release:  `python -X utf8 tools/release.py` (patch + verify; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original ROM: `rom/Legend of Dynamic Goushouden - Houkai no Rondo (Japan).gba` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: this repo's own MesenCE in `tools/mesen/` (release 2.2.1, https://github.com/nesdev-org/MesenCE/releases/download/2.2.1/Mesen_2.2.1_Windows.zip, plus `Firmware/gba_bios.bin` from `fetch_emu.py gba-bios`; gitignored; settings in `tools/emu-config/`). Savestates: `work/states/`.
- Text: `script/archive/fNN.json` (dialogue), `script/rom/*.json` (menus, items, names; `sfx.json`), from
  `python -X utf8 tools/extract.py dump` (never clobbers: `--force` keeps en). Codec: `tools/sjis.py` (cp932 + tags). Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the agent types (translator, reviewer, visual-qa, playtester, graphics) shipped by the plugin as `translate-retro-game:<type>` (Claude Code), `.codex/agents/` (Codex) or `.opencode/agents/` (opencode), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Guard hook: `.claude/settings.json` runs the vendored `.claude/hooks/guard_bash.py` (the plugin's own hook did not load; vendored so the policy is reviewed in git, not pulled by auto-update); it blocks `sed -i` and source heredocs.
- Gotchas: see `docs/re/README.md` (filled in during recon).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
