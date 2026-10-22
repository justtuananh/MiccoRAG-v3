# TEST_PLAN_FE.md — Kế hoạch kiểm thử giao diện MiccoRAG-v3

> Tài liệu kiểm thử thủ công trên trình duyệt cho frontend MiccoRAG-v3.
> Phiên bản: 2026-09-12 · Người soạn: đội vận hành · Xem thêm: [`README.md`](README.md) · [`OPERATIONS.md`](OPERATIONS.md)

---

## 1. Phạm vi & môi trường

**Phạm vi**: toàn bộ chức năng người dùng chạm được trên giao diện web — xác thực, điều hướng, workspace, tải tài liệu, xử lý/lập chỉ mục, phê duyệt, hỏi đáp RAG, quản trị, phân quyền, trải nghiệm.
**Ngoài phạm vi**: kiểm thử hiệu năng/tải, kiểm thử API trực tiếp (trừ vài ca bảo mật), đánh giá chất lượng RAG bằng bộ golden (đã có `harness/eval`).

### 1.1 Địa chỉ truy cập

| Hạng mục | Giá trị |
|---|---|
| **URL kiểm thử (public)** | **https://ctrl-seeking-bills-neural.trycloudflare.com** |
| Giao diện | `/` (trang gốc → tự chuyển `/login`) |
| API | `/api/...` (cùng origin với giao diện) |
| Swagger | `/docs` |

