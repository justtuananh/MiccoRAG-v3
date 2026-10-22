# Checklist nghiệm thu miccoRAG — 22/10/2026

Đích: https://chatbot.coremind.io.vn — phục vụ nghiệm thu ngày 23/10/2026. Đây là **tiêu chí**, chưa có ca nào được xác nhận PASS. Một checklist chung cho bốn nhóm Luna; Sol duyệt bằng chứng và quyết định cuối cùng. Mã local có thể khác bản production: ghi nhận khác biệt, không suy ra hành vi live từ mã.

## Quy tắc thực hiện và ghi kết quả

- Thực hiện qua MCP Playwright như người dùng: mở trang, bấm, nhập, chọn tệp, theo dõi kết quả. Đọc mã/API hỗ trợ chẩn đoán không thay thế thao tác UI. Không sửa code, deploy hoặc thay cấu hình server trong lượt nghiệm thu.
- Mỗi nhóm dùng phiên/browser context riêng và tài khoản QA được parent cấp; không giành shared profile. Lỗi khóa profile là `BLOCKED-TOOL`, không phải lỗi ứng dụng. Parent đã báo cấu hình MCP `--isolated`; mỗi nhóm phải xác nhận công cụ thực sự chạy trước khi kiểm thử. Không sửa cấu hình để tự giải quyết ngoài phạm vi.
- Parent đã tạo tài khoản thường QA dùng một lần qua Admin UI. Dùng tài khoản đó để kiểm tra quyền thường; phiên Admin không thay thế kiểm thử quyền thường. Không ghi mật khẩu, token, hash, dữ liệu nhạy cảm vào báo cáo/ảnh.
- Pha lập tiêu chí chỉ đọc mã, không thay đổi production. Ở pha thực thi, chỉ CRUD trong tài khoản/workspace/tệp QA mà parent cho phép, tiền tố `QA-20261022-<nhóm>-<tên>`. Không sửa/xóa/duyệt dữ liệu nghiệp vụ sẵn có. Thiếu quyền hoặc fixture thì BLOCKED; không tự mở rộng phạm vi. Chat có thể lưu lịch sử/tốn LLM: dùng workspace QA, tối đa 3 câu hỏi cho mỗi kịch bản RAG, không lặp vô hạn.
- Trạng thái từng ca: `NOT-RUN`, `PASS`, `FAIL`, `BLOCKED-TOOL`, `BLOCKED-DATA`, `BLOCKED-AUTH`, `N/A`. Chỉ PASS khi đủ bước và bằng chứng. Ca mới chạy một phần giữ BLOCKED và ghi phần đã kiểm tra. N/A cần Sol chấp nhận lý do; tính năng đang có nút nhưng hỏng không phải N/A.
- Mức độ khi sai: `S0` rò dữ liệu/vượt quyền/mất dữ liệu; `S1` chặn luồng chính đăng nhập, upload, duyệt, đọc tài liệu, RAG hoặc CRUD được phép; `S2` lỗi có cách đi vòng hữu dụng, thiếu khả năng tiếp cận; `S3` thẩm mỹ. Có thể nâng mức theo tác động thực tế, ghi lý do.
- Mỗi ca ghi: ID + biến thể, người chạy, thời gian/múi giờ, URL, vai trò (nguồn phiên: mật khẩu hay cấp sẵn), viewport/isMobile/zoom, fixture ID, bước thực tế, expected, actual, trạng thái, severity nếu lỗi, đường dẫn bằng chứng, blocker/cleanup. Không dùng câu chung “mọi chức năng tốt”.
- Bằng chứng tối thiểu: snapshot hoặc ảnh cho điểm kết thúc; lỗi có ảnh, bước tái hiện, lỗi console/network liên quan (đã che bí mật), HTTP status khi có. Ca thay đổi dữ liệu cần trước/sau và tải lại xác nhận. Download cần tên tệp, kích thước, mở đọc/đối chiếu nội dung. RAG cần câu hỏi, câu trả lời và đoạn nguồn đối chiếu. Không cần lưu toàn bộ nội dung tài liệu thật.
- Mỗi bước tải trang/dữ liệu chờ tối đa 30 giây, chat tối đa 120 giây, xử lý tệp nhỏ tối đa 5 phút; ghi thời gian thực tế. Quá giới hạn ghi timeout và trạng thái còn lại; không tuyên bố thất bại xử lý vĩnh viễn nếu job vẫn đang chạy. Retry một lần nếu cần và giữ cả bằng chứng lần đầu.
- Các nhóm lưu báo cáo riêng dưới thư mục này, cùng tham chiếu ID dưới đây; không sửa tiêu chí hoặc báo cáo của nhóm khác. Không chia sẻ tài khoản giữa nhóm khi đang đăng xuất/đổi phiên. Bàn giao fixture phụ thuộc bằng ID và trạng thái rõ ràng.

