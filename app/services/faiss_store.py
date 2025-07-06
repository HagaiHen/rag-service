import os
from typing import List
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore import InMemoryDocstore
from langchain.schema import Document
from dotenv import load_dotenv

load_dotenv()

embedding_model = OpenAIEmbeddings()
VECTOR_STORE_PATH = "app/data/vector_store"
os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)

# This is a lazy global reference to hold the store after first use
vector_store = None


def add_to_faiss(chunks: List[str]):
    global vector_store
    documents = [Document(page_content=chunk) for chunk in chunks]

    if os.path.exists(VECTOR_STORE_PATH):
        vector_store = FAISS.load_local(
            folder_path=VECTOR_STORE_PATH,
            embeddings=embedding_model,
            allow_dangerous_deserialization=True)
        vector_store.add_documents(documents)
    else:
        vector_store = FAISS.from_documents(documents, embedding_model)

    vector_store.save_local(VECTOR_STORE_PATH)


def search_faiss(query: str, k: int = 3) -> List[str]:
    if not os.path.exists(VECTOR_STORE_PATH):
        return []

    vs = FAISS.load_local(
    folder_path=VECTOR_STORE_PATH,
    embeddings=embedding_model,
    allow_dangerous_deserialization=True
)
    results = vs.similarity_search(query, k=k)
    return [doc.page_content for doc in results]
