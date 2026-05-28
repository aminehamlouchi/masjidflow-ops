import { CalendarDays, ClipboardCheck, LogIn, Sparkles, UsersRound } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { EventSummary, ShiftCoverage, StaffingSuggestion, apiGet, apiPost, login } from "./api";

export default function App() {
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("admin@masjidflow.local");
  const [password, setPassword] = useState("demo-admin");
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [coverage, setCoverage] = useState<ShiftCoverage[]>([]);
  const [suggestions, setSuggestions] = useState<StaffingSuggestion[]>([]);
  const [error, setError] = useState("");

  const selectedEvent = useMemo(
    () => events.find((event) => event.id === selectedEventId) ?? events[0],
    [events, selectedEventId]
  );

  async function handleLogin(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await login(email, password);
      setToken(result.token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  useEffect(() => {
    if (!token) return;
    apiGet<EventSummary[]>("/events", token)
      .then((data) => {
        setEvents(data);
        setSelectedEventId(data[0]?.id ?? null);
      })
      .catch((err) => setError(err.message));
  }, [token]);

  useEffect(() => {
    if (!token || !selectedEvent) return;
    apiGet<ShiftCoverage[]>(`/events/${selectedEvent.id}/coverage`, token)
      .then(setCoverage)
      .catch((err) => setError(err.message));
    setSuggestions([]);
  }, [token, selectedEvent]);

  async function loadSuggestions() {
    if (!selectedEvent || !token) return;
    const data = await apiPost<StaffingSuggestion[]>(`/events/${selectedEvent.id}/suggestions`, token);
    setSuggestions(data);
  }

  if (!token) {
    return (
      <main className="auth-shell">
        <section className="login-panel" aria-label="Login">
          <div>
            <p className="eyebrow">MasjidFlow Ops</p>
            <h1>Event coverage without spreadsheet drift.</h1>
            <p className="lead">Track events, RSVPs, volunteer shifts, and staffing gaps from one organizer dashboard.</p>
          </div>
          <form onSubmit={handleLogin} className="login-form">
            <label>
              Email
              <input value={email} onChange={(event) => setEmail(event.target.value)} />
            </label>
            <label>
              Password
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </label>
            {error && <p className="error">{error}</p>}
            <button type="submit">
              <LogIn size={18} aria-hidden="true" />
              Sign in
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">MasjidFlow Ops</p>
          <h1>Operations Dashboard</h1>
        </div>
        <button className="secondary" onClick={() => setToken("")}>
          Sign out
        </button>
      </header>

      <section className="metric-grid" aria-label="Portfolio metrics">
        <Metric icon={<CalendarDays />} label="Events" value={events.length} />
        <Metric icon={<UsersRound />} label="Expected guests" value={events.reduce((sum, event) => sum + event.expected_attendance, 0)} />
        <Metric icon={<ClipboardCheck />} label="Open slots" value={events.reduce((sum, event) => sum + event.open_slots, 0)} />
      </section>

      <div className="workspace">
        <aside className="event-list" aria-label="Events">
          {events.map((event) => (
            <button
              className={event.id === selectedEvent?.id ? "event-row active" : "event-row"}
              key={event.id}
              onClick={() => setSelectedEventId(event.id)}
            >
              <span>{event.title}</span>
              <small>{event.open_slots} open slots</small>
            </button>
          ))}
        </aside>

        {selectedEvent && (
          <section className="detail-panel" aria-label="Selected event">
            <div className="detail-header">
              <div>
                <p className="eyebrow">{selectedEvent.status}</p>
                <h2>{selectedEvent.title}</h2>
                <p>{new Date(selectedEvent.event_date).toLocaleString()} at {selectedEvent.location}</p>
              </div>
              <button onClick={loadSuggestions} title="Generate staffing suggestions">
                <Sparkles size={18} aria-hidden="true" />
                Suggest coverage
              </button>
            </div>

            <div className="coverage-table" role="table" aria-label="Shift coverage">
              <div className="table-head" role="row">
                <span>Shift</span>
                <span>Skill</span>
                <span>Assigned</span>
                <span>Open</span>
              </div>
              {coverage.map((shift) => (
                <div className="table-row" role="row" key={shift.id}>
                  <span>
                    <strong>{shift.name}</strong>
                    <small>{shift.start_time}-{shift.end_time}</small>
                  </span>
                  <span>{shift.skill}</span>
                  <span>{shift.assigned.length ? shift.assigned.join(", ") : "Unassigned"}</span>
                  <span className={shift.open_slots > 0 ? "open" : "filled"}>{shift.open_slots}</span>
                </div>
              ))}
            </div>

            {suggestions.length > 0 && (
              <section className="suggestions" aria-label="Staffing suggestions">
                <h3>Staffing Suggestions</h3>
                {suggestions.map((suggestion) => (
                  <article key={suggestion.shift_id}>
                    <strong>{suggestion.shift_name}</strong>
                    <p>{suggestion.rationale}</p>
                    <small>{suggestion.suggested_volunteers.length ? suggestion.suggested_volunteers.join(", ") : "No matching volunteer found yet"}</small>
                  </article>
                ))}
              </section>
            )}
          </section>
        )}
      </div>
    </main>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <article className="metric">
      <span>{icon}</span>
      <div>
        <strong>{value}</strong>
        <small>{label}</small>
      </div>
    </article>
  );
}
