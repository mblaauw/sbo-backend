# services/auth_utils.py
"""
Centralized authentication utilities for all services.
"""

from fastapi import HTTPException, status, Depends, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from pydantic import BaseModel, ValidationError
from typing import Dict, List, Optional, Any, Union
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("sbo.auth")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# OAuth2 Bearer token setup
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "admin": "Full administrative access",
        "user": "Regular user access",
        "assessments": "Access to assessments",
        "matches": "Access to skills matching functions",
    },
)

class TokenData(BaseModel):
    """Data model for JWT token claims"""
    sub: str
    role: str = "user"
    scopes: List[str] = []
    exp: Optional[datetime] = None
    
class User(BaseModel):
    """Basic user information extracted from the token"""
    id: str
    role: str = "user"
    scopes: List[str] = []

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with an expiration time.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        The encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error encoding JWT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token",
        )

def get_token_data(token: str) -> TokenData:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token to validate
        
    Returns:
        The decoded token data
        
    Raises:
        HTTPException: If the token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract user ID
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception
        
        # Extract expiration time
        exp = payload.get("exp")
        if exp is None:
            logger.warning("Token missing 'exp' claim")
            raise credentials_exception
            
        # Extract role and scopes
        role = payload.get("role", "user")
        scopes = payload.get("scopes", [])
        
        token_data = TokenData(
            sub=user_id,
            role=role,
            scopes=scopes,
            exp=datetime.fromtimestamp(exp)
        )
        
        return token_data
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise credentials_exception
    except ValidationError as e:
        logger.warning(f"Token data validation error: {str(e)}")
        raise credentials_exception

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from the JWT token.
    
    Args:
        token: The JWT token from the Authorization header
        
    Returns:
        User information extracted from the token
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    token_data = get_token_data(token)
    
    # Check if token is expired
    if datetime.utcnow() > token_data.exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return User(
        id=token_data.sub,
        role=token_data.role,
        scopes=token_data.scopes
    )

def get_current_user_with_scopes(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user and validate required scopes.
    
    Args:
        security_scopes: Required security scopes
        token: The JWT token from the Authorization header
        
    Returns:
        User information extracted from the token
        
    Raises:
        HTTPException: If the token is invalid or missing required scopes
    """
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    token_data = get_token_data(token)
    
    # Check if token is expired
    if datetime.utcnow() > token_data.exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": authenticate_value},
        )
    
    # Check required scopes
    if security_scopes.scopes:
        # Admin role has access to everything
        if token_data.role != "admin":
            for scope in security_scopes.scopes:
                if scope not in token_data.scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Not enough permissions. Required scope: {scope}",
                        headers={"WWW-Authenticate": authenticate_value},
                    )
    
    return User(
        id=token_data.sub,
        role=token_data.role,
        scopes=token_data.scopes
    )

# Dependency for admin-only endpoints
def admin_required(user: User = Depends(get_current_user)) -> User:
    """
    Verify that the current user has admin role.
    
    Args:
        user: The current user
        
    Returns:
        The current user if they have admin role
        
    Raises:
        HTTPException: If the user does not have admin role
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user