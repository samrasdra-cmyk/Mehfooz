FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uncomment to bake in the real-service integrations (heavy image):
# COPY requirements-full.txt .
# RUN pip install --no-cache-dir -r requirements-full.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
