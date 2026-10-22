# Kết quả mới nhất: kiểm thử prompt injection

Đã tái hiện lỗi: **SRC-04 = FAIL**. Tổng hợp kế thừa đợt trước và cập nhật mục này: **70 PASS, 1 FAIL, 45 BLOCKED**. Bản vá thử chưa đạt và chưa triển khai. Xem [báo cáo prompt injection/ngữ cảnh](runs/20260929-injection/REPORT.md).

---

# Kết quả mới nhất sau sửa

Đã triển khai và kiểm thử lại: **70 PASS, 0 FAIL, 46 BLOCKED trên 116 tiêu chí**. Chưa nghiệm thu toàn bộ vì các mục BLOCKED còn thiếu chính sách, nguồn chuẩn hoặc độ bao phủ kiểm thử. Xem [báo cáo sau sửa](runs/20260929-fix/REPORT.md) và [checklist sau sửa](runs/20260929-fix/results-checklist.csv).

---

# Kết quả trước sửa

Đã kết thúc đợt kiểm ngày 29/09/2026: **CHƯA ĐẠT**. Bộ tiêu chí v1.1 có **116 mục** (thêm SEC-25): **19 PASS, 46 FAIL, 49 BLOCKED, 2 NOT_RUN**. Xem [báo cáo đầy đủ](runs/20260929/REPORT.md) và [checklist kết quả](runs/20260929/results-checklist.csv). Phần bên dưới lưu bối cảnh thiết kế v1.0; trạng thái NOT_RUN ở phần đó không phải kết quả hiện tại. Rà soát mã tĩnh đã bổ sung thành 12 phát hiện.

---

# Bộ tiêu chí đánh giá MiccoRAG v3 — v1.0

Ngày: **2026-09-29** · Giai đoạn: **thiết kế tiêu chí, chưa thực thi đánh giá toàn hệ thống**.

Mục tiêu là trả lời bốn câu riêng biệt: **chức năng có hoạt động ổn không; logic và phân quyền có đúng không; quy trình có phù hợp nghiệp vụ không; câu trả lời có đúng và được nguồn có thẩm quyền hỗ trợ không**. Một bản build thành công hoặc câu trả lời có từ khóa không đủ để kết luận cả bốn câu.

Bộ tiêu chí được tổng hợp từ **ba agent `gpt-6-sol`** chuyên trách nghiệp vụ/phân quyền, RAG/nguồn và an toàn thông tin, cùng agent điều phối rà soát chức năng/giao diện/vận hành. Hai agent đầu xây tiêu chí; agent bảo mật thực hiện thêm rà soát mã tĩnh theo yêu cầu bổ sung, phân biệt phát hiện từ mã với lỗi đã tái hiện. Chưa chạy bộ kiểm tra mới, sửa ứng dụng, gọi mô hình trả phí hay thay đổi dữ liệu nghiệp vụ trong bước này.

**Quy mô bộ tiêu chí: 115 mục** — 33 chức năng/vận hành, 28 nghiệp vụ/phân quyền, 30 RAG/nguồn, 24 bảo mật. Mức ưu tiên: **70 P0, 41 P1, 4 P2**. Tất cả ca thực thi mới là NOT_RUN; 11 phát hiện bảo mật được ghi riêng theo bằng chứng mã tĩnh.

## 1. Cách dùng và tài liệu kèm theo