## Ma trận bao phủ từ route thực tế

Nguồn đã đọc: `micco-frontend/src/App.jsx`, `layouts/DashboardLayout.jsx`, `utils/roles.js`, `utils/api.js`, `context/AuthContext.jsx`, các page bên dưới; backend `core/permissions.py`, `models/document.py`. API dùng cả `/api/*` và `/api/v1/*` trong cùng backend; không giả định hai backend riêng. Route không có menu vẫn phải thử trực tiếp.

| Nhóm Luna | Route / phạm vi | Vai trò bắt buộc | Ca sở hữu |
|---|---|---|---|
| A — auth/mobile/admin | `/`, `/landing`, `/login`, `/register`, `/dashboard`, `/admin`, `/departments`; điều hướng, hồ sơ, mobile/keyboard | Khách + thường QA + Admin | A01–A08, U01–U05 |
| B — docs/approval/status | `/documents`, `/documents/:id`, `/approvals`, `/processing-status` | Thường QA + người duyệt được cấp | D01–D10 |
| C — chat/expert/graph | `/chat`, `/expert`, `/graph-knowledge` | Thường QA + Admin cho graph | C01–C07 |
| D — knowledge/workspace | `/knowledge`, `/workspaces` | Thường QA + Admin khi cần quyền | K01–K05 |

Quyền route trong mã: các route nghiệp vụ cần đăng nhập; `/approvals` cho Admin/Trưởng phòng/Giám đốc/Phó giám đốc; `/admin`, `/departments`, `/graph-knowledge` chỉ Admin. Người thường mở trực tiếp route đặc quyền phải bị chặn/chuyển dashboard và không nhận dữ liệu đặc quyền. Các phép đọc cụ thể vẫn phụ thuộc chủ sở hữu/phòng ban/phạm vi; “public” nội bộ không đồng nghĩa công khai cho khách Internet. A kiểm tra chặn route; nhóm tính năng kiểm tra phạm vi dữ liệu.

## A — Auth, dashboard, quản trị (mỗi ca bắt đầu NOT-RUN)

