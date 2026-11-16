#!/bin/sh
# Story pass under Orca (no nested workers): one read-only codex call per chapter, per docs/story-reviewer-brief.md.
#   python -X utf8 tools/story.py && python -X utf8 $SKILL/scripts/qa_gate.py init work/qa/story/manifest.tsv \
#       work/qa/story/chapters --glob "*.txt"
#   JOBS=3 sh tools/story_review.sh [ch01 ch02 ..]     (no args: every chapter; skips non-empty reports unless FORCE=1)
# Reports to work/qa/story/reports/<ch>.txt (R=DIR for a later round). Then `python -X utf8 tools/story.py --verdicts`
# writes work/qa/story/verdicts/<round>_<ch>.tsv from each report's Assessment and prints its findings.
cd "$(dirname "$0")/.." || exit 1
JOBS=${JOBS:-3}
C=work/qa/story/chapters
R=${R:-work/qa/story/reports}
mkdir -p "$R"
if [ $# -eq 0 ]; then set -- $(ls "$C" | sed 's/\.txt$//'); fi
one() {
  c=$1
  if [ -z "$FORCE" ] && [ -s "$R/$c.txt" ]; then return 0; fi
  # The chapter is inlined: codex's file reads go through a size-limited tool that can cut a 50 KB file short.
  { cat docs/story-reviewer-brief.md; echo; echo "Chapter $c ($C/$c.txt), in full below. You may read any other file in this repository."
    echo "End your Assessment sentence with how many entries you read, e.g. (read 300 entries)."; echo; cat "$C/$c.txt"; } |
    timeout 2400 codex exec -s read-only --skip-git-repo-check -o "$R/$c.txt" - > "$R/$c.log" 2>&1
  echo "$c exit $?"
}
while [ $# -gt 0 ]; do
  n=0
  while [ $# -gt 0 ] && [ $n -lt "$JOBS" ]; do
    one "$1" &
    shift
    n=$((n + 1))
  done
  wait
done
echo done
