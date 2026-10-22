# TEST_RESULTS_FE_ROUND6.md — Kiểm chứng vòng 6

> Chạy lại vòng review bị treo trước đó. Thực thi thật bằng trình duyệt (ego-browser) trên
> **https://ctrl-seeking-bills-neural.trycloudflare.com** · Ngày chạy: 13/09/2026
> **Chế độ CHỈ ĐỌC** — không tải lên/xoá tài liệu, không đổi vai trò, không sửa mã nguồn, không commit.
> Mục tiêu: xác minh 4 lỗi R5-1→R5-4 đã sửa, cộng bộ regression (bfcache, phân quyền, chat).

---

## 1. Kết luận

### 🔴 CÒN BUG — 2 lỗi chưa đóng

| Lỗi | Mức | Trạng thái |
|---|---|---|
| **R5-1** — nút Build Communities gọi API 404, không báo lỗi | Trung bình | ❌ **Chưa sửa** — bản vá bị ghi đè, mất hoàn toàn |
| **R5-2 + AUTH-11** — tách trạng thái rỗng / lỗi mạng / hết phiên | Trung bình | ✅ **Đã đóng** |
| **R5-3** — hiện "NaN MB" | Thấp | ✅ **Đã đóng** |
| **R5-4** — sai thời gian hiển thị | Thấp | ⚠️ **Đóng một nửa** — còn sai ở khối *Nhật ký hoạt động* |

**Regression: không phát sinh.** bfcache, phân quyền, chat, đăng nhập đều Pass.
**Dữ liệu demo còn nguyên vẹn** — xem mục 5.

---

## 2. Danh sách lỗi cho Dev

### Lỗi #R6-1 — Bản vá "Build Communities" bị ghi đè, lỗi cũ quay lại nguyên vẹn
- **Mức độ**: Trung bình
- **UC liên quan**: ADM-09 (R5-1)
- **Bước tái hiện**:
  1. Đăng nhập `admin@micco.vn` → vào `/admin`.
  2. Kéo tới khối **AI Tools**, quan sát nút **Build Communities**.
  3. Bấm vào nút.
- **Kết quả hiện tại**: Nút **không** bị vô hiệu hoá (`disabled` = null, `aria-disabled` = null), **không có tooltip**, văn bản phụ vẫn là mô tả gốc *"Phân tích cộng đồng trong knowledge graph (Leiden algorithm + LLM summary)"*. Bấm vào **không hiện bất kỳ thông báo nào** — đúng y lỗi ban đầu.
- **Kết quả mong đợi**: nút bị vô hiệu hoá kèm tooltip giải thích, hoặc ít nhất hiện toast lỗi khi bấm.
- **Nguyên nhân gốc (đã truy được)**: **lost update do 2 agent sửa song song cùng một file.**
  `micco-frontend/src/pages/Admin.jsx` hiện chứa bản sửa trạng thái lỗi (`loadError`, 2 chỗ) nhưng **0 dấu vết** bản sửa Build Communities. Dấu thời gian file `16:34:06` trùng lượt ghi của agent sửa trạng thái lỗi (agent này kết thúc muộn hơn) → nó `scp` đè nguyên file, xoá sạch thay đổi của agent kia.
  Mã nguồn hiện tại (`Admin.jsx:179-191`) vẫn gọi thẳng `authFetch('/api/admin/communities/build', { method: 'POST' })` — endpoint đã xác nhận **không tồn tại** trong 91 route của OpenAPI.
- **File cần sửa**: `micco-frontend/src/pages/Admin.jsx` (hàm `handleBuildCommunities` ~dòng 179, nút JSX ~dòng 358-370).
- **Ghi chú quy trình**: cần tránh để 2 agent cùng ghi một file; hoặc sửa bằng patch/diff thay vì `scp` đè cả file.

### Lỗi #R6-2 — "Nhật ký hoạt động" hiển thị sai thời gian (lệch ~15 giờ)
- **Mức độ**: Thấp
- **UC liên quan**: DOC-02 (R5-4)
- **Bước tái hiện**:
  1. Mở chi tiết một tài liệu bất kỳ, VD `/documents/31`.
  2. So khối **Lịch sử phiên bản** với khối **Nhật ký hoạt động** — **cùng một sự kiện** (*"Admin Hệ Thống đã tải tài liệu này lên"*).
