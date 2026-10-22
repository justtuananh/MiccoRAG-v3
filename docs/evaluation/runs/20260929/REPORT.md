# Báo cáo đánh giá MiccoRAG — 29/09/2026

**Kết luận: CHƯA ĐẠT để nghiệm thu.** Đã kết thúc đợt kiểm tra này; chưa hoàn thành toàn bộ phạm vi nghiệm thu. Các lỗi phân quyền và bảo mật cần được xử lý trước khi nghiệm thu, sau đó chạy lại các ca hồi quy. Đây là báo cáo đánh giá, chưa phải đợt sửa lỗi ứng dụng.

## Kết quả tổng hợp

| Nhóm | Đạt | Không đạt | Chưa đủ điều kiện/kết luận | Chưa chạy |
|---|---:|---:|---:|---:|
| Chức năng và vận hành | 4 | 11 | 16 | 2 |
| Nghiệp vụ và phân quyền | 12 | 4 | 12 | 0 |
| RAG và nguồn | 2 | 9 | 19 | 0 |
| Bảo mật | 1 | 22 | 2 | 0 |
| **Tổng: 116 tiêu chí** | **19** | **46** | **49** | **2** |

Đây là số **tiêu chí**, không phải 46 lỗi độc lập: một lỗi có thể ảnh hưởng nhiều tiêu chí. PASS chỉ có giá trị trong phạm vi bằng chứng của từng hàng. BLOCKED gồm thiếu quyết định nghiệp vụ, dữ liệu chuẩn hoặc bằng chứng kiểm thử cần thiết. Hai tiêu chí chưa chạy là FUNC-11 (bộ lọc/tìm kiếm đầy đủ) và FUNC-26 (khả dụng/trợ năng đầy đủ). Không coi các mục này là đạt.

Chi tiết máy đọc được: [checklist kết quả](results-checklist.csv), [toàn bộ bản ghi](all-results.json), [thống kê](summary.json).

## Phát hiện cần ưu tiên

1. **Đọc nội dung tài liệu riêng mà không đăng nhập.** GET `/api/v1/rag/chunks/{id}` trả 200 và nội dung của tài liệu thử private qua cả backend :8001 và gateway :8888; metadata cùng tài liệu trả 401. Đã tái hiện trên dịch vụ đang chạy bằng dữ liệu tổng hợp và xóa dữ liệu thử. Đây là bằng chứng trực tiếp; chưa kiểm chứng khả năng truy cập từ Internet. [Bằng chứng](live-security-fixture-results.json).
2. **Kiểm soát quyền chưa nhất quán giữa các đường truy cập.** Kiểm thử ASGI cô lập tái hiện truy xuất/chat KB người khác, truy xuất graph bỏ qua tập tài liệu được phép, upload trái phạm vi và giả phòng ban để tự duyệt; các endpoint debug/job/rating cũng có trường hợp thiếu kiểm quyền. Dùng DB/vector/LLM giả để kiểm logic handler, không diễn giải tất cả thành khai thác live. [Chi tiết bảo mật](security-report.md).
3. **Nội dung HTML/Markdown có thể thực thi JavaScript.** Trình duyệt thật chạy được event handler từ nội dung thử qua bộ render của ứng dụng. Các đường HTML phê duyệt và chat cần kiểm soát nội dung không tin cậy. Điều kiện phát tán giữa người dùng chưa được tái hiện trọn chuỗi trên live. [Bằng chứng](xss-results.json).
4. **Ban giám đốc được đọc/hỏi KB, nhưng Expert chưa đồng nhất.** Đường RAG chính cho Giám đốc và Phó giám đốc truy cập 7/7 KB và 17/17 tài liệu hiện có. Tuy nhiên helper Expert loại một số tài liệu mà RAG cho phép. Quyền đọc rộng là yêu cầu đã xác nhận; không đồng nghĩa cấp thêm quyền sửa/xóa/duyệt. [Bằng chứng Expert](expert-scope-results.json), [nghiệp vụ](business-report.md).
5. **Bỏ sót nội dung bảng, dẫn đến trả lời thiếu nghiệp vụ.** Câu hỏi gói mua sắm đúng 500 triệu có đấu thầu phải nêu Giám đốc và tối đa 20 ngày làm việc theo tài liệu hiện có. Cả 6 biến thể đã thử đều thiếu thông tin này hoặc nói tài liệu không có. Đoạn bảng đã nằm trong chỉ mục và được lấy ra khi hỏi hẹp; lỗi nằm ở quá trình chọn ngữ cảnh cho câu hỏi ban đầu, chưa xác định duy nhất một tham số gây lỗi. [Chấm đáp án](rag-graded-answers.json), [chẩn đoán](rag-diagnostics.json).
6. **Lỗi chức năng làm người dùng hiểu sai kết quả.** Stream kết thúc sớm không có sự kiện hoàn tất vẫn hiển thị câu trả lời dở như đã xong; upload lô trả lỗi nhưng đã lưu một phần; một đáp án trích dẫn mã không tồn tại trong danh sách nguồn. Giao diện quản trị cho một số vai trò vào trang nhưng API trả 403. [Chức năng](functional-results.json), [upload lô](functional-multiupload-results.json), [stream lỗi](browser-fault-results.json).

