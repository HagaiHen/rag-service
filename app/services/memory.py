from typing import List

session_memory = {}

def get_memory(session_id: str) -> List[str]:
    return session_memory.get(session_id, [])

def update_memory(session_id: str, user_input: str, answer: str):
    session = session_memory.setdefault(session_id, [])
    session.append(f"User: {user_input}")
    session.append(f"Bot: {answer}")