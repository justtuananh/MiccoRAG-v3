#!/usr/bin/env python3
"""Chẩn đoán trạng thái Gemini API: thành công / rate-limit phút / quota ngày."""
import json
import urllib.error
import urllib.request

from common import GEMINI_BASE, load_gemini_key

url = GEMINI_BASE + "/models/gemini-2.5-flash:generateContent?key=" + load_gemini_key()
payload = {"contents": [{"role": "user", "parts": [{"text": "say hi"}]}],
           "generationConfig": {"temperature": 0}}
req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                            headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("OK — Gemini phản hồi bình thường")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print("HTTP", e.code)
    try:
        j = json.loads(body)
        err = j.get("error", {})
        print("status:", err.get("status"))
        print("message:", err.get("message", "")[:300])
        for d in err.get("details", []):
            if "quotaMetric" in json.dumps(d) or "QuotaFailure" in d.get("@type", ""):
                print("quota detail:", json.dumps(d)[:400])
            if "retryDelay" in json.dumps(d):
                print("retry:", json.dumps(d)[:200])
    except Exception:
        print(body[:500])
