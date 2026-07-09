"use client";

import { useEffect, useState } from "react";
import { UserPlus, CheckCircle2, Clock, RefreshCw } from "lucide-react";
import Topbar from "@/components/Topbar";
import { api, NewJoinerRequest, Floor } from "@/lib/api";

const emptyForm = {
  full_name: "", email: "", designation: "", department_id: "", date_of_joining: "",
  preferred_floor_id: "", preferred_zone: "",
};

export default function NewJoinersPage() {
  const [form, setForm] = useState(emptyForm);
  const [floors, setFloors] = useState<Floor[]>([]);
  const [departments, setDepartments] = useState<{ id: number; name: string }[]>([]);
  const [requests, setRequests] = useState<NewJoinerRequest[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<NewJoinerRequest | null>(null);
  const [error, setError] = useState("");

  const loadRequests = async () => {
    const { data } = await api.get<NewJoinerRequest[]>("/api/new-joiners");
    setRequests(data);
  };

  useEffect(() => {
    (async () => {
      const [f, r] = await Promise.all([
        api.get<Floor[]>("/api/seats/floors"),
        api.get<NewJoinerRequest[]>("/api/new-joiners"),
      ]);
      setFloors(f.data);
      setRequests(r.data);
      // departments aren't a standalone endpoint in this build; pull unique from employees would be heavy,
      // so use the fixed seed list — matches DEPARTMENTS in app/seed.py
      setDepartments([
        { id: 1, name: "Engineering" }, { id: 2, name: "Sales" }, { id: 3, name: "Human Resources" },
        { id: 4, name: "Finance" }, { id: 5, name: "Marketing" }, { id: 6, name: "Operations" },
        { id: 7, name: "Design" }, { id: 8, name: "Product" }, { id: 9, name: "Customer Support" },
        { id: 10, name: "Legal" },
      ]);
    })();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setResult(null);
    try {
      const { data } = await api.post<NewJoinerRequest>("/api/new-joiners", {
        employee: {
          full_name: form.full_name,
          email: form.email,
          designation: form.designation,
          department_id: form.department_id ? Number(form.department_id) : undefined,
          date_of_joining: form.date_of_joining,
        },
        preferred_floor_id: form.preferred_floor_id ? Number(form.preferred_floor_id) : undefined,
        preferred_zone: form.preferred_zone || undefined,
      });
      setResult(data);
      setForm(emptyForm);
      loadRequests();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Something went wrong. Please check the form and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const retryAllocation = async (id: number) => {
    try {
      await api.post(`/api/new-joiners/${id}/retry-allocation`);
      loadRequests();
    } catch {
      // seat still unavailable — leave state as-is
    }
  };

  const pending = requests.filter((r) => r.status === "pending");
  const allocated = requests.filter((r) => r.status === "allocated");

  return (
    <>
      <Topbar title="New Joiners" />
      <div className="p-6 grid lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <UserPlus size={16} className="text-brand" />
            <p className="eyebrow">Onboard a new joiner</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <input required placeholder="Full name" value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                className="col-span-2 px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand placeholder:text-ink-muted" />
              <input required type="email" placeholder="Email" value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="col-span-2 px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand placeholder:text-ink-muted" />
              <input placeholder="Designation" value={form.designation}
                onChange={(e) => setForm({ ...form, designation: e.target.value })}
                className="px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand placeholder:text-ink-muted" />
              <select value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value })}
                className="px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand">
                <option value="">Department</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
              <input required type="date" value={form.date_of_joining}
                onChange={(e) => setForm({ ...form, date_of_joining: e.target.value })}
                className="col-span-2 px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand placeholder:text-ink-muted" />
              <select value={form.preferred_floor_id} onChange={(e) => setForm({ ...form, preferred_floor_id: e.target.value })}
                className="px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand">
                <option value="">Preferred floor (optional)</option>
                {floors.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
              </select>
              <select value={form.preferred_zone} onChange={(e) => setForm({ ...form, preferred_zone: e.target.value })}
                className="px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand">
                <option value="">Preferred zone (optional)</option>
                {["Zone A", "Zone B", "Zone C", "Zone D"].map((z) => <option key={z} value={z}>{z}</option>)}
              </select>
            </div>

            {error && <p className="text-xs text-danger">{error}</p>}

            <button disabled={submitting} type="submit"
              className="w-full py-2.5 text-sm font-medium rounded-lg brand-gradient text-white glow-hover disabled:opacity-50 transition-colors">
              {submitting ? "Allocating…" : "Add joiner & auto-allocate seat"}
            </button>
          </form>

          {result && (
            <div className={`mt-4 p-3 rounded-lg text-sm flex items-start gap-2 ${
              result.status === "allocated" ? "bg-available/10 text-available" : "bg-occupied/10 text-occupied"
            }`}>
              {result.status === "allocated" ? <CheckCircle2 size={16} className="shrink-0 mt-0.5" /> : <Clock size={16} className="shrink-0 mt-0.5" />}
              <span>
                {result.status === "allocated"
                  ? `Seated at ${result.allocated_seat?.seat_code}.`
                  : "No matching seat was free — queued as pending. Try retry once a seat opens up."}
              </span>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="eyebrow">Pending allocation ({pending.length})</p>
            </div>
            {pending.length === 0 ? (
              <p className="text-sm text-ink-muted">No one is waiting on a seat right now.</p>
            ) : (
              <ul className="space-y-2">
                {pending.map((r) => (
                  <li key={r.id} className="flex items-center justify-between text-sm">
                    <div>
                      <p className="font-medium">{r.employee?.full_name}</p>
                      <p className="text-xs text-ink-muted">{r.employee?.employee_code} · requested {r.requested_date}</p>
                    </div>
                    <button onClick={() => retryAllocation(r.id)} className="flex items-center gap-1 text-xs font-medium text-brand hover:underline">
                      <RefreshCw size={12} /> Retry
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card p-5">
            <p className="eyebrow mb-3">Recently allocated ({allocated.length})</p>
            <ul className="space-y-2 max-h-64 overflow-auto">
              {allocated.slice(0, 15).map((r) => (
                <li key={r.id} className="flex items-center justify-between text-sm">
                  <p>{r.employee?.full_name}</p>
                  <span className="font-mono text-xs text-ink-muted">{r.allocated_seat?.seat_code}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </>
  );
}
