# Tham số cấu hình nguồn mirror (có thể ghi đè qua build args)
ARG DOCKER_REGISTRY=
ARG GHCR_REGISTRY=ghcr.io/
ARG APT_MIRROR=
ARG PYPI_INDEX_URL=
ARG APP_VERSION_TAG=
ARG APP_COMMIT_SHA=
ARG APP_COMMIT_SHORT_SHA=
ARG APP_BUILD_DATE=

# Cài đặt uv (sử dụng giai đoạn trung gian để tránh lỗi mở rộng biến trong COPY --from)
FROM ${GHCR_REGISTRY}astral-sh/uv:latest AS uv

# Sử dụng Python 3.10 làm image cơ sở
# Nếu chỉ định DOCKER_REGISTRY thì dùng mirror; ngược lại dùng nguồn chính thức
FROM ${DOCKER_REGISTRY:-}python:3.10-slim

# Khai báo lại ARG (sau FROM phạm vi ARG bị đặt lại)
ARG APT_MIRROR=
ARG PYPI_INDEX_URL=
ARG APP_VERSION_TAG=
ARG APP_COMMIT_SHA=
ARG APP_COMMIT_SHORT_SHA=
ARG APP_BUILD_DATE=

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt phụ thuộc hệ thống (nếu cấu hình APT_MIRROR thì thay thế nguồn trước)
RUN if [ -n "$APT_MIRROR" ]; then \
        if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
            sed -i "s@deb.debian.org@$APT_MIRROR@g" /etc/apt/sources.list.d/debian.sources; \
        else \
            echo "Warning: /etc/apt/sources.list.d/debian.sources not found, skipping mirror setup." >&2; \
        fi; \
    fi && \
    apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Sao chép tệp thực thi từ giai đoạn uv
COPY --from=uv /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

# Sao chép tệp cấu hình dự án
COPY pyproject.toml ./
COPY uv.lock* ./

# Cấu hình nguồn mirror PyPI (nếu chỉ định)
ENV UV_INDEX_URL=${PYPI_INDEX_URL}

# Cấu hình thời gian chờ mạng cho uv
ENV UV_HTTP_TIMEOUT=300

# Cài đặt phụ thuộc Python
# Nếu có tệp uv.lock thì sử dụng --frozen, ngược lại tạo tệp khóa mới
RUN if [ -f uv.lock ]; then \
        uv sync --frozen --no-install-project; \
    else \
        uv sync --no-install-project; \
    fi

# Sao chép mã nguồn backend
COPY backend/ ./backend/

# Sao chép tài nguyên kiểm thử và biểu tượng
COPY assets/ ./assets/

# Tạo các thư mục cần thiết
RUN mkdir -p /app/backend/instance /app/uploads

ENV PYTHONPATH=/app
ENV FLASK_APP=backend/app.py
# Trong container cố định lắng nghe cổng 5000; cổng máy chủ do BACKEND_PORT trong docker-compose điều khiển
ENV IN_DOCKER=1
ENV APP_VERSION_TAG=${APP_VERSION_TAG}
ENV APP_COMMIT_SHA=${APP_COMMIT_SHA}
ENV APP_COMMIT_SHORT_SHA=${APP_COMMIT_SHORT_SHA}
ENV APP_BUILD_DATE=${APP_BUILD_DATE}
ENV DOCKERHUB_REPOSITORY=banana-slides-backend

# Mở cổng
EXPOSE 5000

# Container sử dụng cố định cổng 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["sh", "-c", "curl -f http://localhost:5000/health || exit 1"]

# Khởi động ứng dụng. Sử dụng trực tiếp môi trường ảo đã đồng bộ ở bước build để tránh phải kết nối mạng tải lại khi khởi chạy.
CMD ["sh", "-c", "cd /app/backend && /app/.venv/bin/alembic upgrade head && exec /app/.venv/bin/python app.py"]
