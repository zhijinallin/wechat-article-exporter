#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

node --check "$PROJECT_ROOT/extractor.js"
node --check "$PROJECT_ROOT/popup.js"
python3 "$PROJECT_ROOT/scripts/verify-project.py"
