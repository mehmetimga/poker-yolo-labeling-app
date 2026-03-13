import { useAnnotationStore } from "@/stores/annotationStore";
import { useTaxonomy } from "@/api/schemas";
import Tooltip from "./Tooltip";

export default function AnnotationList() {
  const {
    annotations,
    selectedAnnotationId,
    setSelectedAnnotationId,
    removeAnnotation,
  } = useAnnotationStore();
  const { data: taxonomy } = useTaxonomy();

  const colorMap: Record<string, string> = {};
  const descMap: Record<string, string> = {};
  if (taxonomy) {
    for (const l of taxonomy.labels) {
      colorMap[l.name] = l.color;
      if (l.description) descMap[l.name] = l.description;
    }
  }

  if (annotations.length === 0) {
    return (
      <p className="text-gray-600 text-sm">
        No annotations. Press B to start drawing.
      </p>
    );
  }

  return (
    <div className="space-y-1">
      {annotations.map((ann) => {
        const isSelected = ann.tempId === selectedAnnotationId;
        const color = colorMap[ann.label] || "#ffffff";
        const description = descMap[ann.label] || "";
        return (
          <Tooltip key={ann.tempId} text={description} position="top" delay={400}>
            <div
              onClick={() => setSelectedAnnotationId(ann.tempId)}
              className={`flex items-center gap-2 px-2 py-1 rounded text-sm cursor-pointer ${
                isSelected ? "bg-gray-700 ring-1 ring-blue-500" : "hover:bg-gray-800"
              }`}
            >
              <span
                className="w-2.5 h-2.5 rounded-sm shrink-0"
                style={{ backgroundColor: color }}
              />
              <span className="flex-1 truncate">{ann.label}</span>
              {ann.source !== "manual" && (
                <span className="text-xs text-gray-500">{ann.source}</span>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeAnnotation(ann.tempId);
                }}
                className="text-gray-500 hover:text-red-400 text-xs"
              >
                x
              </button>
            </div>
          </Tooltip>
        );
      })}
    </div>
  );
}
