from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    prompt = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    intent_json = Column(Text, nullable=True)
    database_schema_json = Column(Text, nullable=True)
    api_schema_json = Column(Text, nullable=True)
    ui_schema_json = Column(Text, nullable=True)
    auth_rules_json = Column(Text, nullable=True)
