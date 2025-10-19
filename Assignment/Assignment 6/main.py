"""
Complete AI Memory System Application
Assignment 6 - Part 2

This is the complete application that combines all components:
- API endpoints
- Memory logic functions
- MongoDB models
- Ollama integration
"""

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SHORT_TERM_N = 16  # Number of recent messages to keep in short-term memory
SUMMARIZE_EVERY_USER_MSGS = 5  # Generate summary every N user messages
CHAT_MODEL = "phi3:mini"  # Ollama model to use
EMBED_MODEL = "nomic-embed-text"  # Embedding model
TOP_K_EPISODES = 5  # Number of most relevant episodes to retrieve

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/taskmanager")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client.taskmanager

# Collections
messages_collection = db.messages
summaries_collection = db.summaries
episodes_collection = db.episodes

app = FastAPI(title="AI Memory System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
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

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def get_ollama_response(prompt: str, model: str = CHAT_MODEL) -> str:
    """Get response from Ollama API"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return "I'm sorry, I'm having trouble processing your request right now."

async def get_embedding(text: str, model: str = EMBED_MODEL) -> List[float]:
    """Get embedding from Ollama"""
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": model,
                "prompt": text
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        logger.error(f"Embedding API error: {e}")
        # Return a random embedding as fallback
        return np.random.rand(384).tolist()

def cosine_similarity_score(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings"""
    try:
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)
        return cosine_similarity(vec1, vec2)[0][0]
    except:
        return 0.0

# =============================================================================
# MEMORY LOGIC FUNCTIONS
# =============================================================================

async def save_message(user_id: str, session_id: str, role: str, content: str):
    """Save a message to the database"""
    await messages_collection.insert_one({
        "user_id": user_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow()
    })

async def get_short_term_messages(user_id: str, session_id: str, limit: int = SHORT_TERM_N) -> List[Dict]:
    """Get recent messages for short-term memory"""
    cursor = messages_collection.find(
        {"user_id": user_id, "session_id": session_id}
    ).sort("created_at", -1).limit(limit)
    messages = await cursor.to_list(length=limit)
    return list(reversed(messages))  # Return in chronological order

async def get_long_term_summaries(user_id: str, session_id: str) -> Dict[str, Optional[str]]:
    """Get latest session and lifetime summaries"""
    # Get latest session summary
    session_summary = await summaries_collection.find_one(
        {"user_id": user_id, "session_id": session_id, "scope": "session"},
        sort=[("created_at", -1)]
    )
    
    # Get latest lifetime summary
    lifetime_summary = await summaries_collection.find_one(
        {"user_id": user_id, "scope": "user"},
        sort=[("created_at", -1)]
    )
    
    return {
        "session": session_summary["text"] if session_summary else None,
        "lifetime": lifetime_summary["text"] if lifetime_summary else None
    }

async def extract_episodes(user_id: str, session_id: str, message: str) -> List[Dict]:
    """Extract and store episodes from user message"""
    facts = []
    sentences = message.split('.')
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10 and len(sentence) < 200:
            # Simple importance scoring based on keywords
            importance = 0.5  # Base importance
            if any(word in sentence.lower() for word in ['important', 'remember', 'always', 'never', 'love', 'hate']):
                importance = 0.8
            elif any(word in sentence.lower() for word in ['like', 'prefer', 'want', 'need']):
                importance = 0.6
            
            if importance > 0.4:
                embedding = await get_embedding(sentence)
                episode = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "fact": sentence,
                    "importance": importance,
                    "embedding": embedding,
                    "created_at": datetime.utcnow()
                }
                await episodes_collection.insert_one(episode)
                facts.append(episode)
    
    return facts

async def get_relevant_episodes(user_id: str, message: str, top_k: int = TOP_K_EPISODES) -> List[Dict]:
    """Retrieve most relevant episodes based on message similarity"""
    message_embedding = await get_embedding(message)
    
    # Get all episodes for the user
    cursor = episodes_collection.find({"user_id": user_id})
    episodes = await cursor.to_list(length=None)
    
    # Calculate similarities and sort
    for episode in episodes:
        episode['similarity'] = cosine_similarity_score(message_embedding, episode['embedding'])
    
    # Sort by similarity and return top-k
    episodes.sort(key=lambda x: x['similarity'], reverse=True)
    return episodes[:top_k]

