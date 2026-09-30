# Docker cho MiccoRAG

`compose.yaml` ở gốc repository chạy bốn dịch vụ riêng: PostgreSQL, ChromaDB, FastAPI và frontend tĩnh qua Nginx. Một backend phục vụ cả `/api/*` và `/api/v1/*`; không khởi động `micco-server`. Frontend không dùng Vite dev trong container.

## Cấu hình và build

Yêu cầu Docker Engine có BuildKit và Compose v2 trở lên. Chạy từ thư mục gốc repository:

```bash
cp .env.docker.example .env.docker
chmod 600 .env.docker
openssl rand -hex 32  # tạo POSTGRES_PASSWORD
openssl rand -hex 32  # tạo JWT_SECRET_KEY khác
```

Điền `POSTGRES_PASSWORD` bằng giá trị hex vừa tạo, rồi điền `DATABASE_URL=postgresql+asyncpg://miccorag:<cùng-giá-trị>@postgres:5432/miccorag` vào `.env.docker` (thay placeholder bằng password đã tạo). Backend đọc URL từ env file runtime; Compose truyền password riêng cho PostgreSQL. Điền khóa provider/embedding đang sử dụng; Cohere tùy chọn. Mẫu mặc định dùng Gemini. Với OpenAI, điền `OPENAI_API_KEY`, đổi `LLM_PROVIDER` và `KG_EMBEDDING_PROVIDER` thành `openai`, rồi đặt đúng `LLM_MODEL_FAST`, `KG_EMBEDDING_MODEL` và `KG_EMBEDDING_DIMENSION` của bộ model đang dùng. Không dùng khóa giả nếu cần ingest/hỏi đáp thật. `MICCO_IMAGE_TAG` đặt theo bản phát hành, `MICCO_VCS_REF` đặt theo `git rev-parse HEAD`. Các khóa chỉ được truyền khi chạy backend, không nằm trong build args hoặc frontend.

```bash
docker compose --env-file .env.docker config --quiet
docker compose --env-file .env.docker build
docker compose --env-file .env.docker up -d --wait --wait-timeout 300
docker compose --env-file .env.docker ps
curl --fail http://127.0.0.1:18890/ready
```

Mặc định chỉ xuất frontend ở `127.0.0.1:18890`, tránh chiếm cổng của hệ thống đang chạy. PostgreSQL, ChromaDB và backend chỉ truy cập qua mạng Compose. Khi triển khai công khai, cấu hình reverse proxy/TLS phía trước hoặc đổi `MICCO_BIND_ADDRESS` và `MICCO_HTTP_PORT` theo hạ tầng. Dùng cùng project name và file môi trường cho mọi lần chạy; `docker compose -p micco-package-test ...` tạo mạng/volume kiểm thử riêng. Nếu chạy song song nhiều project, đặt `MICCO_HTTP_PORT` thành một cổng còn trống khác cho từng project; đổi project name không tự đổi cổng hoặc image tag.

Backend chạy một worker không root, giữ namespace/giới hạn graph trong một tiến trình. `/health` là liveness; `/ready` kiểm DB và ChromaDB. `/nginx-health` kiểm riêng frontend. Readiness không xác nhận khóa LLM, model OCR hoặc chất lượng câu trả lời. Model parsing tải khi cần và lưu ở volume cache; lần ingest đầu cần kết nối tải model.

## Tài khoản đầu tiên

Với DB mới, tạo Admin bằng lệnh tương tác, mật khẩu không hiện trên màn hình:

```bash
docker compose --env-file .env.docker exec backend python -m app.bootstrap_admin --name "Quản trị" --email admin@example.com
```

Lệnh chỉ bootstrap khi chưa có Admin đang hoạt động; không ghi đè tài khoản cũ. Không chạy seed tài khoản/mật khẩu mẫu trên production.

## Dữ liệu và schema

Các named volume lưu riêng PostgreSQL, ChromaDB (`/data` theo server đã pin), uploads, dữ liệu graph/parser và model cache. Không gắn thư mục mã nguồn hoặc dữ liệu phục vụ thật vào môi trường kiểm thử. `.dockerignore` loại `.env`, upload, cache, log và virtualenv khỏi image.

`AUTO_CREATE_TABLES=true` dành cho DB trống; ORM tạo schema hiện tại. Với DB cũ, giá trị này không thay thế việc nâng cấp schema. Sao lưu và đối chiếu Alembic trước khi chạy migration. DB legacy của đợt30/09/2026 chưa có `alembic_version`, đã áp patch007–010; không chạy lại toàn bộ lịch sử hoặc tự stamp chỉ để bỏ cảnh báo. Không tự động migrate/seed mỗi lần container khởi động.

Chuyển hệ thống đang chạy trên VPS sang Compose cần một đợt chuyển dữ liệu riêng: DB, Chroma, uploads và graph phải được sao chép nhất quán và kiểm quyền ghi của UID container. Chạy Compose mới không tự nhập dữ liệu hiện tại. Đặc biệt image Chroma đang pin dùng `/data`; mount `/chroma/chroma` không bảo vệ dữ liệu của server này. Không recreate Chroma cũ trước khi xuất và kiểm bản sao dữ liệu thực.

## Kiểm tra và cập nhật

```bash
docker compose --env-file .env.docker logs --tail 100 backend frontend
docker compose --env-file .env.docker restart backend frontend
curl --fail http://127.0.0.1:18890/ready
```

Kiểm tra đăng nhập, upload, quyền truy cập, hỏi đáp và còn dữ liệu sau restart/recreate. SSE được proxy không buffering. Khi nâng phiên bản, giữ nguyên volumes, build/pull tag mới rồi `up -d --wait`. Lưu tag cũ và bản sao dữ liệu trước migration để rollback có căn cứ. `down` dừng stack; **`down -v` xóa các volume và dữ liệu**, không dùng cho dữ liệu cần giữ.

Gói build và kiểm thử Docker không tự đổi gateway hoặc dừng backend/frontend đang phục vụ trên VPS. Các Compose cũ trong `micco-backend/` vẫn là cấu hình dev/hạ tầng cũ; không chạy chồng cùng volume/cổng với stack này.
