# Sol — audit độc lập cuối, 22/10/2026

**Kết luận: NO-GO cho nghiệm thu đầy đủ ngày 23/10.** Có 2 lỗi S1 chặn thao tác cảm ứng ở viewport đã kiểm tra; đồng thời còn thiếu bằng chứng trên history, stream lỗi, chia sẻ/quyền tải trực tiếp và vòng đời phiên bản. Không phát hiện S0 trong phạm vi thực thi; điều này không chứng nhận toàn bộ hệ thống không có lỗi hoặc không có lỗ hổng.

**35 ca chuẩn: 6 PASS / 9 FAIL / 18 PARTIAL / 2 NOT_RUN.** Đây là số ID chuẩn duy nhất, không cộng các dòng biến thể của Luna/parent. FAIL nghĩa là có ít nhất một biến thể sai; PARTIAL nghĩa là đã chạy một phần nhưng chưa đủ toàn bộ tiêu chí. Một lỗi có thể ảnh hưởng nhiều ID, không nhân thành nhiều bug. Có **11 issue được chấp nhận: 2 S1 + 9 S2**; Google và quên mật khẩu là issue bổ sung của UI hiện hữu, không thêm ID vào mẫu số 35. Không có ngoại lệ S2 nào được người nghiệm thu phê chuẩn trong hồ sơ này.

Đích: https://chatbot.coremind.io.vn. Audit kết thúc khoảng 10:20 ICT. Asset trực tiếp được Sol thấy: `/assets/index-BMztbSwt.js`; image parent ghi nhận: frontend `miccorag-frontend:20260930-e16c7ae`, backend `miccorag-backend:20261021-chatfix`. Các kết quả chỉ áp dụng bản này. Đã đọc lại báo cáo knowledge bản FINAL lúc 10:17; nguồn gồm criteria, bốn báo cáo Luna, root-rechecks và common file `docs/NGHIEM_THU_UI.md`.

## Phương pháp và kiểm tra độc lập

MCP Playwright `browser_run_code_unsafe`, context/page riêng, marker `qa-sol-audit`; không điều hướng/click/đóng default page. Bootstrap chỉ khởi tạo phiên ordinary; không xuất hay lưu thông tin xác thực. Không tạo/sửa/xóa dữ liệu, không hỏi LLM, không sửa nguồn/deploy/commit. Chỉ file audit này được ghi. Context riêng đã đóng và route fault injection đã tháo.

| Kiểm tra | Role / device | Thao tác và bằng chứng UI trực tiếp | Kết quả |
|---|---|---|---|
| SOL-01 | Khách, 390×844, isMobile/touch, DPR2, zoom100% | Mở `/login`; click Đăng nhập timeout 2.5s. Nút x40/y446/w310/h48; elementFromPoint ở giữa là DIV vòng tròn của overlay z20, không thuộc nút; visualViewport.scale=1. Không cần gửi credentials để chứng minh interception. | Xác nhận B01. |
| SOL-02 | Ordinary, cùng context, 360×640 | Workspace → Tạo mới; Hủy ở y658.5..704.5 trước/sau scrollIntoView; không có vùng cuộn trong dialog; click timeout vì ngoài viewport. Escape đóng được. | Xác nhận B02. |
| SOL-03 | Ordinary, 1366×768 | Documents → tìm đúng DOC51 → Ban Giám đốc; đợi UI GET có department_id=6 hoàn tất200. Snapshot vẫn có đúng dòng QA 186B sau request. | Xác nhận B03; không phải rò dữ liệu. |
| SOL-04 | Ordinary, desktop | Chỉ chặn GET `/api/knowledge` trong page riêng, trả503 tổng hợp; UI ghi0 bài/“Chưa có tri thức nào”, không error/retry; tháo chặn sau quan sát. | Xác nhận B11 nhánh lỗi mô phỏng; không phải outage tự phát. |
| SOL-05 | Ordinary, desktop | Mở `/qa-sol-audit-unknown-20261022`, đợi networkidle; body text và ariaSnapshot đều rỗng. | Xác nhận B10. Parent cũng đã tái hiện với khách. |
| SOL-06 | Ordinary, desktop | Mở `/documents/51`: UI hiện DOC-0051, đúng filename,186B,Kỹ thuật,Nội bộ,ngày22–29/10,“Đã phê duyệt”, hoạt động upload/approve. | Xác nhận metadata/approval đúng ID; không tải file. Snapshot ban đầu có “TXT — không thể xem trực tiếp”; chưa đợi riêng nội dung preview nên không kết luận bug preview mới. |

