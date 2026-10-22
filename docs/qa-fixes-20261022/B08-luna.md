# B08 — Luna desktop QA

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: public login page, desktop 1366×768.  
Runner: isolated MCP Playwright guest context; no credentials entered.

## Result: PASS — login Google control

Red baseline used public asset `index-D8tIQKNf.js`: clicking **Đăng nhập với Google** left the URL and visible page unchanged and produced no feedback. Postfix used a fresh guest context and loaded the confirmed B08 asset `index-CWoOnrmM.js`.

On the live build, clicking the login Google button displayed the accessible status: “Đăng nhập bằng Google chưa được cấu hình. Vui lòng sử dụng email và mật khẩu để đăng nhập.” Focusing the button and pressing Enter displayed the same message. The URL stayed unchanged. No Google popup, external request, or app auth request followed either action; `docvault_token` remained absent, cookies stayed empty, and no page or console errors were captured. The visible email and password fields accepted temporary noncredential QA sentinels, then were cleared without submitting. No authentication was attempted.

The live desktop DOM also exposes one visible **Đăng ký với Google** button, contrary to the supplied expectation that registration has no such control. I did not activate it; this B08 check was limited to login. Registration behavior remains unverified.

Evidence: red baseline screenshots `harness/reports/fixes-20261022/B08-baseline-login-before.png` and `B08-baseline-login-after-google.png`; postfix screenshots `harness/reports/fixes-20261022/B08-postfix-login-before.png` and `B08-postfix-login-status.png`.
