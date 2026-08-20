#!/usr/bin/env python3
"""rageval/judge.py — LLM-judge (Gemini 2.5 Flash, temp 0, JSON mode), prompt tiếng Việt.

7 judge: correctness 1-5, claim-extraction, groundedness, answer-relevance,
context-relevance, refusal, answerability. Mọi call cache theo sha1(prompt_version
+ judge + payload) trong cache/judge-cache.jsonl → re-run miễn phí.

python3 judge.py --fixtures  → chạy bộ case đóng (datasets/fixtures.jsonl) xác minh judge.
"""
import os
import sys

from common import HERE, JsonlCache, gemini_generate, log, read_jsonl, sha1

PROMPT_VERSION = "v1"
_cache = JsonlCache(os.path.join(HERE, "cache", "judge-cache.jsonl"))

SYSTEM = ("Bạn là giám khảo đánh giá hệ thống hỏi-đáp tài liệu tiếng Việt. "
          "Chỉ trả về JSON đúng schema yêu cầu, không giải thích thêm.")


def _cached(judge_name, payload_key, prompt, max_tokens=2048):
    key = sha1(PROMPT_VERSION, judge_name, payload_key)
    hit = _cache.get(key)
    if hit is not None:
        return hit
    out = gemini_generate(prompt, system=SYSTEM, max_tokens=max_tokens)
    _cache.put(key, out)
    return out


# ---------------------------------------------------------------------------
# Các judge
# ---------------------------------------------------------------------------

def judge_correctness(question, golden, answer):
    """→ {"score": 1-5, "reason": str}"""
    prompt = f"""Chấm độ ĐÚNG của câu trả lời so với ĐÁP ÁN CHUẨN (không dùng kiến thức ngoài).

Thang điểm:
5 = đúng và đầy đủ so với đáp án chuẩn
4 = đúng, chỉ thiếu chi tiết nhỏ
3 = đúng một phần, có ý sai hoặc thiếu ý quan trọng
2 = phần lớn sai
1 = sai hoàn toàn hoặc lạc đề
Lưu ý: số liệu/tên riêng sai so với đáp án chuẩn → tối đa 2 điểm.

CÂU HỎI: {question}
ĐÁP ÁN CHUẨN: {golden}
CÂU TRẢ LỜI CẦN CHẤM: {answer}

Trả về JSON: {{"score": <1-5>, "reason": "<1 câu>"}}"""
    out = _cached("correctness", sha1(question, golden, answer), prompt)
    return {"score": max(1, min(5, int(out.get("score", 1)))),
            "reason": str(out.get("reason", ""))[:300]}


def extract_claims(answer):
    """→ {"claims": [str]} (≤15 mệnh đề nguyên tử)"""
    prompt = f"""Tách câu trả lời sau thành các MỆNH ĐỀ FACTUAL NGUYÊN TỬ (mỗi mệnh đề tự đứng được,
giữ nguyên tên riêng và số liệu). Bỏ qua câu chào hỏi, câu dẫn, ý kiến chủ quan,
câu từ chối kiểu "tài liệu không có thông tin". Tối đa 15 mệnh đề.

CÂU TRẢ LỜI: {answer}

Trả về JSON: {{"claims": ["...", "..."]}}"""
    out = _cached("claims", sha1(answer), prompt)
    claims = [str(c)[:500] for c in out.get("claims", []) if str(c).strip()][:15]
    return {"claims": claims}


def judge_groundedness(claims, context):
    """→ {"labels": ["supported"|"unsupported", ...]} cùng thứ tự claims"""
    if not claims:
        return {"labels": []}
    numbered = "\n".join(f"{i}. {c}" for i, c in enumerate(claims))
    prompt = f"""Với TỪNG mệnh đề bên dưới, phán quyết:
- "supported"   : ngữ cảnh nêu trực tiếp hoặc suy ra được một cách hiển nhiên
- "unsupported" : KHÔNG có trong ngữ cảnh (kể cả khi đúng ngoài đời thực)

NGỮ CẢNH (những gì hệ thống đã truy xuất):
{context[:24000]}

CÁC MỆNH ĐỀ:
{numbered}

Trả về JSON: {{"labels": [{{"idx": 0, "verdict": "supported"}}, ...]}} — đủ {len(claims)} mệnh đề."""
    out = _cached("grounded", sha1("|".join(claims), context[:24000]), prompt)
    labels = ["unsupported"] * len(claims)
    for row in out.get("labels", []):
        try:
            i = int(row.get("idx", -1))
            if 0 <= i < len(claims) and row.get("verdict") in ("supported", "unsupported"):
                labels[i] = row["verdict"]
        except (TypeError, ValueError):
            pass
    return {"labels": labels}