Một lần thử giữ biến global giữa tool calls không tồn tại; đã tìm lại đúng page riêng rồi chạy tiếp. Đây là hạn chế tooling, không phải lỗi sản phẩm và không được tính thêm ca. Tổng cộng sáu recheck nghiệp vụ, không mở rộng sang toàn bộ route.

Sol đã dùng view_image xem: root-mobile-login-overlay, root-workspace-mobile-360, root-auth-invalid-visible, DOCS-empty-validation, DOCS-oversize-validation, DOCS-reject-owner-reloaded, luna-chat-doc51-citation-open, ordinary-approved-after-manager, DOCS-detail-pending, DOCS-manager-approved, DOCS-replacement-indexed, luna-auth-login-success, root-logout-mobile, workspace-in-chat-selector, knowledge-edited, root-knowledge-simulated-503. Tất cả nằm dưới `harness/reports/acceptance-20261022/`.

**Chất lượng artifact:** `DOCS-manager-approved.png` trắng, không tự chứng minh approval. Thay bằng tường thuật UI, replacement-indexed, approval-pending và SOL-06, không ghép ảnh detail DOC47 thành detail DOC51. `workspace-in-chat-selector.png` đang hiển thị KB Kỹ thuật và hội thoại DOC51, chưa chứng minh riêng workspace QA private đã được chọn; K05 giữ PARTIAL. Download DOC47/V1/V2 có so byte theo báo cáo, nhưng Sol không tải lại. Quan sát metadata request phát sinh từ UI được dùng hỗ trợ chẩn đoán, không thay thao tác UI bằng gọi API.

## Ma trận đủ 35 ID

Quy ước: desktop các worker chủ yếu1366×768, không tự chứng nhận1440×900. Phiên ordinary=QA dùng một lần; manager cùng phòng; other=QA khác phòng; Admin/manager thường khởi tạo token. Auth thành công bằng mật khẩu có bằng chứng riêng. Mọi PARTIAL bên dưới là thiếu bằng chứng, không tự xem là product failure.

