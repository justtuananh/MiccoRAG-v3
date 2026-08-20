#!/bin/bash
# harness/be.sh — backend: lint + tests + coverage (component: be)
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
HARNESS_COMPONENT="be"
banner "BACKEND — ruff + pytest + coverage"

PY="$BACKEND_DIR/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
section "0) MÔI TRƯỜNG"
echo "    python: $PY  ($("$PY" -c 'import sys;print(sys.version.split()[0])' 2>/dev/null))"
[ -x "$PY" ] || { no "không có python"; summary; exit $?; }

section "1) RUFF LINT (app/)"
RUFF=""
if command -v ruff >/dev/null 2>&1; then RUFF="ruff"
elif "$PY" -m ruff --version >/dev/null 2>&1; then RUFF="$PY -m ruff"; fi
if [ -n "$RUFF" ]; then
  out=$(cd "$BACKEND_APP_DIR" && $RUFF check app/ 2>&1); rc=$?
  n=$(printf '%s' "$out" | grep -cE ':[0-9]+:[0-9]+:')
  [ "$rc" = 0 ] && ok "ruff check sạch" || wn "ruff: ~$n vấn đề (không chặn — gate mềm)"
else
  wn "ruff chưa cài trong venv — bỏ qua lint (hook settings.json dùng ruff riêng)"
fi

section "2) PYTEST — backend unit"
if "$PY" -m pytest --version >/dev/null 2>&1; then
  COV=""; "$PY" -c 'import pytest_cov' 2>/dev/null && COV="--cov=app --cov-report=term-missing"
  out=$(cd "$BACKEND_APP_DIR" && "$PY" -m pytest tests/ -q -p no:cacheprovider --ignore=tests/integration $COV 2>&1); rc=$?
  sum=$(printf '%s' "$out" | grep -oE '[0-9]+ (passed|failed|error|skipped)[a-z, ]*' | tr '\n' ' ')
  [ -z "$sum" ] && sum=$(printf '%s' "$out" | tail -2 | tr '\n' ' ')
  [ "$rc" = 0 ] && ok "pytest unit PASS — $sum" || no "pytest unit FAIL — $sum"
  if [ -n "$COV" ]; then
    pct=$(printf '%s' "$out" | grep -oE 'TOTAL[^0-9]*[0-9]+%' | grep -oE '[0-9]+%' | tail -1)
    if [ -n "$pct" ]; then note "coverage: $pct"; nn=${pct%\%}; [ "${nn:-100}" -lt 80 ] 2>/dev/null && wn "coverage < 80% (gate mềm ở baseline)"; fi
  else wn "pytest-cov chưa cài — bỏ qua coverage (cài: pip install pytest-cov)"; fi
else no "pytest không khả dụng trong venv"; fi

section "3) PYTEST — integration (opt-in RUN_INTEGRATION=1, gọi Gemini)"
if [ "${RUN_INTEGRATION:-0}" != "1" ]; then
  note "integration bỏ qua (RUN_INTEGRATION=1 + backend để bật; RAG query tốn Gemini API)"
elif [ -d "$BACKEND_APP_DIR/tests/integration" ]; then
  if [ -n "$(detect_backend_port)" ]; then
    out=$(cd "$BACKEND_APP_DIR" && HARNESS_BASE_URL="$(backend_base)" "$PY" -m pytest tests/integration -q -p no:cacheprovider 2>&1); rc=$?
    sum=$(printf '%s' "$out" | grep -oE '[0-9]+ (passed|failed|error|skipped)[a-z, ]*' | tr '\n' ' ')
    [ -z "$sum" ] && sum=$(printf '%s' "$out" | tail -2 | tr '\n' ' ')
    [ "$rc" = 0 ] && ok "integration PASS — $sum" || no "integration FAIL — $sum"
  else wn "backend không chạy — bỏ qua integration"; fi
else note "chưa có tests/integration/"; fi

summary; exit $?
