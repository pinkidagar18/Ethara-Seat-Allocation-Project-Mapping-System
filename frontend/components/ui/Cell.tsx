import { LucideIcon } from "lucide-react";

// The whole app is about mapping people onto a grid of physical seats, so the
// grid-cell is the one visual idea worth repeating everywhere rather than
// inventing a new chart type per screen. This component is deliberately
// polymorphic: the same square building-block renders as an actual seat
// button in the seat map, or as one unit in a proportional utilization
// mosaic on the dashboard — same shape language, two jobs.
export type CellProps =
  | {
      variant: "seat";
      status: "occupied" | "available";
      icon?: LucideIcon;
      selected?: boolean;
      onClick?: () => void;
      title?: string;
    }
  | { variant: "mosaic"; filled: boolean; title?: string };

export default function Cell(props: CellProps) {
  if (props.variant === "seat") {
    const { status, icon: Icon, selected, onClick, title } = props;
    return (
      <button
        onClick={onClick}
        title={title}
        className={`aspect-square rounded-[5px] grid place-items-center transition-all ${
          selected ? "ring-2 ring-brand ring-offset-1" : ""
        } ${
          status === "occupied"
            ? "bg-occupied/25 text-occupied hover:bg-occupied/40"
            : "bg-available/15 text-available hover:bg-available/30 border border-dashed border-available/40"
        }`}
      >
        {Icon && <Icon size={12} strokeWidth={2.25} />}
      </button>
    );
  }

  const { filled, title } = props;
  return (
    <div
      title={title}
      className={`aspect-square rounded-[3px] transition-colors ${
        filled ? "bg-brand" : "bg-border"
      }`}
    />
  );
}
