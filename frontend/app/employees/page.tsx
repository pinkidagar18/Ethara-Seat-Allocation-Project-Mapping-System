"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import Topbar from "@/components/Topbar";
import EntityBadge from "@/components/ui/EntityBadge";
import { api, Employee, Paginated } from "@/lib/api";

function initials(name: string) {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] || "") + (parts[parts.length - 1]?.[0] || "")).toUpperCase();
}

// deterministic tint from the name so avatars aren't all the same color,
// without needing per-employee data we don't have
const TINTS = ["bg-brand/10 text-brand", "bg-available/10 text-available", "bg-occupied/10 text-occupied"];
function tintFor(name: string) {
  const sum = [...name].reduce((a, c) => a + c.charCodeAt(0), 0);
  return TINTS[sum % TINTS.length];
}

export default function EmployeesPage() {
  const [data, setData] = useState<Paginated<Employee> | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    (async () => {
      const { data } = await api.get<Paginated<Employee>>("/api/employees", {
        params: {
          page,
          page_size: pageSize,
          search: search || undefined,
          employment_status: status || undefined,
        },
      });
      setData(data);
    })();
  }, [page, search, status]);

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  return (
    <>
      <Topbar title="Employees" />
      <div className="p-6 space-y-4">
        <div className="flex flex-wrap gap-3 items-center">
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search by name, email, or employee code…"
            className="flex-1 min-w-[240px] px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand placeholder:text-ink-muted"
          />
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand"
          >
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="exited">Exited</option>
          </select>
          {data && (
            <span className="text-xs text-ink-muted font-mono">{data.total.toLocaleString()} results</span>
          )}
        </div>

        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-ink-muted text-xs uppercase tracking-wide">
                <th className="px-4 py-3 font-medium">Employee</th>
                <th className="px-4 py-3 font-medium">Code</th>
                <th className="px-4 py-3 font-medium">Department</th>
                <th className="px-4 py-3 font-medium">Designation</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((e) => (
                <tr key={e.id} className="border-b border-white/[0.06] last:border-0 hover:bg-white/[0.04] transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 shrink-0 rounded-full grid place-items-center text-[11px] font-semibold ${tintFor(e.full_name)}`}>
                        {initials(e.full_name)}
                      </div>
                      <div>
                        <Link href={`/employees/${e.id}`} className="font-medium hover:text-brand">
                          {e.full_name}
                        </Link>
                        <p className="text-xs text-ink-muted">{e.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-ink-muted">{e.employee_code}</td>
                  <td className="px-4 py-3">{e.department?.name || "—"}</td>
                  <td className="px-4 py-3 text-ink-muted">{e.designation || "—"}</td>
                  <td className="px-4 py-3">
                    <EntityBadge kind="employee-status" value={e.employment_status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between">
          <p className="text-xs text-ink-muted">
            Page {page} of {totalPages || 1}
          </p>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="p-2 rounded-lg border border-white/10 disabled:opacity-40 hover:bg-white/[0.06]"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="p-2 rounded-lg border border-white/10 disabled:opacity-40 hover:bg-white/[0.06]"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
