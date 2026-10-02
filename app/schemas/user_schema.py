from pydantic import BaseModel

class UserCreateReq(BaseModel):        # what the client sends to create a user
    username: str
    password: str