⚠️ **URL là tunnel tạm thời (Cloudflare Quick Tunnel)**. Nếu tiến trình `cloudflared` hoặc VPS khởi động lại, URL sẽ đổi sang chuỗi ngẫu nhiên khác — xem [Phụ lục A](#phụ-lục-a--vận-hành-fe-khi-cần-khởi-động-lại) để lấy URL mới.

### 1.2 Sơ đồ luồng

```
Trình duyệt  →  cloudflared  →  nginx :8888  ┬─ /                → Vite dev :5174  (React 19)
                                             ├─ /api, /openapi.json → FastAPI :8001
                                             └─ /docs             → FastAPI :8001
                                                                     ├─ PostgreSQL :15435
                                                                     └─ ChromaDB   :8003
```

### 1.3 Cấu hình AI đang chạy (ảnh hưởng kết quả chat)

| Thành phần | Giá trị |
|---|---|
| LLM | OpenAI `gpt-4.1-mini` (qua cổng chung LiteLLM) |
| Embedding | OpenAI `text-embedding-3-large` (3072 chiều) |
| Rerank | Cohere `rerank-multilingual-v3.0` (qua LiteLLM) |
| Ngưỡng liên quan tối thiểu | `0.15` |
| Thời gian xử lý tối đa 1 tài liệu | 10 phút (quá hạn → `FAILED`) |

---

## 2. Tài khoản kiểm thử

| Email | Mật khẩu | Vai trò | Dùng cho |
|---|---|---|---|
| `admin@micco.vn` | `DTJaV2VDJIqMBf0XLr6V` | **Admin** | Toàn bộ nhóm UC, đặc biệt UC-ADM, UC-APR |
| `user1@micco.vn` | `User_Default_123!` | Nhân viên | UC phân quyền, luồng upload chờ duyệt |
| `user2@micco.vn` | `User_Default_123!` | Nhân viên | UC truy cập chéo (workspace/tài liệu người khác) |
| `user3@micco.vn` | `User_Default_123!` | Nhân viên | UC tài khoản "trắng" (chưa có quyền tài liệu nào) |

⚠️ **Bắt buộc đọc trước khi test**:
- Cả 4 tài khoản seed **chưa được gán phòng ban** (hệ thống có sẵn 6 phòng ban: Ban Giám đốc, Kinh doanh, Kế toán, Kỹ thuật, Nhân sự, Pháp chế — tất cả đang 0 người). Vì vậy **chạy `UC-ADM-03` trước** nhóm `UC-WS` để gán phòng ban cho `user1`/`user2`, nếu không các ca workspace cấp phòng ban sẽ luôn báo lỗi "không thuộc phòng ban nào".
- **Không đổi mật khẩu `admin@micco.vn`** khi chạy `UC-NAV-05`; dùng `user3` để test đổi mật khẩu, tránh làm sai lệch tài liệu này.

---

## 3. Dữ liệu kiểm thử

Bộ file mẫu đã được tạo sẵn trên VPS tại `/home/micco/test-data/`. **Tải về máy của người kiểm thử** (vì thao tác upload thực hiện từ trình duyệt):

```bash
scp -r micco@103.237.147.91:/home/micco/test-data ./micco-test-data
# mật khẩu SSH: hỏi quản trị hệ thống
```

### 3.1 File hợp lệ (good case) — có "mốc kiểm chứng" để đối chiếu câu trả lời chat

| File | Loại | Kích thước | Mốc kiểm chứng nhúng trong nội dung |
|---|---|---|---|
| `micco-bao-cao-noi-bo.pdf` | PDF | 49 KB | Số hiệu **MCC-2026-0147**; doanh thu quý III/2026 **152,3 tỷ đồng**; người đại diện **Nguyễn Văn Khánh**; kho **Bình Dương** 12.400 m²; MST 0101234567 |
| `micco-quy-che-nhan-su.docx` | DOCX | 37 KB | Phép năm **14 ngày**; thử việc **60 ngày**; phụ cấp ăn trưa **780.000 đồng/tháng**; phụ cấp xăng xe 1.200.000 đồng |
| `micco-ghi-chu-ky-thuat.md` | Markdown | 1 KB | Mã lỗi **E-5012** = hết hạn mức gọi LLM; cổng backend 8001, Chroma 8003 |
| `micco-bao-gia.txt` | TXT | 1 KB | Báo giá **BG-2026-0932**; tổng sau thuế **775.500.000 đồng**; hiệu lực **30 ngày**; bảo hành 24 tháng |

### 3.2 File lỗi (bad case)

| File | Kích thước | Kỳ vọng |
|---|---|---|
| `bang-luong.xlsx` | 5 KB | Bị từ chối `400` — **dù giao diện ghi XLSX hợp lệ** (xem [Known issues](#8-lỗi-đã-biết-trước-không-tính-là-bug-mới)) |
| `anh-minh-hoa.png` | 75 B | Bị từ chối `400` — tương tự |
| `goi-cai-dat.zip` | 170 B | Bị từ chối `400` — tương tự |
| `phan-mem.exe` | 1 KB | Bị từ chối `400` |
| `qua-lon.pdf` | **57,7 MB** | Bị từ chối `400 File too large. Max size: 50MB` |
| `rong.pdf` | **0 byte** | Upload qua được → chết ở bước xử lý → `FAILED` |
| `hong.pdf` | 4 KB | Upload qua được (header PDF + rác) → `FAILED` kèm thông báo lỗi |
| `Tài liệu nội bộ - Phòng Kế toán ... đã duyệt.pdf` | 45 KB | Tên dài + dấu tiếng Việt + khoảng trắng → không vỡ giao diện, tải lại được |

**Ràng buộc thật của server**: chỉ nhận `.pdf` `.txt` `.md` `.docx` `.pptx`, tối đa **50 MB**/file.

---

## 4. Quy ước

- **ID**: `UC-<NHÓM>-<số>`. **Loại**: ✅ good case · ❌ bad case.
- **Ưu tiên**: `P0` = chặn phát hành (phải Pass) · `P1` = quan trọng · `P2` = nên có.
- Ghi kết quả vào [mục 7](#7-bảng-ghi-kết-quả). Khi Fail: chụp màn hình + mở DevTools → tab Console/Network chép lại mã lỗi và `detail`.
- Chuỗi thông báo in `đậm` hoặc `code` trong cột Kỳ vọng là **chuỗi thật lấy từ mã nguồn** — sai khác chữ nghĩa cũng tính là Fail.

### Thứ tự chạy khuyến nghị (luồng đầu–cuối)

```
UC-AUTH-01 → UC-ADM-03 (gán phòng ban) → UC-WS-01 → UC-UP-01..03 (4 file tốt)
   → UC-PROC-01 (chờ indexed) → UC-CHAT-01..08 (chat thật) → UC-UP-05..12 (file lỗi)
   → UC-AUTH-02 + UC-UP-04 (nhân viên) → UC-APR-01..03 (duyệt) → UC-ADM-* → UC-SEC-* → UC-UX-*
```

---

## 5. Danh sách use case

### 5.1 UC-AUTH — Xác thực (13 ca)

| ID | Mục tiêu | Các bước chính | Kỳ vọng | Loại | P |
|---|---|---|---|---|---|
| AUTH-01 | Đăng nhập Admin | Mở URL → nhập `admin@micco.vn` / `DTJaV2VDJIqMBf0XLr6V` → **Đăng nhập** | Vào `/dashboard`; sidebar có đủ **Phê duyệt**, **Quản trị**, **Đồ thị tri thức**; `localStorage.docvault_token` có giá trị | ✅ | P0 |
| AUTH-02 | Đăng nhập Nhân viên | Đăng nhập `user1@micco.vn` / `User_Default_123!` | Vào `/dashboard`; **không** thấy Phê duyệt / Quản trị / Đồ thị tri thức | ✅ | P0 |
| AUTH-03 | Sai mật khẩu | Đăng nhập admin với mật khẩu `sai123456` | Banner đỏ **"Đăng nhập thất bại"**; API trả `401 Invalid email or password`; không vào được hệ thống | ❌ | P0 |
| AUTH-04 | Email không tồn tại | Đăng nhập `khongtontai@micco.vn` | Cùng thông báo như AUTH-03 (không tiết lộ email có tồn tại hay không) | ❌ | P1 |
| AUTH-05 | Bỏ trống trường | Bấm Đăng nhập khi chưa nhập gì | Trình duyệt chặn (thuộc tính `required`), không gửi request | ❌ | P2 |
| AUTH-06 | Hiện/ẩn mật khẩu | Bấm **HIỆN** rồi **ẨN** | Mật khẩu chuyển giữa dạng chấm và chữ rõ | ✅ | P2 |
| AUTH-07 | Đăng ký hợp lệ | Sang tab Đăng ký → Họ tên `Nguyễn Test`, email mới, phòng ban **Kỹ thuật**, mật khẩu ≥6 ký tự, tick điều khoản | Tạo tài khoản và vào hệ thống với vai trò **Nhân viên** | ✅ | P1 |
| AUTH-08 | Đăng ký — validate | Lần lượt: tên 1 ký tự · không chọn phòng ban · mật khẩu `123` · xác nhận lệch | Lần lượt: **"Tên phải có ít nhất 2 ký tự"** · **"Vui lòng chọn phòng ban"** · **"Mật khẩu phải có ít nhất 6 ký tự"** · **"Mật khẩu không khớp"** | ❌ | P1 |
| AUTH-09 | Đăng ký trùng email | Đăng ký lại bằng `admin@micco.vn` | **"Email đã được sử dụng. Vui lòng đăng nhập hoặc dùng email khác."** | ❌ | P1 |
| AUTH-10 | Token hỏng | DevTools → Application → sửa `docvault_token` thành `abc` → F5 | Bị đưa về `/login`, token bị xoá khỏi localStorage | ❌ | P0 |
| AUTH-11 | Token mất giữa phiên | Xoá `docvault_token` **không F5** → bấm sang trang Tài liệu | Ghi nhận hành vi thật. *Lưu ý: hệ thống không có interceptor 401 toàn cục → nhiều khả năng hiện danh sách rỗng/lỗi thay vì đá về login (xem Known issues)* | ❌ | P1 |
| AUTH-12 | Đã đăng nhập vào `/login` | Đang đăng nhập → gõ `/login` trên thanh địa chỉ | Tự chuyển về `/dashboard` | ✅ | P2 |
| AUTH-13 | Đăng xuất | Avatar → **Đăng xuất** → bấm nút Back của trình duyệt | Về `/login`, token bị xoá, Back không vào lại được `/dashboard` | ✅ | P0 |

### 5.2 UC-NAV — Điều hướng & hồ sơ (6 ca)

| ID | Mục tiêu | Các bước chính | Kỳ vọng | Loại | P |
|---|---|---|---|---|---|
| NAV-01 | Menu theo vai trò | So sánh sidebar giữa `admin` và `user1` | Cả hai có: Tổng quan, Tài liệu, Tiến trình, Trợ lý AI, Chuyên gia, Tri thức, Workspace. Chỉ admin có thêm Phê duyệt / Quản trị / Đồ thị tri thức | ✅ | P0 |
| NAV-02 | Giao diện sáng/tối | Bấm nút chuyển chế độ → F5 | Đổi màu toàn trang; sau F5 giữ nguyên lựa chọn | ✅ | P2 |
| NAV-03 | Chuông thông báo | Bấm biểu tượng chuông | Admin → sang `/approvals`; Nhân viên → về `/dashboard` | ✅ | P2 |
| NAV-04 | Sửa hồ sơ | Avatar → **Thông tin cá nhân** → đổi Họ và tên → Lưu | Tên hiển thị trên topbar đổi ngay; F5 vẫn giữ; trường Phòng ban ở chế độ chỉ đọc | ✅ | P1 |
| NAV-05 | Đổi mật khẩu | Đăng nhập **`user3`** → Thông tin cá nhân → nhập mật khẩu mới → Lưu → Đăng xuất → đăng nhập lại bằng mật khẩu mới | Đăng nhập mật khẩu mới thành công, mật khẩu cũ bị từ chối | ✅ | P1 |
| NAV-06 | Deep-link + F5 | Gõ thẳng `/documents` khi đã đăng nhập → F5 | Ở đúng trang Tài liệu, không bị đá về login | ✅ | P1 |

### 5.3 UC-WS — Workspace (9 ca)

> Chạy sau `UC-ADM-03` (gán phòng ban cho user1/user2).

| ID | Mục tiêu | Các bước chính | Kỳ vọng | Loại | P |
|---|---|---|---|---|---|
| WS-01 | Admin tạo workspace cá nhân | `/workspaces` → Tạo mới → tên `WS Kiểm thử`, loại **Cá nhân** | Toast **"Đã tạo workspace mới!"**; workspace xuất hiện trong danh sách | ✅ | P0 |
| WS-02 | Admin tạo workspace công khai | Tạo workspace loại **Công khai** | Tạo thành công | ✅ | P1 |
| WS-03 | Nhân viên tạo workspace công khai | Đăng nhập `user1` → tạo loại **Công khai** | Bị chặn: giao diện báo **"Bạn không có quyền tạo loại này"** hoặc API trả `403` **"Chỉ Admin mới được tạo workspace công khai"** | ❌ | P0 |
| WS-04 | Nhân viên tạo workspace phòng ban | `user1` → tạo loại **Phòng ban** | `403` **"Chỉ Admin hoặc Trưởng phòng mới được tạo workspace phòng ban"**; nếu user chưa có phòng ban → `400` **"Bạn không thuộc phòng ban nào để tạo workspace phòng ban"** | ❌ | P1 |
| WS-05 | Sửa workspace | Admin sửa tên workspace vừa tạo | Toast **"Đã cập nhật workspace!"** | ✅ | P1 |
| WS-06 | Xoá workspace | Admin xoá một workspace rỗng | Toast **"Đã xóa workspace!"**; biến mất khỏi danh sách | ✅ | P1 |
| WS-07 | Truy cập workspace người khác | `user2` cố mở workspace cá nhân của admin (chọn trong Trợ lý AI hoặc gọi thẳng API) | `403` **"Bạn không có quyền truy cập workspace này"** | ❌ | P0 |
| WS-08 | Tên workspace rỗng | Tạo workspace để trống tên | Bị chặn (giao diện hoặc `422` từ server) | ❌ | P2 |
| WS-09 | Bộ lọc | Bấm lần lượt **Tất cả / Cá nhân / Phòng ban / Công khai** | Danh sách lọc đúng theo từng loại | ✅ | P2 |

### 5.4 UC-UP — Tải tài liệu lên (13 ca)

| ID | Mục tiêu | Các bước chính | Kỳ vọng | Loại | P |
|---|---|---|---|---|---|
| UP-01 | Upload PDF (kéo-thả) | Admin → `/documents` → **Tải lên** → kéo-thả `micco-bao-cao-noi-bo.pdf` → xác nhận | Toast **"Tải lên 1 tài liệu thành công"**; tài liệu vào danh sách ở trạng thái chờ xử lý | ✅ | P0 |
| UP-02 | Upload nhiều file | Chọn cùng lúc `micco-quy-che-nhan-su.docx`, `micco-ghi-chu-ky-thuat.md`, `micco-bao-gia.txt` | Cả 3 file lên thành công, đếm đúng số lượng trong toast | ✅ | P0 |
| UP-03 | Metadata khi upload | Upload kèm: chọn **Danh mục**, quyền xem **Nội bộ**, nhập 2 thẻ (Enter/dấu phẩy), chọn ảnh đại diện | Lưu đúng danh mục/quyền xem/thẻ; ảnh đại diện hiển thị ở chế độ lưới | ✅ | P1 |
| UP-04 | Nhân viên upload → chờ duyệt | `user1` upload `micco-bao-gia.txt` | Thông báo **"Tải lên thành công! Đang chờ phê duyệt."**; tài liệu ở trạng thái chờ duyệt | ✅ | P0 |
| UP-05 | File XLSX | Upload `bang-luong.xlsx` | `400` **"File type .xlsx not allowed. Allowed: ..."** — **mâu thuẫn với dòng gợi ý trên giao diện** ("PDF, DOCX, XLSX, PPTX, PNG, JPG, MD, ZIP"). Ghi nhận theo Known issues | ❌ | P0 |
| UP-06 | File PNG | Upload `anh-minh-hoa.png` | `400` từ chối (tương tự UP-05) | ❌ | P1 |
| UP-07 | File ZIP | Upload `goi-cai-dat.zip` | `400` từ chối (tương tự UP-05) | ❌ | P1 |
| UP-08 | File thực thi | Upload `phan-mem.exe` | `400` từ chối; không có file nào được lưu lên server | ❌ | P0 |
| UP-09 | File quá lớn | Upload `qua-lon.pdf` (57,7 MB) | `400` **"File too large. Max size: 50MB"**; giao diện hiện lỗi rõ ràng, không treo | ❌ | P0 |
| UP-10 | File rỗng 0 byte | Upload `rong.pdf` | Upload **qua được**; sau khi xử lý → trạng thái **FAILED** kèm thông báo lỗi | ❌ | P1 |
| UP-11 | File hỏng | Upload `hong.pdf` | Upload qua được → **FAILED**, hiển thị `error_message` từ bộ bóc tách | ❌ | P1 |
| UP-12 | Tên file dài có dấu | Upload file `Tài liệu nội bộ - Phòng Kế toán ... đã duyệt.pdf` | Upload được; tên hiển thị không vỡ layout (cắt bớt/xuống dòng gọn); tải lại đúng file | ❌ | P2 |
| UP-13 | Không chọn file | Mở hộp thoại upload rồi bấm xác nhận khi chưa chọn gì | Bị chặn, không gửi request rỗng | ❌ | P2 |

### 5.5 UC-PROC — Xử lý & lập chỉ mục (7 ca)

| ID | Mục tiêu | Các bước chính | Kỳ vọng | Loại | P |
|---|---|---|---|---|---|
| PROC-01 | Chuỗi trạng thái | Sau UP-01, ở lại trang Tài liệu quan sát | Trạng thái chạy `chờ xử lý → bóc tách → lập chỉ mục → hoàn tất`; thanh tiến trình cập nhật (poll 3 giây) | ✅ | P0 |
| PROC-02 | Thông báo hoàn tất | Chờ tới khi tài liệu xong | Toast **`✅ "<tên file>" đã xử lý xong và sẵn sàng sử dụng!`** | ✅ | P1 |
| PROC-03 | Thông báo thất bại | Theo dõi `rong.pdf` / `hong.pdf` (UP-10/11) | Toast **`❌ "<tên file>" xử lý thất bại. Vui lòng thử lại.`**; trạng thái FAILED + lý do hiển thị trên thẻ tài liệu | ❌ | P1 |
| PROC-04 | Chạy lại sau lỗi | Bấm **Analyze/Xử lý lại** trên tài liệu FAILED | Quay lại trạng thái đang xử lý, không báo lỗi ngay | ✅ | P1 |
| PROC-05 | Bấm xử lý 2 lần | Bấm Analyze liên tiếp 2 lần trên cùng tài liệu | Lần 2 trả `409` **"Document is already being analyzed"**, giao diện không hỏng | ❌ | P2 |
| PROC-06 | Trang Tiến trình | Mở `/processing-status` | Liệt kê đúng hàng đợi và trạng thái hiện tại của từng tài liệu | ✅ | P1 |
| PROC-07 | Quá thời gian xử lý | Quan sát tài liệu nào bị treo > 10 phút (nếu có) | Tự chuyển **FAILED** với lý do **"Processing timeout (10min). Click Analyze to retry."** | ❌ | P2 |

### 5.6 UC-APR — Phê duyệt tài liệu (5 ca)

| ID | Mục tiêu | Các bước chính | Kỳ vọng | Loại | P |
|---|---|---|---|---|---|
| APR-01 | Nhận thông báo chờ duyệt | Sau UP-04, đăng nhập admin ở tab khác và chờ ≤15 giây | Menu **Phê duyệt** hiện badge đếm; xuất hiện toast **"Yêu cầu phê duyệt mới!"** | ✅ | P0 |
| APR-02 | Duyệt tài liệu | `/approvals` → **Phê duyệt** tài liệu của user1 | Tài liệu chuyển sang đã duyệt; `user1` nhìn thấy và dùng được tài liệu | ✅ | P0 |
| APR-03 | Từ chối kèm lý do | Bấm **Từ chối** → nhập lý do → xác nhận | Trạng thái chuyển từ chối; lý do hiển thị lại đúng nội dung đã nhập | ✅ | P1 |
| APR-04 | Nhân viên vào trang duyệt | `user1` gõ thẳng `/approvals` | Không thao tác được: API trả `403` **"Permission denied"**. *Lưu ý: route không bị chặn ở tầng giao diện — xem Known issues* | ❌ | P0 |
| APR-05 | Tài liệu chưa duyệt bị chặn | `user2` cố mở tài liệu đang chờ duyệt của `user1` | `403` **"Document chưa được phê duyệt"** | ❌ | P1 |

### 5.7 UC-CHAT — Hỏi đáp RAG thật (15 ca)

> Tiền đề: 4 file good case đã ở trạng thái **hoàn tất (indexed)** và nằm trong workspace đang chọn.

| ID | Câu hỏi / thao tác | Kỳ vọng | Loại | P |
|---|---|---|---|---|
| CHAT-01 | "Doanh thu quý III năm 2026 là bao nhiêu?" | Trả lời nêu đúng **152,3 tỷ đồng**, kèm ít nhất 1 trích dẫn nguồn | ✅ | P0 |
| CHAT-02 | "Người đại diện theo pháp luật của công ty là ai?" | Trả lời **Nguyễn Văn Khánh** (Tổng giám đốc) | ✅ | P0 |
| CHAT-03 | "Số hiệu văn bản của báo cáo quý III là gì?" | Trả lời **MCC-2026-0147** | ✅ | P0 |
| CHAT-04 | "Nhân viên được nghỉ phép bao nhiêu ngày một năm?" | Trả lời **14 ngày** (nguồn: quy chế nhân sự DOCX) | ✅ | P0 |
| CHAT-05 | "Phụ cấp ăn trưa là bao nhiêu?" | Trả lời **780.000 đồng/tháng** | ✅ | P0 |
| CHAT-06 | "Mã lỗi E-5012 nghĩa là gì?" | Trả lời: hết hạn mức gọi mô hình ngôn ngữ (nguồn: file `.md`) | ✅ | P1 |
| CHAT-07 | "Báo giá BG-2026-0932 có hiệu lực bao lâu?" | Trả lời **30 ngày** (nguồn: file `.txt`) | ✅ | P1 |
| CHAT-08 | Kiểm tra trích dẫn | Câu trả lời có mã trích dẫn dạng `[a3x9]` (4 ký tự); bấm vào nguồn → mở đúng tài liệu tương ứng | ✅ | P0 |
| CHAT-09 | Quan sát luồng phát trực tiếp | Chữ hiện dần theo luồng (streaming), có trạng thái trung gian; không phải chờ trắng rồi hiện 1 lần | ✅ | P1 |
| CHAT-10 | Hỏi ngoài phạm vi: "Giá vàng SJC hôm nay bao nhiêu?" | Trả về đúng câu từ chối: **"Dựa trên các tài liệu hiện có trong hệ thống, tôi không tìm thấy thông tin cụ thể về câu hỏi của bạn..."** — tuyệt đối **không được bịa số liệu** | ❌ | P0 |
| CHAT-11 | Hỏi sai lệch có chủ đích: "Doanh thu quý III là 999 tỷ đúng không?" | Model phải đính chính theo tài liệu (152,3 tỷ), không đồng ý theo câu hỏi | ❌ | P0 |
| CHAT-12 | Chế độ truy vấn (Admin) | Admin đổi lần lượt **Hybrid / Vector only / Graph only** rồi hỏi lại CHAT-01 | Cả 3 chế độ đều trả lời được; ghi nhận khác biệt về nguồn/tốc độ. Tài khoản Nhân viên **không thấy** ô chọn chế độ | ✅ | P1 |
| CHAT-13 | Lịch sử hội thoại | F5 giữa cuộc trò chuyện → sau đó bấm xoá lịch sử → chọn **Có** | Sau F5 lịch sử còn nguyên; sau khi xoá thì sạch và không quay lại sau F5 | ✅ | P1 |
| CHAT-14 | Tài khoản chưa có quyền tài liệu | Đăng nhập `user3` (chưa được cấp tài liệu nào) → đặt câu hỏi bất kỳ | Trả về **"Bạn chưa có quyền truy cập vào tài liệu nào để đặt câu hỏi."** | ❌ | P1 |
| CHAT-15 | Tin nhắn quá dài | Dán ~6.000 ký tự vào ô chat rồi gửi | Bị chặn với lỗi xác thực dữ liệu (`422`), giao diện không treo | ❌ | P1 |

### 5.8 UC-DOC — Quản lý tài liệu (6 ca)

| ID | Mục tiêu | Các bước chính | Kỳ vọng | Loại | P |
|---|---|---|---|---|---|
| DOC-01 | Tìm kiếm & đổi kiểu hiển thị | Gõ "báo cáo" vào ô tìm kiếm; đổi giữa dạng bảng và dạng lưới | Lọc đúng kết quả; hai chế độ hiển thị đều đúng dữ liệu | ✅ | P1 |
| DOC-02 | Xem chi tiết | Bấm vào tài liệu → mở `/documents/:id` | Hiện thông tin và bản xem trước của tài liệu | ✅ | P1 |
| DOC-03 | Tải bản gốc | Bấm tải xuống | File tải về mở được, đúng nội dung ban đầu | ✅ | P1 |
| DOC-04 | Tải phiên bản mới | Trong màn chi tiết → tải lên phiên bản mới kèm ghi chú thay đổi | Danh sách phiên bản tăng thêm 1; tải được đúng từng phiên bản cũ/mới | ✅ | P1 |
| DOC-05 | Xoá tài liệu của người khác | `user2` cố xoá tài liệu do `user1` tải lên | `403` **"Không có quyền xóa tài liệu này"** | ❌ | P1 |
| DOC-06 | Trạng thái rỗng | Tìm kiếm từ khoá vô nghĩa `zzzqqq` | Hiện **"Không tìm thấy tài liệu"**, không lỗi trắng trang | ✅ | P2 |

### 5.9 UC-ADM — Quản trị (9 ca)

| ID | Mục tiêu | Các bước chính | Kỳ vọng | Loại | P |
|---|---|---|---|---|---|
| ADM-01 | Bảng điều khiển | Mở `/dashboard` sau khi đã upload | Số liệu thống kê khớp thực tế (tổng tài liệu, trạng thái, biểu đồ theo thời gian) | ✅ | P1 |
| ADM-02 | Thêm người dùng | `/admin` → tab **Người dùng** → Thêm mới | Toast **"Thêm ... thành công"**; user mới đăng nhập được | ✅ | P0 |
| ADM-03 | Gán phòng ban *(bước chuẩn bị)* | Sửa `user1` → phòng **Kỹ thuật**; `user2` → phòng **Nhân sự** | Lưu thành công; phòng ban hiển thị đúng trong hồ sơ người dùng | ✅ | P0 |
| ADM-04 | Vai trò sai phòng ban | Gán vai trò **Giám đốc** cho user thuộc phòng Kỹ thuật | `400` **"Vai trò Giám đốc/Phó giám đốc chỉ áp dụng cho phòng Ban Giám đốc"** | ❌ | P1 |
| ADM-05 | Vai trò không hợp lệ | Gửi vai trò không nằm trong danh sách (sửa request bằng DevTools) | `400` **"Vai trò không hợp lệ"** | ❌ | P2 |
| ADM-06 | Xoá người dùng | Xoá tài khoản tạo ở ADM-02 | Toast **"Xóa người dùng thành công"**; tài khoản đó không đăng nhập được nữa | ✅ | P1 |
| ADM-07 | Quản lý phòng ban | Tab **Phòng ban** → thêm / sửa / xoá 1 phòng ban thử nghiệm | Thao tác thành công, danh sách cập nhật ngay | ✅ | P1 |
| ADM-08 | Nhật ký hệ thống | Tab **Lịch sử hệ thống** | Thấy các lượt chat vừa thực hiện ở UC-CHAT (câu hỏi, thời gian, người hỏi) | ✅ | P1 |
| ADM-09 | Đồ thị tri thức | Admin mở `/graph-knowledge`; thử nút **Build Communities** ở trang Quản trị | Đồ thị hiển thị thực thể/quan hệ từ tài liệu đã index; nút chạy không báo lỗi | ✅ | P2 |

### 5.10 UC-SEC — Phân quyền & bảo mật (6 ca)

| ID | Mục tiêu | Các bước chính | Kỳ vọng | Loại | P |
|---|---|---|---|---|---|
| SEC-01 | Nhân viên vào trang Quản trị | `user1` gõ thẳng `/admin` | **Rủi ro đã biết**: trang vẫn mở được (không có chặn ở router), nhưng API trả `403` **"Admin access required"** → dữ liệu rỗng. Ghi nhận và báo cáo | ❌ | P0 |
| SEC-02 | Nhân viên vào trang phòng ban / phê duyệt | `user1` gõ `/departments` và `/approvals` | Tương tự SEC-01 — chỉ chặn ở tầng API, không chặn ở tầng giao diện | ❌ | P1 |
| SEC-03 | Chặn trang đồ thị tri thức | `user1` gõ `/graph-knowledge` | Bị đẩy về `/dashboard` (chặn đúng ở tầng router) | ✅ | P0 |
| SEC-04 | Cửa hậu `dev-skip` đã vá | Chạy: `curl -s <URL>/api/auth/me -H "Authorization: Bearer dev-skip"` | Trả về `{"detail":"Invalid or expired token"}` — **không được** trả về thông tin Admin | ❌ | P0 |
| SEC-05 | Truy cập chéo dữ liệu | `user2` mở workspace/tài liệu riêng của admin | `403` với thông báo quyền tương ứng; không lộ nội dung | ❌ | P0 |
| SEC-06 | Swagger công khai | Mở `<URL>/docs` ở cửa sổ ẩn danh (chưa đăng nhập) | Trang Swagger hiển thị được → **ghi nhận rủi ro lộ cấu trúc API**; xác nhận mọi endpoint vẫn đòi token khi gọi thử | ❌ | P1 |

### 5.11 UC-UX — Trải nghiệm & ổn định (5 ca)

| ID | Mục tiêu | Các bước chính | Kỳ vọng | Loại | P |
|---|---|---|---|---|---|
| UX-01 | Hiển thị trên màn hình nhỏ | Thu cửa sổ còn ~400px hoặc mở bằng điện thoại | Layout không vỡ, menu thu gọn dùng được, không tràn ngang | ✅ | P1 |
| UX-02 | Trạng thái rỗng | Đăng nhập tài khoản mới hoàn toàn, xem các trang Tài liệu/Workspace/Trợ lý AI | Hiện thông báo rỗng thân thiện (vd. **"Chưa có workspace — tạo trong trang Tài liệu"**), không lỗi | ✅ | P2 |
| UX-03 | Thông báo tự tắt | Thực hiện một thao tác có toast | Toast tự biến mất sau ~3,5 giây (toast quan trọng ~6 giây) | ✅ | P2 |
| UX-04 | Mất mạng | DevTools → Network → Offline → thực hiện thao tác bất kỳ | Hiện lỗi dạng **"Lỗi kết nối: ..."**; không trắng trang, khôi phục được khi bật mạng lại | ❌ | P1 |
| UX-05 | Làm mới trang | F5 ở từng trang chính | Không mất phiên đăng nhập, không có lỗi đỏ nghiêm trọng trong Console | ✅ | P1 |

**Tổng: 94 use case** (P0: 33 · P1: 45 · P2: 16).

---

## 6. Ma trận bao phủ

| Chức năng | Nhóm UC | Admin | Nhân viên |
|---|---|---|---|
| Đăng nhập / đăng ký / phiên | UC-AUTH | ✔ | ✔ |
| Điều hướng, hồ sơ cá nhân | UC-NAV | ✔ | ✔ |
| Workspace & phân quyền workspace | UC-WS | ✔ | ✔ |
| Tải tài liệu (hợp lệ + lỗi) | UC-UP | ✔ | ✔ |
| Xử lý, lập chỉ mục, lỗi xử lý | UC-PROC | ✔ | — |
| Phê duyệt tài liệu | UC-APR | ✔ | ✔ |
| Hỏi đáp RAG (chat thật) | UC-CHAT | ✔ | ✔ |
| Quản lý tài liệu & phiên bản | UC-DOC | ✔ | ✔ |
| Quản trị người dùng / phòng ban / log | UC-ADM | ✔ | — |
| Phân quyền & bảo mật | UC-SEC | ✔ | ✔ |
| Trải nghiệm, ổn định | UC-UX | ✔ | ✔ |

---

## 7. Bảng ghi kết quả

| ID | Kết quả | Người test | Ngày | Ghi chú / mã lỗi |
|---|---|---|---|---|
| AUTH-01 … AUTH-13 | ☐ Pass ☐ Fail | | | |
| NAV-01 … NAV-06 | ☐ Pass ☐ Fail | | | |
| WS-01 … WS-09 | ☐ Pass ☐ Fail | | | |
| UP-01 … UP-13 | ☐ Pass ☐ Fail | | | |
| PROC-01 … PROC-07 | ☐ Pass ☐ Fail | | | |
| APR-01 … APR-05 | ☐ Pass ☐ Fail | | | |
| CHAT-01 … CHAT-15 | ☐ Pass ☐ Fail | | | |
| DOC-01 … DOC-06 | ☐ Pass ☐ Fail | | | |
| ADM-01 … ADM-09 | ☐ Pass ☐ Fail | | | |
| SEC-01 … SEC-06 | ☐ Pass ☐ Fail | | | |
| UX-01 … UX-05 | ☐ Pass ☐ Fail | | | |

> Khuyến nghị tách mỗi UC thành 1 dòng riêng khi chạy thật (sao chép bảng trên và giãn ra).

---

## 8. Lỗi đã biết trước (không tính là bug mới)

| # | Vấn đề | Ảnh hưởng tới UC |
|---|---|---|
| 1 | Giao diện ghi chấp nhận **"PDF, DOCX, XLSX, PPTX, PNG, JPG, MD, ZIP — Tối đa 50MB"** nhưng server chỉ nhận `.pdf .txt .md .docx .pptx` | UP-05, UP-06, UP-07 |
| 2 | Frontend **không kiểm tra file phía client** (cả loại lẫn dung lượng) → người dùng phải chờ tải lên xong mới biết lỗi | UP-05 → UP-09 |
| 3 | `/admin`, `/departments`, `/approvals` **chỉ ẩn khỏi menu, không chặn ở router** — chặn thật chỉ ở tầng API | SEC-01, SEC-02, APR-04 |
| 4 | Không có bộ chặn lỗi `401` toàn cục (chỉ kiểm tra lúc khởi động ứng dụng) → token hỏng giữa phiên có thể hiện dữ liệu rỗng thay vì đá về đăng nhập | AUTH-11 |
| 5 | Chế độ truy vấn ở màn chat (`hybrid`/`vector_only`/`graph_only`) **lệch** với chế độ cấu hình trong workspace (`naive`/`local`/`global`) | CHAT-12 |
| 6 | Backend có endpoint đổi ảnh đại diện nhưng **giao diện chưa nối** → ngoài phạm vi kiểm thử UI | — |
| 7 | Nút **"Quên mật khẩu?"** và **"Đăng nhập với Google"** chưa được đấu nối chức năng | AUTH-06 |
| 8 | Swagger `/docs` mở công khai qua URL tunnel | SEC-06 |
| 9 | URL tunnel là tạm thời, đổi sau mỗi lần khởi động lại `cloudflared`/VPS | Toàn bộ |

---

## 9. Tiêu chí kết thúc

- **Đạt**: 100% ca `P0` Pass; ≥90% ca `P1` Pass; không có lỗi làm mất/ sai lệch dữ liệu; không có lỗi cho phép vượt quyền ngoài các mục đã liệt kê ở phần 8.
- **Không đạt**: bất kỳ ca `P0` nào Fail, hoặc phát hiện lỗ hổng vượt quyền mới chưa có trong phần 8.
- Mọi phát hiện mới ngoài phần 8 phải được ghi lại kèm ảnh chụp màn hình, nội dung tab Network (mã lỗi + `detail`) và các bước tái hiện.

---

## Phụ lục A — Vận hành FE (khi cần khởi động lại)

Toàn bộ chạy dưới tài khoản `micco` trên VPS `103.237.147.91`. **Đây là máy dùng chung**: chỉ thao tác tiến trình/container của MiccoRAG (`nexusrag-*`, `micco-*`, uvicorn :8001, Vite :5174, `cloudflared`), tuyệt đối không đụng `supabase-*`, `airflow-*`, `metabase`, `data-platform-lab-*`, `mobiwork_*`.

| Thành phần | Lệnh | Ghi chú |
|---|---|---|
| Node.js cho FE | `export PATH=/home/micco/node22/bin:$PATH` | **Bắt buộc** — Vite 7 cần Node ≥20.19; Node 18 của apt sẽ lỗi `crypto.hash is not a function` |
| Chạy FE | `cd /home/micco/MiccoRAG-v3/micco-frontend && nohup npm run dev > /home/micco/frontend.log 2>&1 &` | Cổng 5174 |
| Chạy backend | `cd /home/micco/MiccoRAG-v3/micco-backend && source venv/bin/activate && cd backend && nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 > /home/micco/backend.log 2>&1 &` | Cổng 8001 |
| Cổng gateway | `cd /home/micco/MiccoRAG-v3/micco-backend && docker compose -f docker-compose.nginx.yml up -d nginx` | **Chỉ service `nginx`** — không bật `duckdns` (token bị lộ trong git) |
| Hạ tầng dữ liệu | `docker compose -f docker-compose.services.yml up -d` | Postgres 15435, ChromaDB 8003 |
| Tạo URL công khai | `cd /home/micco && nohup ./cloudflared tunnel --url http://localhost:8888 > cloudflared-gw.log 2>&1 &` | |
| Lấy URL mới | `grep -o "https://[a-zA-Z0-9.-]*trycloudflare.com" /home/micco/cloudflared-gw.log \| head -1` | Cập nhật lại mục 1.1 của tài liệu này |
| Tạo lại bộ file test | `/home/micco/.fixtures-venv/bin/python /home/micco/make_fixtures.py` | Ghi ra `/home/micco/test-data/` |

**Kiểm tra nhanh sau khi khởi động lại**:

```bash
curl -s <URL>/ | grep -o 'id="root"'          # giao diện
curl -s <URL>/api/auth/departments | head -c 80   # API
curl -s -o /dev/null -w "%{http_code}\n" <URL>/docs   # 200
```
