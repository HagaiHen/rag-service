# Dockerize your RAG service
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Run Instructions:
# 1. Create a .env file with your OpenAI key
# 2. Install dependencies: pip install -r requirements.txt
# 3. Start server: uvicorn app.main:app --reload
# 4. Or build and run Docker: docker build -t rag-service . && docker run -p 8000:8000 rag-service
