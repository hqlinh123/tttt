FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir uv

COPY pyproject.toml uv.lock /app/

RUN uv sync \
    --frozen \
    --no-dev \
    --no-editable

# Temporary patch for broken fastapi-mail package
RUN python -c "from pathlib import Path; \
p=Path('/app/.venv/lib/python3.12/site-packages/fastapi_mail/config.py'); \
s=p.read_text(); \
s=('from pydantic import SecretStr\n' + s) if 'from pydantic import SecretStr' not in s else s; \
p.write_text(s)"

COPY . /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

CMD ["/bin/sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]