# Dữ liệu thử đợt sửa desktop 22/10/2026

Parent đã bật lại **chỉ tài khoản QA32** (`qa.acceptance.20261022@micco.local`) qua Admin UI để thực hiện fixture. Sau cùng phải vô hiệu hóa lại qua UI. Không đổi mật khẩu tài khoản thật; phiên bootstrap tạm không ghi trong báo cáo.

| Dữ liệu | Chủ sở hữu | Trạng thái / việc còn làm |
|---|---|---|
| QA32 | Tài khoản QA do đợt nghiệm thu trước tạo | Đang hoạt động để kiểm tra; sẽ vô hiệu hóa sau cùng |
| DOC-0078, QA-FIX-20261022-B06-rejection.txt | QA32 | Fixture từ chối B06; giữ đến kiểm tra lại/final cleanup, chỉ soft delete qua UI |
| Knowledge ID5, QA-FIX-20261022-B07-knowledge | QA32 | Fixture B07; giữ qua kiểm tra trạng thái và hồi quy RAG cuối, sau đó soft delete qua UI |
| DOC-0079, QA-FIX-20261022-B07-knowledge.md, workspace8 | QA32 | Sinh từ knowledge5, đã approved/INDEXED; giữ cho RAG cuối rồi kiểm tra trash sau xóa knowledge5 |
| DOC47–54 và knowledge1–4/workspace17–18 | QA của đợt trước | Đã ở thùng rác; không khôi phục hoặc xóa vĩnh viễn |

Các ID55–77 và mọi dữ liệu khác không được coi là fixture của đợt sửa này. Không dọn theo prefix QA chung vì có thể có phiên kiểm tra khác đang chạy. Luna chỉ dọn đúng ID mới được ghi ở bảng này.

Local B05: Luna đã xóa đúng ba tệp lớn vừa tạo; không có upload POST cho tệp lớn hoặc tệp rỗng. Local tệp TXT nhỏ có thể giữ làm fixture chạy lại.

Cuối phiên: đóng đúng context QA của cặp agent/parent, dừng bootstrap localhost18997 và Vite15175 do phiên tạo, xóa riêng JSON chứa phiên tạm; khôi phục tùy chọn MCP profile tạm sau khi các agent xong. Không dừng trình duyệt hay tiến trình của phiên khác.
