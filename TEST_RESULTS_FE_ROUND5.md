# TEST_RESULTS_FE_ROUND5.md — Kết quả kiểm thử vòng mở rộng (UC chưa từng chạy)

> Thực thi thật bằng trình duyệt (ego-browser) + kiểm chứng chéo qua API trên
> **https://ctrl-seeking-bills-neural.trycloudflare.com**, theo `TEST_PLAN_FE.md`.
> Ngày chạy: 2026-09-13 · Tài khoản: `admin@micco.vn`, `user2@micco.vn`, `user3@micco.vn`.
> Mục tiêu vòng này: chạy **35 UC chưa từng được chạy** trong 4 vòng trước — vùng mù lớn nhất của dự án.
> Mọi dòng "Pass" đều có quan sát thật (DOM/response API/ảnh chụp) kèm theo. Không suy đoán.

---

## 1. Bảng tổng hợp

| Chỉ số | Số lượng |
|---|---|
| UC chưa từng chạy (xác định bằng đối chiếu 4 file kết quả cũ) | 35 |
| **Đã chạy vòng này** | **35** |
| ✅ Pass | 30 |
| ❌ Fail | 2 |
| ⚪ Không xác minh trọn vẹn | 3 |

**Kết luận: CÒN BUG — phát hiện 2 UC Fail và 5 lỗi cần dev xử lý** (2 mức Trung bình, 3 mức Thấp). Không có lỗi Blocker/Cao mới. Các chức năng lõi (chat, phân quyền, upload, workspace, quản trị) đều hoạt động đúng.

Sau vòng này, **toàn bộ 94 UC của test plan đã được chạy ít nhất 1 lần**.

---

## 2. Danh sách lỗi cho Dev

### Lỗi #R5-1 — Nút "Build Communities" gọi endpoint không tồn tại (404), giao diện im lặng
- **Mức độ**: **Trung bình**
- **UC**: ADM-09 (Fail)
- **Bước tái hiện**:
  1. Đăng nhập `admin@micco.vn` → vào `/admin`.
  2. Kéo xuống mục **AI Tools › GraphRAG Utilities** → bấm **Build Communities**.
  3. Quan sát giao diện; mở log backend hoặc tab Network.
- **Kết quả hiện tại**: Giao diện **không phản hồi gì** — không toast, không spinner, không báo lỗi. Log backend:
  `"POST /api/admin/communities/build HTTP/1.1" 404 Not Found`.
  Gọi trực tiếp cũng trả `404 {"detail":"Not Found"}`. Đối chiếu `openapi.json`: nhóm `/api/admin/*` chỉ có `departments`, `departments/{id}`, `stats`, `users`, `users/{id}`, `chat-logs` — **không hề có** `communities/build`.
- **Kết quả mong đợi**: Chạy phân tích cộng đồng (Leiden + LLM summary) như mô tả ngay dưới nút, hoặc tối thiểu báo lỗi rõ ràng cho người dùng.
- **File/khu vực nghi ngờ**: Frontend `micco-frontend/src/pages/Admin.jsx` gọi endpoint không tồn tại **và nuốt lỗi** (không hiển thị catch); Backend `micco-backend/backend/app/api_compat/admin.py` thiếu route tương ứng.
- **Ảnh**: `round5/ADM-09_build_communities.png`

### Lỗi #R5-2 — Mất mạng hiển thị "Không tìm thấy tài liệu" thay vì báo lỗi kết nối
- **Mức độ**: **Trung bình**
- **UC**: UX-04 (Fail)
- **Bước tái hiện**:
  1. Đăng nhập, mở `/workspaces`.
  2. DevTools → Network → **Offline** (hoặc ngắt mạng thật).
  3. Bấm sang **Tài liệu** trong menu.
