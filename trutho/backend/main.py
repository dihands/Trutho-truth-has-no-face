import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

load_dotenv()

from database import engine, Base
import models  # ensure tables are registered

# Create all tables
Base.metadata.create_all(bind=engine)

from routes import auth_routes, post_routes, comment_routes, websocket_routes, admin_routes

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title="Trutho API",
    description="Anonymous social reporting platform — Truth Has No Face.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow all for dev; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Serve frontend HTML
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# Register routers
app.include_router(auth_routes.router)
app.include_router(post_routes.router)
app.include_router(comment_routes.router)
app.include_router(websocket_routes.router)
app.include_router(admin_routes.router)


@app.get("/")
def root():
    return {
        "platform": "Trutho",
        "slogan": "Truth Has No Face.",
        "status": "online",
        "docs": "/docs",
        "frontend": "/app"
    }


@app.get("/health")
def health():
    return {"status": "ok"}
