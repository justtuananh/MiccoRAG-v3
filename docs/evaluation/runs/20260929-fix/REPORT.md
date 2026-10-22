# Kết quả sửa và kiểm thử lại MiccoRAG — 29/09/2026

Bản sửa đã triển khai lên hệ thống đang phục vụ. Đối chiếu lại **116 tiêu chí: 70 PASS, 0 FAIL, 46 BLOCKED, 0 NOT_RUN**. Đây là nghiệm thu một phần: các mục BLOCKED chưa đủ căn cứ kết luận đạt. Kết quả trước sửa là 19 PASS, 46 FAIL, 49 BLOCKED, 2 NOT_RUN; số tiêu chí lỗi không tương đương số bug độc lập.

| Nhóm | PASS | FAIL | BLOCKED |
|---|---:|---:|---:|
| Chức năng/vận hành | 16 | 0 | 17 |
| Nghiệp vụ/phân quyền | 18 | 0 | 10 |
| RAG/nguồn | 11 | 0 | 19 |
| Bảo mật | 25 | 0 | 0 |
| Tổng | 70 | 0 | 46 |

Chi tiết từng mục, bằng chứng và giới hạn: [checklist kết quả](results-checklist.csv), [dữ liệu kết quả](all-results.json), [tổng hợp](summary.json). Bộ tiêu chí gốc và kết quả trước sửa được giữ nguyên để đối chiếu.

## Các thay đổi đã triển khai

- Dùng chung kiểm tra quyền KB/tài liệu ở RAG, tài liệu, Expert, thống kê và xử lý chỉ mục. Giám đốc/Phó giám đốc được đọc, truy xuất và hỏi đáp mọi KB; không tự cấp thêm quyền ghi. Khắc phục trường hợp KB private của hai người cùng không có phòng ban.
- Chặn truy xuất không đăng nhập, giới hạn debug cho Admin trong DEBUG, kiểm tra quyền trước tạo tác vụ. KG chỉ dùng nút/cạnh khi mọi tài liệu nguồn đều được phép; danh sách quyền rỗng không được mở rộng phạm vi.
- Rating chỉ dành cho chủ lịch sử; bỏ qua user_id giả; ẩn nội dung nguồn đã bị thu hồi quyền. Ảnh tài liệu dùng endpoint xác thực và kiểm tra quyền thay cho static công khai.
- Upload theo lô kiểm tra trước khi ghi và rollback nếu lỗi; phòng ban do server xác định. Avatar được giải mã/mã hóa lại, giới hạn dung lượng/kích thước, giữ tệp cũ khi commit lỗi. Chặn khóa JWT mặc định/rỗng ngoài DEBUG.
- Làm sạch HTML ở giao diện, bảo vệ tên nguồn/thuộc tính trích dẫn. SSE bị ngắt hoặc báo lỗi được hiển thị đúng, không gửi POST hỏi đáp lần hai. Sửa bộ lọc, tìm kiếm không dấu, phản hồi tìm kiếm cũ, menu Admin và tràn ngang trên màn hình 390px.
- RAG bổ sung ngữ cảnh liền kề có giới hạn trong cùng tài liệu để giữ bảng, lấy tên tài liệu hiện hành từ DB, kiểm tra ID trích dẫn/ảnh trước trả kết quả. Readiness kiểm DB/vector; bảo vệ đóng session khi client ngắt kết nối.
- Harness nhận diện lỗi tiến trình con, thiếu tổng kết và lỗi thu thập test; phân biệt dịch vụ tùy chọn. Khóa dependency và cho phép bước build esbuild của pnpm.

Danh mục **56 tệp** và hash trước/sau: [change-manifest.json](change-manifest.json).

## Bằng chứng kiểm thử

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| Backend unit/regression | 174 PASS, gồm 44 test cũ | [pytest-final.log](pytest-final.log) |
| Ma trận nghiệp vụ trên ORM/SQLite | 161/161 | [business-sqlite-raw.json](business-sqlite-raw.json) |
| Frontend unit và build | 6/6; build thành công | [stage-frontend-final.log](stage-frontend-final.log) |
| Chromium bảo mật/giao diện với API fixture | 18/18 | [frontend-security-browser.json](frontend-security-browser.json) |
| Trình duyệt nối staging, 5 vai trò | 55/55, không lỗi API/JS | [frontend-stage-browser.json](frontend-stage-browser.json) |
| Trình duyệt nối live, 5 vai trò | 20/20, không lỗi API/JS | [frontend-live-smoke.json](frontend-live-smoke.json) |
| SSE lỗi/ngắt, mobile, bàn phím | Đúng trạng thái; không fallback POST; không tràn ngang 390px | [frontend-stage-faults-mobile.json](frontend-stage-faults-mobile.json) |
| QA và deploy harness sau rollout | 23 PASS, 0 FAIL, 9 WARN | [live-harness.log](live-harness.log) |

