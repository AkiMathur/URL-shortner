from pydantic import BaseModel

class UserCreate(BaseModel):        # what the client sends to create a user
    username: str
    email: str
    password: str