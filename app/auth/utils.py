from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Force passlib to use bcrypt without the strict length check
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b",
)


def hash_password(password: str) -> str:
    """Convert plain password to hashed version for DB storage."""
    # Encode to bytes and truncate to 72 bytes manually before hashing
    password_bytes = password.encode("utf-8")[:72]
    password_truncated = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(password_truncated)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if plain password matches the stored hash."""
    password_bytes = plain_password.encode("utf-8")[:72]
    password_truncated = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.verify(password_truncated, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Create a JWT token containing user data.
    Token expires after ACCESS_TOKEN_EXPIRE_MINUTES minutes.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify a JWT token.
    Returns the payload dict if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None