from fastapi import FastAPI
from app.controllers import auth, pins, feed, search
from app.core.database import engine
from app.models.models import Base
from app.core.cloudinary_config import init_cloudinary

# Create DB tables
Base.metadata.create_all(bind=engine)

# Init Cloudinary
init_cloudinary()

app = FastAPI(title="Pinterest Backend", description="Backend using FastAPI, Cloudinary, Elasticsearch, Redis, and PyTorch")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(pins.router, prefix="/api/pins", tags=["pins"])
app.include_router(feed.router, prefix="/api/feed", tags=["feed"])
app.include_router(search.router, prefix="/api/search", tags=["search"])

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Pinterest API is running"}
