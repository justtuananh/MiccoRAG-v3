from pathlib import Path
import json,csv
from collections import Counter
P=Path(__file__).parent;old=P.parent/'20260929'
base=json.loads((old/'all-results.json').read_text())['records']
records={r['criterion_id']:dict(r,previous_status=r['status']) for r in base}
for filename in ['security-fix-results.json','rag-fix-results.json']:
 for r in json.loads((P/filename).read_text())['records']:
  original=records[r['criterion_id']];records[r['criterion_id']]={**original,**r,'previous_status':original['previous_status']}

def set_result(cid,status,actual,evidence,limitations=''):
 records[cid].update(status=status,actual=actual,evidence=evidence,limitations=limitations,scope='Đánh giá lại bản sửa; chi tiết môi trường nêu trong bằng chứng')

# Retest prior business matrix with the newly shared KB policy.
for r in records.values():
 if r['group']=='business':
  if r['status']=='PASS':
   r.update(actual='Kiểm tra lại trên ORM/handler thật, SQLite cô lập: ma trận 161/161 đạt; giữ giới hạn chính sách đã ghi.',evidence='business-sqlite-raw.json; business_sqlite_probe.py')
  else:
   r['actual']='Đợt trước: '+str(r.get('actual',r.get('evidence','')))+' Phần quyết định nghiệp vụ/luồng đầy đủ chưa có bằng chứng mới để nghiệm thu.'
set_result('RBAC-02','PASS','Cả hai vai trò lãnh đạo đọc chunk và query KB private mới qua gateway; Giám đốc chat trả đúng nguồn thử. Ma trận ORM kiểm KB private của hai chủ sở hữu.','live-postfix-results.json; business-sqlite-raw.json; pytest-final.log','Live chỉ một KB thử; chat live dùng Giám đốc, nhánh quyền Phó giám đốc kiểm thêm trong ma trận cô lập.')
set_result('RBAC-05','PASS','Chặn tài liệu gắn public bên trong KB private của người khác ở API; kiểm quyền KB trước quyền tài liệu.','pytest-final.log; security-fix-results.json')
set_result('RBAC-06','PASS','Chunks yêu cầu xác thực và quyền tài liệu; khách 401 qua backend và gateway, nhân viên ngoài KB 403.','live-postfix-results.json; pytest-final.log')
set_result('RBAC-07','PASS','ID không được phép bị loại; tập rỗng không được hiểu là truy xuất toàn KB.','pytest-final.log; security-fix-results.json','Kiểm tamper/empty scope bằng fixture cô lập; không dùng dữ liệu người khác để khai thác live.')
set_result('BIZ-05','PASS','Chủ sở hữu đọc/query được tài liệu private không gắn phòng ban; người khác bị chặn.','business-sqlite-raw.json; pytest-final.log')
set_result('BIZ-12','PASS','Upload dùng phòng ban phía server cho người dùng thường; giả phòng ban không tạo quyền tự duyệt ngoài phạm vi.','pytest-final.log; security-fix-results.json','Admin vẫn giữ lựa chọn phòng ban theo hành vi hiện có.')

