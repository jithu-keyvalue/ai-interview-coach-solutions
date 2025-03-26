from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

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

@app.post("/api/users", response_model=UserOut, status_code=201)
def create_user(user: UserCreate):
    db = SessionLocal()
    hashed_pw = pwd_context.hash(user.password)

    new_user = User(
        name=user.name,
        role=user.role,
        place=user.place,
        password_hash=hashed_pw
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.get("/api/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    db = SessionLocal()

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

