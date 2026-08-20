#!/usr/bin/env python3
"""Benchmark driver — MiccoRAG-v3 RAG latency theo search mode.

Đo latency (wall clock) của POST /api/v1/rag/query cho từng mode {hybrid, vector_only,
naive}. Tự động hoá lại phương pháp đo thủ công trong benchmark_report.md. Zero deps.

Env: HARNESS_BASE_URL, BENCH_WORKSPACE (default 1), BENCH_MODES (default hybrid,vector_only),
     BENCH_QUERIES (số câu, default 3), BENCH_JSON, BENCH_MD
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("HARNESS_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
AUTH = {"Authorization": "Bearer dev-skip", "Content-Type": "application/json"}
WS = int(os.environ.get("BENCH_WORKSPACE", "1"))
MODES = [m.strip() for m in os.environ.get("BENCH_MODES", "hybrid,vector_only").split(",") if m.strip()]
NQ = int(os.environ.get("BENCH_QUERIES", "3"))

QUESTIONS = [
    "RAG và Fine-tuning khác nhau thế nào?",
    "Khi nào nên ưu tiên sử dụng RAG?",
    "Embedding và vector search dùng để làm gì?",
    "Mô hình ngôn ngữ lớn (LLM) là gì?",
    "Cơ chế truy xuất tài liệu trong RAG?",
][:NQ]


def query(mode, q, timeout=180):
    url = BASE + f"/api/v1/rag/query/{WS}"
    data = json.dumps({"question": q, "top_k": 5, "mode": mode}).encode()
    r = urllib.request.Request(url, data=data, headers=AUTH, method="POST")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            body = json.loads(resp.read().decode() or "{}")
            code = resp.status
    except urllib.error.HTTPError as e:
        body, code = {}, e.code
    except Exception:
        body, code = {}, 0
    dt = time.monotonic() - t0
    return code, dt, (body.get("total_chunks", 0) if isinstance(body, dict) else 0)


def pct(xs, p):
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def main():
    print(f"Bench: ws={WS}  modes={MODES}  nq={len(QUESTIONS)}  backend={BASE}")
    print("─" * 74)
    results = {}
    for mode in MODES:
        lat, chunks, okc = [], [], 0
        for q in QUESTIONS:
            code, dt, tc = query(mode, q)
            if code == 200:
                okc += 1
                lat.append(dt)
                chunks.append(tc)
            print(f"  [{mode:11}] {dt:6.2f}s  code={code} chunks={tc}  {q[:38]}")
        if lat:
            results[mode] = {"n": len(lat), "ok": okc, "avg": sum(lat) / len(lat),
                             "p50": pct(lat, 50), "p95": pct(lat, 95), "min": min(lat),
                             "max": max(lat), "avg_chunks": sum(chunks) / len(chunks)}
        else:
            results[mode] = {"n": 0, "ok": okc, "avg": 0, "p50": 0, "p95": 0, "min": 0, "max": 0, "avg_chunks": 0}
    print("─" * 74)
    print(f"  {'mode':12} {'n':>2} {'avg':>7} {'p50':>7} {'p95':>7} {'min':>7} {'max':>7} {'chunks':>7}")
    for m, r in results.items():
        print(f"  {m:12} {r['n']:>2} {r['avg']:>6.2f}s {r['p50']:>6.2f}s {r['p95']:>6.2f}s "
              f"{r['min']:>6.2f}s {r['max']:>6.2f}s {r['avg_chunks']:>7.1f}")
    if "hybrid" in results and "vector_only" in results and results["vector_only"]["avg"] > 0:
        sp = results["hybrid"]["avg"] / results["vector_only"]["avg"]
        print(f"\n  hybrid chậm hơn vector_only ~{sp:.1f}×")

    out = {"base": BASE, "workspace": WS, "queries": len(QUESTIONS), "modes": results}
    jp = os.environ.get("BENCH_JSON")
    if jp:
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"  📄 {jp}")
    mp = os.environ.get("BENCH_MD")
    if mp:
        with open(mp, "w", encoding="utf-8") as f:
            f.write(f"# Benchmark MiccoRAG-v3 (ws {WS}, {len(QUESTIONS)} câu)\n\n")
            f.write("| mode | n | avg | p50 | p95 | min | max | avg_chunks |\n|---|--:|--:|--:|--:|--:|--:|--:|\n")
            for m, r in results.items():
                f.write(f"| {m} | {r['n']} | {r['avg']:.2f}s | {r['p50']:.2f}s | {r['p95']:.2f}s "
                        f"| {r['min']:.2f}s | {r['max']:.2f}s | {r['avg_chunks']:.1f} |\n")
        print(f"  📄 {mp}")
    return 0 if any(r["ok"] > 0 for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
