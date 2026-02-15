from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

# ---------------------------
# APP
# ---------------------------

app = FastAPI(
    title="Sports AI API – WSPM Odds",
    version="6.0.0",
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# ROUTES
# ---------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(router, prefix="/api/v1")

# ---------------------------
# DATABASE INIT
# ---------------------------

from app.db.session import engine, Base
from app.models import match, prediction

Base.metadata.create_all(bind=engine)