| Tài liệu | Nội dung |
|---|---|
| [functional.md](functional.md) | Chức năng UI/API, tính toàn vẹn dữ liệu, lỗi, vận hành và hiệu năng |
| [business.md](business.md) | Ma trận quyền và quy trình nghiệp vụ, phê duyệt, phiên bản và chuyển trạng thái |
| [rag.md](rag.md) | Bóc tách, truy xuất, chất lượng đáp án, trích dẫn và tính đúng nguồn nghiệp vụ |
| [security.md](security.md) | Tiêu chí kiểm tra an toàn thông tin và bằng chứng cần thu |
| [security-review.md](security-review.md) | Báo cáo rà soát mã tĩnh của agent bảo mật; không phải kết quả khai thác trên hệ thống thật |
| [checklist.csv](checklist.csv) | Danh sách tiêu chí để lọc theo ưu tiên và ghi kết quả; ban đầu đều NOT_RUN |
| [source-register.csv](source-register.csv) | Mẫu đăng ký nguồn và mức thẩm quyền, để chủ nghiệp vụ điền/duyệt |
| [golden-case.template.json](golden-case.template.json) | Mẫu một ca hỏi đáp có đáp án và nguồn chuẩn; dữ liệu minh họa, không phải ca đã duyệt |
| [result.template.json](result.template.json) | Mẫu bằng chứng cho một lần chạy test |

Mỗi tiêu chí là một **nhóm ca**. Khi thực thi, tách từng tổ hợp vai trò/dữ liệu/endpoint thành case con (`RBAC-01.director.private`, v.v.); không đánh PASS cả hàng chỉ vì đã thử một tài khoản.

## 2. Nguồn làm chuẩn và cách xử lý mâu thuẫn

Theo lựa chọn của người dùng: **dùng tài liệu dự án hiện có và đánh dấu điểm cần xác nhận**. Không dùng Internet để tự đặt quy định nội bộ MICCO.

| Loại căn cứ | Cách sử dụng |
|---|---|
| Yêu cầu trực tiếp của người dùng | Ưu tiên cao nhất trong phạm vi tính năng; đã xác nhận Ban giám đốc gồm Giám đốc và Phó giám đốc được đọc/hỏi mọi KB, gồm KB private |
| Quy tắc sản phẩm trong README, tài liệu dự án, quyết định đã xác nhận | Chuẩn tạm cho nghiệp vụ phần mềm; mâu thuẫn phải được ghi và chốt, không chọn bản nào chỉ vì dễ PASS |
| Tài liệu nguồn KB, văn bản nội bộ, phụ lục, phiên bản và ngày hiệu lực | Chuẩn cho **nội dung câu trả lời nghiệp vụ** sau khi chủ tài liệu xác nhận; một file được upload/approved kỹ thuật chưa tự chứng minh thẩm quyền nghiệp vụ |
| Mã nguồn, schema, API và cấu hình đang triển khai | Bằng chứng hệ thống đang làm gì; **không** phải bằng chứng việc đó đúng nghiệp vụ |
| Báo cáo test cũ và harness | Bằng chứng giới hạn ở phiên bản, cấu hình, dữ liệu và ca đã chạy; không thay kết quả đánh giá mới |
| Đề xuất trong bộ tiêu chí | Đánh dấu PROP/C hoặc Q-xx, cần chốt trước nghiệm thu; thiếu quyết định thì BLOCKED, không ép PASS/FAIL |

Các nhãn tương đương giữa phụ lục: `XN` = đã xác nhận; `TL/DOC` = tài liệu; `M/CODE` = đọc mã; `C/PROP` = đề xuất hoặc cần xác nhận. Phạm vi đọc rộng không đồng nghĩa quyền quản trị, sửa, xóa hay duyệt rộng hơn; các quyền ghi phải kiểm riêng theo chính sách đã có/chốt.

**Nguồn dự án đã rà soát:** `AGENTS.md`, `README.md` (phân quyền/phê duyệt), `TEST_PLAN_FE.md`, `TEST_RESULTS_FE_ROUND7.md`, `OPERATIONS.md` (đặc biệt hai mục cập nhật 2026-09-29), `harness/qa.sh`, `harness/eval/README.md`, `harness/eval/grade.py`, các route/model/service và giao diện được dẫn trong từng tiêu chí. Tài liệu cũ có cấu hình, vai trò và hành vi đã thay đổi; không tái sử dụng tài khoản/mật khẩu được ghi trong tài liệu làm dữ liệu công khai.

