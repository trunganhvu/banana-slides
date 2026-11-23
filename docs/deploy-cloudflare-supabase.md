# Hướng dẫn triển khai & vận hành Banana Slides trên Cloudflare + Supabase

Tài liệu này lưu lại kiến trúc triển khai production chi phí thấp (~$5/tháng), các tệp cấu hình liên quan trong repository và quy trình chuẩn cho những lần cập nhật, mở rộng hoặc chuyển môi trường về sau.

---

## 1. Tổng quan kiến trúc & Chi phí vận hành

Hệ thống chạy theo mô hình **Serverless Frontend + Containerized Python Backend + Persistent R2 Storage + Managed PostgreSQL**:

```text
Người dùng / Googlebot / AI Bot
            │
            ▼
  Cloudflare Pages (Frontend SPA + SEO/GEO + Pages Functions Proxy)  [$0/tháng]
     ├── /*                  -> frontend/dist/index.html (React/Vite + Static SEO Shell)
     └── /api/*, /files/*, /health
            │ (Reverse Proxy qua BACKEND_ORIGIN, không lỗi CORS)
            ▼
  Cloudflare Worker + Durable Object (cloudflare-backend/src/index.ts)
            │ (Quản lý vòng đời & đánh thức Container qua cổng 5000)
            ▼
  Cloudflare Containers (cloudflare-backend/Dockerfile)                [$5/tháng - Workers Paid]
     ├── Flask Backend + ThreadPoolExecutor + ffmpeg + opencv + onnxruntime
     ├── /app/uploads ──(tigrisfs FUSE đọc-ghi)──▶ Cloudflare R2       [$0 - 10GB free, $0 egress]
     └── SQLAlchemy + Alembic ──(Session Pooler)──▶ Supabase Postgres  [$0 - Free 500MB, ap-southeast-1]
```

### Đặc điểm vận hành quan trọng
- **Tự ngủ khi vắng khách (Scale-to-zero):** Durable Object `BananaSlidesContainer` đặt `INACTIVITY_TIMEOUT_MS = 15 * 60 * 1000` (15 phút). Khi hết timeout, container dừng để tiết kiệm tài nguyên gói Workers Paid.
- **Khởi động lạnh (Cold start):** Lần request đầu tiên sau khi container ngủ cần ~25–45 giây để mount R2 (`tigrisfs`), chạy `alembic upgrade head` và khởi động Flask; Worker chờ tối đa 60 giây (`STARTUP_WAIT_ATTEMPTS = 120`, mỗi lần 500ms) trên `/health` trước khi forward request.
- **Ổ đĩa container là tạm thời:** Tuyệt đối không lưu dữ liệu bền vững lên đĩa cục bộ container. Toàn bộ file tải lên/ảnh/PPTX đi qua `/app/uploads` (mount R2) và toàn bộ metadata/người dùng lưu trên Supabase PostgreSQL.

---

## 2. Bản đồ các tệp triển khai trong repository

### Frontend, Proxy & SEO/GEO (`frontend/`)
- `frontend/src/api/client.ts`: Hỗ trợ `VITE_API_BASE_URL` (để trống khi dùng same-origin proxy qua Pages Functions).
- `frontend/functions/_utils/proxy.js`, `api/[[path]].js`, `files/[[path]].js`, `health.js`: Reverse proxy từ origin Cloudflare Pages sang `BACKEND_ORIGIN`, hỗ trợ SSE streaming và tải tệp lớn.
- `frontend/public/_redirects`, `_headers`: Định tuyến SPA fallback (`/* /index.html 200`), header bảo mật và cache asset.
- `frontend/index.html`: Nâng cấp `JSON-LD @graph` (`WebSite`, `SoftwareApplication`, `FAQPage`) và Static Semantic HTML SEO Shell (`<main class="sr-only">`) giúp các bot AI không chạy JS đọc được nội dung.
- `frontend/public/robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt`, `site.webmanifest`: Khai báo chuẩn SEO Google & Generative Engine Optimization (GEO).
- `frontend/.env.production.example`: Mẫu biến môi trường cho Cloudflare Pages.

