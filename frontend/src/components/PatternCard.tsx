import type { Pattern } from "@/lib/api";

export function PatternCard({ pattern }: { pattern: Pattern }) {
  return (
    <div className="rounded-xl border border-tempo-border bg-tempo-surface p-5">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium">{pattern.title}</h3>
        <span className="shrink-0 rounded-full bg-tempo-accent/10 px-2 py-0.5 text-xs text-tempo-accent">
          {Math.round(pattern.confidence * 100)}%
        </span>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-tempo-muted">
        {pattern.description}
      </p>
    </div>
  );
}
