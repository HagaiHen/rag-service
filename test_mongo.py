#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def test_mongodb_connection():
    mongo_uri = os.getenv("MONGO_URI")
    print(f"🔗 Testing MongoDB connection...")
    print(f"📝 URI: {mongo_uri}")
    
    if not mongo_uri:
        print("❌ MONGO_URI not found in environment")
        return False
    
    try:
        # Remove any trailing % if present
        if mongo_uri.endswith('%'):
            mongo_uri = mongo_uri[:-1]
            print(f"🔧 Fixed URI: {mongo_uri}")
        
        client = MongoClient(mongo_uri)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Test database access
        db_name = os.getenv("MONGO_DB", "rag_service")
        db = client[db_name]
        collection = db["chat_history"]
        
        # Try a simple query
        count = collection.count_documents({})
        print(f"📊 Collection has {count} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

if __name__ == "__main__":
    test_mongodb_connection() 