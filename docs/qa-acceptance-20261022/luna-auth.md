# Authentication and navigation acceptance — Luna

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: https://chatbot.coremind.io.vn  
Role: disposable ordinary QA account (Kỹ thuật), authenticated through UI unless stated  
Viewports: desktop 1366×768; one separate isMobile emulation attempt at 390×844  
Method: MCP Playwright only. Auth setup used private bootstrap locally; credentials and tokens are omitted.

## Summary

5 PASS, 1 FAIL, 7 NOT_RUN, 0 BLOCKED. This is a limited partial pass, not full authentication/navigation acceptance. No business data was changed. No cleanup needed.

| ID | Preconditions / role / viewport | Numbered human steps | Expected | Actual | Status | Evidence | Bug / cleanup |
|---|---|---|---|---|---|---|---|
| AUTH-01 | Fresh browser context, 1366×768, unauthenticated | 1. Open /login. 2. Enter disposable QA account email/password in first login form. 3. Click exact “Đăng nhập”. | Successful login routes to dashboard and shows authenticated user. | Routed to /dashboard; dashboard metrics and account label “QA2” rendered. | PASS | [luna-auth-login-success.png](/home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-auth-login-success.png) | None |
| AUTH-02 | Fresh context, unauthenticated, 1366×768 | 1. Open /login. 2. Submit login form empty. | Required fields prevent submission and indicate missing input. | Email input retained native required validity; browser validation message “Please fill out this field.” appeared. | PASS | [luna-auth-login.png](/home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-auth-login.png) | No data created. |
| AUTH-03 | Fresh context, unauthenticated, 1366×768 | 1. Open /login. 2. Enter QA email and incorrect password. 3. Submit. | Clear human-readable invalid-credentials feedback; remain unauthenticated. | Login API returned 401 and the page stayed at /login, but the login form displayed no visible error text after the response. | FAIL | [luna-auth-invalid.png](/home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-auth-invalid.png) | **Major usability defect:** no visible explanation after rejected credentials. Repro steps above. No data created. |
| NAV-01 | Authenticated ordinary role, desktop 1366×768 | 1. Login via UI. 2. Click account avatar/name. | Account menu exposes profile and logout actions. | Menu rendered identity, department, “Thông tin cá nhân”, and “Đăng xuất”. | PASS | [luna-auth-dashboard.png](/home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-auth-dashboard.png) | None |
| AUTH-04 | Authenticated ordinary role, desktop 1366×768 | 1. Login. 2. Navigate directly to /admin/users. | Ordinary role is denied or redirected with meaningful state. | URL remained /admin/users while body was empty at the observation point; insufficient evidence to distinguish denial, delayed render, or broken route. | NOT_RUN | No screenshot | Needs rerun after route/role behavior clarified. |
| AUTH-05 | Authenticated ordinary role, desktop 1366×768 | 1. Login. 2. Navigate directly to /departments. | Ordinary role cannot access departments administration. | Redirected to /dashboard. | PASS | Dashboard screenshot above | No mutation. |
| AUTH-06 | Authenticated ordinary role, desktop 1366×768 | 1. Login. 2. Navigate directly to /approvals. | Ordinary role cannot access approvals administration. | Redirected to /dashboard. | PASS | Dashboard screenshot above | No mutation. |
| AUTH-07 | Authenticated ordinary role, desktop 1366×768 | 1. Login. 2. Navigate directly to /knowledge-graph. | Unauthorized route denied or redirected. | URL stayed /knowledge-graph with empty body at observation time; inconclusive. | NOT_RUN | No screenshot | Needs route confirmation and rerun. |
| AUTH-08 | Fresh unauthenticated context, 1366×768 | 1. On /login, press password “HIỆN”. 2. Inspect input type. 3. Press “ẨN”. | Password changes between text and password. | Locator became stale after rerender and the evidence capture failed; no PASS claim. | NOT_RUN | None | Rerun needed with stable selector. |
| AUTH-09 | Authenticated ordinary role | 1. Login. 2. Select logout. 3. Use browser Back and refresh. | Session cleared and protected page remains inaccessible. | Not completed; no reliable evidence of logout/back/session semantics. | NOT_RUN | None | No cleanup required. |
| NAV-02 | Authenticated ordinary role, keyboard | 1. Tab through dashboard controls. 2. Open account menu. 3. Press Escape and inspect focus. | Keyboard focus is visible; Escape closes overlays and restores focus. | Not run. | NOT_RUN | None | — |
| NAV-03 | Authenticated ordinary role; 360×640, 390×844, 844×390 and 390×844 isMobile emulation | 1. Login. 2. Open nav drawer/account menu. 3. inspect horizontal overflow and tap targets at each viewport. | Navigation is usable without clipping/overflow. | Attempted mobile login, but first login form was not visible under isMobile emulation; stopped without interacting with shared tabs. | NOT_RUN | None | Mobile layout remains unassessed. |
| AUTH-10 | Unauthenticated, register form | 1. Submit register form empty. 2. Try malformed email/mismatched confirmation. | Safe validation; no account created without valid inputs. | Not run. | NOT_RUN | None | No account created. |

## Notes

- /login presents login and registration forms in the same page; additional email/password inputs belong to the registration form and hidden auxiliary UI. Selectors must scope to the first login form.
- The disposable account and its existing QA-owned records were left intact because other acceptance work may use that account.
- Browser setup succeeded with the isolated MCP server. No shared default page was navigated, clicked, resized, or closed.

