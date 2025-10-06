from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List

class ChatIn(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[int] = None
    title: Optional[str] = None

class ChatOut(BaseModel):
    conversation_id: int
    reply: str

class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    
    @field_validator('created_at', mode='before')
    @classmethod
    def validate_datetime(cls, v):
        if v is None or v == '' or v == 'None':
            return datetime.now()
        return v

class MessagesOut(BaseModel):
    conversation_id: int
    messages: List[ChatMessageOut]

class ConversationOut(BaseModel):
    id: int
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def validate_datetime(cls, v):
        if v is None or v == '' or v == 'None':
            return datetime.now()
        return v
    
    class Config:
        from_attributes = True