- **Kết quả hiện tại**: Lịch sử phiên bản báo **"27 phút trước"** (đúng), Nhật ký hoạt động báo **"14 giờ trước"** cho cùng sự kiện.
- **Kết quả mong đợi**: cả hai khối hiển thị cùng một mốc thời gian đúng.
- **Nguyên nhân gốc (đã truy được)**: **không phải lỗi múi giờ** — mà là **dùng nhầm trường dữ liệu**.
  `DocumentView.jsx:285` và `:292` dựng mục nhật ký bằng `time: doc?.date || doc?.created_at`.
  API `/api/documents/{id}` trả `"date": "2026-09-13"` — **chỉ có ngày, không có giờ** — và **không hề có trường `created_at`** (đã kiểm: `created_at` = không tồn tại). Nên nhánh dự phòng không bao giờ chạy được.
  `parseServerDate("2026-09-13")` → thêm `Z` → `2026-09-13T00:00:00Z` = nửa đêm UTC. So với thời điểm kiểm tra `14:57 UTC` → lệch **15,0 giờ** → render "14 giờ trước".
  Hàm `timeAgo`/`parseServerDate` trong `utils/formatters.js` **hoàn toàn đúng** (khối Lịch sử phiên bản dùng `v.created_at` nên hiển thị chuẩn).
- **Hướng sửa**: backend bổ sung `created_at` (có giờ) vào response chi tiết tài liệu, rồi frontend đổi thứ tự thành `doc?.created_at || doc?.date`. Chỉ đổi thứ tự ở frontend là **chưa đủ** vì trường đó hiện không tồn tại.
- **File**: `micco-frontend/src/pages/DocumentView.jsx:285,292` + response của `/api/documents/{id}` phía backend.

---

## 3. Chi tiết từng hạng mục đã kiểm

### R5-2 + AUTH-11 — ba trạng thái rỗng / lỗi mạng / hết phiên ✅

| Kiểm | Kết quả |
|---|---|
| Ngắt mạng → điều hướng nội bộ sang **Tài liệu** | ✅ Hiện **"Mất kết nối mạng. Vui lòng kiểm tra kết nối và thử lại."** + nút **Thử lại**; KHÔNG hiện "Không tìm thấy tài liệu" |
| Bật mạng → bấm **Thử lại** | ✅ Về đủ **17 tài liệu**, hết thông báo lỗi |
| Hết phiên giữa chừng (xoá `docvault_token` rồi điều hướng) | ✅ Bị đưa về `/login`, không lộ dữ liệu (`{"url":"/login","token":false,"loDuLieu":false}`) |
| **Đăng nhập sai mật khẩu 3 lần rồi đúng** | ✅ Cả 3 lần ở lại `/login` với banner **"Đăng nhập thất bại"** (tiếng Việt); lần đúng vào thẳng `/dashboard` — **không** kẹt vòng lặp đăng xuất |
| **Không bị đăng xuất oan** — dùng liên tục 7 bước bằng `user1` (Tài liệu → phân trang → Workspace → Tiến trình → Trợ lý AI → Tri thức → Tổng quan) | ✅ Giữ phiên suốt 7/7 bước |

> Ghi chú: thử tải lại trang **trong lúc đang offline** thì cả SPA không tải được (lỗi trình duyệt, không phải lỗi ứng dụng) — phải để app chạy rồi mới ngắt mạng và điều hướng nội bộ mới kiểm đúng được.

### R5-3 — "NaN MB" ✅ đã đóng

| Tài liệu | API báo | Giao diện hiện | NaN? |
|---|---|---|---|
| Báo cáo tổng kết… (PDF) | 48 KB | 48 KB (cả 3 vị trí) | Không |
| Quyết định thành lập Hội đồng… (DOCX) | 37 KB | 37 KB | Không |
| Định mức cấp phát… (TXT) | 2 KB | 2 KB | Không |

### R5-4 — thời gian hiển thị ⚠️ đóng một nửa

| Nơi hiển thị | Kết quả |
|---|---|
| Lịch sử phiên bản (chi tiết tài liệu) | ✅ "27 phút trước" — đúng |
| **Nhật ký hoạt động (chi tiết tài liệu)** | ❌ **"14 giờ trước"** cho cùng sự kiện — xem lỗi #R6-2 |
| Quản trị → Lịch sử hệ thống | ✅ "24 phút trước" — đúng |
| Quản trị → Người dùng | ✅ "1 ngày trước" — đúng |
| Chat (dấu thời gian tin nhắn) | ✅ 22:05 / 22:06 — đúng giờ địa phương |
| Tiến trình, Tổng quan | Không hiển thị thời gian tương đối |

