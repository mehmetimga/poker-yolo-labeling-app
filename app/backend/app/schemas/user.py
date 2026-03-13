from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str | None = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "labeler"


class UserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    email: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


TokenResponse.model_rebuild()
