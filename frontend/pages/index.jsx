import { useEffect, useMemo, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

const counties = ["", "broward", "miami-dade"];
const categories = ["", "shelter", "medical", "food-water", "utilities", "transportation"];
const urgencies = ["", "high", "medium", "low"];

function Filters({ county, category, urgency, onChange }) {
  return (
    <div className="filters">
      <select value={county} onChange={(e) => onChange({ county: e.target.value })}>
        {counties.map((c) => (
          <option key={c || "all"} value={c}>
            {c ? c : "All counties"}
          </option>
        ))}
      </select>
      <select value={category} onChange={(e) => onChange({ category: e.target.value })}>
        {categories.map((c) => (
          <option key={c || "allcat"} value={c}>
            {c ? c : "All categories"}
          </option>
        ))}
      </select>
      <select value={urgency} onChange={(e) => onChange({ urgency: e.target.value })}>
        {urgencies.map((u) => (
          <option key={u || "allurg"} value={u}>
            {u ? u : "All urgency"}
          </option>
        ))}
      </select>
    </div>
  );
}

function Card({ card }) {
  const published = card.published_at ? new Date(card.published_at).toLocaleString() : "";
  const urgencyClass = card.urgency ? `urgent-${card.urgency}` : "";
  const location = [card.city, card.county].filter(Boolean).join(", ");
  return (
    <div className="card">
      <div className="meta">
        <span className={`badge ${urgencyClass}`}>{card.urgency || ""}</span>
        <span className="badge">{card.category}</span>
        {card.action_type ? <span className="badge">{card.action_type}</span> : null}
      </div>
      <div className="summary">
        <strong>{card.title}</strong>
      </div>
      <div className="summary">{card.summary}</div>
      <div className="source">
        {location && <span>{location} • </span>}
        <span>{published}</span>
      </div>
      <div className="source">
        Source: <a href={card.source_url} target="_blank" rel="noreferrer">{card.source}</a>
      </div>
    </div>
  );
}

export default function Home() {
  const [mode, setMode] = useState("action");
  const [filters, setFilters] = useState({ county: "", category: "", urgency: "" });
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const query = useMemo(() => {
    const params = new URLSearchParams({ mode });
    if (filters.county) params.append("county", filters.county);
    if (filters.category) params.append("category", filters.category);
    if (filters.urgency) params.append("urgency", filters.urgency);
    params.append("limit", "30");
    return params.toString();
  }, [mode, filters]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const res = await fetch(`${API_BASE}/cards?${query}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) setCards(data);
      } catch (err) {
        if (!cancelled) setError(err.message || "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [query]);

  const onFilterChange = (partial) => setFilters((prev) => ({ ...prev, ...partial }));

  return (
    <div className="container">
      <div className="header">
        <h2>Hurricane Impact Triage</h2>
        <div className="tabs">
          {[
            { key: "action", label: "Action" },
            { key: "info", label: "Information" },
          ].map((t) => (
            <button
              key={t.key}
              className={`tab ${mode === t.key ? "active" : ""}`}
              onClick={() => setMode(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <Filters county={filters.county} category={filters.category} urgency={filters.urgency} onChange={onFilterChange} />

      {loading && <div>Loading...</div>}
      {error && <div style={{ color: "salmon" }}>Error: {error}</div>}

      <div className="cards">
        {cards.map((c) => (
          <Card key={c.id} card={c} />
        ))}
      </div>

      {!loading && cards.length === 0 && <div>No cards found for this mode/filters.</div>}
    </div>
  );
}
