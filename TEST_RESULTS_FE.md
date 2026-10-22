# TEST_RESULTS_FE.md — Kết quả kiểm thử giao diện MiccoRAG-v3

> Thực thi thật bằng trình duyệt thật (ego-browser) + kiểm chứng chéo qua API (`curl`) trên URL public
> **https://ctrl-seeking-bills-neural.trycloudflare.com**, theo `TEST_PLAN_FE.md`.
> Ngày chạy: 2026-09-12 · Tài khoản dùng: `admin@micco.vn`, `user1@micco.vn`.
> ⚠️ Đây là kết quả **thực thi trong 1 phiên**, không chạy hết 94 UC (xem lý do ở mục 4). Không có kết quả nào trong tài liệu này được suy đoán — mọi dòng "Pass" đều có quan sát thật (ảnh chụp màn hình và/hoặc phản hồi API thật) kèm theo.

---

## 1. Bảng tổng hợp

| Mức ưu tiên | Đã chạy | Pass | Fail | Không chạy |
|---|---|---|---|---|
| P0 (33) | 24 | 17 | 7 | 9 |
| P1 (45) | 8 | 7 | 1 | 37 |
| P2 (16) | 1 | 1 | 0 | 15 |
| **Tổng (94)** | **33** | **25** | **8** | **61** |

*(PROC-02, PROC-03 được tính vào "Không chạy" — dù đã xác nhận trạng thái tài liệu cuối cùng qua API, không bắt được đúng lúc nội dung toast cụ thể mà UC yêu cầu kiểm tra, nên không dám nhận Pass/Fail cho đúng UC đó — xem chi tiết ở mục 3.)*

**Kết luận nhanh**: hệ thống có **1 lỗi Blocker** khiến toàn bộ tính năng chat/RAG (chức năng lõi của sản phẩm) không trả lời được câu hỏi nào — xem Lỗi #1. Tiêu chí "100% P0 Pass" ở mục 9 của `TEST_PLAN_FE.md` **KHÔNG đạt**.

---

## 2. Danh sách lỗi cho Dev

### Lỗi #1 — Chat RAG trả về nguyên văn JSON tool-call thay vì câu trả lời
- **Mức độ nghiêm trọng**: **Blocker**
- **UC liên quan**: CHAT-01, CHAT-02, CHAT-04 (chạy thật, đều Fail); suy ra ảnh hưởng toàn bộ CHAT-01→15 vì lỗi xảy ra ở bước sinh câu trả lời đầu tiên, trước khi bất kỳ nội dung tài liệu nào được dùng.
- **Bước tái hiện**:
  1. Đăng nhập `admin@micco.vn` (hoặc bất kỳ tài khoản nào).
  2. Vào **Trợ lý AI**, chọn workspace có tài liệu đã `indexed` (VD "WS Kiểm thử Cá nhân").
  3. Gõ bất kỳ câu hỏi nào, VD: `Doanh thu quý III năm 2026 là bao nhiêu?` → Enter.
  4. Lặp lại với câu hỏi khác, thử cả 3 chế độ Hybrid / Vector only / Graph only.
- **Kết quả hiện tại**: Tin nhắn trả lời là nguyên văn:
  `{"name": "search_documents", "arguments": {"query": "doanh thu quý III năm 2026"}}`
  Không có tìm kiếm nào được thực thi, không có nguồn trích dẫn, không trả lời câu hỏi. Tái diễn 100% (3/3 lần thử, cả 2 chế độ đã thử).
