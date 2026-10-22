import json
from pathlib import Path
root=Path(__file__).parent
raw=json.loads((root/'security-probe.raw.json').read_text())
latest={r['criterion_id']:r for r in raw}
xss=json.loads((root/'xss-results.json').read_text())
live=json.loads((root/'live-probes.json').read_text())

def add(cid,status,actual,evidence,scope,limitations=''):
 latest[cid]={'criterion_id':cid,'status':status,'actual':actual,'evidence':evidence,'environment':'isolated Chromium' if scope=='isolated-browser' else 'remote backend/gateway read-only','scope':scope,'limitations':limitations}
add('SEC-13','FAIL',f'HTML event handler executed={xss["approval"]["executed"]}', 'Approvals.jsx:123-129,587-592 direct HTML sink; knowledge.py:142-174 Admin may read pending entry; browser fixture sets same sink semantics','isolated-browser','The full React approvals flow was not automated; pending-entry delivery established from source')
add('SEC-14','FAIL',f'untrusted Markdown event handler executed={xss["chat"]["executed"]}', 'Exact renderMarkdown function extracted from ChatAssistant.jsx:144-264 and evaluated in Chromium; no network','isolated-browser','Full document upload/preview UI path not automated')
add('SEC-15','FAIL',f'chat text preserved active HTML={xss["chat"]["htmlContainsHandler"]}; executed={xss["chat"]["executed"]}', 'Exact ChatAssistant renderMarkdown on synthetic chat text, Chromium; no network','isolated-browser','Filename attribute variant not separately run; chat-text variant is sufficient to fail')
latest['SEC-22']['actual']='backend: '+','.join(str(x['status']) for x in live if x['port']==8001)+'; gateway: '+','.join(str(x['status']) for x in live if x['port']==8888)
latest['SEC-22']['evidence']='live-probes.json; paths in same order, synthetic nonexistent IDs; no response bodies retained'
latest['SEC-22']['limitations']='404 on nonexistent IDs cannot prove auth on existing private data; direct Markdown yielded 401 on both paths'
latest['SEC-24']['status']='BLOCKED'
latest['SEC-24']['limitations']='Role-only helper exercised on one fixture; actual current and newly created KB route matrix not fully run by security suite'
latest['SEC-20']['limitations']='Effective process secret differed from built-in default; behavior under forced-default startup not executed; deployed process setting may differ'
for r in latest.values():
 r['environment']=r.get('environment','remote venv, fake DB/fixtures')
 r['scope']=r.get('scope','isolated-asgi')
 r['limitations']=r.get('limitations','')
assert set(latest)=={f'SEC-{i:02d}' for i in range(1,26)},set(latest)
records=[latest[f'SEC-{i:02d}'] for i in range(1,26)]
(root/'security-results.json').write_text(json.dumps({'date':'2026-09-29','records':records},ensure_ascii=False,indent=2)+'\n')
counts={k:sum(r['status']==k for r in records) for k in ('PASS','FAIL','BLOCKED')}
lines=['# Kết quả đánh giá bảo mật — 29/09/2026','',f"**{counts['PASS']} PASS / {counts['FAIL']} FAIL / {counts['BLOCKED']} BLOCKED** trên 25 tiêu chí. FAIL là kết quả từ ứng dụng ASGI cô lập, DB/vector/LLM giả, hoặc trình duyệt với HTML giả; chưa khai thác trên dữ liệu thật. Các GET sống chỉ dùng ID không tồn tại và giữ lại mã HTTP.",'','| ID | Kết quả | Bằng chứng ngắn |','|---|---|---|']
for r in records:
 lines.append(f"| {r['criterion_id']} | {r['status']} | {r['actual'].replace('|','/')} |")
lines += ['', 'Các thất bại có tác động rõ nhất: đọc chunk và debug-chat không cần token (SEC-01–04); người ngoài KB vẫn truy vấn nội dung KB riêng tư (SEC-07/09), upload vào KB lạ và giả phòng ban (SEC-11/12), KG trả dữ liệu ngoài danh sách tài liệu được phép (SEC-10), XSS ở các điểm chèn HTML (SEC-13–15), và ghi lịch sử chat dưới ID người khác qua tham số `user_id` (SEC-25).', '', 'Giới hạn: SEC-20 chưa thử khởi động với bí mật JWT mặc định; SEC-22 chỉ xác nhận 404/401 với ID giả trên backend/gateway, không chứng minh chính sách cho tài liệu có thật; SEC-24 mới kiểm helper trên một KB giả. Tất cả kết quả ASGI dùng chặn socket và các dịch vụ giả. Phép thử Chromium chặn mọi yêu cầu mạng. Không gửi process/reindex lên dịch vụ sống, không xem nội dung tài liệu hay bí mật runtime.', '', 'Sự cố trong lần thử đầu: reindex-workspace với ID KB giả 77 đã đi tới lệnh xóa collection thật trước khi bị chặn; Chroma trả “collection kb_77 does not exist”, nên không có collection bị xóa. Mọi lần chạy sau đều thay `get_vector_store` bằng giả và chặn socket. Trong lần đầu, debug-chat có thể đã thử gọi provider với duy nhất câu hỏi giả; không có dữ liệu thật. Lần chạy cuối thay provider bằng giả và chặn socket.', '', 'Tệp tái lập: `security_probe.py` (chạy từ backend venv qua stdin), `security_xss.cjs`, `renderMarkdown.fixture.js`; bằng chứng thô: `security-probe.raw.json`, `xss-results.json`, `live-probes.json`.']
(root/'security-report.md').write_text('\n'.join(lines)+'\n')
print(counts)