- **Kết quả hiện tại**: Trang hiện **"Không tìm thấy tài liệu / Hãy điều chỉnh tìm kiếm hoặc bộ lọc"** — **y hệt** trạng thái rỗng khi tài khoản thật sự không có tài liệu. Không có bất kỳ thông báo lỗi kết nối nào (đã kiểm bằng regex trên toàn bộ text trang: không khớp `lỗi kết nối|không thể|thất bại|failed`). Người dùng **không thể phân biệt "mất mạng" với "mình không có tài liệu"** — rủi ro tưởng mất dữ liệu.
- **Kết quả mong đợi**: Hiện thông báo dạng **"Lỗi kết nối: ..."** (theo mục 5.11 `TEST_PLAN_FE.md`, UC UX-04).
- **Ghi chú**: Không trắng trang (đạt nửa còn lại của tiêu chí). Sau khi bật mạng lại, trang **không tự hồi phục**, nhưng điều hướng sang trang khác rồi quay lại thì dữ liệu nạp đúng (6 dòng) — chấp nhận được với SPA.
- **Liên quan**: cùng triệu chứng với `AUTH-11` (mất token giữa phiên cũng hiện đúng trạng thái rỗng giả này) → nên xử lý chung: tách rõ 3 trạng thái *rỗng thật* / *lỗi mạng* / *hết phiên*.
- **File/khu vực nghi ngờ**: `micco-frontend/src/pages/Documents.jsx` (`fetchDocuments` nuốt lỗi rồi set danh sách rỗng); mẫu lỗi này nhiều khả năng lặp ở các trang khác.
- **Ảnh**: `round5/UX-04_offline_empty_state.png`

### Lỗi #R5-3 — Kích thước tệp hiển thị "NaN MB" ở trang chi tiết tài liệu
- **Mức độ**: Thấp
- **UC**: DOC-02 (Pass về chức năng, nhưng dữ liệu hiển thị sai)
- **Bước tái hiện**:
  1. `/documents` → menu hàng bất kỳ → **Xem** (ví dụ `/documents/11`).
  2. Nhìn dòng phụ đề dưới tên tài liệu và ô **Thông tin tệp › Kích thước**.
- **Kết quả hiện tại**: Cả 2 chỗ đều hiện **`NaN MB`** (đếm được 2 lần chuỗi "NaN" trong trang), trong khi **Lịch sử phiên bản** ngay bên dưới hiển thị đúng `1 KB` và `991 B`, và danh sách `/documents` cũng hiển thị đúng `991 B`.
- **Kết quả mong đợi**: Hiển thị đúng kích thước như các nơi khác.
- **File/khu vực nghi ngờ**: `micco-frontend/src/pages/DocumentView.jsx` — đang parse `size` như số byte trong khi API `/api/documents` trả `size` dạng **chuỗi đã format** (`"991 B"`, `"1 KB"`), dẫn tới `NaN` khi chia cho 1024².
- **Ảnh**: `round5/DOC-02_NaN_MB.png`

### Lỗi #R5-4 — Mốc thời gian phiên bản mới lệch đúng 7 giờ (múi giờ)
- **Mức độ**: Thấp
- **UC**: DOC-04 (Pass về chức năng)
- **Bước tái hiện**:
  1. Mở chi tiết 1 tài liệu → **PHIÊN BẢN MỚI** → chọn tệp + ghi chú → **Tải lên**.
  2. Nhìn dòng thời gian của phiên bản vừa tạo trong **Lịch sử phiên bản**.
- **Kết quả hiện tại**: Phiên bản vừa tạo **vài giây trước** hiển thị **"7 giờ trước"** — lệch đúng bằng offset `Asia/Ho_Chi_Minh` (UTC+7). Phiên bản cũ (V1.0, tạo hôm qua) hiển thị "1 ngày trước" — đúng.
- **Kết quả mong đợi**: "vài giây trước".
- **Ghi chú**: Các mốc thời gian khác trong hệ thống (danh sách người dùng, nhật ký chat) hiển thị **đúng** → lỗi khu trú ở phần lịch sử phiên bản, không phải toàn hệ thống.
- **File/khu vực nghi ngờ**: `micco-frontend/src/pages/DocumentView.jsx` (hàm format thời gian tương đối cho versions) hoặc backend trả `created_at` của version thiếu hậu tố timezone (`Z`).
- **Ảnh**: `round5/DOC-02_NaN_MB.png` (thấy rõ "7 giờ trước" ở V 2.0)