async def should_summarize(user_id: str, session_id: str) -> bool:
    """Check if it's time to generate a summary"""
    user_message_count = await messages_collection.count_documents({
        "user_id": user_id,
        "session_id": session_id,
        "role": "user"
    })
    return user_message_count % SUMMARIZE_EVERY_USER_MSGS == 0

async def generate_session_summary(user_id: str, session_id: str) -> str:
    """Generate a session summary"""
    cursor = messages_collection.find(
        {"user_id": user_id, "session_id": session_id}
    ).sort("created_at", -1).limit(20)
    recent_messages = await cursor.to_list(length=20)
    
    if not recent_messages:
        return ""
    
    conversation = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in reversed(recent_messages)
    ])
    
    prompt = f"""Summarize the following conversation into key points:

{conversation}

Provide a concise summary with 3-5 bullet points:"""
    
    summary = await get_ollama_response(prompt)
    
    await summaries_collection.insert_one({
        "user_id": user_id,
        "session_id": session_id,
        "scope": "session",
        "text": summary,
        "created_at": datetime.utcnow()
    })
    
    return summary

async def update_lifetime_summary(user_id: str) -> str:
    """Update the lifetime user summary"""
    cursor = summaries_collection.find(
        {"user_id": user_id, "scope": "session"}
    ).sort("created_at", -1).limit(5)
    session_summaries = await cursor.to_list(length=5)
    
    if not session_summaries:
        return ""
    
    combined_summaries = "\n\n".join([s["text"] for s in session_summaries])
    
    prompt = f"""Create a lifetime user profile summary from these session summaries:

{combined_summaries}

Provide a concise user profile with key characteristics and preferences:"""
    
    lifetime_summary = await get_ollama_response(prompt)
    
    await summaries_collection.insert_one({
        "user_id": user_id,
        "session_id": None,
        "scope": "user",
        "text": lifetime_summary,
        "created_at": datetime.utcnow()
    })
    
    return lifetime_summary

def build_prompt(system_primer: str, long_term_summaries: Dict, short_term_messages: List[Dict], 
                current_message: str, episodic_facts: List[Dict]) -> str:
    """Build the complete prompt for the LLM"""
    prompt_parts = [system_primer]
    
    if long_term_summaries["lifetime"]:
        prompt_parts.append(f"User Profile: {long_term_summaries['lifetime']}")
    
    if long_term_summaries["session"]:
        prompt_parts.append(f"Session Context: {long_term_summaries['session']}")
    
    if short_term_messages:
        conversation = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in short_term_messages
        ])
        prompt_parts.append(f"Recent conversation:\n{conversation}")
    
    prompt_parts.append(f"User: {current_message}")
    
    if episodic_facts:
        facts_text = "\n".join([f"- {fact['fact']}" for fact in episodic_facts])
        prompt_parts.append(f"Relevant facts:\n{facts_text}")
    
    return "\n\n".join(prompt_parts)

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with memory management"""
    try:
        # Save user message
        await save_message(request.user_id, request.session_id, "user", request.message)
        
        # Get short-term memory
        short_term_messages = await get_short_term_messages(request.user_id, request.session_id)
        
        # Get long-term summaries
        long_term_summaries = await get_long_term_summaries(request.user_id, request.session_id)
        
        # Extract episodes from current message
        episodes = await extract_episodes(request.user_id, request.session_id, request.message)
        
        # Get relevant episodes
        relevant_episodes = await get_relevant_episodes(request.user_id, request.message)
        
        # Build prompt
        system_primer = "You are a helpful AI assistant with memory. Use the provided context and facts to give personalized responses."
        prompt = build_prompt(
            system_primer, 
            long_term_summaries, 
            short_term_messages, 
            request.message, 
            relevant_episodes
        )
        
        # Get LLM response
        reply = await get_ollama_response(prompt)
        
        # Save assistant response
        await save_message(request.user_id, request.session_id, "assistant", reply)
        
        # Check if we should summarize
        if await should_summarize(request.user_id, request.session_id):
            await generate_session_summary(request.user_id, request.session_id)
            if len(short_term_messages) % 5 == 0:
                await update_lifetime_summary(request.user_id)
        
        # Prepare response
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
    """Get memory information for a user"""
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
    """Get aggregated data for a user"""
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
