import { useState, useMemo } from "react";
import type { TaxonomyLabel } from "@/types";

interface Props {
  labels: TaxonomyLabel[];
  value: string;
  onChange: (label: string) => void;
}

export default function LabelDropdown({ labels, value, onChange }: Props) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search) return labels;
    const q = search.toLowerCase();
    return labels.filter((l) =>
      l.name.toLowerCase().includes(q) ||
      (l.description && l.description.toLowerCase().includes(q))
    );
  }, [labels, search]);

  const grouped = useMemo(() => {
    const groups: Record<string, TaxonomyLabel[]> = {};
    for (const label of filtered) {
      const group = label.group || "other";
      if (!groups[group]) groups[group] = [];
      groups[group].push(label);
    }
    return groups;
  }, [filtered]);

  return (
    <div>
      <input
        type="text"
        placeholder="Search labels..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full bg-gray-700 rounded px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-blue-500 mb-2"
      />
      <div className="max-h-48 overflow-y-auto space-y-1">
        {Object.entries(grouped).map(([group, groupLabels]) => (
          <div key={group}>
            <div className="text-xs text-gray-500 uppercase px-1 mt-1">
              {group.replace(/_/g, " ")}
            </div>
            {groupLabels.map((label) => (
              <button
                key={label.id}
                onClick={() => {
                  onChange(label.name);
                  setSearch("");
                }}
                title={label.description || label.name}
                className={`w-full text-left px-2 py-1 rounded text-sm flex items-center gap-2 ${
                  value === label.name
                    ? "bg-blue-600"
                    : "hover:bg-gray-700"
                }`}
              >
                <span
                  className="w-3 h-3 rounded-sm shrink-0"
                  style={{ backgroundColor: label.color }}
                />
                <span className="flex-1 truncate">{label.name}</span>
                {label.shortcut && (
                  <span className="text-xs text-gray-500">
                    {label.shortcut}
                  </span>
                )}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