### Backend tương thích PostgreSQL & Bảo mật (`backend/`, gốc repo)
- `pyproject.toml`, `uv.lock`: Bổ sung `psycopg2-binary` để kết nối PostgreSQL.
- `backend/config.py`, `backend/app.py`, `backend/models/__init__.py`: Hàm `normalize_database_url()` và `build_engine_options()` tự động tách cấu hình kết nối cho SQLite (local/desktop) và PostgreSQL (Supabase).
- `backend/migrations/env.py`, `backend/migrations/versions/019_per_page_template.py`, `backend/desktop_bootstrap.py`: Chuẩn hóa URL `postgres://` -> `postgresql://`, tương thích kiểu boolean `sa.false()`, và bỏ qua sửa schema kiểu SQLite khi chạy trên Postgres.
- `backend/controllers/auth_controller.py`:
  - Khóa `POST /api/auth/dev-login` ở production (trả `403 DEV_LOGIN_DISABLED` trừ khi `TESTING=true` hoặc `ENABLE_DEV_LOGIN=true`).
  - `_is_admin_email()` trả `False` khi `ADMIN_EMAILS` trống (chỉ bootstrap user đầu tiên khi DB chưa có user nào).
  - Xác thực chặt `GOOGLE_CLIENT_ID`, kiểm tra `aud`, `iss` và `email_verified=true` trên Google ID token.
- `backend/controllers/file_controller.py`: Thêm `_is_safe_path_segment()` và `_resolve_contained_path()` (dùng `Path.resolve()` + `relative_to()`) chặn path traversal, sibling-prefix escape và symlink escape nhưng vẫn giữ hỗ trợ tên tệp PPTX tiếng Việt có dấu.

### Gói đóng gói Container (`cloudflare-backend/`, `scripts/`)
- `cloudflare-backend/Dockerfile`: Image Python 3.10 + `uv` + `ffmpeg` + `fonts-noto-cjk` + `fuse3` + `tigrisfs` v1.2.1 (context build là thư mục gốc `..`).
- `cloudflare-backend/entrypoint.sh`: Bắt buộc dùng line ending **LF**; mount R2 vào `/app/uploads`, chạy `alembic upgrade head`, khởi động Flask cổng `5000`, unmount sạch khi nhận `SIGTERM`.
- `cloudflare-backend/src/index.ts`: Durable Object `BananaSlidesContainer` quản lý start, timeout nhàn rỗi và kiểm tra `/health`.
- `cloudflare-backend/wrangler.jsonc`: Cấu hình Container (`instance_type: "basic"`, `max_instances: 1`), Durable Object binding và biến môi trường không nhạy cảm.
- `cloudflare-backend/package.json`: Ghim `wrangler@4.85.0` để tương thích với Node.js `v20.18+` (hoặc nâng cấp lên bản mới hơn nếu máy dùng Node `>= 22.12`).
- `cloudflare-backend/.dev.vars.example`: Danh sách các secret cần nạp.
- `scripts/deploy-cloudflare.ps1`: Script tự động kiểm tra, deploy Backend Container và nghiệm thu các endpoint live.

---

## 3. Quy trình thiết lập từ đầu (First-Time Setup)

### Bước 1: Tạo Database PostgreSQL trên Supabase
1. Tạo project trên Supabase (khuyên dùng vùng **`ap-southeast-1` (Singapore)**).
2. Đặt mật khẩu Database **chỉ gồm chữ cái và chữ số** (tránh ký tự đặc biệt như `@`, `#`, `%`, `&` gây lỗi phân tích URI).
3. Chạy migration khởi tạo schema toàn bộ 11 bảng ứng dụng + bảng `alembic_version` (đặt revision head hiện tại để `alembic upgrade head` không xung đột).
4. **Khóa bảo mật Data API:** Bật Row Level Security (`ENABLE ROW LEVEL SECURITY`) cho tất cả các bảng trong schema `public` và chạy:
   ```sql
   REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
   ```
5. Vào **Connect -> Connection Method: Session pooler -> Type: URI** (cổng `5432`, hỗ trợ IPv4 cho Containers) để lấy chuỗi `DATABASE_URL`:
   ```text
   postgresql://postgres.<project-ref>:<DB_PASSWORD>@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```

### Bước 2: Kích hoạt Cloudflare R2 & Tạo S3 API Token
1. Trên Cloudflare Dashboard -> **R2 Object Storage** -> kích hoạt gói Free (10 GB/tháng, miễn phí băng thông tải ra).
2. Tạo bucket `banana-slides-storage` (vùng `APAC`, `Standard`).
3. Vào **Manage API Tokens -> Create Account API token**:
   - Permissions: **Object Read & Write**
   - Bucket: chỉ định đúng **`banana-slides-storage`**
   - Lưu lại **`Access Key ID`** (nạp vào `AWS_ACCESS_KEY_ID`) và **`Secret Access Key`** (nạp vào `AWS_SECRET_ACCESS_KEY`).

