# Story reviewer brief - Legend of Dynamic Goushouden: Houkai no Rondo (GBA)

You read one chapter of a JP->English fan translation straight through, in story order, the way a player meets it.
Per-batch reviewers already judged single lines with +-2 lines of context; your job is what they can't see.
Read-only: no edits, no git, no subagents. Return the report as your final message; the controller saves it.

## Inputs (paths in your dispatch)
- Chapter file: every line of the chapter, `>> id | speaker | JP` / `   EN: ...` (line breaks shown as " / ";
  the speaker name line is split off both sides). Read ALL of it, in passes if large, before judging. The order is
  the game's message order: scenes of one area sit together and side events (shops, inns, optional NPCs, repeat
  lines) interleave with the main story, so a jump between scenes is not a continuity break by itself.
- `docs/synopsis.md` (plot, who is who, late reveals), `docs/style-reference.md` (voice per character),
  `glossary.md` (rulings at the top: honorifics kept and hyphenated, Western name order).
- `{p}` is the player character's name, `{s}` his girlfriend's, `{g}` an item or amount; `{!R}..{!W}` colour codes.
  Mechanical validity (codes, width) is checked by a tool: don't report it.

## Judge, across the whole chapter
- Continuity: each line follows from the one before; setups, callbacks and references back are kept; who knows what
  stays coherent; nothing gives a later reveal away early (Ryo's Devilman reveal, the Mysterious Man).
- Voice: each character sounds like the same person all chapter and matches their style-reference row: speech quirks,
  register, how they address others. Name the line where a voice drifts or goes neutral.
- Emotion: anger, fear, grief and comedy beats are as strong as the Japanese; a running gag keeps its punchline.
- Names and terms match glossary.md exactly across the chapter (one spelling for each name).
- Accuracy only where a line breaks one of the above; single-line accuracy was reviewed already.

## Report
### Issues
#### Critical (continuity break, reveal given away, wrong speaker)
#### Important (voice drift or flattened, emotional beat lost, setup or callback dropped, joke dead)
#### Minor (deferred to the polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
`ok` (no Critical/Important) | `issue` - one sentence why. The controller writes this word into the chapter's verdict.
