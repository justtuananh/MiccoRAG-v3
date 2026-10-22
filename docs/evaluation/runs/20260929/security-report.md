> Cập nhật kiểm chứng của agent điều phối: SEC-01 đã tái hiện trên dịch vụ đang chạy bằng tài liệu **thử riêng**; SEC-22 chuyển BLOCKED → FAIL. Anonymous đọc chunks fixture43 qua cả :8001 và gateway :8888 nhận200/có marker, trong khi GET metadata cùng tài liệu trả401. Đã xóa fixture. Kết quả cập nhật: **1 PASS / 22 FAIL / 2 BLOCKED**. Bằng chứng: `live-security-fixture-results.json`. Nội dung bên dưới giữ mô tả đợt kiểm cô lập ban đầu; không thử khai thác dữ liệu nghiệp vụ thật hay đường Internet.

# Kết quả đánh giá bảo mật — 29/09/2026

**Kết quả cuối: 1 PASS / 22 FAIL / 2 BLOCKED** trên 25 tiêu chí. Phần lớn bằng chứng từ ASGI cô lập hoặc trình duyệt với nội dung tổng hợp; SEC-01/22 còn có bằng chứng live bằng tài liệu private thử, đã dọn sạch. Bảng dưới mô tả lượt cô lập ban đầu; cập nhật live nêu ở đầu báo cáo.

| ID | Kết quả | Bằng chứng ngắn |
|---|---|---|
| SEC-01 | FAIL | HTTP 200; private sentinel returned=True |
| SEC-02 | FAIL | HTTP 200; foreign user sentinel returned=True |
| SEC-03 | FAIL | HTTP 200; fake retriever invoked=True; private sentinel returned=True |
| SEC-04 | FAIL | HTTP 200; fake retriever invoked=True; private sentinel returned=True |
| SEC-05 | FAIL | HTTP process=200, batch=200, reindex=404, workspace=200 |
| SEC-06 | FAIL | HTTP 200; foreign reindex reached fake RAG=True |
| SEC-07 | FAIL | HTTP 200; foreign user private KB sentinel=True |
| SEC-08 | FAIL | nonstream HTTP 200; foreign private KB retrieval invoked=True |
| SEC-09 | FAIL | HTTP 200; private KB document markdown sentinel=True |
| SEC-10 | FAIL | private KG sentinel returned=True with allowed document_ids=[88] |
| SEC-11 | FAIL | HTTP 200; fake DB added=True; temp files=1 |
| SEC-12 | FAIL | HTTP 200; foreign KB added=True; forged dept retained=True; autoapproved=True |
| SEC-13 | FAIL | HTML event handler executed=True |
| SEC-14 | FAIL | untrusted Markdown event handler executed=True |
| SEC-15 | FAIL | chat text preserved active HTML=True; executed=True |
| SEC-16 | FAIL | HTTP 200; anonymous fixture bytes returned=True |
| SEC-17 | FAIL | HTTP 200; anonymous fake rating changed=True |
| SEC-18 | FAIL | HTTP stats=200, analytics=200; no auth token |
| SEC-19 | FAIL | HTTP 200; recommendation invoked=True |
| SEC-20 | BLOCKED | effective JWT secret uses built-in default=False; DEBUG=False |
| SEC-21 | PASS | DEBUG=false rejected=True; DEBUG=true fixture user returned=True |
| SEC-22 | FAIL | backend: 404,404,404,404,401; gateway: 404,404,404,404,401 |
| SEC-23 | FAIL | non-image bytes with .png HTTP 200; temp file saved=True |
| SEC-24 | BLOCKED | Both management roles read private fixture KB; neither can modify it |
| SEC-25 | FAIL | HTTP 200; authenticated id=22 wrote 2 fake chat rows as id=11=True |

Các thất bại có tác động rõ nhất: đọc chunk và debug-chat không cần token (SEC-01–04); người ngoài KB vẫn truy vấn nội dung KB riêng tư (SEC-07/09), upload vào KB lạ và giả phòng ban (SEC-11/12), KG trả dữ liệu ngoài danh sách tài liệu được phép (SEC-10), XSS ở các điểm chèn HTML (SEC-13–15), và ghi lịch sử chat dưới ID người khác qua tham số `user_id` (SEC-25).

Giới hạn: SEC-20 chưa thử khởi động với bí mật JWT mặc định; SEC-22 chỉ xác nhận 404/401 với ID giả trên backend/gateway, không chứng minh chính sách cho tài liệu có thật; SEC-24 mới kiểm helper trên một KB giả. Tất cả kết quả ASGI dùng chặn socket và các dịch vụ giả. Phép thử Chromium chặn mọi yêu cầu mạng. Không gửi process/reindex lên dịch vụ sống, không xem nội dung tài liệu hay bí mật runtime.

Sự cố trong lần thử đầu: reindex-workspace với ID KB giả 77 đã đi tới lệnh xóa collection thật trước khi bị chặn; Chroma trả “collection kb_77 does not exist”, nên không có collection bị xóa. Mọi lần chạy sau đều thay `get_vector_store` bằng giả và chặn socket. Trong lần đầu, debug-chat có thể đã thử gọi provider với duy nhất câu hỏi giả; không có dữ liệu thật. Lần chạy cuối thay provider bằng giả và chặn socket.

Tệp tái lập: `security_probe.py` (chạy từ backend venv qua stdin), `security_xss.cjs`, `renderMarkdown.fixture.js`; bằng chứng thô: `security-probe.raw.json`, `xss-results.json`, `live-probes.json`.
