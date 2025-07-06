from fastapi import APIRouter, Query
from typing import Optional
from app.services.faiss_store import search_faiss
from app.services.memory import get_memory, update_memory, get_history, delete_session_history
from app.services.openai_llm import get_openai_completion
import logging

router = APIRouter()

@router.post("/chat")
async def chat(
    user_input: str = Query(...),
    session_id: str = Query(...),
    user_id: str = Query(...),
):
    history = get_memory(user_id, session_id)
    context = search_faiss(user_input)

    # Create prompt from context + history + user input
    prompt = "\n".join(history + context + [f"User: {user_input}", "Bot:"])

    # 🔥 Real OpenAI call
    answer = get_openai_completion(prompt)

    update_memory(user_id, session_id, user_input, answer)
    return {"answer": answer}


@router.get("/history")
async def chat_history(
    user_id: str = Query(...),
    session_id: Optional[str] = Query(None),
):
    print(f"🔍 Fetching history for user_id: {user_id}, session_id: {session_id}")
    history = get_history(user_id, session_id)
    print(f"📋 Found history: {history}")
    return {"history": history}


@router.delete("/history")
async def delete_history(
    user_id: str = Query(...),
    session_id: str = Query(...),
):
    print(f"🗑️ Deleting history for user_id: {user_id}, session_id: {session_id}")
    success = delete_session_history(user_id, session_id)
    if success:
        return {"message": "Session history deleted successfully"}
    else:
        return {"error": "Failed to delete session history"}, 400
