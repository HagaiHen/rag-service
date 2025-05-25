from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import os

from app.routers import upload, chat, agent_chat

app = FastAPI()
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(agent_chat.router)

@app.get("/")
def root():
    return {"message": "Welcome to the RAG Service API"}
