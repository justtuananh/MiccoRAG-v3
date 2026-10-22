# B04 — Luna desktop QA

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: `https://chatbot.coremind.io.vn` public live baseline; desktop 1366×768, 100% zoom.  
Runner: isolated MCP Playwright tab. Auth initialized with private bootstrap `qaToken` for QA32 (UI header `QA2`). No app source, deployment, or business records changed.

## Status

**PASS — B04 public desktop postfix verified against `index-BtbYHPBg.js`.**

The pre-fix public baseline reproduced acceptance of a zero-byte TXT. On the live postfix bundle, picker, drop, and mixed selection all reject the empty file with a filename-specific alert and disabled Upload. Removing the empty file restores valid TXT eligibility. Upload was never clicked and no record was created.

## Baseline observations (approx. 13:45 ICT)

- Fixture: `.playwright-mcp/QA-20261022-DOCS-empty.txt` (0 B) and `.playwright-mcp/QA-20261022-DOCS-acceptance.txt` (186 B synthetic TXT).
- Picker: selecting the 0 B file showed `0 B • TXT`. With effective date `2026-10-22`, Upload was enabled and no alert was present. **B04 FAIL reproduced.**
- Drag-drop: dropping the same 0 B file onto the upload drop zone also showed `0 B • TXT`; with the valid date, Upload was enabled. **B04 FAIL reproduced through drop mode.**
- Mixed selection through picker: the zero-byte file and valid 186 B TXT appeared together. Because the zero-byte file had first been dropped, the picker appended its selection and the UI showed two empty-file entries plus the valid TXT. There was no validation alert and Upload remained enabled. The test did not submit.
- Removal recovery: removing both zero-byte entries left the valid TXT visible as `186 B • TXT`, retained the valid date, and kept Upload enabled. The valid synthetic file therefore remains selectable/eligible without uploading it.
- No upload request was issued. The Upload control was not activated; observed document requests in the session were GETs only. The modal was canceled through its Hủy button.
- Console error query: zero console errors. Page-error listener captured no errors during form interactions.

## Evidence

- `harness/reports/fixes-20261022/B04-baseline-picker-empty-valid-date.png` — empty file via picker, valid date, Upload enabled.
- `harness/reports/fixes-20261022/B04-baseline-drop-empty-valid-date.png` — empty file via drop, valid date, Upload enabled.
- `harness/reports/fixes-20261022/B04-baseline-picker-mixed.png` — empty and valid TXT files selected together; Upload enabled.
- `harness/reports/fixes-20261022/B04-baseline-picker-valid-after-empty-removal.png` — empty entries removed; valid TXT remains eligible.

## Live postfix observations (2026-10-22, approx. 13:41 ICT)

- Fresh public navigation with a cache-busting query loaded `index-BtbYHPBg.js` in the isolated MCP Playwright desktop tab. QA32 authenticated through the private bootstrap; viewport was 1366×768.
- Picker: selected the 0 B fixture and set effective date `2026-10-22`. The dialog displayed: `Tệp rỗng (0 B): QA-20261022-DOCS-empty.txt. Hãy xóa tệp rỗng và chọn tệp có nội dung trước khi tải lên.` Upload was disabled. The filename was named in the alert and the footer remained visible within the viewport.
- Drop: dropped the same 0 B fixture. It produced the filename-specific empty-file alert and disabled Upload.
- Mixed picker state: selected the 0 B fixture together with the 186 B valid TXT. The alert continued to identify the empty fixture and Upload remained disabled; both files stayed visible. Footer was visible at y=671 in the 768 px viewport.
- Recovery: removing the empty fixture cleared the alert; the valid TXT remained selected, effective date stayed `2026-10-22`, and Upload became enabled. Removing and reselecting `QA-20261022-DOCS-acceptance.txt` again left it eligible with no alert and the date retained.
- Upload was never activated. The request list showed only GET document-list requests; no empty-file or other upload request was issued. The modal was canceled after checks. Console query returned 0 errors; no page errors were captured.
- No business records were changed. No additional bug IDs were tested.

## Postfix evidence

- `harness/reports/fixes-20261022/B04-postfix-picker-empty-rejected.png` — picker rejection, filename alert, disabled Upload.
- `harness/reports/fixes-20261022/B04-postfix-drop-empty-rejected.png` — drop rejection.
- `harness/reports/fixes-20261022/B04-postfix-mixed-blocked.png` — valid + empty selected, error remains and Upload disabled.
- `harness/reports/fixes-20261022/B04-postfix-valid-after-empty-removed.png` — valid TXT remains eligible after removing the empty file.
- `harness/reports/fixes-20261022/B04-postfix-valid-reselected-eligible.png` — valid TXT removal/reselection recovery.
