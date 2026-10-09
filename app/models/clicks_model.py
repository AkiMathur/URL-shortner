from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class Clicks(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True,autoincrement=True)
    link_id = Column(Integer, ForeignKey("links.id",ondelete='CASCADE'))
    clicked_at = Column(DateTime)