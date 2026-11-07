#!/bin/bash
BASE_URL="http://localhost:5401"

echo "Creating test projects and attachments..."

# Tạo dự án và tải lên tệp
projects=("Bai thuyet trinh ra mat san pham" "Bao cao ket qua kinh doanh quy" "Chien luoc tiep thi thi truong" "Thiet ke kien truc ky thuat" "Tai lieu dao tao doi ngu")

for title in "${projects[@]}"; do
  echo -e "\nCreating project: $title"
  
  # Tạo dự án
  response=$(curl -s -X POST "$BASE_URL/api/projects" \
    -H "Content-Type: application/json" \
    -d "{\"creation_type\":\"idea\",\"idea_prompt\":\"$title\",\"template_style\":\"Phong cách doanh nghiệp tối giản\",\"image_aspect_ratio\":\"16:9\"}")
  
  project_id=$(echo $response | grep -o '"project_id":"[^"]*"' | cut -d'"' -f4)
  
  if [ -n "$project_id" ]; then
    # Tải lên 2-3 tệp cho mỗi dự án
    for i in {1..3}; do
      filename="${title:0:8}_tai_lieu_${i}.txt"
      echo "Đây là tài liệu tham khảo $i cho $title" > /tmp/test_file.txt
      
      curl -s -X POST "$BASE_URL/api/reference-files" \
        -F "file=@/tmp/test_file.txt;filename=$filename" \
        -F "project_id=$project_id" > /dev/null
      
      echo "  - Uploaded: $filename"
      sleep 0.2
    done
  fi
done

# Tải lên tệp toàn cục
echo -e "\nCreating global attachments..."
for name in "Mau_chung" "Huong_dan_Logo_cong_ty" "Cam_nang_thuong_hieu"; do
  filename="${name}.txt"
  echo "Tệp toàn cục: $filename" > /tmp/test_file.txt
  
  curl -s -X POST "$BASE_URL/api/reference-files" \
    -F "file=@/tmp/test_file.txt;filename=$filename" > /dev/null
  
  echo "  - Uploaded: $filename"
  sleep 0.2
done

rm -f /tmp/test_file.txt
echo -e "\n✅ Test data created successfully!"
