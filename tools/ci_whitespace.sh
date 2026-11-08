#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Only empty-tree fallback excludes verbatim sources; normal diffs check every path.
set -euo pipefail
base=${1:?whitespace base required}
if [ "$base" = "$(git rev-parse HEAD)" ]; then
  echo 'Whitespace check skipped: no new commits (rewind or unchanged HEAD).'
  exit 0
fi
empty=$(git hash-object -t tree /dev/null)
if [ "$base" = "$empty" ]; then
  git diff --check "$base" HEAD -- . ':(exclude)compensation_law/29/01.tex' ':(exclude)compensation_law/29/02.tex' ':(exclude)compensation_law/29/03.tex' ':(exclude)appraisal_practice/22/04.tex'
else
  git diff --check "$base" HEAD
fi
