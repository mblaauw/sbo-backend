"""
Utility functions for LLM operations.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

from database import get_db_context
from models import LLMRequestLog, LLMResponseLog, LLMErrorLog

logger = logging.getLogger("sbo.llm_utils")

def log_llm_request(request_type: str, input_data: Dict[str, Any]) -> None:
    """Log an LLM request to the database"""
    with get_db_context() as db:
        try:
            # Sanitize input data if needed (remove large texts, sensitive info)
            sanitized_input = input_data.copy()
            if "text" in sanitized_input and isinstance(sanitized_input["text"], str) and len(sanitized_input["text"]) > 1000:
                sanitized_input["text"] = sanitized_input["text"][:1000] + "... [truncated]"
            
            db_log = LLMRequestLog(
                request_type=request_type,
                input_data=json.dumps(sanitized_input),
                timestamp=datetime.now()
            )
            db.add(db_log)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error logging LLM request: {str(e)}")

def log_llm_response(request_type: str, output_data: Dict[str, Any]) -> None:
    """Log an LLM response to the database"""
    with get_db_context() as db:
        try:
            db_log = LLMResponseLog(
                request_type=request_type,
                output_data=json.dumps(output_data),
                timestamp=datetime.now()
            )
            db.add(db_log)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error logging LLM response: {str(e)}")

def log_llm_error(request_type: str, error_msg: str) -> None:
    """Log an LLM error to the database"""
    with get_db_context() as db:
        try:
            db_log = LLMErrorLog(
                request_type=request_type,
                error_message=error_msg,
                timestamp=datetime.now()
            )
            db.add(db_log)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error logging LLM error: {str(e)}")