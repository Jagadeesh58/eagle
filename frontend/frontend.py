from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

frontend_router = APIRouter(include_in_schema=False)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def get_session_user(request: Request):
    uid = request.cookies.get("user_id")
    name = request.cookies.get("user_name")
    role = request.cookies.get("user_role")
    email = request.cookies.get("user_email")
    if uid and role:
        return {"id": int(uid), "name": name or "", "role": role, "email": email or ""}
    return None

@frontend_router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})

@frontend_router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "admin/dashboard.html", {"request": request, "user": user})


@frontend_router.get("/admin/users", response_class=HTMLResponse)
def admin_users_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "admin/users.html", {"request": request, "user": user})


@frontend_router.get("/admin/areas", response_class=HTMLResponse)
def admin_areas_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "admin/areas.html", {"request": request, "user": user})


@frontend_router.get("/admin/funds", response_class=HTMLResponse)
def admin_funds_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "admin/funds.html", {"request": request, "user": user})


@frontend_router.get("/manager/dashboard", response_class=HTMLResponse)
def manager_dashboard_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "manager":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "manager/dashboard.html", {"request": request, "user": user})


@frontend_router.get("/manager/subareas", response_class=HTMLResponse)
def manager_subareas_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "manager":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "manager/subareas.html", {"request": request, "user": user})


@frontend_router.get("/manager/beneficiaries", response_class=HTMLResponse)
def manager_beneficiaries_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "manager":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "manager/beneficiaries.html", {"request": request, "user": user})


@frontend_router.get("/manager/eligible", response_class=HTMLResponse)
def manager_eligible_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "manager":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "manager/eligible.html", {"request": request, "user": user})


@frontend_router.get("/manager/attendance", response_class=HTMLResponse)
def manager_attendance_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "manager":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "manager/attendance.html", {"request": request, "user": user})


@frontend_router.get("/manager/tracking", response_class=HTMLResponse)
def manager_tracking_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "manager":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "manager/tracking.html", {"request": request, "user": user})


@frontend_router.get("/manager/assignments", response_class=HTMLResponse)
def manager_assignments_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "manager":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "manager/assignments.html", {"request": request, "user": user})


@frontend_router.get("/manager/funds", response_class=HTMLResponse)
def manager_funds_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "manager":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "manager/funds.html", {"request": request, "user": user})


@frontend_router.get("/coordinator/dashboard", response_class=HTMLResponse)
def coordinator_dashboard_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] not in ("field_coordinator", "delivery_coordinator"):
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "coordinator/dashboard.html", {"request": request, "user": user})


@frontend_router.get("/coordinator/attendance", response_class=HTMLResponse)
def coordinator_attendance_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "field_coordinator":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "coordinator/attendance.html", {"request": request, "user": user})


@frontend_router.get("/coordinator/beneficiaries", response_class=HTMLResponse)
def coordinator_beneficiaries_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "field_coordinator":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "coordinator/beneficiaries.html", {"request": request, "user": user})


@frontend_router.get("/coordinator/deliveries", response_class=HTMLResponse)
def coordinator_deliveries_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "delivery_coordinator":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "coordinator/deliveries.html", {"request": request, "user": user})


@frontend_router.get("/coordinator/assignments", response_class=HTMLResponse)
def coordinator_assignments_page(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "delivery_coordinator":
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "coordinator/assignments.html", {"request": request, "user": user})