**Snapshot tham chiếu:** repo `/home/micco/MiccoRAG-v3`, HEAD `debbaa68b2485106e261d2b31525b47580e5640c` cộng các thay đổi chưa commit đang có, đọc ngày 2026-09-29. Vì working tree có thay đổi, SHA trên **không đủ để tái lập**; trước thực thi phải lưu diff hash và bản sao mã được kiểm tra (bảo vệ bí mật), cấu hình đã che khóa, dependency versions, index và dữ liệu snapshot.

Quy ước đường dẫn: `app/...` → `micco-backend/backend/app/...`; trong rag.md, `api/...`, `services/...`, `models/...`, `core/...` cũng nằm dưới `micco-backend/backend/app/`; `src/...` → `micco-frontend/src/...`; các đường dẫn còn lại từ gốc repo VPS. Số dòng chỉ là mốc điều hướng tại thời điểm đọc, không phải kết quả test.

## 3. Phạm vi và ma trận bắt buộc

| Chiều kiểm tra | Tổ hợp tối thiểu |
|---|---|
| Danh tính | Admin; Giám đốc; Phó giám đốc; Trưởng phòng A/B; Nhân viên A/B; nhân viên không phòng; anonymous/token lỗi |
| KB | Public; department A/B; private của mình/đồng nghiệp cùng phòng/khác phòng; KB rỗng; KB đã xóa; KB tạo mới sau khi cấp role |
| Tài liệu | Public/department/internal/private theo enum thực tế; owner/người khác; pending/pending_org/approved/rejected × pending/parsing/processing/indexing/indexed/failed |
| KnowledgeEntry | Trạng thái duyệt và ingest riêng, không mặc định trùng enum Document; pending_dept, pending_org, approved/rejected và private |
| Vòng đời | Tạo; duyệt; từ chối; retry; chỉnh sửa; thêm phiên bản; đổi visibility; chuyển phòng/hạ role; xóa; rebuild index |
| Đường truy cập | UI và gọi API trực tiếp; legacy `/api/*` và v1 `/api/v1/*`; query; chat; stream; expert; KG; file/ảnh/static; lịch sử/log |
| Nội dung nguồn | Văn bản; scan; bảng; hình; số/ngày/đơn vị; ngoại lệ; nhiều nguồn; mâu thuẫn; bản cũ/hiện hành; thiếu nguồn |

Không nhất thiết chạy tích Descartes toàn bộ. Chạy **đầy đủ tổ hợp quyết định quyền/trạng thái ở P0**, dùng pairwise cho biến thể giao diện ít rủi ro. Tạo marker riêng cho từng KB/phiên bản để phát hiện lẫn nguồn. Dữ liệu seed/demo chỉ kiểm pipeline, không chứng minh quy định MICCO là đúng.

## 4. Trạng thái, mức độ và quy tắc kết luận

- **NOT_RUN:** chưa chạy; trạng thái mặc định của toàn bộ bộ tiêu chí này.
- **PASS:** có bằng chứng đủ, kết quả khớp kỳ vọng có căn cứ đã chốt; ca AI phải kiểm cả nội dung và nguồn.
- **FAIL:** hành vi sai so với kỳ vọng đã chốt; ghi cách tái hiện, expected/actual và mức độ.
- **BLOCKED:** thiếu chuẩn nghiệp vụ, dữ liệu, công cụ hoặc điều kiện môi trường; nêu owner và điều kiện gỡ.
- **N/A:** thực sự ngoài phạm vi đã chốt, có lý do; test bị skip không tự trở thành N/A.

**P0:** lộ/vượt quyền; nguồn/số liệu/phiên bản trọng yếu sai; bỏ điều kiện nghiệp vụ quan trọng; hỏng dữ liệu; luồng cốt lõi bị chặn. **P1:** chức năng hoặc độ ổn định quan trọng. **P2:** tiện dụng và cải tiến ít rủi ro. Severity của lỗi thực tế có thể cao hơn priority của ca nếu ảnh hưởng lớn hơn dự kiến.

**Cổng nghiệm thu đề xuất:**

