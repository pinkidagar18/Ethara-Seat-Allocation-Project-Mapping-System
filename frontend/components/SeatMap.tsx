"use client";

import { SeatWithStatus } from "@/lib/api";
import { Armchair, DoorOpen, Coffee } from "lucide-react";
import Cell from "@/components/ui/Cell";

const TYPE_ICON = { regular: Armchair, cabin: DoorOpen, hot_desk: Coffee } as const;

export default function SeatMap({
  seats, onSelect, selectedSeatId,
}: {
  seats: SeatWithStatus[];
  onSelect: (seat: SeatWithStatus) => void;
  selectedSeatId?: number;
}) {
  const zones = Array.from(new Set(seats.map((s) => s.zone))).sort();

  return (
    <div className="space-y-6">
      {zones.map((zone) => {
        const zoneSeats = seats.filter((s) => s.zone === zone);
        const occupiedCount = zoneSeats.filter((s) => s.is_occupied).length;
        return (
          <div key={zone}>
            <div className="flex items-center justify-between mb-2">
              <p className="eyebrow">{zone}</p>
              <p className="text-[11px] font-mono text-ink-muted">
                {occupiedCount}/{zoneSeats.length} occupied
              </p>
            </div>
            <div
              className="grid gap-1.5 p-3 bg-white/[0.03] rounded-lg border border-white/10"
              style={{ gridTemplateColumns: "repeat(auto-fill, minmax(30px, 1fr))" }}
            >
              {zoneSeats.map((seat) => (
                <Cell
                  key={seat.id}
                  variant="seat"
                  status={seat.is_occupied ? "occupied" : "available"}
                  icon={TYPE_ICON[seat.seat_type]}
                  selected={seat.id === selectedSeatId}
                  onClick={() => onSelect(seat)}
                  title={`${seat.seat_code}${seat.occupant_name ? ` — ${seat.occupant_name}` : " — available"}`}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
