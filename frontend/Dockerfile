# Tham số cấu hình nguồn mirror (có thể ghi đè qua build args)
ARG DOCKER_REGISTRY=
ARG NPM_REGISTRY=
ARG APP_VERSION_TAG=
ARG APP_COMMIT_SHA=
ARG APP_COMMIT_SHORT_SHA=

# Giai đoạn build
# Nếu chỉ định DOCKER_REGISTRY thì dùng mirror; ngược lại dùng nguồn chính thức
FROM ${DOCKER_REGISTRY:-}node:18-alpine AS builder

# Khai báo lại ARG (sau FROM phạm vi ARG bị đặt lại)
ARG NPM_REGISTRY=
ARG APP_VERSION_TAG=
ARG APP_COMMIT_SHA=
ARG APP_COMMIT_SHORT_SHA=
ENV VITE_APP_VERSION_TAG=${APP_VERSION_TAG}
ENV VITE_APP_COMMIT_SHA=${APP_COMMIT_SHA}
ENV VITE_APP_COMMIT_SHORT_SHA=${APP_COMMIT_SHORT_SHA}

WORKDIR /app

# Sao chép package.json
COPY frontend/package.json ./

# Cài đặt phụ thuộc (nếu cấu hình NPM_REGISTRY thì đặt nguồn mirror trước)
COPY frontend/package-lock.json* ./
RUN if [ -n "$NPM_REGISTRY" ]; then \
        npm config set registry "$NPM_REGISTRY"; \
    fi && \
    (npm install --frozen-lockfile || npm install)

# Sao chép mã nguồn frontend
COPY frontend/ ./

# Dựng ứng dụng
# Triển khai web cần phân giải tài nguyên từ gốc trên các đường dẫn lồng nhau.
RUN npm run build:web

# Giai đoạn production
# Nếu chỉ định DOCKER_REGISTRY thì dùng mirror; ngược lại dùng nguồn chính thức
FROM ${DOCKER_REGISTRY:-}nginx:alpine

# Sao chép sản phẩm build sang nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Sao chép tệp cấu hình nginx
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Mở cổng
EXPOSE 80

# Khởi động nginx
CMD ["nginx", "-g", "daemon off;"]
