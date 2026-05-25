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
    <nav className="border-b border-tempo-border bg-tempo-surface/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link href="/" className="text-xl font-semibold tracking-tight">
          Tempo<span className="text-tempo-accent">.</span>
        </Link>
        <div className="flex gap-6">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm text-tempo-muted transition hover:text-white"
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