| ID | Bước cụ thể | Kết quả mong đợi | Mức độ nếu sai |
|---|---|---|---|
| A01 | Context sạch mở `/`, `/login`, `/register`, `/landing`; mở `/documents` và một route Admin khi chưa đăng nhập. | Root tới login; landing và form hiển thị; route bảo vệ về login, không ló dữ liệu. Chuyển login/register hoạt động. | S1; lộ dữ liệu S0 |
| A02 | Đăng nhập bằng mật khẩu QA hợp lệ qua form; thử mật khẩu sai một lần, trường rỗng/email sai; reload sau đăng nhập. | Sai có thông báo, không cấp phiên; đúng tới dashboard, tên/vai trò đúng và giữ phiên sau reload; không gửi trùng khi bấm liên tiếp. | S1 |
| A03 | Với phiên đã đăng nhập mở login; logout; Back/Forward/reload vào dashboard và route Admin; nếu có hai tab cùng tài khoản, kiểm tra tab còn lại. | Login chuyển dashboard khi còn phiên; logout chặn đọc dữ liệu ở mọi tab/back cache. Hết hạn/401 phải về login, không hiện danh sách rỗng giả thành công. Mô phỏng hết hạn chỉ trong context QA, ghi rõ mô phỏng. | S0 nếu lộ; khác S1 |
| A04 | Người thường mở trực tiếp `/admin`, `/departments`, `/graph-knowledge`, `/approvals`; đối chiếu menu. Admin mở các route được cấp. | Người thường không có dữ liệu/nút đặc quyền; Admin truy cập đúng. Không coi ẩn menu là đủ bằng chứng phân quyền. | S0 |
| A05 | Dashboard: đọc thống kê, đổi từng tab, mở tài liệu gần đây; đi toàn bộ menu, Back và reload deep link. | Không trang trắng/404 bất ngờ; tab/menu active đúng, số liệu hợp lý và theo quyền; link mở đúng tài liệu. Liệt kê route chỉ truy cập được bằng URL. | S1 nếu chặn luồng; khác S2 |
| A06 | Admin: mở danh sách user, tìm QA, lọc vai trò/phân trang; mở log và chi tiết; mở tab phòng ban và `/departments`. | Bộ lọc/đếm/trang nhất quán, không crash; chi tiết log đọc được. Không đọc sâu dữ liệu cá nhân ngoài nhu cầu QA. | S2; lộ quyền S0 |
| A07 | Trong phạm vi được phép: tạo/sửa user hoặc phòng ban QA, xác nhận reload; mở modal xóa rồi Hủy. Nếu parent đã tạo user, vẫn ghi riêng bước tự thực thi. | Validation rõ, dữ liệu lưu đúng, Hủy không xóa; không tự nâng quyền tài khoản thường. Thao tác chưa được phép là BLOCKED-DATA. | S1 |
| A08 | Mở menu tài khoản/hồ sơ, kiểm tra tên/phòng ban; đóng bằng X/Escape; đổi dark/light và reload. Chỉ lưu thay đổi hồ sơ QA khi được phép, không đổi mật khẩu chung. | Modal hoạt động, dữ liệu đúng, theme đọc được và duy trì theo thiết kế; không thay dữ liệu khi chỉ đóng. | S2 |

**Cổng bằng chứng đăng nhập:** token Admin được parent cấp/mint từ user DB chỉ chứng minh luồng phiên đã đăng nhập; không PASS A02. Mật khẩu DB là hash, không thể coi đó là mật khẩu thật hoặc thử đăng nhập bằng hash. Nếu chưa có mật khẩu dùng được, A02 là `BLOCKED-AUTH`; ghi rõ tài khoản thường QA có/không đăng nhập qua form. Không được suy ra “login tốt” từ `/auth/me` thành công. Register có thể kiểm tra form/validation không submit; tạo tài khoản mới chỉ khi parent cho phép, nếu chưa thử submit phải ghi thiếu bao phủ.

## B — Tài liệu, duyệt, tiến trình

Fixture: tệp TXT/PDF nhỏ chứa câu duy nhất dễ đối chiếu; ngày hiệu lực hợp lệ; ghi workspace/phạm vi/chủ sở hữu. Mã upload chính quảng bá PDF/TXT/DOCX/PPTX/MD, tối đa 50MB; form phiên bản còn nhận XLSX. Kiểm tra đúng lời hứa UI live, không tự coi XLSX được hỗ trợ mọi luồng.

