from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator



# ── Request bodies ───────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr        # Pydantic validates it's a real email format
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 72:
            raise ValueError("Password cannot exceed 72 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Response bodies ──────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_active: bool
    created_at: datetime