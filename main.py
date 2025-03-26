from fastapi import FastAPI, HTTPException
from models import Base, User, UserCreate, UserOut
from database import engine, SessionLocal
from passlib.context import CryptContext

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base.metadata.create_all(bind=engine)

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


@app.put("/api/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserCreate):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = data.name
    user.role = data.role
    user.place = data.place
    user.password_hash = pwd_context.hash(data.password)

    db.commit()
    
    db.refresh(user)
    return user

# 📝 TODO: Fix method name for delete operation
@app.get("/api/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return

# 📝 TODO: Does the response structure look right?
@app.get("/api/users", response_model=list[UserCreate])
def list_users():
    db = SessionLocal()
    return db.query(User).all()
