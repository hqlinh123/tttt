# Sử dụng Python 3.10-slim để tương thích tối đa với thư viện AI/Audio
FROM python:3.10-slim

WORKDIR /app

# Cài đặt các gói hệ thống bắt buộc cho việc xử lý âm thanh và build wheel
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt công cụ quản lý gói uv
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir uv

COPY pyproject.toml uv.lock /app/

# SỬA LỖI: Bỏ --no-editable để uv nạp đầy đủ các gói cấu hình nội bộ nếu có
RUN uv sync \
    --frozen \
    --no-dev

# Vá lỗi gói fastapi-mail tương thích phiên bản python 3.10
RUN python -c "from pathlib import Path; \
p=Path('/app/.venv/lib/python3.10/site-packages/fastapi_mail/config.py'); \
s=p.read_text() if p.exists() else ''; \
if s: \
    s=('from pydantic import SecretStr\n' + s) if 'from pydantic import SecretStr' not in s else s; \
    p.write_text(s)"

COPY . /app

# Đảm bảo các thư mục lưu trữ tĩnh được ánh xạ trong main.py được khởi tạo sẵn
RUN mkdir -p wavs outputs uploads temp outputs/ai-videos videos video-images

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

# Chạy đúng module main:app theo mô hình Application Factory
CMD ["/bin/sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
