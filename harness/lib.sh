#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# harness/lib.sh — thư viện dùng chung cho harness MiccoRAG-v3
# ─────────────────────────────────────────────────────────────────────────────
# SOURCE file này, KHÔNG chạy trực tiếp. Mỗi component (be/fe/qa/...) source lib.sh,
# đặt HARNESS_COMPONENT, gọi ok/no/wn, rồi kết bằng `summary; exit $?`.
#
# ⚠️ VPS DÙNG CHUNG: mọi lệnh docker PHẢI đi qua dki()/dkexec() — chỉ chấp nhận
#    container nexusrag-* / micco-*. Không bao giờ restart/rm/prune bất cứ thứ gì.
# ─────────────────────────────────────────────────────────────────────────────

# Chống double-source
[ -n "${_HARNESS_LIB_LOADED:-}" ] && return 0
_HARNESS_LIB_LOADED=1

# ---- Đường dẫn ----
HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$HARNESS_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/micco-backend"
BACKEND_APP_DIR="$BACKEND_DIR/backend"
FRONTEND_DIR="$PROJECT_ROOT/micco-frontend"
SERVER_DIR="$PROJECT_ROOT/micco-server"
REPORTS_DIR="$HARNESS_DIR/reports"

# ---- Biến đếm + in ----
pass=0; fail=0; warn=0
HARNESS_COMPONENT="${HARNESS_COMPONENT:-harness}"
ok(){   echo "  ✅ PASS: $1"; pass=$((pass+1)); }
no(){   echo "  ❌ FAIL: $1"; fail=$((fail+1)); }
wn(){   echo "  ⚠️  WARN: $1"; warn=$((warn+1)); }
note(){ echo "  ℹ️  $1"; }
section(){ echo "════════ $1 ════════"; }
banner(){
  echo "╔══════════════════════════════════════════════════════════════╗"
  printf   "║  %-60s║\n" "$1"
  echo "╚══════════════════════════════════════════════════════════════╝"
}

# ---- HTTP helpers (luôn có timeout) ----
HARNESS_HTTP_TIMEOUT="${HARNESS_HTTP_TIMEOUT:-8}"
AUTH_HDR="Authorization: Bearer dev-skip"   # dev bypass (core/security.py) cho smoke/read
hcode(){ curl -s -o /dev/null --max-time "$HARNESS_HTTP_TIMEOUT" -w '%{http_code}' "$@" 2>/dev/null; }
hbody(){ curl -s --max-time "${1:-$HARNESS_HTTP_TIMEOUT}" "${@:2}" 2>/dev/null; }

# ---- Tự dò port backend đang sống (/health = healthy) ----
detect_backend_port(){
  local p body
  for p in ${BACKEND_PORT:-} 8001 8000; do
    [ -z "$p" ] && continue
    body=$(curl -s --max-time 6 "http://127.0.0.1:$p/health" 2>/dev/null)
    printf '%s' "$body" | grep -q '"healthy"' && { echo "$p"; return 0; }
  done
  echo ""
}
backend_base(){ local p; p="$(detect_backend_port)"; echo "http://127.0.0.1:${p:-8001}"; }

# ---- Docker: guard VPS dùng chung ----
HARNESS_OUR_CONTAINERS="nexusrag-postgres nexusrag-chromadb micco-nginx-gw micco-duckdns-updater"
_is_ours(){ case " $HARNESS_OUR_CONTAINERS " in *" $1 "*) return 0;; esac; return 1; }
have_docker(){ command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; }
# dki CONTAINER GO_TEMPLATE  → docker inspect -f TEMPLATE CONTAINER (chỉ container của mình)
dki(){
  _is_ours "$1" || { echo "REFUSED (not ours): $1" >&2; return 99; }
  docker inspect -f "$2" "$1" 2>/dev/null
}
# dkexec CONTAINER cmd...    → docker exec CONTAINER cmd (chỉ container của mình)
dkexec(){
  _is_ours "$1" || { echo "REFUSED (not ours): $1" >&2; return 99; }
  local c="$1"; shift; docker exec "$c" "$@"
}

# ---- Kết luận component ----
# In dòng máy-đọc-được cho run.sh parse: "[<comp>] TỔNG: P PASS / F FAIL / W WARN"
summary(){
  echo "──────────────────────────────────────────────────────────────"
  echo "  [$HARNESS_COMPONENT] TỔNG: $pass PASS / $fail FAIL / $warn WARN"
  [ "$fail" -eq 0 ]
}
