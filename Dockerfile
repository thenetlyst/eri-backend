FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -------------------------
# ✅ SYSTEM DEPENDENCIES FIRST
# -------------------------
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    netcat-openbsd \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# ✅ PYTHON DEPENDENCIES
# -------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir py-spy

# -------------------------
# ✅ APP CODE
# -------------------------
COPY . .

# -------------------------
# ✅ DEFAULT CMD (SAFE)
# -------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]