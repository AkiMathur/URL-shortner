from fastapi import Depends
from typing import Annotated
from sqlalchemy.orm import Session
from app.core.security import verify_token
from app.database import get_db

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(verify_token)]