| ID | Bước cụ thể | Kết quả mong đợi | Mức độ nếu sai |
|---|---|---|---|
| D01 | Mở danh sách, chuyển bảng/thẻ; tìm một tên tồn tại rồi chuỗi không tồn tại; lọc loại/trạng thái/phòng ban và xóa bộ lọc. | Kết quả khớp, giữ đúng quyền, empty state rõ; lỗi tải không bị trình bày thành không có tài liệu. | S1; phụ S2 |
| D02 | Mở upload, chọn tệp nhỏ hợp lệ; điền phạm vi/phòng ban/ngày hiệu lực theo form, submit một lần; reload danh sách. | Footer/nút gửi tiếp cận được; một tài liệu được tạo, tên/metadata đúng, có tiến độ hoặc trạng thái chờ duyệt rõ; không báo indexed khi chỉ upload xong. | S1 |
| D03 | Chọn loại không hỗ trợ, tệp rỗng, ngày hết trước ngày hiệu lực; kiểm tra thiếu trường; thử tệp quá giới hạn chỉ nếu fixture/quyền cho phép. | Validation rõ, không toast thành công giả, có thể sửa và gửi lại. Không gửi tệp lớn thật chỉ để tạo tải production. Từng biến thể thiếu fixture ghi BLOCKED-DATA. | S2; chặn tệp hợp lệ S1 |
| D04 | Upload lại cùng fixture QA một lần; quan sát cảnh báo trùng/panel kiểm tra trùng nếu có; Hủy thao tác không cần thiết. | Không tạo âm thầm nhiều bản do double-click/retry; cảnh báo/biện pháp xử lý phù hợp; không lộ tên/nội dung tệp ngoài quyền qua duplicate check. | S1; rò dữ liệu S0 |
| D05 | Với tài liệu thường QA: kiểm tra trước duyệt; người duyệt mở preview, duyệt fixture phù hợp; fixture thứ hai từ chối với lý do. | Chưa duyệt không tham gia RAG; đúng người có quyền duyệt, trạng thái/lý do/badge cập nhật sau reload. Nếu có `pending_org`, không coi duyệt cấp phòng là hoàn tất duyệt tổ chức; không tự duyệt dữ liệu thật. | S1; vượt quyền S0 |
| D06 | Theo dõi cùng ID trên documents/status/approvals, refresh, đổi tab all/active/completed/failed theo UI. | Phân biệt pending/parsing/processing/indexing/indexed/failed và approval; thành công cuối cần indexed + approved, không bắt buộc nhìn thấy mọi bước thoáng qua. Lỗi có lý do; refresh không reset tiến trình. Job quá thời gian ghi timeout, không restart hệ thống. | S1 |
| D07 | Mở detail fixture, đọc preview/markdown/PDF theo loại; kiểm tra tiêu đề/metadata/version; quay lại list. | Đúng tài liệu, ký tự Việt/bảng/ảnh fixture đọc được, loading/error có lối thoát; không spinner vô hạn. | S1 |
| D08 | Tải file hiện tại và phiên bản QA sẵn có, mở bản tải; sao chép link/chia sẻ và mở trong context không quyền. | File đúng tên/nội dung/phiên bản; link không cấp quyền ngoài chính sách, không chỉ tải HTML lỗi. | S1; rò dữ liệu S0 |
| D09 | Nếu được phép, upload phiên bản mới fixture với ghi chú/ngày; reload lịch sử, tải cả hai phiên bản; mở sửa metadata rồi Hủy. | Lịch sử/phiên bản hiện tại đúng, file cũ còn đúng, version mới tuân thủ duyệt/phạm vi; Hủy không lưu. | S1 |
| D10 | Với hai user/phòng ban QA hoặc fixture riêng: người không quyền thử detail/download/preview/version; mở xóa rồi Hủy. Xóa/khôi phục chỉ fixture QA được phép. | Không lộ dữ liệu qua URL trực tiếp; Hủy giữ nguyên; xóa/khôi phục nhất quán và tài liệu bị xóa không được RAG dùng. Thiếu user đối chiếu là BLOCKED-AUTH. | S0; luồng QA lỗi S1 |

## C — Chat/RAG, chuyên gia, graph

