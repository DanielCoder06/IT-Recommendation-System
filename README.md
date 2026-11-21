# RSIT - IT Recommendation System

Hệ thống gợi ý việc làm IT dựa trên phân tích ngữ nghĩa (Semantic Similarity).

RSIT cho phép người dùng tải CV định dạng PDF, phân tích nội dung và so khớp với dữ liệu tuyển dụng để tìm ra những công việc phù hợp nhất.

## 🚀 Công nghệ sử dụng

- **Backend:** Python, FastAPI, Uvicorn.
- **Frontend:** HTML, CSS, Vanilla JavaScript.
- **Database:** PostgreSQL, pgvector.
- **AI/ML:** Sentence Transformers (`all-MiniLM-L6-v2`).
- **PDF Processing:** PyMuPDF.
- **Deployment:** Docker, Docker Compose.

## ⚙️ Cài đặt

**1. Clone dự án**

```bash
git clone <repository-url>
cd IT-Recommendation-System
```

**2. Tạo file môi trường**

```bash
cp .env.example .env
```

**3. Khởi động Database**

```bash
docker compose up -d postgres
```

**4. Tạo môi trường Python**

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**5. Khởi chạy hệ thống**

```bash
python server.py
```

Truy cập: http://localhost:8000

## 📌 Chức năng chính

- Thu thập việc làm từ Jobicy và Arbeitnow.
- Trích xuất và phân tích nội dung CV.
- Phân tích và chia nhỏ nội dung JD.
- Tạo vector embedding bằng Sentence Transformers.
- So khớp CV với Requirements và Responsibilities của JD.
- Xếp hạng và đề xuất Top-K công việc phù hợp.

## 🐳 Docker Commands

```bash
# Khởi động Database
docker compose start postgres

# Dừng Database
docker compose stop postgres

# Xem trạng thái
docker compose ps

# Xem log
docker compose logs -f postgres

# Xóa Database và dữ liệu
docker compose down -v
```

**Lưu ý:** Lệnh `docker compose down -v` sẽ xóa dữ liệu database được lưu trong volume.

---

**Developed by:** [Nguyễn Minh Khôi]

**_Đồ án Niên Luận Cơ Sở Ngành_**