1. Tất cả P0 trong phạm vi đã chốt phải được chạy và PASS; không P0 FAIL/BLOCKED/NOT_RUN. Không lấy điểm trung bình để bù lỗi quyền hoặc số liệu trọng yếu.
2. Tất cả P1 phải được chạy, không có FAIL/BLOCKED chưa được xử lý hoặc ngoại lệ có owner, lý do, phạm vi và thời hạn cụ thể. Ngoại lệ không được biến thành PASS.
3. P2 báo riêng; công bố độ bao phủ và số ca chưa chạy. Chỉ dùng “đạt có điều kiện” khi nêu rõ ngoại lệ.
4. Nghiệp vụ và nguồn phải có người chịu trách nhiệm chốt oracle; nếu chưa có, kết luận **chưa đủ cơ sở đánh giá đúng nghiệp vụ**, dù unit test/build xanh.
5. Các ngưỡng chất lượng RAG ở rag.md cần khóa trước chạy. Mỗi ca P0 đúng nguồn/số liệu phải đạt 100%; ngưỡng trung bình áp dụng các tầng chất lượng chung và không nới P0.

Báo `coverage = (PASS + FAIL)/(tổng áp dụng)` và `pass_rate = PASS/(PASS + FAIL)` riêng theo nhóm/priority; mẫu số tổng áp dụng gồm BLOCKED và NOT_RUN, loại N/A đã được chốt. Nếu chưa chạy ca nào, pass_rate là **N/A**, không phải 0% hay 100%. Báo raw numerator/denominator bên cạnh tỷ lệ.

Với metric RAG, ca không có đáp án không đưa vào recall nguồn; response không có mệnh đề kiểm chứng thì claim_support là N/A nhưng vẫn chấm abstention. Một mệnh đề được xem “supported” phải đọc được nguồn chứng minh, không chỉ đúng tên file. Không trung bình micro giữa tập số liệu dễ và tập quy trình khó để che lỗi; báo cả theo câu hỏi và theo tầng.

## 5. Thiết kế dữ liệu và bằng chứng

Đề xuất khởi đầu **120 câu hỏi gốc** đã được người nghiệp vụ duyệt: 30 câu một nguồn; 20 số liệu/bảng; 15 scan/hình; 15 đa bước/nhiều nguồn; 15 phiên bản/ngày hiệu lực/xung đột; 15 không đáp án/đáp án một phần; 10 chỉ dẫn độc hại/giả nguồn. Mỗi câu có một tầng chính để tránh đếm trùng, có thể nhiều tag phụ. Đây là **kế hoạch lấy mẫu**, chưa có 120 ca đã chuẩn bị.

Phủ đủ KB có nội dung và nhóm nghiệp vụ được dùng thật; tối thiểu 5 câu/KB có nội dung được chọn, tăng cỡ mẫu nếu không đủ. KB rỗng kiểm riêng hành vi rỗng. Các role, query/chat/stream và mode tạo ra biến thể execution bổ sung, không được tính như các câu độc lập để thổi cỡ mẫu. Ca P0 bất định chạy ít nhất 3 lần cùng snapshot, lưu cả ba; một lần lỗi P0 là FAIL, không chọn lần đẹp nhất.

Chia bộ phát triển/holdout khoảng 70/30 **theo cụm tài liệu và phiên bản**, không chia ngẫu nhiên câu cùng đoạn nguồn. Cả hai tập phải có tầng trọng yếu; nếu thiếu mẫu thì bổ sung. Đây là pilot, không đủ để tuyên bố tỷ lệ lỗi thực tế bằng 0. Báo khoảng tin cậy cho tỷ lệ theo câu độc lập, tránh xem các lần lặp cùng câu là mẫu độc lập.

Mỗi execution lưu: case ID, tiêu chí cha, trạng thái, expected/actual, user/role/phòng (không token), KB/document/version IDs, thời điểm, dữ liệu và config hash, request/response đã che bí mật, chunks/context/citations, raw SSE nếu có, source spans/ảnh trang, DB state trước-sau cho ca mutation, log/request ID, người chấm và người phản biện. Các ca quy trình/số liệu trọng yếu cần một người nghiệp vụ xác nhận; AI judge chỉ hỗ trợ sàng lọc.