| ID | Kết quả | Role / device / biến thể đã đối chiếu; phần còn thiếu | Nguồn |
|---|---|---|---|
| A01 | PASS | Khách desktop: root/protected vềlogin, landing/register/form validation tải được. Không chứng nhận đăng ký hợp lệ end-to-end. | ROOT-PUBLIC-REGISTER, Luna auth |
| A02 | FAIL | Ordinary desktop: mật khẩu đúng/sai/rỗng, show/hide và reload có bằng chứng; sai có thông báo. Mobile390 touch100% bị B01. Malformed login email/double-submit chưa đủ. | AUTH01/02, ROOT-AUTH-ERROR/PASSWORD, SOL01 |
| A03 | PARTIAL | Ordinary: logout hai tab, Back/Reload vềlogin đạt. Chưa đủ Forward, mở login khi còn phiên, token-expiry/401 recovery và Safari BFCache. | ROOT-LOGOUT/SESSION-RELOAD |
| A04 | PARTIAL | Ordinary: bốn route thật `/admin`,`/departments`,`/graph-knowledge`,`/approvals` vềdashboard. Admin admin/approvals/graph có thao tác; chưa đủ artifact route `/departments` riêng và toàn bộ menu đối chiếu. Không chứng nhận API RBAC. | ROOT-ROLES, admin/graph/docs reports |
| A05 | PARTIAL | Ordinary desktop/mobile: menu và dashboard tabs dùng được. Chưa đối chiếu toàn bộ metric, recent-document link, Back/deep-link ở mọi menu. | ROOT-DASHBOARD-TABS/MOBILE-NAV |
| A06 | PARTIAL | Admin desktop: QA search/empty/export CSV, audit mask/pagination, department search đạt. Role filter/user pagination, audit detail và departments route riêng chưa đủ. | ROOT-ADMIN-USERS/AUDIT/DEPT |
| A07 | NOT_RUN | Admin CRUD user/department + edit/reload/delete-cancel chưa được nghiệm thu thành ca. Việc parent tạo user để chuẩn bị không đủ validation/evidence vòng đời. Không chạy mutation ở audit. | Common file preparation; không có ca đầy đủ |
| A08 | PARTIAL | Ordinary desktop: profile đúng, sửa nháp/Escape/mở lại không lưu; theme reload đạt. X/save/avatar và đối chiếu theme toàn trang chưa đủ. | ROOT-PROFILE-CANCEL/THEME |
| D01 | FAIL | Ordinary desktop list/grid/search/type/status/reset đạt; department B03 sai. Admin18 tài liệu/4trang sort/pagination đạt; ordinary nhiều trang chưa có dataset. List-error branch chưa chạy. | DOCS D01, ROOT-DOC-SORT-PAGES, SOL03 |
| D02 | PASS | Ordinary desktop: TXT hợp lệ + ngày + Nội bộ tạo một tài liệu, pending rõ và reload metadata; replacement DOC51 liên kết qua duyệt/indexed/chat. | DOCS D02, SOL06 |
| D03 | FAIL | Ordinary desktop: CSV/thiếu ngày/ngày đảo bị chặn; 0B và51MiB không có client validation, Upload bật (B04/B05). Không submit hai tệp đó; backend acceptance chưa biết. | DOCS D03, ảnh empty/oversize |
| D04 | PARTIAL | Ordinary desktop DOC47: upload trùng có cảnh báo, Hủy không tạo bản thứ hai. Chưa double-click/retry và duplicate-check với nội dung ngoài quyền. | DOCS D04/observations |
| D05 | FAIL | Ordinary→manager desktop DOC51 preview/approve/reload đạt; DOC54 reject bắt buộc lý do nhưng owner reload không thấy lý do (B06). Preapproval RAG exclusion/pending_org chưa đủ. | DOCS D05, reject-owner image, SOL06 |
| D06 | PARTIAL | DOC51 approved + completed186B/1chunk, reload và chọn Completed lại đạt; không suy reset tab là reset job. Failed-job/reason và mọi biến thể status chưa đủ. | DOCS D06, replacement-indexed |
| D07 | PARTIAL | DOC47 TXT preview/metadata có ảnh; PDF20 native viewer1/1 zoom đạt. Không chuyển bằng chứng TXT47 thành TXT51; bảng/ảnh/định dạng còn lại và TXT51 preview hoàn tất chưa chứng nhận. | DOCS D07, ROOT-PDF-VIEWER, SOL06 |
| D08 | PARTIAL | Owner DOC47 current/V1/V2 tải và byte-match; other list/detail bị chặn. Share/copy-link sang context không quyền và download replacement DOC51 chưa chạy. | DOCS D08, download artifacts |
| D09 | PARTIAL | Owner desktop upload candidate V2/ghi chú/history và tải V1/V2 đã làm. V1 current khi V2 pending không phải bug; approve→indexed→effective→V2 current, metadata cancel chưa đủ. | DOCS counts/observations/version artifacts |
| D10 | PARTIAL | Owner DOC47 delete-cancel/delete/restore/delete, other list/direct-detail đạt; trash đã làm rõ là soft-delete. Other direct download/preview/version và deleted-document RAG exclusion chưa chạy. | DOCS D10/observations |
| C01 | PASS | Ordinary KB Kỹ thuật/DOC51: blank disabled, gợi ý điền composer, gửi đúng reference, analyzing→final6.1/6.8s. | Luna chat C01, answer/memory images |
| C02 | PASS | Ordinary desktop: citation[yr76] mở đúng filename và reference DOC51 hỗ trợ câu trả lời. | Citation-open image đã xem |
| C03 | PASS | Ordinary desktop: follow-up nhớ mã, câu hỏi ngày không có trong nguồn được abstain; clipboard đối chiếu đúng. Chỉ chứng nhận các câu đã hỏi. | Luna chat C03a/b/c |
| C04 | PARTIAL | Reload/history/cancel-clear và user khác không thấy QA messages đạt. Workspace A→B→A, đổi nhanh/race và logout/login persistence chưa chạy. | Luna chat C04a–d |
| C05 | NOT_RUN | Không có picker thấy được; chưa so ordinary/Admin, abort stream/error/retry, pending/cross-workspace exclusion. Không có bằng chứng để coi picker vắng mặt là N/A cho cả ca. | Luna chat C05 |
| C06 | PARTIAL | Ordinary desktop: search/cards, document link tới list có QA-owned docs. Ask-link timeout chưa có destination; không đủ chứng minh user_id filter thật. Nonsense search có kết quả chưa đủ oracle để FAIL ranking. | Luna Expert C06 |
| C07 | PARTIAL | Admin desktop: workspace data/empty/return, hover/focus/zoom/fit đạt. Pan/legend filter chưa chạy; degree0 là nghi vấn, chưa thành bug. Ordinary route denial có ROOT-ROLES. | Luna graph C07, ROOT-GRAPH-SWITCH |
| K01 | FAIL | Ordinary desktop: inline content/search/category/status/layout và other-user isolation có kiểm tra; 503 mô phỏng thành empty giả (B11). | Luna knowledge K01/K04c, SOL04 |
| K02 | PASS | Ordinary desktop: required fields/create/edit/reload/delete-cancel có UI; edit tạo successor version, không tự kết luận duplicate. HTML/script fixture không được cấp/chạy; không chứng nhận XSS hoặc loại bỏ stale versions trong retrieval. | Luna knowledge FINAL K02, edit images |
| K03 | FAIL | Ordinary→manager: internal submit/preview/approve/reload đạt, nhưng indexed vẫn ghi Chờ xử lý (B07). Preapproval RAG exclusion và đầy đủ restore retrieval chưa chứng nhận. | FINAL K03, ordinary-approved image |
| K04 | FAIL | Ordinary desktop private CRUD/filter/scope-lock/reload; public/dept403 đúng và không tạo record; other/Admin visibility đã quan sát. 390footer đạt;360footer bị B02. | FINAL K04, ROOT-MOBILE-WORKSPACE, SOL02 |
| K05 | PARTIAL | Workspace delete/cancel/restore + selector inspections có tường thuật. Một screenshot selected-workspace không khớp fixture; Documents không có workspace picker. Chưa đủ cross-page ID và quyền sau restore; không suy UI label thành ID đúng. | FINAL K05, selector artifacts |
| U01 | FAIL | Mobile390 menu/composer/upload100% có bằng chứng, workspace390footer đạt; mobilelogin B01 và workspace360 B02 không đạt. Desktop1440×900 riêng, toàn modal/mobile flow chưa đủ. | ROOT-MOBILE-NAV, Luna mobile, SOL01/02 |
| U02 | PARTIAL | Touch100% upload footer thấy được; parent CDP scale2 ghi visual195×422/footer744..784. Chưa chứng minh không thể pan/cuộn tới footer hoặc đủ metrics/reset cùng trạng thái; không chấp nhận FAIL toàn mobile/pinch từ ảnh đơn. | ROOT prior zoom; admin-upload/mobile-zoom-200 |
| U03 | PARTIAL | Enter login, profile một bướcTab/Escape, modal Hủy có bằng chứng; full Tab/ShiftTab/Space/focus-return/trap cho menu/upload/profile chưa chạy đủ. | ROOT-PROFILE-CANCEL/MOBILE-ENTER |
| U04 | PARTIAL | Modal knowledge360 cuộn được; mobile composer hiện. Chưa real keyboard, desktop browser zoom200%, Safari/iOS/Android thật. Đây là giới hạn môi trường, không product fail. | Knowledge mobile, chat mobile |
| U05 | FAIL | B10 unknown URL trắng, B11 knowledge simulated503 empty giả; workspace simulated503/error/retry đạt. Missing document ID, browser offline toàn bộ và console toàn route chưa đủ. | ROOT-UNKNOWN/KNOW-ERROR/WS-ERROR, SOL04/05 |

