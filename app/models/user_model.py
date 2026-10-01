from sqlalchemy import Boolean, Column,Integer,String,Date,ForeignKey
from app.database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True,index=True,autoincrement=True)
    username = Column(String,unique=True,index=True,nullable=False)
    hashed_password = Column(String,nullable=False)

#alembic revision --autogenerate -m "new table"
#alembic upgrade head