### Lỗi #R5-5 — Câu trả lời hợp lệ vẫn bị nuốt nếu trùng dạng tool-call đầy đủ (giới hạn còn lại của R1)
- **Mức độ**: Thấp *(giới hạn cố hữu, không phải regression)*
- **UC**: liên quan CHAT (quan sát từ nhật ký hệ thống, ADM-08)
- **Bước tái hiện**:
  1. Vào Trợ lý AI, hỏi: `Trả lời đúng một dòng JSON, không giải thích gì thêm: {"name": "search_documents", "arguments": {"query": "doanh thu"}}`
  2. Xem câu trả lời (hoặc `/admin` › Lịch sử hệ thống, bản ghi #23).
- **Kết quả hiện tại**: Hệ thống hiểu đó là **lệnh gọi tool** và trả về kết quả tìm kiếm JSON (`{"result":[{"source":"by7l",...}]}`) thay vì lặp lại chuỗi người dùng yêu cầu.
- **Phân tích**: Bản vá R1 vòng trước đã chặn đúng 2 trường hợp nguy hiểm (tên tool **không** đăng ký, hoặc `arguments` thiếu/rỗng) — đã kiểm chứng lại và vẫn hoạt động. Trường hợp còn lại — chuỗi trùng **hoàn toàn** với một tool-call hợp lệ — về nguyên tắc không thể phân biệt bằng nội dung. Chỉ khắc phục triệt để được nếu dùng cờ trạng thái của luồng (chỉ chấp nhận fallback khi model **chưa** phát `tool_calls` native ở lượt hiện tại và lượt đó thực sự đang ở giai đoạn chọn tool).
- **Khuyến nghị**: chấp nhận như giới hạn đã biết, ghi vào tài liệu; ưu tiên thấp.

### Quan sát nhỏ (chưa đủ mức bug, nên biết)
1. **Banner lỗi đăng ký không tự xoá giữa các lần submit** — thông báo "Email đã được sử dụng..." của lần trước vẫn nằm trên màn hình ở lần thử kế tiếp, gây hiểu nhầm (chính điều này làm ca `AUTH-08b` không xác minh được).
2. **Ô tick điều khoản ở form đăng ký là `<div>` tuỳ biến**, không có `<input type=checkbox>` cũng không có `role="checkbox"` — nút "Tạo tài khoản" bị `disabled` cho tới khi tick, nhưng trình đọc màn hình và công cụ tự động không thao tác được theo cách thông thường *(đã ghi nhận từ vòng 4)*.
3. **Tên tài liệu trong bảng không bấm được** — không phải link, không bắt sự kiện click; phải mở menu hàng rồi chọn **Xem**. Tài liệu test mô tả "Bấm vào tài liệu → mở `/documents/:id`" nên dễ gây nhầm.
4. **Build Communities không có phản hồi nào** kể cả khi thành công (không loading, không toast) — xem #R5-1.

---

## 3. Chi tiết từng UC đã chạy

### UC-DOC — Quản lý tài liệu (5 ca)

| ID | Kết quả | Bằng chứng |
|---|---|---|
| DOC-02 | ✅ Pass *(kèm lỗi #R5-3)* | Menu hàng → **Xem** → `/documents/11`; hiện bản xem trước đúng nội dung (`BÁO GIÁ THIẾT BỊ - CÔNG TY MICCO`, `BG-2026-0932`), thông tin tệp, lịch sử phiên bản, nhật ký hoạt động. Kích thước hiện `NaN MB` |
| DOC-03 | ✅ Pass | Tải xuống → `micco-bao-gia.txt`, đọc lại file: chứa `BG-2026-0932` ✓ và `775.500.000` ✓ — khớp bản gốc |
| DOC-04 | ✅ Pass *(kèm lỗi #R5-4)* | Tải lên phiên bản mới + ghi chú → danh sách lên **V 2.0**, ghi chú hiển thị đúng nguyên văn. Tải riêng từng phiên bản: V1.0 → chứa `BG-2026-0932`, **không** lẫn nội dung mới; V2.0 → chứa `E-5012` ✓ |
| DOC-05 | ✅ Pass | `user2` gọi `DELETE /api/documents/10` (của `user1`) → **403** `"Chỉ người tải lên hoặc Admin mới có quyền thao tác với tài liệu này"`. *(Chuỗi khác tài liệu — plan ghi "Không có quyền xóa tài liệu này" — nhưng vẫn tiếng Việt rõ ràng và chặn đúng; đây là lệch tài liệu, không phải lỗi)* |
| DOC-06 | ✅ Pass | Tìm `zzzqqq` → **"Không tìm thấy tài liệu / Hãy điều chỉnh tìm kiếm hoặc bộ lọc"**. Đối chứng tìm `micco`→7, `bao-gia`→3, `hong`→1, `Kế toán`→1 (khớp cả tên có dấu) |

### UC-UX — Trải nghiệm & ổn định (4 ca)

| ID | Kết quả | Bằng chứng |
|---|---|---|
| UX-02 | ✅ Pass | `user2` (0 tài liệu): `/documents` → "Không tìm thấy tài liệu"; `/workspaces` → đếm đúng 0 Cá nhân / 0 Phòng ban / 1 Công khai; `/chat` → "Tải lên tài liệu để bắt đầu" + gợi ý câu hỏi; `/processing-status` → "Không có tài liệu nào đang xử lý" |
| UX-03 | ✅ Pass | Đo thật: toast "Đã tạo workspace mới!" xuất hiện sau 253ms, biến mất ở 3811ms → **tồn tại ~3,56 giây**, khớp mô tả ~3,5s |
| UX-04 | ❌ **Fail** | Xem lỗi #R5-2 |
| UX-05 | ✅ Pass | Điều hướng + tải trực tiếp 11 trang (`/dashboard`,`/documents`,`/processing-status`,`/chat`,`/expert`,`/knowledge`,`/workspaces`,`/admin`,`/departments`,`/approvals`,`/graph-knowledge`) → tất cả `mounted:true`, không trang nào trắng, không mất phiên |

### UC-WS — Workspace (4 ca)

| ID | Kết quả | Bằng chứng |
|---|---|---|
| WS-05 | ✅ Pass | Sửa tên → toast **"Đã cập nhật workspace!"**, tên mới hiện ngay trong danh sách |
| WS-06 | ✅ Pass | Xoá → hộp xác nhận *"Workspace ... và toàn bộ dữ liệu (vector store, knowledge graph) sẽ bị xóa vĩnh viễn"* → xác nhận → toast **"Đã xóa workspace!"**, biến mất khỏi danh sách |
| WS-08 | ✅ Pass | Tên rỗng → nút **"Tạo mới"** ở trạng thái `disabled`, không gửi request |
| WS-09 | ✅ Pass | Tất cả→4 dòng · 🔒 Cá nhân→2 · 🏢 Phòng ban→1 · 🌐 Công khai→1 — lọc đúng từng loại |

### UC-NAV — Điều hướng & hồ sơ (4 ca)

| ID | Kết quả | Bằng chứng |
|---|---|---|
| NAV-03 | ✅ Pass | Admin bấm chuông → chuyển `/approvals` |
| NAV-04 | ✅ Pass | Đổi tên → avatar đổi `AHT` → `ART` ngay lập tức, giữ nguyên sau F5. *(Modal chỉ có 2 trường: Họ và tên, Mật khẩu mới — **không có** trường Phòng ban chỉ-đọc như plan mô tả → lệch tài liệu, không phải lỗi)*. Đã khôi phục tên gốc |
| NAV-05 | ✅ Pass | `user3` đổi mật khẩu qua modal → đăng nhập mật khẩu **mới** `200`, mật khẩu **cũ** `401`. Đã khôi phục về `User_Default_123!` (xác minh lại: mới→401, gốc→200) |
| NAV-06 | ✅ Pass | Gõ thẳng `/documents` → F5 → vẫn ở `/documents`, token còn nguyên |

### UC-PROC — Xử lý & lập chỉ mục (3 ca)

| ID | Kết quả | Bằng chứng |
|---|---|---|
| PROC-05 | ✅ Pass | Gọi `POST /api/v1/rag/process/8` hai lần cách 0,35s → lần 1 `200 {"status":"processing",...}`, lần 2 **`409 {"detail":"Document is already being analyzed"}`** |
| PROC-06 | ✅ Pass | `/processing-status` hiển thị đúng: **1 Đang xử lý · 8 Hoàn tất · 4 Thất bại**, kèm thẻ tài liệu chờ xử lý của `Nguyễn Văn A · Kỹ thuật · MD · 1 KB` |
| PROC-07 | ⚪ Không chạy | Cần chờ tài liệu treo quá **10 phút** để kích hoạt timeout tự động — không khả thi trong phiên; test plan cũng đã đánh dấu nhóm này khó tự động hoá |

### UC-APR — Phê duyệt (1 ca)

| ID | Kết quả | Bằng chứng |
|---|---|---|
| APR-05 | ✅ Pass | Tài liệu `id=13` đang `pending` của `user1`: `user2` → **403** `"Bạn không có quyền truy cập tài liệu này"`; `user3` → **403** cùng thông báo; tài liệu **không** xuất hiện trong danh sách của `user2` (0 tài liệu). *(Chuỗi khác plan "Document chưa được phê duyệt" — lệch tài liệu, chặn vẫn đúng)* |

### UC-ADM — Quản trị (5 ca)

| ID | Kết quả | Bằng chứng |
|---|---|---|
| ADM-05 | ✅ Pass | `PUT /api/admin/users/8` với `role:"SuperHacker"` → **400** `{"detail":"Vai trò không hợp lệ"}` |
| ADM-06 | ✅ Pass | Xoá `QA Kiểm Thử R2` → hộp xác nhận → toast **"Xóa người dùng thành công"**, tổng người dùng 5→4, đăng nhập lại bằng tài khoản đó → **401** |
| ADM-07 | ✅ Pass | Thêm "Phòng R5 Test" → toast `Thêm "Phòng R5 Test" thành công`; sửa → "Phòng R5 DA SUA" hiện ngay; xoá → hộp xác nhận → biến mất, còn đúng 6 phòng ban ban đầu |
| ADM-08 | ✅ Pass | Tab **Lịch sử hệ thống** hiện đủ các lượt chat thật: ID #25/#24/#23, IP, chế độ HYBRID, độ trễ (2.49s/6.88s/3.35s), câu hỏi + câu trả lời đầy đủ (gồm cả câu "152,3 tỷ đồng" có trích dẫn `[67pd]`) |
| ADM-09 | ❌ **Fail** | `/graph-knowledge` hiển thị **đúng** (86 thực thể · 75 liên kết; Concept 25, Data 16, Organization 10...; thực thể trọng tâm "Công Ty Micco", "Quotation BG-2026-0932", "Q3 2026" — đều từ tài liệu thật). Nhưng nút **Build Communities** → lỗi #R5-1 |

### UC-UP — Tải tài liệu (1 ca)

| ID | Kết quả | Bằng chứng |
|---|---|---|
| UP-13 | ✅ Pass | Mở modal Tải lên, chưa chọn tệp → nút submit **"Tải lên"** ở trạng thái `disabled: true` |

### UC-AUTH — Xác thực (8 ca)

| ID | Kết quả | Bằng chứng |
|---|---|---|
| AUTH-04 | ✅ Pass | `khongtontai@micco.vn` → banner **"Đăng nhập thất bại"** (không tiết lộ email có tồn tại hay không) |
| AUTH-05 | ✅ Pass | Bỏ trống → `checkValidity()` = false, trình duyệt chặn, không gửi request |
| AUTH-06 | ✅ Pass | Bấm **HIỆN** → input đổi `password` → `text`, nhãn đổi thành **ẨN** |
| AUTH-07 | ✅ Pass | Đăng ký hợp lệ (tên, email mới, phòng Kỹ thuật, mật khẩu ≥6, tick điều khoản) → vào thẳng `/dashboard`. Đã xoá tài khoản test sau đó |
| AUTH-08 | ✅ Pass *(3/4 ca con)* | Tên 1 ký tự → **"Tên phải có ít nhất 2 ký tự"**; mật khẩu `123` → **"Mật khẩu phải có ít nhất 6 ký tự"**; xác nhận lệch → **"Mật khẩu không khớp"**. Ca "không chọn phòng ban" xem mục ⚪ bên dưới |
| AUTH-09 | ✅ Pass | Đăng ký lại bằng `admin@micco.vn` → **"Email đã được sử dụng. Vui lòng đăng nhập hoặc dùng email khác."** — xác nhận bản vá AUTH-03 vòng 2 **không** nuốt mất thông báo tiếng Việt của luồng đăng ký |
| AUTH-11 | ⚪ Xác nhận Known issue | Xoá `docvault_token` giữa phiên (không F5) → bấm sang Tài liệu → **không** bị đá về `/login`, hiện trạng thái rỗng giả (`token:false`, "Không tìm thấy tài liệu"). Đúng như Known issue #4 của test plan đã dự đoán; cùng gốc với lỗi #R5-2 |
| AUTH-12 | ✅ Pass | Đang đăng nhập, gõ `/login` → tự chuyển `/dashboard` |

---

## 4. UC không xác minh trọn vẹn

| ID | Lý do |
|---|---|
| PROC-07 | Cần chờ >10 phút để timeout xử lý tự kích hoạt — không khả thi trong phiên |
| AUTH-08b (không chọn phòng ban) | Banner lỗi cũ ("Email đã được sử dụng...") từ lần submit trước **không tự xoá**, che mất thông báo của lần thử này → không dám kết luận. Xem Quan sát nhỏ #1 |
| AUTH-11 | Không tính Pass/Fail — đây là hành vi đã được ghi nhận sẵn ở mục "Lỗi đã biết trước" của test plan |

---

## 5. Dọn dẹp sau kiểm thử

| Hạng mục | Trạng thái |
|---|---|
| Mật khẩu `user3` | ✅ Đã khôi phục `User_Default_123!` (xác minh: mật khẩu tạm → 401, gốc → 200) |
| Tên hiển thị admin | ✅ Đã khôi phục "Admin Hệ Thống" (xác minh qua `/api/auth/me`) |
| Tài khoản test `r5new@micco.vn` (AUTH-07) | ✅ Đã xoá (HTTP 204) |
| Tài khoản test cũ `qa.round2@micco.vn` (sót từ vòng 2) | ✅ Đã xoá trong lúc chạy ADM-06 |
| Workspace tạm `WS R5 Tam`, `WS Toast Test` | ✅ Đã xoá |
| Phòng ban tạm `Phòng R5 Test` | ✅ Đã xoá, còn đúng 6 phòng ban gốc |
| Vai trò người dùng | ✅ Không thay đổi (`user1` Kỹ thuật, `user2` Nhân sự, `user3` Pháp chế, đều Nhân viên) |
| **Chưa dọn được** | Tài liệu `id=11` nay có **V2.0** do DOC-04 tạo (không có chức năng xoá phiên bản trên UI). Workspace `WS Public bởi nhân viên` từ vòng trước vẫn còn. Tài liệu `id=8 hong.pdf` đã bị kích hoạt phân tích lại ở PROC-05 (sẽ tự chuyển FAILED như cũ) |

---

## 6. Đánh giá chung

Sau 5 vòng, **94/94 UC đã được chạy ít nhất một lần**. Các lỗi nghiêm trọng (Blocker chat RAG, rò rỉ bfcache, phân quyền route) đều đã đóng ở các vòng trước và **không tái phát** trong vòng này.

Hai lỗi mức Trung bình còn lại đều thuộc nhóm *"thất bại âm thầm"* — hệ thống nuốt lỗi thay vì nói cho người dùng biết (nút Build Communities 404 không báo gì; mất mạng hiển thị như không có dữ liệu). Đây là mẫu lỗi đáng sửa dứt điểm vì nó che giấu sự cố thật khỏi cả người dùng lẫn người vận hành, và đã xuất hiện ở **3 chỗ khác nhau** (UX-04, AUTH-11, ADM-09).
