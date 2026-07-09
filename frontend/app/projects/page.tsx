"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import Topbar from "@/components/Topbar";
import EntityBadge from "@/components/ui/EntityBadge";
import { api, Project, Paginated } from "@/lib/api";

export default function ProjectsPage() {
  const [data, setData] = useState<Paginated<Project> | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    (async () => {
      const { data } = await api.get<Paginated<Project>>("/api/projects", {
        params: { page, page_size: pageSize, search: search || undefined, status: status || undefined },
      });
      setData(data);
    })();
  }, [page, search, status]);

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  return (
    <>
      <Topbar title="Projects" />
      <div className="p-6 space-y-4">
        <div className="flex flex-wrap gap-3 items-center">
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search by project name or client…"
            className="flex-1 min-w-[240px] px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand placeholder:text-ink-muted"
          />
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand"
          >
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="on_hold">On hold</option>
          </select>
          {data && <span className="text-xs text-ink-muted font-mono">{data.total} results</span>}
        </div>

        <div className="grid md:grid-cols-2 gap-3">
          {data?.items.map((p) => (
            <div key={p.id} className="card p-4 border-l-[3px] border-l-brand">
              <div className="flex items-start justify-between">
                <div>
                  <p className="eyebrow">{p.project_code}</p>
                  <p className="font-medium mt-1">{p.name}</p>
                  <p className="text-xs text-ink-muted mt-0.5">{p.client_name}</p>
                </div>
                <EntityBadge kind="project-status" value={p.status} />
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between">
          <p className="text-xs text-ink-muted">Page {page} of {totalPages || 1}</p>
          <div className="flex gap-2">
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="p-2 rounded-lg border border-white/10 disabled:opacity-40 hover:bg-white/[0.06]">
              <ChevronLeft size={16} />
            </button>
            <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)} className="p-2 rounded-lg border border-white/10 disabled:opacity-40 hover:bg-white/[0.06]">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
