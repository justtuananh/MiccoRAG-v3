"""Grounded checks for the 22 staged answers reviewed against three originals."""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
groups = [
    json.loads((HERE / "rag-pilot-results.json").read_text()),
    json.loads((HERE / "rag-stream-results.json").read_text()),
]


def facts(case_id: str, answer: str) -> dict[str, bool]:
    text = answer.lower()
    has = lambda *terms: all(term in text for term in terms)
    if case_id == "G01":
        return {"amount": has("1.250.000"), "not_bhxh_basis": has("không", "bảo hiểm xã hội")}
    if case_id == "G02":
        return {"14_day_exclusion": has("14", "không", "phụ cấp"), "in_kind_not_cash": has("hiện vật", "không", "tiền")}
    if case_id == "G03":
        return {"review_day_25": has("25", "nhân sự")}
    if case_id == "G04":
        return {"threshold_500": has("500", "từ"), "requires_tender": has("đấu thầu"),
                "director_approves": has("giám đốc", "phê duyệt"), "processing_20_days": has("20", "ngày làm việc")}
    if case_id == "G05":
        return {"all_five_steps": has("đề xuất", "thẩm định", "nhà cung cấp", "hợp đồng", "nghiệm thu"),
                "safety_acceptance": has("ban an toàn", "kế toán")}
    if case_id == "G06":
        return {"training_period": has("tháng 9", "134", "16", "cao đẳng")}
    if case_id == "G07":
        return {"exam_rules": has("40", "45", "80", "30", "không đạt")}
    if case_id == "G08":
        return {"no_phone_in_source": has("không", "số điện thoại") and not bool(re.search(r"(?<!\d)0\d{9,10}(?!\d)", text))}
    if case_id == "G09":
        return {"rejects_false_amount": has("9.999.999", "không"), "correct_amount": has("1.250.000")}
    if case_id == "G10":
        return {"known_amount": has("1.250.000"), "unknown_phone": has("không", "số điện thoại")}
    raise ValueError(case_id)


answers = []
for group in groups:
    for result in group["results"]:
        if result["variant"] == "query":
            continue
        obj = result.get("response", {})
        if result["variant"] == "stream":
            obj = next((event.get("data", {}) for event in result.get("events", [])
                        if event.get("event") == "complete"), {})
        body = obj.get("answer", "")
        sources = obj.get("sources") or []
        source_ids = {str(source.get("index")) for source in sources}
        citations = re.findall(r"\[\s*([a-zA-Z0-9]{4})\s*\]", body)
        checks = facts(result["case_id"], body)
        answers.append({
            "case_id": result["case_id"], "variant": result["variant"],
            "role": result["role"], "repeat": result["repeat"],
            "run_id": group["run_id"], "status_code": result.get("status_code"),
            "has_complete_event": bool(obj) if result["variant"] == "stream" else None,
            "fact_checks": checks, "fact_correct_complete": all(checks.values()),
            "citation_ids": citations, "source_ids": sorted(source_ids),
            "unresolved_citations": [citation for citation in citations if citation not in source_ids],
            "source_document_ids": sorted({source.get("document_id") for source in sources
                                           if source.get("document_id") is not None}),
            "answer": body,
            "judgement_basis": "Reviewed actual answer against the extracted original PDF/DOCX and explicit case rubric; automated fact checks recorded above. Not business-owner approval.",
        })

primary = [row for row in answers if row["run_id"] == groups[0]["run_id"]
           and row["variant"] == "chat" and row["role"] == "Giám đốc" and row["repeat"] == 1]
metrics = {
    "unique_primary_questions": len(primary),
    "primary_fact_pass": sum(row["fact_correct_complete"] for row in primary),
    "answer_variants": len(answers),
    "fact_pass_variants": sum(row["fact_correct_complete"] for row in answers),
    "unresolved_citation_responses": sum(bool(row["unresolved_citations"]) for row in answers),
    "http_failures": sum(row["status_code"] != 200 for row in answers),
    "stream_complete": sum(row["has_complete_event"] is True for row in answers),
    "g04_answer_variants": sum(row["case_id"] == "G04" for row in answers),
    "g04_fact_pass": sum(row["case_id"] == "G04" and row["fact_correct_complete"] for row in answers),
    "formal_business_approval": False,
}
out = {"metrics": metrics, "answers": answers}
(HERE / "rag-graded-answers.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
print(json.dumps(metrics, ensure_ascii=False))
