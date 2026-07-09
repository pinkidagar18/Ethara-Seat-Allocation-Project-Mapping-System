"use client";

import { useEffect, useState } from "react";
import { X, Search } from "lucide-react";
import Topbar from "@/components/Topbar";
import SeatMap from "@/components/SeatMap";
import { api, Floor, SeatWithStatus, Employee, Paginated } from "@/lib/api";

export default function SeatsPage() {
  const [floors, setFloors] = useState<Floor[]>([]);
  const [activeFloor, setActiveFloor] = useState<number | null>(null);
  const [seats, setSeats] = useState<SeatWithStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<SeatWithStatus | null>(null);
  const [empSearch, setEmpSearch] = useState("");
  const [empResults, setEmpResults] = useState<Employee[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      const { data } = await api.get<Floor[]>("/api/seats/floors");
      setFloors(data);
      if (data.length) setActiveFloor(data[0].id);
    })();
  }, []);

  const loadSeats = async (floorId: number) => {
    setLoading(true);
    const { data } = await api.get<Paginated<SeatWithStatus>>("/api/seats", {
      params: { floor_id: floorId, page_size: 500 },
    });
    // pull remaining pages if the floor has more than 500 seats
    let all = [...data.items];
    const totalPages = Math.ceil(data.total / 500);
    for (let p = 2; p <= totalPages; p++) {
      const { data: more } = await api.get<Paginated<SeatWithStatus>>("/api/seats", {
        params: { floor_id: floorId, page_size: 500, page: p },
      });
      all = all.concat(more.items);
    }
    setSeats(all);
    setLoading(false);
  };

  useEffect(() => {
    if (activeFloor) loadSeats(activeFloor);
  }, [activeFloor]);

  useEffect(() => {
    if (empSearch.trim().length < 2) { setEmpResults([]); return; }
    const t = setTimeout(async () => {
      const { data } = await api.get<Paginated<Employee>>("/api/employees", {
        params: { search: empSearch, has_seat: false, page_size: 8 },
      });
      setEmpResults(data.items);
    }, 250);
    return () => clearTimeout(t);
  }, [empSearch]);

  const handleAllocate = async (employeeId: number) => {
    if (!selected) return;
    setBusy(true);
    try {
      await api.post("/api/seats/allocate", { seat_id: selected.id, employee_id: employeeId });
      if (activeFloor) await loadSeats(activeFloor);
      setSelected(null);
      setEmpSearch("");
      setEmpResults([]);
    } finally {
      setBusy(false);
    }
  };

  const handleRelease = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      await api.post(`/api/seats/${selected.id}/release`, {});
      if (activeFloor) await loadSeats(activeFloor);
      setSelected(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Topbar title="Seat Map" />
      <div className="p-6 flex gap-6">
        <div className="flex-1 min-w-0 space-y-4">
          <div className="flex gap-1 border-b border-white/10">
            {floors.map((f) => (
              <button
                key={f.id}
                onClick={() => setActiveFloor(f.id)}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  activeFloor === f.id ? "border-brand text-brand" : "border-transparent text-ink-muted hover:text-ink"
                }`}
              >
                {f.name}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-4 text-xs text-ink-muted">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-available/30 border border-dashed border-available/50" /> Available</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-occupied/40" /> Occupied</span>
          </div>

          {loading ? (
            <p className="text-sm text-ink-muted">Loading seat map…</p>
          ) : (
            <SeatMap seats={seats} onSelect={setSelected} selectedSeatId={selected?.id} />
          )}
        </div>

        {selected && (
          <div className="w-80 shrink-0 card p-5 h-fit sticky top-20">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="eyebrow">Seat</p>
                <p className="font-mono text-lg font-medium">{selected.seat_code}</p>
                <p className="text-xs text-ink-muted mt-0.5">{selected.floor?.name} &middot; {selected.zone} &middot; {selected.seat_type.replace("_", " ")}</p>
              </div>
              <button onClick={() => setSelected(null)} className="text-ink-muted hover:text-ink">
                <X size={16} />
              </button>
            </div>

            {selected.is_occupied ? (
              <div className="space-y-3">
                <div className="text-sm">
                  <p className="text-ink-muted text-xs mb-0.5">Occupied by</p>
                  <p className="font-medium">{selected.occupant_name}</p>
                </div>
                <button
                  onClick={handleRelease}
                  disabled={busy}
                  className="w-full py-2 text-sm font-medium rounded-lg border border-danger/30 text-danger hover:bg-danger/5 disabled:opacity-50"
                >
                  {busy ? "Releasing…" : "Release seat"}
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-xs text-ink-muted">This seat is available. Search for an unseated employee to allocate it.</p>
                <div className="relative">
                  <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted" />
                  <input
                    value={empSearch}
                    onChange={(e) => setEmpSearch(e.target.value)}
                    placeholder="Search employee…"
                    className="w-full pl-8 pr-2 py-1.5 text-sm bg-white/5 border border-white/10 rounded-lg focus-visible:outline-none focus:border-brand placeholder:text-ink-muted"
                  />
                </div>
                {empResults.length > 0 && (
                  <div className="space-y-1 max-h-48 overflow-auto">
                    {empResults.map((e) => (
                      <button
                        key={e.id}
                        onClick={() => handleAllocate(e.id)}
                        disabled={busy}
                        className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-white/[0.06] text-sm flex justify-between items-center disabled:opacity-50"
                      >
                        <span>{e.full_name}</span>
                        <span className="font-mono text-xs text-ink-muted">{e.employee_code}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
