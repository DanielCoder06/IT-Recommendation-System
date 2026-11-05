FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết cho psycopg2 và pymupdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy và cài đặt requirements
COPY requirements.txt .
# Cài PyTorch bản CPU để giảm dung lượng (tránh tải CUDA nặng)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn
COPY . .

# Mở port 8000
EXPOSE 8000

# Lệnh chạy server
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]