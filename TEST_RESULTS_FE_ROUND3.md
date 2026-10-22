# TEST_RESULTS_FE_ROUND3.md — Review vòng 3 (sau đợt sửa R1 + route guard + N1/N2/N3)

> Review bằng đọc diff + chạy thật trên trình duyệt (ego-browser) tại
> **https://ctrl-seeking-bills-neural.trycloudflare.com** · Ngày: 2026-09-13
> Người review: agent Opus (không sửa code, không commit git).

---

## 1. Kết luận

> ### 🔴 CÒN BUG — chưa sạch
> - **1 regression mới** do chính đợt sửa này gây ra (mức **Cao**): 3 trang quản trị mất lớp chống rò rỉ dữ liệu qua bfcache.
> - **1 lỗi cũ chưa sửa xong** (mức Thấp): N1 — bản vá dò nhầm chuỗi, vẫn không bao giờ kích hoạt.

| Hạng mục | Số lượng |
|---|---|
| Kiểm tra đã chạy thật | 18 |
| Pass | 16 |
| Fail (regression mới) | 1 |
| Chưa đạt (lỗi cũ còn) | 1 |

---

## 2. Danh sách lỗi cho Dev

### 🔴 BUG A — REGRESSION: 3 trang quản trị mất lớp chống rò rỉ bfcache
- **Mức độ**: **Cao** (rò rỉ dữ liệu sau đăng xuất trên máy dùng chung)
- **Loại**: **Regression — do chính đợt sửa này tạo ra**
- **UC liên quan**: AUTH-13 (áp dụng cho `/admin`, `/departments`, `/approvals`, `/graph-knowledge`)

**Nguyên nhân gốc**: Bản vá bfcache ở vòng trước đặt listener `pageshow` **bên trong `ProtectedRoute`**. Đợt sửa này tách 3 route quản trị ra khỏi `ProtectedRoute`, đưa vào `PrivilegedRoute` — một **route anh em**, không lồng nhau:

```jsx
<Route element={<ProtectedRoute />}>      {/* ✅ có listener pageshow */}
  ... /dashboard, /documents, /chat, /workspaces ...
</Route>

<Route element={<PrivilegedRoute />}>     {/* ❌ KHÔNG có listener */}
  ... /admin, /departments, /approvals ...
</Route>

<Route element={<AdminRoute />}>          {/* ❌ KHÔNG có listener (vốn đã thiếu từ trước) */}
  ... /graph-knowledge ...
</Route>
```

**Bước tái hiện**:
1. Đăng nhập `admin@micco.vn`.
2. Vào `/admin` (tải trang đầy đủ), thấy bảng danh sách người dùng.
3. Avatar → **Đăng xuất** → về `/login`, `localStorage.docvault_token` đã bị xoá (đã kiểm chứng `token: false`).
4. Bấm nút **Back** của trình duyệt.

**Kết quả hiện tại** (quan sát thật):
```
back -> /admin | token: false | 5 dòng người dùng hiển thị
sample: "QK  QA Kiểm Thử R2  qa.round2@micco.vn"
sidebar quyền quản trị (Phê duyệt / Quản trị / Đồ thị tri thức) vẫn hiển thị đầy đủ
```
`/approvals`, `/departments`, `/graph-knowledge` cũng hiển thị nguyên trạng với sidebar quản trị, không bị đẩy về `/login`.

**Đối chứng chứng minh đúng nguyên nhân**: cùng kịch bản nhưng trên `/dashboard` (vẫn nằm trong `ProtectedRoute`) → `{"url":"/login","token":false,"leaked":false}` — chặn đúng, không rò. Chênh lệch này chứng minh lỗi đến từ việc tách route, không phải nguyên nhân khác.

**Kết quả mong đợi**: mọi trang yêu cầu đăng nhập (kể cả trang quản trị) phải kiểm tra lại token khi khôi phục từ bfcache và đẩy về `/login`.

**File nghi ngờ**: `micco-frontend/src/App.jsx` — `useEffect` lắng nghe `pageshow` hiện chỉ nằm trong `ProtectedRoute` (dòng ~38-48).

