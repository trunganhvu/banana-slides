# Project notes

## Bản địa hóa Tiếng Việt & Tiếng Anh (Quan trọng cho mọi Agent)
- Xem chi tiết đầy đủ tại `AGENT_HANDOFF.md`.
- Dự án đã được bản địa hóa hoàn toàn sang **Tiếng Việt (mặc định)** và **Tiếng Anh**, với quy tắc nghiêm ngặt **0 ký tự tiếng Trung (CJK)** trong toàn bộ tệp văn bản/mã nguồn của dự án.
- Giữ nguyên **100% logic nghiệp vụ**. Trên Frontend (`frontend/src/i18n.ts`), bản dịch tiếng Việt được nạp vào khóa `zh` (và bí danh `vi`) từ `frontend/src/locales/zh.json` để giữ nguyên toàn bộ logic điều kiện hiện có.
- Các trường mở rộng mô tả trang chuẩn: `Hình ảnh & Tư liệu`, `Bố cục & Trọng tâm`, `Ghi chú thuyết trình`. Khi cần ánh xạ tương thích ngược với dữ liệu cũ, bắt buộc sử dụng chuỗi Unicode escape (`\u914d\u56fe\u4e0e\u7d20\u6750`, `\u7248\u5f0f\u4e0e\u91cd\u70b9`, `\u6f14\u8bb2\u8005\u5907\u6ce8`), tuyệt đối không đưa ký tự chữ Hán trực tiếp vào mã nguồn.
- Cổng mặc định: Backend `5011` (trong Docker container là `5000`), Frontend `3011` (trong Docker container là `80`). Môi trường Python local đặt tại `.venv`.

## Quy tắc CI / Docker / E2E
- Các job CI cài đặt phụ thuộc trình duyệt Playwright phải cố định vào hệ điều hành được phiên bản khóa hỗ trợ; khi sửa phải quét toàn bộ workflow (bao gồm PR, nightly, phát hành), chạy `scripts/check_browser_runners.py`, không chỉ sửa nơi đang lỗi. Trước khi nâng cấp runner phải kiểm tra tính tương thích để tránh `ubuntu-latest` trôi phiên bản gây lỗi cài đặt trình duyệt.

- Docker E2E sau khi dựng lại container trong kiểm thử môi trường phải đảm bảo runner máy chủ có quyền ghi vào `uploads`, `backend/instance` và tệp SQLite, đồng thời xác minh giao dịch ghi thực tế; tải xuống PPTX phải lắng nghe sự kiện `download` của Page trước khi nhấp, lưu tệp để nghiệm thu, không dùng mã phản hồi HTTP 200 để thay thế.
- Cấu hình PyPI chính thức của nightly phải đồng bộ URL tệp khóa thông qua `scripts/prepare_nightly_lock.py` ở cả hai job kiểm thử và phát hành; `uv sync --frozen` sẽ không dùng biến môi trường index để ghi đè địa chỉ tải xuống đã khóa, không được né lỗi 403 của mirror bằng cách phân giải lại hoặc nâng cấp phụ thuộc.

- Bản dịch README lấy snapshot đồng bộ thành công trong `docs/i18n/readme-state.json` làm cơ sở; giữ nguyên ID chương mục `i18n`, nộp bản dịch cùng tệp trạng thái. Không dùng `git diff HEAD` trên vùng làm việc CI sạch để tính phần thay đổi, cũng không đối chiếu chương mục bằng tiêu đề văn bản. Xem hướng dẫn bảo trì tại `docs/readme-i18n.md`.

- Hộp công cụ tư liệu của cùng một dự án có thể được gắn đồng thời từ nhiều lối vào; danh sách tác vụ và cơ chế polling phải được chia sẻ theo từng dự án, nghiệm thu việc gửi tác vụ xuyên lối vào, đóng một trong các lối vào và gắn lại, tránh ghi đè tác vụ hoặc polling trùng lặp.

- Nhánh `main` chỉ chứa các tính năng mã nguồn mở chung. Các tính năng riêng của `bananaslides.online` gồm Landing, đăng ký thử nghiệm, phản hồi trên trang, Demo công khai, cách ly khách truy cập, lối vào quản trị viên cùng cấu hình/migration chỉ được đưa vào `production/bananaslides-online`; công tắc tắt mặc định không thay thế cho việc cách ly nhánh. Trước khi tạo nhánh và PR cho tác vụ trang chủ phải kiểm tra nhánh cơ sở và nhánh đích, không tự ý đồng bộ nhánh chính khi chưa có yêu cầu rõ ràng.

- Cơ sở mã nguồn chính thức của `bananaslides.online` là `origin/production/bananaslides-online` (thiết lập ngày 2026-09-27, bao gồm trang chủ trực tuyến và các bản vá backend tại thời điểm đó); mọi thay đổi trang chủ xuất phát từ nhánh này, trước khi phát hành phải đối chiếu lại image trực tuyến và phần khác biệt, không coi nhánh `feat/sponsor` cũ hay `feat/public-site-landing` độc lập là mã nguồn trực tuyến đầy đủ.
- Khi truy cập `bananaslides.online` qua Cloudflare, `urllib` của Python từ phía máy chủ có thể nhận mã 403 ngay cả khi máy chủ gốc và trình duyệt hoạt động bình thường. Khi nghiệm thu phát hành cần kiểm tra riêng mã băm bản dựng trên máy chủ gốc và kết quả `curl` công khai / trình duyệt thực tế; không kết luận triển khai thất bại chỉ vì `urllib` bị chặn ở tầng biên.
- Khi phát hành trang chủ có kèm migration cơ sở dữ liệu, trước tiên phải diễn tập trên bản sao lưu trực tuyến của cơ sở dữ liệu SQLite thực tế, sau đó kiểm tra `alembic_version`, các bảng mới và số dòng dữ liệu hiện có trên bản sao lưu đó; `alembic.ini` trong image không được trỏ tới cơ sở dữ liệu giữ chỗ.
- Frontend trang chủ sử dụng `npm run build:online` (bật `VITE_PUBLIC_LANDING=true`); nghiệm thu sản phẩm phát hành thực tế, tiêu đề landing ở đường dẫn gốc công khai và luồng chuyển hướng Demo, không chỉ kiểm tra HTTP 200.

- Khi gỡ bỏ nhà tài trợ phải xóa toàn bộ lối vào thương hiệu, cấu hình mẫu nhà cung cấp, liên kết đăng ký và hướng dẫn lấy khóa API, đồng thời nghiệm thu theo cả khách truy cập mới lẫn cấu hình đã có; không được chỉ xóa thẻ quảng cáo. Việc giữ tương thích tầng dưới không được biến thành tiếp tục hiển thị hoặc điều hướng người dùng.
