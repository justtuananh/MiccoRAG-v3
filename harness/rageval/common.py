#!/usr/bin/env python3
"""rageval/common.py — thư viện dùng chung cho bộ benchmark rageval (MiccoRAG-v3).

Zero external deps (stdlib). Cung cấp:
  - http_json()        : gọi backend NexusRAG (Bearer dev-skip) với retry/backoff
  - gemini_generate()  : gọi Gemini REST v1beta (JSON mode, temp 0) — key đọc từ backend/.env
  - gemini_embed()     : batch embedding gemini-embedding-001 + cosine()
  - vi_tokenize()/normalize_answer(): chuẩn hóa tiếng Việt cho F1/EM
  - read_jsonl/append_jsonl + JsonlCache (cache append-only, resume-safe)
  - pmap()             : ThreadPool có trần concurrency (mặc định 2, cap 4)
"""
import hashlib
import json
import os
import re
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(HERE))          # /home/kms/MiccoRAG-v3
BACKEND_ENV = os.path.join(PROJECT_ROOT, "micco-backend", "backend", ".env")

BASE = os.environ.get("HARNESS_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
AUTH = {"Authorization": "Bearer dev-skip", "Content-Type": "application/json"}
HTTP_TIMEOUT = int(os.environ.get("RAGEVAL_HTTP_TIMEOUT", "180"))
CONCURRENCY = min(int(os.environ.get("RAGEVAL_CONCURRENCY", "2")), 4)

GEMINI_MODEL = os.environ.get("RAGEVAL_JUDGE_MODEL", "gemini-2.5-flash")
EMBED_MODEL = os.environ.get("RAGEVAL_EMBED_MODEL", "gemini-embedding-001")
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Giá tham khảo gemini-2.5-flash (USD / 1M token) để ước lượng chi phí trong report
PRICE_IN_PER_M = 0.30
PRICE_OUT_PER_M = 2.50

_print_lock = threading.Lock()


def log(msg):
    with _print_lock:
        print(msg, flush=True)


# ---------------------------------------------------------------------------
# Backend HTTP
# ---------------------------------------------------------------------------

def http_json(method, path, body=None, timeout=None, retries=2):
    """Gọi backend. Trả (status, parsed_body). Retry trên 429/5xx/timeout."""
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    last = (0, None)
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=AUTH, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout or HTTP_TIMEOUT) as resp:
                raw = resp.read().decode()
                return resp.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            try:
                payload = json.loads(e.read().decode())
            except Exception:
                payload = None
            last = (e.code, payload)
            if e.code not in (429, 500, 502, 503, 504):
                return last
        except Exception as e:
            last = (0, str(e))
        if attempt < retries:
            time.sleep(2 ** attempt * 3)
    return last


