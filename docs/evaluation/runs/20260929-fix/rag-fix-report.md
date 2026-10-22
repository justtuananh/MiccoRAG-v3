# Isolated RAG retest — 29 September 2026

The repaired code was tested against an isolated backend (`:18001`), PostgreSQL
clone (`micco_eval_fix_20260929`) and Chroma copy (`:18003`). The original
evaluation run was left unchanged. KB 9 and KB 11 copied with 387/387 and
388/388 chunks respectively; source uploads and relevant Docling/LightRAG
directories were copied into staging. No live database or vector collection was
mutated by this retest.

## Result

The staged pilot made 10 retrieval requests and 19 answer requests. Three
additional instrumented streams brought the answer sample to 22. All 10
primary questions and all 22 answers passed the recorded source-grounded fact
rubrics. G04 passed **6/6 answer variants**: three Director chats, one Admin
chat, and two Director streams. In each, the 500-million threshold requires
tender, Director approval and a maximum of 20 working days. Six of six streams
had a completion event. All 22 answers returned HTTP 200, and every detected
four-character citation ID mapped to a source in the same response. The final
streams show normalized citation brackets.

The extracted originals for documents 22, 26 and 27 were compared with answer
conditions and numbers: 1,250,000 VND; the 14-day exclusion; monthly review on
day 25; 500 million and 20 working days; 134 trainees for 16 hours; and exam
rules 40 questions, 45 minutes, 80 points, 30 days. The PDF for document 27
has one page and was cited as page 1. The DOCX-derived sources carry page 0,
which denotes no reliable page number. G08 and G10 correctly avoid inventing
a personal phone number. These checks are recorded in
`source-faithfulness.json`, `rag-graded-answers.json` and the raw response files.

The 30-criterion reassessment is in `rag-fix-results.json`: **11 PASS, 0 FAIL,
19 BLOCKED**. SRC-02 was repaired after the initial retest. Staged query,
nonstream chat and stream chat now display document 22's canonical
`original_filename` (`Quy trình mua sắm vật tư an toàn.docx`) despite the old
prefixed label stored in Chroma. All three responses retained document ID 22;
chat and stream citations resolved to their returned sources. Frontend source
labels read the new `source_file` field. The focused proof is in
`src02-proof.json`.

Service regressions cover empty authorized scope, vector results that ignore
filters, mixed or missing graph provenance, bounded adjacent-table recovery,
and citation IDs from the current response. The isolated TXT lifecycle reached
upload, index, query, answer and deletion; the deleted document returned 404
and subsequent query returned zero chunks. That fixture also checked private
read versus write roles. These tests support the scoped PASS statuses; they do
not establish production-wide behavior.

## Limits and next evidence

The pilot uses three source documents and selects one document per question.
It has repeated G01/G04 questions, no answer-bearing image, no OCR scan, no
approved contradictory or versioned document pair, and no multilingual or
accentless holdout. Prompt injection into retrieved content was not tested.
The six stream completions do not exercise reconnect or rollback. Cross-turn
source changes have a unit check for rejecting a prior citation ID but no
end-to-end history pilot. Q-05's effective-version and conflict rules remain
unapproved; no version or authority criteria were promoted to PASS.

The next concrete steps are to assemble approved OCR/image and conflicting
version fixtures, and run cross-turn, prompt-injection and reconnect cases.
Business owners still need to approve the source set and decision rules before
these sample results can serve as formal acceptance.
