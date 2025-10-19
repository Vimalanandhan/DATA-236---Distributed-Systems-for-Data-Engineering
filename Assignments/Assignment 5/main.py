from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
import router
import library_router

app = FastAPI(
    title="Library Management System API",
    description="FastAPI backend for Library Management System with LLM Chat integration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router.router)  
app.include_router(library_router.router)  

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

@app.get("/")
def read_root():
    return {
        "message": "Library Management System API is running!", 
        "docs": "/docs",
        "endpoints": {
            "library": "/library",
            "ai_chat": "/ai"
        }
    }
