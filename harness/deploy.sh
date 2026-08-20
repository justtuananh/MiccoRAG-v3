#!/bin/bash
# harness/deploy.sh — xác minh triển khai (READ-ONLY). component: deploy
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
HARNESS_COMPONENT="deploy"
banner "DEPLOY VERIFY — services · migrations · seed · routing · public"
BPORT="$(detect_backend_port)"; BASE="http://127.0.0.1:${BPORT:-8001}"
echo "    backend :$BPORT | nginx :8888"

section "1) CONTAINERS (nexusrag-*/micco-*)"
if have_docker; then
  for c in nexusrag-postgres nexusrag-chromadb micco-nginx-gw micco-duckdns-updater; do
    st=$(dki "$c" '{{.State.Status}}'); [ "$st" = running ] && ok "$c running" || no "$c = ${st:-missing}"
  done
else wn "không quyền docker — bỏ qua containers"; fi

section "2) DB MIGRATIONS (alembic_version)"
if have_docker; then
  ver=$(dkexec nexusrag-postgres psql -U postgres -d nexusrag -tAc "SELECT version_num FROM alembic_version" 2>/dev/null | tr -d '[:space:]')
  nfiles=$(ls "$BACKEND_APP_DIR/alembic/versions"/*.py 2>/dev/null | wc -l | tr -d ' ')
  if [ -n "$ver" ]; then ok "alembic đã áp (version_num=$ver; $nfiles file migration)"
  else wn "chưa thấy bảng/row alembic_version (có thể dùng AUTO_CREATE_TABLES)"; fi
else wn "bỏ qua migrations (không docker)"; fi

section "3) SEED / DỮ LIỆU LÕI"
if have_docker; then
  for t in departments users knowledge_bases documents; do
    n=$(dkexec nexusrag-postgres psql -U postgres -d nexusrag -tAc "SELECT count(*) FROM $t" 2>/dev/null | tr -d '[:space:]')
    if [ -z "$n" ]; then no "không đọc được bảng $t"
    elif [ "$t" = users ]; then [ "${n:-0}" -ge 1 ] 2>/dev/null && ok "users có $n dòng (seed OK)" || wn "users rỗng — chạy seed_users.py"
    else note "$t: $n dòng"; fi
  done
else wn "bỏ qua seed (không docker)"; fi

section "4) NGINX ROUTING (:8888)"
g=$(hcode http://127.0.0.1:8888/); { [ "$g" = 200 ] || [ "$g" = 304 ]; } && ok "/  (frontend) = $g" || no "/ = $g"
ga=$(hcode http://127.0.0.1:8888/api/v1/config/status)
if [ "$ga" = 200 ]; then ok "/api → backend OK ($ga)"
else wn "/api = $ga — LỆCH: nginx proxy /api→:8089 nhưng backend ở :$BPORT (app dev đi qua Cloudflare tunnel, không qua nginx /api). Sửa nginx.conf để dùng trực tiếp."; fi
gd=$(hcode http://127.0.0.1:8888/docs); [ "$gd" = 200 ] && ok "/docs = $gd" || wn "/docs = $gd (cùng lỗi upstream :8089)"

section "5) PUBLIC / TUNNEL"
sub=$(grep -oE 'SUBDOMAINS=[^ }]*' "$BACKEND_DIR/docker-compose.nginx.yml" 2>/dev/null | head -1)
note "DuckDNS ${sub:-'(không rõ)'}"
tun=$(grep -oE 'https://[a-z0-9.-]+\.trycloudflare\.com' "$FRONTEND_DIR/vite.config.js" 2>/dev/null | head -1)
if [ -n "$tun" ]; then
  tc=$(hcode "$tun/health")
  [ "$tc" = 200 ] && ok "tunnel reachable ($tun)" || wn "tunnel $tun không phản hồi /health ($tc) — URL tạm trycloudflare hay đổi"
else note "không thấy tunnel URL trong vite.config.js"; fi

summary; exit $?
