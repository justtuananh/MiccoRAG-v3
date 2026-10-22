# TEST_RESULTS_FE_ROUND7.md — Kiểm chứng vòng 7 (rút gọn)

> Chạy thật bằng trình duyệt (ego-browser) trên **https://ctrl-seeking-bills-neural.trycloudflare.com**
> Ngày chạy: 13/09/2026 · Tài khoản: `admin@micco.vn`
> **Chế độ chỉ-đọc** — không tải lên, không xoá, không sửa dữ liệu, không đặt câu hỏi chat mới (hệ thống đang chứa dữ liệu demo phục vụ quay video).

## 1. Kết luận

### ✅ SẠCH — cả 2 lỗi đã đóng, không phát sinh lỗi mới

| Lỗi | Mức | Trạng thái |
|---|---|---|
| **R6-1** — nút "Build Communities" gọi API 404, nuốt lỗi | TB | ✅ **Đã đóng** |
| **R6-2** — "Nhật ký hoạt động" lệch ~15 giờ | Thấp | ✅ **Đã đóng** |

---

## 2. R6-1 — Nút "Build Communities"

**Bối cảnh**: bản vá này từng bị một agent khác `scp` đè cả file làm mất sạch (lost update), nay đã áp lại.

**Kết quả đọc trực tiếp từ DOM** (`Quản trị → AI Tools`):

```json
{
 "text": "Build Communities",
 "disabled": true,
 "title": "Backend chưa hỗ trợ tính năng này",
 "cursor": "not-allowed",
 "opacity": "0.6",
 "descriptionBlock": "Build Communities — Phân tích cộng đồng trong knowledge graph
                      (Leiden algorithm + LLM summary) — chưa khả dụng, backend chưa có endpoint"
}
```

| Kỳ vọng | Thực tế | Kết quả |
|---|---|---|
| Nút bị vô hiệu hoá, hiện mờ | `disabled: true`, `opacity: 0.6` | ✅ |
| Con trỏ báo không bấm được | `cursor: not-allowed` | ✅ |
| Tooltip giải thích | `"Backend chưa hỗ trợ tính năng này"` | ✅ |
| Dòng cảnh báo màu hổ phách | `"chưa khả dụng, backend chưa có endpoint"` | ✅ |
| Không phát sinh request tới API chết | **0 request** | ✅ |

**Kiểm tra mạng nghiêm ngặt**: thử bấm bằng **2 cách** — `button.click()` thông thường **và** ép `dispatchEvent(new MouseEvent("click"))` để vượt qua thuộc tính `disabled`. Đếm `performance.getEntriesByType("resource")` lọc theo `communities`: **0 trước và 0 sau khi bấm**. Không còn khả năng gọi `/api/admin/communities/build`.

Ảnh: `test-evidence/round7/r7-build-communities.png`

---

## 3. R6-2 — Thời gian trong "Nhật ký hoạt động"

**Nguyên nhân gốc đã sửa**: API chỉ trả `date: "2026-09-13"` (mất phần giờ) và **không có** `created_at` → frontend quy ra nửa đêm UTC. Nay backend (`api_compat/utils.py`) trả thêm `created_at` đầy đủ, frontend (`DocumentView.jsx`) ưu tiên dùng nó.

**Mốc đối chiếu**: tài liệu `id=31` có `created_at = 2026-09-13 14:28:03` (UTC); thời điểm kiểm ≈ `15:18` UTC → đúng ra phải hiện **~50 phút trước**.

| Tài liệu | Lịch sử phiên bản | Nhật ký hoạt động | Khớp nhau? | Kích thước |
|---|---|---|---|---|
| DOC-0031 *Báo cáo tổng kết công tác an toàn 9 tháng 2026.pdf* | 50 phút trước | **50 phút trước** | ✅ | 48 KB |
| DOC-0020 *Quy trình an toàn trong sản xuất vật liệu nổ công nghiệp.pdf* | 52 phút trước | **52 phút trước** | ✅ | 48 KB |
| DOC-0027 *Kế hoạch huấn luyện và sát hạch an toàn 2026.pdf* | 50 phút trước | **50 phút trước** | ✅ | 47 KB |

- Trước khi sửa: hai khối lệch nhau rõ rệt ("27 phút trước" vs "14 giờ trước").
- Sau khi sửa: **hai khối khớp tuyệt đối** trên cả 3 tài liệu, và khớp với giờ thật (chênh lệch đúng ~50 phút).
- Tiện thể xác nhận **R5-3 ("NaN MB") vẫn đóng**: kích thước hiển thị đúng `48 KB` / `47 KB`, không còn `NaN`.

Ảnh: `test-evidence/round7/r7-doc31-activity.png`

---

## 4. Kiểm tra không hỏng gì

| Hạng mục | Kết quả |
|---|---|
| Số tài liệu trong kho | **17**, hiển thị `"Hiển thị 1 đến 5 trong số 17 tài liệu"` |
| Phân trang | `Trang 1 / 4` — đúng 5 mục/trang | 
| Tên tài liệu | Tiếng Việt có dấu đầy đủ (VD *"Quyết định thành lập Hội đồng An toàn lao động.docx"*) |
| Tài liệu lỗi / `NaN` trên trang danh sách | **Không có** |
| Phiên đăng nhập | Hoạt động bình thường suốt phiên kiểm (điều hướng 6 trang, không bị đá ra) |

*Ghi chú*: không lặp lại kịch bản đăng xuất + bfcache vì **vòng 6 đã kiểm đủ 5/5 trang và Pass toàn bộ**; lặp lại chỉ tốn thời gian mà không thêm giá trị chẩn đoán.

Ảnh: `test-evidence/round7/r7-documents.png`

---

## 5. Xác nhận dữ liệu demo nguyên vẹn

Đếm trực tiếp trong cơ sở dữ liệu **sau khi kiểm xong**:

| Hạng mục | Baseline trước kiểm | Sau khi kiểm | Kết quả |
|---|---|---|---|
| Tài liệu | 17 | **17** | ✅ nguyên vẹn |
| Đã lập chỉ mục | 17 | **17** | ✅ |
| Workspace | 6 | **6** | ✅ |
| Người dùng | 4 | **4** | ✅ |

Không tạo thêm, không xoá, không đổi vai trò, không đặt câu hỏi chat mới, không sửa file mã nguồn nào.
**Hệ thống sẵn sàng để quay video demo.**
