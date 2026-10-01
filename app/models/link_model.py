from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True,autoincrement=True)
    short_code = Column(String, unique=True, index=True)
    original_url = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime)