from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str


class LoginResponse(BaseModel):
    token: str
    user: UserOut


class EventSummary(BaseModel):
    id: int
    title: str
    event_date: str
    location: str
    expected_attendance: int
    status: str
    confirmed_rsvps: int
    volunteer_slots: int
    filled_slots: int
    open_slots: int


class Volunteer(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    skills: list[str]


class ShiftCoverage(BaseModel):
    id: int
    name: str
    start_time: str
    end_time: str
    needed: int
    skill: str
    assigned: list[str]
    open_slots: int


class StaffingSuggestion(BaseModel):
    shift_id: int
    shift_name: str
    skill: str
    open_slots: int
    suggested_volunteers: list[str]
    rationale: str
