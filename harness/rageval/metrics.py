#!/usr/bin/env python3
"""rageval/metrics.py — công thức metric thuần (không network) + --selftest.

Metric per-item:
  retrieval : hit@1/3/k, mrr, context_precision, context_recall, keyword_hit
  answer    : token_f1, exact_match, partial_match (semantic_sim & llm_correct do
              runner gắn vào từ judge/embedding)
  faithful  : faithfulness = supported/total claims (runner gắn label từ judge)

aggregate(rows) gộp theo (dataset × mode × question_type) và tổng.
"""
import sys

from common import normalize_answer, percentile, vi_tokenize


# ---------------------------------------------------------------------------
# Answer metrics
# ---------------------------------------------------------------------------

def token_f1(pred, gold):
    """F1 mức token (âm tiết VI), multiset overlap — chuẩn SQuAD."""
    pt, gt = vi_tokenize(pred), vi_tokenize(gold)
    if not pt or not gt:
        return float(pt == gt)
    common = {}
    for t in gt:
        common[t] = common.get(t, 0) + 1
    overlap = 0
    for t in pt:
        if common.get(t, 0) > 0:
            overlap += 1
            common[t] -= 1
    if overlap == 0:
        return 0.0
    p = overlap / len(pt)
    r = overlap / len(gt)
    return 2 * p * r / (p + r)


def exact_match(pred, gold):
    return float(normalize_answer(pred) == normalize_answer(gold))


def partial_match(pred, gold):
    """1 nếu đáp án chuẩn nằm gọn trong câu trả lời, hoặc phủ ≥80% token gold."""
    np_, ng = normalize_answer(pred), normalize_answer(gold)
    if not ng:
        return 0.0
    if ng in np_:
        return 1.0
    gt = vi_tokenize(gold)
    pt = set(vi_tokenize(pred))
    cover = sum(1 for t in gt if t in pt) / len(gt)
    return float(cover >= 0.8)


# ---------------------------------------------------------------------------
# Retrieval metrics — nhận list bool `rels` theo thứ tự rank
# ---------------------------------------------------------------------------

def hit_at(rels, k):
    return float(any(rels[:k]))


def mrr(rels):
    for i, r in enumerate(rels):
        if r:
            return 1.0 / (i + 1)
    return 0.0


def context_precision(rels):
    return (sum(1 for r in rels if r) / len(rels)) if rels else 0.0


def context_recall(found_gold, total_gold):
    return (found_gold / total_gold) if total_gold else 0.0


def keyword_hit(context, keywords):
    if not keywords:
        return None
    ctx = normalize_answer(context)
    return sum(1 for k in keywords if normalize_answer(k) in ctx) / len(keywords)


# ---------------------------------------------------------------------------
# Faithfulness
# ---------------------------------------------------------------------------

def faithfulness(claim_labels):
    """claim_labels: list 'supported'/'unsupported'. [] → None (không claim nào)."""
    if not claim_labels:
        return None
    return sum(1 for c in claim_labels if c == "supported") / len(claim_labels)


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

NUM_FIELDS = ["hit_at_1", "hit_at_3", "hit_at_k", "mrr", "context_precision",
              "context_recall", "keyword_hit", "token_f1", "exact_match",
              "partial_match", "semantic_sim", "llm_correct", "answer_relevance",
              "faithfulness", "query_latency", "chat_latency", "answer_chars"]


def _mean(vals):
    vs = [v for v in vals if v is not None]
    return (sum(vs) / len(vs)) if vs else None


def _agg_group(rows):
    out = {"n": len(rows)}
    for f in NUM_FIELDS:
        out[f] = _mean([r.get(f) for r in rows])
    # tỉ lệ suy diễn
    corr = [r.get("llm_correct") for r in rows if r.get("llm_correct") is not None]
    out["correct_rate"] = (sum(1 for c in corr if c >= 4) / len(corr)) if corr else None
    fai = [r.get("faithfulness") for r in rows if r.get("faithfulness") is not None]
    out["hallucinated_answer_rate"] = (
        sum(1 for f in fai if f < 1.0) / len(fai)) if fai else None
    # refusal (theo loại câu hỏi)
    unans = [r for r in rows if r.get("question_type") == "unanswerable"
             and r.get("refusal_label")]
    out["refusal_accuracy"] = (
        sum(1 for r in unans if r["refusal_label"] == "refusal") / len(unans)
        if unans else None)
    ans = [r for r in rows if r.get("question_type") != "unanswerable"
           and r.get("refusal_label")]
    out["false_refusal_rate"] = (
        sum(1 for r in ans if r["refusal_label"] == "refusal") / len(ans)
        if ans else None)
    kg = [r.get("kg_source_rate") for r in rows if r.get("kg_source_rate") is not None]
    out["kg_source_rate"] = _mean(kg)
    for f in ("query_latency", "chat_latency"):
        vals = [r.get(f) for r in rows if r.get(f) is not None]
        out[f + "_p50"] = percentile(vals, 50)
        out[f + "_p95"] = percentile(vals, 95)
    return out


