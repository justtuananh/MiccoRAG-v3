#!/usr/bin/env python3
"""rageval/build_hf.py — lấy HotpotQA (distractor/validation) qua HF datasets-server REST.

Không cần cài `datasets` — chỉ HTTPS stdlib. Đầu ra (trong --out):
  hf_raw.jsonl     : ~N item EN {orig_id, question, answer, hop_type, level,
                     gold_titles[], gold_paragraphs[], distractor_titles[]}
  corpus_raw.jsonl : các đoạn văn duy nhất {title, text, is_gold}

Lọc: yes/no ≤ 30%, cân bridge/comparison, answer ≤ 60 chars, cân level.
"""
import argparse
import json
import os
import random
import sys
import urllib.request

from common import log, append_jsonl

API = ("https://datasets-server.huggingface.co/rows?dataset=hotpotqa%2Fhotpot_qa"
       "&config=distractor&split=validation&offset={off}&length=100")
random.seed(20260723)


def fetch_rows(total):
    rows = []
    for off in range(0, total, 100):
        url = API.format(off=off)
        req = urllib.request.Request(url, headers={"User-Agent": "rageval/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        batch = [r["row"] for r in data.get("rows", [])]
        rows.extend(batch)
        log("  fetch offset %d → %d rows" % (off, len(batch)))
        if not batch:
            break
    return rows


def convert(row, n_distractors):
    titles = row["context"]["title"]
    sents = row["context"]["sentences"]
    para = {t: "".join(s) for t, s in zip(titles, sents)}
    gold_titles = sorted(set(row["supporting_facts"]["title"]))
    if not all(t in para for t in gold_titles):
        return None
    distractors = [t for t in titles if t not in gold_titles]
    random.shuffle(distractors)
    distractors = distractors[:n_distractors]
    return {
        "orig_id": row["id"], "question": row["question"].strip(),
        "answer": row["answer"].strip(), "hop_type": row.get("type", ""),
        "level": row.get("level", ""),
        "gold_titles": gold_titles,
        "gold_paragraphs": [para[t] for t in gold_titles],
        "distractor_titles": distractors,
        "distractor_paragraphs": [para[t] for t in distractors],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=130, help="số item ứng viên đầu ra")
    ap.add_argument("--fetch", type=int, default=400, help="số row tải về để lọc")
    ap.add_argument("--distractors", type=int, default=4, help="distractor/item đưa vào corpus")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "datasets", "review", "hf_work"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    rows = fetch_rows(args.fetch)
    log("  tổng %d rows" % len(rows))
    items = [x for x in (convert(r, args.distractors) for r in rows) if x]
    # lọc: answer ngắn, hạn chế yes/no
    items = [it for it in items if len(it["answer"]) <= 60]
    yesno = [it for it in items if it["answer"].lower() in ("yes", "no")]
    other = [it for it in items if it["answer"].lower() not in ("yes", "no")]
    max_yesno = int(args.n * 0.3)
    random.shuffle(yesno)
    random.shuffle(other)
    # cân bridge/comparison trong nhóm other
    bridge = [it for it in other if it["hop_type"] == "bridge"]
    comp = [it for it in other if it["hop_type"] == "comparison"]
    n_other = args.n - min(len(yesno), max_yesno)
    take_comp = min(len(comp), n_other // 3)
    chosen = comp[:take_comp] + bridge[:n_other - take_comp] + yesno[:max_yesno]
    chosen = chosen[:args.n]
    log("  chọn %d item (bridge %d / comparison %d / yesno %d)" % (
        len(chosen), sum(1 for i in chosen if i["hop_type"] == "bridge"
                         and i["answer"].lower() not in ("yes", "no")),
        take_comp, sum(1 for i in chosen if i["answer"].lower() in ("yes", "no"))))

    raw_path = os.path.join(args.out, "hf_raw.jsonl")
    corpus_path = os.path.join(args.out, "corpus_raw.jsonl")
    for p in (raw_path, corpus_path):
        if os.path.exists(p):
            os.remove(p)
    corpus = {}
    for it in chosen:
        append_jsonl(raw_path, it)
        for t, p in zip(it["gold_titles"], it["gold_paragraphs"]):
            corpus.setdefault(t, {"title": t, "text": p, "is_gold": True})
            corpus[t]["is_gold"] = True
        for t, p in zip(it["distractor_titles"], it["distractor_paragraphs"]):
            corpus.setdefault(t, {"title": t, "text": p, "is_gold": False})
    for c in corpus.values():
        append_jsonl(corpus_path, c)
    total_chars = sum(len(c["text"]) for c in corpus.values())
    log("  📄 %s (%d item) · %s (%d đoạn, ~%dk chars ≈ %dk token)" % (
        raw_path, len(chosen), corpus_path, len(corpus),
        total_chars // 1000, total_chars // 4000))
    return 0


if __name__ == "__main__":
    sys.exit(main())
