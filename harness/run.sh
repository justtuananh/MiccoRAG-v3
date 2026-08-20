#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# harness/run.sh — orchestrator: chạy nhiều component, gộp 1 báo cáo thống nhất
# ─────────────────────────────────────────────────────────────────────────────
# Dùng:
#   bash harness/run.sh [COMPONENT... | PRESET] [--json] [--md] [--paid]
#
# Component: smoke be fe test deploy eval bench rageval qa
# Preset:    all  = smoke be fe test deploy   (miễn phí, mặc định)
#            full = smoke be fe test deploy eval bench rageval   (eval/bench/rageval cần --paid)
#            qa   = cổng chất lượng (qa.sh: smoke+be+fe+test + verdict GO/NO-GO)
#
# Cờ: --json  ghi harness/reports/<ts>.json
#     --md    ghi harness/reports/<ts>.md
#     --paid  bật RUN_EVAL/RUN_BENCH/RUN_RAG/RUN_E2E=1 (gọi Gemini/e2e — tốn phí)
#
# Ví dụ:
#   ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh all --json'
#   ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh full --paid'
# ─────────────────────────────────────────────────────────────────────────────
set -u
HDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HDIR/lib.sh"

WANT_JSON=0; WANT_MD=0; comps=()
for a in "$@"; do
  case "$a" in
    --json) WANT_JSON=1;;
    --md)   WANT_MD=1;;
    --paid) export RUN_EVAL=1 RUN_BENCH=1 RUN_RAG=1 RUN_E2E=1 RUN_RAGEVAL=1;;
    all)    comps+=(smoke be fe test deploy);;
    full)   comps+=(smoke be fe test deploy eval bench rageval);;
    smoke|be|fe|test|deploy|eval|bench|rageval|qa) comps+=("$a");;
    *) echo "Không rõ tham số: $a"; exit 2;;
  esac
done
[ "${#comps[@]}" -eq 0 ] && comps=(smoke be fe test deploy)

# khử trùng lặp, giữ thứ tự
uniq_comps=(); for c in "${comps[@]}"; do
  skip=0; for u in "${uniq_comps[@]:-}"; do [ "$u" = "$c" ] && skip=1; done
  [ "$skip" = 0 ] && uniq_comps+=("$c")
done

banner "HARNESS RUN — MiccoRAG-v3  [${uniq_comps[*]}]"
TP=0; TF=0; TW=0; RESULTS=(); rc_any=0
for c in "${uniq_comps[@]}"; do
  script="$HDIR/$c.sh"
  echo; echo "▶▶▶ COMPONENT: $c"
  if [ ! -f "$script" ]; then echo "  (thiếu $script)"; RESULTS+=("$c|NA|0|0|0"); rc_any=1; continue; fi
  out="$(bash "$script"; echo "__RC__=$?")"
  rc="$(printf '%s' "$out" | sed -n 's/^__RC__=//p' | tail -1)"
  printf '%s\n' "$out" | sed '/^__RC__=/d'
  line="$(printf '%s' "$out" | grep -oE 'TỔNG: [0-9]+ PASS / [0-9]+ FAIL / [0-9]+ WARN' | tail -1)"
  p=$(printf '%s' "$line" | grep -oE '[0-9]+ PASS' | grep -oE '[0-9]+'); p=${p:-0}
  f=$(printf '%s' "$line" | grep -oE '[0-9]+ FAIL' | grep -oE '[0-9]+'); f=${f:-0}
  w=$(printf '%s' "$line" | grep -oE '[0-9]+ WARN' | grep -oE '[0-9]+'); w=${w:-0}
  TP=$((TP+p)); TF=$((TF+f)); TW=$((TW+w))
  [ "${rc:-1}" != "0" ] && rc_any=1
  RESULTS+=("$c|$( [ "${rc:-1}" = 0 ] && echo OK || echo FAIL )|$p|$f|$w")
done

echo; banner "TỔNG HỢP HARNESS"
printf "  %-10s %-6s %5s %5s %5s\n" "COMPONENT" "TRẠNG" "PASS" "FAIL" "WARN"
printf "  %-10s %-6s %5s %5s %5s\n" "─────────" "─────" "────" "────" "────"
for r in "${RESULTS[@]}"; do IFS='|' read -r c s p f w <<< "$r"
  printf "  %-10s %-6s %5s %5s %5s\n" "$c" "$s" "$p" "$f" "$w"
done
echo "  ──────────────────────────────────────────────"
printf "  %-10s %-6s %5s %5s %5s\n" "TỔNG" "$( [ "$TF" = 0 ] && echo OK || echo FAIL )" "$TP" "$TF" "$TW"

# ---- Artifact (tùy chọn) ----
if [ "$WANT_JSON" = 1 ] || [ "$WANT_MD" = 1 ]; then
  mkdir -p "$REPORTS_DIR"; ts="$(date +%Y%m%d-%H%M%S)"
  if [ "$WANT_JSON" = 1 ]; then
    { echo "{"; echo "  \"timestamp\": \"$ts\", \"host\": \"$(hostname)\","
      echo "  \"totals\": {\"pass\": $TP, \"fail\": $TF, \"warn\": $TW},"
      echo "  \"components\": ["
      n=${#RESULTS[@]}; i=0
      for r in "${RESULTS[@]}"; do IFS='|' read -r c s p f w <<< "$r"; i=$((i+1))
        printf "    {\"name\":\"%s\",\"status\":\"%s\",\"pass\":%s,\"fail\":%s,\"warn\":%s}%s\n" \
          "$c" "$s" "$p" "$f" "$w" "$([ $i -lt $n ] && echo ,)"
      done
      echo "  ]"; echo "}"; } > "$REPORTS_DIR/$ts.json"
    echo "  📄 JSON: harness/reports/$ts.json"
  fi
  if [ "$WANT_MD" = 1 ]; then
    { echo "# Harness report $ts ($(hostname))"; echo
      echo "| Component | Trạng | PASS | FAIL | WARN |"; echo "|---|---|--:|--:|--:|"
      for r in "${RESULTS[@]}"; do IFS='|' read -r c s p f w <<< "$r"
        echo "| $c | $s | $p | $f | $w |"; done
      echo "| **TỔNG** | $([ "$TF" = 0 ] && echo OK || echo FAIL) | **$TP** | **$TF** | **$TW** |"; } > "$REPORTS_DIR/$ts.md"
    echo "  📄 MD:   harness/reports/$ts.md"
  fi
fi

[ "$TF" -eq 0 ] && [ "$rc_any" -eq 0 ]; exit $?
