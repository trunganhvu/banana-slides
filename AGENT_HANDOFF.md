# Tài liệu Bàn giao & Ngữ cảnh Dự án (Agent Handoff Guide)

> **Mục đích**: Tài liệu này lưu trữ toàn bộ trạng thái dự án, kiến trúc bản địa hóa (Tiếng Việt / Tiếng Anh), quy ước dữ liệu, cách chạy Local và Docker để bất kỳ luồng Chat Agent mới nào cũng có thể nắm bắt ngay lập tức mà không cần đọc lại lịch sử chat cũ.

---

## 1. Tổng quan trạng thái dự án

- **Thư mục gốc**: `f:\DEV\banana-slides` (nhánh nguồn từ `https://github.com/Anionex/banana-slides`)
- **Trạng thái ngôn ngữ**:
  - **Tiếng Việt (`vi` / khóa nội bộ `zh`)**: Ngôn ngữ mặc định toàn hệ thống (UI, AI Prompts, Backend messages, CLI, Desktop, SVG buttons, Docs).
  - **Tiếng Anh (`en`)**: Ngôn ngữ phụ thứ hai.
  - **Cam kết 0% ký tự tiếng Trung (CJK)**: Toàn bộ mã nguồn, comment, docstring, prompt, test, cấu hình Docker/CI và tài nguyên văn bản đã được kiểm tra đạt **0 ký tự CJK** (`[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]`).
- **Nguyên tắc cốt lõi**: Giữ nguyên **100% logic nghiệp vụ (business logic)** và hợp đồng API giữa Frontend ↔ Backend.

---

## 2. Kiến trúc Bản địa hóa (Localization Architecture)

