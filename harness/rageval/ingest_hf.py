#!/usr/bin/env python3
"""rageval/ingest_hf.py — đóng gói corpus VI thành .md, ingest vào workspace benchmark riêng.

Bước: pack (40 bài/file, heading `# {title gốc}` → heading_path → gold matching)
  → POST /workspaces (BENCH-HF-HotpotVI, private, kg_language=Vietnamese)
  → upload từng .md (Admin → auto-approved) → POST /rag/process-batch (tuần tự)
  → poll GET /documents/{id} mỗi 20s (budget 12 phút/doc, FAILED retry 1 lần)
  → verify /rag/stats + /rag/entities → datasets/hf_manifest.json + golden_hf.jsonl

Lệnh: python3 ingest_hf.py --in datasets/review/hf_work [--dry-run|--apply]
Teardown khi cần làm lại: DELETE /workspaces/{ws} (xóa sạch Chroma+KG+DB).
"""
import argparse
import json
import os
import sys
import time

from common import HERE, http_json, log, read_jsonl, upload_file

DS_DIR = os.path.join(HERE, "datasets")
WS_NAME = "BENCH-HF-HotpotVI"
PER_FILE = 40
GEN_DATE = time.strftime("%Y-%m-%d")


def pack(indir):
    corpus = read_jsonl(os.path.join(indir, "corpus_vi.jsonl"))
    pack_dir = os.path.join(indir, "pack")
    os.makedirs(pack_dir, exist_ok=True)
    files = []
    for i in range(0, len(corpus), PER_FILE):
        batch = corpus[i:i + PER_FILE]
        name = "wiki_vi_batch_%02d.md" % (i // PER_FILE + 1)
        path = os.path.join(pack_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            for c in batch:
                f.write("# %s\n\n%s\n\n" % (c["title"], c["text_vi"].strip()))
        files.append({"file": name, "path": path,
                      "titles": [c["title"] for c in batch],
                      "chars": sum(len(c["text_vi"]) for c in batch)})
    return files


def wait_indexed(doc_ids, budget_per_doc=720):
    """Poll tuần tự tới khi mọi doc INDEXED/FAILED. Trả {doc_id: status}."""
    status = {d: "processing" for d in doc_ids}
    deadline = time.time() + budget_per_doc * len(doc_ids)
    while time.time() < deadline:
        pending = [d for d, s in status.items()
                   if s not in ("indexed", "failed")]
        if not pending:
            break
        for d in pending:
            st, body = http_json("GET", "/api/v1/documents/%d" % d, timeout=30)
            if st == 200 and isinstance(body, dict):
                status[d] = body.get("status", "?")
        done = sum(1 for s in status.values() if s == "indexed")
        fail = sum(1 for s in status.values() if s == "failed")
        log("  ... indexed %d / failed %d / tổng %d" % (done, fail, len(doc_ids)))
        if not [d for d, s in status.items() if s not in ("indexed", "failed")]:
            break
        time.sleep(20)
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--workspace-id", type=int, default=0,
                    help="dùng ws đã có (resume) thay vì tạo mới")
    args = ap.parse_args()

    files = pack(args.indir)
    total_chars = sum(f["chars"] for f in files)
    log("pack: %d file .md, %d đoạn, ~%dk chars (~%dk token KG-extract)" % (
        len(files), sum(len(f["titles"]) for f in files),
        total_chars // 1000, total_chars // 4000))
    if args.dry_run or not args.apply:
        for f in files:
            log("  - %s: %d bài, %dk chars" % (f["file"], len(f["titles"]),
                                               f["chars"] // 1000))
        log("(dry-run — thêm --apply để ingest thật; ước tính %d-%d phút xử lý)" % (
            len(files) * 2, len(files) * 8))
        return 0

    # 1. workspace
    if args.workspace_id:
        ws = args.workspace_id
        log("  dùng lại workspace %d" % ws)
    else:
        st, body = http_json("POST", "/api/v1/workspaces", {
            "name": WS_NAME,
            "description": "rageval benchmark corpus (HotpotQA-VI) — safe to delete",
            "visibility": "private", "kg_language": "Vietnamese",
            "search_mode": "hybrid"}, timeout=30)
        if st != 201 or not isinstance(body, dict):
            log("❌ tạo workspace thất bại: %s %s" % (st, str(body)[:200]))
            return 2
        ws = body["id"]
        log("  ✅ workspace %d (%s)" % (ws, WS_NAME))

    # 2. upload
    title_to_doc = {}
    doc_ids = []
    for f in files:
        st, body = upload_file(f["path"], ws)
        if st != 200 or not isinstance(body, dict):
            log("❌ upload %s thất bại: %s" % (f["file"], st))
            return 2
        doc_id = body["id"]
        doc_ids.append(doc_id)
        for t in f["titles"]:
            title_to_doc[t] = doc_id
        log("  ⬆️  %s → doc %d" % (f["file"], doc_id))

    # 3. process-batch (backend xử lý tuần tự)
    st, body = http_json("POST", "/api/v1/rag/process-batch",
                         {"document_ids": doc_ids}, timeout=60)
    log("  process-batch: %s %s" % (st, str(body)[:150]))

    # 4. poll + retry FAILED 1 lần
    status = wait_indexed(doc_ids)
    failed = [d for d, s in status.items() if s != "indexed"]
    if failed:
        log("  ⚠️  retry %d doc failed: %s" % (len(failed), failed))
        for d in failed:
            http_json("POST", "/api/v1/rag/process/%d" % d, timeout=60)
        status.update(wait_indexed(failed))
    failed = [d for d, s in status.items() if s != "indexed"]
    if failed:
        log("❌ vẫn còn doc chưa indexed: %s — xử lý tay rồi chạy lại với "
            "--workspace-id %d" % (failed, ws))

    # 5. verify
    st, stats = http_json("GET", "/api/v1/rag/stats/%d" % ws, timeout=30)
    log("  stats: %s" % json.dumps(stats, ensure_ascii=False))
    st, ents = http_json("GET", "/api/v1/rag/entities/%d?limit=10000" % ws, timeout=120)
    n_ents = len(ents) if isinstance(ents, list) else 0
    if n_ents < 200:
        log("  ⚠️  KG thưa: chỉ %d entities (kỳ vọng >200) — Δ GraphRAG có thể thấp" % n_ents)
    else:
        log("  ✅ KG: %d entities" % n_ents)

    # 6. manifest + golden_hf.jsonl
    manifest = {"workspace_id": ws, "workspace_name": WS_NAME, "date": GEN_DATE,
                "files": [{"file": f["file"], "doc_id": title_to_doc[f["titles"][0]],
                           "titles": f["titles"]} for f in files],
                "title_to_doc": title_to_doc,
                "doc_status": {str(k): v for k, v in status.items()},
                "entities": n_ents}
    with open(os.path.join(DS_DIR, "hf_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    items = read_jsonl(os.path.join(args.indir, "hf_translated.jsonl"))
    out_path = os.path.join(DS_DIR, "golden_hf.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# golden_hf.jsonl — HotpotQA distractor/validation dịch VI (%s)\n" % GEN_DATE)
        for i, it in enumerate(items, 1):
            corpus_vi = {c["title"]: c["text_vi"] for c in read_jsonl(
                os.path.join(args.indir, "corpus_vi.jsonl"))}
            row = {
                "id": "hf-%03d" % i, "dataset": "hf", "workspace_id": ws,
                "question": it["question_vi"], "golden_answer": it["answer_vi"],
                "question_type": "multi",
                "gold_doc_ids": sorted({title_to_doc[t] for t in it["gold_titles"]
                                        if t in title_to_doc}),
                "gold_chunk_ids": [],
                "gold_passages": [corpus_vi.get(t, "") for t in it["gold_titles"]],
                "gold_titles": it["gold_titles"],
                "expected_keywords": [], "difficulty": it.get("level", "medium"),
                "provenance": {"source": "hotpotqa/hotpot_qa:distractor:validation",
                               "orig_id": it["orig_id"],
                               "orig_question": it["question"],
                               "orig_answer": it["answer"],
                               "hop_type": it.get("hop_type"),
                               "gen_model": "gemini-2.5-flash", "date": GEN_DATE},
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    log("  ✅ %s (%d item, ws=%d)" % (out_path, len(items), ws))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
