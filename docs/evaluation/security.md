# Tiêu chí đánh giá an toàn thông tin

Nguồn rà soát tĩnh: `/home/micco/MiccoRAG-v3`. **Tất cả tiêu chí thực nghiệm đều NOT_RUN.** Dùng người dùng, tài liệu, KG giả lập cùng LLM/hàng đợi mock. Với yêu cầu bị từ chối, 401/403/404 theo quy ước API đều chấp nhận nếu **không lộ dữ liệu và không gây hành động**. Giữ chính sách Giám đốc/Phó giám đốc đọc mọi KB.

| ID | Ưu tiên | Đầu vào / tình huống | Kỳ vọng | Nguồn | Phương pháp / trạng thái |
|---|---|---|---|---|---|
| SEC-01 | P0 | Khách gọi `GET /api/v1/rag/chunks/{private_indexed_id}` | Bị từ chối, không có chunk | `app/api/rag.py:572-617` | Tích hợp, NOT_RUN |
| SEC-02 | P0 | Người khác đọc chunk tài liệu riêng tư | Bị từ chối, không có nội dung | `app/api/rag.py:572-617` | Tích hợp, NOT_RUN |
| SEC-03 | P0 | Khách gọi debug-chat với ID tài liệu riêng tư | Bị từ chối; không gọi retriever/LLM | `app/api/rag.py:1342-1408` | Mock tích hợp, NOT_RUN |
| SEC-04 | P0 | Người ngoài KB gọi debug-chat KB riêng tư | Bị từ chối; không lộ prompt/nguồn | `app/api/rag.py:76-87,1342-1408` | Tích hợp, NOT_RUN |
| SEC-05 | P0 | Khách gọi process/process-batch/reindex/reindex-workspace | Bị từ chối; hàng đợi và dữ liệu không đổi | `app/api/rag.py:231-515` | Mock tích hợp, NOT_RUN |
| SEC-06 | P0 | Nhân viên reindex tài liệu phòng khác | Bị từ chối; chỉ mục cũ nguyên vẹn | `app/api/rag.py:365-425` | Mock tích hợp, NOT_RUN |
| SEC-07 | P0 | Người ngoài hỏi KB riêng tư có tài liệu gắn public | Bị từ chối; không trả kết quả | `app/api/workspaces.py:34-44`; `app/api/rag.py:115-146` | Tích hợp, NOT_RUN |
| SEC-08 | P0 | Người ngoài chat KB riêng tư, stream và thường | Bị từ chối; không truy xuất | `app/api/rag.py:922-980`; `app/api/chat_agent.py:845-860` | Tích hợp, NOT_RUN |
| SEC-09 | P0 | Người ngoài liệt kê/xem/tải tài liệu trong KB riêng tư | Bị từ chối dù tài liệu gắn public | `app/api/documents.py:61-98,249-305,403-437` | Tích hợp, NOT_RUN |
| SEC-10 | P0 | KG có dấu mốc riêng tư và tài liệu công khai; hỏi tài liệu công khai | KG summary không có dấu mốc riêng tư | `app/services/deep_retriever.py:88-110,143-160` | Mock KG, NOT_RUN |
| SEC-11 | P0 | Nhân viên upload vào KB riêng tư của người khác | Bị từ chối; không ghi tệp | `app/api/documents.py:182-217` | Tích hợp, NOT_RUN |
| SEC-12 | P0 | Trưởng phòng upload vào KB lạ hoặc giả `department_id` | Bị từ chối/kiểm hợp lệ; không tự duyệt | `app/api/documents.py:219-234` | Tích hợp, NOT_RUN |
| SEC-13 | P0 | Mục tri thức pending có sự kiện HTML vô hại; Admin mở preview | Sự kiện không chạy | `app/api_compat/knowledge.py:142-200`; `micco-frontend/src/pages/Approvals.jsx:123-129,587-592` | Trình duyệt cô lập, NOT_RUN |
| SEC-14 | P0 | Markdown tài liệu thử có HTML/sự kiện vô hại; người khác mở preview | Sự kiện không chạy | `micco-frontend/src/pages/ChatAssistant.jsx:144-263,1180-1183` | Trình duyệt cô lập, NOT_RUN |
| SEC-15 | P1 | Câu trả lời chat/tên nguồn có dấu nháy và ký tự HTML | Văn bản, thuộc tính được escape | `micco-frontend/src/pages/ChatAssistant.jsx:247-263,449-462` | Component/trình duyệt, NOT_RUN |
| SEC-16 | P1 | Khách lấy ảnh trích từ tài liệu riêng tư | Bị từ chối; không trả ảnh | `app/main.py:227-230`; `app/api/rag.py:175-184` | Tích hợp, NOT_RUN |
| SEC-17 | P1 | Khách/người khác đánh giá nguồn với message ID đã biết | Bị từ chối; rating không đổi | `app/api/rag.py:882-913` | Tích hợp, NOT_RUN |
| SEC-18 | P1 | Khách gọi stats/analytics KB riêng tư | Bị từ chối; không lộ tên tệp/KG | `app/api/rag.py:518-569,717-809` | Tích hợp, NOT_RUN |
| SEC-19 | P1 | Người đăng nhập xin gợi ý chuyên gia từ KB riêng tư không thuộc quyền | Bị từ chối; không trả chuyên gia | `app/api/expert.py:20-31,89-105` | Tích hợp, NOT_RUN |
| SEC-20 | P1 | Máy chủ ngoài dev dùng bí mật JWT mặc định | Khởi động thất bại an toàn, không in bí mật | `app/core/config.py:142`; `app/core/security.py:33-51` | Unit cấu hình, NOT_RUN |
| SEC-21 | P1 | Token `dev-skip` với `DEBUG=false`, rồi `DEBUG=true` trong app cô lập | Bị từ chối ngoài dev; nhánh dev đúng phạm vi | `app/core/security.py:61-81` | Tích hợp cấu hình, NOT_RUN |
| SEC-22 | P1 | Gọi tuyến nhạy cảm qua backend trực tiếp và gateway | Cùng chính sách từ chối; không lộ dữ liệu/hành động | `app/main.py:201-230`; gateway thực tế chưa xác minh | Probe chỉ đọc, NOT_RUN |
| SEC-23 | P1 | Upload tệp sai dạng/quá lớn hoặc ảnh giả định dạng | Từ chối có giới hạn, không gọi parser | `app/api/documents.py:198-210`; `app/api_compat/auth.py:158-193` | Tích hợp, NOT_RUN |
| SEC-24 | P1 | Giám đốc/Phó giám đốc đọc mọi KB hiện có và KB tạo thêm, kể cả riêng tư | Được đọc; quyền sửa/xóa kiểm riêng | `app/core/permissions.py:3-8`; `app/api/workspaces.py:34-69` | Ma trận vai trò, NOT_RUN |
| SEC-25 | P0 | Người dùng A gọi chat với `?user_id={ID của B}` | Chỉ ghi lịch sử cho A; không tạo hàng của B | `app/api/rag.py:937-949,1251-1277` | Mock DB/LLM, NOT_RUN |

Path traversal, SSRF, dependency và bí mật runtime cần đợt rà soát riêng; chưa được kiểm chứng hệ thống ở đây.
