from fastapi import FastAPI
from pydantic import BaseModel, Field
from passlib.context import CryptContext
import psycopg2
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    with open("schema.sql") as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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
    hashed_pw = pwd_context.hash(user.password)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, role, place, password_hash) VALUES (%s, %s, %s, %s) RETURNING id",
        (user.name, user.role, user.place, hashed_pw)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return { "id": user_id, "name": user.name, "role": user.role, "place": user.place }

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, role, place FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return dict(zip(["id", "name", "role", "place"], row))
    return {"error": "User not found"}
