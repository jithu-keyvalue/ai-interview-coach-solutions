import os
import time
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.models import User, Message
from app.database import get_db
from app.schemas import UserCreate, UserOut, LoginInput, UpdateUser, ChatInput
from app.auth import hash_password, verify_password, create_token, get_current_user
from openai import OpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


@app.post("/api/chat/stream")
def chat_stream(
    data: ChatInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    past_messages = (
        db.query(Message)
        .filter(Message.user_id == user.id)
        .order_by(Message.id.asc())
        .limit(20)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in past_messages]
    history.append({"role": "user", "content": data.message})

    def event_generator():
        full_reply = ""
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=history,
                stream=True
            )

            for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    token = delta.content
                    full_reply += token
                    yield f"data: {token}\n\n"
                    time.sleep(0.01)  # smoother delivery for UI

            # Save conversation
            db.add(Message(user_id=user.id, role="user", content=data.message))
            db.add(Message(user_id=user.id, role="assistant", content=full_reply))
            db.commit()

        except Exception as e:
            logger.error(f"SSE Error: {e}")
            yield f"event: error\ndata: Chat failed\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/chat/history")
def get_chat_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    messages = db.query(Message).filter(Message.user_id == user.id).order_by(Message.id).all()
    return [
        {"role": m.role, "content": m.content}
        for m in messages
    ]
