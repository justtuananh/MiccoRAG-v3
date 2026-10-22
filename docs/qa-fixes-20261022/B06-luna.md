# B06 — Luna desktop QA

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: `https://chatbot.coremind.io.vn`, desktop 1366×768.  
Runner: isolated MCP Playwright contexts. QA32 owner and manager16 (TĐA, Kỹ thuật) sessions were initialized from the private bootstrap; credentials were not printed or stored.

## Fixture and red baseline

**Fixture ready for Sol:** document ID `DOC-0078` (UI route `/documents/78`), filename `QA-FIX-20261022-B06-rejection.txt`. Created exactly once through the QA32 upload UI as a 133 B synthetic TXT with `Nội bộ`, department Kỹ thuật, effective 2026-10-22 through 2026-10-29. Content explicitly marks it QA-only and references B06-20261022. No preexisting or trashed document was opened for mutation.

Manager16/TĐA opened the approvals UI, previewed this only pending document, then rejected it with the specified reason: `QA B06: Thiếu nội dung hướng dẫn cần bổ sung.` The UI returned success from the UI-triggered rejection action for document 78; the manager queue then showed no items awaiting approval. No approval action was clicked.

After reloading the owner detail, the status displayed `Từ chối`, but the specified reason was not visible in the detail or activity text. This reproduces B06’s red baseline. The synthetic fixture remains active and rejected for postfix verification; do not clean it up until parent approval.

## Evidence

- `harness/reports/fixes-20261022/B06-owner-upload-ready.png` — file, dates, and Internal visibility prepared before the single UI upload.
- `harness/reports/fixes-20261022/B06-manager-pending-preview.png` — manager queue with the QA fixture pending review.
- `harness/reports/fixes-20261022/B06-manager-rejection-reason-ready.png` — requested reason entered in the manager rejection flow before submission.
- `harness/reports/fixes-20261022/B06-manager-rejected-queue.png` — manager queue after rejection; no pending documents.
- `harness/reports/fixes-20261022/B06-owner-rejected-after-reload-baseline.png` — owner reload shows `Từ chối`, without the rejection reason.

## Postfix status

**PASS — verified after parent-confirmed public rollout.** A new owner context loaded the public bundle `index-Cezh4tO7.js` and opened `/documents/78`. After the first reload, owner detail displayed the exact reason `QA B06: Thiếu nội dung hướng dẫn cần bổ sung.`; after a second reload, the same reason remained visible exactly once. Status remained `Từ chối`. The activity log said `Hệ thống đã từ chối tài liệu này`; no pending-approval activity was present.

For the normal-document guard, the owner opened existing approved document `DOC-0020` (`Quy trình an toàn trong sản xuất vật liệu nổ công nghiệp.pdf`) read-only. It showed `Đã phê duyệt`, had no `Lý do từ chối` panel, and did not contain the synthetic B06 reason. The test run captured zero page errors and zero console errors across owner reloads and the read-only normal-document navigation. No approval or additional upload was performed.

Postfix screenshot evidence: `harness/reports/fixes-20261022/B06-owner-rejected-after-reload-postfix.png` and `B06-owner-normal-approved-no-reason.png`. The manager16 review/reject screenshots and owner red-baseline screenshot above preserve the setup and before/after state. DOC-0078 remains active and rejected; cleanup is pending parent approval and was not attempted.
