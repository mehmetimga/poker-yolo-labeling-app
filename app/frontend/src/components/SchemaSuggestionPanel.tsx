import type { SchemaScoreResponse } from "@/types";

interface Props {
  imageId: number;
  schemaResults: SchemaScoreResponse | null;
  onAssign: (schemaName: string) => void;
}

export default function SchemaSuggestionPanel({
  schemaResults,
  onAssign,
}: Props) {
  if (!schemaResults || schemaResults.top_matches.length === 0) {
    return (
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">
          Schema Suggestions
        </h4>
        <p className="text-gray-600 text-sm">
          Save annotations to see schema suggestions.
        </p>
      </div>
    );
  }

  const top5 = schemaResults.top_matches.slice(0, 5);

  return (
    <div>
      <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">
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
              <button
                onClick={() => onAssign(match.schema)}
                className="text-xs bg-blue-600 hover:bg-blue-700 px-2 py-0.5 rounded"
              >
                Assign
              </button>
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
              <div className="text-xs text-yellow-500 mt-1">
                Missing: {match.missing.join(", ")}
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
    </div>
  );
}
