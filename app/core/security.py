import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

if not SECRET_KEY or not ALGORITHM:
    raise RuntimeError("SECRET_KEY or ALGORITHM not set in environment")

def hash_pass(passw: str) -> str:

    salt = bcrypt.gensalt()
    hashed= bcrypt.hashpw(password=passw.encode('utf-8'),salt=salt)
    return hashed.decode('utf-8')

def verify_pass(passw: str, hashed: str) -> bool:
    return bcrypt.checkpw(password=passw.encode('utf-8'), hashed_password=hashed.encode('utf-8'))


#Create JWT token
def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY,algorithm=ALGORITHM)

#Verify JWT token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Token"
        )