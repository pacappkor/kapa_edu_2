#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Run from the repository root; namespace directories stay in the module path.
set -euo pipefail
repo_root=$(python -B -c "import os; print(os.getcwd())")
path_separator=$(python -B -c "import os; print(os.pathsep)")
while IFS= read -r -d '' test_file; do
  test_dir=$(dirname "$test_file")
  module=${test_file%.py}
  module=${module//\//.}
  # Keep legacy sibling imports working without recursive discovery.
  PYTHONPATH="$repo_root/$test_dir${PYTHONPATH:+$path_separator$PYTHONPATH}" python -B -m unittest -v "$module"
done < <(find tools -type f -name 'test_*.py' -print0 | sort -z)
