FROM python:3.12-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local

COPY . /app
WORKDIR /app

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Команда запуска (используем python -m)
CMD ["sh", "-c", "while ! nc -z db 5432; do sleep 1; done && \
     python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]