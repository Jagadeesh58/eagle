from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date
try:
    from backend.eagle import EaglDB
except ModuleNotFoundError:
    from eagle import EaglDB

backend_router = APIRouter()
db = EaglDB()

class User(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    mobile: Optional[str] = None
    manager_id: Optional[int] = None
    
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    mobile: Optional[str] = None
    manager_id: Optional[int] = None
    
class UserUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    mobile: Optional[str] = None
    manager_id: Optional[int] = None

class UpdateProfileRequest(BaseModel):
    user_id: int
    name: str
    mobile: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    user_id: int
    old_password: str
    new_password: str
    
class LoginRequest(BaseModel):
    email: str
    password: str
    
class Area(BaseModel):
    id: Optional[int] = None
    area_name: str
    district: str
    poverty_percent: float
    manager_id: int
    
class Fund(BaseModel):
    id: Optional[int] = None
    manager_id: int
    total_amount: float
    
class SpendRequest(BaseModel):
    manager_id: int
    amount_spent: float
    
class SubArea(BaseModel):
    id: Optional[int] = None
    area_id: int
    sub_area_name: str
    coordinator1_id: int
    manager_id: int
    assigned_date: date
    
class ReassignRequest(BaseModel):
    id: int
    coordinator1_id: int
    
class Attendance(BaseModel):
    id: Optional[int] = None
    coordinator_id: int
    sub_area_id: int
    
class Beneficiary(BaseModel):
    id: Optional[int] = None
    family_name: str
    sub_area_id: int
    family_members: int
    annual_income: float
    collector_id: int
    
class FilterRequest(BaseModel):
    sub_area_id: int
    per_capita_limit: float
    
class Delivery(BaseModel):
    id: Optional[int] = None
    beneficiary_id: int
    coordinator2_id: int
    livestock_type: str
    
class UpdateNotes(BaseModel):
    notes: str
    
class EligibleFamily(BaseModel):
    beneficiary_id: int
    per_capita_income: float
    approval_threshold: float
    approved_by: int
    
class StatusUpdate(BaseModel):
    status: str
    
class Assignment(BaseModel):
    manager_id: int
    coordinator2_id: int
    beneficiary_id: int
    sub_area_id: int
    assigned_date: date
    
class AssignmentUpdate(BaseModel):
    id: int
    coordinator2_id: int
    beneficiary_id: int
    sub_area_id: int
    assigned_date: date

# ============================================================
# USERS
# ============================================================

@backend_router.get('/users', tags=['Users'])
def get_all_users():
    return db.get_all_users()
    
@backend_router.get('/users/{user_id}', tags=['Users'])
def get_user(user_id: int):
    user = db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Exclude password hash
    user.pop("password", None)
    return user

@backend_router.get('/users/manager/{manager_id}/coordinators', tags=['Users'])
def get_coordinators_under_manager(manager_id: int):
    # Instead of throwing 404, just return empty list
    return db.get_coordinators_under_manager(manager_id)

@backend_router.post('/users/login', tags=['Users'])
def login(req: LoginRequest):
    user = db.login(req.email, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return user

@backend_router.post('/users/change-password', tags=['Users'])
def change_password(req: ChangePasswordRequest):
    user = db.get_user_by_id(req.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not db.verify_password(req.old_password, user['password']):
        # Fallback check if it was still plain text
        if user['password'] != req.old_password:
            raise HTTPException(status_code=400, detail="Current password is incorrect")
            
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        
    db.change_password(req.user_id, req.new_password)
    return {"message": "Password updated successfully"}

@backend_router.put('/users/profile', tags=['Users'])
def update_profile(req: UpdateProfileRequest):
    user = db.get_user_by_id(req.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.update_user_profile(req.user_id, req.name, req.mobile)
    updated = db.get_user_by_id(req.user_id)
    updated.pop('password', None)
    return updated

@backend_router.post('/users', tags=['Users'])
def add_user(user: UserCreate):
    if db.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    if user.role in ('field_coordinator', 'delivery_coordinator') and not user.manager_id:
        raise HTTPException(status_code=400, detail="Coordinators must have a manager_id")
        
    if user.role in ('admin', 'manager') and user.manager_id:
        user.manager_id = None
        
    new_id = db.add_user(user.name, user.email, user.password, user.role, user.mobile, user.manager_id)
    new_user = db.get_user_by_id(new_id)
    new_user.pop('password', None)
    return new_user

@backend_router.put('/users', tags=['Users'])
def update_user(user: UserUpdate):
    existing_user = db.get_user_by_id(user.id)
    if existing_user is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.email is not None and user.email != existing_user['email']:
        if db.get_user_by_email(user.email):
            raise HTTPException(status_code=400, detail="Email already registered")
            
    if user.role in ('field_coordinator', 'delivery_coordinator') and not user.manager_id and not existing_user['manager_id']:
        raise HTTPException(status_code=400, detail="Coordinators must have a manager_id")
        
    # Resolve defaults
    u_name = user.name if user.name is not None else existing_user['name']
    u_email = user.email if user.email is not None else existing_user['email']
    u_password = user.password if user.password is not None else existing_user['password']
    u_role = user.role if user.role is not None else existing_user['role']
    u_mobile = user.mobile if user.mobile is not None else existing_user.get('mobile')
    u_manager_id = user.manager_id if user.manager_id is not None else existing_user['manager_id']

    if u_role in ('admin', 'manager'):
        u_manager_id = None

    db.update_user(user.id, u_name, u_email, u_password, u_role, u_mobile, u_manager_id)
    updated = db.get_user_by_id(user.id)
    updated.pop('password', None)
    return updated

@backend_router.delete('/users/{user_id}', tags=['Users'])
def delete_user(user_id: int):
    if db.get_user_by_id(user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete_user(user_id)
    return {"message": "User deleted successfully"}

# ============================================================
# AREAS
# ============================================================

@backend_router.get('/areas', tags=['Areas'])
def get_all_areas():
    return db.get_all_areas()

@backend_router.get('/areas/{area_id}', tags=['Areas'])
def get_area(area_id: int):
    area = db.get_area_by_id(area_id)
    if area is None:
        raise HTTPException(status_code=404, detail="Area not found")
    return area

@backend_router.get('/areas/manager/{manager_id}', tags=['Areas'])
def get_areas_by_manager(manager_id: int):
    # Always return a list, even if empty
    return db.get_areas_by_manager(manager_id)

@backend_router.post('/areas', tags=['Areas'])
def add_area(area: Area):
    if db.get_area_by_name(area.area_name) is None:
        new_id = db.add_area(area.area_name, area.district, area.poverty_percent, area.manager_id)
        return db.get_area_by_id(new_id)
    raise HTTPException(status_code=400, detail="Area with this name already exists")

@backend_router.put('/areas', tags=['Areas'])
def update_area_manager(area: Area):
    if db.get_area_by_id(area.id) is None:
        raise HTTPException(status_code=404, detail="Area not found")
    db.update_area_manager(area.id, area.manager_id)
    return db.get_area_by_id(area.id)

@backend_router.delete('/areas/{area_id}', tags=['Areas'])
def delete_area(area_id: int):
    if db.get_area_by_id(area_id) is None:
        raise HTTPException(status_code=404, detail="Area not found")
    db.delete_area(area_id)
    return {"message": "Area deleted successfully"}

# ============================================================
# FUNDS
# ============================================================

@backend_router.get('/funds', tags=['Funds'])
def get_all_funds():
    return db.get_all_funds()

@backend_router.get('/funds/{fund_id}', tags=['Funds'])
def get_fund(fund_id: int):
    fund = db.get_fund_by_id(fund_id)
    if fund is None:
        raise HTTPException(status_code=404, detail="Fund not found")
    return fund

@backend_router.get('/funds/manager/{manager_id}', tags=['Funds'])
def get_fund_by_manager(manager_id: int):
    # Returns None/empty object rather than throwing 404 to be safe
    fund = db.get_fund_by_manager(manager_id)
    if fund is None:
        return None
    return fund

@backend_router.post('/funds', tags=['Funds'])
def add_fund(fund: Fund):
    if fund.total_amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    new_id = db.add_fund(fund.manager_id, fund.total_amount)
    return db.get_fund_by_id(new_id)

@backend_router.put('/funds/spend', tags=['Funds'])
def spend_from_fund(req: SpendRequest):
    if req.amount_spent <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    try:
        db.deduct_from_fund(req.manager_id, req.amount_spent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return db.get_fund_by_manager(req.manager_id)

@backend_router.delete('/funds/{fund_id}', tags=['Funds'])
def delete_fund(fund_id: int):
    if db.get_fund_by_id(fund_id) is None:
        raise HTTPException(status_code=404, detail="Fund not found")
    db.delete_fund(fund_id)
    return {"message": "Fund deleted successfully"}

# ============================================================
# SUB AREAS
# ============================================================

@backend_router.get('/subareas', tags=['Sub Areas'])
def get_all_sub_areas():
    return db.get_all_sub_areas()

@backend_router.get('/subareas/{subarea_id}', tags=['Sub Areas'])
def get_sub_area(subarea_id: int):
    subarea = db.get_sub_area_by_id(subarea_id)
    if subarea is None:
        raise HTTPException(status_code=404, detail="Sub area not found")
    return subarea

@backend_router.get('/subareas/area/{area_id}', tags=['Sub Areas'])
def get_sub_areas_by_area(area_id: int):
    return db.get_sub_areas_by_area(area_id)

@backend_router.get('/subareas/coordinator/{coordinator1_id}', tags=['Sub Areas'])
def get_sub_areas_by_coordinator(coordinator1_id: int):
    return db.get_sub_areas_by_coordinator(coordinator1_id)
    
@backend_router.get('/subareas/manager/{manager_id}', tags=['Sub Areas'])
def get_sub_areas_by_manager(manager_id: int):
    return db.get_sub_areas_by_manager(manager_id)

@backend_router.post('/subareas', tags=['Sub Areas'])
def add_sub_area(subarea: SubArea):
    new_id = db.add_sub_area(
        subarea.area_id, subarea.sub_area_name,
        subarea.coordinator1_id, subarea.manager_id, subarea.assigned_date
    )
    return db.get_sub_area_by_id(new_id)

@backend_router.put('/subareas', tags=['Sub Areas'])
def reassign_sub_area(req: ReassignRequest):
    if db.get_sub_area_by_id(req.id) is None:
        raise HTTPException(status_code=404, detail="Sub area not found")
    db.reassign_sub_area(req.id, req.coordinator1_id)
    return db.get_sub_area_by_id(req.id)

@backend_router.delete('/subareas/{subarea_id}', tags=['Sub Areas'])
def delete_sub_area(subarea_id: int):
    if db.get_sub_area_by_id(subarea_id) is None:
        raise HTTPException(status_code=404, detail="Sub area not found")
    db.delete_sub_area(subarea_id)
    return {"message": "Sub area deleted successfully"}

# ============================================================
# ATTENDANCE
# ============================================================

@backend_router.get('/attendance/{att_id}', tags=['Attendance'])
def get_attendance(att_id: int):
    record = db.get_attendance_by_id(att_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record

@backend_router.get('/attendance/coordinator/{coordinator_id}', tags=['Attendance'])
def get_attendance_by_coordinator(coordinator_id: int):
    return db.get_attendance_by_coordinator(coordinator_id)

@backend_router.get('/attendance/manager/{manager_id}', tags=['Attendance'])
def get_attendance_by_manager(manager_id: int):
    return db.get_attendance_by_manager(manager_id)

@backend_router.get('/attendance/today/{coordinator_id}', tags=['Attendance'])
def get_todays_attendance(coordinator_id: int):
    record = db.get_todays_attendance(coordinator_id)
    if record is None:
        # Return null to easily check in JS
        return None
    return record

@backend_router.post('/attendance', tags=['Attendance'])
def add_attendance(att: Attendance):
    # Prevent multiple check-ins on same day
    existing = db.get_todays_attendance(att.coordinator_id)
    if existing:
        raise HTTPException(status_code=400, detail="Already checked in today")
        
    new_id = db.add_attendance(att.coordinator_id, att.sub_area_id)
    return db.get_attendance_by_id(new_id)

@backend_router.put('/attendance/verify/{att_id}', tags=['Attendance'])
def verify_attendance(att_id: int):
    if db.get_attendance_by_id(att_id) is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db.mark_present(att_id)
    return db.get_attendance_by_id(att_id)

@backend_router.delete('/attendance/{att_id}', tags=['Attendance'])
def delete_attendance(att_id: int):
    if db.get_attendance_by_id(att_id) is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db.delete_attendance(att_id)
    return {"message": "Attendance record deleted successfully"}

# ============================================================
# BENEFICIARIES
# ============================================================

@backend_router.get('/beneficiaries/{ben_id}', tags=['Beneficiaries'])
def get_beneficiary(ben_id: int):
    ben = db.get_beneficiary_by_id(ben_id)
    if ben is None:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    return ben

@backend_router.get('/beneficiaries/collector/{collector_id}', tags=['Beneficiaries'])
def get_beneficiaries_by_collector(collector_id: int):
    return db.get_beneficiaries_by_collector(collector_id)

@backend_router.get('/beneficiaries/manager/{manager_id}', tags=['Beneficiaries'])
def get_beneficiaries_by_manager(manager_id: int):
    return db.get_beneficiaries_by_manager(manager_id)

@backend_router.get('/beneficiaries/approved', tags=['Beneficiaries'])
def get_approved_beneficiaries():
    return db.get_approved_beneficiaries()

@backend_router.post('/beneficiaries/filter', tags=['Beneficiaries'])
def filter_by_income(req: FilterRequest):
    return db.filter_beneficiaries_by_income(req.sub_area_id, req.per_capita_limit)

@backend_router.post('/beneficiaries', tags=['Beneficiaries'])
def add_beneficiary(ben: Beneficiary):
    if ben.family_members <= 0:
        raise HTTPException(status_code=400, detail="Family members must be > 0")
    if ben.annual_income < 0:
        raise HTTPException(status_code=400, detail="Annual income cannot be negative")
        
    new_id = db.add_beneficiary(
        ben.family_name, ben.sub_area_id, ben.family_members, ben.annual_income, ben.collector_id
    )
    return db.get_beneficiary_by_id(new_id)

@backend_router.put('/beneficiaries/approve/{ben_id}', tags=['Beneficiaries'])
def approve_beneficiary(ben_id: int):
    if db.get_beneficiary_by_id(ben_id) is None:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    db.approve_beneficiary(ben_id)
    return db.get_beneficiary_by_id(ben_id)

@backend_router.delete('/beneficiaries/{ben_id}', tags=['Beneficiaries'])
def delete_beneficiary(ben_id: int):
    if db.get_beneficiary_by_id(ben_id) is None:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    db.delete_beneficiary(ben_id)
    return {"message": "Beneficiary deleted successfully"}

# ============================================================
# DELIVERY
# ============================================================

@backend_router.get('/delivery/{del_id}', tags=['Delivery'])
def get_delivery(del_id: int):
    delivery = db.get_delivery_by_id(del_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery record not found")
    return delivery

@backend_router.get('/delivery/coordinator/{coordinator2_id}', tags=['Delivery'])
def get_deliveries_by_coordinator(coordinator2_id: int):
    return db.get_deliveries_by_coordinator(coordinator2_id)

@backend_router.get('/delivery/all', tags=['Delivery'])
def get_all_deliveries():
    return db.get_all_deliveries()

@backend_router.post('/delivery', tags=['Delivery'])
def add_delivery(delivery: Delivery):
    new_id = db.add_delivery(delivery.beneficiary_id, delivery.coordinator2_id, delivery.livestock_type)
    return db.get_delivery_by_id(new_id)

@backend_router.put('/delivery/deliver/{del_id}', tags=['Delivery'])
def mark_delivered(del_id: int, req: UpdateNotes):
    if db.get_delivery_by_id(del_id) is None:
        raise HTTPException(status_code=404, detail="Delivery record not found")
    db.mark_delivered(del_id, req.notes)
    return db.get_delivery_by_id(del_id)

@backend_router.put('/delivery/upskill/{del_id}', tags=['Delivery'])
def mark_upskill_done(del_id: int, req: UpdateNotes):
    if db.get_delivery_by_id(del_id) is None:
        raise HTTPException(status_code=404, detail="Delivery record not found")
    db.mark_upskill_done(del_id, req.notes)
    return db.get_delivery_by_id(del_id)

@backend_router.delete('/delivery/{del_id}', tags=['Delivery'])
def delete_delivery(del_id: int):
    if db.get_delivery_by_id(del_id) is None:
        raise HTTPException(status_code=404, detail="Delivery record not found")
    db.delete_delivery(del_id)
    return {"message": "Delivery record deleted successfully"}

# ============================================================
# ELIGIBLE FAMILIES
# ============================================================

@backend_router.get('/eligible', tags=['Eligible Families'])
def get_all_eligible():
    return db.get_all_eligible_families()

@backend_router.get('/eligible/status/{status}', tags=['Eligible Families'])
def get_eligible_by_status(status: str):
    return db.get_eligible_by_status(status)

@backend_router.get('/eligible/manager/{manager_id}', tags=['Eligible Families'])
def get_eligible_by_manager(manager_id: int):
    return db.get_eligible_by_manager(manager_id)

@backend_router.get('/eligible/{ef_id}', tags=['Eligible Families'])
def get_eligible(ef_id: int):
    record = db.get_eligible_family_by_id(ef_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@backend_router.post('/eligible', tags=['Eligible Families'])
def add_eligible(ef: EligibleFamily):
    new_id = db.add_eligible_family(ef.beneficiary_id, ef.per_capita_income, ef.approval_threshold, ef.approved_by)
    return db.get_eligible_family_by_id(new_id)

@backend_router.put('/eligible/{ef_id}/status', tags=['Eligible Families'])
def update_eligible_status(ef_id: int, req: StatusUpdate):
    if db.get_eligible_family_by_id(ef_id) is None:
        raise HTTPException(status_code=404, detail="Record not found")
    db.update_delivery_status(ef_id, req.status)
    return db.get_eligible_family_by_id(ef_id)

@backend_router.delete('/eligible/{ef_id}', tags=['Eligible Families'])
def delete_eligible(ef_id: int):
    if db.get_eligible_family_by_id(ef_id) is None:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete_eligible_family(ef_id)
    return {"message": "Record deleted successfully"}


# ============================================================
# ASSIGNMENTS
# ============================================================

@backend_router.get('/assignments/coordinator/{coordinator2_id}', tags=['Assignments'])
def get_assignments_by_coordinator(coordinator2_id: int):
    return db.get_assignments_by_coordinator2(coordinator2_id)

@backend_router.get('/assignments/manager/{manager_id}', tags=['Assignments'])
def get_assignments_by_manager(manager_id: int):
    return db.get_assignments_by_manager(manager_id)

@backend_router.get('/assignments/{assign_id}', tags=['Assignments'])
def get_assignment(assign_id: int):
    assignment = db.get_assignment_by_id(assign_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@backend_router.post('/assignments', tags=['Assignments'])
def add_assignment(assign: Assignment):
    new_id = db.add_assignment(
        assign.manager_id, assign.coordinator2_id,
        assign.beneficiary_id, assign.sub_area_id, assign.assigned_date
    )
    return db.get_assignment_by_id(new_id)

@backend_router.put('/assignments', tags=['Assignments'])
def update_assignment(assign: AssignmentUpdate):
    if db.get_assignment_by_id(assign.id) is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db.update_assignment(
        assign.id,
        assign.coordinator2_id,
        assign.beneficiary_id,
        assign.sub_area_id,
        assign.assigned_date
    )
    return db.get_assignment_by_id(assign.id)

@backend_router.put('/assignments/{assign_id}/status', tags=['Assignments'])
def update_assignment_status(assign_id: int, req: StatusUpdate):
    if db.get_assignment_by_id(assign_id) is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.update_assignment_status(assign_id, req.status)
    return db.get_assignment_by_id(assign_id)

@backend_router.delete('/assignments/{assign_id}', tags=['Assignments'])
def delete_assignment(assign_id: int):
    if db.get_assignment_by_id(assign_id) is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.delete_assignment(assign_id)
    return {"message": "Assignment deleted successfully"}