## Những phần đã hoạt động trong phạm vi thử

- 44 unit test đạt; frontend build đạt. Smoke chạy lại: 13 PASS, 1 FAIL, 2 WARN; lỗi còn lại liên quan dịch vụ DuckDNS tùy chọn không có. Các timeout ban đầu không còn tái hiện ở lượt kiểm lại, không được tính thành lỗi thường trực.
- Trình duyệt: 55 kiểm tra tuyến trang qua 5 vai trò, thêm ca token không hợp lệ; không có page error. Tuyến trang mở đúng không chứng minh API bên trong đủ quyền, như lỗi 403 đã nêu.
- Luồng live bằng tài khoản và KB tạm: tạo/sửa KB, upload TXT, từ chối .exe, xử lý/lập chỉ mục, tải xuống đúng hash, hỏi đáp theo nội dung tổng hợp, xóa tài liệu/KB đều chạy được. Xử lý lặp trả 409. [Bằng chứng](live-lifecycle-results.json).
- Đăng ký, cập nhật hồ sơ, đổi mật khẩu live đạt; gửi vai trò Admin không tự nâng quyền. Lỗi MissingGreenlet từ fixture SQLite không tái hiện live nên đã loại khỏi kết luận. [Bằng chứng](live-auth-profile-results.json).

## Độ đúng câu trả lời và nguồn nghiệp vụ

Pilot gồm **10 câu hỏi chính, 22 biến thể đáp án, đối chiếu 3 tài liệu nguồn** được trích riêng từ DOCX/PDF gốc. Kết quả: **9/10 câu trả lời chính** và **16/22 biến thể** đủ đúng các dữ kiện được kiểm; **1/22** có mã trích dẫn không khớp nguồn; không có lỗi HTTP. Ba lượt stream có đo sự kiện đều hoàn tất và khớp nội dung token.

Các số này là kết quả mẫu nhỏ, có câu hỏi lặp; **không phải tỷ lệ chính xác của toàn hệ thống**. Tài liệu hiện có được dùng làm chuẩn theo yêu cầu người dùng, nhưng thẩm quyền, phiên bản hiệu lực và các điểm nghiệp vụ Q-01–Q-11 vẫn cần chủ nghiệp vụ xác nhận. Chưa đủ mẫu OCR/ảnh, nguồn mâu thuẫn, phiên bản hoặc nhiều nguồn để nghiệm thu toàn diện. [Kết quả RAG](rag-results.json), [nguồn và hash](original-sources.json).

## Phạm vi, tính toàn vẹn và giới hạn

Đánh giá trên phiên bản triển khai tương ứng HEAD `debbaa68b2485106e261d2b31525b47580e5640c` cộng thay đổi chưa commit. [Snapshot](snapshot.json) ghi hash tệp; riêng SHA Git không đủ tái lập trạng thái này. Các agent Sol chuyên trách nghiệp vụ và bảo mật phối hợp với điều phối kiểm RAG, UI và vận hành.

Đã dọn tài khoản, KB, tài liệu và lịch sử thử; kiểm cuối ghi nhận 14 người dùng, 7 KB, 17 tài liệu, không còn bản ghi thử và không thay đổi tệp mã nguồn ứng dụng. [Kiểm tra dọn dữ liệu](cleanup-verification.json).

Trong lượt harness cô lập đầu có thiếu mock khiến phát sinh yêu cầu xóa collection thử `kb_77`; Chroma trả collection không tồn tại, không có collection bị xóa. Một đường debug có thể đã gọi provider với nội dung tổng hợp. Các lượt sau đã bổ sung mock và chặn socket. Không tuyên bố mọi lượt thử ban đầu hoàn toàn không có mạng. Xem [báo cáo bảo mật](security-report.md).

Ưu tiên tiếp theo: sửa kiểm quyền và render nội dung, thống nhất quyền Expert, sửa retrieval bảng và trích dẫn, xử lý upload/stream lỗi; chạy lại ca thất bại, hoàn thành các mục chưa chạy và chốt các quy tắc nghiệp vụ còn mở trước nghiệm thu.
