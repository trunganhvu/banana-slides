#!/bin/bash
# Script kiem tra toan dien moi truong Docker
# Kiem tra day du chuc nang cua du an trong moi truong Docker

set -e  # Thoat ngay khi gap loi

# Dinh nghia mau sac
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ham ghi log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Bat dau kiem tra
echo ""
echo "================================="
echo "🐳 Kiem tra toan dien moi truong Docker"
echo "================================="
echo ""

# Kiem tra dieu kien tien quyet
log_info "Kiem tra dieu kien tien quyet..."

if ! command -v docker &> /dev/null; then
    log_error "Docker chua duoc cai dat, vui long cai dat Docker truoc"
    exit 1
fi

if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose chua duoc cai dat"
    exit 1
fi

if [ ! -f ".env" ]; then
    log_warning "File .env khong ton tai, sao chep tu .env.example"
    cp .env.example .env
fi

log_success "Kiem tra dieu kien tien quyet thanh cong"

# 1. Don dep moi truong cu
log_info "Buoc 1/10: Don dep moi truong cu..."
docker compose down -v 2>/dev/null || true
docker system prune -f >/dev/null 2>&1 || true
log_success "Don dep moi truong hoan tat"

# 2. Xay dung image
log_info "Buoc 2/10: Xay dung Docker image..."
if docker compose build --no-cache; then
    log_success "Xay dung image thanh cong"
else
    log_error "Xay dung image that bai"
    exit 1
fi

# 3. Khoi dong dich vu
log_info "Buoc 3/10: Khoi dong dich vu Docker..."
if docker compose up -d; then
    log_success "Khoi dong dich vu thanh cong"
else
    log_error "Khoi dong dich vu that bai"
    docker compose logs
    exit 1
fi

# 4. Cho dich vu san sang
log_info "Buoc 4/10: Cho dich vu san sang (toi da 60 giay)..."
max_wait=60
waited=0
backend_ready=false
frontend_ready=false

while [ $waited -lt $max_wait ]; do
    # Kiem tra backend
    if curl -s http://localhost:5011/health >/dev/null 2>&1; then
        backend_ready=true
    fi
    
    # Kiem tra frontend
    if curl -s http://localhost:3011 >/dev/null 2>&1; then
        frontend_ready=true
    fi
    
    if [ "$backend_ready" = true ] && [ "$frontend_ready" = true ]; then
        break
    fi
    
    sleep 2
    waited=$((waited + 2))
    echo -n "."
done
echo ""

if [ "$backend_ready" = false ] || [ "$frontend_ready" = false ]; then
    log_error "Khoi dong dich vu qua thoi gian cho"
    log_info "Xem trang thai container:"
    docker compose ps
    log_info "Xem log backend:"
    docker compose logs backend
    log_info "Xem log frontend:"
    docker compose logs frontend
    exit 1
fi

log_success "Dich vu da san sang (mat ${waited} giay)"

# 5. Kiem tra trang thai suc khoe container
log_info "Buoc 5/10: Kiem tra trang thai container..."
backend_status=$(docker compose ps backend | grep -c "Up" || echo "0")
frontend_status=$(docker compose ps frontend | grep -c "Up" || echo "0")

if [ "$backend_status" -eq "0" ] || [ "$frontend_status" -eq "0" ]; then
    log_error "Trang thai container bat thuong"
    docker compose ps
    exit 1
fi
log_success "Trang thai container binh thuong"

# 6. Kiem tra suc khoe backend
log_info "Buoc 6/10: Kiem tra suc khoe backend..."
backend_health=$(curl -s http://localhost:5011/health)
if echo "$backend_health" | grep -q '"status":"ok"'; then
    log_success "Kiem tra suc khoe backend thanh cong"
    echo "    Phan hoi: $backend_health"
else
    log_error "Kiem tra suc khoe backend that bai"
    echo "    Phan hoi: $backend_health"
    exit 1
fi

# 7. Kiem tra truy cap frontend
log_info "Buoc 7/10: Kiem tra truy cap frontend..."
frontend_status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3011)
if [ "$frontend_status_code" = "200" ]; then
    log_success "Truy cap frontend binh thuong (HTTP $frontend_status_code)"
else
    log_error "Truy cap frontend that bai (HTTP $frontend_status_code)"
    exit 1
fi

# 8. Kiem tra chuc nang API
log_info "Buoc 8/10: Kiem tra chuc nang API..."

# 8.1 Tao du an
log_info "  8.1 Tao du an..."
create_response=$(curl -s -X POST http://localhost:5011/api/projects \
    -H "Content-Type: application/json" \
    -d '{"creation_type":"idea","idea_prompt":"Du an thu nghiem Docker"}')

if echo "$create_response" | grep -q '"success":true'; then
    project_id=$(echo "$create_response" | grep -o '"project_id":"[^"]*"' | cut -d'"' -f4)
    log_success "  Tao du an thanh cong: $project_id"