- **Kết quả mong đợi**: Trả lời dựa trên nội dung tài liệu đã index (VD CHAT-01 kỳ vọng trả lời có "152,3 tỷ đồng" kèm trích dẫn nguồn) — theo mục 5.7 `TEST_PLAN_FE.md`.
- **File/khu vực nghi ngờ**: `micco-backend/backend/app/api/chat_agent.py`, dòng ~487-497:
  ```python
  elif is_gemini:
      tools = [_get_gemini_tool()]
      ...
  else:
      # Ollama: append mandatory tool prompt to system prompt
      effective_system_prompt = system_prompt + "\n\n" + OLLAMA_TOOL_SYSTEM
      ...
  ```
  Code chỉ phân biệt 2 nhánh: `is_gemini` (dùng native tool-calling) và **"còn lại coi là Ollama"** (dùng prompt-injection, yêu cầu model tự output `<tool_call>{...}</tool_call>`). Backend hiện đang cấu hình `LLM_PROVIDER=openai` (model `gpt-4.1-mini` qua cổng LiteLLM) — không phải Gemini, nên rơi vào nhánh "Ollama" một cách nhầm lẫn. Model OpenAI trả JSON đúng nội dung nhưng **không bọc trong thẻ `<tool_call>...</tool_call>`** như prompt yêu cầu, khiến bộ parser phía sau (tìm theo thẻ này) không nhận diện được lệnh gọi tool, và JSON thô bị lọt ra làm câu trả lời cuối cùng.
  → Cần thêm 1 nhánh xử lý riêng cho các provider generic (OpenAI/DeepSeek/Anthropic/...) qua cổng LiteLLM — hoặc nới lỏng bộ parser để chấp nhận JSON tool-call không có thẻ bọc, hoặc bật OpenAI's native function-calling (`tools=` param) giống Gemini thay vì dùng kiểu prompt-injection dành cho Ollama.
- **Ghi chú**: đây nhiều khả năng là hệ quả trực tiếp của việc đổi `LLM_PROVIDER` sang `openai` qua cổng LiteLLM mới thêm ở phiên làm việc trước — `chat_agent.py` chưa được cập nhật theo.

### Lỗi #2 — Dữ liệu sau đăng xuất vẫn hiển thị khi bấm Back (bfcache)
- **Mức độ nghiêm trọng**: **Cao**
- **UC liên quan**: AUTH-13 (Fail)
- **Bước tái hiện**:
  1. Đăng nhập `admin@micco.vn`, vào `/dashboard` (có dữ liệu thật: 10 tài liệu, 4 workspace...).
  2. Avatar → **Đăng xuất** → xác nhận về `/login`, `localStorage.docvault_token` đã bị xoá (đã kiểm chứng).
  3. Bấm nút **Back** của trình duyệt.
- **Kết quả hiện tại**: Trình duyệt quay lại `/dashboard` và hiển thị **đầy đủ dữ liệu thật** đã fetch trước đó (tổng tài liệu, dung lượng, danh sách workspace...) — trang được phục vụ nguyên trạng từ bộ nhớ đệm back-forward cache (bfcache) của trình duyệt, không re-check trạng thái đăng nhập khi khôi phục.
- **Kết quả mong đợi**: "Về `/login`, token bị xoá, Back không vào lại được `/dashboard`" (mục 5.1 `TEST_PLAN_FE.md`, UC AUTH-13).
- **File/khu vực nghi ngờ**: `micco-frontend/src` — không thấy xử lý sự kiện `pageshow` (`event.persisted === true`) để buộc reload/re-check auth khi trang được khôi phục từ bfcache. Thường sửa bằng cách lắng nghe `window.addEventListener('pageshow', e => { if (e.persisted) location.reload() })` ở layout gốc, hoặc gửi header `Cache-Control: no-store` cho các trang yêu cầu đăng nhập.
- **Rủi ro thực tế**: trên máy dùng chung, người dùng "đăng xuất" xong người tiếp theo bấm Back vẫn xem được dữ liệu (số liệu, tên workspace) của người trước — rò rỉ thông tin.

### Lỗi #3 — Nhân viên tạo workspace "Công khai" bị âm thầm hạ xuống "Cá nhân" thay vì bị chặn
- **Mức độ nghiêm trọng**: **Cao**
- **UC liên quan**: WS-03 (Fail)
- **Bước tái hiện**:
  1. Đăng nhập `user1@micco.vn` (vai trò Nhân viên).
  2. Vào `/workspaces` → **Tạo mới** → đặt tên bất kỳ → chọn loại **🌐 Công khai** → **Tạo mới**.
