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
from app.schemas.user_schema import UserCreateReq
from app.schemas.link_schema import LinkCreateReq, LinkResponse
from app.core.security import *
from fastapi.security import OAuth2PasswordRequestForm

load_dotenv()
app = FastAPI()


class CreateLinkReq(BaseModel):
    original_url: str

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

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(verify_token)]

@app.post("/newusers/")
async def create_user(user: UserCreateReq, db: db_dependency):
    db_user = db.query(user_model.Users).filter(user_model.Users.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = user_model.Users(username=user.username, hashed_password=hash_pass(user.password))
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully", "username" : user.username}

@app.post("/login", response_model=Token)
async def login(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    db_user = db.query(user_model.Users).filter(user_model.Users.username == form_data.username).first()
    if not db_user or not verify_pass(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(db_user.id, db_user.username)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/links")
async def create_link(link_req: CreateLinkReq, db: db_dependency, token_user: user_dependency):
    db_link = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"], link_model.Link.original_url == link_req.original_url).first()
    if db_link:
        return {"message": "Link already exists", "short_code": db_link.short_code}
    short_code=url_to_shortcode()
    new_shortcode = link_model.Link(
        short_code=short_code,
        original_url=link_req.original_url,
        owner_id=token_user["token_userid"],
        created_at=date.today()
    )
    db.add(new_shortcode)
    db.commit()
    return {"message": "Link created successfully", "short_code": short_code}

@app.get("/all_links")
async def get_all_links(token_user: user_dependency, db: db_dependency) -> list[LinkResponse]:
    db_links = db.query(link_model.Link).filter(link_model.Link.owner_id == token_user["token_userid"]).all()
    if not db_links:
        raise HTTPException(status_code=404, detail="No links found for this user")

    return [LinkResponse(
        original_url=link.original_url,
        short_code=link.short_code,
        created_at=link.created_at
    ) for link in db_links]

@app.get("/{shortcode}/")
async def get_link(shortcode: str, db: db_dependency):
    db_link = db.query(link_model.Link).filter(link_model.Link.short_code == shortcode).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Shortcode not found")
    return RedirectResponse(url=db_link.original_url)


Base.metadata.create_all(engine)