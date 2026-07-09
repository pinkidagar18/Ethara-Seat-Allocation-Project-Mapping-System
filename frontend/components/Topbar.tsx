"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, X } from "lucide-react";
import { api } from "@/lib/api";

interface SearchResults {
  employees: { id: number; full_name: string; employee_code: string }[];
  seats: { id: number; seat_code: string }[];
  projects: { id: number; name: string; project_code: string }[];
}

export default function Topbar({ title }: { title: string }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResults | null>(null);
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults(null);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const { data } = await api.get<SearchResults>("/api/search", { params: { q: query } });
        setResults(data);
        setOpen(true);
      } catch {
        setResults(null);
      }
    }, 250);
    return () => clearTimeout(t);
  }, [query]);

  const hasResults =
    results && (results.employees.length || results.seats.length || results.projects.length);

  return (
    <header className="sticky top-0 z-20 bg-bg/70 backdrop-blur-xl border-b border-white/[0.06]">
      <div className="flex items-center justify-between gap-6 px-6 py-4">
        <h1 className="font-display text-xl font-semibold tracking-tight">{title}</h1>

        <div ref={boxRef} className="relative w-full max-w-sm">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => query.length >= 2 && setOpen(true)}
              placeholder="Search people, seats, projects…"
              className="w-full pl-9 pr-8 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand transition-colors placeholder:text-ink-muted"
            />
            {query && (
              <button
                onClick={() => { setQuery(""); setResults(null); }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {open && hasResults && (
            <div className="absolute mt-2 w-full card p-2 max-h-96 overflow-auto">
              {results!.employees.length > 0 && (
                <div className="mb-2">
                  <p className="eyebrow px-2 py-1">People</p>
                  {results!.employees.map((e) => (
                    <button
                      key={e.id}
                      onClick={() => { router.push(`/employees/${e.id}`); setOpen(false); setQuery(""); }}
                      className="w-full text-left px-2 py-1.5 rounded-md hover:bg-white/[0.06] text-sm flex justify-between"
                    >
                      <span>{e.full_name}</span>
                      <span className="font-mono text-xs text-ink-muted">{e.employee_code}</span>
                    </button>
                  ))}
                </div>
              )}
              {results!.seats.length > 0 && (
                <div className="mb-2">
                  <p className="eyebrow px-2 py-1">Seats</p>
                  {results!.seats.map((s) => (
                    <div key={s.id} className="px-2 py-1.5 text-sm font-mono">{s.seat_code}</div>
                  ))}
                </div>
              )}
              {results!.projects.length > 0 && (
                <div>
                  <p className="eyebrow px-2 py-1">Projects</p>
                  {results!.projects.map((p) => (
                    <div key={p.id} className="px-2 py-1.5 text-sm flex justify-between">
                      <span>{p.name}</span>
                      <span className="font-mono text-xs text-ink-muted">{p.project_code}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
