from pydantic import BaseModel
from typing import List

class PrincipalKPIs(BaseModel):
    total_students: int
    total_staff: int
    fee_collection_rate: float
    pending_approvals: int

class BursarKPIs(BaseModel):
    total_bank_balance: float
    total_fee_arrears: float
    unmatched_transactions: int
    active_lpos: int

class TrendData(BaseModel):
    label: str
    value: float

class EnrolmentData(BaseModel):
    form_1: int
    form_2: int
    form_3: int
    form_4: int
