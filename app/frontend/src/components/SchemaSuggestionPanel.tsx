import { useState } from "react";
import { useAnnotationStore } from "@/stores/annotationStore";
import { useSchemaDefinitions, useSchemaTemplate } from "@/api/schemas";
import type { SchemaScoreResponse } from "@/types";

interface Props {
  imageId: number;
  schemaResults: SchemaScoreResponse | null;
  assignedSchema: string | null;
  onAssign: (schemaName: string) => void;
}

export default function SchemaSuggestionPanel({
  schemaResults,
  assignedSchema,
  onAssign,
}: Props) {
  const { setActiveLabel, setActiveTool, addAnnotation } = useAnnotationStore();
  const { data: schemaConfig } = useSchemaDefinitions();
  const applyTemplate = useSchemaTemplate();
  const [templateStatus, setTemplateStatus] = useState<string | null>(null);

  const handleApplyTemplate = async (schemaName: string) => {
    try {
      const annotations = await applyTemplate.mutateAsync(schemaName);
      if (!annotations || annotations.length === 0) {
        setTemplateStatus("No template found");
        setTimeout(() => setTemplateStatus(null), 2000);
        return;
      }
      for (const ann of annotations) {
        addAnnotation({
          tempId: crypto.randomUUID(),
          label: ann.label,
          x_min: ann.x_min,
          y_min: ann.y_min,
          x_max: ann.x_max,
          y_max: ann.y_max,
          source: "copied",
          confidence: null,
        });
      }
      // Also assign the schema
      onAssign(schemaName);
      setTemplateStatus(`Applied ${annotations.length} boxes`);
      setTimeout(() => setTemplateStatus(null), 2000);
    } catch {
      setTemplateStatus("No template yet — label one image first");
      setTimeout(() => setTemplateStatus(null), 3000);
    }
  };

  const schemas = schemaConfig?.schemas || [];
  const top5 = schemaResults?.top_matches?.slice(0, 5) || [];

  return (
    <div>
      {/* Apply Template section — always visible */}
      <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">
        Apply Template
      </h4>
      <p className="text-xs text-gray-600 mb-2">
        Pick a schema to auto-fill boxes from a previously labeled image.
      </p>
      <div className="flex flex-wrap gap-1 mb-3">
        {schemas.map((s: { name: string }) => (
          <button
            key={s.name}
            onClick={() => handleApplyTemplate(s.name)}
            disabled={applyTemplate.isPending}
            className={`text-xs px-2 py-1 rounded ${
              assignedSchema === s.name
                ? "bg-green-700 text-green-200"
                : "bg-gray-700 hover:bg-gray-600 text-gray-300"
            }`}
            title={`Apply template: ${s.name.replace(/_/g, " ")}`}
          >
            {s.name.replace(/_/g, " ")}
          </button>
        ))}
      </div>
      {templateStatus && (
        <div className="text-xs text-blue-400 mb-2">{templateStatus}</div>
      )}

      {assignedSchema && (
        <div className="text-xs text-green-400 mb-2 flex items-center gap-1">
          <span>Assigned:</span>
          <span className="font-medium">{assignedSchema.replace(/_/g, " ")}</span>
        </div>
      )}

      {/* Schema Suggestions — after saving */}
      {top5.length > 0 && (
        <>
          <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2 mt-3">
            Schema Suggestions
          </h4>
          <div className="space-y-2">
            {top5.map((match) => (
              <div
                key={match.schema}
                className="bg-gray-800 rounded p-2"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">
                    {match.schema.replace(/_/g, " ")}
                  </span>
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleApplyTemplate(match.schema)}
                      disabled={applyTemplate.isPending}
                      className="text-xs bg-purple-600 hover:bg-purple-700 disabled:opacity-50 px-2 py-0.5 rounded"
                      title="Apply boxes from template"
                    >
                      Apply
                    </button>
                    {assignedSchema === match.schema ? (
                      <span className="text-xs text-green-400 px-2 py-0.5">Assigned</span>
                    ) : (
                      <button
                        onClick={() => onAssign(match.schema)}
                        className="text-xs bg-blue-600 hover:bg-blue-700 px-2 py-0.5 rounded"
                      >
                        Assign
                      </button>
                    )}
                  </div>
                </div>
                {/* Score bar */}
                <div className="w-full bg-gray-700 rounded-full h-1.5 mb-1">
                  <div
                    className="bg-blue-500 h-1.5 rounded-full"
                    style={{ width: `${Math.round(match.score * 100)}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500">
                  Score: {(match.score * 100).toFixed(0)}%
                </div>
                {match.missing.length > 0 && (
                  <div className="text-xs text-yellow-500 mt-1 flex flex-wrap items-center gap-1">
                    <span>Missing:</span>
                    {match.missing.map((label) => (
                      <button
                        key={label}
                        onClick={() => {
                          setActiveLabel(label);
                          setActiveTool("draw");
                        }}
                        className="bg-yellow-900/40 hover:bg-yellow-700/50 text-yellow-400 px-1.5 py-0 rounded cursor-pointer"
                        title={`Draw ${label}`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                )}
                {match.conflicts.length > 0 && (
                  <div className="text-xs text-red-500 mt-1">
                    Conflicts: {match.conflicts.join(", ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
