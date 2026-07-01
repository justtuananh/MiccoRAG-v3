#!/bin/bash
# harness/eval.sh — RAG quality eval trên golden set (component: eval). Gated RUN_EVAL=1.
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
HARNESS_COMPONENT="eval"
banner "EVAL — RAG quality (golden set)"

if [ "${RUN_EVAL:-0}" != "1" ]; then
  wn "bỏ qua eval (đặt RUN_EVAL=1 để bật; gọi Gemini — tốn phí). Tùy chọn: EVAL_ANSWER=1 chấm cả câu trả lời."
  summary; exit $?
fi
PY="$BACKEND_DIR/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
if [ -z "$(detect_backend_port)" ]; then no "backend không chạy — không eval được"; summary; exit $?; fi
[ -f "$HARNESS_DIR/eval/golden.jsonl" ] || { no "thiếu golden.jsonl"; summary; exit $?; }

mkdir -p "$REPORTS_DIR"; ts="$(date +%Y%m%d-%H%M%S)"
section "CHẤM ĐIỂM ($(grep -cvE '^\s*#|^\s*$' "$HARNESS_DIR/eval/golden.jsonl") mục golden)"
HARNESS_BASE_URL="$(backend_base)" EVAL_JSON="$REPORTS_DIR/eval-$ts.json" \
  "$PY" "$HARNESS_DIR/eval/grade.py"; rc=$?
echo
[ "$rc" = 0 ] && ok "eval: pass@1 đạt ngưỡng" || no "eval: pass@1 DƯỚI ngưỡng (xem chi tiết ở trên)"
summary; exit $?
