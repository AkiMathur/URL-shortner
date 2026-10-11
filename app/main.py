from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Query
from app.models import link_model, user_model, clicks_model
from app.database import engine, SessionLocal, Base
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
from app.services.shortcode import *
from datetime import datetime, timezone, date
from app.schemas.user_schema import UserCreateReq
from app.schemas.link_schema import LinkCreateReq, LinkResponse, LinkUpdateReq
from app.core.security import verify_token,verify_pass,hash_pass,create_token
from fastapi.security import OAuth2PasswordRequestForm
from redis import Redis
import json
import os
import hashlib
from contextlib import asynccontextmanager
from app.core.rate_limit import rate_limit

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis.from_url(REDIS_URL)
    yield
    app.state.redis.close()


app = FastAPI(lifespan=lifespan)


class Token(BaseModel):
    access_token: str
    token_type: str

# class GetLinksRes(BaseModel):
#     original_url: str
#     short_code: str
#     created_at: date

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_click(link_id: int, ip_hash: str | None = None, user_agent: str | None = None):
    with SessionLocal() as db:
        db.add(clicks_model.Clicks(
            link_id=link_id,
            clicked_at=datetime.now(timezone.utc),
            ip_hash=ip_hash,
            user_agent=user_agent
        ))
        db.commit()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(verify_token)]

@app.post("/newusers", dependencies=[Depends(rate_limit(limit=5, window=60, scope="signup"))])
async def create_user(user: UserCreateReq, db: db_dependency):
    db_user = db.query(user_model.Users).filter(user_model.Users.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = user_model.Users(username=user.username, hashed_password=hash_pass(user.password))
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully", "username" : user.username}

@app.post("/login", response_model=Token, dependencies=[Depends(rate_limit(limit=5, window=60, scope="login"))])
async def login(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    db_user = db.query(user_model.Users).filter(user_model.Users.username == form_data.username).first()
    if not db_user or not verify_pass(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(db_user.id, db_user.username)
    return {"access_token": token, "token_type": "bearer"}

#Future feature: temp db for storing links with expiry date, and a background task to delete expired links. For now, we will just store the links in the database without any expiry date for shorturl without login.

@app.post("/create_link")
async def create_link(link_req: LinkCreateReq, db: db_dependency, token_user: user_dependency, request: Request):
    db_link = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"], link_model.Link.original_url == link_req.original_url).first()
    if db_link:
        return {"message": "Link already exists", "short_code": str(request.base_url) + db_link.short_code}
    
    if link_req.custom_alias:
        short_code = f"{token_user['token_username']}/{link_req.custom_alias}"
        if db.query(link_model.Link).filter(link_model.Link.short_code == short_code).first():
            raise HTTPException(status_code=409, detail="Custom alias already taken")
    else:
        short_code=url_to_shortcode(token_user["token_username"])

    new_shortcode = link_model.Link(
        short_code=short_code,
        original_url=link_req.original_url,
        owner_id=token_user["token_userid"],
        created_at=date.today()
    )
    db.add(new_shortcode)
    db.commit()

    short_code_link = str(request.base_url) + short_code
    return {"message": "Link created successfully", "Link": short_code_link}

@app.get("/user/all_links")
def get_all_links(token_user: user_dependency,db: db_dependency, limit: int = Query(default=20, ge=1, le=100),offset: int = Query(default=0, ge=0)) -> list[LinkResponse]:
    db_links = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"]).offset(offset).limit(limit).all()

    return [LinkResponse(
        original_url=link.original_url,
        short_code=link.short_code,
        created_at=link.created_at
    ) for link in db_links]

@app.get("/user/link/clicks/stats/count/{shorturl:path}")
async def get_clicks_count(shorturl: str, db: db_dependency, token_user: user_dependency):
    db_clicks = db.query(clicks_model.Clicks).join(link_model.Link).filter(link_model.Link.short_code == shorturl, link_model.Link.owner_id == token_user["token_userid"]).count()
    if not db_clicks:
        raise HTTPException(status_code=404, detail="No clicks found for this shorturl")
    return db_clicks

@app.get("/user/link/clicks/stats/history/{shorturl:path}")
async def get_clicks_history(shorturl: str, db: db_dependency, token_user: user_dependency):
    db_clicks = db.query(clicks_model.Clicks).join(link_model.Link).filter(link_model.Link.short_code == shorturl, link_model.Link.owner_id == token_user["token_userid"]).all()
    if not db_clicks:
        raise HTTPException(status_code=404, detail="No clicks found for this shorturl")
    return db_clicks


@app.get("/{shorturl:path}", dependencies=[Depends(rate_limit(limit=60, window=60, scope="redirect"))])
def get_link(shorturl: str, request: Request, background_tasks: BackgroundTasks, db: db_dependency):
    key = f"link:{shorturl}"

    cached = app.state.redis.get(key)
    if cached:
        data = json.loads(cached)
    else:
        db_link = db.query(link_model.Link).filter(link_model.Link.short_code == shorturl).first()
        if not db_link:
            raise HTTPException(status_code=404, detail="ShortURL not found")
        data = {"id":db_link.id, "url":db_link.original_url}

        app.state.redis.setex(key,3600,json.dumps(data))

    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
    user_agent = request.headers.get("user-agent", "unknown")

    background_tasks.add_task(log_click, data['id'], ip_hash, user_agent)
    return RedirectResponse(url=data['url'], status_code=307)

@app.put("/shorturl_update/{shorturl:path}/")
async def update_shorturl(shorturl: str, req: LinkUpdateReq, db: db_dependency, token_user: user_dependency):
    db_link = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"], link_model.Link.short_code == shorturl).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="URL not found")

    db_link.original_url = req.original_url
    db.commit()

    key = f"link:{shorturl}"
    app.state.redis.delete(key)

    return {"message": "URL updated successfully", "short_url": shorturl, "new_url": req.original_url}

@app.delete("/shorturl_delete/{shorturl:path}/")
async def delete_shorturl(shorturl: str, db: db_dependency, token_user: user_dependency):
    db_link = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"], link_model.Link.short_code == shorturl).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="URL not found")

    key = f"link:{shorturl}"
    app.state.redis.delete(key)

    db.delete(db_link)
    db.commit()
    return {"message": "Shorturl deleted successfully", "short_url": shorturl}

