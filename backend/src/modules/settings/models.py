from sqlalchemy import Column, String, Integer, JSON
from src.shared.base_model import BaseModel

class SchoolSettings(BaseModel):
    __tablename__ = "school_settings"

    school_name = Column(String, nullable=False, default="Default High School")
    motto = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    current_academic_year = Column(String, nullable=True)
    current_term = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    # Store dynamic dropdowns or configuration arrays here if needed
    dynamic_config = Column(JSON, default={})
