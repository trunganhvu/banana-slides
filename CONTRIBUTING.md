# Contributing to Banana-slides

Thank you for your interest in contributing to Banana-slides! We welcome contributions from the community.

## Before You Start

### Contributor License Agreement (CLA)

By submitting a Pull Request (or any other Contribution intended for inclusion) to this repository, you confirm that you have read and agree to the terms of our [Contributor License Agreement (CLA)](CLA.md).
If you do not agree to the CLA, please do not submit a Pull Request.

**Why do we need a CLA?**

- To ensure we have the necessary rights to use, modify, and distribute contributions
- To allow the project to explore sustainable commercial models while keeping the open-source edition available
- To protect both contributors and the project legally

**How to agree:**

When you open a Pull Request, the PR template includes a CLA checkbox. Simply check it to indicate your agreement. PRs without the CLA checkbox checked may be delayed or closed.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/Anionex/banana-slides/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - Expected behavior vs actual behavior
   - Screenshots if applicable
   - Your environment (OS, browser, etc.)

### Suggesting Features

1. Check existing issues for similar suggestions
2. Create a new issue with the "feature request" label
3. Describe the feature and its use case

### Submitting Code

1. Fork the repository
2. Create a new branch for your feature/fix: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test your changes thoroughly
5. Commit with clear, descriptive messages
6. Push to your fork
7. Open a Pull Request with:
   - A clear description of the changes
   - Reference to any related issues
   - **CLA checkbox checked** (PRs without this may be delayed/closed)

## Development Setup

### Yêu cầu môi trường / Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) - Trình quản lý gói Python (Python package manager)
- Node.js 16+ và npm
- Khóa API hợp lệ (xem chi tiết trong `.env.example`)

### Các bước cài đặt / Installation

```bash
# Sao chép kho mã nguồn (Clone repository)
git clone https://github.com/Anionex/banana-slides.git
cd banana-slides

# Cài đặt uv (nếu chưa cài đặt)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Cài đặt phụ thuộc backend (chạy tại thư mục gốc của dự án)
uv sync

# Cấu hình biến môi trường
cp .env.example .env
# Chỉnh sửa tệp .env và điền khóa API của bạn

# Cài đặt phụ thuộc frontend
cd frontend
npm install
```

### Khởi động máy chủ phát triển / Start Development Server

```bash
# Khởi động backend (tại thư mục gốc của dự án)
cd backend
uv run alembic upgrade head && uv run python app.py
# Backend chạy tại http://localhost:5011

# Khởi động frontend (mở một cửa sổ dòng lệnh mới)
cd frontend
npm run dev
# Frontend chạy tại http://localhost:3011
```

## Code Style

- Follow the existing code style in the project
- Write clear, self-documenting code
- Add comments for complex logic
- Include tests for new features when applicable

## Questions?

If you have questions, feel free to open an issue or reach out to the maintainers.

---

Thank you for contributing to Banana-slides! 🍌
