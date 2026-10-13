from fastapi import FastAPI
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from redis import Redis
import os

from app.api import auth,links,redirect

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis.from_url(REDIS_URL)
    yield
    app.state.redis.close()




app = FastAPI(title="URL Shortener API", version="1.0.0", lifespan=lifespan)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(links.router)
app.include_router(redirect.router)


#Future feature: 
# 1. temp db for storing links with expiry date, and a background task to delete expired links. For now, we will just store the links in the database without any expiry date for shorturl without login.
# 2. Negative caching for unknown codes