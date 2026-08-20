#!/bin/bash
# harness/bench.sh — benchmark latency RAG theo mode (component: bench). Gated RUN_BENCH=1.
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
HARNESS_COMPONENT="bench"
banner "BENCH — RAG latency per search mode"

if [ "${RUN_BENCH:-0}" != "1" ]; then
  wn "bỏ qua bench (đặt RUN_BENCH=1 để bật; gọi Gemini nhiều lần — tốn phí & lâu, hybrid ~30-40s/câu)."
  summary; exit $?
fi
PY="$BACKEND_DIR/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
[ -z "$(detect_backend_port)" ] && { no "backend không chạy"; summary; exit $?; }

mkdir -p "$REPORTS_DIR"; ts="$(date +%Y%m%d-%H%M%S)"
section "ĐO LATENCY (modes=${BENCH_MODES:-hybrid,vector_only}, queries=${BENCH_QUERIES:-3})"
HARNESS_BASE_URL="$(backend_base)" \
  BENCH_JSON="$REPORTS_DIR/bench-$ts.json" BENCH_MD="$REPORTS_DIR/bench-$ts.md" \
  "$PY" "$HARNESS_DIR/bench/bench.py"; rc=$?
echo
[ "$rc" = 0 ] && ok "bench hoàn tất (report → harness/reports/bench-$ts.{json,md})" || no "bench thất bại"
summary; exit $?
