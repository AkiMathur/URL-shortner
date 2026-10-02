from pydantic import BaseModel
from datetime import date

class LinkCreateReq(BaseModel):        # what the client sends to create a link
    original_url: str
    custom_alias: str | None = None

class LinkResponse(BaseModel):      # what the client gets back
    original_url: str
    short_code: str
    created_at: date

    class Config:
        from_attributes = True      # lets it read directly from a SQLAlchemy model