| ID | Bước cụ thể | Kết quả mong đợi | Mức độ nếu sai |
|---|---|---|---|
| C01 | Mở chat, chọn workspace QA, gửi câu hỏi có đáp án trong D06 đã indexed+approved; quan sát streaming đến kết thúc. | Đúng workspace, không gửi rỗng/trùng, nội dung Việt rõ, trạng thái gửi kết thúc; trả lời phù hợp fixture. Chưa có fixture đạt điều kiện là BLOCKED-DATA, không PASS bằng lời chào. | S1 |
| C02 | Bấm citation trong câu trả lời, mở nguồn/đoạn trích, đối chiếu câu khẳng định và tài liệu gốc. | Citation trỏ đúng tài liệu truy cập được và hỗ trợ nội dung; không bịa nguồn, không lộ tài liệu ngoài quyền. | S1; lộ dữ liệu S0 |
| C03 | Hỏi tiếp “quy định đó áp dụng khi nào?” theo fixture; hỏi một thông tin không có trong nguồn. | Giữ đúng ngữ cảnh; thiếu căn cứ nói rõ giới hạn, không tự khẳng định dữ kiện trái nguồn. Đánh giá theo ý nghĩa, không so khớp nguyên văn câu trả lời. | S1 |
| C04 | Reload, đổi workspace A→B→A; logout/login lại cùng user và thử user QA khác nếu được cấp; mở modal xóa lịch sử rồi Hủy. | Lịch sử đúng user/workspace, không ghi đè bởi request cũ khi đổi nhanh; reload và logout không âm thầm xóa lịch sử; Hủy không mất dữ liệu. Không xóa lịch sử chung. | S0 nếu lộ; khác S1 |
| C05 | Kiểm tra chọn tài liệu/mode nếu UI có; thường so với Admin; thử lỗi mạng/stream ngắt chỉ bằng chặn request trong context QA rồi khôi phục. | Phạm vi/mode theo quyền; không dùng tài liệu chưa duyệt/khác workspace. Stream lỗi có thông báo, không đánh dấu hoàn tất giả và có thể gửi lại. Mô phỏng phải gắn nhãn, không tính là lỗi live tự phát. | S1; lộ dữ liệu S0 |
| C06 | Expert: chọn workspace, tìm chủ đề fixture, mở thẻ/kết quả, bấm đi tới chat/tài liệu. | Kết quả có cơ sở theo dữ liệu được phép; link/context đúng; nếu link có `user_id`, danh sách tài liệu thực sự phải lọc tương ứng. Không có kết quả hiển thị rõ; thiếu fixture chuyên gia không chứng minh ranking PASS. | S2; chặn chính S1 |
| C07 | Admin mở graph, chọn workspace có dữ liệu, tương tác node/pan/zoom/filter nếu có; đổi workspace rỗng rồi quay lại. | Đồ thị/detail khớp workspace, không dữ liệu cũ sót, empty/error rõ, UI vẫn dùng được; người thường bị chặn theo A04. Không chạy build graph production. | S2; rò dữ liệu S0 |

## D — Tri thức và workspace

