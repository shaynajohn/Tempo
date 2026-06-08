"use client";

import { useEffect, useState } from "react";
import {
  getStravaAuthorizeUrl,
  getStravaStatus,
  syncStrava,
  type StravaStatus,
} from "@/lib/api";

export function StravaSyncCard({ onSynced }: { onSynced?: () => void }) {
  const [status, setStatus] = useState<StravaStatus | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadStatus() {
    try {
      setStatus(await getStravaStatus());
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Could not load Strava status.");
    }
  }

  useEffect(() => {
    loadStatus();
  }, []);

  async function handleConnect() {
    setLoading(true);
    setMessage(null);
    try {
      const { auth_url } = await getStravaAuthorizeUrl();
      window.location.href = auth_url;
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Could not start Strava connect.");
      setLoading(false);
    }
  }

  async function handleSync() {
    setLoading(true);
    setMessage(null);
    try {
      const result = await syncStrava();
      setMessage(`Fetched ${result.fetched} activities, imported ${result.imported} new runs.`);
      await loadStatus();
      onSynced?.();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Strava sync failed.");
    } finally {
      setLoading(false);
    }
  }

  const configured = status?.configured ?? false;
  const connected = status?.connected ?? false;

  return (
    <section className="premium-card p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="eyebrow">Automatic Sync</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">Strava</h2>
          <p className="mt-2 max-w-xl text-sm text-tempo-muted">
            Connect Strava once, then Tempo checks for new Garmin-synced runs every{" "}
            {status?.auto_sync_interval_minutes ?? 60} minutes while the backend is running.
            Wellness data still comes from Garmin export for now.
          </p>
          {connected && (
            <p className="mt-3 text-sm text-tempo-accent">
              Connected{status?.athlete_name ? ` as ${status.athlete_name}` : ""}.
              {status?.last_synced_at
                ? ` Last synced ${new Date(status.last_synced_at).toLocaleString()}.`
                : " Not synced yet."}
            </p>
          )}
          {!configured && (
            <p className="mt-3 rounded-xl border border-tempo-warn/30 bg-tempo-warn/10 px-3 py-2 text-sm text-tempo-warn">
              Add STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET to backend/.env to enable this.
            </p>
          )}
          {message && <p className="mt-3 text-sm text-tempo-muted">{message}</p>}
        </div>

        <button
          onClick={connected ? handleSync : handleConnect}
          disabled={loading || !configured}
          className="rounded-xl bg-tempo-accent px-5 py-3 text-sm font-semibold text-tempo-bg shadow-lg shadow-tempo-accent/20 transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Working..." : connected ? "Sync now" : "Connect Strava"}
        </button>
      </div>
    </section>
  );
}
