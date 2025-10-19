from pymongo import MongoClient
from datetime import datetime
from typing import List, Optional, Dict, Any
import motor.motor_asyncio
import os

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/taskmanager")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client.taskmanager

# =============================================================================
# MESSAGES COLLECTION
# =============================================================================

class MessageModel:
    """
    Messages collection schema:
    - user_id: String, required, indexed
    - session_id: String, required, indexed  
    - role: String, enum ['user', 'assistant'], required
    - content: String, required
    - created_at: Date, default now, indexed
    """
    
    @staticmethod
    async def create_indexes():
        """Create indexes for efficient queries"""
        await db.messages.create_index([("user_id", 1), ("session_id", 1), ("created_at", -1)])
        await db.messages.create_index([("user_id", 1), ("created_at", -1)])
        await db.messages.create_index([("created_at", 1)])
    
    @staticmethod
    async def insert_message(user_id: str, session_id: str, role: str, content: str):
        """Insert a new message"""
        return await db.messages.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow()
        })
    
    @staticmethod
    async def get_recent_messages(user_id: str, session_id: str, limit: int = 16):
        """Get recent messages for short-term memory"""
        cursor = db.messages.find(
            {"user_id": user_id, "session_id": session_id}
        ).sort("created_at", -1).limit(limit)
        messages = await cursor.to_list(length=limit)
        return list(reversed(messages))
    
    @staticmethod
    async def get_user_message_count(user_id: str, session_id: str):
        """Get count of user messages for summarization trigger"""
        return await db.messages.count_documents({
            "user_id": user_id,
            "session_id": session_id,
            "role": "user"
        })
    
    @staticmethod
    async def get_daily_message_counts(user_id: str):
        """Get daily message counts for aggregate endpoint"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 30}
        ]
        return await db.messages.aggregate(pipeline).to_list(length=30)

# =============================================================================
# SUMMARIES COLLECTION
# =============================================================================

class SummaryModel:
    """
    Summaries collection schema:
    - user_id: String, required, indexed
    - session_id: String, default null (for lifetime summaries), indexed
    - scope: String, enum ['session', 'user'], required, indexed
    - text: String, required
    - created_at: Date, default now, indexed
    """
    
    @staticmethod
    async def create_indexes():
        """Create indexes for efficient queries"""
        await db.summaries.create_index([("user_id", 1), ("scope", 1), ("created_at", -1)])
        await db.summaries.create_index([("user_id", 1), ("session_id", 1), ("created_at", -1)])
        await db.summaries.create_index([("created_at", 1)])
    
    @staticmethod
    async def insert_summary(user_id: str, session_id: Optional[str], scope: str, text: str):
        """Insert a new summary"""
        return await db.summaries.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "scope": scope,
            "text": text,
            "created_at": datetime.utcnow()
        })
    
    @staticmethod
    async def get_latest_session_summary(user_id: str, session_id: str):
        """Get latest session summary"""
        return await db.summaries.find_one(
            {"user_id": user_id, "session_id": session_id, "scope": "session"},
            sort=[("created_at", -1)]
        )
    
    @staticmethod
    async def get_latest_lifetime_summary(user_id: str):
        """Get latest lifetime summary"""
        return await db.summaries.find_one(
            {"user_id": user_id, "scope": "user"},
            sort=[("created_at", -1)]
        )
    
    @staticmethod
    async def get_recent_summaries(user_id: str, limit: int = 10):
        """Get recent summaries for aggregate endpoint"""
        cursor = db.summaries.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

# =============================================================================
# EPISODES COLLECTION
# =============================================================================

class EpisodeModel:
    """
    Episodes collection schema:
    - user_id: String, required, indexed
    - session_id: String, required, indexed
    - fact: String, required, maxlength 500
    - importance: Number, required, min 0, max 1
    - embedding: Array of Numbers, required
    - created_at: Date, default now, indexed
    """
    
    @staticmethod
    async def create_indexes():
        """Create indexes for efficient queries"""
        await db.episodes.create_index([("user_id", 1), ("created_at", -1)])
        await db.episodes.create_index([("user_id", 1), ("session_id", 1), ("created_at", -1)])
        await db.episodes.create_index([("created_at", 1)])
    
    @staticmethod
    async def insert_episode(user_id: str, session_id: str, fact: str, importance: float, embedding: List[float]):
        """Insert a new episode"""
        return await db.episodes.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "fact": fact,
            "importance": importance,
            "embedding": embedding,
            "created_at": datetime.utcnow()
        })
    
    @staticmethod
    async def get_user_episodes(user_id: str):
        """Get all episodes for a user for similarity search"""
        cursor = db.episodes.find({"user_id": user_id})
        return await cursor.to_list(length=None)
    
    @staticmethod
    async def get_recent_episodes(user_id: str, limit: int = 20):
        """Get recent episodes for aggregate endpoint"""
        cursor = db.episodes.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

# =============================================================================
# COLLECTION INITIALIZATION
# =============================================================================

async def initialize_collections():
    """Initialize all collections with proper indexes"""
    await MessageModel.create_indexes()
    await SummaryModel.create_indexes()
    await EpisodeModel.create_indexes()
    print("✅ MongoDB collections initialized with indexes")

if __name__ == "__main__":
    import asyncio
    asyncio.run(initialize_collections())
