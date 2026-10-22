# Triển khai bản sửa desktop 22/10/2026

Bản live dùng Docker, backend cổng 8001, frontend bundle nginx cổng 5174, gateway 8888; không dùng Vite trên các cổng live. Tên miền public dùng nginx host với root `/var/www/miccorag-chatbot`, proxy API tới8001. Cổng5174/8888 KHÔNG phải nguồn static của tên miền public; Vite15175 chỉ là candidate cục bộ. Khi sửa frontend phải cập nhật cả bundle public và Docker frontend để hai đường truy cập đồng nhất. Không thay env riêng, migration, DB seed hay pending `app/api/rag.py`.

Backend B03: image dựa trên đúng live image trước sửa, chỉ COPY `app/api_compat/documents.py`. Local regression 163 PASS, full backend unit 303 PASS. Luna kiểm tra live PASS. Image và rollback IDs nằm trong `harness/reports/fixes-20261022/deployments.jsonl`.

Cấu hình pin đúng các image đã rollout: `compose.desktop-fixes.yaml` ở repo root, dùng cùng Compose hiện hữu:

```bash
docker compose --env-file /home/micco/.config/miccorag/docker-production.env \
  -f compose.production.yaml -f compose.desktop-fixes.yaml config --services
```

Khi triển khai, chỉ `up -d --no-deps backend` hoặc `frontend` cho service đang sửa; không gọi `down`, không tác động các dự án khác. Cờ deploy-maintenance bảo vệ watchdog trong lượt rollout, chỉ bỏ khi readiness đã đạt. Health cục bộ và health public phải đạt, sau đó Luna kiểm tra hành vi trên public UI.

Rollback dùng image trước sửa đã giữ bằng tag `miccorag-<service>:rollback-<12 ký tự image ID>` và override đúng service. Không xóa image/bundle cũ; giữ asset hash cũ để tab đang mở tiếp tục tải được. Các lệnh rollback cụ thể của phiên được lưu `/tmp/micco-desktop-fixes-deploy/Bxx-<service>-rollback.yaml`.

Frontend source đã đối chiếu với revision e16c7ae của live image: trước sửa chỉ khác whitespace trong bốn file. Build mới có hash khác baseline live; cần kiểm tra hành vi và không coi hash khác là bằng chứng thay đổi nghiệp vụ. Không đẩy toàn dirty backend vào image.

Public B04: đã sao lưu nguyên static site vào `/tmp/micco-desktop-fixes-baseline/public-html`; copy assets trước, thay index.html atomically, giữ mọi hash cũ. Dùng container MiccoRAG tạm chỉ mount đúng thư mục site này; không sửa/reload nginx toàn cục. Mỗi bản sửa sau giữ index trước trong `/tmp/micco-desktop-fixes-deploy/Bxx-frontend/public-index-before.html`.