Các nhóm kiểm tra có phạm vi giao nhau, không cộng thành số ca độc lập. Harness còn cảnh báo ESLint (57 lỗi tồn tại), thiếu ruff/pytest-cov, DuckDNS tùy chọn, chưa có alembic_version và các bài RAG/E2E tùy chọn không bật trong harness; RAG và trình duyệt được chạy riêng như các bằng chứng trên. Không tuyên bố toàn bộ lint/coverage đã đạt.

Pilot RAG trên ba tài liệu nguồn: **10/10 câu chính, 22/22 biến thể trả lời đúng** theo rubric đối chiếu tài liệu gốc, so với 16/22 trước sửa. Ca bảng mua sắm G04 đạt 6/6; không có lỗi HTTP hoặc trích dẫn không giải được trong mẫu cuối, 6/6 stream hoàn tất. Kiểm tra bổ sung tên nguồn hiện hành sau sửa SRC-02 cũng đạt. Đây là mẫu giới hạn, chưa thay thế bộ đáp án chuẩn được chủ nghiệp vụ phê duyệt. Xem [đáp án đã chấm](rag-graded-answers.json), [báo cáo RAG](rag-fix-report.md), [bằng chứng tên nguồn](src02-proof.json).

## Kiểm tra trên hệ thống thật và triển khai

[Probe sau triển khai](live-postfix-results.json) dùng KB private và tài liệu tổng hợp: khách gọi chunks qua backend 8001 và gateway 8888 đều nhận 401; Giám đốc/Phó giám đốc đọc và query nhận 200, thao tác ghi nhận 403; nhân viên ngoài KB nhận 403. Giám đốc hỏi đáp trả đúng số tiền 7.654.321 đồng và thời hạn 6 ngày làm việc của tài liệu thử, kèm trích dẫn. Vòng upload → xử lý → indexed → tải → truy xuất → xóa hoàn tất; xử lý trùng nhận 409.

Hai lần triển khai đầu tự rollback do cửa sổ chờ khởi động 15 giây chưa đủ. Sau khi tăng thời gian chờ lên 120 giây, triển khai thành công; không đổi mã ứng dụng giữa các lần này. [Kết quả triển khai](deployment-result.json) ghi health, ready, frontend và gateway đều 200. Chỉ thao tác ứng dụng này trên các cổng 8001/5174/8888, không thay dịch vụ khác.

Đã giữ bản sao mã nguồn và DB trước triển khai, cùng node_modules và cấu hình tiến trình cũ trong thư mục backup được bảo vệ trên máy chủ. Bản sao DB: `/tmp/micco-fix-baseline-db-20260929.dump`; backup để rollback: `/tmp/micco-fix-20260929/deploy-backup`. Không reset các thay đổi có sẵn và không tạo commit.

[Kiểm tra cuối](cleanup-verification.json): 56/56 tệp live khớp hash bản sửa; DB trở về 14 người dùng, 7 KB, 17 tài liệu, không còn user/KB/tài liệu EVAL. Tài liệu và tài khoản thử đã được xóa. Dịch vụ staging và token trình duyệt tạm được dọn sau kiểm thử; lưu bằng chứng và backup để xem lại.

## Các phần chưa thể nghiệm thu

**46 BLOCKED** gồm các quy tắc nghiệp vụ chưa được xác nhận, nguồn/chính sách chưa có chuẩn phê duyệt, và phạm vi chưa kiểm đủ như toàn bộ định dạng/OCR, phiên bản/lưu giữ, tải/SLA/khôi phục và toàn bộ tương tác/accessibility. Không tự đổi những chính sách này. Một số lỗi kỹ thuật đã sửa nhưng tiêu chí rộng hơn vẫn BLOCKED; xem lý do riêng trong checklist.

25 tiêu chí bảo mật đạt trong phạm vi bằng chứng đã nêu, không phải chứng nhận toàn hệ thống an toàn. XSS dùng Chromium với API fixture; KG hỗn hợp quyền dùng dữ liệu tổng hợp. Xem [báo cáo bảo mật](security-fix-report.md) để biết giới hạn.
