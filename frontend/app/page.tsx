"use client";

import { useEffect, useState } from "react";
import { Users, Armchair, FolderKanban, UserPlus } from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
} from "recharts";
import Topbar from "@/components/Topbar";
import StatCard from "@/components/StatCard";
import Cell from "@/components/ui/Cell";
import { api, DashboardSummary, FloorUtilization } from "@/lib/api";

interface DeptHeadcount { department: string; headcount: number }

const MOSAIC_SIZE = 60;

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [floors, setFloors] = useState<FloorUtilization[]>([]);
  const [depts, setDepts] = useState<DeptHeadcount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setError(null);
        const [s, f, d] = await Promise.all([
          api.get<DashboardSummary>("/api/dashboard/summary"),
          api.get<FloorUtilization[]>("/api/dashboard/utilization-by-floor"),
          api.get<DeptHeadcount[]>("/api/dashboard/headcount-by-department"),
        ]);
        setSummary(s.data);
        setFloors(f.data);
        setDepts(d.data);
      } catch {
        setError("Dashboard data could not be loaded. Please make sure the backend API is running.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <>
      <Topbar title="Dashboard" />
      <div className="p-6 space-y-6">
        {loading ? (
          <p className="text-sm text-ink-muted">Loading...</p>
        ) : error || !summary ? (
          <div className="card p-5 border-occupied/30 bg-occupied/10">
            <p className="text-sm font-medium text-occupied">Unable to load dashboard</p>
            <p className="mt-1 text-sm text-ink-muted">{error ?? "No dashboard data was returned."}</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                label="Active Employees"
                value={summary.active_employees.toLocaleString()}
                sub={`${summary.total_employees.toLocaleString()} total on record`}
                icon={Users}
                accent="brand"
                ratio={summary.active_employees / Math.max(summary.total_employees, 1)}
              />
              <StatCard
                label="Seat Utilization"
                value={`${summary.utilization_percentage}%`}
                sub={`${summary.occupied_seats.toLocaleString()} of ${summary.total_seats.toLocaleString()} seats`}
                icon={Armchair}
                accent="occupied"
                ratio={summary.utilization_percentage / 100}
              />
              <StatCard
                label="Available Seats"
                value={summary.available_seats.toLocaleString()}
                sub="Ready to allocate"
                icon={Armchair}
                accent="available"
                ratio={summary.available_seats / Math.max(summary.total_seats, 1)}
              />
              <StatCard
                label="Pending New Joiners"
                value={summary.pending_new_joiners}
                sub={`${summary.active_projects} active projects`}
                icon={UserPlus}
                accent="danger"
                ratio={summary.pending_new_joiners / Math.max(summary.active_employees, 1)}
              />
            </div>

            <div className="grid lg:grid-cols-2 gap-4">
              <div className="card p-5">
                <div className="flex items-baseline justify-between mb-4">
                  <p className="eyebrow">Utilization by floor</p>
                  <p className="text-[11px] text-ink-muted">each square ≈ {(100 / MOSAIC_SIZE).toFixed(1)}% of seats</p>
                </div>
                <div className="space-y-4">
                  {floors.map((f) => {
                    const filled = Math.round((f.utilization_percentage / 100) * MOSAIC_SIZE);
                    return (
                      <div key={f.floor_id}>
                        <div className="flex items-baseline justify-between mb-1.5">
                          <p className="text-sm font-medium">{f.floor_name}</p>
                          <p className="text-xs font-mono text-ink-muted">
                            {f.occupied_seats}/{f.total_seats} &middot; {f.utilization_percentage}%
                          </p>
                        </div>
                        <div
                          className="grid gap-[3px]"
                          style={{ gridTemplateColumns: `repeat(${MOSAIC_SIZE}, minmax(0, 1fr))` }}
                        >
                          {Array.from({ length: MOSAIC_SIZE }).map((_, i) => (
                            <Cell key={i} variant="mosaic" filled={i < filled} />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="card p-5">
                <p className="eyebrow mb-4">Headcount by department</p>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={depts} layout="vertical" margin={{ left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 12, fill: "#9B9BB0" }} axisLine={false} tickLine={false} />
                    <YAxis
                      type="category"
                      dataKey="department"
                      width={110}
                      tick={{ fontSize: 12, fill: "#9B9BB0" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      cursor={{ fill: "rgba(255,255,255,0.04)" }}
                      contentStyle={{
                        borderRadius: 8,
                        border: "1px solid rgba(102,126,234,0.25)",
                        fontSize: 13,
                        backgroundColor: "rgba(19,19,24,0.95)",
                        color: "#FFFFFF",
                      }}
                    />
                    <Bar dataKey="headcount" radius={[0, 6, 6, 0]} fill="#667eea" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}
