#!/usr/bin/env python3
"""rageval/report.py — kết quả JSON → bảng Markdown + tóm tắt console."""
from common import PRICE_IN_PER_M, PRICE_OUT_PER_M

MAIN_METRICS = [
    ("hit_at_k", "hit@k"), ("mrr", "MRR"),
    ("context_precision", "ctx_prec"), ("context_recall", "ctx_recall"),
    ("token_f1", "F1"), ("semantic_sim", "sem_sim"),
    ("llm_correct", "correct(1-5)"), ("correct_rate", "correct_rate"),
    ("answer_relevance", "ans_rel"), ("faithfulness", "faithful"),
    ("hallucinated_answer_rate", "halu_ans"), ("refusal_accuracy", "refusal_acc"),
    ("false_refusal_rate", "false_refusal"), ("kg_source_rate", "kg_src"),
]
LAT_METRICS = [("query_latency_p50", "query p50"), ("query_latency_p95", "query p95"),
               ("chat_latency_p50", "chat p50"), ("chat_latency_p95", "chat p95")]


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return "%.3f" % v if abs(v) < 10 else "%.1f" % v
    return str(v)


def _table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def write_md(result, path):
    agg = result["aggregate"]
    lines = ["# rageval report %s" % result["timestamp"], "",
             "- items: %d · rows: %d · errors: %d" % (
                 result["n_items"], result["n_rows"], result["n_errors"]),
             "- datasets: %s · modes: %s · top_k: %s" % (
                 ",".join(result["config"]["datasets"]),
                 ",".join(result["config"]["modes"]), result["config"]["top_k"]),
             ""]

    # Bảng chính: metric × (dataset|mode)
    keys = sorted(k for k in agg if k.endswith("|ALL") and not k.startswith("ALL|"))
    keys = ["ALL|%s|ALL" % m for m in result["config"]["modes"]
            if "ALL|%s|ALL" % m in agg] + keys
    lines.append("## Tổng hợp metric (dataset × mode)")
    lines.append("")
    rows = []
    for mk, label in MAIN_METRICS:
        rows.append([label] + [fmt(agg[k].get(mk)) for k in keys])
    col_hdr = [k.replace("|ALL", "").replace("|", "·") for k in keys]
    lines.append(_table(["metric"] + col_hdr, rows))
    lines.append("")

    # Δ GraphRAG: hybrid − vector_only theo question_type
    modes = result["config"]["modes"]
    if "hybrid" in modes and "vector_only" in modes:
        lines.append("## Δ GraphRAG (hybrid − vector_only)")
        lines.append("")
        qtypes = sorted({k.split("|")[2] for k in agg if k.startswith("ALL|hybrid|")})
        rows = []
        for mk, label in [("hit_at_k", "hit@k"), ("context_recall", "ctx_recall"),
                          ("correct_rate", "correct_rate"), ("faithfulness", "faithful"),
                          ("llm_correct", "correct(1-5)"), ("chat_latency", "chat lat(s)")]:
            row = [label]
            for qt in qtypes:
                h = agg.get("ALL|hybrid|%s" % qt, {}).get(mk)
                v = agg.get("ALL|vector_only|%s" % qt, {}).get(mk)
                row.append("%+.3f" % (h - v) if h is not None and v is not None else "—")
            rows.append(row)
        lines.append(_table(["Δ metric"] + qtypes, rows))
        lines.append("")

    # Latency
    lines.append("## Latency (giây)")
    lines.append("")
    rows = []
    lat_keys = ["ALL|%s|ALL" % m for m in modes if "ALL|%s|ALL" % m in agg]
    for mk, label in LAT_METRICS:
        rows.append([label] + [fmt(agg[k].get(mk)) for k in lat_keys])
    lines.append(_table(["latency"] + [k.split("|")[1] for k in lat_keys], rows))
    lines.append("")

    # Chi phí ước tính (rất thô: tokens ≈ chars/4)
    total_ans_chars = sum(r.get("answer_chars") or 0 for r in result["items"])
    out_tok = total_ans_chars / 4
    in_tok = result["n_rows"] * 6000  # ước prompt ~6k tok/lượt chat
    cost = in_tok / 1e6 * PRICE_IN_PER_M + out_tok / 1e6 * PRICE_OUT_PER_M
    lines.append("## Chi phí ước tính (chỉ phần chat, chưa gồm judge)")
    lines.append("")
    lines.append("~%.0fk token in, ~%.0fk token out → ≈ $%.3f" % (
        in_tok / 1e3, out_tok / 1e3, cost))
    lines.append("")

    # Top item tệ nhất theo composite (phục vụ Loop A đọc fail case)
    def composite(r):
        vals = [v for v in (r.get("faithfulness"), r.get("answer_relevance"),
                            r.get("context_precision")) if v is not None]
        return sum(vals) / len(vals) if vals else None

    scored = [(composite(r), r) for r in result["items"]
              if not r.get("error") and composite(r) is not None]
    scored.sort(key=lambda x: x[0])
    lines.append("## Top 10 item điểm thấp nhất (composite = mean(faithful, ans_rel, ctx_prec))")
    lines.append("")
    rows = [["%.3f" % s, r["id"], r["mode"], r["question_type"],
             fmt(r.get("faithfulness")), fmt(r.get("answer_relevance")),
             fmt(r.get("context_precision"))]
            for s, r in scored[:10]]
    lines.append(_table(["composite", "id", "mode", "type", "faithful",
                         "ans_rel", "ctx_prec"], rows))
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def print_summary(result):
    agg = result["aggregate"]
    for mode in result["config"]["modes"]:
        g = agg.get("ALL|%s|ALL" % mode)
        if not g:
            continue
        print("  ── mode=%s (n=%d)" % (mode, g["n"]))
        print("     hit@k=%s mrr=%s ctx_prec=%s ctx_recall=%s" % (
            fmt(g.get("hit_at_k")), fmt(g.get("mrr")),
            fmt(g.get("context_precision")), fmt(g.get("context_recall"))))
        print("     F1=%s sem=%s correct=%s(rate %s) ans_rel=%s" % (
            fmt(g.get("token_f1")), fmt(g.get("semantic_sim")),
            fmt(g.get("llm_correct")), fmt(g.get("correct_rate")),
            fmt(g.get("answer_relevance"))))
        print("     faithful=%s halu_ans=%s refusal_acc=%s false_refusal=%s kg_src=%s" % (
            fmt(g.get("faithfulness")), fmt(g.get("hallucinated_answer_rate")),
            fmt(g.get("refusal_accuracy")), fmt(g.get("false_refusal_rate")),
            fmt(g.get("kg_source_rate"))))
        print("     lat: query p50=%ss p95=%ss · chat p50=%ss p95=%ss" % (
            fmt(g.get("query_latency_p50")), fmt(g.get("query_latency_p95")),
            fmt(g.get("chat_latency_p50")), fmt(g.get("chat_latency_p95"))))
