from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: str
    password: str = Field(..., min_length=6)

class UserOut(BaseModel):
    id: int
    name: str
    email: str

class LoginInput(BaseModel):
    email: str
    password: str
