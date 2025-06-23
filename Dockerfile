FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libpq-dev \
    gcc \
    build-essential \
    libfreetype6 \
    libfreetype6-dev \
    libjpeg-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    tk-dev \
    tcl-dev \
    zlib1g-dev \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Удаляем предварительную установку reportlab
# Теперь — остальные зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]