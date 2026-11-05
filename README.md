# IT Skill Matching & Recommendation System

Hệ thống gợi ý việc làm IT thông minh dựa trên phân tích cấu trúc và ngữ nghĩa (Semantic & Structural Analysis) của CV ứng viên, so khớp với các bản mô tả công việc (Job Description) từ cơ sở dữ liệu.

## 🌟 Tính năng chính

- **Crawler tự động:** Thu thập dữ liệu việc làm IT mới nhất từ các nguồn quốc tế (Arbeitnow, Jobicy).
- **Xử lý CV/JD thông minh:**
  - Trích xuất văn bản từ PDF (hỗ trợ layout 1 cột và 2 cột).
  - Nhận diện cấu trúc Section (SKILLS, EXPERIENCE, PROJECTS...).
  - Phân loại nội dung JD (REQUIREMENT, RESPONSIBILITY).
- **Semantic Chunking:** Cắt nhỏ văn bản dựa trên sự thay đổi ngữ nghĩa (sử dụng Cosine Distance) thay vì cắt máy móc theo số từ.
- **AI Matching (pgvector):**
  - Mã hóa văn bản thành vector 384 chiều (`all-MiniLM-L6-v2`).
  - Tính điểm tương đồng Cosine với thuật toán Top-K Requirements.
  - Áp dụng hệ số suy giảm thời gian (Recency Decay) ưu tiên tin mới.
- **Web App (FastAPI):** Giao diện kéo thả CV, phân trang danh sách công việc và cập nhật dữ liệu trực quan.

## 🛠 Tech Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn.
- **Database:** PostgreSQL 16 + `pgvector` (HNSW Index).
- **AI/ML:** SentenceTransformers, PyTorch, NumPy.
- **Frontend:** HTML5, CSS3, Vanilla JavaScript.

## 📁 Cấu trúc thư mục

```text
.
├── data/                  # Chứa file keywords.yaml và dữ liệu test
├── docker-compose.yml     # Cấu hình Docker cho PostgreSQL
├── public/                # Giao diện Frontend (HTML/CSS/JS)
├── scripts/               # Các công cụ CLI (Backfill, Inspect, Test)
├── src/
│   ├── config/            # Cấu hình Pydantic Settings
│   ├── controllers/       # FastAPI Routers (Jobs, Matching)
│   ├── models/            # Entities và Repositories (DB queries)
│   ├── services/
│   │   ├── embeddings/    # Model AI và hàm encode vector
│   │   ├── matching/      # Lõi Matching, Scoring và Indexing
│   │   ├── processing/    # Bóc tách CV, xử lý JD, Chunking
│   │   └── sources/       # Crawlers (Arbeitnow, Jobicy)
│   └── utils/             # Các hàm dùng chung
├── server.py              # Entry point khởi chạy server
├── requirements.txt       # Danh sách thư viện
└── .env.example           # Mẫu biến môi trường
```
