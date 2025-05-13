# 🧠 RAGify - Lightweight RAG Service with FastAPI, FAISS, and OpenAI

**RAGify** is a minimal and powerful **Retrieval-Augmented Generation (RAG)** service built with **FastAPI**, **FAISS**, and **OpenAI API**.
It allows you to **upload PDF or CSV documents, store them as vector embeddings locally using FAISS, and chat with them using OpenAI's GPT models.**

---

## 🚀 Features

- Upload and parse **PDF** and **CSV** files.
- Embeds documents using **local SentenceTransformer (MiniLM-L6-v2)** or **OpenAI Embeddings**.
- Stores vectors efficiently using **FAISS local index**.
- **Chat** with your documents using **OpenAI GPT models (like GPT-3.5-Turbo)**.
- Lightweight and privacy-friendly (documents never leave your machine).
- Duplicate file uploads are automatically detected using **SHA256 hashing**.
- Simple to run locally or in Docker.

---

## 🛠️ Installation

### 🔧 Running Locally (Recommended for development)

1. Clone the repository:
```bash
git clone https://github.com/your-username/ragify.git
cd rag-service
```

2.	Create .env file in the root:
 ```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

3.	Install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4.	Run the FastAPI server:
```bash
uvicorn app.main:app --reload
```
5.	Visit:
  
•	Swagger Docs: http://localhost:8000/docs <br>
•	ReDoc: http://localhost:8000/redoc

### 🐳 Running with Docker <br>
1.	Build the image:
```bash
docker build -t rag-service .
```

2.	Run the container:
```bash
docker run --env-file .env -p 8000:8000 ragify
```

## 💡 API Usage Example

1. Upload a File
	•	POST /upload
	•	Body: form-data
	•	file: (upload your .pdf or .csv)

2. Chat with your data
	•	POST /chat
	•	Query Params:
	•	user_input: "What is this document about?"
	•	session_id: "my-session-id"

Memory is session-based and persists only while the server runs.

---

## 📜 License

This project is licensed under the MIT License.
Feel free to use, modify, and distribute it.

---

## 🤝 Contributing

Contributions are welcome!
	1.	Fork the repo
	2.	Create your feature branch (git checkout -b feature/awesome-feature)
	3.	Commit your changes (git commit -m 'Add amazing feature')
	4.	Push to the branch (git push origin feature/awesome-feature)
	5.	Open a Pull Request

