from typing import List, Dict, Tuple, Optional, Union
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import time

load_dotenv()

TTL_SECONDS = 15 * 60  # 15 minutes

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB", "rag_service")]
collection = db["chat_history"]

# In-memory history cache keyed by (session_id, user_id)
session_memory: Dict[Tuple[str, str], List[dict]] = {}
# Track last activity for each session to support cleanup
session_last_access: Dict[Tuple[str, str], float] = {}


def _cleanup_expired_sessions() -> None:
    """Remove cached sessions that haven't been used recently."""
    now = time.time()
    expired = [
        key for key, ts in session_last_access.items() if now - ts > TTL_SECONDS
    ]
    for key in expired:
        session_last_access.pop(key, None)
        session_memory.pop(key, None)


def _fetch_history_from_db(user_id: str, session_id: Optional[str] = None) -> Union[List[dict], Dict[str, List[dict]]]:
    """Fetch chat history from MongoDB."""
    if session_id:
        doc = collection.find_one({"user_id": user_id, "session_id": session_id})
        if not doc:
            return []
        return doc.get("history", [])

    docs = collection.find({"user_id": user_id})
    return {d["session_id"]: d.get("history", []) for d in docs}


def get_history(user_id: str, session_id: Optional[str] = None) -> Union[List[dict], Dict[str, List[dict]]]:
    """Return chat history.

    If ``session_id`` is provided, history for that session is returned.
    Otherwise all sessions for the user are retrieved.
    """
    _cleanup_expired_sessions()
    if session_id:
        key = (session_id, user_id)
        history = session_memory.get(key)
        if history is None:
            history = _fetch_history_from_db(user_id, session_id)
            if history:
                session_memory[key] = history
        if history is not None:
            session_last_access[key] = time.time()
        return history

    # Collect all cached sessions for the user
    user_sessions: Dict[str, List[dict]] = {
        sid: hist for (sid, uid), hist in session_memory.items() if uid == user_id
    }

    db_history = _fetch_history_from_db(user_id)
    for sid, hist in db_history.items():
        if sid not in user_sessions:
            user_sessions[sid] = hist
            session_memory[(sid, user_id)] = hist

    for sid in user_sessions:
        session_last_access[(sid, user_id)] = time.time()

    return user_sessions


def get_memory(user_id: str, session_id: str) -> List[str]:
    history = get_history(user_id, session_id)
    formatted = []
    for item in history:
        role = item.get("role", "bot").capitalize()
        message = item.get("message", "")
        formatted.append(f"{role}: {message}")
    return formatted


def update_memory(user_id: str, session_id: str, user_input: str, answer: str):
    key = (session_id, user_id)
    entries = [
        {"role": "user", "message": user_input},
        {"role": "bot", "message": answer},
    ]

    _cleanup_expired_sessions()

    # Update in-memory cache
    session = session_memory.setdefault(key, [])
    session.extend(entries)
    session_last_access[key] = time.time()

    # Persist to MongoDB
    collection.update_one(
        {"user_id": user_id, "session_id": session_id},
        {"$push": {"history": {"$each": entries}}},
        upsert=True,
    )

