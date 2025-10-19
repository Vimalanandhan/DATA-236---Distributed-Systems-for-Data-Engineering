from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from database import get_db
import httpx

router = APIRouter(prefix="/ai", tags=["ai"])

async def call_ollama(message: str, model: str = "llama3.1") -> str:
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        try:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model, 
                    "prompt": message, 
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Ollama service unavailable: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Ollama API error: {str(e)}")

@router.post("/chat", response_model=schemas.ChatOut)
async def chat(input: schemas.ChatIn, db: Session = Depends(get_db)):
    
    if input.conversation_id:
        conv = db.query(models.Conversation).filter_by(id=input.conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = models.Conversation(
            user_id=input.user_id, 
            title=input.title or input.message[:40] + "..." if len(input.message) > 40 else input.message
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    
    user_msg = models.Message(
        conversation_id=conv.id,
        role=models.RoleEnum.user,
        content=input.message
    )
    db.add(user_msg)
    db.commit()
    
    try:
        reply = await call_ollama(input.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Ollama: {str(e)}")
    
    assistant_msg = models.Message(
        conversation_id=conv.id,
        role=models.RoleEnum.assistant,
        content=reply
    )
    db.add(assistant_msg)
    db.commit()
    
    return schemas.ChatOut(conversation_id=conv.id, reply=reply)

@router.get("/conversations", response_model=List[schemas.ConversationOut])
def get_conversations(user_id: str, db: Session = Depends(get_db)):
    conversations = db.query(models.Conversation).filter_by(user_id=user_id).order_by(models.Conversation.updated_at.desc()).all()
    return conversations

@router.get("/messages/{conversation_id}", response_model=schemas.MessagesOut)
def get_messages(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.query(models.Conversation).filter_by(id=conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = db.query(models.Message).filter_by(conversation_id=conversation_id).order_by(models.Message.created_at.asc()).all()
    
    return schemas.MessagesOut(
        conversation_id=conversation_id,
        messages=[
            schemas.ChatMessageOut(
                id=m.id,
                role=m.role.value,
                content=m.content,
                created_at=m.created_at
            ) for m in messages
        ]
    )
