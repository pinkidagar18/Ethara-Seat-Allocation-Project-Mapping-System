import { LucideIcon, CircleCheck, CircleX, CircleDot, Clock3, Ban, Armchair, DoorOpen, Coffee } from "lucide-react";

type Variant = { label: string; className: string; icon?: LucideIcon };

export type EntityBadgeProps =
  | { kind: "employee-status"; value: "active" | "exited" }
  | { kind: "seat-status"; value: "occupied" | "available" }
  | { kind: "project-status"; value: "active" | "completed" | "on_hold" }
  | { kind: "joiner-status"; value: "pending" | "allocated" | "cancelled" }
  | { kind: "seat-type"; value: "regular" | "cabin" | "hot_desk" };

// One lookup table keyed by [kind][value] — this is the whole "polymorphism":
// every page renders <EntityBadge kind="..." value="..." /> and gets the right
// label/color/icon for that entity's status vocabulary, instead of each page
// hand-rolling its own STATUS_STYLE map.
const MAP: Record<string, Record<string, Variant>> = {
  "employee-status": {
    active: { label: "Active", className: "bg-available/10 text-available", icon: CircleCheck },
    exited: { label: "Exited", className: "bg-hold/10 text-hold", icon: CircleX },
  },
  "seat-status": {
    occupied: { label: "Occupied", className: "bg-occupied/10 text-occupied", icon: CircleDot },
    available: { label: "Available", className: "bg-available/10 text-available", icon: CircleCheck },
  },
  "project-status": {
    active: { label: "Active", className: "bg-available/10 text-available", icon: CircleCheck },
    completed: { label: "Completed", className: "bg-brand-light text-brand", icon: CircleCheck },
    on_hold: { label: "On hold", className: "bg-occupied/10 text-occupied", icon: Clock3 },
  },
  "joiner-status": {
    pending: { label: "Pending", className: "bg-occupied/10 text-occupied", icon: Clock3 },
    allocated: { label: "Allocated", className: "bg-available/10 text-available", icon: CircleCheck },
    cancelled: { label: "Cancelled", className: "bg-danger/10 text-danger", icon: Ban },
  },
  "seat-type": {
    regular: { label: "Desk", className: "bg-bg text-ink-muted border border-border", icon: Armchair },
    cabin: { label: "Cabin", className: "bg-bg text-ink-muted border border-border", icon: DoorOpen },
    hot_desk: { label: "Hot desk", className: "bg-bg text-ink-muted border border-border", icon: Coffee },
  },
};

export default function EntityBadge({ kind, value }: EntityBadgeProps) {
  const variant = MAP[kind]?.[value as string] ?? {
    label: String(value).replace("_", " "),
    className: "bg-bg text-ink-muted",
  };
  const Icon = variant.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 pl-1.5 pr-2 py-0.5 rounded-full text-[11px] font-medium tracking-wide ${variant.className}`}
    >
      {Icon && <Icon size={11} strokeWidth={2.5} />}
      {variant.label}
    </span>
  );
}
