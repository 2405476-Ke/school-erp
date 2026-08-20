from sqlalchemy import Column, String, Integer, JSON
from src.shared.base_model import AuditableBase

class SchoolSettings(AuditableBase):
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
    admission_number_format = Column(String, nullable=False, default="ADM-{YYYY}-{NNNN}")
    last_admission_sequence = Column(Integer, nullable=False, default=0)



from sqlalchemy import Boolean
class AdmissionChecklistItem(AuditableBase):
    __tablename__ = "admission_checklist_items"
    
    school_id = Column(String, nullable=False) # Or UUID depending on your TenantMixin
    item_name = Column(String, nullable=False)
    target_status = Column(String, nullable=False) # 'BOARDING', 'DAY', 'ALL'
    is_mandatory = Column(Boolean, default=True)
