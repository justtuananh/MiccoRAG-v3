# B08 — Google login feedback

2026-10-22 ICT. **READY, frontend-only; chờ Luna public PASS.**

Đã kiểm tra backend đang dùng: compat auth chỉ có departments/register/login/me/avatar;
không tìm thấy OAuth Google route, callback, config hay OAuth library. Các Google
imports hiện tại là Gemini. Route frontend `/login` dùng `AuthPage`, không dùng
legacy `Login.jsx`. Nút Google trong SignInForm chưa có handler nên không phản hồi.

Theo tiêu chí audit, candidate báo rõ:
“Đăng nhập bằng Google chưa được cấu hình. Vui lòng sử dụng email và mật khẩu để đăng nhập.”
Thông báo `role="status"`, ID riêng bằng `useId`, button liên kết `aria-describedby`.
Giữ native `type="button"`, focus được, không submit form, không gọi auth/network hay
điều hướng. Email/password đã nhập được giữ nguyên; login lỗi và retry thành công
tiếp tục hoạt động. Không tạo OAuth integration, yêu cầu credentials hay gửi thông tin
ra ngoài. B09 chưa sửa.

Files thay đổi:

- `micco-frontend/src/pages/AuthPage.jsx`: state/feedback riêng cho Google sign-in.
- `micco-frontend/tests/auth-google-unavailable.test.mjs` (mới): render AuthPage thật,
  activation/status, focus/association/repeated activation, no fake authentication,
  giữ inputs và normal login failure/success recovery.
- Report này. Snapshot trước sửa `/tmp/B08-AuthPage-before.jsx`; giữ nguyên edits cũ.

Verification: RED **2 FAIL / 1 PASS**, GREEN focused **3 PASS**; unit **43 PASS**.
Node22 fe harness **2 PASS / 0 FAIL / 1 WARN**, eslint/build đạt. WARN là bỏ qua E2E.
JSDOM kiểm tra native focus/click; Enter/Space thật dành cho Luna, không tuyên bố
đã kiểm browser keyboard. Không deploy/restart/spawn agent.

```bash
# micco-frontend/
export PATH=/home/micco/node22/bin:$PATH
node --test tests/auth-google-unavailable.test.mjs
npm run test:unit
# repo root
RUN_E2E=0 bash harness/run.sh fe --json --md
```

Logs: `harness/reports/qa-fixes-20261022-b08/{red,focused,unit,harness}.log`;
harness `20261022-141956.{json,md}`.

Parent rollout frontend static + container. Luna desktop: click và Tab/Enter/Space
Google, đọc status, không redirect/fake success; normal email/password vẫn dùng được.
Sol chờ parent đóng B08 trước B09.
