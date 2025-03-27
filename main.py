from fastapi import FastAPI, HTTPException
from models import User
from database import SessionLocal
from schemas import UserCreate, UserOut
from passlib.context import CryptContext

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/api/users", response_model=UserOut, status_code=201)
def create_user(user: UserCreate):
    db = SessionLocal()
    hashed_pw = pwd_context.hash(user.password)

    new_user = User(name=user.name, email=user.email, password_hash=hashed_pw)
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
