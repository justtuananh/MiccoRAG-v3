#!/bin/bash
# harness/qa.sh — cổng chất lượng: smoke+be+fe+test → verdict GO/NO-GO (component: qa)
set -u
HDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HDIR/lib.sh"
HARNESS_COMPONENT="qa"
banner "QA GATE — smoke + be + fe + test"

gp=0; gf=0; gw=0; rows=()
for c in smoke be fe test; do
  echo; echo "──────── chạy sub-component: $c ────────"
  out="$(bash "$HDIR/$c.sh"; echo "__RC__=$?")"
  rc="$(printf '%s' "$out" | sed -n 's/^__RC__=//p' | tail -1)"
  printf '%s\n' "$out" | sed '/^__RC__=/d' | sed 's/^/   /'
  line="$(printf '%s' "$out" | grep -oE 'TỔNG: [0-9]+ PASS / [0-9]+ FAIL / [0-9]+ WARN' | tail -1)"
  p=$(printf '%s' "$line" | grep -oE '[0-9]+ PASS' | grep -oE '[0-9]+'); p=${p:-0}
  f=$(printf '%s' "$line" | grep -oE '[0-9]+ FAIL' | grep -oE '[0-9]+'); f=${f:-0}
  w=$(printf '%s' "$line" | grep -oE '[0-9]+ WARN' | grep -oE '[0-9]+'); w=${w:-0}
  gp=$((gp+p)); gf=$((gf+f)); gw=$((gw+w))
  rows+=("$c: ${p}P / ${f}F / ${w}W  (rc=${rc:-?})")
done

section "KẾT LUẬN QA"
for r in "${rows[@]}"; do note "$r"; done
pass=$gp; fail=$gf; warn=$gw
if [ "$gf" -eq 0 ]; then
  echo "  🟢 GO — đủ điều kiện release ($gp PASS, 0 FAIL, $gw WARN)"
else
  echo "  🔴 NO-GO — còn $gf FAIL cần xử lý"
fi
summary; exit $?
