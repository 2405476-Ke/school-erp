from pydantic import BaseModel
from typing import Optional, Dict, Any

class SchoolSettingsBase(BaseModel):
    school_name: str
    motto: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    current_academic_year: Optional[str] = None
    current_term: Optional[str] = None
    address: Optional[str] = None
    dynamic_config: Optional[Dict[str, Any]] = {}

class SchoolSettingsCreate(SchoolSettingsBase):
    pass

class SchoolSettingsUpdate(SchoolSettingsBase):
    school_name: Optional[str] = None

class SchoolSettingsResponse(SchoolSettingsBase):
    id: str

    class Config:
        from_attributes = True
