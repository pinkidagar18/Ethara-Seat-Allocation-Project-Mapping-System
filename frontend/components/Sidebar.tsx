"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutGrid, Users, FolderKanban, Armchair, UserPlus, Sparkles,
} from "lucide-react";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutGrid },
  { href: "/employees", label: "Employees", icon: Users },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/seats", label: "Seat Map", icon: Armchair },
  { href: "/new-joiners", label: "New Joiners", icon: UserPlus },
  { href: "/assistant", label: "Ask Ethara", icon: Sparkles },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex md:flex-col w-60 shrink-0 border-r border-white/[0.06] bg-surface/70 backdrop-blur-xl h-screen sticky top-0">
      <div className="px-5 py-5">
        <Link href="/" className="inline-flex items-center rounded-md bg-white px-3 py-2 shadow-soft">
          <img src="/ethara-ai-logo.png" alt="Ethara.AI" className="h-14 w-auto object-contain" />
        </Link>
        <p className="eyebrow mt-3">Seating &amp; Projects</p>
      </div>

      <nav className="flex-1 px-3 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`group flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors relative ${
                active
                  ? "bg-brand-light text-brand font-medium"
                  : "text-ink-muted hover:bg-white/[0.06] hover:text-ink"
              }`}
            >
              {active && (
                <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full brand-gradient" />
              )}
              <Icon size={17} strokeWidth={2} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-5 py-4 border-t border-border grid-paper">
        <p className="text-[11px] text-ink-muted leading-relaxed">
          ~5,000 employees<br />Main Campus &middot; 5 floors
        </p>
      </div>
    </aside>
  );
}