## Issue được chấp nhận và cách tái hiện

Đường dẫn ảnh dưới đây đều tương đối với `harness/reports/acceptance-20261022/`. Owner là nhóm đề xuất xử lý, chưa phải cam kết đã nhận việc. Tất cả còn OPEN; deadline đề xuất: trước quyết định nghiệm thu23/10. S2 chỉ được miễn khi người có quyền ghi nhận rõ owner/hạn, không tự chuyển thành PASS.

| Bug | Mức / owner | Bước → actual / expected; phạm vi | Artifact |
|---|---|---|---|
| B01 | S1 / frontend-auth | Mobile390×844 touch100% → login → chạm giữa Đăng nhập: overlay chặn pointer. Expected form nhận touch. Enter là workaround nhưng layout che cả form, không đạt login thông thường trên mobile. | root-mobile-login-overlay.png; SOL01 |
| B02 | S1 / frontend-workspace | Mobile360×640 touch100% → Workspace/Tạo mới → cuộn tới footer: Hủy/Tạo mới vẫn ngoài viewport, không vùng cuộn. Expected tiếp cận save/cancel. Escape chỉ hủy, không hoàn tất create; đổi sang thiết bị/viewport khác không hoàn thành luồng ở360. Nâng từ S2 worker vì chặn CRUD được phép. | root-workspace-mobile-360.png; SOL02 |
| B03 | S2 / backend+frontend-documents | Tìm DOC51 Kỹ thuật → chọn Ban Giám đốc → chờ200: vẫn có DOC51. Expected department filter đúng. Không có leak ngoài quyền đã chứng minh. | root-department-filter-mismatch.png; SOL03 |
| B04 | S2 / frontend-upload | Chọn TXT0B + ngày hợp lệ: không error, Upload bật. Expected validation trước submit. Chỉ kết luận client gap. | DOCS-empty-validation.png |
| B05 | S2 / frontend-upload | Chọn51MiB dù copy tối đa50MB + ngày hợp lệ: không error, Upload bật. Expected chặn rõ. Không submit; không tuyên bố server chấp nhận hoặc xử lý file lớn. | DOCS-oversize-validation.png |
| B06 | S2 / frontend+backend-documents | Manager reject DOC54 kèm lý do → owner detail/reload: chỉ Từ chối, không lý do/activity reason. Expected owner biết cách sửa. | DOCS-reject-reason-ready.png; DOCS-reject-owner-reloaded.png |
| B07 | S2 / frontend-knowledge | Duyệt knowledgeQA ID3 → owner reload: card Hoạt động nhưng Chờ xử lý; UI-triggered list diagnosis đã indexed/approved. Expected processing label đồng nhất. Không gọi approval thất bại. | ordinary-approved-after-manager.png; FINAL knowledge report |
| B08 | S2 / frontend-auth | Desktop login → Google: không destination/dialog/feedback. Expected OAuth hoặc trạng thái chưa hỗ trợ rõ. Visible control nằm trong phạm vi UI; provider end-to-end chưa xác minh. | root-auth-placeholder-actions.png; ROOT-GOOGLE |
| B09 | S2 / frontend-auth | Login → Quên mật khẩu: chỉ thêm#; expected recovery/help có ích. | root-auth-placeholder-actions.png; ROOT-FORGOT |
| B10 | S2 / frontend-routing | URL không tồn tại → body trắng, không đường quay lại; expected404 hoặc fallback rõ. | root-unknown-route.png; SOL05 |
| B11 | S2 / frontend-knowledge | Fault injection GET knowledge503 trong contextQA → UI0 bài/Chưa có tri thức nào. Expected lỗi tải/retry, không empty giả. Chỉ bug xử lý lỗi mô phỏng. | root-knowledge-simulated-503.png; SOL04 |