**Ngưỡng hiệu năng pilot đề xuất, chưa phải SLA đã cam kết:** API metadata p95 ≤ 2 giây; RAG retrieval p95 ≤ 5 giây; stream token trả lời đầu tiên p95 ≤ 10 giây (không tính heartbeat/status làm token đầu); hoàn tất câu trả lời giới hạn 800 output tokens p95 ≤ 60 giây; lỗi dịch vụ ngoài lỗi validation dự kiến < 1%. Đo 1 và 10 phiên đồng thời, ít nhất 30 lượt warm-up + 100 lượt đo mỗi cấu hình; báo cold start riêng. Cần chốt theo tài nguyên/model/độ dài tài liệu thực tế trước dùng làm cổng. Timeout tính là thất bại, không loại khỏi báo cáo. Pipeline ingest đo riêng theo định dạng/trang/MB, không áp một ngưỡng cho mọi file.

## 6. Danh sách quyết định nghiệp vụ còn mở

Không hỏi lại quyền Ban giám đốc đọc private KB; yêu cầu đó đã được xác nhận. Những điểm sau chưa được suy diễn từ quyền này:

| ID | Điểm cần chốt | Chuẩn tạm để thiết kế ca / ảnh hưởng |
|---|---|---|
| Q-01 | Public duyệt một hay hai cấp; ai duyệt cấp phòng/tổ chức; Admin có ngoại lệ gì | Mã có pending→pending_org→approved, README cũ mô tả đơn giản hơn; chưa xác nhận “đúng nghiệp vụ” bằng việc khớp mã |
| Q-02 | Ai được xem bản nháp/chờ duyệt/từ chối, preview và file gốc; nguồn trả lời có phải luôn approved+indexed | Giữ điều kiện approved+indexed cho hỏi đáp theo tài liệu dự án; quyền xem hồ sơ phục vụ duyệt phải tách khỏi quyền dùng làm nguồn |
| Q-03 | Đăng ký mở hay Admin tạo tài khoản; ai được chọn/chuyển phòng, gán role | Rà soát auth/admin hiện hành; không mặc định tên phòng là định danh quyền bền vững |
| Q-04 | Dashboard cho Ban giám đốc là toàn tổ chức hay “của tôi”; thống kê/log được xem tới đâu | Nhãn UI và API phải cùng định nghĩa; hiện có dấu hiệu trộn phạm vi |
| Q-05 | Nguồn nào có thẩm quyền; phiên bản/ngày hiệu lực; ưu tiên nguồn xung đột; bản cũ trong khi bản mới chờ duyệt | Chủ tài liệu điền source-register; không lấy “mới upload nhất” thay “đang có hiệu lực” |
| Q-06 | Xóa KB/tài liệu là mềm hay cứng; lưu phiên bản, lịch sử/citation cũ bao lâu; thời điểm dọn index/graph | Cần quy tắc nhất quán DB/file/vector/KG; mọi diễn tập trên fixture riêng |
| Q-07 | “Chuyên gia” là người upload, người soạn, chủ quy trình hay chuyên gia được công nhận; xếp hạng ra sao | Mã đang dùng uploader và số tài liệu liên quan; chưa đủ chứng minh năng lực nghiệp vụ |
| Q-08 | Hạ role/chuyển phòng có thu hồi quyền ngay không; dữ liệu và lịch sử phiên cũ xử lý thế nào | Đề xuất áp dụng quyền mới ở request tiếp theo; kiểm cache/stream hiện hữu riêng |
| Q-09 | Ai xem lịch sử chat và nhật ký của người khác; nội dung nào được lưu, thời hạn lưu | Quyền đọc mọi KB không tự cấp quyền đọc mọi hội thoại; cần chốt riêng |
| Q-10 | Sai số/làm tròn; mức đầy đủ của các bước/ngoại lệ; cách nói thiếu dữ liệu/mâu thuẫn | Exact cho số hiệu và ngày; tiền/tỷ lệ theo tolerance từng golden, không đặt ngầm |
| Q-11 | SLA, quy mô tải, backup RPO/RTO, domain chính thức và yêu cầu tự khởi động | Ngưỡng ở trên chỉ là đề xuất pilot; thiếu DuckDNS/migration row phải đánh giá ảnh hưởng triển khai thật |

