# Khắc phục và kiểm tra lại desktop — 22/10/2026

Đích: https://chatbot.coremind.io.vn. Sol sửa, Luna kiểm tra bằng MCP Playwright, parent triển khai có rollback. Không sửa mobile theo yêu cầu. Kết quả cũ giữ trong [hồ sơ chung](../NGHIEM_THU_UI.md).

| Lỗi | Nội dung | Trạng thái |
|---|---|---|
| B01/B02 | Đăng nhập và footer mobile | Bỏ qua theo yêu cầu |
| B03 | Lọc phòng ban tài liệu | PASS live — [Sol](B03-sol.md), [Luna](B03-luna.md) |
| B04 | Tệp rỗng | PASS public — [Sol](B04-sol.md), [Luna](B04-luna.md) |
| B05 | Tệp vượt 50 MB | PASS public — [Sol](B05-sol.md), [Luna](B05-luna.md) |
| B06 | Lý do từ chối tài liệu | PASS public — [Sol](B06-sol.md), [Luna](B06-luna.md) |
| B07 | Nhãn xử lý tri thức | PASS public — [Sol](B07-sol.md), [Luna](B07-luna.md) |
| B08 | Nút Google không phản hồi | Đã triển khai phản hồi chưa hỗ trợ; chờ Luna xác minh |
| B09 | Quên mật khẩu không có trợ giúp | Chờ |
| B10 | URL lạ hiển thị trắng | Chờ |
| B11 | Lỗi tải tri thức hiển thị thành dữ liệu rỗng | Chờ |

Mỗi lỗi lưu bước tái hiện, expected, kết quả trước/sau, bản mã, bằng chứng và hồi quy trong Bxx-sol.md và Bxx-luna.md. Không ghi thông tin xác thực.

Các log RED/GREEN/unit/harness B04–B07 đã được giữ trong `harness/reports/fixes-20261022/`, không chỉ ở thư mục tạm. Mỗi PASS public có hash bundle và ảnh chụp trong báo cáo Luna tương ứng.
