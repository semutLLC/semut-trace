# models.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True)
    request_type = Column(String)
    request_text = Column(String)
    status = Column(String, default="submitted")
    owner_notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
