import fetch from 'node-fetch';
import FormData from 'form-data';
import fs from 'fs';
import path from 'path';

const BASE_URL = process.env.BASE_URL || 'http://localhost:5401';

// Tạo dự án
async function createProject(title) {
  const response = await fetch(`${BASE_URL}/api/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      creation_type: 'idea',
      idea_prompt: title,
      template_style: 'Phong cách doanh nghiệp tối giản',
      image_aspect_ratio: '16:9'
    })
  });
  const data = await response.json();
  return data.data.project_id;
}

// Tạo tệp kiểm thử tạm thời
function createTempFile(filename, content) {
  const tempDir = '/tmp/test-attachments';
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }
  const filepath = path.join(tempDir, filename);
  fs.writeFileSync(filepath, content);
  return filepath;
}

// Tải lên tệp tham chiếu
async function uploadFile(projectId, filename, content) {
  const filepath = createTempFile(filename, content);
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filepath));
  if (projectId) {
    formData.append('project_id', projectId);
  }

  const response = await fetch(`${BASE_URL}/api/reference-files`, {
    method: 'POST',
    body: formData
  });

  fs.unlinkSync(filepath);
  return response.json();
}

async function main() {
  console.log('Creating test projects and attachments...\n');

  const projects = [
    'Bài thuyết trình ra mắt sản phẩm',
    'Báo cáo kết quả kinh doanh quý',
    'Chiến lược tiếp thị thị trường',
    'Thiết kế kiến trúc kỹ thuật',
    'Tài liệu đào tạo đội ngũ'
  ];

  for (const title of projects) {
    console.log(`Creating project: ${title}`);
    const projectId = await createProject(title);

    // Tải lên 2-3 tệp cho mỗi dự án
    const fileCount = Math.floor(Math.random() * 2) + 2;
    for (let i = 0; i < fileCount; i++) {
      const filename = `${title.substring(0, 8)}_tai_lieu_${i + 1}.txt`;
      const content = `Đây là tài liệu tham khảo ${i + 1} cho ${title}\nThời gian tạo: ${new Date().toISOString()}`;
      await uploadFile(projectId, filename, content);
      console.log(`  - Uploaded: ${filename}`);
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  }

  // Tải lên một số tệp toàn cục (không gắn với dự án cụ thể)
  console.log('\nCreating global attachments...');
  const globalFiles = ['Mau_chung.txt', 'Huong_dan_Logo_cong_ty.txt', 'Cam_nang_thuong_hieu.txt'];
  for (const filename of globalFiles) {
    await uploadFile(null, filename, `Tệp toàn cục: ${filename}\n${new Date().toISOString()}`);
    console.log(`  - Uploaded: ${filename}`);
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  console.log('\n✅ Test data created successfully!');
}

main().catch(console.error);