| ID | Bước cụ thể | Kết quả mong đợi | Mức độ nếu sai |
|---|---|---|---|
| K01 | Knowledge: tìm mục có thật/không có; mở chi tiết; kiểm tra lọc/phạm vi theo UI. | Nội dung và kết quả khớp, không lộ draft/khác phòng ban ngoài quyền, empty/error phân biệt. | S1; lộ dữ liệu S0 |
| K02 | Tạo tri thức QA (tiêu đề/nội dung/phạm vi hợp lệ), thử trường bắt buộc trước; sửa fixture và reload; mở xóa rồi Hủy. | Validation rõ, chỉ một mục được lưu, cập nhật tồn tại sau reload; Hủy không xóa. Nội dung chỉ đọc không chạy HTML/script khi có fixture an toàn được phép. | S1; thực thi mã S0 |
| K03 | Người thường gửi tri thức QA qua luồng duyệt nếu UI hỗ trợ; bàn giao ID cho B kiểm tra tab knowledge/preview/duyệt; sau đó kiểm tra lại. Xóa/restore chỉ fixture được phép. | Phân biệt trạng thái duyệt và ingest; chưa duyệt chưa thành nguồn RAG; preview/render đúng, duyệt và trash không làm mất dữ liệu ngoài fixture. Thiếu lượt duyệt là BLOCKED, không PASS lifecycle. | S1; vượt quyền S0 |
| K04 | Workspace: list/search/lọc phạm vi, mở create; tạo workspace QA, reload, sửa tên/mô tả; kiểm tra loại/phạm vi khi sửa. | Chỉ thấy workspace được phép, create/update tồn tại; mã hiện tại khóa đổi phạm vi workspace đã tạo, UI live cần rõ ràng và nhất quán. Không đổi scope dữ liệu thật. | S1; vượt quyền S0 |
| K05 | Vào workspace QA từ chat/docs/expert nếu có; so user khác; mở delete rồi Hủy; nếu được phép xóa/restore workspace QA và reload. | Các trang thống nhất tên/ID/quyền, Hủy giữ nguyên; xóa có xác nhận và không xóa tài liệu/workspace khác; restore không mở rộng quyền. | S1; mất/lộ dữ liệu S0 |

## U — Thiết bị, bàn phím, modal, lỗi (A sở hữu; nhóm khác bổ sung bằng chứng)

| ID | Bước cụ thể | Kết quả mong đợi | Mức độ nếu sai |
|---|---|---|---|
| U01 | Desktop 1440×900, mobile 390×844 `isMobile:true` ở zoom 100%; mở menu, documents/upload, chat composer, knowledge/workspace modal. | Nội dung/nút chính không bị che/cắt; mobile menu mở/đóng và chọn route được; cuộn tới mọi điều khiển, không phải thu nhỏ để thao tác. | S1 nếu không hoàn thành; khác S2 |
| U02 | Cùng context mobile mở upload 100%, chụp footer; pinch/page scale 200%, ghi `visualViewport` và vị trí footer, thử pan/cuộn tới footer, reset 100%. | Tách hai biến thể. Known case: **100% footer upload thấy được; isMobile=true pinch200% làm visualViewport còn khoảng một nửa và footer nằm ngoài vùng nhìn thấy**. Chỉ kết luận lỗi ở tổ hợp tái hiện; ngoài vùng nhìn ban đầu chưa đủ chứng minh không tiếp cận được. Ghi có/không pan/cuộn tới được, mức ảnh hưởng. Không gọi “toàn bộ mobile hỏng”. | S2 mặc định; S1 nếu chặn hoàn tất không có cách đi vòng |
| U03 | Dùng Tab/Shift+Tab/Enter/Space/Escape qua login, menu, upload, modal hồ sơ/xác nhận; đóng modal và kiểm tra focus. | Focus thấy rõ, thứ tự hợp lý, thao tác chính được bằng bàn phím; modal giữ focus bên trong, Escape theo trạng thái an toàn, đóng trả focus; không submit/xóa khi Hủy. | S2; thao tác mất dữ liệu S0 |
| U04 | Mobile focus input để bật bàn phím nếu môi trường hỗ trợ; thử cuộn modal dài; desktop browser zoom 200% riêng. | Input/footer/composer còn tiếp cận được; không nhầm desktop zoom với pinch mobile. Giả lập không có bàn phím thật phải ghi giới hạn, không PASS phần chưa thử. | S2; chặn chính S1 |
| U05 | Trong context QA mô phỏng offline hoặc abort một request danh sách rồi retry; mở ID không tồn tại và URL lạ; quan sát console trên route chính. | Có thông báo phù hợp và đường quay lại/retry, không thành công giả/empty giả, không lộ stack/secrets; điều hướng khác vẫn dùng được. URL lạ trắng là lỗi trải nghiệm, nâng mức nếu làm mắc kẹt. | S2; chặn chính S1 |

