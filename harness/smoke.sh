#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# harness/smoke.sh — smoke + health hạ tầng đang chạy (component: smoke)
# ─────────────────────────────────────────────────────────────────────────────
# Chỉ ĐỌC trạng thái, chỉ đụng container nexusrag-*/micco-*. An toàn trên VPS chung.
# Tùy chọn: BACKEND_PORT=8001  RUN_RAG=1
# ─────────────────────────────────────────────────────────────────────────────
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
HARNESS_COMPONENT="smoke"

banner "SMOKE + HEALTH — MiccoRAG-v3"
section "0) MÔI TRƯỜNG"
_dk=$(have_docker && echo ok || echo 'không có/không quyền')
echo "    host=$(hostname)  user=$(whoami)  docker=$_dk"
BPORT="$(detect_backend_port)"
BASE="http://127.0.0.1:${BPORT:-8001}"
echo "    backend port dò được: ${BPORT:-'(không thấy — mặc định 8001 cho probe)'}"

section "1) DOCKER SERVICES (chỉ nexusrag-*/micco-*)"
if have_docker; then
  st=$(dki nexusrag-postgres '{{.State.Status}}')
  he=$(dki nexusrag-postgres '{{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}')
  if [ "$st" = "running" ] && { [ "$he" = "healthy" ] || [ "$he" = "n/a" ]; }; then
    ok "nexusrag-postgres running (health=$he)"
  else no "nexusrag-postgres không khỏe (status=${st:-missing} health=${he:-?})"; fi
  for c in nexusrag-chromadb micco-nginx-gw micco-duckdns-updater; do
    st=$(dki "$c" '{{.State.Status}}')
    [ "$st" = "running" ] && ok "$c running" || no "$c không chạy (status=${st:-missing})"
  done
else wn "bỏ qua kiểm tra Docker (không quyền docker)"; fi

section "2) POSTGRESQL (db=nexusrag, host :15435)"
if have_docker; then
  if dkexec nexusrag-postgres pg_isready -U postgres >/dev/null 2>&1; then ok "pg_isready OK"; else no "pg_isready thất bại"; fi
  cnt=$(dkexec nexusrag-postgres psql -U postgres -d nexusrag -tAc \
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('departments','users','knowledge_bases','documents')" \
        2>/dev/null | tr -d '[:space:]')
  [ "${cnt:-0}" -ge 4 ] 2>/dev/null && ok "4 bảng lõi tồn tại" || no "thiếu bảng lõi (đếm ${cnt:-0}/4)"
else wn "bỏ qua kiểm tra Postgres (không quyền docker)"; fi

section "3) CHROMADB (host :8003)"
c=$(hcode http://127.0.0.1:8003/api/v2/heartbeat)
[ "$c" = "200" ] && ok "ChromaDB heartbeat 200 (/api/v2)" || no "ChromaDB heartbeat=$c"

section "4) BACKEND HEALTH"
[ -n "$BPORT" ] && ok "backend sống ở :$BPORT (/health=healthy)" || no "không backend nào (8001/8000) healthy"
r=$(hcode "$BASE/ready"); [ "$r" = "200" ] && ok "/ready=200" || no "/ready=$r"

section "5) API SURFACE (/api/v1)"
c=$(hcode "$BASE/api/v1/rag/capabilities"); [ "$c" = "200" ] && ok "/api/v1/rag/capabilities=200" || no "/api/v1/rag/capabilities=$c"
c=$(hcode "$BASE/api/v1/config/status");   [ "$c" = "200" ] && ok "/api/v1/config/status=200"   || no "/api/v1/config/status=$c"
ws=$(hcode -H "$AUTH_HDR" "$BASE/api/v1/workspaces")
case "$ws" in
  200)     ok "/api/v1/workspaces=200 (dev-skip OK)";;
  401|403) wn "/api/v1/workspaces=$ws (sống nhưng dev-skip tắt)";;
  *)       no "/api/v1/workspaces=$ws";;
esac

section "6) API DOCS"
c=$(hcode "$BASE/docs"); [ "$c" = "200" ] && ok "/docs=200" || no "/docs=$c"

section "7) NGINX GATEWAY (:8888, host network)"
c=$(hcode http://127.0.0.1:8888/)
{ [ "$c" = "200" ] || [ "$c" = "304" ]; } && ok "gateway :8888 phản hồi ($c)" || no "gateway :8888=$c"
NG="$BACKEND_DIR/nginx.conf"
if [ -f "$NG" ]; then
  ups=$(grep -oE '127\.0\.0\.1:[0-9]+' "$NG" | grep -oE '[0-9]+$' | sort -u | tr '\n' ' ')
  note "nginx.conf upstream: ${ups:-?} | backend sống: ${BPORT:-none}"
  [ -n "$BPORT" ] && ! printf ' %s ' "$ups" | grep -q " $BPORT " && \
    wn "LỆCH: nginx '/api' proxy tới cổng khác backend (:$BPORT). Xem OPERATIONS.md."
fi

section "8) FRONTEND (Vite :5174)"
c=$(hcode http://127.0.0.1:5174/); [ "$c" = "200" ] && ok "frontend :5174=200" || wn "frontend :5174=$c (Vite dev có thể tắt)"

section "9) RAG SMOKE (opt-in RUN_RAG=1)"
if [ "${RUN_RAG:-0}" = "1" ]; then
  wid=$(hbody 8 -H "$AUTH_HDR" "$BASE/api/v1/workspaces" | grep -oE '"id"[[:space:]]*:[[:space:]]*[0-9]+' | grep -oE '[0-9]+' | head -1)
  if [ -z "$wid" ]; then wn "không lấy được workspace id — bỏ qua"; else
    resp=$(curl -s --max-time 90 -w $'\n%{http_code}' -H "$AUTH_HDR" -H 'Content-Type: application/json' \
           -X POST "$BASE/api/v1/rag/query/$wid" -d '{"question":"Kiểm tra hệ thống, trả lời ngắn.","top_k":3}' 2>/dev/null)
    rc=$(printf '%s' "$resp" | tail -n1); rb=$(printf '%s' "$resp" | sed '$d')
    nch=$(printf '%s' "$rb" | grep -oE '"total_chunks"[[:space:]]*:[[:space:]]*[0-9]+' | grep -oE '[0-9]+$' | head -1)
    { [ "$rc" = "200" ] && [ -n "$nch" ]; } && ok "RAG /query ws $wid=200 (total_chunks=$nch)" || no "RAG /query ws $wid=HTTP $rc"
  fi
else wn "bỏ qua RAG query (RUN_RAG=1 để bật; tốn Gemini API)"; fi

section "10) GHI CHÚ (không tính điểm)"
note "backend 2 instance: dev :8001 (kms) / prod :8000 (root)"
note "Postgres host thực tế 15435; nginx host-net nghe :8888"

summary; exit $?