else
    log_error "  Tao du an that bai"
    echo "    Phan hoi: $create_response"
    exit 1
fi

# 8.2 Lay chi tiet du an
log_info "  8.2 Lay chi tiet du an..."
get_response=$(curl -s http://localhost:5011/api/projects/$project_id)
if echo "$get_response" | grep -q '"success":true'; then
    log_success "  Lay chi tiet du an thanh cong"
else
    log_error "  Lay chi tiet du an that bai"
    exit 1
fi

# 8.3 Tai len mau (neu ton tai)
if [ -f "template_g.png" ]; then
    log_info "  8.3 Tai len file mau..."
    upload_response=$(curl -s -X POST http://localhost:5011/api/projects/$project_id/template \
        -F "template_image=@template_g.png")
    
    if echo "$upload_response" | grep -q '"success":true'; then
        log_success "  Tai len mau thanh cong"
    else
        log_warning "  Tai len mau that bai (khong nghiem trong)"
    fi
else
    log_warning "  8.3 Bo qua tai len mau (file khong ton tai)"
fi

# 8.4 Xoa du an (don dep)
log_info "  8.4 Xoa du an thu nghiem..."
delete_response=$(curl -s -X DELETE http://localhost:5011/api/projects/$project_id)
if echo "$delete_response" | grep -q '"success":true'; then
    log_success "  Xoa du an thanh cong"
else
    log_warning "  Xoa du an that bai (khong nghiem trong)"
fi

log_success "Kiem tra chuc nang API thanh cong"

# 9. Kiem tra luu tru du lieu ben vung
log_info "Buoc 9/10: Kiem tra luu tru du lieu ben vung..."

# Tao mot du an
create_response=$(curl -s -X POST http://localhost:5011/api/projects \
    -H "Content-Type: application/json" \
    -d '{"creation_type":"idea","idea_prompt":"Kiem tra luu tru ben vung"}')
persist_project_id=$(echo "$create_response" | grep -o '"project_id":"[^"]*"' | cut -d'"' -f4)

# Khoi dong lai container backend
log_info "  Khoi dong lai container backend..."
docker compose restart backend
sleep 5

# Cho backend khoi phuc
for i in {1..30}; do
    if curl -s http://localhost:5011/health >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Kiem tra xem du an con ton tai khong
persist_check=$(curl -s http://localhost:5011/api/projects/$persist_project_id)
if echo "$persist_check" | grep -q '"success":true'; then
    log_success "Kiem tra luu tru du lieu ben vung thanh cong"
else
    log_error "Kiem tra luu tru du lieu ben vung that bai"
    exit 1
fi

# Don dep du lieu thu nghiem
curl -s -X DELETE http://localhost:5011/api/projects/$persist_project_id >/dev/null

# 10. Kiem tra log
log_info "Buoc 10/10: Kiem tra log container co loi khong..."
backend_errors=$(docker compose logs backend 2>&1 | grep -i "error\|exception\|traceback" | grep -v "DEBUG" | wc -l)
frontend_errors=$(docker compose logs frontend 2>&1 | grep -i "error" | grep -v "warn" | wc -l)

if [ "$backend_errors" -gt 5 ]; then
    log_warning "Phat hien $backend_errors loi trong log backend"
    docker compose logs backend | grep -i "error\|exception" | tail -10
else
    log_success "Kiem tra log backend thanh cong ($backend_errors loi)"
fi

if [ "$frontend_errors" -gt 5 ]; then
    log_warning "Phat hien $frontend_errors loi trong log frontend"
else
    log_success "Kiem tra log frontend thanh cong ($frontend_errors loi)"
fi

# Tong ket kiem tra
echo ""
echo "================================="
echo "✅ Hoan tat kiem tra moi truong Docker"
echo "================================="
echo ""
echo "📊 Tom tat kiem tra:"
echo "  ✓ Xay dung image"
echo "  ✓ Khoi dong dich vu"
echo "  ✓ Kiem tra suc khoe"
echo "  ✓ Chuc nang API"
echo "  ✓ Luu tru du lieu ben vung"
echo "  ✓ Kiem tra log"
echo ""
echo "🎯 Buoc tiep theo:"
echo "  1. Chay kiem tra API day du: cd backend && python ../tests/test_e2e.py"
echo "  2. Chay kiem tra E2E: npx playwright test"
echo "  3. Dung moi truong: docker compose down"
echo ""

# Hoi co don dep moi truong khong
if [ "${AUTO_CLEANUP}" != "false" ]; then
    read -p "Ban co muon dung moi truong Docker khong? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Dang dung moi truong Docker..."
        docker compose down
        log_success "Da don dep moi truong"
    else
        log_info "Giu moi truong chay, co the dung thu cong: docker compose down"
    fi
fi

exit 0