### 2.1. Frontend (`frontend/src/`)
- **Cấu hình i18n**: [`frontend/src/i18n.ts`](file:///f:/DEV/banana-slides/frontend/src/i18n.ts)
  - Để giữ nguyên 100% logic kiểm tra ngôn ngữ trong toàn bộ component (như `i18n.language.startsWith('zh')` hoặc khóa `zh` trong `useT`), gói ngôn ngữ tiếng Việt được gắn vào khóa tài nguyên `zh` (và bí danh `vi`), còn tiếng Anh gắn vào `en`.
  - Tệp từ điển tiếng Việt: [`frontend/src/locales/zh.json`](file:///f:/DEV/banana-slides/frontend/src/locales/zh.json)
  - Tệp từ điển tiếng Anh: [`frontend/src/locales/en.json`](file:///f:/DEV/banana-slides/frontend/src/locales/en.json)
  - Tệp từ điển trang Cài đặt: [`frontend/src/components/settings/settingsI18n.ts`](file:///f:/DEV/banana-slides/frontend/src/components/settings/settingsI18n.ts)
  - Tệp từ điển phong cách mẫu: [`frontend/src/config/presetStylesI18n.ts`](file:///f:/DEV/banana-slides/frontend/src/config/presetStylesI18n.ts)
  - HTML gốc: [`frontend/index.html`](file:///f:/DEV/banana-slides/frontend/index.html) đặt `<html lang="vi">`.

### 2.2. Hợp đồng trường mở rộng mô tả trang (`extra_fields`)
Các trường mở rộng trong mô tả chi tiết trang (Page Description) đã được chuẩn hóa sang tiếng Việt ở cả AI Prompts, Backend và Frontend:
| Ý nghĩa | Giá trị chuẩn (Tiếng Việt) | Khóa cũ (được tự động ánh xạ qua mã Unicode escape) |
|---|---|---|
| Hình ảnh & Tư liệu | `Hình ảnh & Tư liệu` | `\u914d\u56fe\u4e0e\u7d20\u6750` |
| Bố cục & Trọng tâm | `Bố cục & Trọng tâm` | `\u7248\u5f0f\u4e0e\u91cd\u70b9` |
| Ghi chú thuyết trình | `Ghi chú thuyết trình` | `\u6f14\u8bb2\u8005\u5907\u6ce8` |

- **Lưu ý quan trọng**: Khi cần tương thích ngược với dữ liệu cũ trong SQLite hoặc `localStorage['banana-available-extra-fields']`, **luôn dùng chuỗi Unicode escape** (ví dụ `\u7248\u5f0f\u4e0e\u91cd\u70b9`) thay vì viết trực tiếp chữ Hán để vừa tự động chuyển đổi dữ liệu cũ sang tiếng Việt vừa đảm bảo 0 ký tự CJK trong mã nguồn.
- Các tệp xử lý ánh xạ trường mở rộng:
  - Backend: [`backend/models/settings.py`](file:///f:/DEV/banana-slides/backend/models/settings.py), [`backend/services/ai_service.py`](file:///f:/DEV/banana-slides/backend/services/ai_service.py), [`backend/services/prompts.py`](file:///f:/DEV/banana-slides/backend/services/prompts.py)
  - Frontend: [`frontend/src/pages/DetailEditor.tsx`](file:///f:/DEV/banana-slides/frontend/src/pages/DetailEditor.tsx), [`frontend/src/store/useProjectStore.ts`](file:///f:/DEV/banana-slides/frontend/src/store/useProjectStore.ts), [`frontend/src/components/preview/DescriptionCard.tsx`](file:///f:/DEV/banana-slides/frontend/src/components/preview/DescriptionCard.tsx), [`frontend/src/components/preview/PagePropertiesDrawer.tsx`](file:///f:/DEV/banana-slides/frontend/src/components/preview/PagePropertiesDrawer.tsx), [`frontend/src/utils/projectUtils.ts`](file:///f:/DEV/banana-slides/frontend/src/utils/projectUtils.ts)

### 2.3. Backend Prompts & AI Service (`backend/services/`)
- [`backend/services/prompts.py`](file:///f:/DEV/banana-slides/backend/services/prompts.py): Toàn bộ 38 hàm tạo prompt cho AI (tạo dàn ý, tạo mô tả trang, tạo ảnh slide, chỉnh sửa ngôn ngữ tự nhiên, trích xuất kiểu chữ, tạo lời thuyết minh video...) đều sử dụng tiếng Việt làm mặc định (`OUTPUT_LANGUAGE=vi`).

---

## 3. Hướng dẫn Build & Chạy Dự án

### 3.1. Chạy bằng Docker Compose (Khuyến nghị)
- **Tệp cấu hình**:
  - [`docker-compose.yml`](file:///f:/DEV/banana-slides/docker-compose.yml)
  - [`backend/Dockerfile`](file:///f:/DEV/banana-slides/backend/Dockerfile)
  - [`frontend/Dockerfile`](file:///f:/DEV/banana-slides/frontend/Dockerfile)
  - [`.env`](file:///f:/DEV/banana-slides/.env) (tạo từ [`.env.example`](file:///f:/DEV/banana-slides/.env.example))
- **Cổng mặc định**:
  - Frontend (Nginx): `http://localhost:3011` (ánh xạ vào cổng `80` trong container `banana-slides-frontend`)
  - Backend (Flask): `http://localhost:5011` (ánh xạ vào cổng `5000` trong container `banana-slides-backend`)
  - OpenAI OAuth Callback: `http://localhost:1455`
- **Các lệnh Docker**:
  ```powershell
  # Build và khởi chạy toàn bộ dịch vụ ở chế độ chạy nền
  docker compose up -d --build

  # Kiểm tra trạng thái container
  docker compose ps

  # Xem log
  docker compose logs -f

  # Dừng dịch vụ
  docker compose down
  ```

### 3.2. Chạy trực tiếp trên máy Local (Development)
- **Môi trường ảo Python**: `f:\DEV\banana-slides\.venv` (Python 3.11)
- **Khởi chạy Backend (Cổng 5011)**:
  ```powershell
  cd f:\DEV\banana-slides\backend
  $env:PYTHONUTF8='1'
  ..\.venv\Scripts\python.exe -u app.py
  ```
- **Khởi chạy Frontend (Cổng 3011)**:
  ```powershell
  cd f:\DEV\banana-slides\frontend
  npm run dev
  ```

---

## 4. Lệnh Kiểm tra & Nghiệm thu cho Agent tiếp theo

1. **Kiểm tra không còn ký tự tiếng Trung (CJK) trong toàn bộ mã nguồn**:
   ```powershell
   $env:PYTHONUTF8='1'; .\.venv\Scripts\python.exe -c "import os,re; r=re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]'); ig={'.git','node_modules','.venv','dist','__pycache__','.pytest_cache'}; ex={'.png','.jpg','.jpeg','.gif','.ico','.icns','.woff','.woff2','.ttf','.otf','.pyc','.db','.sqlite','.pptx','.pdf'}; hits=[(os.path.join(rt,f),i) for rt,ds,fs in os.walk('.') if not ds.__setslice__(0,len(ds),[d for d in ds if d not in ig]) for f in fs if os.path.splitext(f)[1].lower() not in ex for i,l in enumerate(open(os.path.join(rt,f),encoding='utf-8',errors='ignore'),1) if r.search(l)]; print('CJK hits:', len(hits))"
   ```
2. **Kiểm tra biên dịch Backend Python**:
   ```powershell
   .\.venv\Scripts\python.exe -m compileall -q backend
   ```
3. **Kiểm tra Build Frontend TypeScript/Vite**:
   ```powershell
   cd frontend; npm run build
   ```