def judge_answer_relevance(question, answer):
    """→ {"score": 1-5} — câu trả lời có đúng trọng tâm câu hỏi không (không xét đúng/sai)."""
    prompt = f"""Chấm độ LIÊN QUAN của câu trả lời với câu hỏi (KHÔNG xét đúng sai nội dung):
5 = trả lời thẳng, đúng trọng tâm câu hỏi
4 = đúng trọng tâm nhưng lan man
3 = trả lời một phần trọng tâm
2 = chủ yếu lạc đề
1 = hoàn toàn lạc đề hoặc né tránh không lý do

CÂU HỎI: {question}
CÂU TRẢ LỜI: {answer}

Trả về JSON: {{"score": <1-5>}}"""
    out = _cached("ans_rel", sha1(question, answer), prompt)
    return {"score": max(1, min(5, int(out.get("score", 1))))}


def judge_context_relevance(question, golden, chunks):
    """chunks: list str → {"relevant_idx": [int]}"""
    if not chunks:
        return {"relevant_idx": []}
    numbered = "\n\n".join(f"[{i}] {c[:1200]}" for i, c in enumerate(chunks))
    prompt = f"""Câu hỏi: {question}
Đáp án chuẩn (để định hướng): {golden}

Với từng đoạn văn bên dưới, đoạn nào CHỨA THÔNG TIN GIÚP TRẢ LỜI TRỰC TIẾP câu hỏi?

{numbered}

Trả về JSON: {{"relevant_idx": [<các chỉ số đoạn liên quan>]}}"""
    out = _cached("ctx_rel", sha1(question, golden, "|".join(c[:200] for c in chunks)), prompt)
    idx = []
    for i in out.get("relevant_idx", []):
        try:
            i = int(i)
            if 0 <= i < len(chunks):
                idx.append(i)
        except (TypeError, ValueError):
            pass
    return {"relevant_idx": sorted(set(idx))}


def judge_refusal(answer):
    """→ {"label": "refusal"|"attempt"|"partial"}"""
    prompt = f"""Phân loại câu trả lời sau:
- "refusal" : từ chối trả lời / nói tài liệu không có thông tin, KHÔNG đưa nội dung trả lời thực chất
- "attempt" : đưa ra nội dung trả lời thực chất
- "partial" : vừa nói không chắc/thiếu thông tin, vừa đoán ra một phần nội dung

CÂU TRẢ LỜI: {answer}

Trả về JSON: {{"label": "refusal|attempt|partial"}}"""
    out = _cached("refusal", sha1(answer), prompt)
    label = out.get("label", "attempt")
    return {"label": label if label in ("refusal", "attempt", "partial") else "attempt"}


def judge_answerability(question, context):
    """→ {"answerable": bool} — dùng khi build câu unanswerable."""
    prompt = f"""Ngữ cảnh truy xuất được:
{context[:20000]}

Câu hỏi: {question}

Ngữ cảnh trên có ĐỦ THÔNG TIN để trả lời câu hỏi không (không dùng kiến thức ngoài)?
Trả về JSON: {{"answerable": true|false}}"""
    out = _cached("answerable", sha1(question, context[:20000]), prompt)
    return {"answerable": bool(out.get("answerable", False))}


# ---------------------------------------------------------------------------
# Fixture battery
# ---------------------------------------------------------------------------

def run_fixtures():
    path = os.path.join(HERE, "datasets", "fixtures.jsonl")
    fixtures = read_jsonl(path)
    if not fixtures:
        print("❌ thiếu datasets/fixtures.jsonl")
        return 2
    npass = nfail = 0
    for fx in fixtures:
        kind = fx["kind"]
        want = fx["expect"]
        got, ok = None, False
        if kind == "correctness":
            got = judge_correctness(fx["question"], fx["golden"], fx["answer"])["score"]
            ok = eval_expect(got, want)
        elif kind == "refusal":
            got = judge_refusal(fx["answer"])["label"]
            ok = got == want
        elif kind == "faithfulness":
            claims = extract_claims(fx["answer"])["claims"]
            labels = judge_groundedness(claims, fx["context"])["labels"]
            sup = sum(1 for l in labels if l == "supported")
            got = round(sup / len(labels), 2) if labels else None
            ok = got is not None and eval_expect(got, want)
        elif kind == "answer_relevance":
            got = judge_answer_relevance(fx["question"], fx["answer"])["score"]
            ok = eval_expect(got, want)
        elif kind == "answerability":
            got = judge_answerability(fx["question"], fx["context"])["answerable"]
            ok = got == want
        mark = "✅" if ok else "❌"
        npass += ok
        nfail += (not ok)
        log("  %s [%s] %s → %r (kỳ vọng %s)" % (mark, kind, fx["id"], got, want))
    log("  [judge-fixtures] TỔNG: %d PASS / %d FAIL / 0 WARN" % (npass, nfail))
    return 0 if nfail == 0 else 1


def eval_expect(got, want):
    """want dạng ">=4", "<=2", "<=0.75", "==5"."""
    op = want[:2]
    val = float(want[2:])
    return {"<=": got <= val, ">=": got >= val, "==": got == val}[op]


if __name__ == "__main__":
    if "--fixtures" in sys.argv:
        sys.exit(run_fixtures())
    print("dùng: python3 judge.py --fixtures")
