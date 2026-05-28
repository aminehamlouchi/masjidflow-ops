const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8001";

export type EventSummary = {
  id: number;
  title: string;
  event_date: string;
  location: string;
  expected_attendance: number;
  status: string;
  confirmed_rsvps: number;
  volunteer_slots: number;
  filled_slots: number;
  open_slots: number;
};

export type ShiftCoverage = {
  id: number;
  name: string;
  start_time: string;
  end_time: string;
  needed: number;
  skill: string;
  assigned: string[];
  open_slots: number;
};

export type StaffingSuggestion = {
  shift_id: number;
  shift_name: string;
  skill: string;
  open_slots: number;
  suggested_volunteers: string[];
  rationale: string;
};

export async function login(email: string, password: string) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) {
    throw new Error("Login failed");
  }
  return response.json() as Promise<{ token: string; user: { name: string; role: string } }>;
}

export async function apiGet<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${path}`);
  }
  return response.json() as Promise<T>;
}
