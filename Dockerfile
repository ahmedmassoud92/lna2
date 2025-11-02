FROM python:3.11-slim

# مهم: شهادات SSL واللغة/التوقيت
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates tzdata locales curl \
 && rm -rf /var/lib/apt/lists/*
RUN update-ca-certificates
ENV TZ=UTC
ENV LANG=C.UTF-8

WORKDIR /app
COPY backend/ /app/

# تثبيت المتطلبات
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

ENV PORT=8000
EXPOSE 8000

CMD ["python", "app.py"]
