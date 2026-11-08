#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Run stock unittest discovery, checking package layout and completion summary.
# Run from the repository root.
set -euo pipefail
python -I -B tools/ci_tests_supervise.py
