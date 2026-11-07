# Hướng dẫn thiết lập và tối ưu hóa GitHub Actions CI

Tài liệu này giải thích chi tiết cấu trúc, quy trình kích hoạt và chiến lược tối ưu hóa chi phí cho hệ thống GitHub Actions CI của Banana Slides.

## 🎯 Mục tiêu thiết kế

Hệ thống CI được thiết kế xoay quanh ba nguyên tắc cốt lõi:

1. **Tiết kiệm chi phí**: Không gọi các API AI trả phí (OpenAI, Claude, v.v.) trong các nhánh PR thông thường.
2. **Kiểm tra nhanh (Light)**: Cung cấp phản hồi nhanh chóng (lint, build, unit test) trong vòng 2-3 phút cho mỗi commit.
3. **Xác minh đầy đủ (Full)**: Chỉ kích hoạt kiểm thử toàn diện (E2E, Docker, kiểm tra tương thích) khi có nhãn `ready-for-test` hoặc merge vào `main`.

---

## 🔄 Cấu trúc Workflow

### 1. Light CI (`pr-light.yml`)

* **Kích hoạt**: Mọi PR mới mở hoặc khi có commit mới đẩy lên PR.
* **Thời gian chạy**: ~2-3 phút.
* **Nội dung kiểm tra**:
  * Linting và kiểm tra kiểu dữ liệu cho Backend (ruff, mypy)
  * Linting và kiểm tra kiểu dữ liệu cho Frontend (eslint, tsc)
  * Unit tests cho Backend (không gọi API AI bên ngoài)
  * Build Frontend để kiểm tra không có lỗi biên dịch

### 2. Full CI (`pr-full.yml` / `main.yml`)

* **Kích hoạt**:
  * Khi gán nhãn `ready-for-test` vào PR
  * Khi merge vào nhánh `main`
* **Thời gian chạy**: ~10-15 phút.
* **Nội dung kiểm tra**:
  * Toàn bộ các bước của Light CI
  * Kiểm thử môi trường Docker Compose
  * Playwright E2E tests (kiểm tra toàn bộ luồng tạo slide)
  * Kiểm tra tính tương thích của browser runner

---

## 🛠️ Hướng dẫn chạy kiểm thử cục bộ

### Chạy kiểm tra nhanh (Light checks)
```bash
# Backend
cd backend
pytest tests/unit

# Frontend
cd frontend
npm run lint
npm run build
```

### Chạy kiểm tra đầy đủ (E2E & Docker)
```bash
# Kiểm tra Docker build
docker compose build

# Chạy test Docker
./scripts/test_docker_environment.sh
```

---

## ❓ Câu hỏi thường gặp (FAQ)

### Q1: Kiểm thử E2E bị timeout?
* **Nguyên nhân**: Quá trình sinh ảnh/nội dung AI mất nhiều thời gian hoặc kết nối mạng không ổn định.
* **Giải pháp**: Kiểm tra API key và quota dịch vụ AI; chạy test cục bộ với `npx playwright test`.

### Q2: Build Frontend thất bại?
* **Nguyên nhân**: Lỗi TypeScript hoặc cú pháp không hợp lệ.
* **Giải pháp**: Chạy `npm run build` ở thư mục `frontend/` để kiểm tra chi tiết lỗi.

---
**Đội ngũ phát triển Banana Slides**