def aggregate(rows):
    """rows = list per-item dict (đã có dataset/mode/question_type + metric)."""
    rows = [r for r in rows if not r.get("error")]
    groups = {}
    for r in rows:
        for key in [
            ("ALL", r.get("mode", "?"), "ALL"),
            (r.get("dataset", "?"), r.get("mode", "?"), "ALL"),
            (r.get("dataset", "?"), r.get("mode", "?"), r.get("question_type", "?")),
            ("ALL", r.get("mode", "?"), r.get("question_type", "?")),
        ]:
            groups.setdefault(key, []).append(r)
    return {"|".join(k): _agg_group(v) for k, v in groups.items()}


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------

def selftest():
    checks = []

    def ck(name, cond):
        checks.append((name, bool(cond)))

    ck("f1 giống hệt = 1", abs(token_f1("RAG là kỹ thuật", "RAG là kỹ thuật") - 1) < 1e-9)
    ck("f1 rời rạc = 0", token_f1("hoàn toàn khác", "RAG embedding") == 0.0)
    ck("f1 một phần", abs(token_f1("RAG là kỹ thuật truy xuất", "RAG là gì") - 0.5) < 0.26)
    ck("em normalize dấu câu", exact_match("Đúng, rồi!", "đúng rồi") == 1.0)
    ck("em khác = 0", exact_match("có", "không") == 0.0)
    ck("partial chứa trọn", partial_match("Câu trả lời là 42 nhé bạn", "42") == 1.0)
    ck("partial thiếu = 0", partial_match("không rõ", "42 nghìn tỷ") == 0.0)
    ck("hit@1 đầu tiên", hit_at([True, False], 1) == 1.0)
    ck("hit@1 miss", hit_at([False, True], 1) == 0.0)
    ck("hit@3 rank3", hit_at([False, False, True], 3) == 1.0)
    ck("mrr rank1", mrr([True]) == 1.0)
    ck("mrr rank2 = 0.5", mrr([False, True]) == 0.5)
    ck("mrr none = 0", mrr([False, False]) == 0.0)
    ck("precision 2/4", context_precision([True, False, True, False]) == 0.5)
    ck("recall 1/2", context_recall(1, 2) == 0.5)
    ck("kw hit 1/2", keyword_hit("có transformer ở đây", ["transformer", "bert"]) == 0.5)
    ck("kw none = None", keyword_hit("abc", []) is None)
    ck("faithfulness 2/3", abs(faithfulness(["supported", "supported", "unsupported"]) - 2 / 3) < 1e-9)
    ck("faithfulness rỗng = None", faithfulness([]) is None)
    ck("tokenize VI dấu", vi_tokenize("Chi phí: 5 tỷ (VNĐ)!") == ["chi", "phí", "5", "tỷ", "vnđ"])
    agg = aggregate([
        {"dataset": "self", "mode": "hybrid", "question_type": "single",
         "token_f1": 1.0, "llm_correct": 5, "faithfulness": 1.0, "refusal_label": "attempt"},
        {"dataset": "self", "mode": "hybrid", "question_type": "unanswerable",
         "refusal_label": "refusal"},
    ])
    g = agg["self|hybrid|ALL"]
    ck("agg n=2", g["n"] == 2)
    ck("agg correct_rate", g["correct_rate"] == 1.0)
    ck("agg refusal_accuracy", g["refusal_accuracy"] == 1.0)
    ck("agg false_refusal", g["false_refusal_rate"] == 0.0)

    npass = sum(1 for _, c in checks if c)
    for name, cond in checks:
        print("  %s %s" % ("✅" if cond else "❌", name))
    print("  [metrics-selftest] TỔNG: %d PASS / %d FAIL / 0 WARN"
          % (npass, len(checks) - npass))
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print("dùng: python3 metrics.py --selftest")
