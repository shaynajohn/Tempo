"use client";

import { useEffect, useState } from "react";
import {
  getGarminConnectStatus,
  syncGarminConnect,
  type GarminConnectStatus,
} from "@/lib/api";

export function GarminConnectSyncCard({ onSynced }: { onSynced?: () => void }) {
  const [status, setStatus] = useState<GarminConnectStatus | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadStatus() {
    try {
      setStatus(await getGarminConnectStatus());
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Could not load Garmin Connect status.");
    }
  }

  useEffect(() => {
    loadStatus();
  }, []);

  async function handleSync() {
    setLoading(true);
    setMessage(null);
    try {
      const result = await syncGarminConnect();
      setMessage(
        `Fetched ${result.fetched} Garmin activities, found ${result.runs_found} runs, imported ${result.imported} new runs.`
      );
      await loadStatus();
      onSynced?.();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Garmin Connect sync failed.");
    } finally {
      setLoading(false);
    }
  }

  const configured = status?.configured ?? false;

  return (
    <section className="premium-card p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="eyebrow">Automatic Sync</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">Garmin Connect</h2>
          <p className="mt-2 max-w-xl text-sm text-tempo-muted">
            Tempo can log into Garmin Connect from your local backend and pull recent runs
            every {status?.auto_sync_interval_minutes ?? 60} minutes while the backend is
            running. This uses an unofficial Garmin client, so manual export stays as backup.
          </p>
          {configured ? (
            <p className="mt-3 text-sm text-tempo-accent">
              Credentials configured.
              {status?.last_synced_at
                ? ` Last synced ${new Date(status.last_synced_at).toLocaleString()}.`
                : " Not synced yet."}
            </p>
          ) : (
            <p className="mt-3 rounded-xl border border-tempo-warn/30 bg-tempo-warn/10 px-3 py-2 text-sm text-tempo-warn">
              Add GARMIN_EMAIL and GARMIN_PASSWORD to backend/.env, then restart the backend.
            </p>
          )}
          {message && <p className="mt-3 text-sm text-tempo-muted">{message}</p>}
        </div>

        <button
          onClick={handleSync}
          disabled={loading || !configured}
          className="rounded-xl bg-tempo-accent px-5 py-3 text-sm font-semibold text-tempo-bg shadow-lg shadow-tempo-accent/20 transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Syncing..." : "Sync Garmin"}
        </button>
      </div>
    </section>
  );
}
