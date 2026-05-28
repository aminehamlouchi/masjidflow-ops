from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.auth import create_token, hash_password, verify_token
from app.database import connect, init_db
from app.schemas import EventSummary, LoginRequest, LoginResponse, ShiftCoverage, StaffingSuggestion, UserOut, Volunteer

app = FastAPI(title="MasjidFlow Ops API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("MASJIDFLOW_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db(seed=True)


def current_user(authorization: str | None = Header(default=None)) -> UserOut:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = verify_token(authorization.replace("Bearer ", "", 1))
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    with connect() as db:
        row = db.execute("SELECT id, email, name, role FROM users WHERE id = ?", (payload["sub"],)).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return UserOut(**dict(row))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE email = ?", (request.email,)).fetchone()

    if not row or row["password_hash"] != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = UserOut(id=row["id"], email=row["email"], name=row["name"], role=row["role"])
    return LoginResponse(token=create_token(user.id, user.role), user=user)


@app.get("/events", response_model=list[EventSummary])
def list_events(_: UserOut = Depends(current_user)) -> list[EventSummary]:
    with connect() as db:
        events = db.execute("SELECT * FROM events ORDER BY event_date").fetchall()
        return [_event_summary(db, event["id"]) for event in events]


@app.get("/events/{event_id}", response_model=EventSummary)
def get_event(event_id: int, _: UserOut = Depends(current_user)) -> EventSummary:
    with connect() as db:
        event = db.execute("SELECT id FROM events WHERE id = ?", (event_id,)).fetchone()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return _event_summary(db, event_id)


@app.get("/volunteers", response_model=list[Volunteer])
def list_volunteers(_: UserOut = Depends(current_user)) -> list[Volunteer]:
    with connect() as db:
        volunteers = db.execute("SELECT * FROM volunteers ORDER BY name").fetchall()
        results: list[Volunteer] = []
        for volunteer in volunteers:
            skills = db.execute(
                "SELECT skill FROM volunteer_skills WHERE volunteer_id = ? ORDER BY skill",
                (volunteer["id"],),
            ).fetchall()
            results.append(Volunteer(**dict(volunteer), skills=[row["skill"] for row in skills]))
        return results


@app.get("/events/{event_id}/coverage", response_model=list[ShiftCoverage])
def coverage(event_id: int, _: UserOut = Depends(current_user)) -> list[ShiftCoverage]:
    with connect() as db:
        if not db.execute("SELECT id FROM events WHERE id = ?", (event_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Event not found")
        return _coverage(db, event_id)


@app.post("/events/{event_id}/suggestions", response_model=list[StaffingSuggestion])
def staffing_suggestions(event_id: int, _: UserOut = Depends(current_user)) -> list[StaffingSuggestion]:
    with connect() as db:
        shift_coverage = _coverage(db, event_id)
        suggestions: list[StaffingSuggestion] = []
        for shift in shift_coverage:
            if shift.open_slots <= 0:
                continue
            candidates = db.execute(
                """
                SELECT v.name
                FROM volunteers v
                JOIN volunteer_skills s ON s.volunteer_id = v.id
                WHERE s.skill = ?
                AND v.name NOT IN (
                    SELECT v2.name
                    FROM shift_assignments a
                    JOIN volunteers v2 ON v2.id = a.volunteer_id
                    WHERE a.shift_id = ?
                )
                ORDER BY v.name
                LIMIT ?
                """,
                (shift.skill, shift.id, shift.open_slots),
            ).fetchall()
            names = [row["name"] for row in candidates]
            suggestions.append(
                StaffingSuggestion(
                    shift_id=shift.id,
                    shift_name=shift.name,
                    skill=shift.skill,
                    open_slots=shift.open_slots,
                    suggested_volunteers=names,
                    rationale=(
                        f"{shift.name} needs {shift.open_slots} more volunteer(s) with {shift.skill} experience. "
                        "The recommendation prefers volunteers with matching skills who are not already assigned to that shift."
                    ),
                )
            )
        return suggestions


def _event_summary(db, event_id: int) -> EventSummary:
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    volunteer_slots = db.execute("SELECT COALESCE(SUM(needed), 0) AS total FROM shifts WHERE event_id = ?", (event_id,)).fetchone()["total"]
    filled_slots = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM shift_assignments a
        JOIN shifts s ON s.id = a.shift_id
        WHERE s.event_id = ?
        """,
        (event_id,),
    ).fetchone()["total"]
    confirmed_rsvps = db.execute(
        "SELECT COUNT(*) AS total FROM rsvps WHERE event_id = ? AND status = 'confirmed'",
        (event_id,),
    ).fetchone()["total"]
    return EventSummary(
        **dict(event),
        confirmed_rsvps=confirmed_rsvps,
        volunteer_slots=volunteer_slots,
        filled_slots=filled_slots,
        open_slots=max(volunteer_slots - filled_slots, 0),
    )


def _coverage(db, event_id: int) -> list[ShiftCoverage]:
    shifts = db.execute("SELECT * FROM shifts WHERE event_id = ? ORDER BY start_time", (event_id,)).fetchall()
    results: list[ShiftCoverage] = []
    for shift in shifts:
        assigned = db.execute(
            """
            SELECT v.name
            FROM shift_assignments a
            JOIN volunteers v ON v.id = a.volunteer_id
            WHERE a.shift_id = ?
            ORDER BY v.name
            """,
            (shift["id"],),
        ).fetchall()
        names = [row["name"] for row in assigned]
        results.append(
            ShiftCoverage(
                id=shift["id"],
                name=shift["name"],
                start_time=shift["start_time"],
                end_time=shift["end_time"],
                needed=shift["needed"],
                skill=shift["skill"],
                assigned=names,
                open_slots=max(shift["needed"] - len(names), 0),
            )
        )
    return results
