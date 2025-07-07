from typing import List, Dict, Tuple, Optional, Union
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import time
from app.services.openai_llm import summarize_text

load_dotenv()

TTL_SECONDS = 15 * 60  # 15 minutes
MAX_HISTORY_MESSAGES = 20
KEEP_LAST_MESSAGES = 6

# Fix: Use MONGO_URI to match .env file
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    print("⚠️ MONGO_URI environment variable not found!")
    mongo_uri = "mongodb://localhost:27017"  # fallback

print(f"🔗 Connecting to MongoDB: {mongo_uri[:50]}...")

try:
    client = MongoClient(mongo_uri)
    # Test the connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    # Create a dummy client for development
    client = None

if client is not None:
    db = client[os.getenv("MONGO_DB", "rag_service")]
else:
    db = None
if db is not None:
    collection = db["chat_history"]
else:
    collection = None

# In-memory history cache keyed by (session_id, user_id)
session_memory: Dict[Tuple[str, str], List[dict]] = {}
# Store running summaries for each session
session_summaries: Dict[Tuple[str, str], str] = {}
# Track last activity for each session to support cleanup
session_last_access: Dict[Tuple[str, str], float] = {}

print('session_memory', session_memory)
def _cleanup_expired_sessions() -> None:
    """Remove cached sessions that haven't been used recently."""
    now = time.time()
    expired = [
        key for key, ts in session_last_access.items() if now - ts > TTL_SECONDS
    ]
    for key in expired:
        session_last_access.pop(key, None)
        session_memory.pop(key, None)
        session_summaries.pop(key, None)


def _fetch_history_from_db(user_id: str, session_id: Optional[str] = None) -> Union[List[dict], Dict[str, List[dict]]]:
    """Fetch chat history from MongoDB."""
    print(f"🗄️ Fetching from DB - user_id: {user_id}, session_id: {session_id}")
    
    if collection is None:
        print("⚠️ MongoDB collection not available, returning empty result")
        return [] if session_id else {}
    
    try:
        if session_id:
            doc = collection.find_one({"user_id": user_id, "session_id": session_id})
            print(f"📄 Found document: {doc}")
            if not doc:
                return []
            session_summaries[(session_id, user_id)] = doc.get("summary", "")
            history = doc.get("history", [])
            if doc.get("summary"):
                history = history[-KEEP_LAST_MESSAGES:]
            return history

        docs = collection.find({"user_id": user_id})
        docs_list = list(docs)
        print(f"📚 Found {len(docs_list)} documents for user: {docs_list}")
        result = {}
        for d in docs_list:
            session_summaries[(d["session_id"], user_id)] = d.get("summary", "")
            hist = d.get("history", [])
            if d.get("summary"):
                hist = hist[-KEEP_LAST_MESSAGES:]
            result[d["session_id"]] = hist
        return result
    except Exception as e:
        print(f"❌ Error fetching from MongoDB: {e}")
        return [] if session_id else {}


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
    summary = session_summaries.get((session_id, user_id))
    if summary:
        formatted.append(f"Summary: {summary}")
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

    # Summarize if history grows too long
    if len(session) > MAX_HISTORY_MESSAGES:
        to_summarize = session[:-KEEP_LAST_MESSAGES]
        formatted = "\n".join(
            f"{e['role'].capitalize()}: {e['message']}" for e in to_summarize
        )
        summary = summarize_text(formatted)
        existing = session_summaries.get(key)
        if existing:
            summary = existing + "\n" + summary
        session_summaries[key] = summary
        session[:] = session[-KEEP_LAST_MESSAGES:]

    # Persist to MongoDB
    if collection is not None:
        try:
            update = {"$push": {"history": {"$each": entries}}}
            summary = session_summaries.get(key)
            if summary is not None:
                update["$set"] = {"summary": summary}
            collection.update_one(
                {"user_id": user_id, "session_id": session_id},
                update,
                upsert=True,
            )
            print(f"💾 Saved to MongoDB: user_id={user_id}, session_id={session_id}")
        except Exception as e:
            print(f"❌ Error saving to MongoDB: {e}")
    else:
        print("⚠️ MongoDB not available, only using in-memory cache")


def delete_session_history(user_id: str, session_id: str) -> bool:
    """Delete a specific session's history from both MongoDB and in-memory cache."""
    print(f"🗑️ Deleting session history: user_id={user_id}, session_id={session_id}")
    
    # Remove from in-memory cache
    key = (session_id, user_id)
    session_memory.pop(key, None)
    session_last_access.pop(key, None)
    session_summaries.pop(key, None)
    
    # Remove from MongoDB
    if collection is not None:
        try:
            result = collection.delete_one({"user_id": user_id, "session_id": session_id})
            print(f"🗑️ Deleted from MongoDB: {result.deleted_count} document(s)")
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Error deleting from MongoDB: {e}")
            return False
    else:
        print("⚠️ MongoDB not available, only deleted from in-memory cache")
        return True

