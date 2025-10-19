from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import models
import schemas
from database import get_db
import httpx

router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/test")
def test_endpoint():
    try:
        from database import get_db
        from sqlalchemy.orm import Session
        db = next(get_db())
        
        conversations = db.query(models.Conversation).all()
        
        return {
            "status": "success",
            "message": "Database connection working",
            "conversations_count": len(conversations)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }

async def call_ollama(message: str, model: str = "llama3.1:latest") -> str:
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
    try:
        if input.conversation_id:
            conv = db.query(models.Conversation).filter_by(id=input.conversation_id).first()
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            now = datetime.now()
            conv = models.Conversation(
                user_id=input.user_id, 
                title=input.title or input.message[:40] + "..." if len(input.message) > 40 else input.message,
                created_at=now,
                updated_at=now
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
        
        now = datetime.now()
        user_msg = models.Message(
            conversation_id=conv.id,
            role=models.RoleEnum.user,
            content=input.message,
            created_at=now
        )
        db.add(user_msg)
        db.commit()
        
        try:
            reply = await call_ollama(input.message)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling Ollama: {str(e)}")
        
        now = datetime.now()
        assistant_msg = models.Message(
            conversation_id=conv.id,
            role=models.RoleEnum.assistant,
            content=reply,
            created_at=now
        )
        db.add(assistant_msg)
        db.commit()
        
        return schemas.ChatOut(conversation_id=conv.id, reply=reply)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/conversations", response_model=List[schemas.ConversationOut])
def get_conversations(user_id: str, db: Session = Depends(get_db)):
    conversations = db.query(models.Conversation).filter_by(user_id=user_id).all()
    
    valid_conversations = []
    for conv in conversations:
        try:
            if conv.created_at is None or conv.updated_at is None:
                continue
            if str(conv.created_at) == 'None' or str(conv.updated_at) == 'None':
                continue
            if str(conv.created_at) == '' or str(conv.updated_at) == '':
                continue
            if not isinstance(conv.created_at, datetime) or not isinstance(conv.updated_at, datetime):
                continue
            valid_conversations.append(conv)
        except Exception as e:
            continue
    
    valid_conversations.sort(key=lambda x: x.updated_at, reverse=True)
    
    return valid_conversations

@router.get("/messages/{conversation_id}", response_model=schemas.MessagesOut)
def get_messages(conversation_id: int, db: Session = Depends(get_db)):
    """Get all messages in a conversation"""
    conv = db.query(models.Conversation).filter_by(id=conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = db.query(models.Message).filter_by(conversation_id=conversation_id).order_by(models.Message.created_at.asc()).all()
    
    valid_messages = []
    for m in messages:
        try:
            if m.created_at is None:
                continue
            if str(m.created_at) == 'None':
                continue
            if str(m.created_at) == '':
                continue
            valid_messages.append(m)
        except Exception as e:
            continue
    
    return schemas.MessagesOut(
        conversation_id=conversation_id,
        messages=[
            schemas.ChatMessageOut(
                id=m.id,
                role=m.role.value,
                content=m.content,
                created_at=m.created_at
            ) for m in valid_messages
        ]
    )
