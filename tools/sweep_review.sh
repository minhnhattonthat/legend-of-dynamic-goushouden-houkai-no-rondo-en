#!/bin/sh
# Read-only codex review of a static graphics sweep (docs/re/graphics.md): PER pages (4 zoomed quarters each) per
# call, 3 calls at a time. Results: $DIR/review$TAG/chunkNN.txt. Prereqs: tools/gfxsweep.py, tools/sweep_quarters.py.
# Codex misses hits at random (one pass skipped a block another pass found): run two passes with different PER and
# take the union.
#   DIR=work/sweep PER=4 TAG= sh tools/sweep_review.sh [FIRST_PAGE LAST_PAGE]
cd "$(dirname "$0")/.." || exit 1
DIR=${DIR:-work/sweep}
PER=${PER:-4}
TAG=${TAG:-}
first=${1:-0}
last=${2:-$(($(ls "$DIR"/page*.png | wc -l) - 1))}
out="$DIR/review$TAG"
mkdir -p "$out"
run() {
  c=$1
  [ "$c" -le "$last" ] || return 0
  files=""
  names=""
  p=$c
  while [ "$p" -lt $((c + PER)) ] && [ "$p" -le "$last" ]; do
    pp=$(printf "page%03d" "$p")
    for q in 0 1 2 3; do
      files="$files,$DIR/q/${pp}_q$q.png"
      names="$names ${pp}_q$q.png"
    done
    p=$((p + 1))
  done
  n=$(printf "%02d" $((c / PER)))
  { cat tools/sweep_review_prompt.txt; echo; echo "Attached in order (zoomed quarters):$names"; } |
    timeout 1200 codex exec -s read-only --skip-git-repo-check -o "$out/chunk$n.txt" -i "${files#,}" - \
      > "$out/chunk$n.log" 2>&1
  echo "chunk $n exit $?"
}
c=$first
while [ "$c" -le "$last" ]; do
  run "$c" &
  run $((c + PER)) &
  run $((c + 2 * PER)) &
  wait
  c=$((c + 3 * PER))
done
echo done
