"use client";

import { useState } from "react";
import {
  searchWorkouts,
  indexWorkouts,
  formatPace,
  formatDistance,
  type SearchResult,
} from "@/lib/api";

const SUGGESTIONS = [
  "Find runs similar to my best tempo runs",
  "What workouts preceded my PR?",
  "Runs with pace fade in the second half",
  "Cool weather long runs",
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [indexed, setIndexed] = useState<number | null>(null);

  async function handleSearch(q?: string) {
    const text = q ?? query;
    if (!text.trim()) return;
    setLoading(true);
    try {
      if (indexed === null) {
        const r = await indexWorkouts();
        setIndexed(r.indexed);
      }
      const hits = await searchWorkouts(text);
      setResults(hits);
    } catch (e) {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold">Semantic search</h1>
        <p className="mt-1 text-tempo-muted">
          RAG over workout summaries — find similar runs in natural language.
        </p>
      </header>

      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Find runs similar to my best tempo runs…"
          className="flex-1 rounded-xl border border-tempo-border bg-tempo-surface px-4 py-3 text-sm outline-none focus:border-tempo-accent"
        />
        <button
          onClick={() => handleSearch()}
          disabled={loading}
          className="rounded-xl bg-tempo-accent px-5 py-3 text-sm font-medium text-tempo-bg hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "…" : "Search"}
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => {
              setQuery(s);
              handleSearch(s);
            }}
            className="rounded-full border border-tempo-border px-3 py-1 text-xs text-tempo-muted hover:border-tempo-accent hover:text-white"
          >
            {s}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {results.map((r) => (
          <article
            key={r.activity_id}
            className="rounded-xl border border-tempo-border bg-tempo-surface p-5"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-medium">{r.name || "Run"}</h3>
                <p className="mt-1 text-xs text-tempo-muted">
                  {new Date(r.started_at).toLocaleDateString()} ·{" "}
                  {formatDistance(r.distance_m)} · {formatPace(r.avg_pace_s_per_km)}
                </p>
                <p className="mt-2 text-sm text-tempo-muted">{r.content}</p>
              </div>
              <span className="shrink-0 rounded-full bg-tempo-accent/10 px-2 py-0.5 text-xs text-tempo-accent">
                {(r.similarity * 100).toFixed(0)}% match
              </span>
            </div>
          </article>
        ))}
        {results.length === 0 && !loading && query && (
          <p className="text-center text-sm text-tempo-muted">
            No results. Import data and ensure OPENAI_API_KEY is set.
          </p>
        )}
      </div>
    </div>
  );
}
