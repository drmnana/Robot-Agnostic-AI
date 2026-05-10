#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."
PYTHONPATH=/workspace/backend pytest -q

