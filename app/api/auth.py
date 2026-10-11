from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import db_dependency, user_dependency




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