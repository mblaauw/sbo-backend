# services/middleware.py
"""
Common middleware for error handling and request logging across all services.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import time
import traceback
from typing import Callable, Dict, Any

logger = logging.getLogger("sbo.middleware")

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
        
        request_id = request.headers.get("X-Request-ID", "unknown")
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

def setup_middleware(app: FastAPI) -> None:
    """
    Set up all common middleware for a FastAPI application.
    
    Args:
        app: The FastAPI application to configure
    """
    setup_error_handlers(app)
    add_request_logging_middleware(app)