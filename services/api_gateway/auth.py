# api_gateway/auth.py
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status
from typing import Dict, Any
from jose import jwt
from datetime import datetime, timedelta
import os

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT access token with an expiration time.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str) -> Dict[str, Any]:
    """
    Validate the JWT token and return the user information.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return {"user_id": user_id, "role": payload.get("role", "user")}
    except jwt.PyJWTError:
        raise credentials_exception