def upload_file(path, workspace_id, filename=None, timeout=120):
    """Upload multipart lên POST /api/v1/documents/upload/{ws} (stdlib, không requests)."""
    boundary = "----rageval%s" % hashlib.sha1(os.urandom(8)).hexdigest()[:12]
    name = filename or os.path.basename(path)
    with open(path, "rb") as f:
        content = f.read()
    body = b"".join([
        ("--%s\r\n" % boundary).encode(),
        ('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % name).encode(),
        b"Content-Type: application/octet-stream\r\n\r\n",
        content,
        ("\r\n--%s--\r\n" % boundary).encode(),
    ])
    req = urllib.request.Request(
        BASE + "/api/v1/documents/upload/%d" % workspace_id, data=body, method="POST",
        headers={"Authorization": "Bearer dev-skip",
                 "Content-Type": "multipart/form-data; boundary=%s" % boundary})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, None


# ---------------------------------------------------------------------------
# Gemini REST
# ---------------------------------------------------------------------------

_gemini_key = None


def load_gemini_key():
    global _gemini_key
    if _gemini_key:
        return _gemini_key
    key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if not key and os.path.exists(BACKEND_ENV):
        with open(BACKEND_ENV, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^GOOGLE_AI_API_KEY\s*=\s*(.+)$", line.strip())
                if m:
                    key = m.group(1).strip().strip('"').strip("'")
                    break
    if not key:
        raise RuntimeError("Không tìm thấy GOOGLE_AI_API_KEY (env hoặc backend/.env)")
    _gemini_key = key
    return key


def _gemini_post(path, payload, timeout=90, retries=3):
    url = "%s/%s?key=%s" % (GEMINI_BASE, path, load_gemini_key())
    data = json.dumps(payload).encode()
    last_err = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode())
            except Exception:
                err = {"error": {"message": str(e)}}
            last_err = err
            if e.code == 429:
                delay = 15
                msg = json.dumps(err)
                m = re.search(r'"retryDelay"\s*:\s*"(\d+)', msg)
                if m:
                    delay = max(int(m.group(1)), 5)
                time.sleep(delay)
                continue
            if e.code >= 500:
                time.sleep(2 ** attempt * 5)
                continue
            raise RuntimeError("Gemini HTTP %d: %s" % (e.code, json.dumps(err)[:300]))
        except Exception as e:
            last_err = {"error": {"message": str(e)}}
            time.sleep(2 ** attempt * 3)
    raise RuntimeError("Gemini thất bại sau retry: %s" % json.dumps(last_err)[:300])


def gemini_generate(prompt, system=None, model=None, temp=0.0, json_mode=True,
                    max_tokens=4096, timeout=90):
    """Sinh text/JSON. json_mode=True → parse JSON (tự sửa fence, retry parse 1 lần)."""
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temp, "maxOutputTokens": max_tokens},
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"
    for attempt in range(2):
        out = _gemini_post("models/%s:generateContent" % (model or GEMINI_MODEL),
                           payload, timeout=timeout)
        try:
            parts = out["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError):
            text = ""
        if not json_mode:
            return text
        cleaned = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            if attempt == 0:
                payload["contents"][0]["parts"][0]["text"] = (
                    prompt + "\n\nCHÚ Ý: lần trước trả về JSON không hợp lệ. "
                    "Chỉ trả về đúng một object JSON hợp lệ.")
                continue
            raise RuntimeError("Gemini JSON parse lỗi: %r" % text[:200])


def gemini_embed(texts, model=None, task_type="SEMANTIC_SIMILARITY"):
    """Batch embed (chia lô 50). Trả list vector."""
    model = model or EMBED_MODEL
    out = []
    for i in range(0, len(texts), 50):
        batch = texts[i:i + 50]
        payload = {"requests": [
            {"model": "models/%s" % model,
             "content": {"parts": [{"text": t[:8000]}]},
             "taskType": task_type}
            for t in batch]}
        resp = _gemini_post("models/%s:batchEmbedContents" % model, payload, timeout=60)
        out.extend([e["values"] for e in resp["embeddings"]])
    return out


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


# ---------------------------------------------------------------------------
# Chuẩn hóa tiếng Việt
# ---------------------------------------------------------------------------

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_WS = re.compile(r"\s+")


def normalize_answer(s):
    s = unicodedata.normalize("NFC", (s or "").lower())
    s = _PUNCT.sub(" ", s)
    return _WS.sub(" ", s).strip()


def vi_tokenize(s):
    return normalize_answer(s).split()


# ---------------------------------------------------------------------------
# JSONL + cache
# ---------------------------------------------------------------------------

def read_jsonl(path):
    items = []
    if not os.path.exists(path):
        return items
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return items


def append_jsonl(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()


class JsonlCache:
    """Cache append-only key→value, thread-safe, resume xuyên run."""

    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        self._data = {}
        for row in read_jsonl(path):
            if "k" in row:
                self._data[row["k"]] = row.get("v")

    def get(self, key):
        return self._data.get(key)

    def put(self, key, value):
        with self._lock:
            if key in self._data:
                return
            self._data[key] = value
            append_jsonl(self.path, {"k": key, "v": value})

    def __contains__(self, key):
        return key in self._data

    def __len__(self):
        return len(self._data)


def sha1(*parts):
    h = hashlib.sha1()
    for p in parts:
        h.update(str(p).encode("utf-8", "ignore"))
        h.update(b"\x00")
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Song song có trần
# ---------------------------------------------------------------------------

def pmap(fn, items, workers=None, label=None):
    """Chạy fn(item) song song, giữ thứ tự. Exception → {'__error__': str}."""
    workers = min(workers or CONCURRENCY, 4)
    results = [None] * len(items)
    done = [0]

    def _run(i, it):
        try:
            results[i] = fn(it)
        except Exception as e:
            results[i] = {"__error__": "%s: %s" % (type(e).__name__, e)}
        done[0] += 1
        if label and done[0] % 10 == 0:
            log("    ... %s %d/%d" % (label, done[0], len(items)))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_run, i, it) for i, it in enumerate(items)]
        for f in futs:
            f.result()
    return results


def percentile(vals, p):
    if not vals:
        return 0.0
    vs = sorted(vals)
    idx = min(int(round(p / 100.0 * (len(vs) - 1))), len(vs) - 1)
    return vs[idx]


def now_ts():
    return time.strftime("%Y%m%d-%H%M%S")


if __name__ == "__main__":
    # tự kiểm tra nhanh (không network trừ khi --net)
    assert vi_tokenize("Xin chào, thế-giới!") == ["xin", "chào", "thế", "giới"]
    assert normalize_answer("  RAG   và  Fine-tuning. ") == "rag và fine tuning"
    assert abs(cosine([1, 0], [1, 0]) - 1.0) < 1e-9
    print("common.py OK")
    if "--net" in sys.argv:
        load_gemini_key()
        print("key: OK (đọc được, không in)")
        r = gemini_generate('Trả về JSON {"ping": "pong"}')
        print("gemini:", r)