U02 cần ghi: viewport cấu hình, `isMobile`, DPR, `innerWidth/innerHeight`, `visualViewport.width/height/scale/offsetTop/offsetLeft`, `getBoundingClientRect()` footer, screenshot 100% và 200%; đối chiếu cùng trạng thái modal. Không báo PASS pinch chỉ vì đổi viewport nhỏ hoặc desktop zoom. Nếu MCP không hỗ trợ pinch, phần đó BLOCKED-TOOL và giữ known case như thông tin cần xác minh, không tự chứng nhận đã sửa.

## Sol audit và điều kiện GO / NO-GO

1. Parent thu đủ bốn báo cáo và artifact rồi giao **một lượt Sol review mới**. Các lượt khóa shared profile ban đầu được ghi BLOCKED-TOOL; lượt thay thế phải có bằng chứng thực thi mới, không chuyển kết quả cũ thành PASS theo suy đoán.
2. Sol đối chiếu từng ID/biến thể với checklist; lập bảng PASS/FAIL/BLOCKED/NOT-RUN/N/A theo nhóm, vai trò, desktop/mobile. Không lấy tổng PASS của harness/local test làm bằng chứng nghiệm thu production UI. Ghi build/version production nếu biết và mọi giới hạn chưa đối chiếu được.
3. Audit 100% S0/S1 và blocker; xem artifact của A02/A03/A04, D02/D05/D06/D08/D10, C01/C02/C04, K02/K04/K05, U01/U02. Kiểm tra ID fixture liên kết qua upload→duyệt→indexed→RAG, không ghép bằng chứng từ tài liệu khác. Mỗi nhóm phải có ít nhất một bằng chứng thao tác UI thực tế; báo cáo toàn mô tả mã/API chưa đủ.
4. Bằng chứng thiếu/mâu thuẫn: trả về BLOCKED/chưa xác minh, chỉ định bước chạy lại có giới hạn. Mỗi lỗi có severity, tác động, cách tái hiện, artifact, owner; trùng lỗi gộp issue nhưng giữ các test ID. Không giảm severity chỉ vì là lỗi đã biết.
5. **GO** khi tất cả ca áp dụng đã có bằng chứng đủ, không còn S0/S1, không còn BLOCKED/NOT-RUN trên luồng chính: login mật khẩu và session, quyền thường, upload→duyệt→indexed→xem/tải→RAG/citation/history, CRUD knowledge/workspace, mobile 100%. Ca S2/S3 hoặc phần phụ ngoài luồng chính còn thiếu phải được người có quyền nghiệm thu chấp nhận ngoại lệ rõ ràng, ghi owner/hạn xử lý; Sol không tự coi là PASS.
6. **NO-GO** nếu có S0/S1 chưa xử lý, hoặc thiếu bằng chứng/khả năng chạy luồng chính kể trên. Phân biệt “NO-GO vì lỗi đã xác nhận” với “NO-GO vì chưa đủ bằng chứng”; không diễn giải BLOCKED do mật khẩu/công cụ thành lỗi sản phẩm. Chỉ có token mint và thiếu A02 thì chưa đủ ký GO đầy đủ.
7. Nếu U02 chỉ lỗi pinch200% trong khi U01 100% đạt, ghi ngoại lệ đúng phạm vi và khả năng đi vòng; không NO-GO toàn mobile theo suy luận. Nếu xác nhận nút gửi không thể tiếp cận và chặn tác vụ thì áp quy tắc S1. Không hứa GO trước khi có dữ liệu thực thi.

Mẫu dòng kết quả để tái sử dụng: `ID | biến thể/role/device | status | actual | severity | evidence | blocker/cleanup`. Báo cáo cuối ghi rõ số ca chưa chạy và giới hạn, không chỉ tỷ lệ PASS.