**Hướng sửa đề xuất**: tách logic `pageshow` thành một hook dùng chung (vd `useBfcacheAuthGuard()`) rồi gọi trong cả `ProtectedRoute`, `PrivilegedRoute`, `AdminRoute`; hoặc lồng `PrivilegedRoute`/`AdminRoute` **bên trong** `ProtectedRoute`; hoặc đặt listener ở `DashboardLayout` (component bọc mọi trang đã đăng nhập).

---

### 🟡 BUG B — N1 vẫn chưa kích hoạt: bản vá dò nhầm chuỗi từ chối
- **Mức độ**: Thấp (chỉ ảnh hưởng kiểu hiển thị; câu trả lời vẫn đúng và vẫn hiện)
- **Loại**: Lỗi cũ **chưa sửa xong** (không phải regression)
- **UC liên quan**: CHAT-10

**Nguyên nhân gốc**: Backend có **hai chuỗi từ chối khác nhau**, bản vá chỉ dò theo chuỗi không được dùng:

| Chuỗi | Vị trí | Có được dùng trong luồng chat không |
|---|---|---|
| "Dựa trên các tài liệu hiện có... **không tìm thấy thông tin** cụ thể... **kiểm tra lại từ khóa**... **cung cấp thêm hồ sơ**..." | `chat_prompt.py:190` (1 chỗ) | ❌ Không phải chuỗi model thực sự dùng |
| **"Tài liệu không chứa thông tin này."** | `chat_agent.py:506, 628, 769` · `rag.py:1169, 1427` (5 chỗ) | ✅ Đây mới là chỉ dẫn được nhồi vào lượt tool-result — model tuân theo chuỗi này |

`isFallbackMessage()` (`ChatAssistant.jsx:382-393`) dò 4 cụm, **cả 4 đều trích từ chuỗi không dùng**.

**Bước tái hiện**: chat trong workspace có tài liệu → hỏi `"Giá vàng SJC hôm nay là bao nhiêu?"`

**Kết quả hiện tại**: model trả `"Tài liệu không chứa thông tin về giá vàng SJC hôm nay."` → khớp **0/4** cụm → `isFallbackMessage()` trả `false` → kiểu hiển thị đặc biệt vẫn không kích hoạt (đúng y như trước khi sửa).

**Kết quả mong đợi**: nhận diện được câu từ chối và hiển thị đúng kiểu riêng.

**Hướng sửa đề xuất**: thêm `'tài liệu không chứa thông tin'` làm **cụm độc lập** (đủ đặc trưng, không cần khớp 2 cụm); đồng thời nên thống nhất 2 chuỗi từ chối ở backend để tránh tái diễn.

---

### ⚪ Giới hạn còn lại của R1 (ghi nhận, KHÔNG phải bug)
Nếu model trả về **đúng** dạng `{"name":"<tên tool đã đăng ký>","arguments":{...không rỗng...}}` làm câu trả lời cuối, nó vẫn sẽ bị coi là lệnh gọi tool. Đây là giới hạn cố hữu của mọi heuristic dò tool-call trên text, và là kịch bản rất gượng ép. Các chốt chặn mới **đã loại bỏ rủi ro thực tế** (đã kiểm chứng: câu trả lời JSON bình thường đến được người dùng).

### ⚪ Ghi chú nhỏ
Khối `PrivilegedRoute` dùng một instance `<DashboardLayout>` riêng → chuyển giữa `/dashboard` và `/admin` sẽ remount layout (polling đếm phê duyệt khởi động lại). Không ảnh hưởng chức năng.

---

## 3. Chi tiết các kiểm tra đã chạy

### Chặn route theo vai trò (trọng tâm đợt sửa)

| Vai trò | `/admin` | `/departments` | `/approvals` | `/graph-knowledge` | Kết quả |
|---|---|---|---|---|---|
| Nhân viên (`user1`) | → `/dashboard` | → `/dashboard` | → `/dashboard` | → `/dashboard` | ✅ Pass |
| Admin | vào được | vào được | vào được | vào được | ✅ Pass |
| Trưởng phòng (`user2` tạm nâng quyền) | vào được | vào được | vào được | → `/dashboard` | ✅ Pass — không chặn nhầm |

