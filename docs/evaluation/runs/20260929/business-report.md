# Kết quả BIZ/RBAC — 2026-09-29

Đã chạy API live chỉ đọc, handler với mock, và backend thật trên SQLite bất đồng bộ cô lập. Có thêm bằng chứng SEC chạy API với fixture giả, dẫn ở các ca liên quan. Không sửa dữ liệu nghiệp vụ hiện hữu. Token/mật khẩu không lưu trong JSON. Trạng thái PASS chỉ cho phạm vi nêu ở cột bằng chứng; BLOCKED là chưa đủ biến thể hoặc thiếu oracle nghiệp vụ.

**Tổng 28 tiêu chí:** 12 PASS, 4 FAIL, 12 BLOCKED. Hồi quy có sẵn 21 passed; mock handler 68/68; SQLite 159/161, hai sai lệch đều thuộc cùng lỗi hỏi tài liệu private của owner.

Live ban đầu: 7 KB, không có private; 17 docs, không có private; 0 KnowledgeEntry/pending. SQLite fixture có 5 KB (2 private), 8 Document, 7 KnowledgeEntry, 6 vai trò; state transitions thật trên DB cô lập, background tasks không thực thi.

| ID | Kết quả | Bằng chứng và giới hạn |
|---|---|---|
| RBAC-01 | PASS | Live lãnh đạo 7/7 KB, chi tiết 7/7 HTTP 200; SQLite private KB 14/15: hai vai trò lãnh đạo thấy trong list/summary và GET 200. |
| RBAC-02 | BLOCKED | Chưa hỏi RAG KB private; live không có private KB/tài liệu. |
| RBAC-03 | PASS | 12/12 PUT/DELETE KB của người khác với Giám đốc/Phó giám đốc: 403, 0 commit (handler cô lập). |
| RBAC-04 | PASS | Live nhân viên/trưởng phòng 2 KB và GET khác phòng 403; SQLite 6 vai trò × 5 KB xác nhận public, phòng mình, private của mình; private người khác 403. |
| RBAC-05 | FAIL | SEC-07/08: người ngoài GET/query/chat KB private theo ID và nhận sentinel từ tài liệu trong fixture; fail phân quyền truy xuất, chi tiết security-results.json. |
| RBAC-06 | FAIL | SEC-02: user khác owner lấy sentinel tài liệu private qua API chunk; ngoài ra private filter theo department thiếu owner check. Chi tiết security-results.json. |
| RBAC-07 | BLOCKED | Test hồi quy sẵn có xác nhận query loại ID cấm trong mock, nhưng chưa có kiểm live đủ query/chat/citation. |
| RBAC-08 | PASS | Live lãnh đạo 17/17 docs; SQLite 6 vai trò kiểm list/GET private doc 104/105: lãnh đạo/Admin và owner 200, người khác 403. |
| RBAC-09 | PASS | SQLite 6 vai trò × private KnowledgeEntry 201/202: lãnh đạo/Admin và owner nhìn thấy; vai trò khác bị 403/không liệt kê. |
| RBAC-10 | PASS | SQLite pending 205/206 và rejected 207: lãnh đạo chỉ liệt kê approved, owner/Admin thấy bản của mình; GET tuân cùng phạm vi. Quy tắc xem bản nháp vẫn cần chủ nghiệp vụ xác nhận nếu muốn mở rộng. |
| RBAC-11 | PASS | SQLite PUT/DELETE private KnowledgeEntry khác owner: Staff/Director 403, không đổi; owner sửa/xóa thành công, Admin sửa thành công. |
| RBAC-12 | PASS | SQLite: Staff tạo private gắn owner; Admin tạo public; Head C tạo department gắn phòng C; Staff/Director tạo public 403, Staff tạo department 403. |
| RBAC-13 | PASS | SQLite Admin chuyển Staff→Director→Staff; cùng JWT cũ truy vấn user từ DB nhận role mới, quyền private B được cấp rồi thu hồi. |
| RBAC-14 | PASS | SQLite Admin update role Director ở phòng A và Staff ở Ban Giám đốc đều HTTP 400; chuyển role cùng phòng hợp lệ thành công. Quy tắc tên phòng vẫn cần chốt riêng. |
| BIZ-01 | BLOCKED | Chưa upload/duyệt tài liệu nội bộ; chỉ kiểm nhánh quyền duyệt âm bằng DB giả. |
| BIZ-02 | BLOCKED | SQLite public Document pending→pending_org→approved/processing; trước INDEXED không vào allowed IDs; task index chỉ được xếp hàng, không chạy. |
| BIZ-03 | PASS | Handler cô lập 12/12 approve/reject trái phòng hoặc trái cấp duyệt: 403, 0 commit. |
| BIZ-04 | PASS | Handler cô lập approve/reject lặp trên approved/rejected và pending_org không public: 400, 0 commit. |
| BIZ-05 | FAIL | SQLite private docs 104/105 do owner A/B sở hữu, department_id=NULL: `get_allowed_document_ids` trả [] thay vì [104]/[105]; owner không thể hỏi tài liệu private của mình. Live lifecycle Admin private có thể query, không phủ định lỗi Staff. |
| BIZ-06 | BLOCKED | SQLite public KnowledgeEntry pending_dept→pending_org→approved/Active/ingest_status=processing; chỉ xếp task, chưa ingest/hỏi. |
| BIZ-07 | BLOCKED | Handler cô lập: reject KnowledgeEntry thiếu lý do 400, Document thiếu lý do 200/rejected/note null. Cần chủ nghiệp vụ chốt thống nhất. |
| BIZ-08 | BLOCKED | Chưa thử sửa tri thức và xóa chỉ mục cũ; thiếu dữ liệu và oracle vòng đời. |
| BIZ-09 | BLOCKED | Chưa upload phiên bản mới, chưa đối chiếu index cũ/mới; thiếu oracle thời điểm ngừng phục vụ bản cũ. |
| BIZ-10 | BLOCKED | SQLite allowed IDs bỏ pending_org và FAILED kể cả doc còn INDEXED; chưa seed vector cũ hay chạy graph/chat. |
| BIZ-11 | BLOCKED | SQLite count/list đúng từng role/cấp; handler status của Trưởng phòng A với pending Document phòng B trả 200 (ngoài queue), cần xác nhận phạm vi detail. |
| BIZ-12 | FAIL | SEC-12: upload mạo department_id phòng khác HTTP 200, lưu phòng mạo và autoapproved. Xem security-results.json. |
| BIZ-13 | BLOCKED | Không đổi tên phòng live; quy tắc dựa tên phòng cần oracle chính thức. |
| BIZ-14 | BLOCKED | SQLite PUT visibility=public lên private KB giữ private như mã hiện hành; cần hợp đồng API chốt việc im lặng bỏ qua. |

`business-live-raw.json`, `business-isolated-raw.json`, `business-sqlite-raw.json` và 3 script probe là bằng chứng gốc. `security-results.json` chứng minh các lỗ hổng API bằng fixture giả. SQLite cài riêng `aiosqlite` dưới `/tmp/micco-eval-20260929-py`; không đổi venv ứng dụng. Gọi trực tiếp `auth.update_me` trên cùng session SQLite có thể phát sinh `MissingGreenlet`, nhưng API live đã trả 200 và mật khẩu mới hoạt động; đây là sai khác harness, không tính lỗi sản phẩm.