## Kết luận bị bác bỏ hoặc chưa đủ chứng cứ

- AUTH-03 “không báo sai mật khẩu”: bác bỏ. `root-auth-invalid-visible.png` cho thấy Đăng nhập thất bại ngoài form; locator worker quá hẹp.
- D01-SORT “sort không hoạt động”: bác bỏ. Dataset hai dòng có thể trùng newest/name order; parent18 dòng/4trang đổi sort và localeCompare('vi') đạt. Không cộng FAIL đó.
- `/admin/users` và `/knowledge-graph` trắng không chứng minh vượt/chặn quyền route thật. Dùng `/admin` và `/graph-knowledge`; URL lạ trắng thuộc B10 riêng.
- V2 pending trong khi V1 current không phải bug được chứng minh. Giữ D09 PARTIAL đến khi UI xác nhận activation; không lấy code comments thay bằng chứng.
- Knowledge edit có successor/supersedes: không gắn duplicate FAIL. Việc nhiều sibling version active/listed còn cần product xác nhận và kiểm tra retrieval; chưa hứa không có stale-source issue.
- Expert nonsense trả66/60%: chưa có policy/oracle cho no-match/fallback; chỉ quan sát chất lượng, không FAIL ranking. Ask-link và owner filter vẫn cần chạy.
- Graph degree0 dù có edges, nguồn rộng trong câu abstain trước handoff: chưa đủ chứng minh sai ngữ nghĩa; không tính bug.
- Trash DOC47/candidate: bản follow-up giải thích trống ngay sau restore, sau delete có restore actions. Không còn chứng cứ permanent delete. Giữ các thiếu sót D10 khác.
- Profile-lock trước retry là BLOCKED-TOOL đã vượt qua, không product fail. Harness20P/0F/5W chỉ smoke/deploy, không cộng vào35 ca UI.

