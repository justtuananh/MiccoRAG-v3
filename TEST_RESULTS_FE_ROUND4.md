# TEST_RESULTS_FE_ROUND4.md — Kiểm chứng vòng 2 (sau khi sửa BUG A & BUG B)

> Thực thi thật bằng trình duyệt (ego-browser) trên **https://ctrl-seeking-bills-neural.trycloudflare.com**
> Ngày chạy: 2026-09-13 · Tài khoản: `admin@micco.vn`, `user1@micco.vn`, `user2@micco.vn`
> Vòng review thứ 2 trong vòng lặp `sửa → review`. Mọi dòng Pass đều có quan sát thật kèm theo, không suy đoán.

---

## 1. KẾT LUẬN: ✅ SẠCH — KHÔNG PHÁT HIỆN BUG

| Hạng mục | Số kiểm tra | Pass | Fail |
|---|---|---|---|
| BUG A (bfcache) | 5 | 5 | 0 |
| Regression phân quyền | 10 | 10 | 0 |
| BUG B (nhận diện câu từ chối) | 1 | 1 | 0 |
| Regression chức năng lõi | 7 | 7 | 0 |
| **Tổng** | **23** | **23** | **0** |

Cả 2 bug của vòng review trước đã đóng. **Không phát sinh regression mới.**

---

## 2. BUG A — Rò rỉ dữ liệu qua bfcache: ✅ ĐÃ ĐÓNG

Kịch bản mỗi trang: đăng nhập admin → mở trang → **Đăng xuất** (xác nhận token đã mất, đang ở `/login`) → bấm **Back**.

| Trang | Sau đăng xuất | Sau khi bấm Back | Rò dữ liệu? |
|---|---|---|---|
| `/admin` | `/login`, token=false | `/login`, token=false, **0 dòng bảng** | ❌ không |
| `/departments` | `/login`, token=false | `/login`, token=false | ❌ không |
| `/approvals` | `/login`, token=false | `/login`, token=false | ❌ không |
| `/graph-knowledge` | `/login`, token=false | `/login`, token=false | ❌ không |
| `/dashboard` *(đối chứng lớp cũ)* | `/login`, token=false | `/login`, token=false | ❌ không |

Đối chiếu vòng trước: `/admin` từng rò **5 dòng người dùng thật** (`"QK QA Kiểm Thử R2 qa.round2@micco.vn"`) kèm sidebar quản trị. Nay nội dung sau Back là trang đăng nhập: `"Đăng nhập Chào mừng trở lại! Nhập thông tin để tiếp tục..."`.

**Nguyên nhân đã xử lý đúng**: `PrivilegedRoute` và `AdminRoute` được lồng **bên trong** `ProtectedRoute` (`src/App.jsx`), nên listener `pageshow` phủ mọi trang cần đăng nhập thay vì chỉ nhóm route cũ.

---

## 3. Regression phân quyền: ✅ KHÔNG VỠ

Đây là phần rủi ro nhất vì đợt sửa đã tái cấu trúc cây route.

| Vai trò | `/admin` | `/departments` | `/approvals` | `/graph-knowledge` |
|---|---|---|---|---|
| **Nhân viên** (`user1`) | → `/dashboard` | → `/dashboard` | → `/dashboard` | → `/dashboard` |
| **Trưởng phòng** (`user2` tạm đổi vai trò) | ✅ vào được | ✅ vào được | ✅ vào được | → `/dashboard` (đúng, chỉ Admin) |
| **Admin** | ✅ vào được | ✅ vào được | ✅ vào được | ✅ vào được |

- **Không chặn nhầm lúc đang tải**: F5 trên `/admin` khi đã đăng nhập admin → đường dẫn quan sát liên tục 14 lần chỉ ra `["/admin"]`, không hề nháy sang `/dashboard` (3 guard đều trả `LoadingSpinner` khi `loading=true`).
- `user2` **đã được trả về vai trò Nhân viên** sau khi test xong (xác nhận trên bảng: `TT Trần Thị B user2@micco.vn Nhân viên Nhân sự`).

---

## 4. BUG B — Nhận diện câu từ chối: ✅ ĐÃ ĐÓNG

`isFallbackMessage()` dùng để **ẩn khối nguồn trích dẫn** khi model trả lời không tìm thấy thông tin (tránh gắn nguồn cho câu từ chối gây hiểu lầm).

