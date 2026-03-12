import type { ImageStatus } from "@/types";

const STATUSES: (ImageStatus | null)[] = [
  null,
  "new",
  "in_progress",
  "labeled",
  "reviewed",
  "approved",
  "rejected",
];

const LABELS: Record<string, string> = {
  "": "All",
  new: "New",
  in_progress: "In Progress",
  labeled: "Labeled",
  reviewed: "Reviewed",
  approved: "Approved",
  rejected: "Rejected",
};

interface Props {
  value: ImageStatus | null;
  onChange: (status: ImageStatus | null) => void;
}

export default function StatusFilter({ value, onChange }: Props) {
  return (
    <select
      value={value || ""}
      onChange={(e) =>
        onChange((e.target.value || null) as ImageStatus | null)
      }
      className="w-full bg-gray-700 rounded px-2 py-1 text-sm outline-none"
    >
      {STATUSES.map((s) => (
        <option key={s || ""} value={s || ""}>
          {LABELS[s || ""]}
        </option>
      ))}
    </select>
  );
}
