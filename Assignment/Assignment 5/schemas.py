from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional, List

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    quantity: int = 0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

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

class MessagesOut(BaseModel):
    conversation_id: int
    messages: List[ChatMessageOut]

class ConversationOut(BaseModel):
    id: int
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AuthorBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

class AuthorCreate(AuthorBase):
    pass

class AuthorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None

class Author(AuthorBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BookBase(BaseModel):
    title: str
    isbn: str
    publication_year: int
    available_copies: int = 1
    author_id: int

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    available_copies: Optional[int] = None
    author_id: Optional[int] = None

class Book(BookBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    author: Optional[Author] = None
    
    class Config:
        from_attributes = True

class BookWithAuthor(Book):
    author: Author
    
    class Config:
        from_attributes = True

class PaginatedAuthors(BaseModel):
    authors: List[Author]
    total: int
    page: int
    per_page: int
    total_pages: int

class PaginatedBooks(BaseModel):
    books: List[BookWithAuthor]
    total: int
    page: int
    per_page: int
    total_pages: int