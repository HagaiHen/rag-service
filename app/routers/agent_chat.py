from fastapi import APIRouter, Query
from app.services.agent_service import get_or_create_agent

router = APIRouter()

@router.post("/agent_chat")
async def agent_chat(user_input: str = Query(...), session_id: str = Query(...)):
    agent = get_or_create_agent(session_id)
    response = agent.run(user_input)
    return {"answer": response}