`user2` đã được **trả về vai trò "Nhân viên"** sau khi test (xác nhận `status 200`).

### Các kiểm tra khác

| # | Nội dung | Kết quả | Bằng chứng |
|---|---|---|---|
| 1 | CHAT-01 — doanh thu quý III | ✅ Pass | "Doanh thu quý III năm 2026 đạt **152,3 tỷ đồng**, tăng 18,7%..." kèm trích dẫn `[ep3g]`, "Tìm thấy 3 nguồn" |
| 2 | N2 — nhớ workspace sau F5 | ✅ Pass | Đổi sang "WS Kiểm thử Cá nhân" → `micco_last_workspace_id="1"`; sau F5 vẫn đúng workspace, lịch sử còn nguyên |
| 3 | WS-03 — Nhân viên tạo workspace Công khai | ✅ Pass | Radio giờ chọn được + cảnh báo; submit → toast **"Chỉ Admin mới được tạo workspace công khai"** (hiện ~0,8s rồi tự tắt); workspace **không** bị âm thầm tạo thành Cá nhân |
| 4 | N3 — API `/api/approvals/pending` | ✅ Pass | `user1` → `403 {"detail":"Permission denied"}`; trên UI `user1` bị chặn ngay ở router (không còn thấy trang rỗng) |
| 5 | R1 — phản ví dụ câu trả lời JSON | ✅ Pass | Câu trả lời JSON `{"result":[...]}` **đến được người dùng**, không bị nuốt |
| 6 | AUTH-01 — đăng nhập admin | ✅ Pass | Vào `/dashboard`, `/api/auth/me` trả role `Admin` |
| 7 | AUTH-03 — sai mật khẩu | ✅ Pass | Hiện **"Đăng nhập thất bại"** (tiếng Việt), không còn "Invalid email or password" |
| 8 | Đăng ký trùng email (regression fix #7) | ✅ Pass | API trả **"Email đã được sử dụng..."**; `handleRegister` giữ nguyên `result.error` → thông báo tiếng Việt chi tiết không bị phá |
| 9 | AUTH-13 trên `/dashboard` | ✅ Pass | Sau đăng xuất + Back → `/login`, `leaked: false` |
| 10 | **AUTH-13 trên `/admin`** | ❌ **Fail** | Xem BUG A |
| 11 | CHAT-10 — câu hỏi ngoài phạm vi | ⚠️ Một phần | Nội dung trả lời đúng (từ chối, không bịa) nhưng kiểu hiển thị fallback không kích hoạt — xem BUG B |
| 12 | Hạ tầng | ✅ Pass | backend/Vite/cloudflared sống; `/`, `/api/auth/departments`, `/docs` đều 200; nginx `:8888` = 200 sau khi sửa compose |

---

## 4. Đánh giá chất lượng đợt sửa

**Điểm tốt**: cả 2 bản vá backend đều chắc tay — `_parse_fallback_tool_call` giờ có 3 lớp chốt đúng hướng (bắt buộc có `tools`, tên tool phải đã đăng ký, `arguments` phải là dict không rỗng) và đọc phòng thủ qua `_get()` cho cả dict lẫn object; sửa `approvals.py` tái sử dụng đúng `ALL_APPROVER_ROLES` sẵn có. Phía frontend, `PrivilegedRoute` xử lý `loading` đúng thứ tự (không đá nhầm khi chưa nạp xong user) và dùng lại đúng helper `isPrivilegedRole` nên điều kiện hiện menu và điều kiện vào route luôn khớp — đã kiểm chứng cả 3 vai trò, không chặn nhầm Trưởng phòng.

**Điểm trừ**: việc tái cấu trúc route đã vô tình vô hiệu hoá bản vá bfcache của vòng trước trên đúng nhóm trang nhạy cảm nhất — đây là kiểu regression điển hình khi một bản vá bảo vệ được gắn vào một nhánh cây route cụ thể thay vì một lớp dùng chung. BUG B cho thấy bản vá được viết dựa trên tài liệu đặc tả thay vì kiểm chứng chuỗi mà hệ thống thực sự phát ra.

**Cần làm tiếp**: sửa BUG A (ưu tiên) và BUG B, rồi review lại vòng nữa.
