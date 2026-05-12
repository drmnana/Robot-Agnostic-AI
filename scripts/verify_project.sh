#!/usr/bin/env bash
set -uo pipefail

MODE="fail-fast"

usage() {
  echo "Usage: scripts/verify_project.sh [--all]"
}

if [[ $# -gt 1 ]]; then
  usage
  exit 2
fi

if [[ $# -eq 1 ]]; then
  if [[ "$1" == "--all" ]]; then
    MODE="all"
  else
    usage
    exit 2
  fi
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

elapsed_seconds() {
  python3 - "$1" <<'PY'
import sys
import time

started = float(sys.argv[1])
print(f"{time.monotonic() - started:.1f}")
PY
}

start_timer() {
  python3 - <<'PY'
import time

print(time.monotonic())
PY
}

run_check() {
  local name="$1"
  local command="$2"
  local started duration output status
  started="$(start_timer)"
  output="$(bash -lc "$command" 2>&1)"
  status=$?
  duration="$(elapsed_seconds "$started")"

  if [[ "$status" -eq 0 ]]; then
    echo "[PASS] ${name} (${duration}s)"
  else
    echo "[FAIL] ${name} (${duration}s)"
    echo "$output"
  fi
  return "$status"
}

real_checks() {
  CHECK_NAMES=(
    "backend API tests"
    "mission YAML validation"
    "OpenAPI drift check"
  )
  CHECK_COMMANDS=(
    "PYTHONPATH=/workspace/backend pytest -q /workspace/backend/tests/test_backend_api.py"
    "PYTHONPATH=/workspace/backend python /workspace/backend/scripts/validate_missions.py"
    "PYTHONPATH=/workspace/backend python -c 'import json; from pathlib import Path; from app.main import app; assert json.loads(Path(\"/workspace/docs/openapi.json\").read_text(encoding=\"utf-8\")) == app.openapi()'"
  )
}

fake_checks() {
  local pattern="${ORIMUS_VERIFY_FAKE_PATTERN:-pass}"
  case "$pattern" in
    pass)
      CHECK_NAMES=("fake one" "fake two")
      CHECK_COMMANDS=("true" "true")
      ;;
    fail-first)
      CHECK_NAMES=("fake one" "fake two" "fake three")
      CHECK_COMMANDS=("false" "true" "true")
      ;;
    fail-second)
      CHECK_NAMES=("fake one" "fake two" "fake three")
      CHECK_COMMANDS=("true" "false" "true")
      ;;
    *)
      echo "Unknown ORIMUS_VERIFY_FAKE_PATTERN: $pattern"
      exit 2
      ;;
  esac
}

if [[ "${ORIMUS_VERIFY_FAKE_CHECKS:-}" == "1" ]]; then
  fake_checks
else
  real_checks
fi

passed=0
failed=0
failed_names=()

for index in "${!CHECK_NAMES[@]}"; do
  if run_check "${CHECK_NAMES[$index]}" "${CHECK_COMMANDS[$index]}"; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
    failed_names+=("${CHECK_NAMES[$index]}")
    if [[ "$MODE" == "fail-fast" ]]; then
      echo "SUMMARY: ${passed} passed, ${failed} failed"
      echo "FAILED: ${failed_names[*]}"
      exit 1
    fi
  fi
done

echo "SUMMARY: ${passed} passed, ${failed} failed"
if [[ "$failed" -gt 0 ]]; then
  echo "FAILED: ${failed_names[*]}"
  exit 1
fi
