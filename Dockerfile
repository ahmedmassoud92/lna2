FROM python:3.11-slim

WORKDIR /app
COPY backend/ /app/

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8000
EXPOSE 8000

CMD ["python", "app.py"]
