# Kết quả kiểm tra lại 25 tiêu chí bảo mật

Đã kiểm bản sửa trong môi trường cô lập và kiểm lại ranh giới quyền sau triển khai thật. **25 PASS, 0 FAIL, 0 BLOCKED** trong phạm vi 25 tiêu chí này. Bằng chứng live: `live-postfix-results.json`, `frontend-live-smoke.json`.

Bằng chứng tổng hợp: `pytest-final.log` (174 unit PASS tại thời điểm báo cáo), `tests/unit/test_fix_crossstack.py`, `tests/unit/test_api_security_regressions.py`, `tests/unit/test_retrieval_scope.py`, và `frontend-security-browser.json`. Các payload đều là dữ liệu tổng hợp, không gọi provider trong test bảo mật.

| Tiêu chí | Trạng thái | Kết quả |
|---|---|---|
| SEC-01 | PASS | Khách gọi chunks bị 401 trước truy vấn vector. |
| SEC-02 | PASS | Người ngoài KB private bị 403; không thấy sentinel và không gọi vector. |
| SEC-03 | PASS | Debug-chat không xác thực trả 401 trước retriever/LLM. |
| SEC-04 | PASS | Người ngoài private KB bị 403 ở debug-chat trước truy xuất. |
| SEC-05 | PASS | Bốn tuyến process/batch/reindex/reindex-workspace đều từ chối khách 401, không tạo tác vụ. |
| SEC-06 | PASS | Người ngoài không thể reindex tài liệu hoặc KB private; 403 trước xóa chỉ mục. |
| SEC-07 | PASS | Query KB private có tài liệu gắn public vẫn trả 403, không gọi vector. |
| SEC-08 | PASS | Chat thường và stream KB private trả 403 trước truy xuất. |
| SEC-09 | PASS | Liệt kê/markdown/tải tài liệu public-marked trong KB private bị từ chối cho người ngoài. |
| SEC-10 | PASS | KG loại nút/cạnh có nguồn trộn được phép với cấm hoặc thiếu nguồn; empty scope chặn vector/KG. |
| SEC-11 | PASS | Upload v1 vào KB private của người khác trả 403 trước ghi tệp/DB. |
| SEC-12 | PASS | Trưởng phòng upload vào KB thuộc phòng mình nhưng giả department_id/visibility: server lưu phòng thật và loại KB; lô compat của nhân viên cũng bỏ department_id giả. |
| SEC-13 | PASS | Preview duyệt HTML thử không chạy event handler hoặc javascript URL trong Chromium. |
| SEC-14 | PASS | Chat history/preview với payload img onerror và SVG onload không thực thi trong Chromium. |
| SEC-15 | PASS | Tên nguồn chứa dấu nháy và thuộc tính trích dẫn được giữ như văn bản, không thoát attribute. |
| SEC-16 | PASS | StaticFiles ảnh công khai đã gỡ; ảnh private chỉ lấy qua endpoint bearer: khách 401, người ngoài 403, chủ sở hữu nhận đúng bytes. |
| SEC-17 | PASS | Khách 401, người khác 404, chủ tin nhắn assistant sửa rating thành công. |
| SEC-18 | PASS | Stats/analytics private KB từ khách 401, trước truy vấn dữ liệu. |
| SEC-19 | PASS | Expert recommend private KB của người ngoài trả 403, không gợi ý chuyên gia. |
| SEC-20 | PASS | Startup ngoài DEBUG với khóa JWT mặc định/blank thất bại trước DB; khóa cấu hình và DEBUG fixture được chấp nhận. |
| SEC-21 | PASS | dev-skip bị từ chối khi DEBUG=false và chỉ dùng được trong fixture DEBUG=true. |
| SEC-22 | PASS | Live: chunks ẩn danh qua backend/gateway đều 401; Giám đốc/Phó giám đốc đọc và query private KB 200, ghi 403; nhân viên ngoài KB 403. |
| SEC-23 | PASS | Avatar giả dạng .png bị từ chối; ảnh hợp lệ được giải mã/mã hóa lại, hậu tố độc hại bị loại. V1 upload kiểm giới hạn byte và đuôi tệp. |
| SEC-24 | PASS | Giám đốc/Phó giám đốc đọc KB private mới tạo và không sửa được; ma trận read hiện có duy trì. |
| SEC-25 | PASS | ?user_id=1 bị bỏ qua; lịch sử câu hỏi/trả lời chỉ ghi cho caller ID=5. |

Giới hạn: XSS được kiểm bằng Chromium với API mock, chưa thử vòng lưu/đọc qua tài khoản khác trên hệ thống phục vụ; KG được kiểm bằng dữ liệu pha trộn tổng hợp, chưa có fixture KG live hỗn hợp quyền. Kiểm 25 tiêu chí này không bao phủ path traversal, SSRF, dependencies hay bí mật runtime ngoài điều kiện JWT mặc định.