## 7. Các dấu hiệu cần kiểm chứng trước tiên

Agent bảo mật đã bổ sung **11 phát hiện khi rà soát mã tĩnh** và **24 tiêu chí SEC**, trình bày trong [security-review.md](security-review.md) và [security.md](security.md). Hai phát hiện được xếp Critical có điều kiện là đọc chunks và debug chat thiếu xác thực ở tầng ứng dụng: mức độ phản ánh tác động nếu đường API tiếp cận được, **chưa xác minh đường khai thác từ Internet/gateway đang chạy**. Không coi quyền Ban giám đốc đọc mọi KB là lỗ hổng. Không có bản vá ứng dụng trong bước xây tiêu chí/rà soát này.


Đây là **quan sát khi đọc mã/tài liệu**, chưa phải báo cáo lỗi đã tái hiện:

| Điểm | Dấu hiệu | Tiêu chí kiểm chứng |
|---|---|---|
| Scope RAG/KB private | `app/api/rag.py:76` xác minh tồn tại KB; bộ lọc tài liệu còn dựa phòng, cần thử private cùng phòng | RBAC-05/06, RAG-08/09 |
| Scope đồ thị tri thức | `app/services/deep_retriever.py:88` gửi document_ids cho vector nhưng không cho KG | RAG-05/06, SRC-03 |
| Scope Expert | `app/api/expert.py:49` vẫn chỉ miễn lọc phòng cho Admin, khác helper quyền đọc Ban giám đốc | FUNC-20/21 |
| Duyệt hồ sơ | README và luồng hai cấp trong approvals chưa đồng nhất; preview/status cần thử scope từng mục | BIZ-02/03/11 |
| Chuẩn chấm hiện tại | Harness keyword/citation hiện diện chưa đo fact đúng, citation hỗ trợ hay phiên bản đúng | SRC-01/02, RAG-10/17; dùng golden do nghiệp vụ duyệt |
| API ngoài màn hình | Route process/batch/chunks/graph/static cần kiểm quyền trực tiếp, không suy từ việc menu bị ẩn | FUNC-04/12/22, RBAC-05, BIZ-10 |
| Sẵn sàng vận hành | /health và /ready trả giá trị tĩnh; screen hiện chưa tự restart sau reboot | OPS-01/05 |

## 8. Kế hoạch chạy sau khi hoàn tất tiêu chí

1. Chốt Q-xx ảnh hưởng P0, fixture và source register; tạo golden đã duyệt, xác định snapshot môi trường thử.
2. Đọc mã + chạy unit/API hợp đồng; chạy ma trận quyền với tài khoản thực, không dùng admin/dev-skip để đại diện mọi role.
3. Chạy luồng E2E upload→duyệt→index→hỏi→mở nguồn, cộng phiên bản/xóa/lỗi; thao tác ghi trên dữ liệu thử cô lập.
4. Chạy RAG golden qua query, chat và stream; đánh giá từng claim và nguồn, gồm KG và Expert; ghi usage/chi phí thực tế.
5. Chạy fault/load/restore trên môi trường phù hợp; không thử phá dependency hay restart máy production dùng chung.
6. Phản biện chéo kết quả bởi agent khác, người nghiệp vụ duyệt ca nội dung; xuất verdict theo cổng mục 4, danh sách lỗi và bước tái hiện.

Kết quả hiện tại chỉ là **bộ tiêu chí sẵn để chuẩn bị đánh giá**; chưa kết luận MiccoRAG ổn, đúng hay đạt nghiệm thu toàn diện.
