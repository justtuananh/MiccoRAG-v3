import json,re,statistics
from pathlib import Path
P=Path(__file__).parent
pilot=json.loads((P/'rag-pilot-results.json').read_text());stream=json.loads((P/'rag-stream-results.json').read_text())
answers=[]
for group in [pilot,stream]:
 for r in group['results']:
  if r['variant']=='query':continue
  obj=r.get('response',{})
  if r['variant']=='stream':
   if group is stream:obj=next((e['data'] for e in r.get('events',[]) if e.get('event')=='complete'),{})
   else:obj=next((e for e in r.get('events',[]) if 'answer' in e),{})
  answer=obj.get('answer','');sources=obj.get('sources',[]);ids={str(s['index']) for s in sources}
  citations=re.findall(r'\[([a-zA-Z0-9]{4})\]',answer)
  unresolved=[c for c in citations if c not in ids]
  # Manual source-grounded judgement: G04 omits two required fields available in original table.
  facts_ok=r['case_id']!='G04' and r.get('status_code')==200 and bool(answer)
  answers.append({'case_id':r['case_id'],'variant':r['variant'],'role':r['role'],'repeat':r['repeat'],'run_id':group['run_id'],'status_code':r.get('status_code'),'fact_correct_complete':facts_ok,'citation_ids':citations,'source_ids':sorted(ids),'unresolved_citations':unresolved,'source_document_ids':sorted({s['document_id'] for s in sources}),'answer':answer,'seconds':r['seconds'],'judgement_basis':'Human-readable review by evaluation agent against independently extracted original PDF/DOCX; not business-owner signoff','failure_reason':'Thiếu cấp phê duyệt Giám đốc và thời hạn 20 ngày dù bảng nguồn có; nói sai rằng tài liệu không nêu' if not facts_ok else ('Citation không ánh xạ source của response' if unresolved else None)})
primary=[a for a in answers if a['run_id']==pilot['run_id'] and a['variant']=='chat' and a['role']=='Giám đốc' and a['repeat']==1]
metrics={'unique_primary_questions':len(primary),'primary_fact_pass':sum(a['fact_correct_complete'] for a in primary),'answer_variants':len(answers),'fact_pass_variants':sum(a['fact_correct_complete'] for a in answers),'unresolved_citation_responses':sum(bool(a['unresolved_citations']) for a in answers),'http_failures':sum(a['status_code']!=200 for a in answers),'stream_instrumented':len(stream['results']),'source_documents':3,'formal_business_approval':False}
(P/'rag-graded-answers.json').write_text(json.dumps({'metrics':metrics,'answers':answers},ensure_ascii=False,indent=2))
records=[]
def rec(id,status,actual,scope='live-grounded-pilot',lim='Không phải bộ 120 golden/holdout đã được chủ nghiệp vụ duyệt'):
 records.append({'criterion_id':id,'status':status,'actual':actual,'scope':scope,'evidence':'rag-pilot-results.json; rag-stream-results.json; rag-graded-answers.json; original-sources.json; rag-diagnostics.json','limitations':lim})
