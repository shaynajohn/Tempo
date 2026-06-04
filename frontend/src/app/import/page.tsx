"use client";

import { useEffect, useState } from "react";
import {
  getLibraryStatus,
  uploadFile,
  importGarminExport,
  type LibraryStatus,
} from "@/lib/api";
import { DataLibraryCard } from "@/components/DataLibraryCard";

const DEFAULT_EXPORT_PATH =
  "/Users/shayna/Downloads/5d4f6607-507c-47de-b6f4-6218de6fcc99_1/DI_CONNECT";

export default function ImportPage() {
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exportPath, setExportPath] = useState(DEFAULT_EXPORT_PATH);
  const [libraryStatus, setLibraryStatus] = useState<LibraryStatus | null>(null);

  async function refreshLibraryStatus() {
    try {
      setLibraryStatus(await getLibraryStatus());
    } catch {
      // The main dashboard already shows API connection errors. Keep import simple.
    }
  }

  useEffect(() => {
    refreshLibraryStatus();
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setStatus(null);
    try {
      const result = await uploadFile(file);
      setStatus(
        `Imported ${result.activities_imported} activities, ${result.daily_metrics_imported} daily metrics.`
      );
      if (result.errors?.length) {
        setStatus((s) => `${s} ${result.errors.join(" ")}`);
      }
      refreshLibraryStatus();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleFullExport() {
    setLoading(true);
    setStatus(null);
    try {
      const result = await importGarminExport(exportPath);
      setStatus(
        `Imported ${result.activities_imported} runs and ${result.daily_metrics_imported} wellness days (with sleep + stress).`
      );
      if (result.errors?.length) {
        setStatus((s) => `${s} Notes: ${result.errors.join(" ")}`);
      }
      refreshLibraryStatus();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Import failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <header>
        <h1 className="text-3xl font-semibold">Import Garmin data</h1>
        <p className="mt-2 text-sm text-tempo-muted">
          Use your full export folder for activities, sleep, and stress — or upload a single JSON file.
        </p>
      </header>

      {libraryStatus && <DataLibraryCard status={libraryStatus} />}

      <section className="rounded-xl border border-tempo-accent/30 bg-tempo-accent/5 p-5">
        <h2 className="font-medium text-tempo-accent">Full Garmin export (recommended)</h2>
        <p className="mt-1 text-xs text-tempo-muted">
          Imports runs from summarizedActivities + wellness from UDS & sleep files.
        </p>
        <label className="mt-3 block text-xs text-tempo-muted">Path to DI_CONNECT folder</label>
        <input
          type="text"
          value={exportPath}
          onChange={(e) => setExportPath(e.target.value)}
          className="mt-1 w-full rounded-lg border border-tempo-border bg-tempo-bg px-3 py-2 text-xs"
        />
        <button
          onClick={handleFullExport}
          disabled={loading}
          className="mt-3 w-full rounded-lg bg-tempo-accent py-2.5 text-sm font-medium text-tempo-bg hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Importing…" : "Import full export"}
        </button>
      </section>

      <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-tempo-border bg-tempo-surface p-10 transition hover:border-tempo-accent/50">
        <span className="text-3xl">📁</span>
        <span className="mt-3 font-medium">
          {loading ? "Working…" : "Or upload a single file"}
        </span>
        <span className="mt-1 text-xs text-tempo-muted">.json, .csv</span>
        <input
          type="file"
          accept=".json,.csv"
          className="hidden"
          disabled={loading}
          onChange={handleUpload}
        />
      </label>

      {status && (
        <p
          className={`rounded-lg p-4 text-sm ${
            status.toLowerCase().includes("fail") || status.includes("Error")
              ? "bg-tempo-danger/10 text-tempo-danger"
              : "bg-tempo-accent/10 text-tempo-accent"
          }`}
        >
          {status}
        </p>
      )}
    </div>
  );
}
