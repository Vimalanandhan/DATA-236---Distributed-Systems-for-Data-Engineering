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

async def get_ollama_response(prompt: str, model: str = CHAT_MODEL) -> str:
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
        return np.random.rand(384).tolist()

def cosine_similarity_score(embedding1: List[float], embedding2: List[float]) -> float:
    try:
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)
        return cosine_similarity(vec1, vec2)[0][0]
    except:
        return 0.0

async def save_message(user_id: str, session_id: str, role: str, content: str):
    await messages_collection.insert_one({
        "user_id": user_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow()
    })

async def get_short_term_messages(user_id: str, session_id: str, limit: int = SHORT_TERM_N) -> List[Dict]:
    cursor = messages_collection.find(
        {"user_id": user_id, "session_id": session_id}
    ).sort("created_at", -1).limit(limit)
    messages = await cursor.to_list(length=limit)
    return list(reversed(messages))  

async def get_long_term_summaries(user_id: str, session_id: str) -> Dict[str, Optional[str]]:
    session_summary = await summaries_collection.find_one(
        {"user_id": user_id, "session_id": session_id, "scope": "session"},
        sort=[("created_at", -1)]
    )
    
    lifetime_summary = await summaries_collection.find_one(
        {"user_id": user_id, "scope": "user"},
        sort=[("created_at", -1)]
    )
    
    return {
        "session": session_summary["text"] if session_summary else None,
        "lifetime": lifetime_summary["text"] if lifetime_summary else None
    }

async def should_summarize(user_id: str, session_id: str) -> bool:
    user_message_count = await messages_collection.count_documents({
        "user_id": user_id,
        "session_id": session_id,
        "role": "user"
    })
    return user_message_count % SUMMARIZE_EVERY_USER_MSGS == 0

async def generate_session_summary(user_id: str, session_id: str) -> str:
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


async def extract_episodes(user_id: str, session_id: str, message: str) -> List[Dict]:
    facts = []
    sentences = message.split('.')
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10 and len(sentence) < 200: 
            importance = 0.5  
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
    message_embedding = await get_embedding(message)
    
    cursor = episodes_collection.find({"user_id": user_id})
    episodes = await cursor.to_list(length=None)
    
    for episode in episodes:
        episode['similarity'] = cosine_similarity_score(message_embedding, episode['embedding'])
    
    episodes.sort(key=lambda x: x['similarity'], reverse=True)
    return episodes[:top_k]

def build_prompt(system_primer: str, long_term_summaries: Dict, short_term_messages: List[Dict], 
                current_message: str, episodic_facts: List[Dict]) -> str:
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
