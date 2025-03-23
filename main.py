from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI()
users = {}

class User(BaseModel):
    name: str = Field(..., min_length=2, max_length=10)
    role: Literal["developer", "designer", "product-manager", "tester"]
    place: str = Field(..., min_length=2)

@app.post("/api/users", status_code=201)
def create_user(user: User):
    user_id = len(users) + 1
    users[user_id] = user.model_dump()
    return {"id": user_id, "message": "User profile saved!"}

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return users.get(user_id, {"error": "User not found"})
