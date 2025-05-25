from fastapi import APIRouter, Query
from app.services.faiss_store import search_faiss
from app.services.memory import get_memory, update_memory
from app.services.openai_llm import get_openai_completion

router = APIRouter()

@router.post("/chat")
async def chat(user_input: str = Query(...), session_id: str = Query(...)):
    history = get_memory(session_id)
    context = search_faiss(user_input)

    prompt = "\n".join(history + context + [f"User: {user_input}", "Bot:"])

    answer = get_openai_completion(prompt)

    update_memory(session_id, user_input, answer)
    return {"answer": answer}