### Bước 3: Nâng cấp Workers Paid & Cấu hình Google OAuth
1. Trên Cloudflare Dashboard -> **Workers plans** -> chọn gói **Workers Paid ($5/tháng)** để bật Cloudflare Containers và Durable Objects.
2. Trên **Google Cloud Console -> Credentials -> OAuth 2.0 Client ID**: thêm URL Cloudflare Pages (`https://<ten-project>.pages.dev`) và tên miền riêng (nếu có) vào **Authorized JavaScript origins**.

### Bước 4: Deploy Backend Container & Nạp Secrets
Đảm bảo **Docker Desktop** đang chạy trên máy, mở PowerShell tại `cloudflare-backend/`:

```powershell
cd cloudflare-backend
npm install
npx wrangler login
npx wrangler deploy
```

Sau khi deploy lần đầu để khởi tạo Worker, nạp lần lượt các secrets (nhập **tên biến** ở lệnh, chỉ dán **giá trị** khi Wrangler hỏi `Enter a secret value:`):

```powershell
npx wrangler secret put DATABASE_URL
npx wrangler secret put SECRET_KEY
npx wrangler secret put GOOGLE_CLIENT_ID
npx wrangler secret put ADMIN_EMAILS
npx wrangler secret put CORS_ORIGINS
npx wrangler secret put AWS_ACCESS_KEY_ID
npx wrangler secret put AWS_SECRET_ACCESS_KEY
# Tùy chọn (nếu muốn cấp AI key mặc định cho toàn hệ thống thay vì user tự nhập):
# npx wrangler secret put GOOGLE_API_KEY
```

### Bước 5: Tạo & Nối Cloudflare Pages (Frontend)
1. Tạo Cloudflare Pages project trỏ tới GitHub repo với cấu hình:
   - **Production branch:** `main`
   - **Root directory:** `frontend`
   - **Build command:** `npm run build:web`
   - **Build output directory:** `dist`
2. Trong **Settings -> Variables and secrets** (cả Production và Preview), thêm biến:
   - `BACKEND_ORIGIN` = `https://banana-slides-backend.<workers-subdomain>.workers.dev`
3. Trong GitHub App của Cloudflare Pages (nút **Manage** cạnh Git repository), đảm bảo đã cấp quyền cho repository để mỗi lần `git push origin main` tự động kích hoạt build.

---

## 4. Hướng dẫn Deploy cho các lần cập nhật sau (Day-2 Operations)

### A. Khi chỉ sửa code Frontend (`frontend/`)
```powershell
git add frontend/
git commit -m "feat(frontend): mo ta thay doi"
git push origin main
```
Cloudflare Pages tự build lại bản Web. Nếu webhook GitHub chưa tự chạy, vào Cloudflare Pages -> **Deployments -> Create deployment** (hoặc retry) trên nhánh `main`.

### B. Khi sửa code Backend hoặc cấu hình Container (`backend/`, `cloudflare-backend/`, `pyproject.toml`, `uv.lock`)
1. Đảm bảo **Docker Desktop** đang mở.
2. Chạy script deploy & nghiệm thu tự động từ thư mục gốc repository:
   ```powershell
   .\scripts\deploy-cloudflare.ps1 -BackendUrl "https://banana-slides-backend.<your-subdomain>.workers.dev"
   ```
   *(Hoặc chạy nhanh `.\scripts\deploy-cloudflare.ps1` nếu chỉ cần nghiệm thu qua domain Frontend.)*
3. Commit và push thay đổi lên GitHub để đồng bộ mã nguồn:
   ```powershell
   git add backend/ cloudflare-backend/ pyproject.toml uv.lock .env.example
   git commit -m "chore(backend): mo ta thay doi"
   git push origin main
   ```

