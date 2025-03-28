import os
import openai
import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.models import User
from app.database import get_db
from app.schemas import UserCreate, UserOut, LoginInput, UpdateUser
from app.auth import hash_password, verify_password, create_token, get_current_user

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@app.post("/api/users", response_model=UserOut, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        logger.warning(f"Signup failed: Email already exists - {user.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    new_user = User(name=user.name, email=user.email, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"New user created: {new_user.email} (id={new_user.id})")
    return new_user

@app.post("/api/login")
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({ "user_id": user.id })
    return { "token": token }

@app.get("/api/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.put("/api/me", response_model=UserOut)
def update_me(data: UpdateUser, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.name:
        user.name = data.name
    if data.email:
        user.email = data.email
    if data.password:
        user.password_hash = hash_password(data.password)

    db.commit()
    db.refresh(user)
    return user


@app.delete("/api/me", status_code=204)
def delete_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.delete(current_user)
    db.commit()
    return


@app.post("/api/chat")
def chat(request: Request, payload: dict):
    message = payload.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{ "role": "user", "content": message }]
        )
        reply = response.choices[0].message.content
        return { "reply": reply }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))