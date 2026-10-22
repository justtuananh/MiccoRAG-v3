"""Summarize staged pilot evidence without reusing old manual judgements."""
import json
import re
from pathlib import Path

evidence = Path(__file__).parent
pilot = json.loads((evidence / "rag-pilot-results.json").read_text())
rows = []

for record in pilot["results"]:
    if record["case_id"] != "G04":
        continue
    obj = record.get("response", {})
    if record["variant"] == "stream":
        obj = next(
            (event["data"] for event in record.get("events", []) if event.get("event") == "complete"),
            {},
        )
    body = obj.get("context", "") if record["variant"] == "query" else obj.get("answer", "")
    lower = body.lower()
    required = {"500": "500" in lower, "20": "20" in lower,
                "giám đốc": "giám đốc" in lower, "đấu thầu": "đấu thầu" in lower}
    sources = obj.get("sources") or []
    ids = {str(source.get("index")) for source in sources}
    cited = re.findall(r"\[\s*([a-zA-Z0-9]{4})\s*\]", body)
    rows.append({
        "variant": record["variant"], "role": record["role"], "repeat": record["repeat"],
        "status_code": record.get("status_code"), "has_complete_event": bool(obj) if record["variant"] == "stream" else None,
        "required_found": required, "all_required_found": all(required.values()),
        "source_ids": sorted(ids), "citation_ids": cited,
        "unresolved_citation_ids": [item for item in cited if item not in ids],
        "body": body,
    })

report = {
    "run_id": pilot["run_id"],
    "g04_variants": len(rows),
    "g04_all_required_variants": sum(row["all_required_found"] for row in rows),
    "g04_unresolved_citation_variants": sum(bool(row["unresolved_citation_ids"]) for row in rows),
    "g04_http_failures": sum(row["status_code"] != 200 for row in rows),
    "rows": rows,
}
(evidence / "g04-graded-stage.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({key: report[key] for key in report if key != "rows"}, ensure_ascii=False))
