#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Resolve once for both changed-path selection and whitespace checking.
set -euo pipefail
base=
all=true
candidate=${CI_BEFORE:-}
if [ "${CI_EVENT:-}" = pull_request ]; then
  candidate=${CI_BASE:-}
fi
if [ "${CI_EVENT:-}" != workflow_dispatch ] && [ -n "$candidate" ] &&
   [[ ! "$candidate" =~ ^0+$ ]] &&
   git rev-parse --verify --quiet "$candidate^{commit}" >/dev/null; then
  if [ "${CI_EVENT:-}" = pull_request ] || git merge-base --is-ancestor "$candidate" HEAD; then
    base=$candidate
    all=false
  else
    # A rewritten branch must run every group, even with a common ancestor.
    base=$(git merge-base "$candidate" HEAD) || base=
  fi
fi
whitespace=$base
if ! git rev-parse --verify --quiet 'HEAD^' >/dev/null; then
  whitespace=$(git hash-object -t tree /dev/null)
elif [ "${CI_EVENT:-}" = workflow_dispatch ]; then
  whitespace=$(git rev-parse 'HEAD^')
elif [ -z "$whitespace" ]; then
  whitespace=$(git hash-object -t tree /dev/null)
fi
printf 'base=%s\nall=%s\nwhitespace_base=%s\n' "$base" "$all" "$whitespace"