### R5-1 — Build Communities ❌ chưa sửa
Xem lỗi #R6-1. Ảnh: `BUG-R5-1-build-communities.png`.

---

## 4. Regression — tất cả Pass

### bfcache sau đăng xuất (regression nghiêm trọng nhất)

| Trang | Sau đăng xuất | Sau khi bấm Back | Token | Lộ dữ liệu |
|---|---|---|---|---|
| `/dashboard` | `/login` | `/login` | false | **Không** |
| `/admin` | `/login` | `/login` | false | **Không** |
| `/departments` | `/login` | `/login` | false | **Không** |
| `/approvals` | `/login` | `/login` | false | **Không** |
| `/graph-knowledge` | `/login` | `/login` | false | **Không** |

Nội dung sau khi Back ở cả 5 trang đều là màn hình đăng nhập (*"Đăng nhập — Chào mừng trở lại!…"*).

### Phân quyền — `user1` (Nhân viên) gõ thẳng URL

| URL | Kết thúc ở | Bị chặn | Còn phiên |
|---|---|---|---|
| `/admin` | `/dashboard` | ✅ | ✅ |
| `/departments` | `/dashboard` | ✅ | ✅ |
| `/approvals` | `/dashboard` | ✅ | ✅ |
| `/graph-knowledge` | `/dashboard` | ✅ | ✅ |

### Chat (CHAT-01) ✅
- `Khoảng cách an toàn tối thiểu khi nổ mìn là bao nhiêu mét?` → **"…là 300 mét[iauc]."** + **"Tìm thấy 1 nguồn"** + trích dẫn 4 ký tự.
- `Giá cổ phiếu MICCO hôm nay là bao nhiêu?` → **"Tài liệu không chứa thông tin về giá cổ phiếu MICCO hôm nay."** — từ chối đúng, không bịa.

### Kho tài liệu ✅
**17 tài liệu**, phân trang **"Hiển thị 1 đến 5 trong số 17 tài liệu" / "Trang 1 / 4"**, toàn bộ tên tiếng Việt có dấu, không tài liệu nào ở trạng thái lỗi, không có "NaN".

---

## 5. Xác nhận dữ liệu demo còn nguyên vẹn ✅

| Chỉ số | Trước khi kiểm | Sau khi kiểm |
|---|---|---|
| Tài liệu | 17 | **17** |
| Workspace | 6 | **6** |
| Người dùng | 4 | **4** |
| Trạng thái tài liệu | 17 INDEXED | **17 INDEXED** |
| Vai trò người dùng | admin=Admin, user1–3=Nhân viên | **không đổi** |

Không tạo thêm, không xoá, không đổi vai trò, không sửa mã nguồn, không commit.

**Một tác dụng phụ nhỏ cần biết trước khi quay video**: vòng kiểm này có đặt **2 câu hỏi chat** trong workspace *KB Ban Giám đốc* (về khoảng cách nổ mìn và giá cổ phiếu). Chúng nằm lại trong lịch sử chat và trong *Quản trị → Lịch sử hệ thống*. Nếu muốn khung chat sạch khi quay, bấm biểu tượng thùng rác → **Xóa lịch sử** trước khi ghi hình.

---

## 6. Phát hiện thêm (không phải lỗi — có lợi cho video demo)

Câu hỏi gợi ý trong Trợ lý AI **đã sinh đúng theo nội dung tài liệu thật**, không còn là 4 câu chung chung kiểu *"Phân tích rủi ro & cơ hội?"*. Với workspace *KB Ban Giám đốc*, hệ thống gợi ý:

1. "Lịch huấn luyện an toàn năm 2026 gồm những đợt nào?"
2. "Nội dung huấn luyện an toàn bao gồm gì?"
3. "Ai là đối tượng tham gia huấn luyện an toàn?"
4. "Tiêu chí và hình thức sát hạch an toàn ra sao?"

→ Cảnh 5 của kịch bản demo **có thể bấm thẳng vào câu hỏi gợi ý** thay vì phải gõ tay, và lưu ý trong kịch bản về "câu hỏi mẫu chung chung" giờ **không còn đúng nữa**.

---

## 7. Ảnh bằng chứng

Lưu tại `/home/micco/test-evidence/round6/`:
- `BUG-R5-1-build-communities.png` — nút vẫn bấm được, không tooltip
- `BUG-R5-4-nhat-ky-hoat-dong.png` — "27 phút trước" vs "14 giờ trước" cùng một trang
- `CHAT-01-pass.png` — chat trả lời 300 mét kèm nguồn
