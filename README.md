# IT Skill Matching & Recommendation System

Hệ thống gợi ý việc làm IT thông minh dựa trên phân tích cấu trúc, ngữ nghĩa (Semantic & Structural Chunking) của CV ứng viên và so khớp với các bản mô tả công việc (Job Description) từ cơ sở dữ liệu.

---

## 🌟 Tính năng chính

- **Bóc tách CV thông minh:** Trích xuất các đề mục cốt lõi (`SKILLS`, `EXPERIENCE`, `PROJECTS`,...) từ file CV định dạng `.pdf`.
- **Semantic & Structured Chunking:** Phân đoạn văn bản ngữ nghĩa và mã hóa vector nhúng (Embedding) bằng `sentence-transformers`.
- **So khớp & Chấm điểm (Matching & Scoring):**
  - Tính toán độ tương đồng Cosine giữa yêu cầu công việc và nội dung CV.
  - Lọc công việc Senior phù hợp với cấp độ ứng viên.
  - Áp dụng hệ số suy giảm thời gian (Decay multiplier) ưu tiên các tin tuyển dụng mới nhất.
- **Giao diện Web tương tác (Fullstack):**
  - Kéo thả file PDF CV trực quan.
  - Hiển thị bảng Top 10 việc làm phù hợp nhất kèm link tuyển dụng gốc.
  - Nút chuyển hướng xem danh sách việc làm hiện có trực tiếp dưới phần tải CV.
  - Danh sách toàn bộ việc làm IT có hỗ trợ phân trang (Pagination).
  - Tích hợp nút cào & cập nhật dữ liệu việc làm IT mới nhất từ các nguồn (Jobicy, Arbeitnow) với thông báo trạng thái trực quan.
  - Hỗ trợ truy cập đa thiết bị trong mạng LAN (`0.0.0.0`).

---

## 📁 Cấu trúc thư mục

```text
IT-Skill-Matching/
├── database/            # Quản lý kết nối SQLite và CRUD Job repository
│   ├── connection.py
│   └── job_repository.py
├── src/
│   ├── matching/        # Thuật toán so khớp vector và chấm điểm
│   │   ├── chunk_job_scorer.py
│   │   └── chunk_similarity_matcher.py
│   ├── pipeline/        # Service tích hợp luồng gợi ý công việc & cập nhật data
│   │   ├── matching_service.py
│   │   └── update_jobs.py
│   └── processing/      # Xử lý CV & JD (Chunking, filtering, lifecycle)
│       ├── cv_chunker.py
│       ├── cv_structure.py
│       ├── jd_chunker.py
│       ├── job_filter.py
│       ├── job_lifecycle.py
│       └── semantic_chunker.py
├── web/                 # Giao diện Frontend (HTML, CSS, JS)
│   ├── home.html
│   ├── main.js
│   └── style.css
├── server.py            # FastAPI Backend server phục vụ API & Static web
├── start.bat            # Script khởi chạy nhanh hệ thống (1-click)
├── requirements.txt     # Danh sách các thư viện phụ thuộc
└── README.md
```

---

## 🚀 Hướng dẫn cài đặt & Khởi chạy

### 1. Yêu cầu hệ thống
- Python 3.10+
- Môi trường Windows / Linux / macOS

### 2. Cài đặt môi trường ảo & Thư viện
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo
# Trên Windows:
.venv\Scripts\activate
# Trên Linux/macOS:
source .venv/bin/activate

# Cài đặt các gói phụ thuộc
pip install -r requirements.txt
```

### 3. Khởi chạy hệ thống

#### Cách 1: Sử dụng file chạy nhanh (Khuyên dùng trên Windows)
Nhấp đúp chuột hoặc chạy lệnh trong terminal:
```bat
.\start.bat
```

#### Cách 2: Chạy thủ công với Uvicorn
```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## 🌐 Truy cập ứng dụng

- **Trên máy tính hiện tại:** Mở trình duyệt và truy cập `http://127.0.0.1:8000` hoặc `http://localhost:8000`.
- **Từ thiết bị khác trong cùng mạng LAN/Wi-Fi:** Truy cập qua địa chỉ IP máy chủ:
  ```text
  http://<IP_MAY_BAN>:8000
  ```
  *(Ví dụ: `http://172.22.5.135:8000`)*.