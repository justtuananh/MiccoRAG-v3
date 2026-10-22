# TEST_RESULTS_FE_ROUND2.md — Kiểm chứng sau khi sửa 8 lỗi

> Vòng 2: kiểm chứng bằng **trình duyệt thật** (ego-browser) + đối chiếu chéo qua API, trên
> **https://ctrl-seeking-bills-neural.trycloudflare.com**, theo `TEST_PLAN_FE.md`.
> Ngày chạy: 2026-09-12 · Tài khoản: `admin@micco.vn`, `user1@micco.vn`.
> Mọi dòng "Pass" đều có quan sát thật (ảnh chụp màn hình và/hoặc phản hồi API thật). Không có kết quả nào được suy đoán.

---

## 1. Bảng tổng hợp

| Hạng mục | Số lượng |
|---|---|
| UC đã chạy vòng này | **31** |
| ✅ Pass | **29** |
| ❌ Fail | **1** (CHAT-10 — lệch chuỗi, xem Lỗi mới N1) |
| ⚪ Không xác minh trọn vẹn | **1** (CHAT-09 — streaming) |
| Lỗi cũ đã đóng | **7/8** |
| Lỗi cũ không tái hiện | **1/8** (Lỗi #4) |
| Regression phát hiện | **0** |
| Lỗi mới phát hiện | **3** (đều mức Thấp/Thông tin) |

**Kết luận nhanh**: lỗi **Blocker đã được sửa dứt điểm** — chat RAG trả lời đúng nội dung tài liệu kèm trích dẫn ở cả 3 chế độ truy vấn. Toàn bộ nhóm CHAT (15 UC) lần đầu tiên được xác minh thật. Backend log **0 traceback / 0 ERROR** trong suốt phiên test.

---

## 2. Trạng thái 8 lỗi cũ

| # | Lỗi | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1 | **Blocker** — chat trả JSON tool-call thô | ✅ **ĐÃ ĐÓNG** | Hỏi "Doanh thu quý III năm 2026?" → *"Doanh thu quý III năm 2026 đạt 152,3 tỷ đồng, tăng 18,7%..."* kèm trích dẫn `[iccc]` + "Tìm thấy 3 nguồn". 12/12 câu hỏi đều trả lời đúng, không còn JSON thô |
| 2 | Cao — Back sau đăng xuất lộ dữ liệu (bfcache) | ✅ **ĐÃ ĐÓNG** | Đăng xuất → bấm Back → ở lại `/login`, `token=false`, không hiện "TỔNG TÀI LIỆU"/"admin@micco.vn" |
| 3 | Cao — workspace "Công khai" bị âm thầm hạ cấp | ✅ **ĐÃ ĐÓNG** | `user1` chọn được radio Công khai (`disabled:false`), submit → server trả `403 "Chỉ Admin mới được tạo workspace công khai"`, **không** tạo ra workspace private âm thầm; modal giữ nguyên |
| 4 | TB — danh sách Quản trị không refresh | ⚪ **KHÔNG TÁI HIỆN** | Gán phòng ban "Pháp chế" cho `user3` → bảng đổi **ngay lập tức** từ "Chưa phân" → "Pháp chế", không cần F5. Agent B đã điều tra và **không sửa code** (code FE vốn đã gọi `fetchUsers()` đúng). Nhiều khả năng quan sát vòng 1 là do đo quá sớm |
| 5 | TB — `.xlsx`/`.png` được nhận rồi mới FAILED | ✅ **ĐÃ ĐÓNG** | Chặn ngay khi chọn file, không lên danh sách chờ; server cũng trả `400 "Định dạng file không được hỗ trợ: .xlsx"` |
| 6 | Thấp — whitelist client mâu thuẫn | ✅ **ĐÃ ĐÓNG** | Hint = `PDF, TXT, DOCX, PPTX, MD — Tối đa 50MB`; `accept=".pdf,.txt,.md,.docx,.pptx"` — khớp chính xác `ALLOWED_EXTENSIONS` server |
| 7 | Thấp — lỗi đăng nhập tiếng Anh | ✅ **ĐÃ ĐÓNG** | Sai mật khẩu → banner **"Đăng nhập thất bại"** (không còn "Invalid email or password") |
| 8 | Thấp — toast thiếu "Đang chờ phê duyệt" | ✅ **ĐÃ ĐÓNG** | `user1` upload → **"Tải lên 1 tài liệu thành công! Đang chờ phê duyệt."** |

---

## 3. Lỗi mới & rủi ro cho Dev

### N1 — Câu từ chối của chat không đúng nguyên văn chuỗi quy định
- **Mức độ**: Thấp · **UC**: CHAT-10 (Fail theo quy tắc so khớp chuỗi)
- **Tái hiện**: đăng nhập admin → Trợ lý AI → workspace "WS Kiểm thử Cá nhân" → hỏi *"Giá vàng SJC hôm nay bao nhiêu?"*
- **Hiện tại**: `"Tài liệu không chứa thông tin về giá vàng SJC hôm nay."`
- **Mong đợi**: `"Dựa trên các tài liệu hiện có trong hệ thống, tôi không tìm thấy thông tin cụ thể về câu hỏi của bạn..."` (mục 5.7 `TEST_PLAN_FE.md`)
- **Tác động thật**: hành vi **đúng** (không bịa đặt), nhưng frontend nhận diện câu từ chối bằng `msg.content.includes(<chuỗi chính xác>)` để tô kiểu riêng → **kiểu hiển thị đặc biệt này không bao giờ kích hoạt**.
- **Khu vực**: `micco-backend/backend/app/api/chat_prompt.py` (chuỗi do prompt chỉ thị, `gpt-4.1-mini` diễn đạt lại) và `micco-frontend/src/components/chat/ChatMessage.jsx`. Nên đổi sang cờ dữ liệu (vd. `sources.length === 0`) thay vì so khớp chuỗi.

### N2 — Chat không nhớ workspace đang chọn sau khi F5
- **Mức độ**: Thấp · **UC**: CHAT-13 (vẫn Pass, nhưng phát sinh quan sát này)
- **Tái hiện**: chọn workspace "WS Kiểm thử Cá nhân" → chat vài câu → F5
- **Hiện tại**: quay về workspace mặc định ("KB Kỹ thuật") với màn hình rỗng; người dùng tưởng mất lịch sử. Chọn lại đúng workspace thì lịch sử còn nguyên.
- **Mong đợi**: giữ workspace đang chọn (localStorage/URL param).
- **Khu vực**: `micco-frontend/src/pages/ChatAssistant.jsx` (logic auto-select workspace).

### N3 — `/api/approvals/pending` trả 200 + rỗng thay vì 403
- **Mức độ**: Thông tin · **UC**: APR-04 (Pass về mặt an toàn dữ liệu)
- **Hiện tại**: `user1` (Nhân viên) gọi → `200 {"documents":[],"knowledge":[]}`
- **Mong đợi** (theo tài liệu): `403 "Permission denied"`
- **Đánh giá**: không rò rỉ dữ liệu nên không phải lỗ hổng, nhưng lệch tài liệu và khiến trang `/approvals` mở được với giao diện trống thay vì báo lỗi rõ ràng.

### R1 — ⚠️ Rủi ro trong bản vá Blocker (chưa bung ra khi test, cần Dev xem lại)
`app/services/llm/litellm_provider.py::_parse_fallback_tool_call()` kích hoạt khi **toàn bộ** text là JSON `{"name": ...}` — nhưng:
- **không kiểm tra `name` có phải tool hợp lệ** (`search_documents`);
- `arguments` là **tuỳ chọn** (`data.get("arguments", data.get("args", {}))` → thiếu vẫn cho qua).

Hệ quả: nếu người dùng hỏi *"trả lời cho tôi dạng JSON"* và model trả đúng một object như `{"name": "Nguyễn Văn Khánh"}`, nó sẽ **bị nuốt thành lệnh gọi tool giả** thay vì hiển thị câu trả lời. Xác suất thấp nhưng hậu quả khó hiểu cho người dùng.
**Khuyến nghị**: chỉ chấp nhận khi `name` nằm trong danh sách tool đã đăng ký, và bắt buộc `arguments` là dict không rỗng.

---

## 4. Chi tiết từng UC

### 4.1 Nhóm CHAT — 15 UC (lần đầu xác minh thật)

| ID | Câu hỏi / thao tác | KQ | Bằng chứng |
|---|---|---|---|
| CHAT-01 | "Doanh thu quý III năm 2026 là bao nhiêu?" | ✅ | *"...đạt **152,3 tỷ đồng**, tăng 18,7%..."* + `[iccc]` + "Tìm thấy 3 nguồn" |
| CHAT-02 | "Ai là người đại diện theo pháp luật?" | ✅ | *"...ông **Nguyễn Văn Khánh**, chức vụ Tổng giám đốc"* + `[b62c]` |
| CHAT-03 | "Số hiệu văn bản báo cáo quý III?" | ✅ | *"**MCC-2026-0147**. Ngày ban hành 30/09/2026"* + `[a2mv]` |
| CHAT-04 | "Nghỉ phép bao nhiêu ngày một năm?" | ✅ | *"...nghỉ phép năm **14 ngày**, hưởng nguyên lương..."* + `[bxt2]` |
| CHAT-05 | "Phụ cấp ăn trưa là bao nhiêu?" | ✅ | *"**780.000 đồng** mỗi tháng, chi trả cùng kỳ lương"* |
| CHAT-06 | "Mã lỗi E-5012 nghĩa là gì?" | ✅ | *"Hết hạn mức gọi mô hình ngôn ngữ"* + `[qh14]` |
| CHAT-07 | "Báo giá BG-2026-0932 hiệu lực bao lâu?" | ✅ | *"**30 ngày** kể từ ngày phát hành... đến hết 12/10/2026"* + `[a3x9][wok4]` |
| CHAT-08 | Trích dẫn + mở nguồn | ✅ | Mã trích dẫn 4 ký tự đúng chuẩn; mở panel nguồn: `[30ob] Tài liệu 1 ↳ 2. Kết quả kinh doanh`, `[7oz2] ↳ 3. Công nợ và dòng tiền`; bấm nguồn mở panel xem tài liệu đúng |
| CHAT-09 | Quan sát streaming | ⚪ | Câu trả lời **đúng** (kế hoạch quý IV: 175 tỷ, 15/11/2026, 20/12/2026, Trần Thị Mai Hương). Nhưng lấy mẫu mỗi 2,5s không bắt được nội dung tăng dần → **không dám kết luận** phần streaming trực quan |
| CHAT-10 | "Giá vàng SJC hôm nay?" | ❌ | Từ chối đúng bản chất nhưng **lệch chuỗi** — xem N1 |
| CHAT-11 | "Doanh thu quý III là 999 tỷ đúng không?" | ✅ | *"...là **152,3 tỷ đồng, không phải 999 tỷ đồng**"* + `[30ob]` — không hùa theo câu hỏi sai |
| CHAT-12 | 3 chế độ truy vấn (Admin) | ✅ | **Vector only** → "thử việc **60 ngày**" `[dkm8]`; **Graph only** → "ba kho: **Bình Dương** 12.400 m², Hải Phòng, Đà Nẵng" `[a2ozj]`; **Hybrid** → CHAT-01 |
| CHAT-13 | Lịch sử sau F5 | ✅ | Sau F5 + chọn lại workspace: lịch sử còn đủ (`152,3`, `Nguyễn Văn Khánh`, `60 ngày`) — kèm quan sát N2 |
| CHAT-14 | Tài khoản chưa có quyền tài liệu | ✅ | `user1` hỏi vào workspace riêng của admin → *"Bạn chưa có quyền truy cập vào tài liệu nào để đặt câu hỏi."* (test bằng `user1` thay vì `user3` — cùng điều kiện "không có quyền") |
| CHAT-15 | Tin nhắn 6.441 ký tự | ✅ | `422 "String should have at most 5000 characters"` |

### 4.2 Các UC ứng với 8 lỗi + P0 bổ sung

| ID | KQ | Bằng chứng |
|---|---|---|
| AUTH-03 | ✅ | Banner **"Đăng nhập thất bại"**, `token=false`, ở lại `/login` |
| AUTH-13 | ✅ | Sau đăng xuất, Back → `/login`, không lộ dữ liệu dashboard |
| WS-03 | ✅ | Radio Công khai chọn được; server `403 "Chỉ Admin mới được tạo workspace công khai"`; danh sách workspace **không** phát sinh bản private âm thầm |
| WS-07 | ✅ | `user1` → `GET /api/v1/workspaces/1` → `403 "Bạn không có quyền truy cập workspace này"` |
| UP-01/02 | ✅ | Admin upload `.txt` + `.md` → cả 2 vào danh sách (regression OK) |
| UP-04 | ✅ | `user1` upload → **"Tải lên 1 tài liệu thành công! Đang chờ phê duyệt."** |
| UP-05 | ✅ | `.xlsx` → *"Định dạng file không được hỗ trợ: bang-luong.xlsx. Chỉ chấp nhận PDF, TXT, DOCX, PPTX, MD — Tối đa 50MB."*, không lên danh sách chờ |
| UP-06 | ✅ | `.png` → chặn cùng cơ chế UP-05 |
| UP-07 | ✅ | `.zip` → vẫn bị chặn (regression OK) |
| UP-08 | ✅ | `.exe` → vẫn bị chặn (regression OK) |
| UP-09 | ✅ | `qua-lon.pdf` 57,7MB → submit → **"vượt quá giới hạn 50MB"** (regression OK) |
| ADM-02 | ✅ | Tạo `qa.round2@micco.vn` (Nhân viên/Kinh doanh) → hiện ngay trong bảng, "Tổng người dùng" 4 → 5 |
| ADM-03 | ✅ | Gán "Pháp chế" cho `user3` → bảng đổi ngay, **không cần F5** (lỗi #4 không tái hiện) |
| APR-04 | ✅ | `user1` mở `/approvals` → giao diện trống, không rò rỉ dữ liệu (kèm ghi nhận N3) |
| SEC-05 | ✅ | `user1` hỏi vào dữ liệu riêng của admin → *"Bạn chưa có quyền truy cập vào tài liệu nào..."*, `sources: []` |
| Regression đăng ký | ✅ | `POST /api/auth/register` email trùng → `400 "Email đã được sử dụng. Vui lòng đăng nhập hoặc dùng email khác."` — thông báo tiếng Việt của luồng đăng ký **không bị phá** bởi bản vá lỗi #7 |

---

## 5. Nhận xét chất lượng 2 bản vá

**Backend (Agent A)** — chất lượng tốt. `tool_calls_acc` là biến cục bộ trong `astream()` nên **không rò rỉ giữa các vòng lặp agentic**; gom `name` (chỉ có ở chunk đầu) + nối `arguments` rải rác là đúng chuẩn OpenAI streaming; `json.loads` bọc try/except không làm sập stream; helper `_get()` truy cập phòng thủ dict-or-object là hợp lý với LiteLLM. Điểm cần siết lại: **R1** ở trên.

**Frontend (Agent B)** — sạch, phạm vi hẹp, đúng trọng tâm. Đáng ghi nhận: khi điều tra lỗi #4 đã **không sửa mò** mà báo cáo trung thực là không tái hiện được — kiểm chứng vòng này xác nhận kết luận đó đúng. Lưu ý nhỏ: listener `pageshow` phụ thuộc `logout` trong mảng dependency — nếu `logout` không được `useCallback` trong `AuthContext` thì listener sẽ đăng ký lại mỗi lần render (không sai chức năng, chỉ hơi lãng phí).

**Còn tồn tại (không thuộc phạm vi lần sửa này)**: không có kiểm tra dung lượng phía client → file 57,7MB vẫn phải truyền hết lên mạng rồi mới bị server từ chối.

---

## 6. UC chưa chạy

Các UC P1/P2 còn lại (`NAV-02→06`, `WS-04/05/06/08/09`, `UP-03`, `PROC-02→07`, `APR-03/05`, `DOC-01→06`, `ADM-04→09`, `UX-01→05`) chưa chạy vòng này do phạm vi được giao là: 8 lỗi + trọn nhóm CHAT + 9 UC P0 còn thiếu. Sau vòng này **toàn bộ 33 UC P0 đã được chạy ít nhất một lần** (24 ở vòng 1 + 9 bổ sung ở vòng 2).
