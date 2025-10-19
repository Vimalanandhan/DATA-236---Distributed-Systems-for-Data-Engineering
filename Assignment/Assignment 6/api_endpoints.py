from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import os
from datetime import datetime, timedelta
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
import motor.motor_asyncio
from bson import ObjectId
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SHORT_TERM_N = 16  
SUMMARIZE_EVERY_USER_MSGS = 5  
CHAT_MODEL = "phi3:mini"  
EMBED_MODEL = "nomic-embed-text"  
TOP_K_EPISODES = 5 

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/taskmanager")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client.taskmanager

messages_collection = db.messages
summaries_collection = db.summaries
episodes_collection = db.episodes

app = FastAPI(title="AI Memory System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = "default"
    message: str

class ChatResponse(BaseModel):
    reply: str
    memory_used: Dict[str, Any]

class MemoryResponse(BaseModel):
    short_term_messages: List[Dict[str, Any]]
    session_summary: Optional[str]
    lifetime_summary: Optional[str]
    recent_episodes: List[Dict[str, Any]]

class AggregateResponse(BaseModel):
    daily_message_counts: List[Dict[str, Any]]
    recent_summaries: List[Dict[str, Any]]
    recent_episodes: List[Dict[str, Any]]

from memory_logic import (
    save_message, get_short_term_messages, get_long_term_summaries,
    extract_episodes, get_relevant_episodes, should_summarize,
    generate_session_summary, update_lifetime_summary, build_prompt,
    get_ollama_response
)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        await save_message(request.user_id, request.session_id, "user", request.message)
        
        short_term_messages = await get_short_term_messages(request.user_id, request.session_id)
        
        long_term_summaries = await get_long_term_summaries(request.user_id, request.session_id)
        
        episodes = await extract_episodes(request.user_id, request.session_id, request.message)
        
        relevant_episodes = await get_relevant_episodes(request.user_id, request.message)
        
        system_primer = "You are a helpful AI assistant with memory. Use the provided context and facts to give personalized responses."
        prompt = build_prompt(
            system_primer, 
            long_term_summaries, 
            short_term_messages, 
            request.message, 
            relevant_episodes
        )
        
        reply = await get_ollama_response(prompt)
        
        await save_message(request.user_id, request.session_id, "assistant", reply)
        
        if await should_summarize(request.user_id, request.session_id):
            await generate_session_summary(request.user_id, request.session_id)
            if len(short_term_messages) % 5 == 0:
                await update_lifetime_summary(request.user_id)
        
        memory_used = {
            "short_term_count": len(short_term_messages),
            "long_term_summary": long_term_summaries["lifetime"],
            "session_summary": long_term_summaries["session"],
            "episodic_facts": [{"fact": ep["fact"], "importance": ep["importance"]} for ep in relevant_episodes]
        }
        
        return ChatResponse(reply=reply, memory_used=memory_used)
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/{user_id}", response_model=MemoryResponse)
async def get_memory(user_id: str):
    try:
        recent_session = await messages_collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )
        session_id = recent_session["session_id"] if recent_session else "default"
        
        short_term_messages = await get_short_term_messages(user_id, session_id)
        
        summaries = await get_long_term_summaries(user_id, session_id)
        
        episodes_cursor = episodes_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(20)
        recent_episodes = await episodes_cursor.to_list(length=20)
        
        return MemoryResponse(
            short_term_messages=[
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    "created_at": msg["created_at"].isoformat()
                }
                for msg in short_term_messages
            ],
            session_summary=summaries["session"],
            lifetime_summary=summaries["lifetime"],
            recent_episodes=[
                {
                    "fact": ep["fact"],
                    "importance": ep["importance"],
                    "created_at": ep["created_at"].isoformat()
                }
                for ep in recent_episodes
            ]
        )
        
    except Exception as e:
        logger.error(f"Memory retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/aggregate/{user_id}", response_model=AggregateResponse)
async def get_aggregate(user_id: str):
    try:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 30}
        ]
        daily_counts = await messages_collection.aggregate(pipeline).to_list(length=30)
        
        summaries_cursor = summaries_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(10)
        recent_summaries = await summaries_cursor.to_list(length=10)
        
        episodes_cursor = episodes_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(20)
        recent_episodes = await episodes_cursor.to_list(length=20)
        
        return AggregateResponse(
            daily_message_counts=[
                {"date": item["_id"], "count": item["count"]}
                for item in daily_counts
            ],
            recent_summaries=[
                {
                    "scope": s["scope"],
                    "text": s["text"][:100] + "..." if len(s["text"]) > 100 else s["text"],
                    "created_at": s["created_at"].isoformat()
                }
                for s in recent_summaries
            ],
            recent_episodes=[
                {
                    "fact": e["fact"],
                    "importance": e["importance"],
                    "created_at": e["created_at"].isoformat()
                }
                for e in recent_episodes
            ]
        )
        
    except Exception as e:
        logger.error(f"Aggregate retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
