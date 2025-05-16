from fastapi import APIRouter, Query
from app.services.agent_service import agent


router = APIRouter()

@router.post("/agent_chat")
async def agent_chat(user_input: str = Query(...)):
    response = agent.run(user_input)
    return {"answer": response}