# llm_service/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from .database import Base

class LLMRequestLog(Base):
    __tablename__ = "llm_request_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String, index=True)
    input_data = Column(Text)
    timestamp = Column(DateTime(timezone=True))

class LLMResponseLog(Base):
    __tablename__ = "llm_response_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String, index=True)
    output_data = Column(Text)
    timestamp = Column(DateTime(timezone=True))

class LLMErrorLog(Base):
    __tablename__ = "llm_error_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String, index=True)
    error_message = Column(Text)
    timestamp = Column(DateTime(timezone=True))





