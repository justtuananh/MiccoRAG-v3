# Sol — phụ lục DELTA cuối, 22/10/2026

**NO-GO giữ nguyên. 35 ca chuẩn: 6 PASS / 9 FAIL / 19 PARTIAL / 1 NOT_RUN (A07); tổng 35.** Có **11 issue được chấp nhận: 2 S1 + 9 S2**, chưa có bằng chứng sửa lỗi. B01 overlay mobile 390×844 ở 100% và B02 footer workspace 360×640 vẫn chặn luồng. Không quan sát S0 trong phạm vi đã chạy; không bảo đảm không còn lỗi.

Phạm vi: đọc lại `luna-chat.md` bản cập nhật, đối chiếu `criteria.md`, `sol-audit.md` và xem trực tiếp ba ảnh mới bên dưới. Chỉ ghi phụ lục này; giữ nguyên nội dung và timestamp audit gốc. Không chạy lại sáu kiểm tra độc lập, không hỏi LLM, không thao tác UI/API hoặc sửa nguồn/deploy.

## Ma trận 35 ca — chỉ các dòng thay đổi

Các dòng khác kế thừa audit gốc; biến thể PASS không tự nâng cả ID chuẩn thành PASS.

| ID | Trước → sau | Bằng chứng bổ sung được chấp nhận | Phần chưa đủ |
|---|---|---|---|
| C04 | PARTIAL → PARTIAL | C04a–c đã có reload, Hủy/xóa và cách ly user. C04d báo cáo đăng nhập bằng form trong context không inject token, gửi câu QA51, đổi KB Kỹ thuật → Default Workspace → KB Kỹ thuật, logout rồi login lại; lịch sử còn. | Chưa thử đổi nhanh khi request cũ đang chạy, race/ghi đè lịch sử. Ảnh tĩnh không chứng minh toàn chuỗi chuyển trạng thái. |
| C05 | NOT_RUN → PARTIAL | Ordinary không thấy mode/system prompt; Admin có Hybrid/Vector only/Graph only, chọn Vector rồi trả Hybrid, không gửi câu hỏi. Abort request chat trong browser làm hiện lỗi, gợi ý thử lại và dừng loading; báo cáo ghi composer dùng được. | Chưa so đầu ra retrieval giữa mode; chưa bấm retry và xác nhận hoàn tất. Abort trước backend chưa kiểm chứng ngắt giữa stream đang trả dữ liệu. Chưa chứng minh loại trừ tài liệu pending/khác workspace. |

## Đối chiếu artifact mới

Tất cả ảnh ở `harness/reports/acceptance-20261022/`.

- Đã xem `luna-c04-workspace-a-return.png` và `luna-c04-login-history.png`: đều thấy QA2, KB Kỹ thuật, câu QA51, đáp án đúng mã và citation `[p8sc]`. Hai ảnh có cùng nội dung byte; tự chúng không phân biệt thời điểm trước/sau login. Chấp nhận chuỗi thao tác theo báo cáo Luna, không coi ảnh là bằng chứng độc lập đầy đủ.
- Đã xem `luna-c05-aborted-stream.png`: thấy `Failed to fetch` và “Đưa câu hỏi vào ô nhập để thử lại”, không có đáp án hoàn tất giả. Ảnh không tự chứng minh composer có thể gửi thành công; phần này dựa trên quan sát worker và chưa có retry hoàn tất.
- Artifact bổ trợ được báo cáo: `luna-c04-login.png`, `luna-c04-seed.png`, `luna-c04-workspace-b.png`, `luna-c04-logout.png`, `luna-c05-admin-mode.png`, `luna-c04-c05-cleanup.png`. Chưa xem trực tiếp các ảnh này trong lượt DELTA.

## Điều kiện còn lại

Tổng chat trả phí được worker báo là **7**; thông điệp fault injection bị abort trước mạng/backend, không phải một truy vấn LLM hay outage production. Worker báo đã xóa riêng chat QA, reload xác nhận và đóng context; phụ lục không xác minh cleanup fixture/account do parent phụ trách.

Trước GO vẫn cần sửa/retest hai S1, hoàn tất các khoảng trống C04/C05 trên và D08/D09/D10/K05 cùng các PARTIAL khác hoặc ngoại lệ được người nghiệm thu chấp nhận. A07 vẫn NOT_RUN. Không thêm issue cho Expert no-match; giữ các kết luận bác bỏ login-error/sort và đánh giá version pending của audit gốc. Parent cập nhật một tài liệu dùng lại `docs/NGHIEM_THU_UI.md` theo DELTA này, không thay timestamp audit cũ.
