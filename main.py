from fastapi import FastAPI

app = FastAPI()

users = {}

@app.post("/api/users")
def create_user(data: dict):
    user_id = len(users) + 1
    users[user_id] = data
    return {"id": user_id, "message": "User profile saved!"}

@app.get("/api/users/{id}")
def get_user(id: int):
    return users[id]