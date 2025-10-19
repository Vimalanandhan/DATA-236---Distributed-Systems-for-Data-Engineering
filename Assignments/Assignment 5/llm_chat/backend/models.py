from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Text, DateTime, func
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()

class RoleEnum(enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), nullable=False)
    title = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    conversation = relationship("Conversation", back_populates="messages")
