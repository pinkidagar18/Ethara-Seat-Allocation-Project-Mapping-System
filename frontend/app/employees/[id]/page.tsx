"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Armchair, MapPin, Briefcase } from "lucide-react";
import Topbar from "@/components/Topbar";
import EntityBadge from "@/components/ui/EntityBadge";
import { api, Employee, Seat, ProjectAssignment } from "@/lib/api";

interface EmployeeDetail extends Employee {
  current_seat?: Seat;
  active_projects: ProjectAssignment[];
}

export default function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [emp, setEmp] = useState<EmployeeDetail | null>(null);
  const [releasing, setReleasing] = useState(false);

  const load = async () => {
    const { data } = await api.get<EmployeeDetail>(`/api/employees/${id}`);
    setEmp(data);
  };

  useEffect(() => { load(); }, [id]);

  const handleRelease = async () => {
    if (!emp?.current_seat) return;
    setReleasing(true);
    try {
      await api.post(`/api/seats/${emp.current_seat.id}/release`, { notes: "Released via employee profile" });
      await load();
    } finally {
      setReleasing(false);
    }
  };

  if (!emp) {
    return (
      <>
        <Topbar title="Employee" />
        <div className="p-6 text-sm text-ink-muted">Loading…</div>
      </>
    );
  }

  return (
    <>
      <Topbar title={emp.full_name} />
      <div className="p-6 space-y-6 max-w-4xl">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-sm text-ink-muted hover:text-ink"
        >
          <ArrowLeft size={14} /> Back
        </button>

        <div className="card p-6 flex items-start justify-between">
          <div>
            <p className="eyebrow">{emp.employee_code}</p>
            <h2 className="font-display text-2xl font-semibold mt-1">{emp.full_name}</h2>
            <p className="text-sm text-ink-muted mt-1">{emp.designation} &middot; {emp.department?.name}</p>
            <p className="text-sm text-ink-muted">{emp.email}{emp.phone ? ` · ${emp.phone}` : ""}</p>
          </div>
          <span className="h-fit">
            <EntityBadge kind="employee-status" value={emp.employment_status} />
          </span>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Armchair size={16} className="text-brand" />
              <p className="eyebrow">Current seat</p>
            </div>
            {emp.current_seat ? (
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-mono text-lg font-medium">{emp.current_seat.seat_code}</p>
                  <p className="text-xs text-ink-muted flex items-center gap-1 mt-1">
                    <MapPin size={12} /> {emp.current_seat.floor?.name} · {emp.current_seat.zone}
                  </p>
                </div>
                <button
                  onClick={handleRelease}
                  disabled={releasing}
                  className="text-xs font-medium text-danger border border-danger/30 px-3 py-1.5 rounded-lg hover:bg-danger/5 disabled:opacity-50"
                >
                  {releasing ? "Releasing…" : "Release seat"}
                </button>
              </div>
            ) : (
              <p className="text-sm text-ink-muted">No seat currently assigned.</p>
            )}
          </div>

          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Briefcase size={16} className="text-brand" />
              <p className="eyebrow">Active projects</p>
            </div>
            {emp.active_projects.length ? (
              <ul className="space-y-2">
                {emp.active_projects.map((a) => (
                  <li key={a.id} className="flex items-center justify-between text-sm">
                    <div>
                      <p className="font-medium">{a.project?.name}</p>
                      <p className="text-xs text-ink-muted">{a.role_on_project}</p>
                    </div>
                    <span className="font-mono text-xs text-ink-muted">{a.allocation_percentage}%</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink-muted">Not assigned to any active projects.</p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