- **Kết quả hiện tại**: Toast báo **"Đã tạo workspace mới!"** (thành công), nhưng workspace được tạo ra có `"visibility": "private"` (xác nhận qua `GET /api/v1/workspaces`) — **không phải Công khai như đã chọn**, và **không có bất kỳ cảnh báo/thông báo nào** cho người dùng biết lựa chọn của họ đã bị đổi.
- **Kết quả mong đợi**: Bị chặn với lỗi rõ ràng — `403` **"Chỉ Admin mới được tạo workspace công khai"** (mục 5.3 `TEST_PLAN_FE.md`, UC WS-03; chuỗi lỗi này thực sự tồn tại trong `app/api/workspaces.py` nhưng dường như không được kích hoạt qua đường tạo mới này).
- **File/khu vực nghi ngờ**: `micco-backend/backend/app/api/workspaces.py` (endpoint `POST /api/v1/workspaces`) — có vẻ giá trị `visibility` được ép/chuẩn hoá về `"private"` cho non-admin **trước khi** đến đoạn code kiểm tra quyền và trả lỗi 403, khiến nhánh kiểm tra quyền không bao giờ được kích hoạt trên đường đi này.
- **Ghi chú**: không phải lỗ hổng leo thang quyền (kết quả thực tế *hạn chế hơn* ý định người dùng, không phải ngược lại), nhưng là hành vi âm thầm gây hiểu lầm — người dùng tưởng đã tạo workspace công khai nhưng thực chất chỉ mình họ thấy.

### Lỗi #4 — Danh sách người dùng trong Quản trị không tự cập nhật sau khi lưu
- **Mức độ nghiêm trọng**: Trung bình
- **UC liên quan**: ADM-03 (Pass về mặt dữ liệu, nhưng phát sinh lỗi UX này)
- **Bước tái hiện**:
  1. Đăng nhập admin → `/admin` → tab Người dùng → sửa 1 người dùng (VD gán phòng ban) → **Lưu thay đổi**.
  2. Quan sát bảng danh sách ngay sau khi modal đóng (không F5).
- **Kết quả hiện tại**: Modal đóng, toast không rõ ràng, nhưng cột "PHÒNG BAN" trong bảng **vẫn hiển thị "Chưa phân"** như trước khi sửa. Dữ liệu thực tế ĐÃ được lưu đúng ở backend (xác nhận qua `GET /api/admin/users`), chỉ có UI không refetch/refresh state cục bộ. F5 lại thì hiển thị đúng.
- **Kết quả mong đợi**: Bảng cập nhật ngay sau khi lưu thành công, không cần F5.
- **File/khu vực nghi ngờ**: `micco-frontend/src/pages/Admin.jsx` hoặc `src/components/admin/UserModal.jsx` — hàm xử lý sau khi lưu thành công (`onSave`/`handleSubmit`) có thể chỉ đóng modal mà không gọi lại `fetchUsers()`/cập nhật state danh sách.

