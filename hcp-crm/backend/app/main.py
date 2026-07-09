from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import chat, interactions, hcp

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-First CRM - HCP Module", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(interactions.router)
app.include_router(hcp.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
