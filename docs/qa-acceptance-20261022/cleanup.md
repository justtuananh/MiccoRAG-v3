# Dọn dữ liệu sau kiểm tra

Parent thực hiện sau khi cả kiểm thử chức năng và Sol audit hoàn tất, ngày22/10/2026. Đây là bước dọn dữ liệu, không thay đổi kết luận các ca đã kiểm tra.

- Qua UI nhân viên, chuyển đúng `DOC-0051 / QA-20261022-DOCS-acceptance.txt` vào thùng rác và kiểm tra nó xuất hiện trong thùng rác. Không xóa tài liệu nghiệp vụ.
- Qua UI nhân viên, xóa workspace tự sinh `personal-32`, ID17, chỉ thuộc tài khoản QA32 và đã có0tài liệu đang hoạt động. Workspace thử ID18 đã ở thùng rác từ lượt Luna. Không xóa workspace phòng ban hoặc Default Workspace.
- Qua UI Admin, tìm đúng `qa.acceptance.20261022@micco.local`, mở Vô hiệu hóa, kiểm tra modal ghi đúng tênQA, xác nhận và reload. Dòng tài khoản chuyển **Không hoạt động**. UserID32 được giữ cho nhật ký, không xóa user có sẵn.
- Đối chiếu DB chỉ đọc sau thao tácUI:0tài liệuQA hoạt động,0tri thứcQA hoạt động,0workspace thuộcQA hoạt động. Tài liệu47,48,49,50,51,52,53,54 ở thùng rác;48/50/52/53 là tài liệu được tạo từ tri thứcQA. Tri thức1/2/3/4 và workspace17/18 đã soft-delete. Giữ dữ liệu theo chính sách thùng rác30ngày; không purge hàng loạt hoặc xóa audit log.
- Luna đã xóa lịch sử chatQA tạo trong đợt và xác nhận bằng reload; không xóa chat của người dùng thật. Tổng7câu hỏi UI gửi tớiLLM; ca abort được chặn trongbrowser trướcbackend.
- Các context của các nhómchat/knowledge và Sol được đóng; parent dọn cáccontext riêng và phiênadmin thử còn lại. Phiênbootstrap ngắn hạn không phải tài khoản/mật khẩu để dùng lại ngày mai.
- Serverbootstrap localhost và cácfile chứa phiên/mật khẩu tạm được dừng/xóa ở cuối lượt; cấu hìnhMCP tạm `--isolated` được hoàn nguyên. Lần chạy song song sau vẫn phải chuẩn bị profile tách biệt theo phần hướng dẫn.
- Ảnh/log, CSV chỉ có một dòngQA và fixtureTXT nhỏ được giữ làm bằng chứng. Tệp51MB local được xóa sau kiểm tra; không từng được upload lênproduction.

Bằng chứngUI: `harness/reports/acceptance-20261022/root-cleanup-doc51-trash.png`, `root-cleanup-qa-user-disabled.png`. Sổ fixture trên đây bổ sung ID cụ thể cho phần tồn dư trong audit gốc; DOC51 **không còn active** sau cleanup. Muốn chạy lại phải tạo/restore fixture và kích hoạt/reset tài khoảnQA theo quy trìnhadmin phù hợp.
