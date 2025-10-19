from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
import router

app = FastAPI(
    title="LLM Chat API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router.router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    print("LLM Chat API is ready!")

@app.get("/")
def read_root():
    return {"message": "LLM Chat API is running!", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "LLM Chat API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
