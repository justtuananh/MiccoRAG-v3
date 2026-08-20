#!/bin/bash
# harness/rageval.sh — benchmark RAG đa tiêu chí (component: rageval). Gated RUN_RAGEVAL=1.
# Metric: retrieval (hit@k/MRR/precision/recall) · answer (F1/EM/sem-sim/LLM-correct/relevance)
#         · hallucination (faithfulness/refusal) · latency p50-p95 · Δ GraphRAG (hybrid vs vector_only)
# Env: RAGEVAL_DATASETS RAGEVAL_MODES RAGEVAL_N RAGEVAL_PHASES RAGEVAL_RUN_DIR (xem rageval/README.md)
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
HARNESS_COMPONENT="rageval"
banner "RAGEVAL — benchmark đa tiêu chí (2 dataset × 2 mode)"

if [ "${RUN_RAGEVAL:-0}" != "1" ]; then
  wn "bỏ qua rageval (đặt RUN_RAGEVAL=1 để bật; gọi Gemini — tốn phí). Smoke: RAGEVAL_N=5"
  summary; exit $?
fi
PY="$(command -v python3)"
RAGDIR="$HARNESS_DIR/rageval"

if [ -z "$(detect_backend_port)" ]; then no "backend không chạy — không bench được"; summary; exit $?; fi

section "SELFTEST METRIC (miễn phí)"
if (cd "$RAGDIR" && "$PY" metrics.py --selftest >/dev/null 2>&1); then
  ok "metrics.py --selftest"
else
  no "metrics.py --selftest FAIL"; summary; exit $?
fi

have_ds=0
[ -f "$RAGDIR/datasets/golden_self.jsonl" ] && { ok "dataset self có mặt"; have_ds=1; } \
  || wn "thiếu golden_self.jsonl (build: rageval/build_golden.py --loop)"
[ -f "$RAGDIR/datasets/golden_hf.jsonl" ] && { ok "dataset hf có mặt"; have_ds=1; } \
  || wn "thiếu golden_hf.jsonl (build: build_hf.py → translate.py → ingest_hf.py)"
if [ "$have_ds" = 0 ] && [ -z "${RAGEVAL_SUBSET:-}" ]; then
  no "không có dataset nào để chạy"; summary; exit $?
fi

section "BENCHMARK"
mkdir -p "$REPORTS_DIR"; ts="$(date +%Y%m%d-%H%M%S)"
HARNESS_BASE_URL="$(backend_base)" \
RAGEVAL_JSON="${RAGEVAL_JSON:-$REPORTS_DIR/rageval-$ts.json}" \
RAGEVAL_MD="${RAGEVAL_MD:-$REPORTS_DIR/rageval-$ts.md}" \
  "$PY" "$RAGDIR/runner.py"; rc=$?
echo
[ "$rc" = 0 ] && ok "rageval: đạt ngưỡng (correct_rate/faithfulness)" \
             || no "rageval: DƯỚI ngưỡng hoặc lỗi (rc=$rc, xem report)"
summary; exit $?