functional_pass={
 'FUNC-01':('Đăng nhập đúng/sai được kiểm lại trên tài khoản thử; JWT thật cho các vai trò, không token 401; không tự nâng Admin.','stage-auth-profile-results.json; live-postfix-results.json; pytest-final.log'),
 'FUNC-03':('Đăng ký/đổi tên/đổi mật khẩu được kiểm lại; avatar giả bị từ chối, ảnh hợp lệ mã hóa lại và lỗi commit không mất ảnh cũ.','stage-auth-profile-results.json; pytest-final.log'),
 'FUNC-04':('55/55 tuyến theo 5 vai trò đúng; quản trị chỉ Admin, không còn 403 do giao diện cấp nhầm quyền. Backend chặn gọi trực tiếp trái quyền.','frontend-stage-browser.json; pytest-final.log'),
 'FUNC-05':('Tạo/sửa/xóa KB thử thành công; kiểm quyền danh sách/chi tiết và tạo KB qua ma trận ORM.','live-postfix-results.json; business-sqlite-raw.json',''),
 'FUNC-11':('Kiểm API tên Unicode/loại/phòng ban/category; UI lọc tag/trạng thái/sắp xếp và loại phản hồi cũ; tìm quy trinh trả đúng 3 tên có dấu trên staging.','pytest-final.log; frontend-security-browser.json; frontend-stage-search.json'),
 'FUNC-12':('Đọc, tải và preview kiểm quyền KB/tài liệu; tải TXT thử giữ đúng hash; endpoint ảnh kiểm bearer và chủ sở hữu.','live-postfix-results.json; pytest-final.log'),
 'FUNC-16':('Complete hoàn tất; EOF sớm, lỗi SSE và HTTP503 báo lỗi/đáp án dở, không POST dự phòng. Cleanup DB vẫn chạy khi client hủy.','frontend-stage-faults-mobile.json; pytest-final.log'),
 'FUNC-17':('Danh tính ghi lịch sử lấy từ JWT; giả user_id không chèn lịch sử người khác; nguồn đã thu hồi không trả lại trong history.','pytest-final.log; security-fix-results.json'),
 'FUNC-18':('22/22 đáp án pilot ánh xạ citation đúng; query/chat/stream dùng tên tài liệu hiện tại, UI click theo ID.','rag-graded-answers.json; src02-proof.json; frontend-security-browser.json'),
 'FUNC-19':('Các điểm render nội dung không tin cậy được khử HTML; payload thử không thực thi trong Chromium.','frontend-security-browser.json; security-fix-results.json'),
 'FUNC-21':('Expert dùng chung quyền KB và tập tài liệu với RAG; tập rỗng không gọi vector.','pytest-final.log; security-fix-results.json'),
 'FUNC-22':('Graph lọc theo toàn bộ nguồn góp vào nút/cạnh; loại nguồn thiếu ánh xạ hoặc trộn nguồn cấm.','pytest-final.log; security-fix-results.json'),
 'OPS-01':('Readiness thật kiểm DB/vector; fixture mất từng dependency trả503; live sau triển khai trả200 với cả hai checks=true.','pytest-final.log; deployment-result.json; live-harness.log'),
 'OPS-02':('Staging sao chép cấu hình provider và index đã kiểm; vector hai KB khớp387/388chunks; không xuất khóa. Build và RAG thực dùng cấu hình này.','copy_stage_vectors.py; rag-fix-report.md; deployment-result.json'),
 'OPS-06':('Harness không nuốt child exit lỗi/thiếu summary/collection lỗi thành PASS; báo technical gate thay vì GO toàn hệ thống; DuckDNS thiếu được phân loại tùy chọn minh bạch.','harness-regressions.json; live-harness.log'),
 'OPS-07':('Snapshot giữ nguyên dirty baseline, kiểm hash trước/sau 56 tệp; bản sao source/dependency và log triển khai có thể đối chiếu.','change-manifest.json; deployment-result.json; REPORT.md'),
}
for cid,values in functional_pass.items():
 actual,evidence=values[:2]
 set_result(cid,'PASS',actual,evidence,'PASS trong phạm vi thử đã ghi, không thay nghiệm thu mọi biến thể hoặc chính sách chưa chốt.')
set_result('FUNC-07','BLOCKED','Đã sửa upload sai KB/phòng ban; TXT hợp lệ, .exe sai bị chặn. Chưa chạy mới đầy đủ PDF/DOCX/MD/PPTX và mọi giới hạn kích thước.','live-postfix-results.json; pytest-final.log','Lỗi bảo mật đã đóng; độ phủ đầy đủ các định dạng còn thiếu.')
set_result('FUNC-08','BLOCKED','Lô có tệp sai bị từ chối trước ghi; lô hợp lệ commit một lần; lỗi giữa lô rollback DB và dọn tệp.','pytest-final.log','Lỗi lưu một phần đã đóng; chính sách upload trùng và gửi lại khi mất mạng chưa chốt/kiểm hết.')
set_result('FUNC-26','BLOCKED','Mobile390px không tràn, tìm kiếm dùng được; Tab/focus, theme, loading/empty/error đã kiểm.','frontend-stage-faults-mobile.json; frontend-security-browser.json','Chưa nghiệm thu đủ mọi modal, tên dài và bộ trợ năng trên tất cả trang.')
# Other previously-blocked functional requirements keep their limits, with new evidence where relevant.
for r in records.values():
 if r['group']=='functional' and r['status']=='BLOCKED' and r['criterion_id'] not in {'FUNC-07','FUNC-08','FUNC-26'}:
  r['actual']='Đợt kiểm lại chưa đủ điều kiện nghiệm thu toàn tiêu chí. '+str(r.get('actual',''))
  r['evidence']='stage-lifecycle-results.json; business-sqlite-raw.json; pytest-final.log; REPORT.md'
set_result('SEC-22','PASS','Sau triển khai, endpoint chunks của tài liệu private thử trả401 cho khách qua cả :8001 và :8888; lãnh đạo được đọc/query, nhân viên ngoài KB bị403.','live-postfix-results.json','Kiểm qua gateway trên VPS; không tuyên bố đã kiểm mọi đường truy cập Internet.')

rs=list(records.values());assert len(rs)==116 and not any(r['status']=='NOT_RUN' for r in rs)
summary={'criteria':116,'status':dict(Counter(r['status'] for r in rs)),'by_group':{g:dict(Counter(r['status'] for r in rs if r['group']==g)) for g in ['functional','business','rag','security']},'previous_status':dict(Counter(r['previous_status'] for r in rs)),'verdict':'FIXES_DEPLOYED; ACCEPTANCE_PARTIAL','note':'Không có FAIL trong phạm vi đã kiểm lại; các mục BLOCKED chưa được nghiệm thu.'}
(P/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(P/'all-results.json').write_text(json.dumps({'summary':summary,'records':rs},ensure_ascii=False,indent=2))
with (P/'results-checklist.csv').open('w',encoding='utf-8-sig',newline='') as f:
 fields=['criterion_id','group','priority','previous_status','status','actual','evidence','limitations']
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rs)
print(json.dumps(summary,ensure_ascii=False))
