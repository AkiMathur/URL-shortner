from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class Clicks(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(Integer, ForeignKey("links.id", ondelete='CASCADE'), index=True)
    clicked_at = Column(DateTime, index=True)
    ip_hash = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)