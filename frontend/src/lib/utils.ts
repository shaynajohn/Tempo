export function cn(...classes: (string | false | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

export function riskColor(level: string): string {
  switch (level) {
    case "low":
      return "text-tempo-accent";
    case "moderate":
      return "text-tempo-warn";
    case "high":
      return "text-tempo-danger";
    default:
      return "text-tempo-muted";
  }
}