## Phần phải chạy lại, blocker và dữ liệu tồn dư

**Không còn blocker MCP hoặc thiếu mật khẩu chung cho lượt này.** C05 và A07 là NOT_RUN; không được đổi tên thành lỗi công cụ. Ordinary multipage thiếu dataset (Admin đã kiểm tra riêng). Real mobile keyboard/Safari/Android chưa có môi trường; HTML/script fixture chưa có trong phạm vi. Không thực hiện API-only security audit.

Trước GO cần tối thiểu: sửa và retest B01/B02 ở100% đúng360/390 touch; hoàn tất C04 workspaceA→B→A/rapid-switch/logout-login và C05 abort/error/retry; D08 share/copy/direct unauthorized file/version; D09 approved-version activation; D10 direct unauthorized preview/download/version và deleted-source exclusion; K05 đúng fixture/ID và quyền sau restore; bổ sung evidence các PARTIAL khác hoặc xin ngoại lệ rõ ràng cho biến thể phụ. Kiểm tra preapproval exclusion bằng fixture phù hợp và giữ giới hạn LLM; không hỏi vô hạn để tìm câu trả lời đẹp.

Dữ liệu theo báo cáo cuối, **Sol không dọn hay thay đổi**:

- DOC51 đang active/approved/indexed,186B,KB Kỹ thuật, reference `DOCS-ACCEPTANCE-20261022-01`; Sol06 thấy đúng ID/approval. Parent quyết định cleanup sau khi kết thúc review.
- DOC47 và candidate version trong trash30ngày; DOC54 rejected trong trash. Candidate ID chưa được báo cáo rõ: parent cần bổ sung trước cleanup, không đoán ID và không purge hàng loạt.
- Knowledge IDs1/2/3/4 và `QA-20261022-WS-Luna-Private` soft-deleted trong trash; public/dept permission fixtures nhận403 nên không được tạo. Generated knowledge docs được worker báo đã không còn trong exact search; chưa chứng nhận purge vector.
- Disposable QA user cùng quyền/department được chuẩn bị cho lượt này còn tồn tại; manager/Admin/other-user sessions chỉ dùng theo cấp. Parent cần chốt user nào là tài khoản tạo mới để disable/delete đúng người. Không coi các user sẵn có là dữ liệu QA để xóa.
- Chat worker báo đã xóa riêng lịch sử QA tạo trong lượt và reload xác nhận; không xóa history tài khoản khác. Local downloads/TXT/sparse51MiB và ảnh/log còn trong artifacts; chúng không phải document51MiB trên production.

## Handoff cho common file lần chạy sau

Parent đưa phần kết luận/ma trận này vào **một common file** `docs/NGHIEM_THU_UI.md`, đánh dấu rõ các dòng worker bị supersede thay vì để FAIL cũ đứng ngang kết luận cuối. Sol chỉ sở hữu file audit này, không sửa common file.

Các bước cần thêm để common file tự chạy lại được: sổ fixture theo ID/owner/workspace/scope/current-version và lịch cleanup; endpoint bootstrap là tạm thời không phải prerequisite dùng lại ngày mai, lấy credentials qua kênh riêng; chọn đúng visible form/toàn-body error; ghi viewport/touch/DPR/zoom và thử pointer thật không force-click; dataset sort có hai thứ tự khác nhau và đọc đủ các trang; chờ đúng request/UI state thay fixed delay; download đối chiếu bytes; capture terminal screenshot không trắng; chụp selected QA workspace cùng tên/ID; nhãn rõ fault injection; U02 đủ visualViewport metrics và pan/scroll/reset; U03 full focus loop; U04 real keyboard/desktopzoom200%; ghi retry tối đa/timeouts/giới hạn LLM và trạng thái dữ liệu trước cleanup. Parent cần giữ một artifact index với tên file thực tế, vai trò, timestamp và linked canonicalID.

**NO-GO gồm cả lỗi đã xác nhận và thiếu bằng chứng luồng chính.** Ngay cả khi hạ hai mobile issue thành S2 theo ngoại lệ được chủ nghiệm thu chấp nhận, hồ sơ hiện tại vẫn chưa đủ GO vì các kiểm tra history/stream/version/access còn thiếu. Không có thay đổi nguồn hoặc triển khai nào được audit này tuyên bố đã sửa lỗi.
