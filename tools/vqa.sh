#!/bin/sh
# Visual QA under Orca (no nested workers): one read-only codex call per qa_gate chunk, per docs/visual-qa-brief.md.
#   python -X utf8 $SKILL/scripts/qa_gate.py todo work/qa/manifest.tsv work/qa/verdicts --size 12 --out-dir work/qa/chunks
#   JOBS=3 sh tools/vqa.sh [work/qa/chunks/chunk_000.txt ..]     (default: every chunk with no verdict file yet)
# Writes work/qa/verdicts/<chunk>.tsv (only the id<TAB>verdict<TAB>note lines of codex's answer) and <chunk>.log.
# Sheets come from tools/tour_sheets.py (English | original side by side).
cd "$(dirname "$0")/.." || exit 1
JOBS=${JOBS:-3}
mkdir -p work/qa/verdicts
[ $# -gt 0 ] || set -- work/qa/chunks/chunk_*.txt
one() {
  c=$1
  n=$(basename "$c" .txt)
  out=work/qa/verdicts/$n.tsv
  [ -s "$out" ] && return 0
  files=$(paste -sd, "$c")  # qa_gate chunks list paths only; the id is the file name without .png (flat tour dir)
  { cat docs/visual-qa-brief.md; echo; echo "Chunk $n, attached in this order (id<TAB>path):"
    while read -r p; do printf '%s\t%s\n' "$(basename "$p" .png)" "$p"; done < "$c"; } |
    timeout 1500 codex exec -s read-only --skip-git-repo-check -o "work/qa/verdicts/$n.raw" -i "$files" - \
      > "work/qa/verdicts/$n.log" 2>&1
  grep -P '^[^\t]+\t(ok|issue)\t' "work/qa/verdicts/$n.raw" > "$out.tmp" && mv "$out.tmp" "$out"
  echo "$n: $(wc -l < "$c") sheets, $(grep -c . "$out" 2>/dev/null || echo 0) verdicts"
}
i=0
for c in "$@"; do
  one "$c" &
  i=$((i + 1))
  [ $((i % JOBS)) -eq 0 ] && wait
done
wait
