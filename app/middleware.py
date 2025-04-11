"""
Middleware for error handling, logging, and authentication for all services.
"""

from fastapi import FastAPI, Request, Response, status, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from jose import jwt, JWTError
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Dict, Any, Callable, Union
import logging
import time
import traceback
from datetime import datetime, timedelta

from config import get_settings

logger = logging.getLogger("sbo.middleware")
settings = get_settings()

# JWT configuration from settings
SECRET_KEY = settings.security.jwt_secret_key
ALGORITHM = settings.security.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.jwt_access_token_expire_minutes

# OAuth2 Bearer token setup with scopes
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "admin": "Full administrative access",
        "user": "Regular user access",
        "skills": "Access to skills functions",
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

def setup_error_handlers(app: FastAPI) -> None:
    """
    Set up standard error handlers for a FastAPI application.
    
    Args:
        app: The FastAPI application to configure
    """
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP error: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        error_msg = f"Unexpected error: {str(exc)}"
        stack_trace = traceback.format_exc()
        logger.error(f"{error_msg}\n{stack_trace}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )

def add_request_logging_middleware(app: FastAPI) -> None:
    """
    Add request logging middleware to a FastAPI application.
    
    Args:
        app: The FastAPI application to configure
    """
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next: Callable):
        start_time = time.time()
        
        request_id = request.headers.get("X-Request-ID", f"req-{datetime.now().timestamp()}")
        method = request.method
        path = request.url.path
        query = request.url.query
        client_host = request.client.host if request.client else "unknown"
        
        logger.info(f"Request started: {method} {path}?{query} from {client_host} (ID: {request_id})")
        
        try:
            response = await call_next(request)
            
            process_time_ms = round((time.time() - start_time) * 1000, 2)
            status_code = response.status_code
            
            logger.info(
                f"Request completed: {method} {path} - {status_code} in {process_time_ms}ms (ID: {request_id})"
            )
            
            # Add processing time header
            response.headers["X-Process-Time-Ms"] = str(process_time_ms)
            response.headers["X-Request-ID"] = request_id
            
            return response
        except Exception as e:
            process_time_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"Request failed: {method} {path} in {process_time_ms}ms - {str(e)} (ID: {request_id})"
            )
            raise

def setup_cors(app: FastAPI) -> None:
    """
    Set up CORS middleware for a FastAPI application.
    
    Args:
        app: The FastAPI application to configure
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.service.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_middleware(app: FastAPI) -> None:
    """
    Set up all common middleware for a FastAPI application.
    
    Args:
        app: The FastAPI application to configure
    """
    if settings.service.enable_cors:
        setup_cors(app)
    
    setup_error_handlers(app)
    add_request_logging_middleware(app)