| Câu hỏi | Câu trả lời | Khối nguồn |
|---|---|---|
| "Doanh thu quý III năm 2026 là bao nhiêu?" | "…đạt **152,3 tỷ đồng**, tăng 18,7%… Hòa Phát Xanh 24,5 tỷ đồng`[67pd]`" | ✅ **có** — "Tìm thấy 3 nguồn" |
| "Giá vàng SJC hôm nay bao nhiêu?" | "**Tài liệu không chứa thông tin** về giá vàng SJC hôm nay." | ✅ **không có** (đúng) |

Toàn hội thoại chỉ đếm được **1** khối `"Tìm thấy N nguồn"` — thuộc câu trả lời thật. Trước khi sửa, bản vá dò nhầm chuỗi của `chat_prompt.py` (không được dùng) nên khớp 0/4 cụm và nhánh này không bao giờ kích hoạt.
Ảnh: `shots/BUGB_chat_tuongphan_nguon.png`

---

## 5. Regression chức năng lõi: ✅ KHÔNG VỠ

| UC | Kết quả | Bằng chứng |
|---|---|---|
| CHAT-01 | ✅ Pass | "152,3 tỷ đồng" + trích dẫn `[67pd]` + "Tìm thấy 3 nguồn" |
| AUTH-01 / AUTH-13 | ✅ Pass | Đăng nhập vào `/dashboard`; đăng xuất xoá token, Back không quay lại được (mục 2) |
| AUTH-03 | ✅ Pass | Sai mật khẩu → **"Đăng nhập thất bại"** (tiếng Việt), không còn chuỗi tiếng Anh |
| Luồng **đăng ký** | ✅ Pass | Email trùng → **"Email đã được sử dụng. Vui lòng đăng nhập hoặc dùng email khác."** — thông báo tiếng Việt chi tiết của backend còn nguyên, không bị bản vá AUTH-03 nuốt mất |
| WS-03 | ✅ Pass | Nhân viên chọn "🌐 Công khai" (radio **không còn bị khoá**, kèm cảnh báo) → submit → toast **"Chỉ Admin mới được tạo workspace công khai"**, không tạo nhầm workspace |
| ADM-03 | ✅ Pass | Đổi vai trò `user2` → bảng hiển thị "Trưởng phòng" **ngay lập tức**, không cần F5 |
| N2 | ✅ Pass | `micco_last_workspace_id="1"`; F5 → vẫn "WS Kiểm thử Cá nhân", lịch sử chat còn đủ |
| N3 | ✅ Pass | `user1` vào `/approvals` bị chặn ngay ở tầng router (không còn thấy trang rỗng) |

---

## 6. Ghi nhận thêm (không phải bug, ngoài phạm vi)

- Ô tick "Tôi đồng ý với Điều khoản" ở form đăng ký là `div` tuỳ biến, **không phải `<input type=checkbox>`**, không có `role="checkbox"`, và phần tử con chặn pointer event. Không ảnh hưởng người dùng thật (bấm bằng chuột vẫn được) nhưng gây khó cho kiểm thử tự động và **không thân thiện với trình đọc màn hình**. Có sẵn từ trước, không do đợt sửa này.
- Backend vẫn tồn tại **2 chuỗi từ chối khác nhau** (`chat_prompt.py` vs `chat_agent.py`/`rag.py`). Frontend hiện đã bắt được cả hai, nhưng nên thống nhất ở backend để tránh phải vá vòng ở frontend lần sau.
- Còn tồn dư dữ liệu test từ các vòng trước: workspace `"WS Public bởi nhân viên"` (loại Cá nhân — hệ quả của bug #3 cũ đã sửa), `"WS Công khai Kiểm thử"`, và người dùng `qa.round2@micco.vn`. Nên dọn nếu muốn môi trường sạch.

---

## 7. Phạm vi chưa kiểm ở vòng này

Vòng này tập trung xác minh 2 bug vừa sửa + regression liên quan. **Không** chạy lại toàn bộ 94 UC của `TEST_PLAN_FE.md`; các nhóm `DOC`, `UX`, phần lớn `NAV`/`WS`/`ADM`/`PROC` giữ nguyên kết quả từ `TEST_RESULTS_FE_ROUND2.md`.
