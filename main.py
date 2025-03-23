from fastapi import FastAPI

app = FastAPI()

users = {}

@app.post("/api/users")
def create_user(data: dict):
    user_id = len(users) + 1
    users[user_id] = data
    return {"id": user_id, "message": "User profile saved!"}

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return users.get(user_id, {"error": "User not found"})

@app.put("/api/users/{user_id}")
def update_user(user_id: int, data: dict):
    if user_id not in users:
        return {"error": "User not found"}
    users[user_id].update(data)
    return {"message": "User updated!"}

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int):
    if user_id in users:
        del users[user_id]
        return {"message": "User deleted!"}
    return {"error": "User not found"}
