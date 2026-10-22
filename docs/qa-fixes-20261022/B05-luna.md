# B05 — Luna desktop QA

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: `https://chatbot.coremind.io.vn`, desktop 1366×768.  
Runner: isolated MCP Playwright; QA32 authenticated through private bootstrap. Public postfix bundle verified as `index-D_MP0DTz.js` (`miccorag-frontend:20261022-desktop-b05`).

## Result

**PASS — client-side oversize validation and boundary behavior verified.** No upload was submitted, no business records changed, and no later bug IDs were tested.

## Steps and observations

1. Before rollout, on public `index-BtbYHPBg.js`, selected and dropped a local 51 MiB TXT with effective date `2026-10-22`. Both paths showed `51.0 MB • TXT`, no validation alert, and enabled Upload. This reproduced the B05 red baseline. Upload was not clicked.
2. After the parent confirmed the public B05 rollout, opened a fresh cache-busted session and verified the loaded asset `index-D_MP0DTz.js` and QA32 header (`QA2`). Picker selection of `QA-FIX-20261022-B05-51MiB.txt` (53,477,376 bytes) displayed a filename-specific alert stating the 50 MiB (52,428,800 byte) limit; Upload was disabled.
3. Dropped the same 51 MiB file through the upload drop zone. The same limit and filename alert appeared, and Upload stayed disabled.
4. Selected the valid 186 B TXT together with the 51 MiB fixture. The oversize alert remained and Upload was disabled. Removing the oversize file cleared the alert, kept the valid file and date selected, and re-enabled Upload.
5. Selected an exact 50 MiB TXT (52,428,800 bytes): no alert and Upload enabled. Selected a 50 MiB + 1 byte TXT (52,428,801 bytes): filename and byte limit appeared in the alert and Upload was disabled.
6. Quick B04 regression: the 0 B TXT still produced the empty-file filename alert and disabled Upload.

All states used valid effective date `2026-10-22`. The modal was canceled after checks. Network inspection showed only GET requests; no upload POST was issued. Console error query returned zero errors, and page-error capture was empty.

## Evidence

- Red baseline: `harness/reports/fixes-20261022/B05-baseline-picker-51MiB.png`, `B05-baseline-drop-51MiB.png`.
- Postfix: `B05-postfix-picker-51MiB-rejected.png`, `B05-postfix-drop-51MiB-rejected.png`, `B05-postfix-mixed-oversize-blocked.png`, `B05-postfix-valid-after-oversize-removed.png`, `B05-postfix-exact-50MiB-eligible.png`, `B05-postfix-50MiB-plus1-rejected.png`, `B05-postfix-B04-empty-regression.png` (all under `harness/reports/fixes-20261022/`).

The three local B05 large fixtures were deleted after testing; the existing small QA fixtures were left untouched.
