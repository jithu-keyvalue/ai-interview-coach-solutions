from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

users = {}
ALLOWED_ROLES = {"developer", "designer", "product-manager"}

@app.post("/api/users")
def create_user(data: dict):
    if "name" not in data or not isinstance(data["name"], str):
        return JSONResponse(status_code=400, content={"error": "Name is required and must be a string"})

    if "role" not in data or data["role"] not in ALLOWED_ROLES:
        return JSONResponse(status_code=400, content={"error": "Unsupported role"})

    if "place" not in data or not isinstance(data["place"], str):
        return JSONResponse(status_code=400, content={"error": "Place is required and must be a string"})

    user_id = len(users) + 1
    users[user_id] = data
    return JSONResponse(status_code=201, content={"id": user_id, "message": "User profile saved!"})

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    if user_id not in users:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    return users[user_id]
