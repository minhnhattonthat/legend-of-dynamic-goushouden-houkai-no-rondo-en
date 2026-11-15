#!/bin/sh
# Read-only codex review of translation batches (references/translation.md §Review), one batch per call, JOBS calls
# at a time. Pairs files from tools/pairs.py; reports to work/qa/review/reports/bNNN.txt (skips existing non-empty
# reports unless FORCE=1; R=DIR for a later round). Parse them with tools/review_findings.py (--rep DIR).
#   JOBS=4 sh tools/review.sh b002 b003 ...      (no args: every batch with a pairs file)
cd "$(dirname "$0")/.." || exit 1
JOBS=${JOBS:-4}
P=work/qa/review/pairs
R=${R:-work/qa/review/reports}
mkdir -p "$R"
if [ $# -eq 0 ]; then set -- $(ls "$P" | sed 's/\.txt$//'); fi
one() {
  b=$1
  if [ -z "$FORCE" ] && [ -s "$R/$b.txt" ]; then return 0; fi
  { cat tools/review_prompt.txt; echo; echo "Pairs file: $P/$b.txt (batch $b)"; } |
    timeout 1500 codex exec -s read-only --skip-git-repo-check -o "$R/$b.txt" - > "$R/$b.log" 2>&1
  echo "$b exit $?"
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
