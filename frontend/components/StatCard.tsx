import { LucideIcon } from "lucide-react";
import Cell from "@/components/ui/Cell";

const ACCENT = {
  brand: "text-brand",
  available: "text-available",
  occupied: "text-occupied",
  danger: "text-danger",
} as const;

// A small 3x2 mosaic in the corner stands in for a literal chart — it echoes
// the seat-grid motif used everywhere else instead of a generic sparkline,
// and its fill ratio reflects the stat's own proportion where one applies.
function MiniMosaic({ ratio, tone }: { ratio: number; tone: keyof typeof ACCENT }) {
  const cells = 6;
  const filled = Math.round(Math.max(0, Math.min(1, ratio)) * cells);
  const dotClass = {
    brand: "bg-brand",
    available: "bg-available",
    occupied: "bg-occupied",
    danger: "bg-danger",
  }[tone];
  return (
    <div className="grid grid-cols-3 gap-[3px] w-8">
      {Array.from({ length: cells }).map((_, i) => (
        <div key={i} className={`aspect-square rounded-[2px] ${i < filled ? dotClass : "bg-border"}`} />
      ))}
    </div>
  );
}

export default function StatCard({
  label, value, sub, icon: Icon, accent = "brand", ratio,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: LucideIcon;
  accent?: keyof typeof ACCENT;
  /** optional 0–1 proportion this stat represents, drives the corner mosaic */
  ratio?: number;
}) {
  return (
    <div className="card p-5 relative overflow-hidden">
      <div className="flex items-start justify-between">
        <Icon size={16} strokeWidth={2} className={ACCENT[accent]} />
        {typeof ratio === "number" && <MiniMosaic ratio={ratio} tone={accent} />}
      </div>
      <p className="font-display text-[32px] leading-none font-semibold mt-4 tracking-tight tabular-nums">
        {value}
      </p>
      <p className="eyebrow mt-2">{label}</p>
      {sub && <p className="text-xs text-ink-muted mt-1">{sub}</p>}
    </div>
  );
}
