"""
Authentication endpoints for SBO application.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from middleware import create_access_token
from models import User as UserModel

router = APIRouter(tags=["auth"])

class TokenRequest(BaseModel):
    username: str
    password: str

@router.post("/token")
def login_for_access_token(form_data: TokenRequest, db: Session = Depends(get_db)):
    """Simple token endpoint for testing"""
    # In a real app, we would check credentials against database
    # For this prototype, we'll accept any username with 'password' as password
    if form_data.password != "password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find user or use default
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    if not user:
        user_id = "1"  # Default user ID
        user_role = "user"
    else:
        user_id = str(user.id)
        user_role = "admin" if form_data.username == "admin" else "user"

    # Create access token with user ID, role, and scopes
    scopes = ["user"]
    if user_role == "admin":
        scopes.extend(["admin", "skills", "assessments", "matches"])

    access_token = create_access_token(
        data={
            "sub": user_id,
            "role": user_role,
            "scopes": scopes
        }
    )

    return {"access_token": access_token, "token_type": "bearer"}
