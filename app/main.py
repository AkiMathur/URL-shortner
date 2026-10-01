from fastapi import FastAPI, Depends, HTTPException
from app.models import link_model, user_model
from app.database import engine, SessionLocal, Base
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
from app.services.shortcode import *
from datetime import datetime,timezone,date

load_dotenv()

app = FastAPI()


class CreateUserReq(BaseModel):
    username: str
    password: str

class CreateLinkReq(BaseModel):
    original_url: str
    owner_id: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/users/")
async def create_user(user: CreateUserReq, db: db_dependency):
    db_user = db.query(user_model.Users).filter(user_model.Users.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = user_model.Users(username=user.username, hashed_password=user.password)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully", "username" : user.username}


@app.post("/links")
async def create_link(link_req: CreateLinkReq, db: db_dependency):
    db_link = db.query(link_model.Link).filter(link_model.Link.owner_id == link_req.owner_id, link_model.Link.original_url == link_req.original_url).first()
    if db_link:
        return {"message": "Link already exists", "short_code": db_link.short_code}
    short_code=url_to_shortcode()
    new_shortcode = link_model.Link(
        short_code=short_code,
        original_url=link_req.original_url,
        owner_id=link_req.owner_id,
        created_at=date.today()
    )
    db.add(new_shortcode)
    db.commit()
    return {"message": "Link created successfully", "short_code": short_code}


@app.get("/{shortcode}/")
async def get_link(shortcode: str, db: db_dependency):
    db_link = db.query(link_model.Link).filter(link_model.Link.short_code == shortcode).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Shortcode not found")
    return RedirectResponse(url=db_link.original_url)


Base.metadata.create_all(engine)