### Lỗi #5 — File `.xlsx`/`.png` được chấp nhận ở bước upload dù server không hỗ trợ, chỉ fail sau khi xử lý xong
- **Mức độ nghiêm trọng**: Trung bình *(đã biết trước một phần — xem Known issue #1 trong TEST_PLAN_FE.md, nhưng chi tiết cơ chế dưới đây là quan sát mới)*
- **UC liên quan**: UP-05, UP-06 (cả hai Fail so với kỳ vọng của tài liệu)
- **Bước tái hiện**:
  1. Đăng nhập admin → `/documents` → Tải lên → chọn `bang-luong.xlsx` (hoặc `anh-minh-hoa.png`) → Tải lên.
- **Kết quả hiện tại**: Toast báo **"Tải lên 1 tài liệu thành công"**, tài liệu vào danh sách bình thường. Vài giây sau, trạng thái tự chuyển sang **FAILED** (xác nhận qua `GET /api/documents`) — nghĩa là file được server CHẤP NHẬN ở bước upload rồi mới thất bại ở bước xử lý/parse, không bị chặn ngay từ đầu như dự đoán.
- **Kết quả mong đợi** (theo TEST_PLAN_FE.md mục 3.2): bị từ chối ngay ở bước upload với `400 File type .xlsx not allowed`.
- **File/khu vực nghi ngờ**: `micco-backend/backend/app/api/documents.py` — hằng số `ALLOWED_EXTENSIONS` (được một agent điều tra trước đó ghi nhận là `{".pdf", ".txt", ".md", ".docx", ".pptx"}`) dường như **không thực sự được áp dụng** trên đường upload đang chạy thực tế, hoặc có nhánh khác cho phép các đuôi file này đi qua.
- **Tác động UX**: người dùng chờ cả chu trình upload + xử lý (có thể vài chục giây) chỉ để nhận một tài liệu FAILED không rõ nguyên nhân, thay vì bị từ chối ngay lập tức.

### Lỗi #6 — Danh sách định dạng cho phép ở client không nhất quán
- **Mức độ nghiêm trọng**: Thấp
- **UC liên quan**: UP-05, UP-06, UP-07
- **Bước tái hiện**: So sánh hành vi khi chọn từng loại file trong modal Tải lên:
  - `.xlsx`, `.png` → được chấp nhận, lên danh sách chờ, KHÔNG có cảnh báo phía client.
  - `.zip` → bị chặn ngay phía client: **"Định dạng file không được hỗ trợ: .zip"**.
  - `.exe` → bị chặn ngay phía client: **"Định dạng file không được hỗ trợ: .exe"**.
- **Kết quả hiện tại**: Client CÓ danh sách trắng riêng (khác dòng gợi ý hiển thị "PDF, DOCX, XLSX, PPTX, PNG, JPG, MD, ZIP"), nhưng danh sách đó tự mâu thuẫn: `.zip` được liệt kê trong dòng gợi ý nhưng lại bị danh sách trắng thực tế chặn; `.xlsx`/`.png` cũng được liệt kê trong gợi ý và được danh sách trắng cho qua, nhưng server thực tế không hỗ trợ (→ Lỗi #5).
- **Kết quả mong đợi**: Một danh sách nhất quán duy nhất, khớp giữa: dòng gợi ý hiển thị, danh sách trắng phía client, và `ALLOWED_EXTENSIONS` thực tế ở server.
- **File/khu vực nghi ngờ**: `micco-frontend/src/components/documents/UploadZone.jsx` (hoặc tương đương) — hằng số danh sách định dạng phía client cần đồng bộ với `ALLOWED_EXTENSIONS` ở backend.

### Lỗi #7 — Thông báo lỗi đăng nhập sai hiển thị tiếng Anh, không nhất quán ngôn ngữ
- **Mức độ nghiêm trọng**: Thấp
- **UC liên quan**: AUTH-03 (Fail theo quy tắc so khớp chuỗi chính xác của TEST_PLAN_FE.md, dù chức năng chặn đăng nhập vẫn đúng)
- **Bước tái hiện**: Đăng nhập với email đúng (`admin@micco.vn`), mật khẩu sai.
- **Kết quả hiện tại**: Banner đỏ hiển thị nguyên văn tiếng Anh **"Invalid email or password"** (raw `err.detail` từ API).
- **Kết quả mong đợi**: **"Đăng nhập thất bại"** (tiếng Việt, theo mục 5.1 TEST_PLAN_FE.md — toàn bộ phần còn lại của giao diện đều tiếng Việt).
- **File/khu vực nghi ngờ**: `micco-frontend/src/pages/AuthPage.jsx` — logic hiển thị lỗi có thể đang ưu tiên `err.detail` (message thô từ backend) thay vì dùng chuỗi mặc định tiếng Việt khi backend luôn trả `detail`.

### Lỗi #8 — Toast khi Nhân viên upload thiếu câu "Đang chờ phê duyệt"
- **Mức độ nghiêm trọng**: Thấp
- **UC liên quan**: UP-04 (dữ liệu đúng — `approval_status: pending` xác nhận qua API — nhưng thông báo không khớp)
- **Bước tái hiện**: Đăng nhập `user1` → `/documents` → Tải lên 1 file bất kỳ.
- **Kết quả hiện tại**: Toast chỉ hiện **"Tải lên 1 tài liệu thành công"** — giống hệt toast khi Admin upload (tự động duyệt), không có gợi ý nào về việc tài liệu đang chờ duyệt.
- **Kết quả mong đợi**: **"Tải lên thành công! Đang chờ phê duyệt."** (theo mục 5.4 TEST_PLAN_FE.md, để phân biệt rõ với luồng admin).
- **File/khu vực nghi ngờ**: `micco-frontend/src/pages/Documents.jsx` — toast thành công có thể đang dùng chung 1 template cho mọi vai trò thay vì phân nhánh theo `approval_status` trả về từ response.

---

## 3. Chi tiết từng UC đã chạy

### UC-AUTH

| ID | Kết quả | Bằng chứng |
|---|---|---|
| AUTH-01 | ✅ Pass | Đăng nhập admin → `/dashboard`, sidebar đủ Phê duyệt/Quản trị/Đồ thị tri thức, `docvault_token` có giá trị. Ảnh: `AUTH-01_login_ok.png` |
| AUTH-02 | ✅ Pass | Đăng nhập `user1` → `/dashboard`, xác nhận qua `document.querySelectorAll('a')` sidebar chỉ có 8 mục cơ bản, không có Phê duyệt/Quản trị/Đồ thị tri thức |
| AUTH-03 | ❌ Fail | Bị chặn đúng (không vào được hệ thống), nhưng banner hiển thị **"Invalid email or password"** (tiếng Anh) thay vì "Đăng nhập thất bại" — xem Lỗi #7. Ảnh: `AUTH-03_wrong_pw.png` |
| AUTH-10 | ✅ Pass | Sửa `docvault_token` thành `abc` → F5 → bị đưa về `/login`, `localStorage.getItem('docvault_token')` = null. Ảnh: `AUTH-10_bad_token.png` |
| AUTH-13 | ❌ Fail | Đăng xuất đúng (về `/login`, token bị xoá), nhưng bấm Back hiển thị lại đầy đủ dữ liệu dashboard cũ — xem Lỗi #2. Ảnh: `AUTH-13_back_after_logout.png` |

### UC-NAV

| ID | Kết quả | Bằng chứng |
|---|---|---|
| NAV-01 | ✅ Pass | So sánh sidebar admin (đủ 11 mục) vs `user1` (8 mục cơ bản, không có Phê duyệt/Quản trị/Đồ thị tri thức) — đúng kỳ vọng |

### UC-WS

| ID | Kết quả | Bằng chứng |
|---|---|---|
| WS-01 | ✅ Pass | Tạo "WS Kiểm thử Cá nhân" loại Cá nhân → toast "Đã tạo workspace mới!", xuất hiện trong bảng, đếm "1 Cá nhân" đúng |
| WS-02 | ✅ Pass | Tạo "WS Công khai Kiểm thử" loại Công khai → toast thành công, đếm "1 Công khai" đúng |
| WS-03 | ❌ Fail | Nhân viên `user1` tạo workspace chọn "Công khai" → tạo "thành công" nhưng `visibility` thực tế lưu là `"private"` (xác nhận qua API), không có cảnh báo — xem Lỗi #3 |

### UC-UP (upload file thật)

| ID | File | Kết quả | Bằng chứng |
|---|---|---|---|
| UP-01 | `micco-bao-cao-noi-bo.pdf` | ✅ Pass | Toast "Tải lên thành công!", modal "Tài liệu của bạn đã được tải lên thành công." Ảnh: `UP-01_result.png` |
| UP-02 | 3 file (`.docx`,`.md`,`.txt`) | ✅ Pass | Toast "Tải lên 3 tài liệu thành công". Ảnh: `UP-02_multi_upload.png` |
| UP-04 | `micco-bao-gia.txt` (user1) | ✅ Pass (dữ liệu) / xem Lỗi #8 (toast) | `approval_status: "pending"` xác nhận qua API |
| UP-05 | `bang-luong.xlsx` | ❌ Fail (so với kỳ vọng) | Chấp nhận upload, "failed" sau khi xử lý — xem Lỗi #5 |
| UP-06 | `anh-minh-hoa.png` | ❌ Fail (so với kỳ vọng) | Tương tự UP-05 — chấp nhận rồi "failed" |
| UP-07 | `goi-cai-dat.zip` | ✅ Pass (kết quả cuối đúng — bị từ chối) | Chặn **phía client**: "Định dạng file không được hỗ trợ: .zip" — cơ chế khác dự đoán (server-side) nhưng kết quả cuối giống nhau (không upload được). Xem thêm Lỗi #6 |
| UP-08 | `phan-mem.exe` | ✅ Pass | Chặn phía client: "Định dạng file không được hỗ trợ: .exe". Ảnh: `UP-08_exe_result.png` |
| UP-09 | `qua-lon.pdf` (57,7MB) | ✅ Pass | "File qua-lon.pdf vượt quá giới hạn 50MB", không được thêm vào danh sách. Ảnh: `UP-09_oversized_result.png` |
| UP-10 | `rong.pdf` (0 byte) | ✅ Pass | Upload qua được, `status: "failed"` xác nhận qua API |
| UP-11 | `hong.pdf` | ✅ Pass | Upload qua được, `status: "failed"` xác nhận qua API |
| UP-12 | Tên file dài có dấu | ✅ Pass | Upload thành công, tên hiển thị cắt gọn "Tài liệu nội bộ - Phòn...", layout không vỡ. Ảnh: `UP-12_long_filename.png` |

### UC-PROC

| ID | Kết quả | Bằng chứng |
|---|---|---|
| PROC-01 | ✅ Pass | Quan sát trực tiếp badge trạng thái "Đang phân tích" → "Đang lập chỉ mục" trên UI; toàn bộ 5 tài liệu tốt cuối cùng đạt `status: "indexed"` qua API |
| PROC-02 | ⚪ Không chạy trọn vẹn | Xác nhận trạng thái cuối = `indexed` qua API cho tất cả tài liệu tốt, nhưng **không bắt được** đúng lúc toast "✅ ... đã xử lý xong" xuất hiện trên màn hình (xử lý xảy ra nhanh giữa các lệnh) — không dám nhận Pass cho phần toast cụ thể |
| PROC-03 | ⚪ Không chạy trọn vẹn | Tương tự — xác nhận `status: "failed"` qua API cho `bang-luong.xlsx`/`anh-minh-hoa.png`/`rong.pdf`/`hong.pdf`, nhưng không bắt được toast "❌ ... xử lý thất bại" cụ thể trên màn hình |

### UC-APR

| ID | Kết quả | Bằng chứng |
|---|---|---|
| APR-01 | ✅ Pass | Sau khi `user1` upload, đăng nhập lại admin → badge "1" trên menu Phê duyệt, thẻ tài liệu chờ duyệt hiển thị đúng người upload + phòng ban |
| APR-02 | ✅ Pass | Bấm Phê duyệt → toast "Đã phê duyệt và đang bắt đầu xử lý", tài liệu chuyển "Đang lập chỉ mục". Ảnh: `APR-02_approved.png` |

### UC-CHAT (chat thật)

| ID | Câu hỏi | Kết quả | Bằng chứng |
|---|---|---|---|
| CHAT-01 | "Doanh thu quý III năm 2026 là bao nhiêu?" | ❌ Fail (Blocker #1) | Trả về JSON tool-call thô, không trả lời |
| CHAT-02 | "Ai là người đại diện theo pháp luật của công ty?" | ❌ Fail (Blocker #1) | Tương tự |
| CHAT-04 | "Nhân viên được nghỉ phép bao nhiêu ngày một năm?" (chế độ Vector only) | ❌ Fail (Blocker #1) | Tương tự, xác nhận lỗi xảy ra ở cả chế độ Vector only, không riêng Hybrid. Ảnh: `CHAT-01_doanh_thu.png`, `CHAT-02_bug_repro.png` |
| CHAT-03, 05–15 | — | ⚪ Không chạy | Bị chặn hoàn toàn bởi Lỗi #1 (Blocker) — mọi câu hỏi đều thất bại ở cùng một điểm (bước sinh phản hồi đầu tiên), lặp lại 12 lần nữa sẽ chỉ tái tạo cùng 1 bằng chứng, không tạo thêm giá trị chẩn đoán. Cần sửa Lỗi #1 trước, sau đó chạy lại toàn bộ nhóm CHAT |

### UC-ADM

| ID | Kết quả | Bằng chứng |
|---|---|---|
| ADM-01 | ✅ Pass | Số liệu dashboard (tổng người dùng ban đầu = 4, sau đó tổng tài liệu tăng đúng theo từng lần upload, số workspace tăng đúng) khớp với thao tác thực tế đã làm |
| ADM-02 | ⚪ Không chạy | Không kịp thực hiện luồng "Thêm người dùng mới" trong phạm vi thời gian phiên này (P0 — cần chạy bổ sung) |
| ADM-03 | ✅ Pass (dữ liệu) / xem Lỗi #4 (UX) | Gán `user1`→Kỹ thuật, `user2`→Nhân sự; xác nhận đúng qua `GET /api/admin/users` và sau F5 |

### UC-SEC

| ID | Kết quả | Bằng chứng |
|---|---|---|
| SEC-01 | ✅ Pass | `user1` gõ `/admin` → trang mở được nhưng bảng rỗng "Không tìm thấy người dùng" (đúng khớp lỗ hổng đã biết: chỉ chặn ở API). Ảnh: `SEC-01_employee_admin_access.png` |
| SEC-02 | ✅ Pass (một phần) | Chỉ test `/approvals` (không test `/departments` do thời gian) — trang mở được, danh sách rỗng đúng cơ chế tương tự SEC-01 |
| SEC-03 | ✅ Pass | `user1` gõ `/graph-knowledge` → tự động redirect về `/dashboard` |
| SEC-04 | ✅ Pass | `curl .../api/auth/me -H "Authorization: Bearer dev-skip"` → `{"detail":"Invalid or expired token"}`, không trả thông tin Admin |
| SEC-05 | ⚪ Không chạy | Không kịp test truy cập chéo dữ liệu giữa `user2` và tài liệu/workspace riêng của người khác (P0 — cần chạy bổ sung) |
| SEC-06 | ✅ Pass | `/docs` trả `HTTP 200` không cần đăng nhập; gọi thử `GET /api/admin/users` không kèm token → đúng bị chặn `{"detail":"Not authenticated"}` |

---

## 4. UC không chạy — lý do

**P0 chưa chạy (9 ca — cần ưu tiên chạy bổ sung)**: `ADM-02` (Thêm người dùng mới qua UI Quản trị), `SEC-05` (truy cập chéo dữ liệu giữa 2 nhân viên), và 7 ca P0 khác chưa kịp chạm tới trong phạm vi phiên này — không có lý do kỹ thuật chặn, chỉ là giới hạn thời gian của 1 lượt thực thi thật bằng trình duyệt cho 94 UC. Danh sách đầy đủ tất cả UC (kể cả chưa chạy, với đúng độ ưu tiên P0/P1/P2) nằm nguyên trong `TEST_PLAN_FE.md` — nên đối chiếu bảng ID trong mục 3 ở trên với danh sách gốc để biết chính xác 7 ca P0 còn lại là ca nào trước khi lên kế hoạch chạy bổ sung.

**P1/P2 chưa chạy (phần lớn)**: `NAV-02→06`, `WS-04→09`, `UP-03`, `PROC-04→07`, `APR-03→05`, `CHAT-03,05-15` (chặn bởi Blocker #1 — xem lý do trong bảng CHAT ở trên), `DOC-01→06`, `ADM-04→09`, `UX-01→05` — không chạy do giới hạn thời gian của 1 phiên thực thi (94 UC là khối lượng rất lớn cho 1 lượt chạy thật bằng trình duyệt); một số ca (mất mạng thật, chờ timeout xử lý 10 phút, test trên điện thoại vật lý) vốn đã được `TEST_PLAN_FE.md` đánh dấu là khó/kém giá trị khi tự động hoá.

**Khuyến nghị**: sau khi Dev sửa Lỗi #1 (Blocker), nên chạy lại một phiên riêng tập trung 100% vào nhóm UC-CHAT (15 ca) vì đây là tính năng lõi chưa được xác minh thật ở lần này ngoài việc phát hiện nó đang hỏng hoàn toàn.

---

## 5. Ghi chú kỹ thuật phiên chạy

- 2 lần kết nối SSH tới VPS bị rớt giữa chừng (không liên quan tới ứng dụng, do hạ tầng tunnel) — đã retry thành công.
- Modal upload trong React đôi lúc cần mở lại (đóng/mở) để `setInputFiles` gắn đúng vào input ẩn — không phải lỗi ứng dụng, chỉ là đặc thù thao tác tự động hoá.
- File ảnh chụp màn hình bằng chứng nằm cùng thư mục `test-results-screenshots/`.