### C. Khi thêm migration Database mới (Alembic)
1. Viết migration hỗ trợ cả SQLite lẫn PostgreSQL (ví dụ cột `Boolean` phải dùng `server_default=sa.false()` hoặc `sa.true()`, tránh `sa.text('0')` hay SQL chỉ có ở SQLite).
2. Khi container khởi động sau `wrangler deploy`, `cloudflare-backend/entrypoint.sh` tự chạy `alembic upgrade head`.
3. **Nếu migration tạo thêm bảng mới trong schema `public`:** Vào Supabase SQL Editor bật ngay RLS và thu hồi quyền `anon`/`authenticated` cho bảng mới:
   ```sql
   ALTER TABLE public.<ten_bang_moi> ENABLE ROW LEVEL SECURITY;
   REVOKE ALL ON TABLE public.<ten_bang_moi> FROM anon, authenticated;
   ```

### D. Khi xoay vòng / cập nhật Secrets
- Chạy `npx wrangler secret put <TEN_BIEN>` trong `cloudflare-backend/`.
- **Lưu ý bảo mật:** Luôn giữ nguyên tên biến đúng chuẩn (`DATABASE_URL`, `SECRET_KEY`, ...), chỉ dán giá trị sau khi hiện dấu nhắc `Enter a secret value:`. Tuyệt đối không commit tệp `.env` hoặc `.dev.vars` lên Git.

### E. Checklist khi gắn Tên miền riêng (Custom Domain)
1. **Cloudflare Pages -> Custom domains:** Thêm `yourdomain.com` (và `www.yourdomain.com` nếu cần).
2. **Google Cloud Console -> OAuth Client ID:** Thêm `https://yourdomain.com` vào **Authorized JavaScript origins**.
3. **Backend Worker Secret:** Cập nhật `CORS_ORIGINS` (trong `cloudflare-backend/`) thành `https://yourdomain.com,https://<project>.pages.dev`.
4. **SEO & AI Search:**
   - Thay `yourdomain.com` trong `frontend/public/sitemap.xml` bằng tên miền thật và cập nhật `og:image` / `<link rel="canonical">` trong `frontend/index.html` nếu cần URL tuyệt đối.
   - Trên Cloudflare Dashboard của domain -> **Security -> Bots**, kiểm tra **không chặn** các AI Search Crawlers (`OAI-SearchBot`, `GPTBot`, `PerplexityBot`, `ClaudeBot`, `Googlebot`).
5. **Kiểm tra nhanh sau gắn domain:**
   ```powershell
   .\scripts\deploy-cloudflare.ps1 -VerifyOnly -FrontendUrl "https://yourdomain.com"
   ```

---

## 5. Xử lý sự cố thường gặp (Troubleshooting)

| Triệu chứng | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| `Wrangler requires at least Node.js v22.12.0` | Wrangler mới (>= 4.90) yêu cầu Node 22+ | Giữ `wrangler@4.85.0` trong `cloudflare-backend/package.json` khi dùng Node 20, hoặc nâng cấp Node.js lên v22 LTS. |
| `HTTP 500 - error code: 1101` ở request đầu tiên | Container ngủ dậy mất ~25–45s khởi động R2 FUSE + Python | Kiểm tra `STARTUP_WAIT_ATTEMPTS = 120` (60s) trong `cloudflare-backend/src/index.ts`; refresh lại sau vài giây. |
| Container thoát ngay: `exec /app/entrypoint.sh: no such file or directory` | Tệp `cloudflare-backend/entrypoint.sh` bị Windows lưu thành CRLF (`\r\n`) | Chuyển `entrypoint.sh` về **LF (`\n`)** rồi deploy lại (`scripts/deploy-cloudflare.ps1` tự kiểm tra bước này). |
| Container lỗi kết nối DB (`Network is unreachable` / timeout) | Dùng nhầm Direct Connection (chỉ có IPv6 trên Supabase) | Đổi `DATABASE_URL` sang **Session pooler** (cổng `5432`, hỗ trợ IPv4) và kiểm tra encode ký tự đặc biệt trong mật khẩu. |
| `403 DEV_LOGIN_DISABLED` khi gọi `/api/auth/dev-login` | Chốt bảo mật khóa endpoint test trên production | Bình thường ở production; đăng nhập bằng Google SSO (hoặc đặt `ENABLE_DEV_LOGIN=true` chỉ trên máy dev). |
| `git push` không thấy Cloudflare Pages tự build | GitHub App chưa được cấp quyền webhook cho repo | Vào Pages **Settings -> Build -> Manage** để cấp quyền cho repo, hoặc trigger deploy thủ công từ Dashboard/API. |
