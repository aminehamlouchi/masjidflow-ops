from __future__ import annotations

from pathlib import Path
import os
import sqlite3

from app.auth import hash_password


def get_db_path() -> Path:
    return Path(os.getenv("MASJIDFLOW_DB_PATH", "./masjidflow.db"))


def connect() -> sqlite3.Connection:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(seed: bool = True) -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                event_date TEXT NOT NULL,
                location TEXT NOT NULL,
                expected_attendance INTEGER NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS volunteers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS volunteer_skills (
                volunteer_id INTEGER NOT NULL,
                skill TEXT NOT NULL,
                UNIQUE(volunteer_id, skill),
                FOREIGN KEY(volunteer_id) REFERENCES volunteers(id)
            );

            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY,
                event_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                needed INTEGER NOT NULL,
                skill TEXT NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id)
            );

            CREATE TABLE IF NOT EXISTS shift_assignments (
                id INTEGER PRIMARY KEY,
                shift_id INTEGER NOT NULL,
                volunteer_id INTEGER NOT NULL,
                UNIQUE(shift_id, volunteer_id),
                FOREIGN KEY(shift_id) REFERENCES shifts(id),
                FOREIGN KEY(volunteer_id) REFERENCES volunteers(id)
            );

            CREATE TABLE IF NOT EXISTS rsvps (
                id INTEGER PRIMARY KEY,
                event_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id)
            );
            """
        )
    if seed:
        seed_demo_data()


def seed_demo_data() -> None:
    with connect() as db:
        db.execute(
            "INSERT OR IGNORE INTO users (id, email, name, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (1, "admin@masjidflow.local", "Demo Admin", hash_password("demo-admin"), "admin"),
        )

        events = [
            (1, "MSA Welcome Halaqah", "2026-08-24T18:30:00", "University of Louisville SAC", 65, "planning"),
            (2, "Community Service Day", "2026-09-07T09:00:00", "Alnur Mosque Islamic Center", 110, "planning"),
            (3, "Friday Youth Night", "2026-09-12T19:15:00", "Alnur Mosque Gym", 85, "confirmed"),
        ]
        db.executemany(
            "INSERT OR IGNORE INTO events (id, title, event_date, location, expected_attendance, status) VALUES (?, ?, ?, ?, ?, ?)",
            events,
        )

        volunteers = [
            (1, "Sara Ahmed", "sara@example.com", "502-555-0101"),
            (2, "Yusuf Khan", "yusuf@example.com", "502-555-0102"),
            (3, "Leila Omar", "leila@example.com", "502-555-0103"),
            (4, "Hamza Ali", "hamza@example.com", "502-555-0104"),
            (5, "Mariam Noor", "mariam@example.com", "502-555-0105"),
        ]
        db.executemany(
            "INSERT OR IGNORE INTO volunteers (id, name, email, phone) VALUES (?, ?, ?, ?)",
            volunteers,
        )

        skills = [
            (1, "setup"), (1, "welcome"),
            (2, "livestream"), (2, "cleanup"),
            (3, "welcome"), (3, "food"),
            (4, "security"), (4, "setup"),
            (5, "food"), (5, "cleanup"),
        ]
        db.executemany("INSERT OR IGNORE INTO volunteer_skills (volunteer_id, skill) VALUES (?, ?)", skills)

        shifts = [
            (1, 1, "Room setup", "17:30", "18:15", 3, "setup"),
            (2, 1, "Welcome table", "18:00", "19:00", 2, "welcome"),
            (3, 1, "Cleanup", "20:00", "20:30", 2, "cleanup"),
            (4, 2, "Food packing", "08:15", "09:30", 4, "food"),
            (5, 2, "Parking and safety", "08:30", "11:00", 2, "security"),
            (6, 3, "Livestream check", "18:45", "19:20", 1, "livestream"),
        ]
        db.executemany(
            "INSERT OR IGNORE INTO shifts (id, event_id, name, start_time, end_time, needed, skill) VALUES (?, ?, ?, ?, ?, ?, ?)",
            shifts,
        )

        assignments = [
            (1, 1, 1),
            (2, 2, 3),
            (3, 4, 5),
            (4, 6, 2),
        ]
        db.executemany(
            "INSERT OR IGNORE INTO shift_assignments (id, shift_id, volunteer_id) VALUES (?, ?, ?)",
            assignments,
        )

        rsvps = [
            (1, 1, "Amina", "amina@example.com", "confirmed"),
            (2, 1, "Bilal", "bilal@example.com", "confirmed"),
            (3, 1, "Omar", "omar@example.com", "interested"),
            (4, 2, "Nadia", "nadia@example.com", "confirmed"),
            (5, 3, "Zayd", "zayd@example.com", "confirmed"),
        ]
        db.executemany(
            "INSERT OR IGNORE INTO rsvps (id, event_id, name, email, status) VALUES (?, ?, ?, ?, ?)",
            rsvps,
        )
