// Browser: default to same-origin proxy (next.config.js → port 8001).
// Set NEXT_PUBLIC_API_URL to call the backend directly.
const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (typeof window !== "undefined" ? "" : "http://127.0.0.1:8001");

const METERS_PER_MILE = 1609.344;
const KM_TO_MILES = 0.621371;

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...options?.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export interface DashboardStats {
  total_activities: number;
  total_distance_km: number;
  avg_weekly_km: number;
  recent_fatigue_score: number | null;
  recent_insights: number;
}

export interface LibraryStatus {
  activity_count: number;
  wellness_count: number;
  first_activity_date: string | null;
  latest_activity_date: string | null;
  first_wellness_date: string | null;
  latest_wellness_date: string | null;
  latest_data_date: string | null;
  days_since_latest: number | null;
  freshness: "empty" | "fresh" | "aging" | "stale";
  needs_import: boolean;
  summary: string;
}

export interface Split {
  distance_m?: number;
  duration_s?: number;
  avg_hr?: number;
  avg_cadence?: number;
  avg_pace_s_per_km?: number;
}

export interface Activity {
  id: number;
  name: string | null;
  started_at: string;
  distance_m: number | null;
  duration_s?: number | null;
  avg_pace_s_per_km: number | null;
  avg_hr: number | null;
  max_hr?: number | null;
  avg_cadence: number | null;
  training_load: number | null;
  temperature_c: number | null;
  elevation_gain_m?: number | null;
  vo2_max?: number | null;
  summary_text: string | null;
  splits?: Split[] | null;
}

export interface TrendsData {
  weekly_volume: { week: string; km: number }[];
  pace_trend: { date: string; pace: number; name: string; id: number }[];
  wellness: {
    date: string;
    resting_hr?: number | null;
    sleep_hours?: number | null;
    hrv?: number | null;
    stress?: number | null;
  }[];
}

export interface CoachingReportData {
  fatigue_summary?: string;
  patterns?: { title: string; description: string; confidence: number }[];
  final_report?: string;
  forecast?: string;
}

export interface PerformanceActivity {
  id: number;
  name: string;
  started_at: string;
  distance_m: number | null;
  duration_s: number | null;
  pace_s_per_km: number;
}

export interface PerformanceMark {
  distance_key: string;
  distance_label: string;
  seconds: number;
  formatted_time: string;
  pace_s_per_km: number;
  method: string;
  activity?: PerformanceActivity;
  source_activity?: PerformanceActivity;
}

export interface PerformanceData {
  personal_bests: PerformanceMark[];
  race_projections: PerformanceMark[];
  fastest_run: PerformanceActivity | null;
  longest_run: PerformanceActivity | null;
  projection_source: PerformanceActivity | null;
  summary: string;
}

export interface ReadinessFactor {
  label: string;
  impact: "positive" | "negative" | "neutral";
  detail: string;
}

export interface ReadinessData {
  score: number;
  level: "high" | "moderate" | "low" | "unknown";
  recommendation: string;
  factors: ReadinessFactor[];
  latest_metric_date: string | null;
  metrics: {
    resting_hr?: number | null;
    sleep_hours?: number | null;
    sleep_score?: number | null;
    stress_avg?: number | null;
    body_battery?: number | null;
  };
  training: {
    last_7_days_km?: number;
    baseline_weekly_km?: number;
    days_since_run?: number | null;
  };
}

export interface FatiguePoint {
  date: string;
  score: number;
  risk_level: string;
  factors: string[];
}

export interface FatigueData {
  current_score: number;
  risk_level: string;
  trend: FatiguePoint[];
  recommendation: string;
}

export interface Pattern {
  pattern_type: string;
  title: string;
  description: string;
  evidence: Record<string, unknown>;
  confidence: number;
}

export interface Insight {
  id: number;
  insight_type: string;
  title: string;
  body: string;
  confidence: number | null;
  activity_id: number | null;
  created_at: string;
}

export interface SearchResult {
  activity_id: number;
  name: string | null;
  started_at: string;
  distance_m: number | null;
  avg_pace_s_per_km: number | null;
  content: string;
  similarity: number;
}

export function getDashboard() {
  return fetchApi<DashboardStats>("/api/v1/analytics/dashboard");
}

export function getLibraryStatus() {
  return fetchApi<LibraryStatus>("/api/v1/analytics/library");
}

export function getActivities(limit = 50) {
  return fetchApi<{ items: Activity[]; total: number }>(
    `/api/v1/activities?limit=${limit}`
  );
}

export function getActivity(id: number) {
  return fetchApi<Activity>(`/api/v1/activities/${id}`);
}

export function getTrends() {
  return fetchApi<TrendsData>("/api/v1/analytics/trends");
}

export function getCoachingReport(activityId?: number) {
  const q = activityId ? `?activity_id=${activityId}` : "";
  return fetchApi<CoachingReportData>(`/api/v1/analytics/coaching-report${q}`);
}

export function getPerformance() {
  return fetchApi<PerformanceData>("/api/v1/analytics/performance");
}

export function getReadiness() {
  return fetchApi<ReadinessData>("/api/v1/analytics/readiness");
}

export function getFatigue() {
  return fetchApi<FatigueData>("/api/v1/analytics/fatigue");
}

export function getPatterns() {
  return fetchApi<Pattern[]>("/api/v1/analytics/patterns");
}

export function getInsights() {
  return fetchApi<Insight[]>("/api/v1/insights");
}

export function explainRun(activityId: number) {
  return fetchApi<Insight>(`/api/v1/insights/explain/${activityId}`, {
    method: "POST",
  });
}

export function searchWorkouts(query: string) {
  return fetchApi<SearchResult[]>("/api/v1/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit: 10 }),
  });
}

export function indexWorkouts() {
  return fetchApi<{ indexed: number }>("/api/v1/search/index", {
    method: "POST",
  });
}

export async function importGarminExport(exportPath: string) {
  return fetchApi<{
    activities_imported: number;
    daily_metrics_imported: number;
    errors: string[];
  }>("/api/v1/ingest/garmin-export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ export_path: exportPath }),
  });
}

export async function uploadFile(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/api/v1/ingest/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function formatPace(secPerKm: number | null): string {
  if (!secPerKm) return "—";
  const secPerMile = secPerKm / KM_TO_MILES;
  const m = Math.floor(secPerMile / 60);
  const s = Math.round(secPerMile % 60);
  return `${m}:${s.toString().padStart(2, "0")}/mi`;
}

export function formatDistance(m: number | null): string {
  if (!m) return "—";
  return `${(m / METERS_PER_MILE).toFixed(1)} mi`;
}

export function formatKmAsMiles(km: number | null | undefined): string {
  if (km == null) return "—";
  return `${(km * KM_TO_MILES).toFixed(1)} mi`;
}

export function kmToMiles(km: number): number {
  return km * KM_TO_MILES;
}

export function secPerKmToMinPerMile(secPerKm: number): number {
  return secPerKm / KM_TO_MILES / 60;
}
