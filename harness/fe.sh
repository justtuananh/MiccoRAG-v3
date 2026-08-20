#!/bin/bash
# harness/fe.sh — frontend: eslint + vite build + playwright e2e (component: fe)
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
HARNESS_COMPONENT="fe"
banner "FRONTEND — eslint + vite build + e2e"
cd "$FRONTEND_DIR" || { no "không vào được $FRONTEND_DIR"; summary; exit $?; }

section "0) MÔI TRƯỜNG"
echo "    node=$(node --version 2>/dev/null)  npm=$(npm --version 2>/dev/null)"
[ -d node_modules ] || wn "node_modules thiếu — chạy 'npm install' trước"

section "1) ESLINT"
out=$(npm run lint 2>&1); rc=$?
[ "$rc" = 0 ] && ok "eslint sạch" || wn "eslint có cảnh báo/lỗi (không chặn build) — $(printf '%s' "$out" | grep -cE 'error|warning') dòng"

section "2) VITE BUILD"
out=$(npm run build 2>&1); rc=$?
if [ "$rc" = 0 ] && [ -d dist ]; then
  ok "vite build thành công (dist=$(du -sh dist 2>/dev/null | cut -f1))"
else
  no "vite build THẤT BẠI"; printf '%s\n' "$out" | tail -12
fi

section "3) PLAYWRIGHT E2E (opt-in RUN_E2E=1)"
if [ "${RUN_E2E:-0}" = "1" ]; then
  if [ -d node_modules/playwright ] || [ -d node_modules/@playwright/test ]; then
    out=$(npm run test:e2e 2>&1); rc=$?
    printf '%s\n' "$out" | grep -E 'PASS|FAIL' | sed 's/^/     /'
    [ "$rc" = 0 ] && ok "playwright e2e PASS" || no "playwright e2e FAIL — $(printf '%s' "$out" | tail -3 | tr '\n' ' ')"
  else
    wn "playwright chưa cài — chạy: npm i -D playwright && npx playwright install chromium"
  fi
else wn "bỏ qua e2e (RUN_E2E=1 để bật; cần frontend :5174 hoặc gateway :8888 chạy)"; fi

summary; exit $?
