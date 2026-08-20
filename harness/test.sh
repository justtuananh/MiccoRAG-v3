#!/bin/bash
# harness/test.sh — runner thuần: mọi pytest suite (component: test)
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
HARNESS_COMPONENT="test"
banner "TEST — pytest backend + micco-server"
PY="$BACKEND_DIR/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
echo "    python: $PY"

run_pytest(){ # $1 label  $2 dir  $3.. args
  local label="$1" dir="$2"; shift 2
  if [ ! -d "$dir" ]; then wn "$label: thư mục không tồn tại"; return; fi
  local out rc sum
  out=$(cd "$dir" && "$PY" -m pytest -q -p no:cacheprovider "$@" 2>&1); rc=$?
  sum=$(printf '%s' "$out" | grep -oE '[0-9]+ (passed|failed|error|skipped|deselected)[a-z, ]*' | tr '\n' ' ')
  [ -z "$sum" ] && sum=$(printf '%s' "$out" | tail -2 | tr '\n' ' ')
  if [ "$rc" = 0 ]; then
    ok "$label — $sum"
  elif printf '%s' "$out" | grep -qiE 'ModuleNotFoundError|error during collection|no tests ran|collected 0'; then
    miss=$(printf '%s' "$out" | grep -oE "No module named '[^']+'" | head -1)
    wn "$label — BỎ QUA (thiếu môi trường: ${miss:-collection error}). Cài dep của suite để bật."
  else
    no "$label — $sum"
  fi
}

section "1) BACKEND UNIT (micco-backend/backend/tests)"
run_pytest "backend/tests" "$BACKEND_APP_DIR" tests/ --ignore=tests/integration

section "2) MICCO-SERVER (micco-server/tests, ~110)"
run_pytest "micco-server/tests" "$SERVER_DIR" tests/

section "3) INTEGRATION (opt-in: RUN_INTEGRATION=1 + backend chạy)"
if [ "${RUN_INTEGRATION:-0}" = "1" ] && [ -d "$BACKEND_APP_DIR/tests/integration" ]; then
  if [ -n "$(detect_backend_port)" ]; then
    HARNESS_BASE_URL="$(backend_base)" run_pytest "integration" "$BACKEND_APP_DIR" tests/integration
  else wn "backend không chạy — bỏ qua integration"; fi
else note "integration bỏ qua (RUN_INTEGRATION=1 + backend để bật)"; fi

summary; exit $?
