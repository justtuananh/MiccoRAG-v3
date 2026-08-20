#!/usr/bin/env python3
"""rageval/translate.py — dịch HotpotQA EN→VI bằng Gemini (temp 0, cache resume).

Đọc hf_raw.jsonl + corpus_raw.jsonl (từ build_hf.py), ghi:
  corpus_vi.jsonl    : {title (GIỮ NGUYÊN), text_vi, is_gold}
  hf_translated.jsonl: hf_raw + {question_vi, answer_vi}
  hf_translate_sample.md : 20 mẫu EN↔VI để user skim

Quy tắc: giữ nguyên tên riêng/tác phẩm/địa danh dạng gốc (Latin) — để entity matching
của LightRAG và gold-matching theo title còn hoạt động.
QC: loại item có bản dịch rỗng / lệch độ dài >3x / còn nguyên tiếng Anh.
"""
import argparse
import os
import random
import sys

from common import (HERE, JsonlCache, gemini_generate, log, pmap, read_jsonl,
                    append_jsonl, sha1)

_cache = JsonlCache(os.path.join(HERE, "cache", "translate-cache.jsonl"))
random.seed(20260723)

RULES = ("Giữ NGUYÊN mọi tên riêng, tên người, tên tác phẩm, địa danh, tên tổ chức "
         "ở dạng gốc (chữ Latin, không phiên âm). Dịch tự nhiên, chính xác tuyệt đối "
         "số liệu, năm, thứ tự.")


def translate_paragraph(title, text):
    key = sha1("para", title, text[:6000])
    hit = _cache.get(key)
    if hit is not None:
        return hit
    out = gemini_generate(
        f"""Dịch đoạn văn bách khoa sau sang tiếng Việt. {RULES}

TIÊU ĐỀ (không dịch): {title}
ĐOẠN VĂN:
{text[:6000]}

Trả về JSON: {{"vi": "<bản dịch>"}}""", max_tokens=4096)
    vi = out.get("vi", "")
    _cache.put(key, vi)
    return vi


def translate_qa(question, answer):
    key = sha1("qa", question, answer)
    hit = _cache.get(key)
    if hit is not None:
        return hit
    out = gemini_generate(
        f"""Dịch cặp câu hỏi - đáp án sau sang tiếng Việt. {RULES}
Đáp án dịch NGẮN GỌN đúng như bản gốc (nếu là "yes"/"no" thì dịch "có"/"không";
nếu là tên riêng thì GIỮ NGUYÊN).

CÂU HỎI: {question}
ĐÁP ÁN: {answer}

Trả về JSON: {{"question_vi": "...", "answer_vi": "..."}}""", max_tokens=1024)
    val = {"question_vi": out.get("question_vi", ""), "answer_vi": out.get("answer_vi", "")}
    _cache.put(key, val)
    return val


def mostly_english(s):
    if not s:
        return True
    ascii_letters = sum(1 for c in s if c.isascii() and c.isalpha())
    letters = sum(1 for c in s if c.isalpha())
    return letters > 20 and ascii_letters / letters > 0.9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--keep", type=int, default=100)
    args = ap.parse_args()

    corpus = read_jsonl(os.path.join(args.indir, "corpus_raw.jsonl"))
    items = read_jsonl(os.path.join(args.indir, "hf_raw.jsonl"))
    log("dịch corpus %d đoạn + %d cặp Q/A..." % (len(corpus), len(items)))

    para_vi = pmap(lambda c: translate_paragraph(c["title"], c["text"]),
                   corpus, label="para")
    corpus_out = os.path.join(args.indir, "corpus_vi.jsonl")
    if os.path.exists(corpus_out):
        os.remove(corpus_out)
    bad_titles = set()
    for c, vi in zip(corpus, para_vi):
        if isinstance(vi, dict) and vi.get("__error__"):
            vi = ""
        ratio = (len(vi) / len(c["text"])) if c["text"] else 0
        if not vi or ratio < 0.3 or ratio > 3.0:
            bad_titles.add(c["title"])
            continue
        append_jsonl(corpus_out, {"title": c["title"], "text_vi": vi,
                                  "is_gold": c["is_gold"]})
    if bad_titles:
        log("  ⚠️  %d đoạn dịch hỏng (loại): %s" % (len(bad_titles),
                                                    list(bad_titles)[:5]))

    qa_vi = pmap(lambda it: translate_qa(it["question"], it["answer"]),
                 items, label="qa")
    out_path = os.path.join(args.indir, "hf_translated.jsonl")
    if os.path.exists(out_path):
        os.remove(out_path)
    kept = []
    for it, qa in zip(items, qa_vi):
        if not isinstance(qa, dict) or qa.get("__error__"):
            continue
        qv, av = qa.get("question_vi", ""), qa.get("answer_vi", "")
        if not qv or not av or mostly_english(qv):
            continue
        if any(t in bad_titles for t in it["gold_titles"]):
            continue
        it2 = dict(it)
        it2["question_vi"], it2["answer_vi"] = qv, av
        kept.append(it2)
    random.shuffle(kept)
    kept = kept[:args.keep]
    for it in kept:
        append_jsonl(out_path, it)
    log("  giữ %d/%d item sau QC → %s" % (len(kept), len(items), out_path))

    sample = random.sample(kept, min(20, len(kept)))
    md = os.path.join(args.indir, "hf_translate_sample.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Mẫu dịch EN↔VI (skim nhanh)\n\n")
        for it in sample:
            f.write("- **EN:** %s → *%s*\n  **VI:** %s → *%s*\n\n" % (
                it["question"], it["answer"], it["question_vi"], it["answer_vi"]))
    log("  📄 %s (20 mẫu)" % md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
