import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState
from sqlalchemy.orm import Session
from app.models import User, Message
from app.database import get_db
from app.schemas import UserCreate, UserOut, LoginInput, UpdateUser
from app.auth import hash_password, verify_password, create_token, get_current_user, decode_token
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

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, 
    db: Session = Depends(get_db),
):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message")
            token = data.get("token")

            if not token:
                await websocket.send_text("Missing token.")
                await websocket.close()
                return

            # Decode token and fetch user manually
            try:
                payload = decode_token(token)
                user_id = payload.get("user_id")
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    await websocket.send_text("Invalid user.")
                    await websocket.close()
                    return
            except Exception:
                await websocket.send_text("Invalid token.")
                await websocket.close()
                return

            # Fetch last 20 messages
            past_messages = db.query(Message).filter(Message.user_id == user.id).order_by(Message.id.asc()).limit(20).all()
            history = [
                {"role": m.role, "content": m.content}
                for m in past_messages
            ]
            history.append({"role": "user", "content": message})

            # Save user's message
            db.add(Message(user_id=user.id, role="user", content=message))
            db.commit()

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=history,
                stream=True
            )

            full_reply = ""
            for chunk in response:
                delta = chunk.choices[0].delta
                content = delta.content or ""
                full_reply += content
                if websocket.application_state == WebSocketState.DISCONNECTED:
                    break
                await websocket.send_text(content)
                await asyncio.sleep(0.01)

            # Save reply
            db.add(Message(user_id=user.id, role="assistant", content=full_reply))
            db.commit()

    except WebSocketDisconnect:
        print("WebSocket disconnected")
