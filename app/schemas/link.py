from pydantic import BaseModel
from datetime import datetime

class LinkCreate(BaseModel):        # what the client sends to create a link
    original_url: str
    custom_alias: str | None = None

class LinkResponse(BaseModel):      # what the client gets back
    short_code: str
    original_url: str
    created_at: datetime

    class Config:
        from_attributes = True      # lets it read directly from a SQLAlchemy model