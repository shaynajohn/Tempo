import type { Pattern } from "@/lib/api";

export function PatternCard({ pattern }: { pattern: Pattern }) {
  return (
    <div className="premium-card p-5 transition duration-300 hover:-translate-y-0.5 hover:border-tempo-accent/40">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-tempo-muted">
            {pattern.pattern_type.replaceAll("_", " ")}
          </p>
          <h3 className="mt-2 font-medium">{pattern.title}</h3>
        </div>
        <span className="shrink-0 rounded-full border border-tempo-accent/20 bg-tempo-accent/10 px-2 py-0.5 text-xs text-tempo-accent">
          {Math.round(pattern.confidence * 100)}%
        </span>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-tempo-muted">
        {pattern.description}
      </p>
    </div>
  );
}
