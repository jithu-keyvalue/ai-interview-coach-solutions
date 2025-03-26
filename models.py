from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    place = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    role: str
    place: str
    password: str = Field(..., min_length=6)

class UserOut(BaseModel):
    id: int
    name: str
    role: str
    place: str
