import Link from "next/link";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/import", label: "Import" },
  { href: "/activities", label: "Activities" },
  { href: "/performance", label: "Performance" },
  { href: "/search", label: "Search" },
];

export function Nav() {
  return (
    <nav className="sticky top-0 z-50 border-b border-white/10 bg-tempo-bg/65 backdrop-blur-2xl">
      <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <Link href="/" className="group flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-tempo-accent/30 bg-tempo-accent/10 text-sm font-bold text-tempo-accent shadow-lg shadow-tempo-accent/10 transition group-hover:scale-105">
              T
            </span>
            <span className="text-xl font-semibold tracking-tight">
              Tempo<span className="text-tempo-accent">.</span>
            </span>
          </Link>
          <div className="hidden items-center gap-1 rounded-full border border-white/10 bg-white/[0.04] p-1 shadow-2xl shadow-black/20 md:flex">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="rounded-full px-4 py-2 text-sm text-tempo-muted transition hover:bg-white/[0.07] hover:text-white"
              >
                {l.label}
              </Link>
            ))}
          </div>
          <div className="flex items-center gap-2 rounded-full border border-tempo-accent/20 bg-tempo-accent/10 px-3 py-1.5 text-xs text-tempo-accent">
            <span className="h-2 w-2 rounded-full bg-tempo-accent shadow-[0_0_16px_rgba(61,214,198,0.9)]" />
            Local
          </div>
        </div>
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1 md:hidden">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="shrink-0 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-tempo-muted"
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