rec('RAG-01','BLOCKED','Đã đối chiếu original PDF/DOCX với markdown và truy xuất; live upload TXT→indexed→query thành công. Chưa chạy upload mới PDF/DOCX 2 trang trong fixture.')
rec('RAG-02','FAIL','G04 bỏ mất hàng bảng 500 triệu/20 ngày/Giám đốc; lặp qua 3 chat director +2 stream +1 admin vector. G06 bảng134 người/16giờ đúng.')
rec('RAG-03','BLOCKED','Không có bộ scan/OCR và vùng ảnh được chủ tài liệu duyệt để chấm; nguồn pilot là PDF text và DOCX.')
rec('RAG-04','BLOCKED','Nguồn pilot không có hình nghiệp vụ chứa đáp án độc lập; thiếu golden ảnh được duyệt.')
rec('RAG-05','FAIL','Bộ lọc IDs đúng trong pilot vector; fixture SEC-10 chứng minh nhánh KG có thể trả sentinel ngoài allowed IDs.','live-pilot + isolated-KG','Live dữ liệu chưa có KG mixed-permission để tái hiện toàn luồng.')
rec('RAG-06','FAIL','SEC-10 chạy DeepRetriever thật với vector/KG giả: KG private sentinel xuất hiện khi document_ids chỉ cho phép tài liệu public.','isolated-KG','Không đọc nội dung trái quyền từ tài liệu nghiệp vụ thật.')
rec('RAG-07','BLOCKED','44 unit tests gồm bộ lọc approved+INDEXED đạt; chưa có đầy đủ trạng thái + pipeline vector/KG stale để chấm mọi nhánh.')
rec('RAG-08','FAIL','SEC-07/08/09 và RBAC fixture trả dữ liệu private KB cho foreign user; owners private docs department=None có lỗi thiếu quyền ngược chiều.','isolated-ASGI + SQLite')
rec('RAG-09','BLOCKED','Pilot 3 docs trong2 KB đúng document IDs; chưa dựng đồng thời2KB có đáp án mâu thuẫn và đầy đủ vector/KG/image để kiểm tất cả đường.')
rec('RAG-10','BLOCKED','Thiếu nguồn V1/V2 có ngày hiệu lực và quy tắc phục vụ bản cũ được duyệt (Q-05).')
rec('RAG-11','BLOCKED','Thiếu timeline chuyển tiếp/hồi tố được chủ tài liệu xác nhận (Q-05).')
rec('RAG-12','BLOCKED','Chưa có thứ bậc thẩm quyền và cặp tài liệu mâu thuẫn được chốt (Q-05).')
rec('RAG-13','BLOCKED','Chưa có golden xung đột ngang cấp được duyệt và quy tắc diễn đạt kết luận (Q-05/Q-10).')
rec('RAG-14','FAIL','G04 chỉ lấy quy tắc đấu thầu, bỏ cấp duyệt và thời hạn; các câu G02/G05/G07 đầy đủ trên nguồn thử.')
rec('RAG-15','PASS','G10 nêu đúng1.250.000 đồng/tháng và nói nguồn không có số điện thoại; không tự điền số.','live pilot: G10 only','Kết quả đúng trong mẫu1câu; không suy rộng mọi câu nhiều phần.')
rec('RAG-16','PASS','G08 qua chat và2 stream đều nói nguồn không có số điện thoại; đối chiếu toàn bộ DOCX26 xác nhận không có.','live pilot: G08 3variants','Đúng trên câu no-answer đã thử; chưa phải độ chính xác no-answer của toàn bộ KB.')
rec('RAG-17','FAIL','G04 thiếu20ngày và khẳng định nguồn không có thời hạn dù bản gốc có; phụ cấp, ngày25, ngưỡng14, sát hạch40/45/80/30 đều đúng.')
rec('RAG-18','BLOCKED','Chưa có golden tổng hợp2+nguồn độc lập đã duyệt; pilot cố định1doc/câu để truy nguyên lỗi.')
rec('SRC-01','FAIL','G01 director repeat2 dẫn[hbc1] nhưng sources trả[index=hbcl]; một citation không có bằng chứng ánh xạ trong response.')
rec('SRC-02','FAIL','Một citation ID không ánh xạ nguồn: hbc1≠hbcl; metadata tên nguồn còn dùng prefix cũ khác original_filename, cần chuẩn hóa.')
rec('SRC-03','FAIL','SEC-10 xác nhận KG context có sentinel ngoài danh sách nguồn được phép; không thể coi mọi fact KG là bằng chứng đã duyệt.','isolated-KG')
rec('SRC-04','BLOCKED','XSS đã kiểm bằng HTML fixture, nhưng đó không thay thế prompt injection vào retrieval; chưa có bộ payload chỉ dẫn độc hại cùng golden được duyệt.')
rec('SRC-05','BLOCKED','Pilot không dùng history chứa citation cũ; chưa đo ánh xạ citation xuyên2lượt sau đổi nguồn.')
rec('SRC-06','BLOCKED','Thiếu fixture text/image/table khác trang có mapping vàng; pilot không truy xuất ảnh.')
rec('RAG-19','BLOCKED','3stream có complete, token cuối khớpanswer3/3; G01/G08 nhất quán chat, G04 đều bỏ bảng. Chưa đủ ma trận quyền và biến thể rollback/reconnect.')
rec('RAG-20','BLOCKED','Chưa có nguồn thay đổi hiệu lực và câu nối tiếp đã duyệt; lifecycle thử1version, không thay tài liệu thật.')
rec('RAG-21','BLOCKED','2câu so hybrid director và vector Admin: G01đúng/G04sai cả2; chưa có golden quan hệ/thực thể để so recall.')
rec('RAG-22','BLOCKED','Chưa có golden biến thể không dấu/song ngữ/thực thể gần giống được duyệt; không dùng paraphrase tùy ý để chấm PASS.')
rec('RAG-23','BLOCKED','Fixture TXT xóa rồi GET404/query0chunks đạt; chưa đủ vòngđời thayversion + graph/images để nghiệm thu tiêu chí đầy đủ.')
rec('RAG-24','BLOCKED','Pilot cố định force_search để đo nguồn; chưa đo chính sách phân biệt chào hỏi và truy vấn nghiệp vụ tự động.')
assert len(records)==30
(P/'rag-results.json').write_text(json.dumps({'metrics':metrics,'records':records},ensure_ascii=False,indent=2))
print(json.dumps(metrics,ensure_ascii=False))
